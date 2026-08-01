from __future__ import annotations

import uuid

import pytest

from features.bridge.task_contract import TaskContract
from features.kernel.models import (
    Intent, Goal, GoalSet, GoalPriority, UnifiedContext, Strategy, StrategyType,
)
from features.kernel.intent_engine import IntentEngine
from features.kernel.goal_engine import GoalEngine
from features.kernel.context_engine import ContextEngine
from features.kernel.strategy_engine import StrategyEngine
from features.kernel.kernel import CognitiveKernel


# ── helpers ──────────────────────────────────────────────────────────────

def make_task(objective: str = "implement feature X",
              constraints: list[str] | None = None,
              expected_output: str | None = None,
              task_id: str = "task-001") -> TaskContract:
    return TaskContract(
        id=task_id,
        project="muscal-core",
        objective=objective,
        constraints=constraints or [],
        expected_output=expected_output,
        verification_required=True,
    )


# ══════════════════════════════════════════════════════════════════════════
# 1. Models (~12 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestIntentModel:

    def test_create(self):
        intent = Intent(
            task_id="t1", type="implementation", goal="do thing",
            constraints=[], priority="high", risk="low",
            required_capabilities=["code"], expected_outcome="done",
            confidence=0.8,
        )
        assert intent.task_id == "t1"
        assert intent.type == "implementation"
        assert intent.confidence == 0.8

    def test_to_dict(self):
        intent = Intent(
            task_id="t1", type="repair", goal="fix crash",
            constraints=["no prod"], priority="critical", risk="critical",
            required_capabilities=["debugging"], expected_outcome="fixed",
            confidence=0.95, reasoning="urgent",
        )
        d = intent.to_dict()
        assert d["intent"]["task_id"] == "t1"
        assert d["intent"]["type"] == "repair"
        assert d["intent"]["priority"] == "critical"
        assert d["intent"]["risk"] == "critical"
        assert d["intent"]["reasoning"] == "urgent"

    def test_default_reasoning(self):
        intent = Intent(
            task_id="t1", type="validation", goal="test coverage",
            constraints=[], priority="normal", risk="low",
            required_capabilities=["testing"], expected_outcome="pass",
            confidence=0.7,
        )
        assert intent.reasoning == ""


class TestGoalPriorityEnum:

    def test_values(self):
        assert GoalPriority.PRIMARY.value == "PRIMARY"
        assert GoalPriority.SECONDARY.value == "SECONDARY"
        assert GoalPriority.SAFETY.value == "SAFETY"
        assert GoalPriority.VERIFICATION.value == "VERIFICATION"
        assert GoalPriority.KNOWLEDGE.value == "KNOWLEDGE"
        assert GoalPriority.OPTIMIZATION.value == "OPTIMIZATION"

    def test_is_enum(self):
        assert isinstance(GoalPriority.PRIMARY, GoalPriority)


class TestGoalModel:

    def test_create(self):
        g = Goal(id="g1", description="test goal", priority=GoalPriority.PRIMARY)
        assert g.id == "g1"
        assert g.status == "pending"

    def test_to_dict(self):
        g = Goal(id="g2", description="verify", priority=GoalPriority.VERIFICATION,
                 dependencies=["g1"], status="active")
        d = g.to_dict()
        assert d["goal"]["id"] == "g2"
        assert d["goal"]["priority"] == "VERIFICATION"
        assert d["goal"]["dependencies"] == ["g1"]
        assert d["goal"]["status"] == "active"

    def test_default_dependencies_and_status(self):
        g = Goal(id="g3", description="learn", priority=GoalPriority.KNOWLEDGE)
        assert g.dependencies == []
        assert g.status == "pending"


class TestGoalSetModel:

    def test_create(self):
        gs = GoalSet()
        assert gs.goals == []

    def test_by_priority(self):
        g1 = Goal(id="g1", description="primary", priority=GoalPriority.PRIMARY)
        g2 = Goal(id="g2", description="safety", priority=GoalPriority.SAFETY)
        gs = GoalSet(goals=[g1, g2])
        primary = gs.by_priority(GoalPriority.PRIMARY)
        assert len(primary) == 1
        assert primary[0].id == "g1"

    def test_by_priority_empty(self):
        g = Goal(id="g1", description="p", priority=GoalPriority.PRIMARY)
        gs = GoalSet(goals=[g])
        assert gs.by_priority(GoalPriority.OPTIMIZATION) == []

    def test_to_dict(self):
        g1 = Goal(id="g1", description="primary", priority=GoalPriority.PRIMARY)
        g2 = Goal(id="g2", description="verify", priority=GoalPriority.VERIFICATION)
        gs = GoalSet(goals=[g1, g2])
        d = gs.to_dict()
        assert len(d["goal_set"]["goals"]) == 2
        assert d["goal_set"]["goals"][0]["goal"]["id"] == "g1"


