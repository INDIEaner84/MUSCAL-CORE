from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from event_bus import EventBus, EventMessage, EventPriority
from features.identity.execution_context import (
    ExecutionContext,
    get_context_manager,
)
from features.identity.reality import (
    normalize_verification_state,
    verify_state_transition,
)
from features.identity.uuid7 import uuid7
from features.tool_runtime.tool_runtime import (
    ExecutionReceipt,
    UnifiedToolRuntime,
    VerificationResult,
    VerificationStatus,
)
from features.verification.rules import HardRuleViolation, RuleEngine
from features.verification.verifier import (
    BUILTIN_VERIFIERS,
    IntegrityVerifier,
    Verifier,
)

logger = logging.getLogger(__name__)

ORCHESTRATOR_VERSION = "2.0.0"

LIFECYCLE_EVENTS = frozenset({
    "VERIFICATION_PASSED",
    "VERIFICATION_FAILED",
})


class VerificationOrchestrator:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        rule_engine: Optional[RuleEngine] = None,
    ):
        self._verifiers: Dict[str, Verifier] = dict(BUILTIN_VERIFIERS)
        self._event_bus = event_bus
        self._rule_engine = rule_engine or RuleEngine()
        self._verification_store: Dict[str, VerificationResult] = {}
        self._ctx_mgr = get_context_manager()

    def register_verifier(self, name: str, verifier: Verifier) -> None:
        self._verifiers[name] = verifier

    def get_verifier(self, name: str) -> Optional[Verifier]:
        return self._verifiers.get(name)

    def verify(
        self,
        receipt: ExecutionReceipt,
        expected_state: Optional[Dict[str, Any]] = None,
        publish: bool = True,
    ) -> VerificationResult:
        integrity = IntegrityVerifier()
        integrity_result = integrity.verify(receipt)
        if integrity_result.status in (VerificationStatus.TAMPERED,):
            vr = integrity_result
            self._store_and_publish(vr, publish)
            return vr

        verifier = self._verifiers.get(receipt.tool_name)
        if verifier is None:
            vr = VerificationResult(
                verification_id=uuid7(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id="none",
                status=VerificationStatus.NOT_SUPPORTED,
                expected_state={},
                observed_state={},
                evidence={"note": f"No verifier registered for '{receipt.tool_name}'"},
                verified_at=time.time(),
            )
            self._store_and_publish(vr, publish)
            return vr

        try:
            vr = verifier.verify(receipt, expected_state=expected_state)
        except Exception as e:
            vr = VerificationResult(
                verification_id=uuid7(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=receipt.tool_name,
                status=VerificationStatus.INCONCLUSIVE,
                expected_state={},
                observed_state={},
                evidence={"verifier": receipt.tool_name, "error": str(e)},
                verified_at=time.time(),
            )

        violations = self._rule_engine.check(vr)
        if violations:
            logger.warning(
                "Verification %s violates hard rules: %s",
                vr.verification_id, violations,
            )

        receipt.set_verification(vr)
        self._store_and_publish(vr, publish)
        return vr

    def verify_execution(
        self,
        execution_id: str,
        utr: Optional[UnifiedToolRuntime] = None,
        publish: bool = True,
    ) -> List[VerificationResult]:
        results: List[VerificationResult] = []
        if utr is not None:
            for receipt in self._collect_receipts_for_execution(execution_id, utr):
                vr = self.verify(receipt, publish=publish)
                results.append(vr)
        return results

    def _collect_receipts_for_execution(
        self,
        execution_id: str,
        utr: UnifiedToolRuntime,
    ) -> List[ExecutionReceipt]:
        receipts: List[ExecutionReceipt] = []
        for r in utr.receipts():
            if r.execution_id == execution_id:
                receipts.append(r)
        return receipts

    def _store_and_publish(
        self,
        vr: VerificationResult,
        publish: bool,
    ) -> None:
        self._verification_store[vr.verification_id] = vr

        if publish and self._event_bus is not None:
            self._publish_verification_event(vr)

    def _publish_verification_event(self, vr: VerificationResult) -> None:
        is_passed = vr.status == VerificationStatus.VERIFIED
        event_type = "VERIFICATION_PASSED" if is_passed else "VERIFICATION_FAILED"

        ctx = self._ctx_mgr.current_or_default()
        payload = ctx.enrich_payload({
            "event_type": event_type,
            "verification_id": vr.verification_id,
            "execution_id": vr.execution_id,
            "receipt_id": vr.receipt_id,
            "verifier_id": vr.verifier_id,
            "status": vr.status,
            "expected_state": vr.expected_state,
            "observed_state": vr.observed_state,
            "state_diff": vr.state_diff,
            "evidence": vr.evidence,
            "verified_at": vr.verified_at,
        })

        if is_passed:
            ctx.set_verification("verified", evidence_receipt_id=vr.receipt_id)
        elif vr.status == VerificationStatus.FAILED:
            ctx.set_verification("failed", evidence_receipt_id=vr.receipt_id)

        self._event_bus.publish(
            event_type,
            payload,
            source="verification_orchestrator",
            priority=EventPriority.HIGH,
        )

    def verification_results(
        self,
        execution_id: Optional[str] = None,
    ) -> List[VerificationResult]:
        if execution_id is not None:
            return [
                vr for vr in self._verification_store.values()
                if vr.execution_id == execution_id
            ]
        return list(self._verification_store.values())

    def get_result(self, verification_id: str) -> Optional[VerificationResult]:
        return self._verification_store.get(verification_id)
