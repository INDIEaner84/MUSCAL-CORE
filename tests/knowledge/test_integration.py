from __future__ import annotations

from features.knowledge.extractor import KnowledgeExtractor
from features.knowledge.validator import KnowledgeValidator
from features.knowledge.knowledge_writer import KnowledgeWriter
from features.knowledge.retriever import KnowledgeRetriever
from features.knowledge.models import KnowledgeState, EvidenceLevel


class TestKnowledgeIntegration:

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
                return {"verification_report": {"status": status, "facts": [{"statement": "All checks pass"}], "verification_findings": []}}
        return MockVerification()

    def test_full_flow_extract_validate_store(self):
        extractor = KnowledgeExtractor()
        validator = KnowledgeValidator()
        writer = KnowledgeWriter()

        output = self._make_bridge_output()
        verification = self._make_verification()

        candidate = extractor.extract(output, verification_report=verification)
        assert candidate is not None
        assert candidate.state == KnowledgeState.CANDIDATE

        is_valid, reasons = validator.validate(candidate)
        assert is_valid, f"Validation failed: {reasons}"
        assert len(reasons) == 0

        state = validator.evaluate(candidate)
        assert state == KnowledgeState.VALIDATED

        kid = writer.write_validated(candidate)
        assert kid is not None

        entry = writer.get_entry(kid)
        assert entry is not None

    def test_extract_validated_entry_can_be_retrieved(self):
        extractor = KnowledgeExtractor()
        validator = KnowledgeValidator()
        writer = KnowledgeWriter()

        output = self._make_bridge_output()
        candidate = extractor.extract(output, verification_report=self._make_verification())
        writer.write_validated(candidate)

        retriever = KnowledgeRetriever(writer=writer)
        results = retriever.retrieve_relevant(candidate.problem[:20], top_k=3)
        assert len(results) >= 1
        assert results[0].source_execution == candidate.source_execution_id

    def test_rejected_candidate_not_stored_as_entry(self):
        writer = KnowledgeWriter()
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output()
        candidate = extractor.extract(output, verification_report=self._make_verification())
        candidate.confidence = 0.01
        validator = KnowledgeValidator()
        state = validator.evaluate(candidate)
        assert state == KnowledgeState.CANDIDATE
        writer.write_candidate(candidate)
        assert len(writer.list_entries()) == 0

    def test_failed_execution_no_knowledge(self):
        extractor = KnowledgeExtractor()
        output = self._make_bridge_output(status="failed")
        candidate = extractor.extract(output)
        assert candidate is None

    def test_successful_execution_creates_validated_knowledge(self):
        extractor = KnowledgeExtractor()
        validator = KnowledgeValidator()
        writer = KnowledgeWriter()

        output = self._make_bridge_output()
        candidate = extractor.extract(output, verification_report=self._make_verification("passed"))
        assert candidate.evidence_level == EvidenceLevel.VERIFIED
        state = validator.evaluate(candidate)
        assert state == KnowledgeState.VALIDATED
        writer.write_validated(candidate)
        assert len(writer.list_entries()) == 1
