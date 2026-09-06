"""
Tests for Review Agents.
"""


import pytest

from features.multi_llm_review.agents import (
    AgentConfig,
    ArchitectAgent,
    AuditorAgent,
    BaseReviewAgent,
    ImplementationReviewerAgent,
    JudgeAgent,
    create_agent,
    create_all_agents,
)
from features.multi_llm_review.review_schemas import ReviewFinding, ReviewTask


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, responses: dict | None = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_messages = None

    @property
    def provider_id(self) -> str:
        return "mock-provider"

    @property
    def is_available(self) -> bool:
        return True

    def chat(self, messages, temperature=0.0, max_tokens=None, structured_output_schema=None):
        self.call_count += 1
        self.last_messages = messages

        # Return a valid structured response
        return {
            "findings": [
                {
                    "finding_type": "security",
                    "severity": "high",
                    "confidence": 0.85,
                    "claim": "SQL injection vulnerability in user input",
                    "evidence_refs": [
                        {
                            "source_id": "src/db.py:42",
                            "relation_type": "CONTAINS",
                            "status": "VERIFIED",
                            "evidence_source": "static_analysis",
                            "reason": "Direct code observation",
                        }
                    ],
                    "file_refs": ["src/db.py:42"],
                }
            ]
        }

    def analyze(self, task, context, structured_output_schema=None):
        return {"result": "analyzed"}

    def get_capabilities(self):
        return ["chat", "analyze"]

    def get_metrics(self):
        return {}


class MockRegistry:
    """Mock provider registry."""

    def __init__(self, provider: MockProvider):
        self.provider = provider

    def resolve(self, role: str, task_fit=None):
        return self.provider


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_agent_config_creation(self):
        config = AgentConfig(role="auditor", temperature=0.1)
        assert config.role == "auditor"
        assert config.temperature == 0.1

    def test_agent_config_defaults(self):
        config = AgentConfig(role="reviewer")
        assert config.role == "reviewer"
        assert config.temperature == 0.0
        assert config.provider_id is None


class TestBaseReviewAgent:
    """Test BaseReviewAgent abstract base class."""

    def test_base_agent_creation(self):
        config = AgentConfig(role="test", temperature=0.1)
        provider = MockProvider()
        registry = MockRegistry(provider)

        class ConcreteAgent(BaseReviewAgent):
            def get_system_prompt(self):
                return "test prompt"

            def get_analysis_prompt(self, task, context):
                return "test analysis"

        agent = ConcreteAgent(config, registry)
        assert agent.config.role == "test"
        assert agent.provider_registry is not None

    def test_provider_lazy_loading(self):
        config = AgentConfig(role="auditor")
        provider = MockProvider()
        registry = MockRegistry(provider)

        class ConcreteAgent(BaseReviewAgent):
            def get_system_prompt(self):
                return "test"

            def get_analysis_prompt(self, task, context):
                return "analysis"

        agent = ConcreteAgent(config, registry)
        assert agent._provider is None

        # Accessing provider should lazy-load
        p = agent.provider
        assert p is provider


class TestAuditorAgent:
    """Test AuditorAgent."""

    def test_auditor_creation(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = AuditorAgent(registry)

        assert agent.role == "auditor"
        assert agent.config.temperature == 0.1

    def test_auditor_system_prompt(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = AuditorAgent(registry)

        prompt = agent.get_system_prompt()
        assert "adversarial" in prompt.lower()
        assert "security" in prompt.lower()
        assert "gaps" in prompt.lower()

    def test_auditor_analysis_prompt(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = AuditorAgent(registry)

        task = ReviewTask(
            task_id="test-123",
            target_commit="abc123",
            target_files=["src/test.py"],
            review_type="security",
        )

        prompt = agent.get_analysis_prompt(task, "test context")
        assert "abc123" in prompt
        assert "src/test.py" in prompt
        assert "security" in prompt


class TestArchitectAgent:
    """Test ArchitectAgent."""

    def test_architect_creation(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = ArchitectAgent(registry)

        assert agent.role == "architect"
        assert agent.config.temperature == 0.2

    def test_architect_system_prompt(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = ArchitectAgent(registry)

        prompt = agent.get_system_prompt()
        assert "architecture" in prompt.lower()
        assert "contract" in prompt.lower()
        assert "invariant" in prompt.lower()


class TestImplementationReviewerAgent:
    """Test ImplementationReviewerAgent."""

    def test_reviewer_creation(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = ImplementationReviewerAgent(registry)

        assert agent.role == "reviewer"
        assert agent.config.temperature == 0.1

    def test_reviewer_system_prompt(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = ImplementationReviewerAgent(registry)

        prompt = agent.get_system_prompt()
        assert "correctness" in prompt.lower()
        assert "quality" in prompt.lower()
        assert "standard" in prompt.lower()


class TestJudgeAgent:
    """Test JudgeAgent."""

    def test_judge_creation(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = JudgeAgent(registry)

        assert agent.role == "judge"
        assert agent.config.temperature == 0.0

    def test_judge_system_prompt(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = JudgeAgent(registry)

        prompt = agent.get_system_prompt()
        assert "synthesis" in prompt.lower()
        assert "conflict" in prompt.lower()
        assert "dissent" in prompt.lower()
        assert "technical verification" in prompt.lower()


class TestAgentFactory:
    """Test agent factory functions."""

    def test_create_agent_valid_roles(self):
        registry = MockRegistry(MockProvider())

        for role in ["auditor", "architect", "reviewer", "judge"]:
            agent = create_agent(role, registry)
            assert agent.role == role

    def test_create_agent_invalid_role(self):
        registry = MockRegistry(MockProvider())
        with pytest.raises(ValueError, match="Unknown agent role"):
            create_agent("invalid", registry)

    def test_create_all_agents(self):
        registry = MockRegistry(MockProvider())
        agents = create_all_agents(registry)

        assert set(agents.keys()) == {"auditor", "architect", "reviewer", "judge"}
        for role, agent in agents.items():
            assert agent.role == role


class TestAgentAnalysis:
    """Test agent analysis execution (with mocked provider)."""

    def test_auditor_analyze_returns_findings(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = AuditorAgent(registry)

        task = ReviewTask(
            task_id="test-123",
            target_commit="abc123",
            target_files=["src/test.py"],
            review_type="security",
        )

        findings = agent.analyze(task, "test context")

        assert len(findings) == 1
        finding = findings[0]
        assert isinstance(finding, ReviewFinding)
        assert finding.finding_type == "security"
        assert finding.severity == "high"
        assert finding.confidence == 0.85
        assert "SQL injection" in finding.claim
        assert len(finding.evidence) == 1
        # Mock provider returns fixed file_refs
        assert finding.file_refs == ["src/db.py:42"]

    def test_provider_called_with_correct_params(self):
        provider = MockProvider()
        registry = MockRegistry(provider)
        agent = AuditorAgent(registry)

        task = ReviewTask(task_id="test-123", target_commit="abc123")
        agent.analyze(task, "test context")

        assert provider.call_count == 1
        assert provider.last_messages is not None
        assert len(provider.last_messages) == 2  # system + user
        assert provider.last_messages[0]["role"] == "system"
        assert provider.last_messages[1]["role"] == "user"
