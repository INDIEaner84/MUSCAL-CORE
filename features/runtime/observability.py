from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from runtime.event_store import EventStore

from .models import ALL_RUNTIME_EVENTS, RUNTIME_EVENTS, INTERFACE_EVENTS


class RuntimeObservability:

    def __init__(self, event_store: Optional[EventStore] = None):
        self._store = event_store

    def emit(
        self,
        topic: str,
        payload: dict,
        execution_id: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        session_id: str = "",
        task_id: str = "",
    ) -> Optional[int]:
        if topic not in ALL_RUNTIME_EVENTS:
            raise ValueError(f"Unknown runtime event topic '{topic}'. Must be one of: {sorted(ALL_RUNTIME_EVENTS)}")
        if self._store is None:
            return None

        event: dict[str, Any] = {
            "topic": topic,
            "payload": {
                **payload,
                "session_id": session_id,
                "task_id": task_id,
            },
            "source": "features/runtime/observability.py",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": str(uuid.uuid4()),
            "execution_id": execution_id,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "causation_id": causation_id,
            "execution_mode": "real",
            "execution_state": "completed",
            "verification_state": "unverified",
            "receipt_id": "",
        }
        return self._store.append(event)

    def emit_started(self, correlation_id: str = "") -> Optional[int]:
        return self.emit("runtime.started", {"message": "Runtime initialized"}, correlation_id=correlation_id)

    def emit_session_created(self, session: Any) -> Optional[int]:
        return self.emit(
            "runtime.session.created",
            session.to_dict(),
            execution_id=session.execution_id,
            correlation_id=session.execution_id,
            session_id=session.session_id,
            task_id=session.task_id,
        )

    def emit_session_updated(self, session: Any) -> Optional[int]:
        return self.emit(
            "runtime.session.updated",
            session.to_dict(),
            execution_id=session.execution_id,
            correlation_id=session.execution_id,
            session_id=session.session_id,
            task_id=session.task_id,
        )

    def emit_session_restored(self, session: Any) -> Optional[int]:
        return self.emit(
            "runtime.session.restored",
            session.to_dict(),
            execution_id=session.execution_id,
            correlation_id=session.execution_id,
            session_id=session.session_id,
            task_id=session.task_id,
        )

    def emit_checkpoint_created(self, checkpoint: Any) -> Optional[int]:
        return self.emit(
            "runtime.checkpoint.created",
            checkpoint.to_dict(),
            execution_id=checkpoint.execution_id,
            correlation_id=checkpoint.execution_id,
            session_id=checkpoint.session_id,
            task_id=checkpoint.task_id,
        )

    def emit_execution_started(self, execution_id: str, task_id: str = "",
                                session_id: str = "") -> Optional[int]:
        return self.emit(
            "runtime.execution.started",
            {"execution_id": execution_id, "task_id": task_id, "session_id": session_id},
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
        )

    def emit_execution_completed(self, execution_id: str, task_id: str = "",
                                  session_id: str = "", result: Optional[dict] = None) -> Optional[int]:
        return self.emit(
            "runtime.execution.completed",
            {"execution_id": execution_id, "task_id": task_id,
             "session_id": session_id, "result": result or {}},
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
        )

    def emit_execution_failed(self, execution_id: str, task_id: str = "",
                               session_id: str = "", error: str = "") -> Optional[int]:
        return self.emit(
            "runtime.execution.failed",
            {"execution_id": execution_id, "task_id": task_id,
             "session_id": session_id, "error": error},
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
        )

    def emit_execution_interrupted(self, execution_id: str, task_id: str = "",
                                    session_id: str = "", reason: str = "") -> Optional[int]:
        return self.emit(
            "runtime.execution.interrupted",
            {"execution_id": execution_id, "task_id": task_id,
             "session_id": session_id, "reason": reason},
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
        )

    def emit_recovery_started(self, execution_id: str, task_id: str = "",
                               session_id: str = "", strategy: str = "") -> Optional[int]:
        return self.emit(
            "runtime.recovery.started",
            {"execution_id": execution_id, "task_id": task_id,
             "session_id": session_id, "strategy": strategy},
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
        )

    def emit_recovery_completed(self, execution_id: str, task_id: str = "",
                                  session_id: str = "", result: str = "") -> Optional[int]:
        return self.emit(
            "runtime.recovery.completed",
            {"execution_id": execution_id, "task_id": task_id,
             "session_id": session_id, "result": result},
            execution_id=execution_id,
            task_id=task_id,
            session_id=session_id,
        )

    def emit_knowledge_candidate_created(self, candidate: Any,
                                          execution_id: str = "",
                                          task_id: str = "") -> Optional[int]:
        return self.emit(
            "knowledge.candidate.created",
            candidate.to_dict() if hasattr(candidate, "to_dict") else candidate,
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_knowledge_candidate_validated(self, candidate: Any,
                                            execution_id: str = "",
                                            task_id: str = "") -> Optional[int]:
        return self.emit(
            "knowledge.candidate.validated",
            candidate.to_dict() if hasattr(candidate, "to_dict") else candidate,
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_knowledge_candidate_rejected(self, candidate: Any,
                                           execution_id: str = "",
                                           task_id: str = "") -> Optional[int]:
        return self.emit(
            "knowledge.candidate.rejected",
            candidate.to_dict() if hasattr(candidate, "to_dict") else candidate,
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_knowledge_retrieval_requested(self, context: str,
                                             result_count: int = 0,
                                             execution_id: str = "",
                                             task_id: str = "") -> Optional[int]:
        return self.emit(
            "knowledge.retrieval.requested",
            {"context": context[:500], "result_count": result_count},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_optimization_evaluated(self, result: Any,
                                     execution_id: str = "",
                                     task_id: str = "") -> Optional[int]:
        return self.emit(
            "optimization.execution.evaluated",
            result.to_dict() if hasattr(result, "to_dict") else result,
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_agent_profile_updated(self, agent_id: str,
                                    profile: Any,
                                    execution_id: str = "",
                                    task_id: str = "") -> Optional[int]:
        return self.emit(
            "optimization.agent.profile.updated",
            {"agent_id": agent_id, "profile": profile.to_dict() if hasattr(profile, "to_dict") else profile},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_selection_recommended(self, recommendation: Any,
                                    execution_id: str = "",
                                    task_id: str = "") -> Optional[int]:
        return self.emit(
            "optimization.selection.recommended",
            recommendation.to_dict() if hasattr(recommendation, "to_dict") else recommendation,
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_workflow_improved(self, recommendation: Any,
                                execution_id: str = "",
                                task_id: str = "") -> Optional[int]:
        return self.emit(
            "optimization.workflow.improved",
            recommendation.to_dict() if hasattr(recommendation, "to_dict") else recommendation,
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_tool_requested(self, tool_id: str, action: str,
                             execution_id: str = "",
                             task_id: str = "") -> Optional[int]:
        return self.emit(
            "tool.requested",
            {"tool_id": tool_id, "action": action},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_tool_approved(self, tool_id: str, action: str,
                            execution_id: str = "",
                            task_id: str = "") -> Optional[int]:
        return self.emit(
            "tool.approved",
            {"tool_id": tool_id, "action": action},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_tool_denied(self, tool_id: str, action: str, reason: str = "",
                          execution_id: str = "",
                          task_id: str = "") -> Optional[int]:
        return self.emit(
            "tool.denied",
            {"tool_id": tool_id, "action": action, "reason": reason},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_tool_executed(self, tool_id: str, action: str, result: Any,
                            execution_id: str = "",
                            task_id: str = "") -> Optional[int]:
        return self.emit(
            "tool.executed",
            {"tool_id": tool_id, "action": action,
             "result": result.to_dict() if hasattr(result, "to_dict") else str(result)},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_tool_failed(self, tool_id: str, action: str, error: str,
                          execution_id: str = "",
                          task_id: str = "") -> Optional[int]:
        return self.emit(
            "tool.failed",
            {"tool_id": tool_id, "action": action, "error": error},
            execution_id=execution_id,
            correlation_id=execution_id,
            task_id=task_id,
        )

    def emit_kernel_intent_created(self, intent: Any,
                                    execution_id: str = "",
                                    task_id: str = "") -> Optional[int]:
        return self.emit(
            "kernel.intent.created",
            intent.to_dict() if hasattr(intent, "to_dict") else intent,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_kernel_goal_created(self, goals: Any,
                                  execution_id: str = "",
                                  task_id: str = "") -> Optional[int]:
        return self.emit(
            "kernel.goal.created",
            goals.to_dict() if hasattr(goals, "to_dict") else goals,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_kernel_context_built(self, context: Any,
                                   execution_id: str = "",
                                   task_id: str = "") -> Optional[int]:
        return self.emit(
            "kernel.context.built",
            context.to_dict() if hasattr(context, "to_dict") else context,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_kernel_strategy_selected(self, strategy: Any,
                                       execution_id: str = "",
                                       task_id: str = "") -> Optional[int]:
        return self.emit(
            "kernel.strategy.selected",
            strategy.to_dict() if hasattr(strategy, "to_dict") else strategy,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_kernel_pipeline_completed(self, result: Any,
                                        execution_id: str = "",
                                        task_id: str = "") -> Optional[int]:
        return self.emit(
            "kernel.pipeline.completed",
            result.to_dict() if hasattr(result, "to_dict") else result,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_created(self, entry: Any,
                             execution_id: str = "",
                             task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.created",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_classified(self, entry: Any,
                                execution_id: str = "",
                                task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.classified",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_retrieved(self, context: Any,
                               execution_id: str = "",
                               task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.retrieved",
            context.to_dict() if hasattr(context, "to_dict") else context,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_consolidated(self, entry: Any,
                                  execution_id: str = "",
                                  task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.consolidated",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_promoted(self, entry: Any,
                              execution_id: str = "",
                              task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.promoted",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_persisted(self, entry: Any,
                               execution_id: str = "",
                               task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.persisted",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_validation_started(self, entry_id: str, reasons: list[str],
                                        execution_id: str = "",
                                        task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.validation.started",
            {"entry_id": entry_id, "reasons": reasons},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_validation_completed(self, entry: Any,
                                          execution_id: str = "",
                                          task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.validation.completed",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_lifecycle_changed(self, entry: Any,
                                       execution_id: str = "",
                                       task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.lifecycle.changed",
            entry.to_dict() if hasattr(entry, "to_dict") else entry,
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_memory_consolidation_completed(self, entries: list[Any],
                                             execution_id: str = "",
                                             task_id: str = "") -> Optional[int]:
        return self.emit(
            "memory.consolidation.completed",
            {"count": len(entries),
             "entries": [e.to_dict() if hasattr(e, "to_dict") else e for e in entries]},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_interface_requested(self, interface: str, action: str,
                                  request_id: str = "",
                                  execution_id: str = "",
                                  task_id: str = "") -> Optional[int]:
        return self.emit(
            "interface.requested",
            {"interface": interface, "action": action, "request_id": request_id},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_interface_approved(self, interface: str, action: str,
                                 request_id: str = "",
                                 execution_id: str = "",
                                 task_id: str = "") -> Optional[int]:
        return self.emit(
            "interface.approved",
            {"interface": interface, "action": action, "request_id": request_id},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_interface_executed(self, interface: str, action: str,
                                 request_id: str = "",
                                 success: bool = True,
                                 duration: float = 0.0,
                                 execution_id: str = "",
                                 task_id: str = "") -> Optional[int]:
        return self.emit(
            "interface.executed",
            {"interface": interface, "action": action, "request_id": request_id,
             "success": success, "duration": duration},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_interface_failed(self, interface: str, action: str,
                               request_id: str = "",
                               error: str = "",
                               execution_id: str = "",
                               task_id: str = "") -> Optional[int]:
        return self.emit(
            "interface.failed",
            {"interface": interface, "action": action, "request_id": request_id, "error": error},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )

    def emit_interface_verified(self, interface: str, action: str,
                                 request_id: str = "",
                                 verification_state: str = "VERIFIED",
                                 execution_id: str = "",
                                 task_id: str = "") -> Optional[int]:
        return self.emit(
            "interface.verified",
            {"interface": interface, "action": action, "request_id": request_id,
             "verification_state": verification_state},
            execution_id=execution_id, correlation_id=execution_id, task_id=task_id,
        )
