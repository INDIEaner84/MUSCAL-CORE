from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from event_bus import EventBus, EventMessage, EventPriority
from features.identity.execution_context import (
    ExecutionContext,
    get_context_manager,
)
from features.identity.reality import (
    ExecutionMode,
    normalize_execution_mode,
)
from features.identity.uuid7 import uuid7
from features.monitoring.execution_watchdog import ExecutionWatchdog
from features.streaming.ws_adapter import WebSocketAdapter
from features.verification.orchestrator import VerificationOrchestrator
from muscal_os import MuscalOS
from boot_manager import BootReport

logger = logging.getLogger(__name__)

BOOTSTRAP_VERSION = "1.0.0"

LIFECYCLE_EVENTS = frozenset({
    "EXECUTION_STARTED",
    "EXECUTION_COMPLETED",
    "EXECUTION_FAILED",
})


class EnrichedMuscalOS:
    def __init__(
        self,
        os: MuscalOS,
        ws_adapter: Optional[WebSocketAdapter] = None,
        verification_orchestrator: Optional[VerificationOrchestrator] = None,
    ):
        self._os = os
        self._ws = ws_adapter
        self._verifier = verification_orchestrator
        self._ctx_mgr = get_context_manager()
        self._watchdog: Optional[ExecutionWatchdog] = None

    def start(self) -> BootReport:
        report = self._os.start()
        if not report.success:
            return report

        # Atomic swap — no event-loss window between unsubscribe and subscribe
        self._os.events.swap_subscriber("*", self._os._persist_to_store, self._enriched_persist)

        if self._ws is not None:
            self._ws.start()
            logger.info("WebSocketAdapter lifecycle bound to EnrichedMuscalOS")

        self._init_trust_core()

        return report

    def _init_trust_core(self):
        if self._os.event_store is None:
            logger.warning(
                "Trust Core wiring SKIPPED — no EventStore. "
                "All UTR instances will lack receipt/verification persistence."
            )
            return

        from features.tool_runtime.tool_runtime import (
            set_global_event_store,
            set_global_default_timeout,
        )

        set_global_event_store(self._os.event_store)
        set_global_default_timeout(300)
        logger.info(
            "Global EventStore set — all create_default_utr() calls auto-wired"
        )

        if self._verifier is None:
            from features.verification.orchestrator import VerificationOrchestrator
            self._verifier = VerificationOrchestrator(event_bus=self._os.events)
            logger.info(
                "VerificationOrchestrator auto-created with EventBus"
            )

        self._watchdog = ExecutionWatchdog(
            event_store=self._os.event_store,
            event_bus=self._os.events,
        )
        self._watchdog.start()
        logger.info("ExecutionWatchdog started")

    def shutdown(self) -> BootReport:
        if self._watchdog is not None:
            self._watchdog.stop()
            logger.info("ExecutionWatchdog stopped via EnrichedMuscalOS shutdown")
        if self._ws is not None:
            self._ws.stop()
            logger.info("WebSocketAdapter stopped via EnrichedMuscalOS shutdown")
        return self._os.shutdown()

    def run(
        self,
        input_text: str,
        execution_mode: str = "real",
        correlation_id: str = "",
        causation_id: str = "",
        parent_context: Optional[ExecutionContext] = None,
    ) -> Dict[str, Any]:
        parent_ctx = parent_context or self._ctx_mgr.get_context()

        ctx = ExecutionContext(
            execution_id=uuid7(),
            correlation_id=correlation_id or (parent_ctx.execution_id if parent_ctx else ""),
            causation_id=causation_id or (parent_ctx.execution_id if parent_ctx else ""),
            execution_mode=normalize_execution_mode(execution_mode),
            execution_state="running",
            verification_state="unverified",
        )
        self._ctx_mgr.set_context(ctx)

        self._publish_lifecycle("EXECUTION_STARTED", {
            "input": input_text,
            "execution_id": ctx.execution_id,
            "execution_mode": ctx.execution_mode,
            "execution_state": "running",
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id,
        })

        try:
            result = self._os.run(input_text, execution_context=ctx)

            if result.get("success", False):
                ctx.transition_state("completed")
                self._publish_lifecycle("EXECUTION_COMPLETED", {
                    "execution_id": ctx.execution_id,
                    "result": result,
                })
            else:
                ctx.transition_state("failed")
                self._publish_lifecycle("EXECUTION_FAILED", {
                    "execution_id": ctx.execution_id,
                    "error": result.get("errors", "unknown error"),
                })

            return result

        except Exception as e:
            ctx.transition_state("failed")
            self._publish_lifecycle("EXECUTION_FAILED", {
                "execution_id": ctx.execution_id,
                "error": str(e),
            })
            raise

        finally:
            if parent_ctx is not None:
                self._ctx_mgr.set_context(parent_ctx)
            else:
                self._ctx_mgr.clear_context()

    def verify_execution(
        self,
        execution_id: str,
        utr: Any = None,
    ) -> None:
        if self._verifier is not None and utr is not None:
            self._verifier.verify_execution(execution_id, utr=utr)

    @property
    def verification_orchestrator(self) -> Optional[VerificationOrchestrator]:
        return self._verifier

    def _publish_lifecycle(self, event_type: str, extra: Dict[str, Any]) -> None:
        ctx = self._ctx_mgr.current_or_default()
        payload = ctx.enrich_payload(extra)
        payload.setdefault("event_type", event_type)
        self._os.events.publish(
            event_type,
            payload,
            source="enriched_bootstrap",
            priority=EventPriority.HIGH,
        )

    def _enriched_persist(self, msg: EventMessage) -> None:
        if self._os.event_store is None:
            return
        ctx = self._ctx_mgr.current_or_default()
        enriched_payload = ctx.enrich_payload(dict(msg.payload or {}))
        self._os.event_store.append({
            "topic": msg.topic,
            "payload": enriched_payload,
            "source": msg.source,
            "priority": msg.priority,
            "timestamp": msg.timestamp,
            "id": msg.id,
            "execution_id": ctx.execution_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id,
            "execution_mode": ctx.execution_mode,
            "execution_state": ctx.execution_state,
            "verification_state": ctx.verification_state,
        })

    def __getattr__(self, name: str) -> Any:
        return getattr(self._os, name)

    @property
    def os(self) -> MuscalOS:
        return self._os

    @property
    def bootstrap_version(self) -> str:
        return BOOTSTRAP_VERSION
