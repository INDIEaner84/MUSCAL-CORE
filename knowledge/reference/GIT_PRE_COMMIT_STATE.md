# GIT_PRE_COMMIT_STATE — Phase A baseline (captured before any git operation)

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Capture date:** 2026-08-01 · **Captured:** before PA-01/PA-02 commits
**Baseline commit:** `cdaa1c29e18417af78ad180a2f652cbfa7c0dff4` (2026-07-20 20:59:32 +0200, "docs: update project state after P0/P1 gap closure")
**Tracked files in repo at baseline:** 576

---

## 1. git status — summary

| Bucket | Count | Note |
|--------|------:|------|
| Modified (tracked) | 29 | 1.628 insertions / 1.650 deletions |
| Untracked | 168 | 60 docs, 48 tests, 45 features, 6 spec, 6 frontend, 3 root reports |
| **Total dirty** | **197** | = audit wave + implementation wave + core modifications |

## 2. Changed files — MODIFIED (29, classification CAT-C → PA-03/PA-07, adjudication only)

`api/main.py` (+4) · `api_server.py` (340±) · `compose.yml` (+1) · `docs/SESSION_REGISTRY.md` (+1) · `event_bus.py` (12±) · `features/bridge/__init__.py` (+23) · `features/replay/replay_service.py` (+6) · `features/runtime/__init__.py` (+19) · `frontend/Dashboard.jsx` (+3) · `graph.py` (23±) · `kernel.py` (326±) · `mel.py` (42±) · `muscal_loop.py` (74±) · `muscal_os.py` (52±) · `os_config.py` (+8) · `permission_engine.py` (38±) · `plugin_registry.py` (51±) · `runtime/database.py` (+283) · `runtime/event_store.py` (367±) · `runtime/kernel/writer.py` (50±) · `runtime/main.py` · `schema.py` · `spec/ADR-014-tool-runtime.md` · `spec/OVERRIDE.md` · `supervisor.py` (51±) · `system_runtime.py` · `tests/reconciliation/test_regression_baseline.py` (8±) · `tests/test_bus_store_bridge.py` (2±) · `tools.py` (+17)

## 3. Changed files — UNTRACKED (168, classified below)

### CAT-A: Audit/certification wave → PA-01 (docs, 71 files)
- `docs/audit/` **55 files** (MC-TC-002…007, MC-TC-007_STATUS_ZUSAMMENFASSUNG, GRAPH_OS_ARCHITECTURE_FREEZE_v1.0, E3.5.1)
- `docs/session_handovers/HANDOVER_S-2026-07-27-001.md`
- `docs/governance/` (SESSION_REGISTRY.md, ADR-014-IMPLEMENTATION_PLAN_v1.0/1.1, MUSCAL_PHASE1A_*, MUSCAL_RUNTIME_FOUNDATION, HANDOVER_TEMPLATE, checkpoints/)
- `docs/bridge/`, `docs/engineering/`, `docs/interface/`, `docs/kernel/`
- `spec/ADRs/` (new), `spec/certifications/` (new)
- Root reports: `E3.1-PHASE2-REPORT.md`, `E3.3_EXECUTION_LEDGER.md`, `INSTRUMENTS.md`

### CAT-B: Implementation wave → PA-02 (code+tests, 107 files)
- `features/` **45 entries**: agent_detection, boot, bootstrap, cognitive_unit, events, execution, execution_guard, identity, interface_gateway, kernel, knowledge, memory_fabric, monitoring, optimization, orchestration, projection, provenance, safety, streaming, supl, tool_runtime, tools, verification, worker, runtime_canonical.py, runtime/{checkpoint_manager,coordinator,models,observability,runtime_state,session_manager}.py, pipeline/{__init__,cu_stage,governance_stage,routing_stage}.py, bridge/{bridge_event_writer,handoff_report,opencode_adapter,orchestrator,project_scanner,recovery,result_normalizer,server_manager,session_continuity,task_contract}.py
- `tests/` **48 entries**: bridge/, execution_guard/, knowledge/, optimization/, orchestration/, runtime/, supl/, tools/, + 32 new test files (test_phase1a…test_trust_boundary_e3_2, test_execution_integrity_*, test_provenance_e3_*, test_mc_tc_005_3_*, …)
- `frontend/` **6 files**: ModeToggle, SemanticGraphView, SemanticOverlay, SuplApp, SuplExecutionView, useSuplWebSocket

### CAT-D: Spec drafts (chat-derived, not certified) → PA-02, DRAFT-tagged commit (3 files)
- `spec/MC-006-HANDOVER.md`, `spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md`, `spec/MSCE-SPECIFICATION_v0.1.md`, `spec/EXECUTION_INTEGRITY_CONTRACT.md`

## 4. Diff statistics (modified files vs HEAD)

| Metric | Value |
|--------|------:|
| Files changed | 29 |
| Insertions | 1.628 |
| Deletions | 1.650 |
| Net | −22 |
| Heaviest | kernel.py (326±), runtime/event_store.py (367±), api_server.py (340±), runtime/database.py (+283) |
| Docs/spec among modified | docs/SESSION_REGISTRY.md (+1), spec/ADR-014-tool-runtime.md, spec/OVERRIDE.md |

## 5. Classification of changed artifacts

| Class | Contents | Owner item | Phase status |
|-------|----------|------------|--------------|
| CAT-A | Audit/certification + governance + handover + spec/ADRs + reports | PA-01 | APPROVED — commit |
| CAT-B | features/ + tests/ + frontend/ (implementation wave) | PA-02 | APPROVED — commit after pytest gate |
| CAT-D | spec drafts (MC-006, MSCE, EXECUTION_INTEGRITY_CONTRACT) | PA-02 | APPROVED — commit, DRAFT-tagged |
| CAT-C | 29 modified tracked files (core + runtime + tests + spec) | PA-03/PA-07 | **NOT approved** — adjudication artifact only |
| — | PA-08/PA-09 (P0 decision) | — | NOT executed |

## 6. Integrity note

State captured via `git status --short` / `git diff --stat` / `git diff --numstat` on 2026-08-01 before any staging or commit. Untracked content was not modified during capture (read-only). No index changes (`git add` performed only during PA-01/PA-02 execution).

---

*Provenance: git state at capture time; full untracked listing reproducible via `git status --short` (197 entries).*
