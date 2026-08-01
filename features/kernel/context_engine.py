from __future__ import annotations

from typing import Any, Optional

from .models import UnifiedContext


class ContextEngine:

    def __init__(self):
        self._runtime_state_provider = None
        self._knowledge_provider = None
        self._session_provider = None
        self._profile_provider = None
        self._memory_fabric_provider = None

    def register_runtime_provider(self, provider: Any) -> None:
        self._runtime_state_provider = provider

    def register_knowledge_provider(self, provider: Any) -> None:
        self._knowledge_provider = provider

    def register_session_provider(self, provider: Any) -> None:
        self._session_provider = provider

    def register_profile_provider(self, provider: Any) -> None:
        self._profile_provider = provider

    def register_memory_fabric_provider(self, provider: Any) -> None:
        self._memory_fabric_provider = provider

    def build(self, task_analysis: Optional[Any] = None,
              execution_id: str = "",
              intent: Optional[Any] = None,
              goal: Optional[Any] = None) -> UnifiedContext:
        runtime_state = self._safe_call(self._runtime_state_provider, "get_state")
        if runtime_state is None:
            runtime_state = self._safe_call(self._runtime_state_provider, "compute")
        if runtime_state is None:
            runtime_state = {}

        knowledge = []
        if self._knowledge_provider is not None:
            ctx = " ".join(str(v) for v in (task_analysis or {}).values()) if task_analysis else ""
            if hasattr(self._knowledge_provider, "retrieve_relevant"):
                matches = self._knowledge_provider.retrieve_relevant(ctx[:200])
                knowledge = [m.to_dict() for m in matches] if matches else []

        session = None
        if self._session_provider is not None:
            if hasattr(self._session_provider, "get_session"):
                session = self._session_provider.get_session(execution_id)

        agent_profiles = []
        if self._profile_provider is not None:
            if hasattr(self._profile_provider, "get_all_profiles"):
                profiles = self._profile_provider.get_all_profiles()
                agent_profiles = [p.to_dict() for p in profiles] if profiles else []

        memory_context = None
        if self._memory_fabric_provider is not None:
            if hasattr(self._memory_fabric_provider, "retrieve_context"):
                intent_dict = intent.to_dict() if intent and hasattr(intent, "to_dict") else None
                goal_dict = goal.to_dict() if goal and hasattr(goal, "to_dict") else None
                analysis_dict = task_analysis.to_dict() if task_analysis and hasattr(task_analysis, "to_dict") else None
                mem_ctx = self._memory_fabric_provider.retrieve_context(
                    task=analysis_dict,
                    intent=intent_dict,
                    goal=goal_dict,
                    execution_id=execution_id,
                )
                memory_context = mem_ctx.to_dict()

        return UnifiedContext(
            runtime_state=runtime_state if isinstance(runtime_state, dict) else {},
            knowledge=knowledge,
            session=session.to_dict() if session and hasattr(session, "to_dict") else None,
            agent_profiles=agent_profiles,
            task_analysis=task_analysis.to_dict() if task_analysis and hasattr(task_analysis, "to_dict") else None,
            memory_context=memory_context,
            execution_id=execution_id,
        )

    def _safe_call(self, obj: Any, method: str, *args, **kwargs) -> Any:
        if obj is not None and hasattr(obj, method):
            try:
                return getattr(obj, method)(*args, **kwargs)
            except Exception:
                return None
        return None