class TestUnifiedContextModel:

    def test_create(self):
        ctx = UnifiedContext()
        assert ctx.runtime_state == {}
        assert ctx.knowledge == []
        assert ctx.session is None
        assert ctx.agent_profiles == []
        assert ctx.task_analysis is None
        assert ctx.event_history == []
        assert ctx.execution_id == ""

    def test_to_dict(self):
        ctx = UnifiedContext(
            runtime_state={"cpu": 0.5},
            knowledge=[{"key": "val"}],
            session={"id": "s1"},
            agent_profiles=[{"name": "agent1"}],
            task_analysis={"cat": "bug"},
            event_history=[{"ev": "1"}],
            execution_id="ex-1",
        )
        d = ctx.to_dict()
        assert d["unified_context"]["runtime_state"] == {"cpu": 0.5}
        assert d["unified_context"]["session"] == {"id": "s1"}
        assert d["unified_context"]["event_history_count"] == 1
        assert d["unified_context"]["execution_id"] == "ex-1"

    def test_to_dict_empty(self):
        ctx = UnifiedContext()
        d = ctx.to_dict()
        assert d["unified_context"]["event_history_count"] == 0
        assert d["unified_context"]["execution_id"] == ""


class TestStrategyModel:

    def test_create(self):
        s = Strategy(type=StrategyType.ARCHITECTURE, description="design",
                     reasoning="best approach", recommended_autonomy="A2")
        assert s.type == StrategyType.ARCHITECTURE
        assert s.recommended_autonomy == "A2"

    def test_to_dict(self):
        s = Strategy(type=StrategyType.REPAIR, description="fix it",
                     reasoning="low risk", recommended_autonomy="A3")
        d = s.to_dict()
        assert d["strategy"]["type"] == "repair"
        assert d["strategy"]["reasoning"] == "low risk"

    def test_strategy_type_values(self):
        assert StrategyType.ARCHITECTURE.value == "architecture"
        assert StrategyType.IMPLEMENTATION.value == "implementation"
        assert StrategyType.INVESTIGATION.value == "investigation"
        assert StrategyType.REPAIR.value == "repair"
        assert StrategyType.VALIDATION.value == "validation"
        assert StrategyType.DOCUMENTATION.value == "documentation"


