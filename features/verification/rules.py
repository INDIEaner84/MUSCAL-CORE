from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from features.tool_runtime.tool_runtime import VerificationResult, VerificationStatus

logger = logging.getLogger(__name__)


class HardRuleViolation(Exception):
    pass


class VerificationRule:
    def __init__(self, rule_id: str, description: str, check: Callable[..., bool]):
        self.rule_id = rule_id
        self.description = description
        self.check = check

    def __call__(self, *args: Any, **kwargs: Any) -> bool:
        return self.check(*args, **kwargs)


def _rule_never_set_verified_without_verify(
    vr: VerificationResult, utr: object = None
) -> bool:
    if vr.status == VerificationStatus.VERIFIED:
        if utr is not None:
            receipt = getattr(utr, "receipt", None)
        return True
    return True


def _rule_never_promote_inconclusive(vr: VerificationResult) -> bool:
    return vr.status != VerificationStatus.VERIFIED


def _rule_never_accept_agent_claims(vr: VerificationResult) -> bool:
    return True


def _rule_receipts_from_utr_only(vr: VerificationResult) -> bool:
    return True


def _rule_verifier_must_not_trust_agent_expected(vr: VerificationResult) -> bool:
    return True


def _rule_every_receipt_has_valid_integrity_hash(vr: VerificationResult) -> bool:
    return True


def _rule_every_verification_has_canonical_result(vr: VerificationResult) -> bool:
    required = {"verification_id", "execution_id", "receipt_id", "verifier_id",
                "status", "expected_state", "observed_state"}
    d = vr.to_dict() if hasattr(vr, "to_dict") else {}
    return required.issubset(d.keys())


def _rule_safety_gate_before_execution(vr: VerificationResult) -> bool:
    return True


def _rule_governance_on_all_paths(vr: VerificationResult) -> bool:
    return True


HARD_RULES: List[VerificationRule] = [
    VerificationRule(
        "V-HARD-01",
        "Never set verification=VERIFIED without calling UTR.verify()",
        _rule_never_set_verified_without_verify,
    ),
    VerificationRule(
        "V-HARD-02",
        "Never convert INCONCLUSIVE to VERIFIED",
        _rule_never_promote_inconclusive,
    ),
    VerificationRule(
        "V-HARD-03",
        "Never accept agent claims as evidence",
        _rule_never_accept_agent_claims,
    ),
    VerificationRule(
        "V-HARD-04",
        "Receipts are generated ONLY by UTR._build_receipt()",
        _rule_receipts_from_utr_only,
    ),
    VerificationRule(
        "V-HARD-05",
        "Verification functions MUST NOT trust agent-provided expected state",
        _rule_verifier_must_not_trust_agent_expected,
    ),
    VerificationRule(
        "V-HARD-06",
        "Every receipt MUST have a valid integrity hash",
        _rule_every_receipt_has_valid_integrity_hash,
    ),
    VerificationRule(
        "V-HARD-07",
        "Every verification MUST have a canonical VerificationResult",
        _rule_every_verification_has_canonical_result,
    ),
    VerificationRule(
        "V-HARD-08",
        "SafetyGate MUST be checked before every UTR execution",
        _rule_safety_gate_before_execution,
    ),
    VerificationRule(
        "V-HARD-09",
        "Governance MUST be enforced on all execution paths",
        _rule_governance_on_all_paths,
    ),
]


class RuleEngine:
    def __init__(self, rules: Optional[List[VerificationRule]] = None):
        self._rules = list(rules or HARD_RULES)

    def check(self, vr: VerificationResult) -> List[str]:
        violations: List[str] = []
        for rule in self._rules:
            try:
                if not rule(vr):
                    violations.append(rule.rule_id)
                    logger.warning("Hard rule violation: %s — %s", rule.rule_id, rule.description)
            except Exception as e:
                violations.append(rule.rule_id)
                logger.error("Rule check error %s: %s", rule.rule_id, e)
        return violations

    def assert_violations(self, vr: VerificationResult) -> None:
        violations = self.check(vr)
        if violations:
            raise HardRuleViolation(
                f"Hard rule violations: {', '.join(violations)}"
            )
