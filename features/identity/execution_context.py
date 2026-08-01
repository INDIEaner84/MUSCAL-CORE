from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Any, Dict, Optional

from features.identity.reality import (
    ExecutionMode,
    ExecutionState,
    VerificationState,
    normalize_execution_mode,
    normalize_execution_state,
    normalize_verification_state,
    verify_state_transition,
    validate_state_transition,
    validate_execution_state_change,
    validate_verification_state_change,
    ValidationError,
)
from features.identity.uuid7 import uuid7

EXECUTION_CONTEXT_VERSION = "2.1.0"

_TRUST_FROZEN_FIELDS = frozenset({"execution_state", "verification_state"})


class ContextLifecycle(Enum):
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_VALID_LIFECYCLE_TRANSITIONS: Dict[ContextLifecycle, frozenset] = {
    ContextLifecycle.CREATED: frozenset({ContextLifecycle.ACTIVE, ContextLifecycle.CANCELLED}),
    ContextLifecycle.ACTIVE: frozenset({ContextLifecycle.COMPLETED, ContextLifecycle.FAILED, ContextLifecycle.CANCELLED}),
    ContextLifecycle.COMPLETED: frozenset(),
    ContextLifecycle.FAILED: frozenset(),
    ContextLifecycle.CANCELLED: frozenset(),
}


