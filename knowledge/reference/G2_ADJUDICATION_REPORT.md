# G2_ADJUDICATION_REPORT — Decision Package for Approval

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Gate:** G2 · **Date:** 2026-08-01
**Status:** DECISION PACKAGE — no changes applied, no commits, no refactoring
**Scope:** 1. PA-03/PA-07 (29-file immutability review) · 2. FL-01 (23 pytest failures) · 3. OVERRIDE.md governance conflict
**Baseline:** `cdaa1c2` (2026-07-20) · **Post-wave head:** `d5f5ce7` (2026-08-01)

---

## 1. PA-03 / PA-07 — 29-file immutability review

### Cluster map

| Cluster | Files (remaining modified) | Swept (committed) |
|---------|---------------------------|-------------------|
| **C1 — MC-TC-004/006 certified** | runtime/event_store.py, runtime/database.py, runtime/kernel/writer.py, runtime/main.py | features/replay/replay_service.py |
| **C2 — Phase 1A execution identity** | kernel.py, event_bus.py, schema.py, os_config.py, muscal_os.py, graph.py, plugin_registry.py | — |
| **C3 — E3.2 / UTR rewiring** | muscal_loop.py, tools.py, mel.py, permission_engine.py, system_runtime.py | features/bridge/__init__.py, features/runtime/__init__.py |
| **C4 — Phase 1b / SUPL** | supervisor.py, api_server.py, api/main.py, compose.yml | frontend/Dashboard.jsx |
| **C5 — Governance docs** | spec/OVERRIDE.md, spec/ADR-014-tool-runtime.md | — |
| **C6 — Test files** | — | tests/reconciliation/test_regression_baseline.py, tests/test_bus_store_bridge.py |

---

### G2-01 — C1: EventStore/Replay certified cluster (4 files + 1 swept)

- **ID:** G2-01
- **Evidence:** runtime/event_store.py +367 (6 new columns per OVERRIDE.md §Files Modified), runtime/database.py +283 (decision/event tables), runtime/kernel/writer.py 49+/1− (severity→priority, uuid), runtime/main.py (EventStore wiring). **MC-TC-004 CERTIFIED 30.07** (`docs/audit/MC-TC-004_CERTIFICATION_REPORT.md` + ARB_DECISION, committed `392734e`); MC-TC-006 replay certification (27.07). [C0]
- **Current classification:** SANCTIONED (certified wave)
- **Options:**
  - **A) Keep as-is** — certified, certification evidence committed
  - B) Keep with governance update — no additional update needed
  - C) Revert — destroys certified functionality + contradicts MC-TC-004
  - D) Requires ADR — certification already serves as decision record
- **Risk:** A/B: low. C: high (reverting certified EventStore). D: process overhead only.
- **Impact:** A/B: EventStore trust boundary remains intact (MC-TC-004). C: reopens certified trust core, contradicts ARB decision.
- **Recommended decision:** **A (Keep as-is)** — commit the 4 files; certification (MC-TC-004/006) is the governing decision record. [C1]

### G2-02 — C2: Phase 1A execution identity cluster (7 files)

- **ID:** G2-02
- **Evidence:** kernel.py 252+/74− (run()→stage_rag decomposition, `_register_pipeline_stages`, execution_id threading), event_bus.py 11+/1− (uuid7 ids, swap_subscriber), schema.py +2 (execution_id), os_config.py +8 (execution_mode), muscal_os.py 44+/8− (run signature), graph.py 16+/7− (execution_id param), plugin_registry.py 50+/1− (PLUGIN_CAPABILITIES/CAPABILITY_MAP). Override (24.07) claims **NONE** for kernel.py/event_bus.py/schema.py/os_config.py/muscal_os.py — contradicted by actual diffs. Features wave (identity, execution_context, uuid7) committed `1436ad6`; MC-TC-005.1/005.3 single-event-authority docs committed. [C0]
- **Current classification:** SANCTIONED-CONDITIONAL (covered by Phase 1A wave, but override document contradicts reality)
- **Options:**
  - A) Keep as-is — leaves contradiction standing (override claims NONE while code is modified)
  - **B) Keep with governance update** — commit files + update OVERRIDE.md to match reality (mechanism column: kernel/event_bus/schema/os_config/muscal_os DID change; describe actual mechanism)
  - C) Revert — loses execution identity + event authority work (MC-TC-005.1/005.3 rely on uuid7/execution_id)
  - D) Requires ADR — new ADR for "Phase 1A execution identity" would formalize; heavier than B
