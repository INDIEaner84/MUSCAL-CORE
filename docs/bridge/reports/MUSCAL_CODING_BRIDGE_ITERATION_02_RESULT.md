# MUSCAL Coding Bridge — Iteration 2 Result

## Decision
**GO**

## Architecture Pre-Gate
- **Authority conflicts:** None detected.
- **Resolved:** Proposed authority map matches existing repository ownership exactly.
- **Remaining:** None.

## Components

### Reused
- `runtime/event_store.EventStore` — canonical event authority for bridge execution events
- `docs/session_handovers/HANDOVER_*.md` — handover format pattern
- `features/bridge/` — existing namespace (populated empty `__init__.py`)
- `docs/governance/CHECKPOINT_INDEX.md` — append-only checkpoint pattern

### Created
- `features/bridge/project_scanner.py` — typed project context scanner
- `features/bridge/opencode_adapter.py` — subprocess wrapper around `opencode run --format json`
- `features/bridge/result_normalizer.py` — evidence-based result classification with verified/observed/inferred/unknown separation
- `features/bridge/bridge_event_writer.py` — writes typed `bridge.execution` events to EventStore
- `features/bridge/handoff_report.py` — generates Markdown + YAML structured handoff reports
- `features/bridge/orchestrator.py` — coordinates full bridge flow (`run_bridge()` entry point)
- `features/bridge/__init__.py` — exports all bridge components

### Rejected
- `knowledge_writer.py` — renamed to `bridge_event_writer.py` (bridge writes events, not knowledge)
- `state.yaml` inside `features/bridge/` — placed in `docs/bridge/state/` (not inside Python source)
- `AGENTS.yaml` registration — bridge is an infrastructure adapter, not an agent; schema has no matching type

## Files Created
- `features/bridge/__init__.py`
- `features/bridge/project_scanner.py`
- `features/bridge/opencode_adapter.py`
- `features/bridge/result_normalizer.py`
- `features/bridge/bridge_event_writer.py`
- `features/bridge/handoff_report.py`
- `features/bridge/orchestrator.py`
- `tests/bridge/__init__.py`
- `tests/bridge/test_project_scanner.py` (9 tests)
- `tests/bridge/test_opencode_adapter.py` (9 tests)
- `tests/bridge/test_result_normalizer.py` (7 tests)
- `tests/bridge/test_bridge_event_writer.py` (6 tests)
- `tests/bridge/test_handoff_report.py` (5 tests)
- `tests/bridge/test_orchestrator.py` (5 tests)
- `docs/bridge/reports/MUSCAL_CODING_BRIDGE_ITERATION_01_REPORT.md`
- `docs/bridge/reports/MUSCAL_CODING_BRIDGE_ITERATION_01_REPORT.yaml`
- `docs/bridge/reports/MUSCAL_CODING_BRIDGE_ARCHITECTURE_PREGATE.md`
- `docs/bridge/state/current.yaml`

## Files Modified
- `features/bridge/__init__.py` (previously empty, now populated with exports)

## Tests
- **Passed:** 39/39 (100%)
- **Failed:** 0
- **Skipped:** 0

## Bridge Capability
- **Project scanning:** ✅ `ProjectScanner` detects root, branch, commit, dirty state, modified/untracked counts
- **OpenCode execution:** ✅ `OpenCodeAdapter` wraps `opencode run --format json` with timeout, session tracking, structured failure
- **Session tracking:** ✅ Extracts session ID from output; supports `-s/--session` for continue
- **Result normalization:** ✅ Evidence-based classification: facts (verified), observations (extracted), interpretations (inferred), hypotheses (proposed), unknowns
- **Event persistence:** ✅ `BridgeEventWriter` writes typed `bridge.execution` events to canonical EventStore
- **Handoff reports:** ✅ Generates Markdown + YAML reports with project context, execution results, changes, tests, risks, next action
- **Runtime state:** ✅ Derived `current.yaml` in `docs/bridge/state/` (not canonical authority)

## Verified Limitations
1. Bridge does not create its own EventStore — requires dependency injection or DB path
2. Bridge does not modify Git, EventStore, or ADR files
3. Bridge does not classify execution output as permanent knowledge (events only)
4. Bridge does not implement error recovery (deferred to Iteration 3)
5. Bridge does not implement desktop/browser automation
6. Bridge does not require an OpenCode REST API

## P0/P1 Findings
| Priority | Finding | Status |
|----------|---------|--------|
| P0 | Dirty working tree (25 modified, ~70 untracked files) | Documented; bridge snapshots git state |
| P0 | No remote configured | Documented as infra concern |
| P1 | `features/bridge/` namespace shared with `input_classifier_plugin.py` | No naming conflict |
| P1 | Multiple memory/knowledge systems (divergence risk) | Bridge events write to EventStore only |
| P2 | HDR-001-004 referenced but not found as canonical records | May be in untracked docs/audit/ |

## Next Iteration
- **Exact objective:** Iteration 3 — Bridge Error Recovery & Integration
  - Add retry logic to `OpenCodeAdapter`
  - Add execution timeout hardening
  - Add `git stash`/`git checkout` safety nets before bridge execution
  - Integrate with MUSCAL `VerificationOrchestrator` for verified execution receipts
  - Add `opencode serve` adapter mode for persistent bridge server

## Human Action Required
- None
