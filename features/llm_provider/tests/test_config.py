"""
Tests for LLM Provider Configuration.
"""

import os
from unittest.mock import patch

from features.llm_provider.provider_config import (
    DEFAULT_ROLE_CONFIGS,
    ProviderConfig,
    get_default_role_config,
    load_provider_configs,
)


def test_provider_config_from_env():
    """Test creating ProviderConfig from environment."""
    with patch.dict(os.environ, {
        "LLM_TEST_PROVIDER_ID": "test-provider",
        "LLM_TEST_TYPE": "ollama",
        "LLM_TEST_MODEL": "qwen2.5:7b-instruct",
        "LLM_TEST_BASE_URL": "http://localhost:11434",
        "LLM_TEST_API_KEY": "secret-key",
        "LLM_TEST_TEMPERATURE": "0.5",
        "LLM_TEST_MAX_TOKENS": "2048",
    }):
        config = ProviderConfig.from_env("LLM_TEST")
        assert config is not None
        assert config.provider_id == "test-provider"
        assert config.provider_type == "ollama"
        assert config.model == "qwen2.5:7b-instruct"
        assert config.base_url == "http://localhost:11434"
        assert config.api_key == "secret-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048


def test_provider_config_from_env_defaults():
    """Test ProviderConfig defaults when env vars missing."""
    with patch.dict(os.environ, {
        "LLM_TEST_PROVIDER_ID": "test-provider",
    }, clear=True):
        config = ProviderConfig.from_env("LLM_TEST")
        assert config is not None
        assert config.provider_id == "test-provider"
        assert config.provider_type == "ollama"  # default
        assert config.model == "qwen2.5:7b-instruct"  # default
        assert config.base_url is None
        assert config.api_key is None
        assert config.temperature == 0.0
        assert config.max_tokens is None


def test_provider_config_from_env_missing_id():
    """Test ProviderConfig returns None when provider_id missing."""
    with patch.dict(os.environ, {}, clear=True):
        config = ProviderConfig.from_env("LLM_TEST")
        assert config is None


def test_load_provider_configs_roles():
    """Test loading provider configs for standard roles."""
    env_vars = {
        "LLM_AUDITOR_PROVIDER_ID": "auditor-provider",
        "LLM_AUDITOR_TYPE": "ollama",
        "LLM_AUDITOR_MODEL": "qwen2.5:7b-instruct",
        "LLM_ARCHITECT_PROVIDER_ID": "architect-provider",
        "LLM_ARCHITECT_TYPE": "openai",
        "LLM_ARCHITECT_MODEL": "gpt-4o",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        configs = load_provider_configs()
        assert "auditor" in configs
        assert "architect" in configs
        assert configs["auditor"].provider_id == "auditor-provider"
        assert configs["architect"].provider_id == "architect-provider"
        assert configs["auditor"].provider_type == "ollama"
        assert configs["architect"].provider_type == "openai"


def test_load_provider_configs_numbered():
    """Test loading numbered provider configs."""
    env_vars = {
        "LLM_PROVIDER_1_PROVIDER_ID": "provider-1",
        "LLM_PROVIDER_1_TYPE": "ollama",
        "LLM_PROVIDER_1_MODEL": "llama3",
        "LLM_PROVIDER_2_PROVIDER_ID": "provider-2",
        "LLM_PROVIDER_2_TYPE": "anthropic",
        "LLM_PROVIDER_2_MODEL": "claude-3-haiku",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        configs = load_provider_configs()
        assert "provider_1" in configs
        assert "provider_2" in configs
        assert configs["provider_1"].provider_id == "provider-1"
        assert configs["provider_2"].provider_id == "provider-2"


def test_get_default_role_config():
    """Test getting default role config from env."""
    with patch.dict(os.environ, {
        "LLM_AUDITOR_PROVIDER_ID": "auditor-provider",
        "LLM_AUDITOR_MODEL": "qwen2.5:7b-instruct",
    }, clear=True):
        config = get_default_role_config("auditor")
        assert config is not None
        assert config.provider_id == "auditor-provider"
        assert config.model == "qwen2.5:7b-instruct"


def test_get_default_role_config_missing():
    """Test get_default_role_config returns None when missing."""
    with patch.dict(os.environ, {}, clear=True):
        config = get_default_role_config("auditor")
        assert config is None


def test_default_role_configs_structure():
    """Test DEFAULT_ROLE_CONFIGS has expected structure."""
    expected_roles = ["auditor", "architect", "reviewer", "judge", "orchestrator"]
    for role in expected_roles:
        assert role in DEFAULT_ROLE_CONFIGS
        assert "provider" in DEFAULT_ROLE_CONFIGS[role]
        assert "model" in DEFAULT_ROLE_CONFIGS[role]
        assert DEFAULT_ROLE_CONFIGS[role]["provider"].startswith("env:")
        assert DEFAULT_ROLE_CONFIGS[role]["model"].startswith("env:")