- **Risk:** A: governance lie persists (override falsity propagates; immutability enforcement loses credibility). C: breaks single-event-authority (MC-TC-005.3 test committed). D: delay.
- **Impact:** B: restores consistency between governance doc and code; D-006/D-022 satisfied retroactively via amended override + decision entry.
- **Recommended decision:** **B (Keep with governance update)** — commit the 7 files together with an OVERRIDE.md correction section documenting the actual Phase 1A core changes (see G2-06). [C1]

### G2-03 — C3: E3.2/UTR rewiring cluster (5 files + 2 swept)

- **ID:** G2-03
- **Evidence:** muscal_loop.py 66+/8− (EXECUTORS→UTR, receipts), tools.py +17 (`_get_global_utr`), mel.py 37+/5− (`_register_tools_to_utr`), permission_engine.py 25+/13− (EXECUTORS→UTR), system_runtime.py 29+/22− (deprecated shim). E3.2 closure docs committed (`D-E3.2-001/-002`, D-E3.0.2-006) `1c4a1e7`; chat 23.07 (E3.2 Trust Boundary Abschluss). **But** ADR-014 (Unified Tool Runtime) is **DRAFT** — implementation preceded ADR decision. [C0]
- **Current classification:** SANCTIONED (E3.2 wave) with open ADR-014 status
- **Options:**
  - A) Keep as-is — code + E3.2 docs; ADR-014 remains DRAFT
  - **B) Keep with governance update** — commit files; finalize ADR-014 (DRAFT→APPLIED/ACCEPTED) with decision entry
  - C) Revert — reverts UTR safety-gate enforcement (E3.2 trust boundary closure undone)
  - D) Requires ADR — ADR-014 finalization IS the D path
- **Risk:** A: governance gap (ADR DRAFT while applied in code) persists; C: high — reopens E3.2 trust boundary.
- **Impact:** B/D: ADR-014 becomes the decision record; immutability trail complete.
- **Recommended decision:** **B (Keep with governance update)** — commit the 5 files; the ADR-014 finalization (status + decision entry) is the governance update; if human prefers a formal ADR decision first, escalate to D. [C1]

### G2-04 — C4: Phase 1b/SUPL cluster (4 files + 1 swept)

- **ID:** G2-04
- **Evidence:** supervisor.py 45+/1− (Phase 1b SUPL + FastAPI control plane), api_server.py 150+/190− (create_app refactor, EventStore import), api/main.py 3+/1− (create_app), compose.yml +1 (SUPL_API_PORT), Dashboard.jsx +3 (SuplApp mount). Spec basis: `spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md` committed **DRAFT** (`8e97c8c`); gate1 production wiring certification committed (spec/certifications/). [C0]
- **Current classification:** SANCTIONED-CONDITIONAL (implementation precedes MC-006 spec ratification)
- **Options:**
  - A) Keep as-is — spec remains DRAFT while production wiring exists
  - **B) Keep with governance update** — commit files; record decision "Phase 1b implementation sanctioned pending MC-006 ratification" in DECISION_REGISTRY
  - C) Revert — disables SUPL runtime + FastAPI plane (breaks compose/API tests)
  - D) Requires ADR — ratify MC-006 (or create ADR) first
