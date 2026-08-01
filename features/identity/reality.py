from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)

REALITY_VERSION = "1.0.0"


class ExecutionMode(Enum):
    REAL = "real"
    SIMULATED = "simulated"
    PROPOSED = "proposed"
    SHADOW = "shadow"
    REPLAY = "replay"


class ExecutionState(Enum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VerificationState(Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"
    REJECTED = "rejected"


_VALID_EXECUTION_MODES = frozenset(e.value for e in ExecutionMode)
_VALID_EXECUTION_STATES = frozenset(e.value for e in ExecutionState)
_VALID_VERIFICATION_STATES = frozenset(e.value for e in VerificationState)


def normalize_execution_mode(value: Optional[str]) -> str:
    if value in _VALID_EXECUTION_MODES:
        return value
    logger.warning("invalid execution_mode '%s', falling back to 'real'", value)
    return "real"


def normalize_execution_state(value: Optional[str]) -> str:
    if value in _VALID_EXECUTION_STATES:
        return value
    logger.warning("invalid execution_state '%s', falling back to 'planned'", value)
    return "planned"


def normalize_verification_state(value: Optional[str]) -> str:
    if value in _VALID_VERIFICATION_STATES:
        return value
    logger.warning("invalid verification_state '%s', falling back to 'unverified'", value)
    return "unverified"


_EXECUTION_MODE_STATE_MATRIX: Dict[str, frozenset] = {
    "real": frozenset(("planned", "queued", "running", "completed", "failed", "cancelled")),
    "simulated": frozenset(("planned", "queued", "running", "completed", "failed", "cancelled")),
    "proposed": frozenset(("planned", "cancelled")),
    "shadow": frozenset(("planned", "queued", "running", "completed", "failed", "cancelled")),
    "replay": frozenset(("planned", "queued", "running", "completed", "failed", "cancelled")),
}

_VERIFICATION_MODE_MATRIX: Dict[str, Dict[str, str]] = {
    "real": {"unverified": "VALID", "verified": "VALID", "failed": "VALID", "rejected": "VALID"},
    "simulated": {"unverified": "VALID", "verified": "CONTEXT_DEPENDENT", "failed": "VALID", "rejected": "VALID"},
    "proposed": {"unverified": "VALID", "verified": "INVALID", "failed": "INVALID", "rejected": "VALID"},
    "shadow": {"unverified": "VALID", "verified": "VALID", "failed": "VALID", "rejected": "VALID"},
    "replay": {"unverified": "VALID", "verified": "CONTEXT_DEPENDENT", "failed": "VALID", "rejected": "VALID"},
}


def validate_state_transition(
    execution_mode: str,
    execution_state: str,
    verification_state: str,
) -> bool:
    allowed_states = _EXECUTION_MODE_STATE_MATRIX.get(execution_mode)
    if allowed_states is None:
        logger.warning("unknown execution_mode '%s'", execution_mode)
        return False
    if execution_state not in allowed_states:
        logger.warning(
            "invalid state: execution_mode='%s' + execution_state='%s'",
            execution_mode, execution_state,
        )
        return False

    mode_rules = _VERIFICATION_MODE_MATRIX.get(execution_mode, {})
    validity = mode_rules.get(verification_state, "INVALID")
    if validity == "INVALID":
        logger.warning(
            "invalid combination: execution_mode='%s' + verification_state='%s'",
            execution_mode, verification_state,
        )
        return False
    return True


class ValidationError(ValueError):
    pass


def verify_state_transition(
    execution_mode: str,
    execution_state: str,
    verification_state: str,
) -> None:
    if not validate_state_transition(execution_mode, execution_state, verification_state):
        raise ValidationError(
            f"Invalid state: execution_mode='{execution_mode}', "
            f"execution_state='{execution_state}', "
            f"verification_state='{verification_state}'"
        )


_VALID_EXECUTION_STATE_TRANSITIONS: Dict[str, frozenset] = {
    "planned": frozenset({"queued", "cancelled"}),
    "queued": frozenset({"running", "cancelled"}),
    "running": frozenset({"completed", "failed", "cancelled"}),
    "completed": frozenset(),
    "failed": frozenset({"queued", "cancelled"}),
    "cancelled": frozenset(),
}


def validate_execution_state_change(current: str, target: str) -> bool:
    allowed = _VALID_EXECUTION_STATE_TRANSITIONS.get(current)
    if allowed is None:
        return False
    return target in allowed


def verify_execution_state_change(current: str, target: str) -> None:
    if not validate_execution_state_change(current, target):
        raise ValidationError(
            f"Invalid execution state transition: {current} → {target}"
        )


_VALID_VERIFICATION_STATE_TRANSITIONS: Dict[str, frozenset] = {
    "unverified": frozenset({"verified", "failed", "rejected"}),
    "verified": frozenset({"failed"}),  # external contradiction
    "failed": frozenset({"unverified"}),  # re-verify
    "rejected": frozenset(),
}


def validate_verification_state_change(current: str, target: str) -> bool:
    allowed = _VALID_VERIFICATION_STATE_TRANSITIONS.get(current)
    if allowed is None:
        return False
    return target in allowed


def verify_verification_state_change(current: str, target: str) -> None:
    if not validate_verification_state_change(current, target):
        raise ValidationError(
            f"Invalid verification state transition: {current} → {target}"
        )


SEMANTIC_RULES = [
    "proposed + verified = INVALID — a plan cannot be verified before execution",
    "proposed + running = INVALID — a plan is not executed",
    "simulated + verified = Verified as internally consistent, NOT verified as matching reality",
    "replay + verified = Replay is faithful, NOT the replayed execution is verified",
    "Verification applies to the execution result, not the execution mode",
]


# ── simulation_mode Compatibility Mapping ──────────────────────────────

SIMULATION_MODE_VERSION = "1.0.0"


def map_simulation_mode(simulation_mode: bool) -> str:
    """Map legacy simulation_mode bool to canonical ExecutionMode string.

    simulation_mode=True  → "simulated"
    simulation_mode=False → "real"
    """
    return "simulated" if simulation_mode else "real"


def map_execution_mode_to_simulation(execution_mode: str) -> bool:
    """Reverse map: canonical ExecutionMode → legacy simulation_mode bool.

    Only returns True for "simulated". All other modes (real, proposed,
    shadow, replay) return False because they are NOT simulation.
    """
    return execution_mode == "simulated"