# ══════════════════════════════════════════════════════════════════════════
# 2. IntentEngine (~12 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestIntentEngine:

    def _engine(self) -> IntentEngine:
        return IntentEngine()

    def test_create_returns_intent(self):
        task = make_task("implement the login flow")
        intent = self._engine().create(task)
        assert isinstance(intent, Intent)
        assert intent.task_id == "task-001"
        assert intent.goal == "implement the login flow"

    def test_classify_architecture(self):
        engine = self._engine()
        assert engine._classify_type("need to architect the system") == "architecture"
        assert engine._classify_type("design the database schema") == "architecture"
        assert engine._classify_type("structure the codebase") == "architecture"

    def test_classify_implementation(self):
        engine = self._engine()
        assert engine._classify_type("implement the API") == "implementation"
        assert engine._classify_type("add new endpoint") == "implementation"
        assert engine._classify_type("create the module") == "implementation"
        assert engine._classify_type("feature: user login") == "implementation"

    def test_classify_investigation(self):
        engine = self._engine()
        assert engine._classify_type("investigate the crash") == "investigation"
        assert engine._classify_type("analyze performance") == "investigation"
        assert engine._classify_type("audit security") == "investigation"
        assert engine._classify_type("root cause of failure") == "investigation"

    def test_classify_repair(self):
        engine = self._engine()
        assert engine._classify_type("fix the login bug") == "repair"
        assert engine._classify_type("repair the broken test") == "repair"
        assert engine._classify_type("error handling missing") == "repair"
        assert engine._classify_type("crash on startup") == "repair"

    def test_classify_validation(self):
        engine = self._engine()
        assert engine._classify_type("test the module") == "validation"
        assert engine._classify_type("verify the output") == "validation"
        assert engine._classify_type("validate the schema") == "validation"
        assert engine._classify_type("run coverage") == "validation"

    def test_classify_documentation(self):
        engine = self._engine()
        assert engine._classify_type("write docs for API") == "documentation"
        assert engine._classify_type("update readme") == "documentation"
        assert engine._classify_type("document the protocol") == "documentation"

    def test_classify_default(self):
        engine = self._engine()
        assert engine._classify_type("random thing to do") == "implementation"

    def test_determine_priority_critical(self):
        task = make_task("critical production outage needs fix")
        assert self._engine()._determine_priority(task) == "critical"
        task2 = make_task("urgent: p0 blocker in main")
        assert self._engine()._determine_priority(task2) == "critical"

    def test_determine_priority_high(self):
        task = make_task("high priority feature for release")
        assert self._engine()._determine_priority(task) == "high"
        task2 = make_task("important security update p1")
        assert self._engine()._determine_priority(task2) == "high"

    def test_determine_priority_medium(self):
        task = make_task("medium enhancement p2")
        assert self._engine()._determine_priority(task) == "medium"

    def test_determine_priority_normal(self):
        task = make_task("write some documentation")
        assert self._engine()._determine_priority(task) == "normal"

    def test_determine_risk_architecture(self):
        engine = self._engine()
        task = make_task("architect the system")
        assert engine._determine_risk(task, "architecture") == "high"

    def test_determine_risk_repair_production(self):
        engine = self._engine()
        task = make_task("fix the bug", constraints=["production impact"])
        assert engine._determine_risk(task, "repair") == "critical"

    def test_determine_risk_with_constraints(self):
        engine = self._engine()
        task = make_task("implement feature", constraints=["must be fast"])
        assert engine._determine_risk(task, "implementation") == "medium"

    def test_determine_risk_default(self):
        engine = self._engine()
        task = make_task("write docs")
        assert engine._determine_risk(task, "documentation") == "low"

    def test_determine_capabilities(self):
        engine = self._engine()
        assert "architecture" in engine._determine_capabilities("architecture", "design")
        assert "code_generation" in engine._determine_capabilities("implementation", "add")
        assert "debugging" in engine._determine_capabilities("repair", "fix")
        assert "testing" in engine._determine_capabilities("validation", "test")
        assert "documentation" in engine._determine_capabilities("documentation", "doc")
        assert "code_analysis" in engine._determine_capabilities("investigation", "audit")

    def test_compute_confidence_base(self):
        task = make_task("hi")
        assert self._engine()._compute_confidence(task) == 0.5

    def test_compute_confidence_long_objective(self):
        task = make_task("a" * 25)
        assert self._engine()._compute_confidence(task) == 0.7

    def test_compute_confidence_with_expected(self):
        task = make_task("a" * 25, expected_output="working code")
        assert self._engine()._compute_confidence(task) == 0.85

    def test_compute_confidence_with_constraints(self):
        task = make_task("a" * 25, constraints=["fast"], expected_output="working code")
        assert self._engine()._compute_confidence(task) == 0.95

    def test_compute_confidence_capped(self):
        task = make_task("a" * 25, constraints=["a", "b"], expected_output="x")
        assert self._engine()._compute_confidence(task) <= 1.0

    def test_full_intent_creation_integration(self):
        task = make_task(
            "implement a new authentication module",
            constraints=["must be secure", "follow OAuth2"],
            expected_output="working auth module",
        )
        intent = self._engine().create(task)
        assert intent.task_id == "task-001"
        assert intent.type == "implementation"
        assert intent.priority == "normal"
        assert intent.risk == "medium"
        assert "code_generation" in intent.required_capabilities
        assert intent.expected_outcome == "working auth module"
        assert 0.5 < intent.confidence <= 1.0
        assert intent.constraints == ["must be secure", "follow OAuth2"]