- **Risk:** A: MC-006 DRAFT cited as authoritative while unratified; C: breaks gate1 production wiring tests.
- **Impact:** B/D: closes the spec-vs-implementation gap; gate1 certification becomes consistent.
- **Recommended decision:** **B (Keep with governance update)** — commit the 4 files; DECISION_REGISTRY entry for Phase 1b sanction; MC-006 ratification listed as Phase B follow-up (D-type item). [C1]

### G2-05 — C5: Governance docs (2 files) — see also §3

- **ID:** G2-05
- **Evidence:** spec/OVERRIDE.md rewritten 1.298→189 lines (working tree, post-baseline); spec/ADR-014-tool-runtime.md PROPOSED→DRAFT + E3.0.2 scope. OVERRIDE-052 governance mechanism reads `spec/OVERRIDE.md` — now **deactivated** (0 mentions vs 3 at baseline). Full detail in §3. [C0]
- **Current classification:** ADJUST (both files need doc-level correction before commit)
- **Options:**
  - A) Keep as-is — breaks OVERRIDE-052 mechanism + loses history
  - **B) Keep with governance update** — restore OVERRIDE-052 block + historical entries (recoverable from `cdaa1c2:spec/OVERRIDE.md`) + add Phase 1A section truthfully
  - C) Revert — restore 1.298-line baseline, then re-apply Phase 1A as additive section (equivalent outcome to B, more steps)
  - D) Requires ADR — overkill; this is doc hygiene, not a new decision
- **Risk:** A: OVERRIDE-052 silently disabled (infra commits now blocked without override); governance history lost.
- **Impact:** B/C: mechanism restored; Phase 1A changes truthfully documented; ADR-014 status fixed via G2-03.
- **Recommended decision:** **B (Keep with governance update)** — single doc-level edit merging baseline content + Phase 1A section + OVERRIDE-052 restoration; commit together with G2-02/G2-03 clusters. [C1]

### G2-06 — Swept files (6) — retroactive adjudication

- **ID:** G2-06
- **Evidence:** Committed via directory `git add` during PA-02: `1436ad6` (features/bridge/__init__.py +23, features/replay/replay_service.py +6, features/runtime/__init__.py +19), `8025f2f` (frontend/Dashboard.jsx +3), `ae2792d` (tests/reconciliation/test_regression_baseline.py 8±, tests/test_bus_store_bridge.py 2±). No content altered; deviation documented in execution result. [C0]
- **Current classification:** SANCTIONED-CONDITIONAL (retroactive; test files see FL-01)
- **Options:**
  - A) Keep as-is — content is correct for their waves; only the staging path deviated
  - **B) Keep with governance update** — record retroactive sanction in DECISION_REGISTRY (one entry covering the sweep)
  - C) Revert — pointless: would delete valid wave code from history (rewrite history) — not recommended
  - D) Requires ADR — no new decision; governance bookkeeping only
- **Risk:** A: sweep stays undocumented → future audits misread it as bypass. B: closed. C: history rewrite risk.
- **Impact:** B: immutability trail complete (29/29 accounted).
- **Recommended decision:** **B (Keep with governance update)** — DECISION_REGISTRY entry "PA-02 sweep retroactively sanctioned; test file baselines handled under FL-01b". [C1]

---

## 2. FL-01 — 23 pytest failures (verified twice, reproducible)

### FL-01a — 19 order-dependent failures (flakiness)

