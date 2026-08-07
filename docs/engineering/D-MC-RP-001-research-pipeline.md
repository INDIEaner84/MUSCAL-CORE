# D-MC-RP-001 — Research Pipeline Architecture

**Date:** 2026-08-07
**Status:** APPLIED
**Scope:** `features/research_pipeline/` — new MUSCAL extension
**Core impact:** none (Core files untouched)

---

## 1. Context

MUSCAL has two independent research features:

- **Browser Intelligence** (`features/browser_intelligence/`) — executes web
  research (browser-use + Ollama) and returns structured `ResearchFindings`.
- **Research Memory** (`features/research_memory/`) — persists findings in a
  feature-owned SQLite DB and serves them back via a deterministic hash cache.

There is no orchestration layer: consumers (OpenCode/MCP) must choose between
"run expensive research" and "reuse memory" themselves, and every new provider
(github, docs, local knowledge) would have to re-implement the same flow.

This decision introduces the **Research Pipeline**: one entry point that
implements the cache-aside flow and abstracts providers behind an interface,
so new providers plug in without touching memory or browser logic.

## 2. Requirements

1. Unified `research.execute` MCP tool (cache-first, provider on miss).
2. Provider abstraction (`ResearchProvider`) + adapter for Browser Intelligence.
3. No direct `browser_use` imports in the pipeline layer.
4. Research Memory and Browser Intelligence behavior preserved (no redesign).
5. Extension points for future providers (github, documentation, local knowledge).
6. Tests (pipeline flow, adapter, MCP) + plugin-loading regression + `compileall`.

## 3. Decision

### 3.1 Module layout

```
features/research_pipeline/
├── __init__.py       # public API
├── config.py         # env-driven config
├── models.py         # ResearchRequest / ResearchResult + depth constraints
├── interfaces.py     # ResearchProvider ABC, ResearchProviderError
├── registry.py       # named provider registry (lazy factories)
├── service.py        # ResearchPipelineService (cache-aside flow)
├── adapters/
│   ├── __init__.py
│   └── browser_intelligence.py   # Browser Intelligence adapter
├── mcp_server.py     # MCP stdio server, tool research.execute
├── README.md
└── tests/            # test_pipeline_service / test_browser_adapter / test_mcp_server
```

### 3.2 Data model

`ResearchRequest`: `question` (required), `context`, `depth`
(`quick|standard|deep`), `force_refresh`, `metadata` (provider hint,
constraints, domain).

`ResearchResult`: `source`, `facts`, `analysis`, `options`, `recommendation`,
`confidence`, `sources`, `warnings`, `timestamp`.

Depth maps to provider constraints via `resolve_constraints()` (mirrors
Browser Intelligence semantics without importing it).

### 3.3 Pipeline flow (cache-aside)

1. Validate request (question required, depth allowed).
2. If not `force_refresh`: `ResearchMemoryService.get_cached_research()`.
3. Hit -> `ResearchResult(source="research_memory")`.
4. Miss -> select provider via registry (metadata hint or default).
5. `provider.research(request)` -> normalized `ResearchResult`.
6. Persist into Research Memory (facts/analysis/options/recommendation/
   confidence/sources).
7. Return result.

### 3.4 Provider interface & adapter

```python
class ResearchProvider(abc.ABC):
    name: str = "abstract"
    async def research(self, request: ResearchRequest) -> ResearchResult: ...
```

`BrowserIntelligenceAdapter` translates the request (question/context/depth ->
ResearchService API) and normalizes output (accepts dicts with lowercase or
uppercase keys, or objects with `.to_dict()`). Errors are wrapped in
`ResearchProviderError`. The default backend imports Browser Intelligence
lazily inside the async call so module import stays side-effect free.

### 3.5 Registry & extension model

`ResearchProviderRegistry` registers lazy factories by name. Initial provider:
`browser_intelligence`. Extension points reserved: `github`, `documentation`,
`local_knowledge` (registering new providers is one call; no pipeline change).

### 3.6 MCP tool

`research.execute` — input `{question, context?, depth?, force_refresh?}`,
output `{facts, analysis, options, recommendation, confidence, sources,
warnings}`. FastMCP stdio server, same pattern as the other feature servers.

## 4. Verification

- `features/research_pipeline/tests/` — **19 passed** (2026-08-07):
  - pipeline service: cache hit does not call provider; miss calls provider;
    miss persists; force_refresh bypasses cache and overwrites memory;
    unknown provider raises; request validation.
  - adapter: request reaches backend; sync + async backends; uppercase and
    object result normalization; sources normalization; error wrapping;
    empty-result error.
  - MCP: tool registration (`research.execute`), input schema
    (`required: ["question"]`), validation errors, response schema, cache
    reuse on repeat call.
- `features/research_memory/tests/` — **34 passed** (regression; `cache.put`
  now updates in place per hash).
- Plugin-loading regression (loading/audit/health): **7 passed**.
- `compileall features/research_pipeline` — clean.
- Live MCP stdio roundtrip: initialize, `list_tools` -> `research.execute`,
  invalid input -> `isError: true`.
- Live adapter smoke test drove the real Browser Intelligence session
  successfully (Google search navigated; research completes in minutes on this
  CPU-bound box).

## 5. Known limitations

- Default provider resolution is by name string; no failover/fallback chain yet.
- No provider health/priority model (a failed provider aborts the request).
- No streaming; MCP tool blocks until research completes (minutes on CPU-bound
  Ollama).
- Cache is exact-hash (v1); semantic recall comes with the Knowledge Foundation.

## 6. Consequences

- One entry point for consumers; memory reuse is automatic.
- New providers are one adapter + one registry call — no pipeline changes.
- Browser Intelligence / Research Memory remain untouched and independently
  testable.
- Core stays immutable; no root dependency additions.

## 7. Files

```
features/research_pipeline/
├── __init__.py
├── config.py
├── models.py
├── interfaces.py
├── registry.py
├── service.py
├── mcp_server.py
├── README.md
├── adapters/
│   ├── __init__.py
│   └── browser_intelligence.py
└── tests/
    ├── conftest.py
    ├── test_pipeline_service.py
    ├── test_browser_adapter.py
    └── test_mcp_server.py
```
