import logging
import time
from typing import Any, Dict, Optional

from event_bus import EventMessage
from features.identity.execution_context import ExecutionContext
from features.identity.reality import (
    normalize_execution_mode,
    normalize_execution_state,
    normalize_verification_state,
    ValidationError,
    verify_state_transition,
)

logger = logging.getLogger(__name__)

PROJECTION_VERSION = "2.0.0"

CANONICAL_SOURCES = frozenset({
    "muscal_kernel",
    "muscal_core",
    "EnrichedMuscalOS",
    "VerificationOrchestrator",
    "UnifiedToolRuntime",
    "GraphBuilder",
    "kernel",
    "enriched_bootstrap",
    "graph_os_projection",
    "feedback",
    "plugin_loader",
    "ExecutionWatchdog",
})

CANONICAL_EVENT_TYPES = frozenset({
    "NODE_CREATED",
    "NODE_UPDATED",
    "NODE_COMPLETED",
    "NODE_FAILED",
    "NODE_ARCHIVED",
    "EDGE_CREATED",
    "EDGE_REMOVED",
    "EXECUTION_STARTED",
    "EXECUTION_COMPLETED",
    "EXECUTION_FAILED",
    "SIMULATION_STARTED",
    "SIMULATION_COMPLETED",
    "VERIFICATION_PASSED",
    "VERIFICATION_FAILED",
})

SENSITIVE_PAYLOAD_FIELDS = frozenset({
    "tool_result",
    "file_path",
    "command",
    "credentials",
    "environment",
    "input_text",
    "api_key",
    "token",
    "password",
    "secret",
})

ENRICHMENT_FIELDS = frozenset({
    "execution_id",
    "correlation_id",
    "causation_id",
    "execution_mode",
    "execution_state",
    "verification_state",
    "event_version",
    "provenance",
})


class ProjectionError(Exception):
    pass


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for key, value in payload.items():
        if key in SENSITIVE_PAYLOAD_FIELDS:
            continue
        if key == "error" and isinstance(value, str):
            sanitized[key] = value[:500]
            continue
        sanitized[key] = value
    return sanitized


def validate_normalized(event: Dict[str, Any]) -> None:
    required = {"event_id", "event_type", "timestamp", "sequence_number",
                "execution_id", "source", "actor",
                "execution_mode", "execution_state", "verification_state",
                "payload"}
    missing = required - set(event.keys())
    if missing:
        raise ProjectionError(f"missing required fields: {missing}")

    verify_state_transition(
        event["execution_mode"],
        event["execution_state"],
        event["verification_state"],
    )


class GraphOSProjection:
    def __init__(self, event_store=None):
        self._event_store = event_store
        self._projected_count = 0
        self._rejected_count = 0

    def project(self, raw: EventMessage) -> Optional[Dict[str, Any]]:
        topic = raw.topic.upper()
        if topic not in CANONICAL_EVENT_TYPES:
            self._rejected_count += 1
            logger.debug("rejected non-canonical event type: %s", raw.topic)
            return None

        source = raw.source or (raw.payload.get("source", "") if raw.payload else "") or "muscal_kernel"
        if source not in CANONICAL_SOURCES:
            logger.warning("non-canonical source '%s' projected — consider adding to CANONICAL_SOURCES", source)

        payload = raw.payload or {}
        seq = self._resolve_seq(raw)

        ctx = ExecutionContext.extract_from_payload(payload)

        event_type = payload.get("event_type", topic)
        event_version = payload.get("event_version", 1)
        actor = payload.get("actor", source)

        event_id = (payload.get("event_id")
                    or raw.id
                    or f"{topic}_{seq}_{int(time.time() * 1000)}")

        provenance = payload.get("provenance")

        normalized = {
            "event_id": event_id,
            "event_type": event_type,
            "event_version": event_version,
            "timestamp": _fmt_timestamp(raw.timestamp),
            "sequence_number": seq,
            "execution_id": ctx.execution_id,
            "correlation_id": ctx.correlation_id or None,
            "causation_id": ctx.causation_id or None,
            "source": source,
            "actor": actor,
            "execution_mode": ctx.execution_mode,
            "execution_state": ctx.execution_state,
            "verification_state": ctx.verification_state,
            "provenance": provenance,
            "payload": sanitize_payload(payload),
        }

        try:
            validate_normalized(normalized)
        except (ProjectionError, ValidationError) as e:
            logger.warning("projection rejected event %s: %s", raw.id, e)
            self._rejected_count += 1
            return None

        self._projected_count += 1
        return normalized

    def _resolve_seq(self, raw: EventMessage) -> int:
        if self._event_store is not None:
            try:
                return self._event_store.get_cursor()
            except Exception:
                pass
        return int(raw.timestamp * 1000)

    def stats(self) -> Dict[str, Any]:
        return {
            "projected": self._projected_count,
            "rejected": self._rejected_count,
            "version": PROJECTION_VERSION,
        }


def _fmt_timestamp(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()
