"""
Tests for Review Orchestrator.
"""


import pytest

from features.multi_llm_review.orchestrator.orchestrator import (
    OrchestratorConfig,
    ReviewOrchestrator,
    ReviewResult,
)
from features.multi_llm_review.review_schemas import (
    Consensus,
    ReviewFinding,
    ReviewTask,
    TechnicalVerification,
)


class MockEventStore:
    """Mock EventStore for testing."""

    def __init__(self):
        self.appended = []
        self.replay_results = {}

    def append(self, topic: str, payload: dict, source: str) -> int:
        self.appended.append((topic, payload, source))
        return len(self.appended)

    def replay(self, topic: str):
        return self.replay_results.get(topic, [])


class MockTechnicalVerifier:
    """Mock TechnicalVerifier."""

    def verify(self, task):
        return TechnicalVerification(
            review_task_id=task.task_id,
            tests_passed=True,
            tests_total=100,
            tests_failed=0,
            tests_skipped=5,
            coverage_pct=85.0,
            static_analysis={},
            import_checks={},
            findings=[],
        )


class MockConsensusBuilder:
    """Mock ConsensusBuilder."""

    def build(self, task, model_findings, technical_verification):
        return Consensus(
            review_task_id=task.task_id,
            model_findings=model_findings,
            technical_verification=technical_verification,
            status="VERIFIED",
            confidence=0.85,
            dissent=[],
            recommended_actions=["Proceed"],
        )


class MockAgent:
    """Mock review agent."""

    def __init__(self, role: str, findings: list = None):
        self.role = role
        self._findings = findings or []

    def analyze(self, task, context):
        return self._findings


class MockEvidenceStore:
    """Mock ReviewEvidenceStore."""

    def __init__(self):
        self.recorded = []

    def record_review_task(self, task):
        self.recorded.append(("task", task))

    def record_review_finding(self, finding):
        self.recorded.append(("finding", finding))

    def record_technical_verification(self, verification):
        self.recorded.append(("verification", verification))

    def record_consensus(self, consensus):
        self.recorded.append(("consensus", consensus))


