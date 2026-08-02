# PHASE_A_REMEDIATION_PLAN — MUSCAL Knowledge Reconciliation Audit

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Plan:** PHASE_A · **Status:** DRAFT — AWAITING APPROVAL
**Date:** 2026-08-01 · **Constraint:** NO code changes before explicit approval. This document only.
**Reference:** MASTER_INDEX.md §4 (Phase A), SESSION_CONTINUITY_AUDIT.md (M-1…M-8), DECISION_REGISTRY.md (D-006/D-017/D-022)

**Change classification legend:** `DOC` = documents only · `GOV` = governance process · `ADJ` = adjudication decision (no artifact change) · `CODE` = code modification (FORBIDDEN this phase) · `TEST` = verification runs (read-only)

---

## Item PA-01 — Commit audit wave (TF-01, part 1)

- **ID:** PA-01
- **Finding:** The entire audit/certification wave (MC-TC-002…007, E3.x) exists only as untracked files. Git-as-truth (CHANGE_JOURNAL hierarchy) hides the newest project truth; a fresh session cannot reach it.
- **Evidence:** `git status` 2026-08-01: 168 untracked entries; 55 files in `docs/audit/` incl. `MC-TC-006-REPLAY-DETERMINISTIC-RECONSTRUCTION-CERTIFICATION.md`, `MC-TC-007-FULL-REALITY-CLOSURE-CERTIFICATION.md`, `MC-TC-007_STATUS_ZUSAMMENFASSUNG.md`, `MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION.md`, `MC-TC-004_CERTIFICATION_REPORT.md`, `GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md`; last commit `cdaa1c2` (2026-07-20). [C0]
- **Risk:** If these files are lost or forgotten, 11 days of decisions and certifications vanish; MC-TC-004 CERTIFIED and MC-TC-007 CONDITIONAL GO have no historical record. HIGH.
- **Recommended action:** Stage and commit the documentation wave in 3 reviewed chunks (order matters, see below). Chunk 1: audit/certification docs. Chunk 2: governance/handover/spec docs. Chunk 3: reports at repo root. Commit messages follow existing convention (e.g. `docs(audit): commit MC-TC-002..007 certification wave`).
- **Files affected:** `docs/audit/*` (55), `docs/session_handovers/HANDOVER_S-2026-07-27-001.md`, `docs/governance/SESSION_REGISTRY.md` (new location), `docs/governance/checkpoints/`, `docs/interface/`, `docs/kernel/`, `spec/ADRs/`, `spec/certifications/`, `E3.1-PHASE2-REPORT.md`, `E3.3_EXECUTION_LEDGER.md`, `INSTRUMENTS.md`
- **Change classification:** DOC (git history change only)
- **Rollback possibility:** HIGH — `git reset --soft HEAD~1` per chunk; nothing is destroyed, files remain on disk.
- **Validation test:** `git status --short` no longer lists the committed paths; `git log --oneline -4` shows the new commits; `git fsck --no-dangling` clean.

## Item PA-02 — Commit implementation wave (TF-01, part 2)

