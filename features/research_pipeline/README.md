# Research Pipeline (MUSCAL feature)

Unified research orchestration layer between OpenCode/MCP, Research Memory and
research providers (Browser Intelligence today).

```
OpenCode / MCP
     |
     v
research.execute (MCP tool)
     |
ResearchPipelineService
     |                  \
     | cache-aside       \-- select provider (registry)
     |                   v
Research Memory      ResearchProvider (interface)
(SQLite, feature)     |  adapters
                     v
              BrowserIntelligenceAdapter
                     |
              Browser Intelligence (untouched)
```

## Architecture summary

- **Orchestration only.** The pipeline layer contains no research logic: it
  serves fresh memory when possible, otherwise delegates to a provider via the
  `ResearchProvider` interface and persists the result into Research Memory.
- **Adapters keep providers out of the pipeline.** `BrowserIntelligenceAdapter`
  translates `ResearchRequest` -> Browser Intelligence API and normalizes the
  result. No `browser_use` import anywhere in this feature.
- **Provider registry.** `ResearchProviderRegistry` maps names to lazy
  factories. Initial provider: `browser_intelligence`. Extension points
  prepared for `github`, `documentation`, `local_knowledge`.
- **Behavior preserved.** Browser Intelligence and Research Memory are not
  modified by this feature; the pipeline composes them.

## Data flow

1. Receive `ResearchRequest` (`question`, `context?`, `depth?`,
   `force_refresh?`, `metadata?`).
2. If `force_refresh` is false: ask Research Memory for a fresh cached result
   (deterministic hash over `query + context`, TTL-aware).
3. Cache hit -> return `ResearchResult` (`source="research_memory"`).
4. Cache miss -> select provider from the registry.
5. Execute provider (adapter normalizes to `ResearchResult`).
6. Persist the result into Research Memory.
7. Return `ResearchResult`.

## Usage

```python
import asyncio
from features.research_pipeline import (
    ResearchPipelineService,
    ResearchRequest,
)

service = ResearchPipelineService()

result = asyncio.run(service.research(
    ResearchRequest(question="is browser-use stable?", context="python", depth="standard")
))
print(result.to_dict())
```

Custom provider (future extension point):

```python
from features.research_pipeline import ResearchProvider, ResearchProviderRegistry, ResearchRequest, ResearchResult

class GitHubProvider(ResearchProvider):
    name = "github"
    async def research(self, request: ResearchRequest) -> ResearchResult:
        return ResearchResult(source=self.name, facts=["..."], ...)

registry = ResearchProviderRegistry()
registry.register("github", lambda: GitHubProvider())
service = ResearchPipelineService(registry=registry)
```

## MCP

```bash
.venv/bin/python -m features.research_pipeline.mcp_server
```

| tool | input | output |
|------|-------|--------|
| `research.execute` | `question` (required), `context?`, `depth?`, `force_refresh?` | `{facts, analysis, options, recommendation, confidence, sources, warnings}` |

opencode config:

```jsonc
{
  "mcp": {
    "research-pipeline": {
      "type": "stdio",
      "command": "/home/hz/AlitaProject/Codebase/MUSCAL CORE/.venv/bin/python",
      "args": ["-m", "features.research_pipeline.mcp_server"]
    }
  }
}
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RESEARCH_PIPELINE_PROVIDER` | `browser_intelligence` | default provider name |
| `RESEARCH_PIPELINE_DEPTH` | `standard` | default depth (`quick`/`standard`/`deep`) |
| `RESEARCH_MEMORY_DB_PATH` | (memory feature default) | where results are cached |

## Tests

```bash
.venv/bin/python -m pytest features/research_pipeline/tests/ -v
.venv/bin/python -m pytest features/research_memory/tests/ -v
.venv/bin/python -m pytest tests/test_plugin_loading.py
```

## Related documents

- `docs/engineering/D-MC-RP-001-research-pipeline.md` — architecture decision
- `docs/engineering/D-MC-RM-001-research-memory.md` — research memory (cache)
- `features/research_memory/README.md`
- `features/browser_intelligence/README.md`