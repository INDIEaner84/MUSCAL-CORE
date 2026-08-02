# PA-03/PA-07 — IMMUTABILITY ADJUDICATION DISPOSITION (ARTIFACT ONLY — NO CHANGES)

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Date:** 2026-08-01 · **Type:** ADJUDICATION ARTIFACT
**Constraint:** This artifact only documents; it applies NO disposition (no revert, no adjust, no commit). Dispositions take effect only after explicit approval.
**Reference:** DECISION_REGISTRY.md D-006/D-017/D-022 · PHASE_A_REMEDIATION_PLAN.md PA-03/PA-07 · spec/OVERRIDE.md

---

## 0. Executive summary

- Baseline: commit `cdaa1c2` (2026-07-20). Post-baseline, **29 tracked files** carried uncommitted modifications (1.628+/1.650−).
- **6 of the 29 were swept into the approved PA-02 directory commits** during execution (see §6) — they are now in history and must be adjudicated **retroactively**.
- **22 remain modified** and are covered by this disposition table (§5).
- The governance basis that *claims* to authorize part of this wave exists: `spec/OVERRIDE.md` (Phase 1A, 2026-07-24, Architecture Gate v1.0). **However, the override's own claim ("no core-file modifications are made in this phase") is contradicted by the actual diffs** (kernel.py, event_bus.py, schema.py, os_config.py ARE modified). → CRITICAL adjudication finding.

## 1. Key governance documents in play

| Doc | Status in wave | Role |
|-----|----------------|------|
| `spec/OVERRIDE.md` | MODIFIED (1.298→189 lines, rewritten 24.07) | Phase 1A override under GRAPH_OS freeze approval; claims core untouched |
| `spec/ADR-014-tool-runtime.md` | MODIFIED (PROPOSED→DRAFT, 22.07 E3.0.2 scope) | UTR consolidation |
| `docs/engineering/D-E3.2-002-FINAL-CLOSURE.md` | committed (PA-01) | E3.2 trust boundary closure |
| `docs/audit/MC-TC-004_*` | committed (PA-01) | EventStore certification evidence |

## 2. Override-vs-reality contradiction (top finding)

| Override claim (OVERRIDE.md 24.07) | Reality (git diff vs cdaa1c2) |
|------------------------------------|-------------------------------|
| `kernel.py`: **NONE** — "ExecutionContext wraps Kernel.run() externally — no kernel code changed" | kernel.py: **252+/74−** — `run()` decomposed into `stage_rag()`, `_register_pipeline_stages()` added, execution_id threaded |
| `event_bus.py`: **NONE** | event_bus.py: 11+/1− — uuid7 event IDs + `swap_subscriber()` |
| `schema.py`: **NONE** | schema.py: +2 — `execution_id` field |
| `os_config.py`: **NONE** | os_config.py: +8 — `execution_mode` + `_STRING_KEYS` |
| `muscal_os.py`: **NONE** — "wiring documented; adapter start in bootstrap" | muscal_os.py: 44+/8− — `run()` signature extended with execution_mode/execution_context |

**Assessment:** Either (a) the override predates these changes and they were made later without updating it, or (b) the override understates reality. Either way the immutability contract (D-006/D-022) was NOT satisfied by documentation. [C1]

## 3. Additional governance findings

- **OVERRIDE-051 + all historical override entries were REPLACED**, not appended (1.298→189 lines). Historical overrides exist only in git history. Recovery/consolidation decision required.
- The pre-commit hook cannot distinguish `features/kernel/kernel.py` (new plugin) from core `kernel.py` (basename match in CORE_FILES) — false positive observed during PA-02 (documented in commit 1436ad6).
- MC-TC-005 NOT AUTHORIZED yet `spec/ADR-014` moved to DRAFT with expanded scope without an ADR decision record.

## 4. Disposition legend

| Disposition | Meaning | Action (only after approval) |
|-------------|---------|------------------------------|
| **SANCTIONED** | Change is covered by a documented wave (Phase 1A override, E3.2/UTR, MC-TC-004) AND diff is consistent with that wave | Commit as-is (PA-03), record in DECISION_REGISTRY |
| **SANCTIONED-CONDITIONAL** | Covered by a wave but contradicts the wave's own override document (see §2) | Commit + update OVERRIDE.md to match reality (ADJUST on doc) |
| **REVERT** | Not traceable to any wave or superseded | `git checkout` from cdaa1c2 |
| **ADJUST** | Needs code/diff correction (core write) | Separate approval, `--allow-core-write` per hook |

## 5. Disposition table (22 remaining modified files)

