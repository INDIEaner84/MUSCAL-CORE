from __future__ import annotations

from features.orchestration.task_analyzer import TaskAnalyzer, ComplexityLevel, RiskLevel, TaskCategory
from features.bridge.task_contract import TaskContract


class TestTaskAnalyzer:

    def _make_task(self, objective: str, constraints: list = None, verification: bool = True):
        return TaskContract(
            id="t1", project="muscal-core",
            objective=objective,
            constraints=constraints or [],
            verification_required=verification,
        )

    def test_classify_bug_fix(self):
        assert TaskCategory.classify("fix the login bug") == TaskCategory.BUG_FIX
        assert TaskCategory.classify("crash on startup") == TaskCategory.BUG_FIX

    def test_classify_feature(self):
        assert TaskCategory.classify("add new user dashboard") == TaskCategory.FEATURE
        assert TaskCategory.classify("implement search") == TaskCategory.FEATURE

    def test_classify_refactor(self):
        assert TaskCategory.classify("refactor the API layer") == TaskCategory.REFACTOR

    def test_classify_documentation(self):
        assert TaskCategory.classify("write README docs") == TaskCategory.DOCUMENTATION

    def test_classify_testing(self):
        assert TaskCategory.classify("add unit tests for models") == TaskCategory.TESTING

    def test_classify_deployment(self):
        assert TaskCategory.classify("deploy to production") == TaskCategory.DEPLOYMENT

    def test_classify_analysis(self):
        assert TaskCategory.classify("analyze performance") == TaskCategory.ANALYSIS

    def test_classify_other(self):
        assert TaskCategory.classify("do a thing") == TaskCategory.OTHER

    def test_analyze_returns_analysis(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("fix the login authentication bug")
        analysis = analyzer.analyze(task)
        assert analysis.task_id == "t1"
        assert analysis.category == "bug_fix"
        assert analysis.verification_required is True

    def test_complexity_simple(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("fix typo")
        analysis = analyzer.analyze(task)
        assert analysis.complexity == ComplexityLevel.SIMPLE.value

    def test_complexity_complex(self):
        analyzer = TaskAnalyzer()
        task = self._make_task(
            "refactor the entire authentication pipeline including OAuth, session management, "
            "and token refresh logic across the frontend and backend services",
            constraints=["no breaking changes", "maintain backwards compat", "update all docs", "add migration"],
        )
        analysis = analyzer.analyze(task)
        assert analysis.complexity == ComplexityLevel.COMPLEX.value

    def test_complexity_moderate(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("implement a new API endpoint for user profiles", constraints=["follow existing patterns"])
        analysis = analyzer.analyze(task)
        assert analysis.complexity == ComplexityLevel.MODERATE.value

    def test_risk_high_for_deployment(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("deploy to production")
        analysis = analyzer.analyze(task)
        assert analysis.risk_level == RiskLevel.HIGH.value

    def test_risk_medium_for_bugfix(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("fix the login bug")
        analysis = analyzer.analyze(task)
        assert analysis.risk_level == RiskLevel.MEDIUM.value

    def test_risk_low_for_documentation(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("write documentation")
        analysis = analyzer.analyze(task)
        assert analysis.risk_level == RiskLevel.LOW.value

    def test_effort_small(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("fix typo")
        analysis = analyzer.analyze(task)
        assert analysis.estimated_effort == "small"

    def test_effort_large(self):
        analyzer = TaskAnalyzer()
        long_objective = " ".join(["complex" for _ in range(60)])
        task = self._make_task(long_objective, constraints=["a", "b", "c", "d"])
        analysis = analyzer.analyze(task)
        assert analysis.estimated_effort == "large"

    def test_recommended_autonomy_high_risk(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("deploy to production")
        analysis = analyzer.analyze(task)
        assert analysis.recommended_autonomy == "A2"

    def test_recommended_autonomy_low_risk(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("write documentation")
        analysis = analyzer.analyze(task)
        assert analysis.recommended_autonomy == "A4"

    def test_required_capabilities_for_bugfix(self):
        analyzer = TaskAnalyzer()
        task = self._make_task("fix the login bug")
        analysis = analyzer.analyze(task)
        assert "debugging" in analysis.required_capabilities
        assert "code_understanding" in analysis.required_capabilities