# ══════════════════════════════════════════════════════════════════════════
# 3. GoalEngine (~12 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestGoalEngine:

    def _make_intent(self, type: str = "implementation",
                     priority: str = "normal",
                     risk: str = "low",
                     constraints: list[str] | None = None,
                     goal: str = "do the thing") -> Intent:
        return Intent(
            task_id="t1", type=type, goal=goal,
            constraints=constraints or [],
            priority=priority, risk=risk,
            required_capabilities=["code"],
            expected_outcome="done",
            confidence=0.8,
        )

    def test_create_returns_goalset(self):
        engine = GoalEngine()
        gs = engine.create(self._make_intent())
        assert isinstance(gs, GoalSet)

    def test_always_has_primary_goal(self):
        gs = GoalEngine().create(self._make_intent())
        assert len(gs.by_priority(GoalPriority.PRIMARY)) == 1

    def test_primary_goal_description(self):
        gs = GoalEngine().create(self._make_intent(type="repair", goal="fix the crash"))
        primary = gs.by_priority(GoalPriority.PRIMARY)[0]
        assert "repair" in primary.description
        assert "fix the crash" in primary.description

    def test_always_has_verification_goal(self):
        gs = GoalEngine().create(self._make_intent())
        assert len(gs.by_priority(GoalPriority.VERIFICATION)) == 1

    def test_verification_depends_on_primary(self):
        gs = GoalEngine().create(self._make_intent())
        primary = gs.by_priority(GoalPriority.PRIMARY)[0]
        verification = gs.by_priority(GoalPriority.VERIFICATION)[0]
        assert primary.id in verification.dependencies

    def test_always_has_knowledge_goal(self):
        gs = GoalEngine().create(self._make_intent())
        assert len(gs.by_priority(GoalPriority.KNOWLEDGE)) == 1

    def test_safety_goal_for_high_risk(self):
        gs = GoalEngine().create(self._make_intent(risk="high"))
        assert len(gs.by_priority(GoalPriority.SAFETY)) == 1

    def test_safety_goal_for_critical_risk(self):
        gs = GoalEngine().create(self._make_intent(risk="critical"))
        assert len(gs.by_priority(GoalPriority.SAFETY)) == 1

    def test_no_safety_goal_for_low_risk(self):
        gs = GoalEngine().create(self._make_intent(risk="low"))
        assert len(gs.by_priority(GoalPriority.SAFETY)) == 0

    def test_optimization_goal_for_high_priority(self):
        gs = GoalEngine().create(self._make_intent(priority="high"))
        assert len(gs.by_priority(GoalPriority.OPTIMIZATION)) == 1

    def test_optimization_goal_for_critical_priority(self):
        gs = GoalEngine().create(self._make_intent(priority="critical"))
        assert len(gs.by_priority(GoalPriority.OPTIMIZATION)) == 1

    def test_no_optimization_for_normal_priority(self):
        gs = GoalEngine().create(self._make_intent(priority="normal"))
        assert len(gs.by_priority(GoalPriority.OPTIMIZATION)) == 0

    def test_constraint_goals_created(self):
        gs = GoalEngine().create(self._make_intent(constraints=["no sql", "use redis"]))
        secondary = gs.by_priority(GoalPriority.SECONDARY)
        assert len(secondary) == 2
        assert any("no sql" in g.description for g in secondary)
        assert any("use redis" in g.description for g in secondary)

    def test_no_constraint_goals_when_empty(self):
        gs = GoalEngine().create(self._make_intent(constraints=[]))
        assert len(gs.by_priority(GoalPriority.SECONDARY)) == 0

    def test_all_goals_depend_on_primary(self):
        gs = GoalEngine().create(self._make_intent(risk="high", priority="high",
                                                    constraints=["c1"]))
        primary = gs.by_priority(GoalPriority.PRIMARY)[0]
        for g in gs.goals:
            if g.id != primary.id:
                assert primary.id in g.dependencies, f"{g.priority} goal missing primary dep"

    def test_goalset_to_dict(self):
        gs = GoalEngine().create(self._make_intent())
        d = gs.to_dict()
        assert "goal_set" in d
        assert len(d["goal_set"]["goals"]) == 3  # primary + verification + knowledge


# ══════════════════════════════════════════════════════════════════════════
# 4. ContextEngine (~12 tests)
# ══════════════════════════════════════════════════════════════════════════

class _MockProvider:
    def __init__(self, **methods):
        for name, impl in methods.items():
            setattr(self, name, impl)