| # | File | Diff summary | Wave link | Disposition | Evidence |
|---|------|--------------|-----------|-------------|----------|
| 1 | `kernel.py` | 252+/74−; run()→stage_rag decomposition, pipeline stage registration, execution_id threading | Phase 1A execution identity (features/identity) | **SANCTIONED-CONDITIONAL** | OVERRIDE.md claims NONE (contradiction); features/identity committed 1436ad6 |
| 2 | `event_bus.py` | 11+/1−; uuid7 ids, swap_subscriber | Phase 1A canonical event identity (MC-TC-005.1/005.3) | **SANCTIONED-CONDITIONAL** | OVERRIDE.md claims NONE |
| 3 | `schema.py` | +2; execution_id field | Phase 1A | **SANCTIONED-CONDITIONAL** | OVERRIDE.md claims NONE |
| 4 | `os_config.py` | +8; execution_mode | Phase 1A reality | **SANCTIONED-CONDITIONAL** | OVERRIDE.md claims NONE |
| 5 | `muscal_os.py` | 44+/8−; run(execution_mode, execution_context) | Phase 1A | **SANCTIONED-CONDITIONAL** | OVERRIDE.md claims NONE |
| 6 | `graph.py` | 16+/7−; execution_id param on add_node | Phase 1A | **SANCTIONED-CONDITIONAL** | consistent with execution identity wave |
| 7 | `muscal_loop.py` | 66+/8−; EXECUTORS→UTR rewiring, receipts | E3.2/ADR-014 UTR (D-E3.2-002 committed) | **SANCTIONED** | E3.2 closure docs committed PA-01 |
| 8 | `tools.py` | +17; global UTR wiring | E3.2/ADR-014 UTR | **SANCTIONED** | same |
| 9 | `mel.py` | 37+/5−; _register_tools_to_utr | E3.2/ADR-014 UTR | **SANCTIONED** | same |
| 10 | `permission_engine.py` | 25+/13−; EXECUTORS→UTR | E3.2/ADR-014 UTR | **SANCTIONED** | same |
| 11 | `plugin_registry.py` | 50+/1−; PLUGIN_CAPABILITIES/CAPABILITY_MAP | Phase 1A capability routing (governance_stage) | **SANCTIONED-CONDITIONAL** | no ADR/override entry for capability map |
| 12 | `system_runtime.py` | 29+/22−; deprecated shim→UTR | E3.2 | **SANCTIONED** | E3.2 closure |
| 13 | `supervisor.py` | 45+/1−; Phase 1b SUPL + FastAPI | Phase 1b/SUPL (spec/MC-006 committed DRAFT) | **SANCTIONED-CONDITIONAL** | MC-006 is DRAFT spec (chunk D) — implementation precedes spec approval |
| 14 | `api_server.py` | 150+/190−; create_app refactor, EventStore wiring | MC-TC-004 + Phase 1b | **SANCTIONED-CONDITIONAL** | refactor not explicitly in override |
| 15 | `api/main.py` | 3+/1−; create_app import | MC-TC-004 | **SANCTIONED** | matches api_server refactor |
| 16 | `compose.yml` | +1; SUPL_API_PORT | Phase 1b | **SANCTIONED-CONDITIONAL** | infra, minor |
| 17 | `runtime/event_store.py` | 367±; 6 new columns + replay integration | **MC-TC-004 CERTIFIED (30.07)** | **SANCTIONED** | override §Files Modified lists it; certification committed |
| 18 | `runtime/database.py` | +283; decisions/sequences tables, event tables | MC-TC-004 | **SANCTIONED** | certification evidence |
| 19 | `runtime/kernel/writer.py` | 49+/1−; severity→priority, uuid | MC-TC-004/006 | **SANCTIONED** | replay certification |
| 20 | `runtime/main.py` | 3+/1−; EventStore wiring | MC-TC-004 | **SANCTIONED** | same |
| 21 | `spec/OVERRIDE.md` | rewritten 1298→189; Phase 1A override | Governance doc | **ADJUST** — extend with §2 contradiction resolution + historical overrides note; then SANCTIONED | historical override entries replaced (data loss) |
| 22 | `spec/ADR-014-tool-runtime.md` | PROPOSED→DRAFT + E3.0.2 scope | E3.0.2/ADR-014 | **ADJUST** — needs ADR decision record (status DRAFT without decision) | D-E3.0.2-006 committed |

**Disposition tally:** SANCTIONED 8 · SANCTIONED-CONDITIONAL 12 · ADJUST 2 · REVERT 0

## 6. Swept files (6 of 29) — committed during PA-02, retroactive adjudication

| File | Swept into | Commit | Suggested disposition |
|------|-----------|--------|----------------------|
| `features/bridge/__init__.py` (+23) | PA-02 chunk A (git add features/) | 1436ad6 | SANCTIONED (bridge wave) |
| `features/replay/replay_service.py` (+6) | PA-02 chunk A | 1436ad6 | SANCTIONED (MC-TC-006) |
| `features/runtime/__init__.py` (+19) | PA-02 chunk A | 1436ad6 | SANCTIONED (runtime wave) |
| `frontend/Dashboard.jsx` (+3) | PA-02 chunk C | 8025f2f | SANCTIONED (SUPL UI wave) |
| `tests/reconciliation/test_regression_baseline.py` (8±) | PA-02 chunk B | ae2792d | SANCTIONED-CONDITIONAL (4 full-suite failures; see FL-01) |
| `tests/test_bus_store_bridge.py` (2±) | PA-02 chunk B | ae2792d | SANCTIONED (uuid id assertion matches event_bus change) |

**Deviation note:** These were swept via directory `git add` (features/, tests/, frontend/) instead of per-file staging; documented for transparency — no content was altered.

## 7. P0 blockers (PA-08/PA-09 — decision-only, NOT executed)

Per user directive, P0-1 (Graph-OS reconstructability) and P0-2 (watchdog persistence) are recorded in PROJECT_STATE.md (committed d5f5ce7) as OPEN with decision pending. No options were selected, no code touched. [C1]

---

*Artifact created read-only on 2026-08-01. Dispositions are RECOMMENDATIONS requiring approval; application (PA-03) is BLOCKED until then.*