class TestReviewOrchestrator:
    """Test ReviewOrchestrator."""

    @pytest.fixture
    def mock_event_store(self):
        return MockEventStore()

    @pytest.fixture
    def config(self):
        return OrchestratorConfig()

    @pytest.fixture
    def orchestrator(self, mock_event_store, config):
        return ReviewOrchestrator(mock_event_store, config)

    @pytest.fixture
    def sample_task(self):
        return ReviewTask(
            target_commit="abc123",
            target_files=["src/test.py"],
            review_type="full",
        )

    def test_orchestrator_creation(self, orchestrator):
        assert orchestrator is not None
        assert orchestrator.config is not None

    def test_run_review_basic(self, orchestrator, sample_task):
        # Replace components with mocks
        orchestrator.evidence_store = MockEvidenceStore()
        orchestrator.technical_verifier = MockTechnicalVerifier()
        orchestrator.consensus_builder = MockConsensusBuilder()
        orchestrator._agents = {
            "auditor": MockAgent("auditor", []),
            "architect": MockAgent("architect", []),
        }

        result = orchestrator.run_review(sample_task)

        assert isinstance(result, ReviewResult)
        assert result.review_task == sample_task
        assert result.technical_verification is not None
        assert result.consensus is not None
        assert result.consensus.status == "VERIFIED"

    def test_run_review_records_task(self, orchestrator, sample_task):
        evidence_store = MockEvidenceStore()
        orchestrator.evidence_store = evidence_store
        orchestrator.technical_verifier = MockTechnicalVerifier()
        orchestrator.consensus_builder = MockConsensusBuilder()
        orchestrator._agents = {}

        orchestrator.run_review(sample_task)

        assert len(evidence_store.recorded) >= 1
        assert any(r[0] == "task" for r in evidence_store.recorded)

    def test_run_review_records_verification(self, orchestrator, sample_task):
        evidence_store = MockEvidenceStore()
        orchestrator.evidence_store = evidence_store
        orchestrator.technical_verifier = MockTechnicalVerifier()
        orchestrator.consensus_builder = MockConsensusBuilder()
        orchestrator._agents = {}

        orchestrator.run_review(sample_task)

        assert any(r[0] == "verification" for r in evidence_store.recorded)

    def test_run_review_records_consensus(self, orchestrator, sample_task):
        evidence_store = MockEvidenceStore()
        orchestrator.evidence_store = evidence_store
        orchestrator.technical_verifier = MockTechnicalVerifier()
        orchestrator.consensus_builder = MockConsensusBuilder()
        orchestrator._agents = {}

        orchestrator.run_review(sample_task)

        assert any(r[0] == "consensus" for r in evidence_store.recorded)

    def test_run_review_agent_findings_recorded(self, orchestrator, sample_task):
        evidence_store = MockEvidenceStore()
        orchestrator.evidence_store = evidence_store
        orchestrator.technical_verifier = MockTechnicalVerifier()
        orchestrator.consensus_builder = MockConsensusBuilder()

        # Create mock agent with findings
        finding = ReviewFinding(
            finding_id="finding-1",
            review_task_id=sample_task.task_id,
            finding_type="security",
            severity="high",
            confidence=0.9,
            claim="Test finding",
            evidence=[],
            file_refs=["src/test.py"],
        )
        agent = MockAgent("auditor", [finding])
        orchestrator._agents = {"auditor": agent}

        orchestrator.run_review(sample_task)

        # Check finding was recorded
        finding_records = [r for r in evidence_store.recorded if r[0] == "finding"]
        assert len(finding_records) >= 1

    def test_orchestrator_config_defaults(self):
        config = OrchestratorConfig()
        assert config.enable_auditor is True
        assert config.enable_architect is True
        assert config.enable_reviewer is True
        assert config.enable_judge is True
        assert config.max_parallel_agents == 4
        assert config.timeout_seconds == 300

    def test_orchestrator_config_custom(self):
        config = OrchestratorConfig(
            enable_auditor=False,
            enable_reviewer=False,
            timeout_seconds=60,
        )
        assert config.enable_auditor is False
        assert config.enable_reviewer is False
        assert config.timeout_seconds == 60

    def test_is_enabled(self, orchestrator):
        assert orchestrator._is_enabled("auditor") is True
        assert orchestrator._is_enabled("architect") is True

        orchestrator.config.enable_auditor = False
        assert orchestrator._is_enabled("auditor") is False

    def test_get_agents_creates_once(self, orchestrator):
        agents1 = orchestrator._get_agents()
        agents2 = orchestrator._get_agents()
        assert agents1 is agents2  # Same instance

    def test_build_context(self, orchestrator, sample_task):
        context = orchestrator._build_context(sample_task)
        assert sample_task.target_commit in context
        assert sample_task.review_type in context

    def test_build_consensus(self, orchestrator, sample_task):
        from features.multi_llm_review.review_schemas import ReviewFinding

        finding = ReviewFinding(
            finding_id="test-1",
            review_task_id=sample_task.task_id,
            finding_type="security",
            severity="high",
            confidence=0.9,
            claim="Test",
            evidence=[],
            file_refs=[],
        )

        consensus = orchestrator._build_consensus(
            sample_task,
            {"auditor": [finding]},
            TechnicalVerification(review_task_id=sample_task.task_id, tests_passed=True),
            [],
        )

        assert isinstance(consensus, Consensus)
        assert consensus.status in ("VERIFIED", "PARTIALLY", "UNVERIFIED", "CONTRADICTION")


class TestOrchestratorConfig:
    """Test OrchestratorConfig."""

    def test_defaults(self):
        config = OrchestratorConfig()
        assert config.enable_auditor is True
        assert config.enable_architect is True
        assert config.enable_reviewer is True
        assert config.enable_judge is True
        assert config.max_parallel_agents == 4
        assert config.timeout_seconds == 300

    def test_custom_config(self):
        config = OrchestratorConfig(
            enable_auditor=False,
            max_parallel_agents=2,
            timeout_seconds=60,
        )
        assert config.enable_auditor is False
        assert config.max_parallel_agents == 2
        assert config.timeout_seconds == 60