- **ID:** FL-01a
- **Evidence:** Reproduced 2× in full suite (23 failed / 2.343 passed / 1 skipped, 2.367 collected). All 19 pass in isolation and in subsets (verified: 177/177, 176+1). Affected: tests/test_worker.py (6), tests/test_tool_runtime_phase3.py (6), tests/test_specialized_cu_phase5.py (3), tests/test_runtime_convergence.py (2), tests/test_pipeline_phase4.py (1), tests/test_phase6_production_readiness.py (1). Mechanism: **global singleton state** — `tools.py:_UTR`, `set_global_utr()`, `features/tool_runtime/tool_runtime.py:set_global_event_store/set_global_default_timeout` mutated across tests without reset. [C1]
- **Current classification:** OPEN — flakiness defect (test-isolation gap), not production defect
- **Options:**
  - A) Keep as-is — full-suite runs stay flaky (CI risk)
  - **B) Keep with governance update** — add test-scoped reset fixtures (autouse fixture clearing `_UTR`/global event store per test; **test-only code change**) + document ordering policy
  - C) Revert — delete/checkout the 19 tests: loses wave coverage (worker/UTR/CU/specialized-CU) without fixing root cause
  - D) Requires ADR — global-state policy ADR (singleton ownership) as follow-up; does not fix flakiness by itself
- **Risk:** A: CI intermittency, false reds, eroded trust in 2.367-test suite. C: coverage loss on certified-adjacent modules.
- **Impact:** B: deterministic full-suite; D follow-up gives long-term singleton governance. Note: production code needs **no** change for B.
- **Recommended decision:** **B (Keep with governance update)** — test-only autouse reset fixtures; plus **D** as recorded follow-up (global-state ownership ADR in Phase B). [C1]

### FL-01b — 4 deterministic baseline-drift failures

- **ID:** FL-01b
- **Evidence:** tests/reconciliation/test_regression_baseline.py `EXPECTED_TOTAL = 94` (line 17) vs actual **471** — "Expected 94 findings, got 471". Fails deterministically in isolation (verified). Cause: wave commits (`392734e`, `1c4a1e7`, `1436ad6`, `ae2792d`) added ~575 files → reconciliation scanners (broken-link, ADR-validator, import-validator, drift) count more findings. Test file was modified in wave (swept `ae2792d`) but EXPECTED_TOTAL not recalibrated. [C0]
- **Current classification:** OPEN — deterministic test defect (stale baseline constant)
- **Options:**
  - A) Keep as-is — full suite permanently red (CI blocked)
  - **B) Keep with governance update** — recalibrate EXPECTED_TOTAL (+ per-scanner counts) to current reality **after** G2 commits; **test-only change**; commit as "baseline recalibration"
  - C) Revert — restoring 94 would be wrong; baseline test must reflect repo truth, revert makes it fail forever
  - D) Requires ADR — no decision needed; numeric recalibration only
- **Risk:** A: suite blocked (2.343-green state unreachable). C: meaningless failure.
- **Impact:** B: baseline scanner becomes honest again; finding-count regression detection restored.
- **Recommended decision:** **B (Keep with governance update)** — recalibrate EXPECTED_TOTAL + scanner expectations post-G2-commit; order with FL-01a fixtures so a single clean full-suite run validates both. [C1]

---

## 3. OVERRIDE.md governance conflict

- **ID:** G2-07
- **Evidence:** Working-tree rewrite of `spec/OVERRIDE.md` (1.298→189 lines) replaced the complete historical override registry. Baseline `cdaa1c2:spec/OVERRIDE.md` = 1.298 lines (verified). Consequences (all [C0]):
  1. **OVERRIDE-052 mechanism deactivated**: `override_052_is_active()` (guards/governance_validator.py:123) reads `spec/OVERRIDE.md`; current file contains **0** "OVERRIDE-052" mentions vs **3** at baseline → ALLOW_INFRA path for guards/.github/ infra commits silently disabled.
  2. **Historical overrides (incl. OVERRIDE-051 lineage) unrecoverable from working tree** — exist only in git history (`cdaa1c2`, `ad4aff8`, `cf82987`, `fe9650c`, `eb3f851`).
  3. **False immutability claims**: Phase 1A section states "No core-file modifications are made" while kernel.py/event_bus.py/schema.py/os_config.py/muscal_os.py carry real modifications (G2-02) → the override document itself is inaccurate.
  4. Pre-commit hook override path (`--allow-core-write` note "Document the override in spec/OVERRIDE.md") now has nowhere correct to append.
