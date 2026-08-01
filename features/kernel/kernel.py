from __future__ import annotations

from typing import Any, Optional

from ..bridge.task_contract import TaskContract
from ..orchestration.task_analyzer import TaskAnalyzer
from ..orchestration.agent_selector import AgentSelector
from ..orchestration.planner import ExecutionPlanner
from ..orchestration.policy import OrchestrationPolicy
from .models import Intent, GoalSet, UnifiedContext, Strategy
from .intent_engine import IntentEngine
from .goal_engine import GoalEngine
from .context_engine import ContextEngine
from .strategy_engine import StrategyEngine


class CognitiveKernel:

    def __init__(self, intent_engine: Optional[IntentEngine] = None,
                 goal_engine: Optional[GoalEngine] = None,
                 context_engine: Optional[ContextEngine] = None,
                 strategy_engine: Optional[StrategyEngine] = None,
                 task_analyzer: Optional[TaskAnalyzer] = None,
                 agent_selector: Optional[AgentSelector] = None,
                 planner: Optional[ExecutionPlanner] = None,
                 policy: Optional[OrchestrationPolicy] = None,
                 event_emitter: Optional[Any] = None):
        self._intent = intent_engine or IntentEngine()
        self._goals = goal_engine or GoalEngine()
        self._context = context_engine or ContextEngine()
        self._strategy = strategy_engine or StrategyEngine()
        self._analyzer = task_analyzer or TaskAnalyzer()
        self._selector = agent_selector or AgentSelector()
        self._policy = policy or OrchestrationPolicy()
        self._planner = planner or ExecutionPlanner(policy=self._policy)
        self._events = event_emitter

    def process(self, task: TaskContract) -> dict:
        execution_id = task.id

        intent = self._intent.create(task)
        self._emit("kernel.intent.created", intent, execution_id, task.id)

        goals = self._goals.create(intent)
        self._emit("kernel.goal.created", goals, execution_id, task.id)

        task_analysis = self._analyzer.analyze(task)
        ctx = self._context.build(task_analysis=task_analysis, execution_id=execution_id,
                                   intent=intent, goal=goals)
        self._emit("kernel.context.built", ctx, execution_id, task.id)

        strategy = self._strategy.select(intent, goals, context=ctx)
        self._emit("kernel.strategy.selected", strategy, execution_id, task.id)

        selection = self._selector.select(task_analysis, knowledge_context=str(ctx.knowledge))
        plan = self._planner.plan(task_analysis, selection)

        actions = [s.action for s in plan.steps]
        violations = self._policy.validate_plan_actions(actions, plan.autonomy_level)
        if violations:
            plan.risk_controls.extend(violations)

        result = {
            "intent": intent.to_dict(),
            "goals": goals.to_dict(),
            "context": ctx.to_dict(),
            "strategy": strategy.to_dict(),
            "analysis": task_analysis.to_dict(),
            "selection": selection.to_dict(),
            "plan": plan.to_dict(),
        }
        self._emit("kernel.pipeline.completed", result, execution_id, task.id)
        return result

    def _emit(self, topic: str, data: Any, execution_id: str = "", task_id: str = "") -> None:
        if self._events is not None and hasattr(self._events, 'emit'):
            payload = data.to_dict() if hasattr(data, "to_dict") else data
            self._events.emit(topic, payload, execution_id=execution_id, task_id=task_id)

    @property
    def context_engine(self) -> ContextEngine:
        return self._context
