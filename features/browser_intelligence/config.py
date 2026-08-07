"""Browser Intelligence - configuration

Environment-driven, no Core imports. Every knob reads from the environment so
the feature stays self-contained and side-effect free at import time.
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv optional
    pass


class BrowserIntelConfig:

    def __init__(self) -> None:
        self.ollama_base = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
        self.ollama_model = os.environ.get("BROWSER_INTEL_OLLAMA_MODEL", "qwen2.5:7b-instruct")
        self.llm_provider = os.environ.get("BROWSER_INTEL_LLM", "").lower()
        self.headless = os.environ.get("BROWSER_USE_HEADLESS", "1").lower() not in ("0", "false", "no")
        self.chromium = os.environ.get("BROWSER_INTEL_CHROMIUM", "") or (
            "/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else ""
        )
        self.max_steps = int(os.environ.get("BROWSER_INTEL_MAX_STEPS", "12"))
        self.max_results = int(os.environ.get("BROWSER_INTEL_MAX_RESULTS", "5"))
        self.request_timeout_seconds = int(
            os.environ.get("BROWSER_INTEL_TIMEOUT_SECONDS", "120")
        )
        self.cloud_model = os.environ.get("BROWSER_INTEL_CLOUD_MODEL", "bu-2-0")
        self.openai_model = os.environ.get("BROWSER_INTEL_OPENAI_MODEL", "gpt-4o-mini")
        self.synthesize = os.environ.get("BROWSER_INTEL_SYNTHESIZE", "1").lower() not in ("0", "false", "no")
        self.agent_mode = os.environ.get("BROWSER_INTEL_AGENT", "0").lower() in ("1", "true", "yes")
        self.start_timeout = float(os.environ.get("BROWSER_INTEL_START_TIMEOUT", "120"))
        self.launch_timeout = float(os.environ.get("BROWSER_INTEL_LAUNCH_TIMEOUT", "120"))
        self.nav_timeout = float(os.environ.get("BROWSER_INTEL_NAV_TIMEOUT", "60"))
        self.browser_retries = int(os.environ.get("BROWSER_INTEL_BROWSER_RETRIES", "3"))
        self.synthesis_max_tokens = int(os.environ.get("BROWSER_INTEL_SYNTH_MAX_TOKENS", "512"))
        self.synthesis_timeout_seconds = int(
            os.environ.get("BROWSER_INTEL_SYNTH_TIMEOUT_SECONDS", "240")
        )

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


_CONFIG: BrowserIntelConfig | None = None


def get_config() -> BrowserIntelConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = BrowserIntelConfig()
    return _CONFIG