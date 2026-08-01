from __future__ import annotations

from features.knowledge.extractor import KnowledgeExtractor
from features.knowledge.models import EvidenceLevel


class TestKnowledgeExtractor:

    def _make_bridge_output(self, status="completed", task_id="t1", errors=None):
        class MockBridgeOutput:
            def __init__(self):
                self.status = status
                self.task_id = task_id
                self.errors = errors or []
                self.execution_record = {"execution_record": {"bridge_execution_id": "e1", "task_identity": {"id": task_id}}}
                self.normalized = None
        return MockBridgeOutput()

    def _make_verification(self, status="passed"):
        class MockVerification:
            def to_dict(self):
                return {"verification_report": {"status": status, "facts": [], "verification_findings": []}}
        return MockVerification()

    def test_extract_successful_execution(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output()
        kc = extractor.extract(output, verification_report=self._make_verification())
        assert kc is not None
        assert kc.source_execution_id == "e1"
        assert kc.source_task_id == "t1"

    def test_extract_failed_execution_returns_none(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output(status="failed")
        kc = extractor.extract(output)
        assert kc is None

    def test_extract_none_output(self):
        extractor = KnowledgeExtractor()
        kc = extractor.extract(None)
        assert kc is None

    def test_extract_evidence_level_verified(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output()
        kc = extractor.extract(output, verification_report=self._make_verification("passed"))
        assert kc.evidence_level == EvidenceLevel.VERIFIED

    def test_extract_evidence_level_unknown_no_verification(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output()
        kc = extractor.extract(output)
        assert kc.evidence_level == EvidenceLevel.UNKNOWN

    def test_extract_confidence_with_errors(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output(errors=["something went wrong"])
        kc = extractor.extract(output, verification_report=self._make_verification("passed"))
        assert kc.confidence < 0.8

    def test_extract_category_bug_fix(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output()
        kc = extractor.extract(output)
        assert kc.category is not None

    def test_extract_with_task(self):
        extractor = KnowledgeExtractor()
        task = type("MockTask", (), {"id": "t1", "project": "muscal-core", "objective": "fix bug", "to_dict": lambda self: {"task": {"id": "t1", "project": "muscal-core", "objective": "fix bug"}}})()
        output = self._make_bridge_output()
        kc = extractor.extract(output, task=task)
        assert kc is not None
        assert "fix bug" in kc.problem
