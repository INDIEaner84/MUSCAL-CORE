# Research Memory (MUSCAL feature)

Persistent, cacheable storage for research results. Stores prior findings in a
feature-owned SQLite database and reuses them instead of re-running expensive
web research (Browser Intelligence) every time.

```
OpenCode / CLI          (+ future: Knowledge Foundation)
    |
ResearchMemoryService   (features/research_memory/)
    |                                |
ResearchMemoryCache              ResearchPipeline (abstract)
    |                                └── supplied by a provider at runtime
research_hash (sha256 query+context)      (today: Browser Intelligence accessor)
    |
ResearchMemoryRepository
    |
ResearchMemoryStore  ←-- SQLite  (features/research_memory/data/research_memory.db)
```

**Design rules (architecture summary)**

- **Independent of Browser Intelligence.** This feature never imports
  `browser_intelligence` / `browser_use`. Fresh research is computed only via
  an injected `ResearchPipeline` (see `pipeline.py`). This makes Research
  Memory provider-agnostic and testable without a browser or Ollama.
- **No vector DB.** v1 cache strategy is a deterministic SHA-256 over
  normalized `query + context`. Embeddings/semantic search are a future
  Knowledge Foundation concern (see `D-MC-RM-001-research-memory.md` §4).
- **Feature-owned storage.** The SQLite database lives under
  `features/research_memory/data/`. The Core database and EventStore are never
  touched.
- **MREIL placeholders.** `metrics.py` holds the `MREIL` counter+latency
  placeholders (hits, misses, refreshes, latency) that the future Knowledge
  Foundation will extend with relevance/dedup signals.

## Data model

`ResearchRecord` fields: `id, query, context, domain, created_at, updated_at,
sources, facts, options, analysis, recommendation, confidence, status, hash, ttl`.

- **Confidence:** `low | medium | high`
- **Status:** `new | reviewed | accepted | rejected | obsolete | archived`
  - `cache` serves `new`, `reviewed`, `accepted`
  - `rejected`/`obsolete`/`archived` are kept (history/export) but never served
    as fresh memory
- **ttl:** time-to-live in seconds; config default `RESEARCH_MEMORY_DEFAULT_TTL`
  (7 days). `None` disables the TTL check.

## Quickstart (Python)

```python
from features.research_memory import ResearchMemoryService, FunctionResearchPipeline

service = ResearchMemoryService()

# 1. Run research via an injected pipeline (here: any callable that returns
#    a payload dict; uppercase FACTS/ANALYSIS/... is accepted too).
def my_provider(query, context=""):
    return {"facts": ["...", "..."], "analysis": "...", "recommendation": "..."}

service.save_research("is feature X stable?", payload={"facts": ["yes, v1.2"]})

# 2. Cache-aside: return stored memory or compute via pipeline.
record = service.execute(
    "is feature X stable?",
    FunctionResearchPipeline(find_provider),
)
print(record.to_markdown())

# 3. Lifecycle.
record  = service.get_cached_research("is feature X stable?")
service.promote_candidate(record.id)   # new/reviewed -> accepted
service.invalidate(record.id)          # -> obsolete (soft delete)
service.archive(record.id)             # -> archived
```

## MCP server

Expose stored research memory to opencode / MCP clients:

```bash
.venv/bin/python -m features.research_memory.mcp_server
```

| tool | input | output |
|------|-------|--------|
| `research_memory.search` | `query` (required), optional `domain`, `status`, `limit` | `{count, records:[ResearchRecord]}` |
| `research_memory.get` | `id` (required) | `{record: ResearchRecord \| null}` |
| `research_memory.promote` | `id` (required) | `{record}` after NEW/REVIEWED -> ACCEPTED |

opencode config:

```jsonc
{
  "mcp": {
    "research-memory": {
      "type": "stdio",
      "command": "/home/hz/AlitaProject/Codebase/MUSCAL CORE/.venv/bin/python",
      "args": ["-m", "features.research_memory.mcp_server"]
    }
  }
}
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RESEARCH_MEMORY_DB_PATH` | `features/research_memory/data/research_memory.db` | SQLite file location |
| `RESEARCH_MEMORY_DEFAULT_TTL` | `604800` (7 days) | default record TTL in seconds (`none` to disable) |
| `RESEARCH_MEMORY_MAX_RESULTS` | `100` | list/search limits |
| `RESEARCH_MEMORY_METRICS` | `1` | enable MREIL counter tracking |

## Tests

```bash
.venv/bin/python -m pytest features/research_memory/tests/ -v
.venv/bin/python -m pytest tests/test_plugin_loading.py           # regression
```

## Future / Knowledge Foundation mapping

See `docs/engineering/D-MC-RM-001-research-memory.md` §4. In short: Research
Memory becomes one *source of experience* inside the future Knowledge
Foundation; embeddings/relevance and dedup metrics plug into the MREIL
placeholder fields.