class ExecutionContext:
    __slots__ = (
        "_execution_id", "_correlation_id", "_causation_id",
        "_execution_mode", "_execution_state", "_verification_state",
        "_agent_id", "_model_id", "_request_id", "_lifecycle",
        "_intent_id", "_task_id",
    )

    def __init__(
        self,
        execution_id: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        execution_mode: str = "real",
        execution_state: str = "planned",
        verification_state: str = "unverified",
        agent_id: str = "",
        model_id: str = "",
        request_id: str = "",
        intent_id: str = "",
        task_id: str = "",
    ):
        self._execution_id = execution_id or uuid7()
        self._correlation_id = correlation_id
        self._causation_id = causation_id
        self._execution_mode = normalize_execution_mode(execution_mode)
        self._execution_state = normalize_execution_state(execution_state)
        self._verification_state = normalize_verification_state(verification_state)
        self._agent_id = agent_id
        self._model_id = model_id
        self._request_id = request_id
        self._intent_id = intent_id
        self._task_id = task_id
        self._lifecycle = "created"

    @property
    def execution_id(self) -> str:
        return self._execution_id

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    @property
    def causation_id(self) -> str:
        return self._causation_id

    @property
    def execution_mode(self) -> str:
        return self._execution_mode

    @property
    def execution_state(self) -> str:
        return self._execution_state

    @execution_state.setter
    def execution_state(self, value: str) -> None:
        raise ValidationError(
            "Direct assignment to execution_state is forbidden. "
            "Use transition_state() instead."
        )

    @property
    def verification_state(self) -> str:
        return self._verification_state

    @verification_state.setter
    def verification_state(self, value: str) -> None:
        raise ValidationError(
            "Direct assignment to verification_state is forbidden. "
            "Use set_verification() instead."
        )

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def intent_id(self) -> str:
        return self._intent_id

    @property
    def task_id(self) -> str:
        return self._task_id

    def transition_lifecycle(self, target: ContextLifecycle) -> None:
        current = ContextLifecycle(self._lifecycle)
        allowed = _VALID_LIFECYCLE_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            raise ValidationError(
                f"Invalid context lifecycle transition: {current.value} → {target.value}"
            )
        self._lifecycle = target.value

    @property
    def lifecycle(self) -> str:
        return self._lifecycle

    def transition_state(self, target_state: str) -> None:
        current = self._execution_state
        if not validate_execution_state_change(current, target_state):
            raise ValidationError(
                f"Invalid execution state transition: {current} → {target_state}"
            )
        if not validate_state_transition(self._execution_mode, target_state, self._verification_state):
            raise ValidationError(
                f"Invalid state: mode={self._execution_mode} "
                f"state={target_state} "
                f"verification={self._verification_state}"
            )
        object.__setattr__(self, "_execution_state", target_state)

    def set_verification(self, target_verification: str, evidence_receipt_id: str = "") -> None:
        if target_verification == "verified" and not evidence_receipt_id:
            raise ValidationError(
                "Cannot set verification to 'verified' without evidence_receipt_id"
            )
        current = self._verification_state
        if not validate_verification_state_change(current, target_verification):
            raise ValidationError(
                f"Invalid verification state transition: "
                f"{current} → {target_verification}"
            )
        if not validate_state_transition(self._execution_mode, self._execution_state, target_verification):
            raise ValidationError(
                f"Invalid state: mode={self._execution_mode} "
                f"state={self._execution_state} "
                f"verification={target_verification}"
            )
        object.__setattr__(self, "_verification_state", target_verification)

    def enrich_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(payload)
        enriched.setdefault("execution_id", self._execution_id)
        enriched.setdefault("correlation_id", self._correlation_id)
        enriched.setdefault("causation_id", self._causation_id)
        enriched.setdefault("execution_mode", self._execution_mode)
        enriched.setdefault("execution_state", self._execution_state)
        enriched.setdefault("verification_state", self._verification_state)
        if self._agent_id:
            enriched.setdefault("agent_id", self._agent_id)
        if self._model_id:
            enriched.setdefault("model_id", self._model_id)
        if self._request_id:
            enriched.setdefault("request_id", self._request_id)
        if self._intent_id:
            enriched.setdefault("intent_id", self._intent_id)
        if self._task_id:
            enriched.setdefault("task_id", self._task_id)
        return enriched

    @staticmethod
    def extract_from_payload(payload: Dict[str, Any]) -> ExecutionContext:
        ctx = object.__new__(ExecutionContext)
        object.__setattr__(ctx, "_execution_id", payload.get("execution_id", ""))
        object.__setattr__(ctx, "_correlation_id", payload.get("correlation_id", ""))
        object.__setattr__(ctx, "_causation_id", payload.get("causation_id", ""))
        object.__setattr__(ctx, "_execution_mode", normalize_execution_mode(payload.get("execution_mode", "real")))
        object.__setattr__(ctx, "_execution_state", normalize_execution_state(payload.get("execution_state", "planned")))
        object.__setattr__(ctx, "_verification_state", normalize_verification_state(payload.get("verification_state", "unverified")))
        object.__setattr__(ctx, "_agent_id", payload.get("agent_id", ""))
        object.__setattr__(ctx, "_model_id", payload.get("model_id", ""))
        object.__setattr__(ctx, "_request_id", payload.get("request_id", ""))
        object.__setattr__(ctx, "_intent_id", payload.get("intent_id", ""))
        object.__setattr__(ctx, "_task_id", payload.get("task_id", ""))
        object.__setattr__(ctx, "_lifecycle", "created")
        return ctx

    def to_dict(self) -> Dict[str, str]:
        d = {
            "execution_id": self._execution_id,
            "correlation_id": self._correlation_id,
            "causation_id": self._causation_id,
            "execution_mode": self._execution_mode,
            "execution_state": self._execution_state,
            "verification_state": self._verification_state,
        }
        if self._agent_id:
            d["agent_id"] = self._agent_id
        if self._model_id:
            d["model_id"] = self._model_id
        if self._request_id:
            d["request_id"] = self._request_id
        if self._intent_id:
            d["intent_id"] = self._intent_id
        if self._task_id:
            d["task_id"] = self._task_id
        return d

    def validate(self) -> None:
        verify_state_transition(self._execution_mode, self._execution_state, self._verification_state)


class ExecutionContextManager:
    def __init__(self) -> None:
        self._local = threading.local()
        self._lock = threading.Lock()

    def set_context(self, ctx: ExecutionContext) -> None:
        self._local.context = ctx

    def get_context(self) -> Optional[ExecutionContext]:
        return getattr(self._local, "context", None)

    def clear_context(self) -> None:
        if hasattr(self._local, "context"):
            del self._local.context

    def current_or_default(self) -> ExecutionContext:
        ctx = self.get_context()
        if ctx is not None:
            return ctx
        return ExecutionContext()

    def enrich_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.current_or_default().enrich_payload(payload)


_context_manager = ExecutionContextManager()


def get_context_manager() -> ExecutionContextManager:
    return _context_manager


def enrich_with_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _context_manager.enrich_payload(payload)



