# Browser Intelligence (MUSCAL feature)

LLM-driven web research for the MUSCAL development workflow, powered by
[Browser-Use](https://github.com/browser-use/browser-use) (v0.13.7) and the
local Ollama instance. Exposes a `ResearchService` abstraction that can later
back MCP tools or other research providers.

```
OpenCode / CLI / tests
        |
   ResearchService          (features/browser_intelligence/)
        |
   BrowserUseProvider       (providers/browser_use.py)
        |
   browser-use (Agent | BrowserSession)
        |
   Chromium (headless)
```

## Setup

All dependencies are installed into the **shared project venv** at the
repository root (`./.venv`), not into a feature-local venv.

```bash
# 1. Create the shared venv (if not already present)
python3 -m venv .venv

# 2. Install dependencies (pinned in this directory)
.venv/bin/pip install -r features/browser_intelligence/requirements.txt

# 3. Browser binaries
#    Either install Playwright's Chromium:
.venv/bin/playwright install chromium
#    Or point at the system Chromium via BROWSER_INTEL_CHROMIUM.

# 4. LLM: the local Ollama instance is used automatically if reachable.
#    No API key needed for the default path.
```

## Quick start

```python
from features.browser_intelligence import ResearchService

findings = ResearchService().research(
    "What are the installation requirements of the browser-use library?",
    constraints=["answer concisely", "name the Python version and pip command"],
)
print(findings.to_markdown())
```

Structured output contains: `FACTS`, `ANALYSIS`, `OPTIONS`,
`RECOMMENDATION`, `CONFIDENCE` (Low/Medium/High) plus `SOURCES`.

### CLI

```bash
.venv/bin/python -m features.browser_intelligence.cli "research question"
```

### Tests

```bash
.venv/bin/python -m pytest features/browser_intelligence/tests/ -v
```

## Execution modes

| Mode | Trigger | What happens |
|------|---------|--------------|
| Extract (always) | default | `BrowserSession` navigates Google -> Bing -> DuckDuckGo and reads page text. No LLM. |
| Synthesis (default) | `BROWSER_INTEL_SYNTHESIZE=1` (default) | One LLM call (local Ollama preferred) turns the raw extract into the structured report. |
| Agent (opt-in) | `BROWSER_INTEL_AGENT=1` | Full browser-use `Agent` loop; the chat model drives navigation. Requires a fast LLM. |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BROWSER_INTEL_LLM` | (auto) | `ollama` / `openai` / `browseruse` / `none` |
| `BROWSER_INTEL_OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Ollama model for synthesis/agent |
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama endpoint (shared with MUSCAL) |
| `BROWSER_INTEL_AGENT` | `0` | Enable agent mode |
| `BROWSER_INTEL_SYNTHESIZE` | `1` | Enable LLM synthesis of raw extracts |
| `BROWSER_INTEL_MAX_STEPS` | `12` | Agent loop cap |
| `BROWSER_INTEL_MAX_RESULTS` | `5` | Max facts from extraction |
| `BROWSER_INTEL_CHROMIUM` | `/usr/bin/chromium` if present | Path to a Chromium binary |
| `BROWSER_INTEL_START_TIMEOUT` | `120` | Seconds allowed for browser session start |
| `BROWSER_INTEL_LAUNCH_TIMEOUT` | `120` | Seconds allowed for the local Chromium launch |
| `BROWSER_INTEL_NAV_TIMEOUT` | `60` | Seconds allowed for page navigation |
| `BROWSER_INTEL_BROWSER_RETRIES` | `3` | Retries for the browser start/extract phase |
| `BROWSER_INTEL_SYNTH_MAX_TOKENS` | `512` | Token budget for the synthesis LLM call |
| `BROWSER_INTEL_SYNTH_TIMEOUT_SECONDS` | `240` | Read timeout for the synthesis LLM call |
| `BROWSER_USE_HEADLESS` | `1` | Set to `0` for a visible browser |

## MCP gateway integration

Two ways to expose the research capability as the tool `browser_intelligence.research`:

### 1. Native MCP stdio server (OpenCode)

A standalone MCP server that publishes `browser_intelligence.research` over
JSON-RPC on stdio — this is the format OpenCode consumes directly. The tool
reuses `ResearchService` unchanged and returns structured findings:

```
question (str, required)  context (str, optional)  depth (quick|standard|deep, default standard)
  └──> { facts, analysis, options, recommendation, confidence, warnings, sources }
```

```bash
.venv/bin/python -m features.browser_intelligence.mcp_server
```

OpenCode config (`opencode.json`):

```jsonc
{
  "mcp": {
    "browser-intelligence": {
      "type": "stdio",
      "command": "/home/hz/AlitaProject/Codebase/MUSCAL CORE/.venv/bin/python",
      "args": ["-m", "features.browser_intelligence.mcp_server"]
    }
  }
}
```

Verified against the `mcp` client SDK: initialize handshake, `tools/list`
returns exactly one tool, invalid input surfaces as `isError: true` with the
validation message.

```python
# Call the tool programmatically (any MCP client, incl. a future OpenCode session)
from features.browser_intelligence.mcp_server import run_research

result = run_research({"question": "What is MUSCAL?", "depth": "deep"})
```

### 2. Internal MCP gateway registration

The same capability registers into the existing MUSCAL interface gateway /
Unified Tool Runtime:

```python
from features.browser_intelligence.mcp_registration import register_research_tool

register_research_tool()  # registers into MCPGateway + ToolRegistry
```

Registration is guarded: it never raises and reports status dicts.

## Constraints / notes

- MUSCAL Core is untouched; everything lives under `features/`.
- Imports of `browser_use` and `mcp` are lazy (inside the server/tool
  functions) so the plugin loader never chokes on a system python without the
  venv packages. `mcp_server.py` triggers no side effects at import time and
  needs no `Plugin` class (it runs as a separate stdio process).
- Search engines occasionally block headless browsers (captcha); captcha pages
  are detected and skipped so the fallback engine chain (Google -> Bing ->
  DuckDuckGo) is used instead. The module degrades gracefully (Low confidence
  + warning) instead of failing.
- Local browser start is retried up to `BROWSER_INTEL_BROWSER_RETRIES` times
  (default 3) because the default browser-use event budgets (30s) race slow
  Chromium cold starts on loaded machines; the feature raises its own
  start/launch budgets via `BROWSER_INTEL_*_TIMEOUT` accordingly.
- On CPU-only Ollama the LLM calls are slow (~1-3 min). Prefer a warm model
  or a GPU-backed Ollama for agent mode.
