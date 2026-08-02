# MASTER_INDEX — MUSCAL Knowledge Reconciliation Audit

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Date:** 2026-08-01 · **Status:** COMPLETE (read-only)
**Scope:** All knowledge sources S1 (ChatGPT export 1.107 conversations) · S2 (44 new chats 17.–31.07.2026) · S3 (MUSCAL CORE repo) · S4 (governance) · S5 (session docs) · S6 (external) · S7 (chat history of this audit).
**Constraint:** Read-only — no modifications, no migration, no implementation. All claims carry provenance + confidence (C0–C4/HYP).

---

## 1. Document Index

| # | Document | Type | Status | Purpose |
|---|----------|------|--------|---------|
| 1 | AUDIT_SCOPE.md | Foundation | ✅ | Scope, source table S1–S7, method, confidence model |
| 2 | REPOSITORY_CENSUS.md | Structural | ✅ | S3 census: 1.209 files, 611 py = 77.376 LOC, 422 md, ADR ×4 duplication, git state |
| 3 | SOURCE_OF_TRUTH_MAP.md | Structural | ✅ | Authority matrix for 7 domains, stale-doc list, SO-1…SO-5 recommendations |
| 4 | TECHNICAL_MANUAL_CONFLICT_REPORT.md | Conflict | ✅ | 3-way diff M-ROOT/M-0.6/M-0.7; TC-C1/C2/H1 + module line-count errors |
| 5 | CHAT_CODE_DOC_RECONCILIATION.md | Reconciliation | ✅ | 43 new chats, 20 verified claims, 8 false claims, MC-TC-004/007 status |
| 6 | DECISION_REGISTRY.md | Registry | ✅ | D-001…D-035, supersessions, conflicts, missing decisions |
| 7 | CONCEPT_EVOLUTION_MAP.md | Temporal | ✅ | Concept register (MUSCAL, ALITA, EventStore, Cognitive Kernel …), stability tiers |
| 8 | REFERENCE_GRAPH.md | Structural | ✅ | Node/edge model (~120 nodes, 12 edge types) for future Knowledge Graph |
| 9 | SESSION_CONTINUITY_AUDIT.md | Continuity | ✅ | Fresh-session reconstruction test; SCORE 41/100; gap list M-1…M-8 |

## 2. Metrics

### M1 — Repository Health: **55/100** [C0]
Formula: 100 − (uncommitted-work penalty + duplication penalty + truth-consistency penalty), weighted.
Evidence: 197 uncommitted changes (29 modified core files, 168 untracked) since last commit 2026-07-20 [C0]; ADR artifacts duplicated ×4 locations (`spec/`, `spec/ADRs/`, `specs/`, `archive/history/adrs/`) [C0]; ADR-013 file mislabeled (contains ADR-007 content) [C0]; muscal-mvp duplicate dir [C0].

### M2 — Governance Consistency: **45/100** [C1]
Evidence: Decision process exists (HDR-001..004, MC-TC-001..007, E3.x) but MC-TC-005 NOT AUTHORIZED, MC-TC-004 certified only in untracked audit file [C0]; no ADR for EventStore/v0.8 or MKSD [C0]; PROJECT_STATE "READY WITH RISKS" (20.07) contradicts D-017 CONDITIONAL GO (31.07) [C1]; 29 modified core files violate D-006/D-022 immutability contract [C0].

### M3 — Session Continuity: **41/100** [C1]
Formula/evidence: see SESSION_CONTINUITY_AUDIT.md §2 (target-averaged reconstruction scores) — stale prio-1..6 docs (PROJECT_STATE 20.07, ROADMAP 08.07), handover gap 28.–31.07, audit truth unreachable via SESSION_RULES reading order.

### M4 — Documentation Redundancy: **35/100** [C0]
Evidence: 3 parallel Technical Manuals (v0.5 root, v0.6 history, v0.7) with conflicting numbers [C0]; ADR ×4 [C0]; test-count claims differ across 5 sources (0/547/812/431/384 vs actual 2.869) [C0]. High redundancy + low consistency = low score.

