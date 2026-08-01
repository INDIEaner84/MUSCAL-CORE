from __future__ import annotations

import hashlib
import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from features.identity.uuid7 import uuid7
from features.provenance.mcpl_events import (
    MCPLEventType,
    create_provenance_event,
    get_event_mapping,
    validate_event_mapping,
)
from features.provenance.mcpl_schema import (
    MCPL_SCHEMA_VERSION,
    ProvenanceRecord,
    _now_iso,
)

log = logging.getLogger("muscal.mcpl.emitter")


# ---------------------------------------------------------------------------
# Integrity helpers
# ---------------------------------------------------------------------------

def compute_record_hash(record: ProvenanceRecord) -> str:
    raw = json.dumps(record.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def compute_previous_hash(previous_record: Optional[ProvenanceRecord] = None) -> str:
    if previous_record is None:
        return ""
    return compute_record_hash(previous_record)


# ---------------------------------------------------------------------------
# Event emitter
# ---------------------------------------------------------------------------

class MCPLEmitter:
    """Provenance event emitter — thread-safe, non-breaking addition.

    Collects ProvenanceRecord events.  Does NOT persist; persistence is
    handled by MCPLStore (separation of concerns).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: List[ProvenanceRecord] = []
        self._listeners: List[Callable[[ProvenanceRecord], None]] = []
        self._previous_hash: Optional[ProvenanceRecord] = None

    def add_listener(self, listener: Callable[[ProvenanceRecord], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[ProvenanceRecord], None]) -> None:
        with self._lock:
            self._listeners = [l for l in self._listeners if l is not listener]

    def emit(
        self,
        event_type: MCPLEventType,
        *,
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
        actor: Optional[Dict[str, Any]] = None,
        subject: Optional[Dict[str, Any]] = None,
        causal_links: Optional[List[Dict[str, Any]]] = None,
        payload: Optional[Dict[str, Any]] = None,
        retention: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRecord:
        record = create_provenance_event(
            event_type,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor=actor,
            subject=subject,
            causal_links=causal_links,
            payload=payload,
            retention=retention,
        )

        errors = validate_event_mapping(record)
        if errors:
            log.warning("MCPL event validation failed for %s: %s", event_type.value, errors)

        previous_hash = compute_previous_hash(self._previous_hash)
        record.integrity = {
            "previous_hash": previous_hash,
        }

        record_hash = compute_record_hash(record)
        record.integrity["hash"] = record_hash

        with self._lock:
            self._events.append(record)
            self._previous_hash = record

        for listener in self._listeners:
            try:
                listener(record)
            except Exception as exc:
                log.error("MCPL listener error: %s", exc)

        return record

    def emit_intent_created(
        self,
        intent_id: str,
        *,
        description: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        tenant_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.INTENT_CREATED,
            parent_id="",
            causation_id=causation_id or intent_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "Intent", "id": intent_id},
            payload={"description": description, **(metadata or {})},
        )

    def emit_task_created(
        self,
        task_id: str,
        *,
        intent_id: str,
        description: str = "",
        agent_id: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.TASK_CREATED,
            parent_id=intent_id,
            causation_id=causation_id or intent_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "Task", "id": task_id},
            payload={"description": description, "agent_id": agent_id},
        )

    def emit_model_output(
        self,
        output_id: str,
        *,
        model_id: str,
        agent_id: str,
        candidates: List[str],
        output_hash: str = "",
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
        prompt_hash: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.MODEL_OUTPUT,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "Model", "id": model_id},
            subject={"type": "ModelOutput", "id": output_id},
            payload={
                "output_id": output_id,
                "model_id": model_id,
                "agent_id": agent_id,
                "candidates": candidates,
                "output_hash": output_hash,
                "prompt_hash": prompt_hash,
            },
        )

    def emit_decision(
        self,
        decision_type: MCPLEventType,
        decision_id: str,
        *,
        task_id: str = "",
        agent_id: str = "",
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRecord:
        return self.emit(
            decision_type,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "Agent", "id": agent_id} if agent_id else {"type": "system"},
            subject={"type": "Decision", "id": decision_id},
            payload={
                "decision_id": decision_id,
                "task_id": task_id,
                **(payload or {}),
            },
        )

    def emit_execution_started(
        self,
        execution_id: str,
        *,
        task_id: str,
        tool_name: str,
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.EXECUTION_STARTED,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "Execution", "id": execution_id},
            payload={"task_id": task_id, "tool_name": tool_name},
        )

    def emit_execution_completed(
        self,
        execution_id: str,
        *,
        duration_ms: float = 0.0,
        success: bool = True,
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        event_type = MCPLEventType.EXECUTION_COMPLETED if success else MCPLEventType.EXECUTION_FAILED
        return self.emit(
            event_type,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "Execution", "id": execution_id},
            payload={"duration_ms": duration_ms, "success": success},
        )

    def emit_verification_result(
        self,
        verification_id: str,
        *,
        subject_id: str,
        subject_type: str,
        verifier_type: str,
        status: str,
        confidence: float = 0.0,
        evidence_ref: str = "",
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.VERIFICATION_RESULT,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "Verifier", "id": verifier_type},
            subject={"type": "Verification", "id": verification_id},
            payload={
                "verification_id": verification_id,
                "subject_id": subject_id,
                "subject_type": subject_type,
                "verifier_type": verifier_type,
                "status": status,
                "confidence": confidence,
                "evidence_ref": evidence_ref,
            },
        )

    def emit_tool_call(
        self,
        tool_call_id: str,
        *,
        execution_id: str,
        tool_name: str,
        args_hash: str = "",
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.TOOL_CALL,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "ToolCall", "id": tool_call_id},
            payload={
                "tool_call_id": tool_call_id,
                "execution_id": execution_id,
                "tool_name": tool_name,
                "args_hash": args_hash,
            },
        )

    def emit_tool_call_result(
        self,
        tool_call_id: str,
        *,
        result_hash: str = "",
        success: bool = True,
        duration_ms: float = 0.0,
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.TOOL_CALL_RESULT,
            parent_id=parent_id,
            causation_id=causation_id or parent_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "ToolCall", "id": tool_call_id},
            payload={
                "tool_call_id": tool_call_id,
                "result_hash": result_hash,
                "success": success,
                "duration_ms": duration_ms,
            },
        )

    def emit_artifact_created(
        self,
        artifact_id: str,
        *,
        name: str,
        content_hash: str,
        mime_type: str = "",
        tool_call_id: str = "",
        execution_id: str = "",
        parent_id: str = "",
        causation_id: str = "",
        correlation_id: str = "",
        tenant_id: str = "",
    ) -> ProvenanceRecord:
        return self.emit(
            MCPLEventType.ARTIFACT_CREATED,
            parent_id=parent_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor={"type": "system", "id": "kernel"},
            subject={"type": "Artifact", "id": artifact_id},
            payload={
                "artifact_id": artifact_id,
                "name": name,
                "content_hash": content_hash,
                "mime_type": mime_type,
                "tool_call_id": tool_call_id,
                "execution_id": execution_id,
            },
        )

    def get_events(self) -> List[ProvenanceRecord]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._previous_hash = None

    def event_count(self) -> int:
        with self._lock:
            return len(self._events)


_emitter: Optional[MCPLEmitter] = None
_emitter_lock = threading.Lock()


def get_emitter() -> MCPLEmitter:
    global _emitter
    if _emitter is None:
        with _emitter_lock:
            if _emitter is None:
                _emitter = MCPLEmitter()
    return _emitter


def reset_emitter() -> None:
    global _emitter
    with _emitter_lock:
        _emitter = None