- **Current classification:** CRITICAL governance defect (documentation + mechanism break)
- **Options:**
  - A) Keep as-is — OVERRIDE-052 dead, governance history lost, override channel broken
  - **B) Keep with governance update** — rebuild OVERRIDE.md from `cdaa1c2` (1.298 lines) + append truth-corrected Phase 1A section (actual core changes, mechanisms) + re-include OVERRIDE-052; **doc-only change**
  - C) Revert — `git checkout cdaa1c2 -- spec/OVERRIDE.md` restores registry but Phase 1A governance would then be entirely undocumented (works only with B-equivalent follow-up)
  - D) Requires ADR — create ADR "Core Modification Override Protocol v2" formalizing when core changes are legal; complementary, not a substitute for B
- **Risk:** A: governance enforcement silently weakened; future infra commits blocked; audit trail broken. C-alone: Phase 1A changes (24.–31.07) lack documented authorization.
- **Impact:** B: mechanism restored, history preserved, Phase 1A truthfully documented, G2-02/C5 consistency. D (follow-up): strengthens immutability protocol for future waves.
- **Recommended decision:** **B (Keep with governance update)** — rebuild from baseline + truthful Phase 1A section + OVERRIDE-052 restoration; commit together with G2-02/G2-03 (one "governance reconciliation" commit). Optional **D** recorded as Phase B item. [C1]

---

## 4. Decision package summary (for approval)

| ID | Item | Recommended | Action after approval | Files |
|----|------|-------------|----------------------|-------|
| G2-01 | C1 EventStore/Replay | **A** Keep as-is | commit 4 files | runtime/event_store.py, runtime/database.py, runtime/kernel/writer.py, runtime/main.py |
| G2-02 | C2 Phase 1A identity | **B** Keep + governance update | commit 7 files + OVERRIDE.md correction | kernel.py, event_bus.py, schema.py, os_config.py, muscal_os.py, graph.py, plugin_registry.py |
| G2-03 | C3 E3.2/UTR | **B** Keep + governance update | commit 5 files + ADR-014 finalization | muscal_loop.py, tools.py, mel.py, permission_engine.py, system_runtime.py |
| G2-04 | C4 Phase 1b/SUPL | **B** Keep + governance update | commit 4 files + DECISION_REGISTRY entry | supervisor.py, api_server.py, api/main.py, compose.yml |
| G2-05 | C5 Governance docs | **B** Keep + governance update | merge into G2-07 rebuild | spec/OVERRIDE.md, spec/ADR-014-tool-runtime.md |
| G2-06 | Swept files | **B** Keep + governance update | DECISION_REGISTRY retroactive entry | (6 committed files, no action) |
| G2-07 | OVERRIDE.md conflict | **B** Keep + governance update | rebuild from cdaa1c2 + Phase 1A section + OVERRIDE-052 | spec/OVERRIDE.md |
| FL-01a | 19 flaky tests | **B** + D follow-up | test-only autouse reset fixtures | tests/test_worker.py, tests/test_tool_runtime_phase3.py, tests/test_specialized_cu_phase5.py, tests/test_runtime_convergence.py, tests/test_pipeline_phase4.py, tests/test_phase6_production_readiness.py |
| FL-01b | 4 baseline-drift tests | **B** | recalibrate EXPECTED_TOTAL to 471+ | tests/reconciliation/test_regression_baseline.py |

**Net effect if approved:** all 22 remaining files committed (git clean), OVERRIDE-052 restored, Phase 1A truthfully documented, suite deterministic, baseline honest. **No production code is created or refactored — only test fixtures + doc corrections + commits.**

**Out of scope:** PA-08/PA-09 (P0 options) remain OPEN; TF-02/TF-06 (manual numbers) remain planned separately.

---

*Decision package created read-only on 2026-08-01. No changes, commits, or refactoring performed. Awaiting approval.*
