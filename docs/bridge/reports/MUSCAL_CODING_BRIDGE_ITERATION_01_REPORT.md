# MUSCAL Coding Bridge — Iteration 1 Discovery Report

## A. Executive Result

```
GO WITH CONDITIONS
```

Conditions:
- Working tree is dirty (25 modified, ~70 untracked files) — bridge must snapshot state before/after
- No remote configured — CI/backup concern, not a bridge blocker
- HDR-001 through HDR-004 referenced but not found as canonical records

## B. Canonical Project Identity

| Attribute | Value |
|-----------|-------|
| Root | `/home/hz/AlitaProject/Codebase/MUSCAL CORE` |
| Repository | Single git repo |
| Branch | `main` |
| Commit | `cdaa1c29e18417af78ad180a2f652cbfa7c0dff4` |
| Modified | 25 files |
| Untracked | ~70 files |
| Remote | None configured |
| Commits | 42 |

## C. OpenCode Capability Matrix

| Capability | Status | Evidence | Recommended Use |
|-----------|--------|----------|----------------|
| CLI available | verified | `/home/hz/.opencode/bin/opencode` v1.18.7 | Primary interface |
| Headless execution | verified | `opencode run --format json` | Bridge task submission |
| Session continuity | verified | `-c/--continue`, `-s/--session`, `--fork` | Resume interrupted bridges |
| Session export (JSON) | verified | `opencode export [sessionID]` | Result capture |
| Session import | verified | `opencode import <file>` | Restore session |
| Session list | verified | `opencode session list` | Monitor bridges |
| Headless server | verified | `opencode serve` | Long-running endpoint |
| ACP server | verified | `opencode acp` | Agent-to-agent protocol |
| MCP management | verified | `opencode mcp` | External tools |
| JSON output | verified | `opencode run --format json` | Parseable results |
| Programmatic API | partial | No native REST API; `opencode serve` available | CLI adapter pattern |
| Session-to-repo binding | partial | No built-in repo tracking | Enforce via bridge wrapper |
| Built-in IPC | partial | `opencode attach` / `opencode serve` | Bridge adapter handles |
| Event subscription | unavailable | No native event stream | Use MUSCAL EventBus |
| Project state API | unavailable | No native project state | Use MUSCAL state infra |

## D. MUSCAL Continuity Matrix

| Continuity Layer | Existing Component | Maturity | Action |
|-----------------|-------------------|----------|--------|
| Project state | `docs/PROJECT_STATE.md` | stable/manual | Extend with machine-readable YAML frontmatter |
| Session registry | `docs/governance/SESSION_REGISTRY.md` | stable/manual | Extend with auto-generated entries |
| Checkpoint index | `docs/governance/CHECKPOINT_INDEX.md` | stable/manual | Reuse append-only contract |
| Session handovers | 13 `HANDOVER_*.md` files | stable | Reuse format for bridge handovers |
| Event persistence | `EventStore` (`runtime/event_store.py`) | stable | Reuse as canonical event authority |
| Event bus | `EventBus` (`event_bus.py`) | stable | Reuse for bridge events |
| Decision ledger | 14 ADRs (`spec/ADR-*.md`) + 3 new ADRs | stable | Reuse; add bridge ADR |
| Execution history | `features/execution/validation_store.py` | partial | Investigate for bridge storage |
| Knowledge index | `graph_memory.py`, `memory.py`, `rag.py` | stable | Context retrieval only |
| Provenance tracker | `features/provenance/` | partial | Bridge traceability |
| Task state | `WORK_QUEUE.md`, `ACTIVE_TASKS.md` | partial/manual | Extend for bridge-aware tracking |
| Agent registry | `AGENTS.yaml` (`.opencode/REGISTRY/`) | stable | Register bridge as infra component |

## E. Existing Knowledge Infrastructure

| Aspect | Status |
|--------|--------|
| ADR repository | 14 legacy + 3 new ADRs — immutable, append-only |
| Architecture records | `TECHNICAL_BASELINE.md` stable; `ARCHITECTURE.md` not found |
| Memory systems | `memory.py` (SQLite+JSONL), `graph_memory.py`, `features/memory/` |
| Event store | Append-only SQLite with cursor-based replay — canonical |
| Audit trail | 30+ reports in `docs/audit/` (untracked) |
| Checkpoints | 1 checkpoint file — MVP needs automated checkpointing |
| Duplication risk | Medium — multiple memory backends (graph_memory, memory, rag, mcxf_memory) |
| Missing: bridge knowledge writer | No component writes structured execution results into knowledge store |
| Missing: structured handoff | Session handovers exist but not machine-parseable |
| Missing: automated state snapshot | `PROJECT_STATE.md` manually updated |

## F. Bridge MVP Gap Matrix

| Required Capability | Existing | Missing | Priority |
|--------------------|----------|---------|----------|
| Project scanner | git commands available | No wrapper | P1 |
| Project context builder | `PROJECT_STATE.md` (manual) | No automated assembly | P1 |
| OpenCode adapter | `opencode run --format json` | No Python wrapper | P0 |
| Execution result capture | `opencode export [session]` | No structured parser | P0 |
| Result normalizer | None | Must create | P0 |
| Event writer (bridge events) | EventStore | No bridge-specific writer | P1 |
| Structured handoff report | None | Must create | P1 |
| Machine-readable bridge state | None | Must create | P1 |
| Bridge session ID tracking | None | Correlation tracking | P2 |
| Error recovery | None | Deferred to Iteration 3 | P3 |

## G. Risks

| Priority | Risk | Mitigation |
|----------|------|------------|
| P0 | Dirty working tree; bridge may operate on dirty state | Snapshot git diff before/after |
| P0 | No remote configured — no backup/CI | Document as infra concern |
| P1 | `features/bridge/` namespace collision | Bridge MVP files isolated in same directory |
| P1 | Multiple memory/knowledge systems | Bridge events target EventStore as canonical |
| P2 | HDR-001-004 unresolved blockers | May be in untracked docs/audit/ |
| P3 | Two API servers (Flask :5001, FastAPI :8000) | Bridge avoids depending on either |

## H. Recommended Iteration 2

Create minimal MUSCAL Coding Bridge MVP — CLI adapter wrapping `opencode run --format json`, producing structured execution records in EventStore.

Components:
- `project_scanner.py` — repository identity inspection
- `opencode_adapter.py` — subprocess wrapper around `opencode run --format json`
- `result_normalizer.py` — parse and classify execution output
- `bridge_event_writer.py` — write execution events to EventStore
- `handoff_report.py` — generate Markdown + YAML handoff
- `orchestrator.py` — coordinate the full bridge flow