class TestContextEngine:

    def test_build_no_providers(self):
        ctx = ContextEngine().build()
        assert isinstance(ctx, UnifiedContext)
        assert ctx.runtime_state == {}
        assert ctx.knowledge == []
        assert ctx.session is None
        assert ctx.agent_profiles == []

    def test_register_runtime_provider(self):
        engine = ContextEngine()
        provider = _MockProvider(get_state=lambda: {"cpu": 0.8})
        engine.register_runtime_provider(provider)
        ctx = engine.build()
        assert ctx.runtime_state == {"cpu": 0.8}

    def test_register_knowledge_provider(self):
        engine = ContextEngine()
        class Entry:
            def to_dict(self):
                return {"id": 1, "content": "relevant"}

        class KnowledgeProvider:
            def retrieve_relevant(self, ctx_str: str):
                return [Entry()]

        engine.register_knowledge_provider(KnowledgeProvider())
        ctx = engine.build()
        assert len(ctx.knowledge) == 1
        assert ctx.knowledge[0]["id"] == 1

    def test_knowledge_provider_without_retrieve(self):
        engine = ContextEngine()
        engine.register_knowledge_provider(_MockProvider())
        ctx = engine.build()
        assert ctx.knowledge == []

    def test_register_session_provider(self):
        engine = ContextEngine()
        class Session:
            def to_dict(self):
                return {"id": "sess1", "status": "active"}

        provider = _MockProvider(get_session=lambda eid: Session())
        engine.register_session_provider(provider)
        ctx = engine.build(execution_id="ex-1")
        assert ctx.session is not None
        assert ctx.session["id"] == "sess1"

    def test_session_provider_without_get_session(self):
        engine = ContextEngine()
        engine.register_session_provider(_MockProvider())
        ctx = engine.build()
        assert ctx.session is None

    def test_register_profile_provider(self):
        engine = ContextEngine()
        class Profile:
            def to_dict(self):
                return {"name": "agent1", "skill": "coding"}

        provider = _MockProvider(get_all_profiles=lambda: [Profile()])
        engine.register_profile_provider(provider)
        ctx = engine.build()
        assert len(ctx.agent_profiles) == 1
        assert ctx.agent_profiles[0]["name"] == "agent1"

    def test_profile_provider_without_get_all_profiles(self):
        engine = ContextEngine()
        engine.register_profile_provider(_MockProvider())
        ctx = engine.build()
        assert ctx.agent_profiles == []

    def test_runtime_provider_fallback_to_compute(self):
        engine = ContextEngine()
        provider = _MockProvider(compute=lambda: {"mem": 512})
        engine.register_runtime_provider(provider)
        ctx = engine.build()
        assert ctx.runtime_state == {"mem": 512}

    def test_runtime_provider_fallback_all_none(self):
        engine = ContextEngine()
        provider = _MockProvider()
        engine.register_runtime_provider(provider)
        ctx = engine.build()
        assert ctx.runtime_state == {}

    def test_safe_call_valid_method(self):
        obj = _MockProvider(foo=lambda x: x * 2)
        result = ContextEngine()._safe_call(obj, "foo", 5)
        assert result == 10

    def test_safe_call_missing_method(self):
        obj = _MockProvider()
        result = ContextEngine()._safe_call(obj, "nonexistent")
        assert result is None

    def test_safe_call_exception(self):
        obj = _MockProvider(crash=lambda: 1 / 0)
        result = ContextEngine()._safe_call(obj, "crash")
        assert result is None

    def test_build_with_task_analysis(self):
        engine = ContextEngine()
        class Analysis:
            def to_dict(self):
                return {"category": "bug_fix"}

        ctx = engine.build(task_analysis=Analysis())
        assert ctx.task_analysis == {"category": "bug_fix"}

    def test_build_all_providers_integration(self):
        engine = ContextEngine()
        engine.register_runtime_provider(_MockProvider(get_state=lambda: {"cpu": 1}))
        engine.register_knowledge_provider(_MockProvider())
        engine.register_session_provider(_MockProvider())
        engine.register_profile_provider(_MockProvider())
        ctx = engine.build(execution_id="ex-99")
        assert ctx.runtime_state == {"cpu": 1}
        assert ctx.execution_id == "ex-99"


