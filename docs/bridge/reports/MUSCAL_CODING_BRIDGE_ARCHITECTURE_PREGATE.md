# MUSCAL Coding Bridge — Architecture Pre-Gate

## Decision
**GO**

## Authority Conflicts
None detected.

| Proposed Authority | Existing Authority | Conflict | Resolution |
|-------------------|-------------------|----------|------------|
| Git — source code | Git (verified) | None | Git remains code authority |
| EventStore — events | EventStore (verified) | None | EventStore remains canonical event authority |
| OpenCode — sessions | OpenCode (verified) | None | OpenCode remains external session authority |
| ADRs — decisions | ADRs (verified) | None | ADRs remain decision authority |
| Bridge — scanner | No existing scanner | None | New component justified |
| Bridge — adapter | No existing OpenCode adapter | None | New component justified |

## Existing Systems Reused
- `runtime/event_store.EventStore` — bridge event persistence (canonical event authority)
- `docs/session_handovers/HANDOVER_*.md` — handover format pattern (extended for machine readability)
- `features/bridge/` — existing namespace for bridge plugins (no naming conflict)
- `storage/` — existing data directory (bridge writes to EventStore, not directly to storage)

## New Components Justified
1. **`features/bridge/project_scanner.py`** — repository identity inspection (no existing equivalent)
2. **`features/bridge/opencode_adapter.py`** — subprocess wrapper for `opencode run --format json` (no existing equivalent)
3. **`features/bridge/result_normalizer.py`** — evidence-based result classification (no existing equivalent)
4. **`features/bridge/bridge_event_writer.py`** — writes typed bridge events to EventStore (no existing equivalent)
5. **`features/bridge/handoff_report.py`** — structured handoff generation (extends existing handover pattern)
6. **`features/bridge/orchestrator.py`** — coordinates full bridge flow (new adapter layer)

## Components Rejected
- **knowledge_writer.py** — renamed to `bridge_event_writer.py` per A4 constraint (bridge writes events, not knowledge)
- **state.yaml inside features/bridge/** — placed in `docs/bridge/state/` per A5 constraint (not inside Python source)
- **AGENTS.yaml registration** — bridge is an infrastructure adapter, not an agent; schema has no "infrastructure" type; registered via README instead

## State Location
`docs/bridge/state/`
- `current.yaml` — derived runtime view (not independent authority)
- `snapshots/` — immutable timestamped execution snapshots

## Event Location
`bridge.execution` topic in `runtime/event_store.EventStore` (canonical event authority)

## Report Location
`docs/bridge/reports/`
- Iteration 1 discovery reports
- Bridge execution reports

Handovers placed in `docs/bridge/handovers/` (parallel to existing `docs/session_handovers/`)

## P0 Blockers
None.

## P1 Conditions
1. Bridge must snapshot git state before/after execution (dirty working tree)
2. Bridge events target EventStore only (no duplicate persistence)
3. All new components in `features/bridge/` with clear naming
4. No core/immutable files modified
