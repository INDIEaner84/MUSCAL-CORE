"""
Tests für ReviewEvidenceStore - Wrapper um EventStore.
"""

from unittest.mock import Mock

import pytest

from features.multi_llm_review.evidence_store import ReviewEvidenceStore
from features.multi_llm_review.review_schemas import (
    Consensus,
    ReviewFinding,
    ReviewTask,
    TechnicalVerification,
)
from features.provenance.evaluation import EvidenceRef
from runtime.event_store import EventStore


class TestReviewEvidenceStore:
    """Tests für ReviewEvidenceStore."""

    @pytest.fixture
    def mock_event_store(self):
        """Mock EventStore für Tests."""
        store = Mock(spec=EventStore)
        store.append = Mock(return_value=1)
        store.replay = Mock(return_value=[])
        return store

    @pytest.fixture
    def evidence_store(self, mock_event_store):
        """ReviewEvidenceStore mit Mock EventStore."""
        return ReviewEvidenceStore(mock_event_store)

    @pytest.fixture
    def sample_review_task(self):
        """Sample ReviewTask für Tests."""
        return ReviewTask(
            task_id="test-task-123",
            target_commit="abc123",
            target_files=["src/module.py"],
            review_type="security",
        )

    @pytest.fixture
    def sample_finding(self):
        """Sample ReviewFinding für Tests."""
        return ReviewFinding(
            finding_id="finding-123",
            review_task_id="test-task-123",
            finding_type="security",
            severity="high",
            confidence=0.8,
            claim="SQL injection vulnerability in user input handling",
            evidence=[
                EvidenceRef(
                    source_id="src/module.py:42",
                    relation_type="CONTAINS",
                    status="VERIFIED",
                    evidence_source="static_analysis",
                    reason="Direct code observation",
                )
            ],
            file_refs=["src/module.py:42"],
        )

    @pytest.fixture
    def sample_verification(self):
        """Sample TechnicalVerification für Tests."""
        return TechnicalVerification(
            verification_id="ver-123",
            review_task_id="test-task-123",
            tests_passed=True,
            tests_total=100,
            tests_failed=0,
            tests_skipped=5,
            coverage_pct=85.5,
            static_analysis={"pylint": {"exit_code": 0}, "mypy": {"exit_code": 0}},
            import_checks={"valid": ["src/module.py"], "invalid": []},
            findings=[],
        )

    @pytest.fixture
    def sample_consensus(self):
        """Sample Consensus für Tests."""
        return Consensus(
            consensus_id="cons-123",
            review_task_id="test-task-123",
            model_findings=[],
            technical_verification=None,
            status="VERIFIED",
            confidence=0.85,
            dissent=[],
            recommended_actions=["Proceed with integration"],
        )

    def test_record_review_task(self, evidence_store, mock_event_store, sample_review_task):
        """Test: ReviewTask wird als Event gespeichert."""
        seq = evidence_store.record_review_task(sample_review_task)

        assert seq == 1
        mock_event_store.append.assert_called_once()
        call_args = mock_event_store.append.call_args
        assert call_args.kwargs["topic"] == "review.task"
        assert call_args.kwargs["source"] == "multi_llm_review"
        assert call_args.kwargs["payload"]["task_id"] == "test-task-123"

    def test_record_review_finding(self, evidence_store, mock_event_store, sample_finding):
        """Test: ReviewFinding wird als Event gespeichert."""
        seq = evidence_store.record_review_finding(sample_finding)

        assert seq == 1
        mock_event_store.append.assert_called_once()
        call_args = mock_event_store.append.call_args
        assert call_args.kwargs["topic"] == "review.finding"
        assert call_args.kwargs["payload"]["finding_id"] == "finding-123"

    def test_record_technical_verification(
        self, evidence_store, mock_event_store, sample_verification
    ):
        """Test: TechnicalVerification wird als Event gespeichert."""
        seq = evidence_store.record_technical_verification(sample_verification)

        assert seq == 1
        mock_event_store.append.assert_called_once()
        call_args = mock_event_store.append.call_args
        assert call_args.kwargs["topic"] == "verification.result"
        assert call_args.kwargs["payload"]["verification_id"] == "ver-123"

    def test_record_consensus(self, evidence_store, mock_event_store, sample_consensus):
        """Test: Consensus wird als Event gespeichert."""
        seq = evidence_store.record_consensus(sample_consensus)

        assert seq == 1
        mock_event_store.append.assert_called_once()
        call_args = mock_event_store.append.call_args
        assert call_args.kwargs["topic"] == "review.consensus"
        assert call_args.kwargs["payload"]["consensus_id"] == "cons-123"

    def test_get_review_findings_empty(self, evidence_store, mock_event_store):
        """Test: Leere Findings-Liste wenn keine Events."""
        mock_event_store.replay.return_value = []

        findings = evidence_store.get_review_findings("test-task-123")

        assert findings == []

    def test_get_review_findings_with_data(self, evidence_store, mock_event_store, sample_finding):
        """Test: Findings werden korrekt gelesen."""
        mock_event = Mock()
        mock_event.payload = sample_finding.to_dict()
        mock_event_store.replay.return_value = [mock_event]

        findings = evidence_store.get_review_findings("test-task-123")

        assert len(findings) == 1
        assert findings[0].finding_id == "finding-123"

    def test_get_technical_verification_none(self, evidence_store, mock_event_store):
        """Test: None wenn keine Verification."""
        mock_event_store.replay.return_value = []

        verification = evidence_store.get_technical_verification("test-task-123")

        assert verification is None

    def test_get_technical_verification_with_data(
        self, evidence_store, mock_event_store, sample_verification
    ):
        """Test: Verification wird korrekt gelesen."""
        mock_event = Mock()
        mock_event.payload = sample_verification.to_dict()
        mock_event_store.replay.return_value = [mock_event]

        verification = evidence_store.get_technical_verification("test-task-123")

        assert verification is not None
        assert verification.verification_id == "ver-123"

    def test_get_consensus_none(self, evidence_store, mock_event_store):
        """Test: None wenn kein Consensus."""
        mock_event_store.replay.return_value = []

        consensus = evidence_store.get_consensus("test-task-123")

        assert consensus is None

    def test_invalid_payload_raises_error(self, evidence_store):
        """Test: Ungültige Payload wirft ValueError."""
        invalid_payload = {
            "target_commit": "abc123",
            "review_type": "full",
            "target_files": [],
            "created_at": 0.0,
        }

        from features.multi_llm_review.event_schemas import validate_payload

        assert not validate_payload("review.task", invalid_payload)