- **ID:** PA-02
- **Finding:** A large implementation wave (features, tests, frontend, spec drafts) from 21.–31.07 is untracked and unreviewed. It contains real, potentially certified code (EventStore, replay, execution guard) plus spec drafts that are chat-only artifacts.
- **Evidence:** Untracked: `features/{agent_detection,boot,bootstrap,cognitive_unit,events,execution,execution_guard,identity,interface_gateway,kernel,knowledge,memory_fabric,monitoring,optimization,orchestration,projection,provenance,safety,streaming,supl,tool_runtime,tools,verification,worker}/`, `features/runtime/{checkpoint_manager,coordinator,models,observability,runtime_state,session_manager}.py`, `features/runtime_canonical.py`, `features/pipeline/*`, `tests/{bridge,execution_guard,knowledge,optimization,orchestration,runtime,supl}/`, 11 new `tests/test_*.py`, `frontend/{ModeToggle,SemanticGraphView,SemanticOverlay,SuplApp,SuplExecutionView}.jsx`, `frontend/useSuplWebSocket.js`, `spec/MC-006-*.md`, `spec/MSCE-SPECIFICATION_v0.1.md`, `spec/EXECUTION_INTEGRITY_CONTRACT.md`. [C0]
- **Risk:** Unreviewed code entering history without adjudication; or — worse — code kept uncommitted indefinitely (loss, confusion, undetectable drift). MEDIUM–HIGH.
- **Recommended action:** Before committing, split into (a) certified/verified modules (EventStore, replay, execution guard — cross-referenced by MC-TC-004/006 artifacts) and (b) draft/experimental modules (supl, bootstrap, boot, tool_runtime spec drafts). Commit (a) as functional chunks, commit (b) explicitly tagged as DRAFT (`docs(spec): record draft artifacts for MUSCAL 2.0 wave`). Do NOT commit code that fails `pytest`.
- **Files affected:** as listed in Evidence
- **Change classification:** GOV (requires review/disposition before commit); CODE enters history via commit, not by modification
- **Rollback possibility:** HIGH — per-chunk `git reset --soft`; content preserved.
- **Validation test:** `pytest -q` passes before each functional chunk commit (TEST, read-only); `git status --short` clean after; chunk boundary = one domain per commit.

## Item PA-03 — Commit/restore modified core files (TF-01 + TF-04, gate: PA-07)

- **ID:** PA-03
- **Finding:** 29 tracked files carry uncommitted modifications; at least 8 are core runtime files whose modification conflicts with the D-006/D-022 immutability contract unless adjudicated.
- **Evidence:** `git status` (M): `kernel.py`, `graph.py`, `event_bus.py`, `muscal_os.py`, `muscal_loop.py`, `supervisor.py`, `system_runtime.py`, `tools.py`, `mel.py`, `permission_engine.py`, `plugin_registry.py`, `schema.py`, `api_server.py`, `api/main.py`, `compose.yml`, `os_config.py`, `runtime/database.py`, `runtime/event_store.py`, `runtime/kernel/writer.py`, `runtime/main.py`, `features/bridge/__init__.py`, `features/replay/replay_service.py`, `features/runtime/__init__.py`, `frontend/Dashboard.jsx`, `spec/ADR-014-tool-runtime.md`, `spec/OVERRIDE.md`, `tests/reconciliation/test_regression_baseline.py`, `tests/test_bus_store_bridge.py`, `docs/SESSION_REGISTRY.md`. [C0]
- **Risk:** Committing without adjudication silently rewrites the "immutable" core; reverting loses 11 days of intended work. HIGH.
- **Recommended action:** BLOCKED until PA-07 completes. Afterwards: `git add` only files marked SANCTIONED, commit as `fix(audit): commit adjudicated post-gate core changes`; files marked REVERT are `git checkout`ed; ADJUST files get the documented adjustment applied (code change — requires separate approval).
- **Files affected:** 29 files above
- **Change classification:** ADJ → CODE (conditional on PA-07 outcome)
- **Rollback possibility:** HIGH — pre-state is the commit `cdaa1c2`; revert via `git checkout -- <file>` or `git revert`.
- **Validation test:** disposition table in PA-07 covers 29/29 files; after commit `git status --short` shows only intended remainder; `pytest -q` green.

## Item PA-04 — Restore project state truth (TF-03)

- **ID:** PA-04
- **Finding:** `docs/PROJECT_STATE.md` (20.07) reports "Stable Prototype / READY WITH RISKS / 547 tests" and misses everything from 21.–31.07: MC-TC-004 CERTIFIED (30.07), MC-TC-006, MC-TC-007 CONDITIONAL GO (31.07), 2 P0 blockers, E3.2 closure.
- **Evidence:** PROJECT_STATE.md mtime 2026-07-20, content §status; MC-TC-007_STATUS_ZUSAMMENFASSUNG.md (31.07, untracked) = CONDITIONAL GO; DECISION_REGISTRY D-017. [C0/C1]
- **Risk:** Any session or human reading only the canonical doc misjudges project phase; P0 work may not start. CRITICAL.
- **Recommended action:** Rewrite §status of PROJECT_STATE.md: add "MC-TC-007: CONDITIONAL GO (31.07)", P0 blocker section (PA-08/PA-09), pointer to `docs/audit/`, update date/version. Pure documentation edit.
- **Files affected:** `MUSCAL CORE/docs/PROJECT_STATE.md` (single file)
- **Change classification:** DOC
- **Rollback possibility:** HIGH — restore from commit `cdaa1c2` (`git show cdaa1c2:docs/PROJECT_STATE.md`) or `git checkout -- docs/PROJECT_STATE.md`.
- **Validation test:** `grep -c "MC-TC-007" docs/PROJECT_STATE.md` ≥ 1; `grep -c "CONDITIONAL GO"` ≥ 1; P0 section lists both P0-1 and P0-2; content consistent with MC-TC-007_STATUS_ZUSAMMENFASSUNG.md (no contradictions).