### M5 — Knowledge Coverage: **50/100** [C1]
Formula: share of chat-derived knowledge (S1+S2) that is mirrored in repo docs (S3–S5). Evidence: 100% of 28.–31.07 decisions (MC-TC-007 status, E3.2 closure, MUSCAL 2.0, agent/compiler specs, Cognitive Kernel) exist only in chat [C0]; pre-20.07 knowledge largely mirrored [C0].

**Overall Reconciliation Score (M1–M5 avg): 45.2/100 → REQUIRES ACTION** [C1]

## 3. TOP FINDINGS

| ID | Finding | Evidence source | Impact | Recommended next action |
|----|---------|-----------------|--------|-------------------------|
| TF-01 | **Git truth gap**: 197 uncommitted changes since 20.07; entire audit wave + MC-TC-004/007 untracked | git status/log; census | Session reconstruction hides newest truth; CHANGE_JOURNAL hierarchy broken | Commit wave in reviewed chunks; re-establish Git-as-truth (B-1) |
| TF-02 | **Manual numbers wrong**: v0.7 claims 184 py / 10.744 LOC; reality 611 py / 77.376 LOC; kernel.py 417 vs 708 lines | M-0.7 §4 vs repo | External claims/status messages cite false numbers | Single canonical manual; verify numbers (C-1) |
| TF-03 | **Newest status is chat-only**: MC-TC-007 CONDITIONAL GO (31.07) with 2 P0 blockers (Graph-OS not reconstructable, watchdog events not persisted); MC-TC-004 CERTIFIED (30.07) | S2 31.07 chat; audit dir | Fresh sessions see 20.07 "READY WITH RISKS" and misjudge phase; P0s invisible | Add MC-TC-007 status to PROJECT_STATE; close P0s (B-2) |
| TF-04 | **Immutability violated**: 29 core files modified without decision trail | git status; D-006/D-022 | D-017 gate violated; changes unreviewed | Adjudicate modifications vs DECISIONS (B-3) |
| TF-05 | **ADR fragmentation**: ADRs in 4 locations + ADR-013 mislabeled | census §ADR; file content | Wrong references, supersession confusion | Consolidate to `spec/ADRs/` canonical (C-2) |
| TF-06 | **Test-count contradictions**: 5 sources disagree (0/547/812/431/384); real 2.869 functions / 204 files | manuals + PROJECT_STATE vs repo | False confidence in "547/547 passing" | Re-run suite, publish verified count (C-3) |
| TF-07 | **Roadmap/decision lag**: ROADMAP 08.07, DECISIONS/CHANGE_JOURNAL 12–13.07; 28.–31.07 work undocumented | mtimes | Roadmap/priorities stale for future planning | Backfill decisions + roadmap sync (C-4) |

## 4. Final Recommendation

**Phase A — Governance Cleanup (immediate, days):**
1. Commit audit wave + new docs (TF-01).
2. Update PROJECT_STATE.md + SESSION_REGISTRY.md with MC-TC-004/007 status and P0 list (TF-03).
3. Adjudicate 29 modified core files (TF-04); fix ADR-013 mislabel.
4. Re-run test suite; publish verified numbers; correct or retire the 3 conflicting manuals (TF-02, TF-06).

**Phase B — Knowledge Consolidation (next):**
5. Backfill handovers 28.–31.07; extend SESSION_RULES reading order to include `docs/audit/` + handovers (SO-2..SO-4).
6. Extract 28.–31.07 chat decisions into ADRs/DECISIONS.md (EventStore/v0.8, MUSCAL 2.0, Cognitive Kernel, agent/compiler specs); flag chat-only specs as PENDING (TF-07).
7. Consolidate ADR duplication to canonical `spec/ADRs/` (TF-05).
8. Regenerate REFERENCE_GRAPH edges + CONCEPT_EVOLUTION_MAP entries for the backfilled knowledge.

**Phase C — Reconciliation Completion (gate):** Re-run metrics; target >75 on all 5; only then start the 20-document Knowledge Foundation plan (using this audit as its source basis).

**Stopping rule:** This audit is read-only. Any modification, migration, commit, or knowledge-foundation execution requires explicit user approval.

---

*All findings traceable to: S1 export JSON (1.107 conversations), S2 44 new chats, S3 repo census + git, S4 governance docs, S5 session docs, source code of 611 Python modules.*
