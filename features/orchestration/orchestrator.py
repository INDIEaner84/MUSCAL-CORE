from __future__ import annotations

from typing import Any, Optional

from ..bridge.task_contract import TaskContract
from .models import TaskAnalysis, SelectionResult, ExecutionPlan, ORCHESTRATION_EVENTS
from .task_analyzer import TaskAnalyzer
from .agent_selector import AgentSelector
from .planner import ExecutionPlanner
from .policy import OrchestrationPolicy


class CognitiveOrchestrator:

    def __init__(self, analyzer: Optional[TaskAnalyzer] = None,
                 selector: Optional[AgentSelector] = None,
                 planner: Optional[ExecutionPlanner] = None,
                 policy: Optional[OrchestrationPolicy] = None,
                 knowledge_context: Optional[str] = None,
                 event_emitter: Optional[Any] = None):
        self._analyzer = analyzer or TaskAnalyzer()
        self._selector = selector or AgentSelector()
        self._policy = policy or OrchestrationPolicy()
        self._planner = planner or ExecutionPlanner(policy=self._policy)
        self._knowledge_context = knowledge_context
        self._events = event_emitter
        self._kernel = None

    def attach_kernel(self, kernel: Any) -> None:
        self._kernel = kernel
        if hasattr(kernel, 'context_engine'):
            ctx_engine = kernel.context_engine
            ctx_engine.register_knowledge_provider(self._selector)
            if self._policy:
                ctx_engine.register_runtime_provider(self._policy)

    def analyze(self, task: TaskContract) -> TaskAnalysis:
        analysis = self._analyzer.analyze(task)
        self._emit("orchestration.task.analyzed", analysis.to_dict(),
                   task_id=task.id)
        return analysis

    def select_agent(self, analysis: TaskAnalysis) -> SelectionResult:
        result = self._selector.select(analysis, self._knowledge_context)
        self._emit("orchestration.agent.selected", result.to_dict(),
                   task_id=analysis.task_id)
        return result

    def create_plan(self, analysis: TaskAnalysis, selection: SelectionResult) -> ExecutionPlan:
        plan = self._planner.plan(analysis, selection)
        actions = [s.action for s in plan.steps]
        violations = self._policy.validate_plan_actions(actions, plan.autonomy_level)
        if violations:
            plan.risk_controls.extend(violations)
        self._emit("orchestration.plan.created", plan.to_dict(),
                   task_id=analysis.task_id)
        return plan

    def orchestrate(self, task: TaskContract) -> dict:
        if self._kernel is not None:
            return self._kernel.process(task)
        analysis = self.analyze(task)
        selection = self.select_agent(analysis)
        plan = self.create_plan(analysis, selection)
        return {
            "analysis": analysis.to_dict(),
            "selection": selection.to_dict(),
            "plan": plan.to_dict(),
        }

    def _emit(self, topic: str, payload: dict, task_id: str = "") -> None:
        if self._events is not None and hasattr(self._events, 'emit'):
            self._events.emit(topic, payload, task_id=task_id)