## Item PA-05 — Update SESSION_REGISTRY (TF-03)

- **ID:** PA-05
- **Finding:** `docs/SESSION_REGISTRY.md` (modified, untracked twin at `docs/governance/`) ends at session 27.07; sessions 28.–31.07 (MC-TC-004 certification, MC-TC-007, audits) are unrecorded — the registry's own continuity claim is broken.
- **Evidence:** SESSION_REGISTRY last entry S-2026-07-27-001; HANDOVER gap 28.–31.07 (SESSION_CONTINUITY_AUDIT M-5); file modified but uncommitted. [C0]
- **Risk:** Session chain cannot be reconstructed; who-did-what during the audit wave is lost. MEDIUM.
- **Recommended action:** Add registry entries for 28.–31.07 sessions (ID, date, artifacts produced, status) derived from untracked audit files and S2 chats. Decide ONE canonical location (`docs/` vs `docs/governance/`) and consolidate. Handover backfill for 28.–31.07 remains Phase B (requires reconstructing content).
- **Files affected:** `docs/SESSION_REGISTRY.md` (+ `docs/governance/SESSION_REGISTRY.md` — deduplicate)
- **Change classification:** DOC
- **Rollback possibility:** HIGH — `git checkout -- docs/SESSION_REGISTRY.md`.
- **Validation test:** last registry entry dated ≥ 2026-07-31; entries 28.–31.07 present; only one SESSION_REGISTRY.md exists after dedup.

## Item PA-06 — Fix ADR-013 mislabel (TF-04, minor)

- **ID:** PA-06
- **Finding:** `spec/ADR-013-pipeline.md` contains ADR-007 content (mislabeled file); `spec/ADRs/` duplicates ADR set ×4 locations.
- **Evidence:** REPOSITORY_CENSUS §ADR; file content check. [C0]
- **Risk:** Wrong references propagate; supersession tracking breaks. LOW.
- **Recommended action:** Rename/fix ADR-013 to match content or regenerate correct ADR-013; record canonical location `spec/ADRs/`. Full ×4 consolidation = Phase B (C-2). DOC-only fix now.
- **Files affected:** `spec/ADR-013-pipeline.md` (+ index references)
- **Change classification:** DOC
- **Rollback possibility:** HIGH.
- **Validation test:** filename/content match; references in DECISIONS.md resolve.

## Item PA-07 — Adjudicate immutability violations (TF-04, gate for PA-03)

