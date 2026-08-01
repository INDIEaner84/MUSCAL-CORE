from __future__ import annotations

from features.knowledge.validator import KnowledgeValidator
from features.knowledge.models import (
    KnowledgeCandidate, KnowledgeState, EvidenceLevel,
)


class TestKnowledgeValidator:

    def _make_candidate(self, **overrides):
        params = dict(
            id="kc-1", source_execution_id="e1", source_task_id="t1",
            project="test", category="general", problem="This is a valid problem statement",
            solution="This is a valid solution with enough detail",
            evidence="All verification checks passed",
            verification="passed", confidence=0.8,
            evidence_level=EvidenceLevel.VERIFIED,
        )
        params.update(overrides)
        return KnowledgeCandidate(**params)

    def test_validate_valid_candidate(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate()
        is_valid, reasons = validator.validate(candidate)
        assert is_valid
        assert len(reasons) == 0

    def test_validate_no_execution_id(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(source_execution_id="")
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid
        assert any("source_execution_id" in r for r in reasons)

    def test_validate_no_task_id(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(source_task_id="")
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid
        assert any("source_task_id" in r for r in reasons)

    def test_validate_short_problem(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(problem="abc")
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid
        assert any("Problem" in r for r in reasons)

    def test_validate_short_solution(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(solution="abc")
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid
        assert any("Solution" in r for r in reasons)

    def test_validate_no_evidence(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(evidence="No verification report available")
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid

    def test_validate_low_confidence(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(confidence=0.05)
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid
        assert any("Confidence" in r for r in reasons)

    def test_validate_unknown_evidence_level(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(evidence_level=EvidenceLevel.UNKNOWN)
        is_valid, reasons = validator.validate(candidate)
        assert not is_valid
        assert any("UNKNOWN" in r for r in reasons)

    def test_evaluate_valid_returns_validated(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate()
        state = validator.evaluate(candidate)
        assert state == KnowledgeState.VALIDATED

    def test_evaluate_invalid_returns_candidate(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(confidence=0.05)
        state = validator.evaluate(candidate)
        assert state == KnowledgeState.CANDIDATE

    def test_evaluate_rejected_stays_rejected(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(state=KnowledgeState.REJECTED)
        state = validator.evaluate(candidate)
        assert state == KnowledgeState.REJECTED

    def test_evaluate_superseded_stays_superseded(self):
        validator = KnowledgeValidator()
        candidate = self._make_candidate(state=KnowledgeState.SUPERSEDED)
        state = validator.evaluate(candidate)
        assert state == KnowledgeState.SUPERSEDED
