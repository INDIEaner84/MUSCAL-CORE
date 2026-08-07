# D-MC-BI-001 — Browser Intelligence Architecture

**Date:** 2026-08-04
**Status:** APPLIED
**Scope:** `features/browser_intelligence/` — new MUSCAL extension
**Core impact:** none (Core files untouched)

---

## 1. Context

The MUSCAL development workflow needs browser-based research (search docs,
inspect GitHub repos, collect technical facts) without coupling a browser
stack into the Core. MUSCAL already declares browser tool stubs
(`features/tools/browser_tool.py`, `features/interface_gateway/browser_adapter.py`)
that are unimplemented and dead code.

Browser-Use (MIT, PyPI 0.13.7) was selected as the research engine because:

- Official library with an LLM-driven agent AND a low-level session API
  (works without any LLM).
- Supports local Ollama out of the box (`browser_use.llm.ollama.chat.ChatOllama`).
- MUSCAL already runs a local Ollama instance (`OLLAMA_BASE` in `.env.example`).

## 2. Requirements

1. Browser-Use installed and configured, defaulting to the local Ollama.
2. MUSCAL Core untouched.
3. Feature implemented as a plugin/module under `features/`.
4. `ResearchService` abstraction that can later support Browser-Use, MCP
   tools, or other research providers.
5. Minimal working end-to-end test (question -> browser search -> structured
   result).
6. README + setup instructions + architecture notes.

## 3. Decision

### 3.1 Module location

`features/browser_intelligence/` — satisfies the "ALL EXTENSIONS GO TO
/features/" rule and keeps the feature self-contained.

### 3.2 Provider abstraction

```text
ResearchService (facade, sync+async)
  └── ResearchProvider (ABC)
        └── BrowserUseProvider (browser-use)
        (future: MCP provider, web_search provider)
```

`ResearchService.research()` returns `ResearchFindings` with the mandated
output contract: `FACTS`, `ANALYSIS`, `OPTIONS`, `RECOMMENDATION`,
`CONFIDENCE` (+ `SOURCES`).

### 3.3 LLM resolution order (default = local Ollama)

1. `BROWSER_INTEL_LLM=ollama` or Ollama reachable -> native `ChatOllama`
2. `OPENAI_API_KEY` -> `ChatOpenAI`
3. `BROWSER_USE_API_KEY` -> `ChatBrowserUse`
4. none -> deterministic extraction only (no LLM)

### 3.4 Execution modes

| Mode | Default | Description |
|------|---------|-------------|
| Extract | always | BrowserSession navigates search engines (Google -> Bing -> DDG), reads page text. LLM-free. |
| Synthesis | on | ONE LLM call turns the raw extract into the structured report. |
| Agent | off (`BROWSER_INTEL_AGENT=1`) | Full browser-use Agent loop (LLM drives navigation). |

Rationale: the local Ollama is CPU-bound on the current machine (~1-3 min per
LLM call). Agent mode would time out per step; a single synthesis call is
feasible. Agent mode stays available for faster LLMs (GPU-backed Ollama or
remote keys).

### 3.5 MCP integration

Two layers expose the research capability as tool `browser_intelligence.research`:

**a) Native MCP stdio server (`mcp_server.py`)** — JSON-RPC over stdio via
`mcp.server.fastmcp.FastMCP` (SDK `mcp>=1.26.0`, installed in the shared
venv). Serves exactly one tool with input `{question, context, depth}` and
output `{facts, analysis, options, recommendation, confidence, warnings,
sources}`. The tool body calls the same `ResearchService` used by CLI and
tests — no duplicate research logic. Module is import-light (lazy
`mcp`/`browser_use` imports) and side-effect-free at import time, so it
satisfies the plugin loader contract without a `Plugin` class (it runs as a
separate process).

**b) Internal gateway registration** — `mcp_registration.register_research_tool()`
registers into `features/interface_gateway/mcp_gateway.py` and the Unified
Tool Runtime registry. Registration is guarded (no-op + status dict on
failure) so the feature never breaks Core boot.

## 4. Verification

- `features/browser_intelligence/tests/test_research_e2e.py` — 2 passed
  (2026-08-04, re-run 2026-08-07), including a real browser+Ollama research run.
- `features/browser_intelligence/tests/test_mcp_server.py` — 8 passed
  (2026-08-07): tool registration/schema, input validation, ResearchService
  mapping (fake + patched real class), gateway registration compatibility.
- MCP stdio round-trip against the `mcp` client SDK (2026-08-07): initialize
  handshake, `tools/list` -> exactly `browser_intelligence.research` with
  `question` required, invalid input returns `isError: true` + message.
- CLI smoke: `.venv/bin/python -m features.browser_intelligence.cli "..."`.
- Plugin loader regression: `tests/test_plugin_loading.py` (+ audit/health) —
  7 passed (2026-08-07).
- MCP gateway: tool `browser_intelligence.research` registers and is
  discoverable.

## 5. Alternatives considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Direct MCP stdio server (`mcp` SDK) as OpenCode tool | native OpenCode tool integration, reuses ResearchService | extra dependency, transport layer work | **chosen (2026-08-07)** |
| Official browser-use MCP server (`uvx ... browser-use --mcp`) | zero code | bypasses ResearchService abstraction, requires remote API key, couples OpenCode directly to browser-use | not chosen |
| Playwright directly | no new dep | no LLM agent, no a11y-tree extraction, duplicates existing dead stubs | not chosen |
| langchain ChatOllama | familiar API | incompatible with browser-use 0.13 BaseChatModel protocol (verified: `AttributeError: provider`) | rejected after empirical test |

## 6. Consequences

- **+** Research capability is testable end-to-end without API keys.
- **+** Provider abstraction allows MCP/web providers later without API change.
- **+** Core stays immutable; no root dependency pollution (pins live in the
  feature).
- **-** Search engines may captcha headless browsers; graceful degradation
  (Low confidence + warning) is the designed fallback.
- **-** Local CPU-only Ollama is slow; synthesis is one LLM call by design.

## 7. Files

```
features/browser_intelligence/
├── __init__.py
├── config.py
├── models.py
├── llm.py
├── research_service.py
├── cli.py
├── mcp_registration.py
├── mcp_server.py
├── requirements.txt
├── README.md
├── providers/
│   ├── __init__.py
│   ├── base.py
│   └── browser_use.py
└── tests/
    ├── test_mcp_server.py
    └── test_research_e2e.py
```