- **ID:** PA-07
- **Finding:** 29 modified tracked files, incl. core (`kernel.py`, `graph.py`, `event_bus.py`, `muscal_os.py`, `system_runtime.py`, `supervisor.py`), violate D-006/D-022 ("no modifications to core without decision") — no decision trail found.
- **Evidence:** `git status` M-list (PA-03 evidence); D-006/D-022 in DECISIONS.md; DECISION_REGISTRY §Conflict D-017. [C0]
- **Risk:** Unadjudicated changes become "sanctioned by default" once committed; trust boundary of the immutability contract collapses. HIGH.
- **Recommended action:** Produce a disposition table (29 rows): per file — diff summary (from `git diff`), origin session/artifact (cross-ref SESSION_CONTINUITY_AUDIT M-6 + S2 chats), classification SANCTIONED (post-gate work, matches ADR-014/EventStore/replay wave) / REVERT (accidental or superseded) / ADJUST (needs correction — CODE, requires separate approval). Register outcome as DECISION_REGISTRY addition (new D-ID). No file changes during adjudication.
- **Files affected:** none (pure analysis artifact: append to DECISION_REGISTRY.md + this plan's disposition appendix)
- **Change classification:** ADJ (GOV)
- **Rollback possibility:** N/A (no artifact change); disposition table itself is trivially editable.
- **Validation test:** disposition table 29/29 rows; each row has diff-summary + disposition + evidence; PA-03 commit set == SANCTIONED set.

## Item PA-08 — P0-1: Graph-OS reconstructability (P0 blocker)

- **ID:** PA-08
- **Finding:** MC-TC-007 (31.07) lists P0 blocker: Graph-OS state (GraphState/SphereState) is in-memory only and cannot be reconstructed after restart.
- **Evidence:** MC-TC-007_STATUS_ZUSAMMENFASSUNG.md + S2 chat 31.07; GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md (untracked, 30.07). [C0/C1]
- **Risk:** Any restart loses visual/state context; certified trust core (MC-TC-004) does not cover graph state. HIGH.
- **Recommended action (Phase A = decision only):** Record P0-1 in PROJECT_STATE (PA-04); define remediation options for approval: (a) persist GraphState snapshots via EventStore replay, (b) derive from graph.py + event reconstruction, (c) scope reduction of Graph-OS. Implementation = CODE, next phase after approval. Do NOT modify code now.
- **Files affected:** none (decisions recorded in PROJECT_STATE.md + DECISION_REGISTRY.md)
- **Change classification:** ADJ (implementation deferred, CODE-flagged)
- **Rollback possibility:** N/A (no code); choice can be re-decided.
- **Validation test:** P0-1 documented in PROJECT_STATE §P0 with option selected and owner; no code diff.

## Item PA-09 — P0-2: Watchdog event persistence (P0 blocker)

- **ID:** PA-09
- **Finding:** MC-TC-007 (31.07) lists P0 blocker: watchdog events are not persisted to EventStore — runtime safety observability gap.
- **Evidence:** MC-TC-007_STATUS_ZUSAMMENFASSUNG.md + S2 chat 31.07. [C0/C1]
- **Risk:** Post-incident forensics impossible; trust-boundary guarantees (MC-TC-003F/004) do not cover watchdog path. HIGH.
- **Recommended action (Phase A = decision only):** Record P0-2 in PROJECT_STATE (PA-04); define options: (a) extend EventStore persistence to watchdog channel, (b) dedicated watchdog log with audit checksum, (c) defer with explicit risk acceptance (needs D-registry entry). Implementation = CODE, next phase. Do NOT modify code now.
- **Files affected:** none (decisions in PROJECT_STATE.md + DECISION_REGISTRY.md)
- **Change classification:** ADJ (implementation deferred, CODE-flagged)
- **Rollback possibility:** N/A (no code).
- **Validation test:** P0-2 documented in PROJECT_STATE §P0 with option + risk acceptance status; no code diff.

---

## Sequencing & Dependencies

```
PA-07 (adjudication) ──► PA-03 (commit core)      [PA-03 BLOCKED until PA-07 done]
PA-01 ──► PA-02 ──► PA-05 ──► PA-04 ──► PA-06    [independent, any order; PA-04 recommended first]
PA-08 + PA-09  (decision-only, parallel, no code)
```
**Gate:** PA-03 + PA-04 + PA-05 = Phase A completion criteria. PA-08/PA-09 remain OPEN (decision recorded, implementation pending).

## Out of scope (this plan)

- TF-02 / TF-06 (manual numbers, test counts) — planned separately per MASTER_INDEX Phase A step 4 after this plan's approval.
- Phase B items (handover backfill 28.–31.07, SESSION_RULES extension, ADR consolidation ×4, chat-decision extraction).
- Any CODE change (PA-02 commit excludes failing tests; PA-03 only commits adjudicated SANCTIONED files; PA-08/09 explicitly deferred).

---

*Read-only validation performed 2026-08-01: git status/log, docs/audit listing, pyproject (pytest≥9). No modifications made. Awaiting approval before executing PA-01…PA-09.*