# ══════════════════════════════════════════════════════════════════════════
# 5. StrategyEngine (~12 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestStrategyEngine:

    def _make_intent(self, type: str = "implementation",
                     priority: str = "normal",
                     risk: str = "low",
                     goal: str = "do thing") -> Intent:
        return Intent(
            task_id="t1", type=type, goal=goal,
            constraints=[], priority=priority, risk=risk,
            required_capabilities=["code"],
            expected_outcome="done", confidence=0.8,
        )

    def _make_goalset(self) -> GoalSet:
        return GoalSet(goals=[
            Goal(id="g1", description="primary", priority=GoalPriority.PRIMARY),
        ])

    def test_select_architecture(self):
        intent = self._make_intent(type="architecture")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.ARCHITECTURE

    def test_select_implementation(self):
        intent = self._make_intent(type="implementation")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.IMPLEMENTATION

    def test_select_investigation(self):
        intent = self._make_intent(type="investigation")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.INVESTIGATION

    def test_select_repair(self):
        intent = self._make_intent(type="repair")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.REPAIR

    def test_select_validation(self):
        intent = self._make_intent(type="validation")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.VALIDATION

    def test_select_documentation(self):
        intent = self._make_intent(type="documentation")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.DOCUMENTATION

    def test_high_risk_overrides_to_investigation(self):
        intent = self._make_intent(type="implementation", risk="high")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.INVESTIGATION
        assert "risk override" in strategy.reasoning.lower()

    def test_critical_risk_overrides_to_investigation(self):
        intent = self._make_intent(type="repair", risk="critical")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.INVESTIGATION

    def test_low_risk_repair_keeps_repair(self):
        intent = self._make_intent(type="repair", risk="low")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.REPAIR
        assert "low-risk repair" in strategy.reasoning.lower()

    def test_knowledge_in_context_mentioned(self):
        intent = self._make_intent(type="implementation")
        ctx = UnifiedContext(knowledge=[{"id": 1}])
        strategy = StrategyEngine().select(intent, self._make_goalset(), context=ctx)
        assert "knowledge entr" in strategy.reasoning.lower()

    def test_autonomy_a2_for_high_risk(self):
        intent = self._make_intent(type="implementation", risk="high")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.recommended_autonomy == "A2"

    def test_autonomy_a2_for_critical_risk(self):
        intent = self._make_intent(type="repair", risk="critical")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.recommended_autonomy == "A2"

    def test_autonomy_a3_for_low_risk(self):
        intent = self._make_intent(type="documentation", risk="low")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.recommended_autonomy == "A3"

    def test_unknown_type_defaults_to_implementation(self):
        intent = self._make_intent(type="unknown")
        strategy = StrategyEngine().select(intent, self._make_goalset())
        assert strategy.type == StrategyType.IMPLEMENTATION

    def test_integration_with_intent_and_goalset(self):
        intent = self._make_intent(type="architecture", risk="high", priority="critical")
        gs = self._make_goalset()
        ctx = UnifiedContext(knowledge=[{"k": "v"}])
        strategy = StrategyEngine().select(intent, gs, context=ctx)
        assert strategy.type == StrategyType.INVESTIGATION
        assert strategy.recommended_autonomy == "A2"
        assert "architecture" in strategy.reasoning or "risk" in strategy.reasoning


# ══════════════════════════════════════════════════════════════════════════
# 6. CognitiveKernel (~6-8 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestCognitiveKernel:

    def test_process_returns_dict(self):
        kernel = CognitiveKernel()
        task = make_task("implement feature X")
        result = kernel.process(task)
        assert isinstance(result, dict)

    def test_process_contains_intent_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("fix the login bug"))
        assert "intent" in result
        assert result["intent"]["intent"]["task_id"] == "task-001"

    def test_process_contains_goals_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("add new API"))
        assert "goals" in result
        assert "goal_set" in result["goals"]

    def test_process_contains_context_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("write documentation"))
        assert "context" in result
        assert "unified_context" in result["context"]

    def test_process_contains_strategy_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("investigate performance"))
        assert "strategy" in result
        assert result["strategy"]["strategy"]["type"] == "investigation"

    def test_process_contains_analysis_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("deploy to staging"))
        assert "analysis" in result
        assert "task_analysis" in result["analysis"]

    def test_process_contains_selection_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("refactor the auth layer"))
        assert "selection" in result
        assert "agent_selection" in result["selection"]

    def test_process_contains_plan_key(self):
        kernel = CognitiveKernel()
        result = kernel.process(make_task("add unit tests"))
        assert "plan" in result
        assert "execution_plan" in result["plan"]

    def test_process_with_critical_task(self):
        kernel = CognitiveKernel()
        task = make_task("critical production bug fix",
                         constraints=["production impact"])
        result = kernel.process(task)
        assert result["intent"]["intent"]["priority"] == "critical"
        assert result["intent"]["intent"]["risk"] == "critical"
        assert result["strategy"]["strategy"]["recommended_autonomy"] == "A2"

    def test_process_with_complex_objective(self):
        kernel = CognitiveKernel()
        task = make_task(
            "architect and implement a distributed caching layer",
            constraints=["high availability", "eventual consistency"],
            expected_output="design doc and implementation",
        )
        result = kernel.process(task)
        assert result["intent"]["intent"]["confidence"] > 0.5
        assert len(result["goals"]["goal_set"]["goals"]) >= 5
