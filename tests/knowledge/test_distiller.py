from __future__ import annotations

from features.knowledge.distiller import KnowledgeDistiller
from features.bridge.task_contract import TaskContract


class TestKnowledgeDistiller:

    def _make_mock_result(self, stdout: str = ""):
        class MockResult:
            def to_dict(self):
                return {"result": {"stdout": stdout, "output": ""}}
        return MockResult()

    def _make_mock_verification(self, status: str = "passed", facts: list = None):
        class MockVerification:
            def to_dict(self):
                return {"verification_report": {"status": status, "facts": facts or []}}
        return MockVerification()

    def test_distill_with_task(self):
        distiller = KnowledgeDistiller()
        task = TaskContract(id="t1", project="muscal-core", objective="fix the login bug")
        result = distiller.distill(task, self._make_mock_result("Fixed the login validation"))
        assert "fix the login bug" in result["problem"]
        assert "Fixed the login validation" in result["solution"]
        assert result["context"] is not None

    def test_distill_with_verification(self):
        distiller = KnowledgeDistiller()
        task = TaskContract(id="t1", project="muscal-core", objective="add tests")
        ver = self._make_mock_verification("passed", [{"statement": "All tests pass"}])
        result = distiller.distill(task, self._make_mock_result(), ver)
        assert "All tests pass" in result["evidence"]

    def test_distill_missing_solution_fallback(self):
        distiller = KnowledgeDistiller()
        task = TaskContract(id="t1", project="muscal-core", objective="do something")
        result = distiller.distill(task, self._make_mock_result(""))
        assert "no detailed solution" in result["solution"].lower()

    def test_distill_with_constraints(self):
        distiller = KnowledgeDistiller()
        task = TaskContract(id="t1", project="muscal-core", objective="refactor",
                            constraints=["no breaking changes"])
        result = distiller.distill(task, self._make_mock_result("refactored"))
        assert "no breaking changes" in result["context"]

    def test_distill_extracts_limitations(self):
        distiller = KnowledgeDistiller()
        task = TaskContract(id="t1", project="muscal-core", objective="deploy")
        ver = self._make_mock_verification("passed", [])
        ver.to_dict = lambda: {"verification_report": {"status": "passed", "risks": [{"statement": "Requires manual review"}]}}
        result = distiller.distill(task, self._make_mock_result(), ver)
        assert "Requires manual review" in result["limitations"]

    def test_distill_no_verification(self):
        distiller = KnowledgeDistiller()
        task = TaskContract(id="t1", project="muscal-core", objective="test")
        result = distiller.distill(task, self._make_mock_result(), None)
        assert result["evidence"] == "No verification report available"
