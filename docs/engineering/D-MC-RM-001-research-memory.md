# D-MC-RM-001 — Research Memory Architecture

**Date:** 2026-08-07
**Status:** APPLIED
**Scope:** `features/research_memory/` — new MUSCAL extension
**Core impact:** none (Core files untouched)

---

## 1. Context

Browser Intelligence (`features/browser_intelligence/`) performs expensive,
multi-minute web research. Every identical or similar question triggers a new
browser session + Ollama synthesis. The project needs a **research memory**: a
place that stores previous findings and reuses them for repeated questions.

The desired properties (mode EXECUTE, requirements supplied 2026-08-07):

- feature module under `features/`
- SQLite persistence owned by the feature (Core DB + EventStore untouched)
- no vector database, no embedding dependency (v1)
- no duplication of Browser Intelligence logic
- modular interfaces: storage / repository / service / cache / export / MCP
- tests + documentation

## 2. Requirements

1. `ResearchRecord` data model with the mandated fields (incl. `hash`, `ttl`).
2. `Confidence` (low/medium/high) and status lifecycle
   (new/reviewed/accepted/rejected/obsolete/**archived**).
3. SQLite store with `save/get/find_by_hash/list_recent/delete`.
4. `ResearchMemoryService` with `save_research/get_cached_research/
   should_refresh/promote_candidate/invalidate`.
5. MCP stdio server exposing `research_memory.search/get/promote`.
6. Tests: storage, service, MCP + plugin-loading regression + `compileall`.
7. **Independence**: Research Memory must not import Browser Intelligence;
   only an abstract `ResearchPipeline` computes fresh research (future
   Research Pipeline abstraction).
8. **MREIL metric placeholders** for the future Knowledge Foundation.

## 3. Decision

### 3.1 Module layout

```
features/research_memory/
├── __init__.py      # public API
├── config.py        # env-driven config (feature-owned DB path)
├── models.py        # ResearchRecord, Source, Confidence, RecordStatus, hash
├── storage.py       # SQLite store (lowest layer, raw CRUD)
├── repository.py    # domain access layer (ResearchRecord objects + lifecycle)
├── pipeline.py      # ResearchPipeline abstraction (provider seam)
├── cache.py         # deterministic-hash cache + freshness/TTL policy
├── service.py       # Research MemoryService orchestration
├── export.py        # JSON / JSONL / Markdown export helpers
├── mcp_server.py    # MCP stdio server (research_memory.*)
├── README.md
└── tests/           # test_storage.py, test_service.py, test_mcp.py
```

### 3.2 Data model

`ResearchRecord` fields: `id, query, context, domain, created_at, updated_at,
sources, facts, options, analysis, recommendation, confidence, status, hash, ttl`.

- `hash` = deterministic SHA-256 over normalized `query + "\x1f" + context`
  (v1 cache key, no embeddings).
- `Confidence`: `low|medium|high`; `RecordStatus`:
  `new|reviewed|accepted|rejected|obsolete|archived`.

### 3.3 Cache strategy (v1)

- Exact-match cache keyed by the deterministic hash.
- Only `new|reviewed|accepted` records are served; `rejected|obsolete|archived`
  are retained for history/export but never served fresh.
- TTL: record/`ttl` else `RESEARCH_MEMORY_DEFAULT_TTL` (env, default 7d);
  `None` disables expiry.
- `should_refresh` returns True when (a) no record, (b) record older than TTL.

### 3.4 Pipeline abstraction (independence + future Research Pipeline)

Fresh research is obtained ONLY through an injected `ResearchPipeline`
(`research(query, context="", **opts) -> dict`). Concrete providers supply a
pipeline at runtime:

- Today: a thin accessor over Browser Intelligence (lives in the consumer / a
  bridge, never inside memory) — or purely callable for tests.
- Tomorrow: web_search, Knowledge Foundation as additional pipelines; storage
  strategy stays unchanged.

This is why service.py contains **no** browser/ollama import (verified by a
unit test asserting the source text).

### 3.5 MREIL metrics placeholders

`metrics.py` defines `MREILMetrics` — in-memory counters (hits, misses,
refreshes, promotions, invalidations, exports, stored items) plus latency
fields and `knowledge_foundation.{retrieval_relevance, dedup_ratio}` stubs.
These become real signals when the Knowledge Foundation ships.

### 3.6 MCP tools

| tool | input | output |
|------|-------|--------|
| `research_memory.search` | `query` (required), `domain`?, `status`?, `limit`? | `{count, records:[...]}` |
| `research_memory.get` | `id` (required) | `{record|null}` |
| `research_memory.promote` | `id` (required) | `{record}` (NEW/REVIEWED->ACCEPTED) |

## 4. Future Knowledge Foundation integration

Research Memory is a candidate **source of experience** in the future
Knowledge Foundation. Planned join points:

1. **Embeddings/semantic recall** — replace the v1 exact-hash lookup with
   vector retrieval (chromadb) without changing service/cache interfaces.
2. **Relevance scoring & dedup** — fill `MREIL.retrieval_relevance` and
   `dedup_ratio` placeholders (today `0.0`, status `placeholder`).
3. **Persistence reuse** — export (`export.py`) targets the Foundation
   ingestion format; common taxonomy for `confidence`/`status`.

## 5. Verification

- `features/research_memory/tests/` — **34 passed** (2026-08-07):

  - storage: save/get round-trip, hash lookup (latest update wins),
    delete/count, `list_recent` ordering, filtered find, deterministic hash.
  - service: cache hit, cache miss, uppercased-payload normalization,
    refresh/TTL freshness, cache-aside pipeline `execute`, force-refresh,
    promotion (new->accepted, rejected unchanged, unknown->None),
    invalidation, archive, forget, MREI counters + snapshot, and
    independence test (source contains no `browser_intelligence`/`browser_use`).
  - mcp: 3 tools registered; search/get/promote validation + response schema.
- Plugin-loading regression (loading+audit+health): **7 passed**.
- `compileall features/research_memory` — clean.
- MCP stdio client roundtrip (2026-08-07): initialize, `list_tools` returns
  the 3 `research_memory.*`, `search` returns `isError: false`.

## 6. Known limitations

- **No semantic retrieval yet** (v1 is exact hash only).
- **TTL is coarse** — no per-domain or per-confidence age filter (v2).
- **No automatic invalidation on source publish** (push never; only manual
  `invalidate()`).
- `MREIL` semantic fields are placeholders (0.0) until Knowledge Foundation.

## 7. Files

```
features/research_memory/
├── __init__.py
├── config.py
├── models.py
├── storage.py
├── metrics.py
├── repository.py
├── pipeline.py
├── cache.py
├── service.py
├── export.py
├── mcp_server.py
├── README.md
└── tests/
    ├── test_storage.py
    ├── test_service.py
    └── test_mcp.py
```
## 8. Consequences

- The feature is self-contained, browser-independent, and testable without a
  headless Chromium or Ollama.
- A future Research Pipeline provider can slot in with zero memory changes.
- Core remains immutable; no root dependency additions (stdlib sqlite3).