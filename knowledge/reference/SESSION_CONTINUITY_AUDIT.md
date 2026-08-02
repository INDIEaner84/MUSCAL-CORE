# SESSION_CONTINUITY_AUDIT — Can a fresh OpenCode session reconstruct the project?

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** STRUCTURED KNOWLEDGE / INFERRED / HYPOTHESIS
**Date:** 2026-08-01 · **Method:** simulated fresh session strictly following `.opencode/SESSION_RULES.md` reading order; each reconstruction target scored by what the documents alone would yield.

---

## 1. Simulation Setup

A new OpenCode session in `MUSCAL CORE/` is started with zero prior context. It reads, in order:
1. `docs/PROJECT_STATE.md` (Prio 1)
2. `docs/TECHNICAL_BASELINE.md` (Prio 2)
3. `spec/ADR-*.md` (Prio 3)
4. `archive/history/adrs/*`, `archive/history/rfcs/*` (Prio 4, reference only)
5. `docs/ARCHITECTURE.md` (Prio 5)
6. `README.md` (Prio 6)

Optionally: `docs/SESSION_REGISTRY.md`, `docs/CHANGE_JOURNAL.md`, handovers.

## 2. Reconstruction Scoring

Score = how accurately the session can reconstruct each target **from these documents alone** (100 = fully accurate & current; 0 = nothing).

| Target | Documents available | Newest source date | Reconstructable? | Score | Confidence |
|--------|--------------------|--------------------|------------------|-------|------------|
| **Project phase/status** | PROJECT_STATE: "Prototype Stable / READY WITH RISKS", HDR-001 blocking | 2026-07-20 | Partial — status **11 days stale**; newest status (MC-TC-007 Conditional GO, Graph-OS P0) lives only in chat (31.07) | **35/100** | C1 |
| **Architecture state** | TECHNICAL_BASELINE + ARCHITECTURE (12.07) + 14 ADRs + ADR-EVENT/API/RUNTIME (spec/ADRs/) | 2026-07-28 (ADR-014) | Mostly — 7 layers, capability-first, plugin model, EventStore via ADR-012/ADRs. But Graph-OS freeze (30.07) and MUSCAL 2.0 direction missing | **70/100** | C1 |
| **Active roadmap** | ROADMAP.md — v0.7 done, v0.8 items listed | 2026-07-08 | Poor — roadmap 3.5 weeks stale; E3.2→E3.6 wave, benchmark framework, agent specs invisible | **25/100** | C1 |
| **Audit status** | none in prio-1..6 docs; handovers mention MC-TC-004 pre-gate (27.07); audit dir has 55 files but SESSION_RULES does not reference it | 2026-07-30 (untracked) | **No** — the session would not even look at `docs/audit/`; MC-TC-004 CERTIFIED + MC-TC-007 not reachable via reading order | **10/100** | C1 |
| **Current priorities** | ACTIVE_TASKS / WORK_QUEUE (20.07) | 2026-07-20 | Weak — HDR-001 blocking stated, but post-20.07 priorities (E3.6 Knowledge Distillation, Graph-OS P0 blockers) missing | **30/100** | C1 |
| **Historical decisions** | DECISIONS.md + ADRs + CHANGE_JOURNAL (ends 13.07) | 2026-07-13 | Partial — decisions to 11.07 documented; 13.07–31.07 decisions (E3.2, MC-TC-004, EventStore evolution, MUSCAL 2.0) missing | **55/100** | C1 |
| **Implementation truth** | git history (last commit 20.07) — CHANGE_JOURNAL hierarchy | 2026-07-20 | Partial — 197 uncommitted changes invisible; session sees code files (current mtimes) but no commit trail | **60/100** | C1 |

## 3. What a Fresh Session Would MISS (gap list)

| # | Missing knowledge | Where it exists | Impact |
|---|-------------------|-----------------|--------|
| M-1 | MC-TC-007 status: **CONDITIONAL GO, 2 P0 blockers** (Graph-OS not reconstructable; watchdog events not persisted) | S2 chat 31.07 only | **CRITICAL** — session would treat project as "READY WITH RISKS" and may start feature work instead of closing P0s |
| M-2 | MC-TC-004 certification + MC-TC-005 NOT AUTHORIZED | audit files (untracked, 30.07) | HIGH — scope boundary unknown |
| M-3 | E3.2 closure + B-07 remaining mitigation | `docs/engineering/D-E3.2-001-*` (untracked) | HIGH — trust-boundary state unknown |
| M-4 | MUSCAL 2.0 direction (MC-015 hybrid) | chat 25.07 | MEDIUM — architectural drift risk |
| M-5 | Session continuity broken: no handover 28.–31.07; SESSION_REGISTRY ends 27.07 | registry + handover dir | HIGH — who did what on 28–31.07? |
| M-6 | 29 modified core files (immutability violation, uncommitted) | git status | HIGH — session may "fix" files that were intentionally changed post-20.07 |
| M-7 | v0.8 changelog exists but ROADMAP/DECISIONS not updated | CHANGELOG_v0.8.md | MEDIUM |
| M-8 | ADR-013 file mislabeled (contains ADR-007 content) | spec/ADR-013-pipeline.md | LOW — wrong references |

## 4. Document Freshness Table (S5)

| Document | Last update | Age at audit | OK? |
|----------|-------------|--------------|-----|
| PROJECT_STATE.md | 2026-07-20 | 12 days | ❌ |
| TECHNICAL_BASELINE.md | 2026-07-12 | 20 days | ❌ |
| ARCHITECTURE.md | 2026-07-12 | 20 days | ❌ |
| ROADMAP.md | 2026-07-08 | 24 days | ❌ |
| DECISIONS.md | 2026-07-12 | 20 days | ❌ |
| CHANGE_JOURNAL.md | 2026-07-13 | 19 days | ❌ |
| SESSION_REGISTRY.md | 2026-07-28 | 4 days | ⚠️ (last session 27.07) |
| Handovers | 2026-07-27 | 5 days | ⚠️ (28.–31.07 missing) |
| AGENTS.md / SESSION_RULES.md | 2026-07-20/22 | 10–12 days | ⚠️ (rule text OK, references stale) |

## 5. Root-Cause Analysis

**RCA-1 [C1] — No single "current status" authority is fed by the audit wave.** The audit/certification process (MC-TC-002→007) produces 55 files in `docs/audit/` but nothing updates PROJECT_STATE.md or SESSION_REGISTRY. The audits themselves are the newest truth, yet SESSION_RULES' reading order never reaches them.
**RCA-2 [C0] — Git gap.** Last commit 20.07; all audit artifacts untracked. CHANGE_JOURNAL's own hierarchy (Git = truth) therefore hides the audit wave.
**RCA-3 [C1] — Handover discipline lapsed after 27.07.** Sessions that produced MC-TC-004 certification (30.07) and MC-TC-007 status (31.07) left no handover.

## 6. Continuity Score

**SESSION_CONTINUITY_SCORE = 41/100** (average of §2 targets, unweighted) [C1]
→ Classification: **REQUIRES RECONCILIATION PHASE + governance cleanup** (see MASTER_INDEX recommendation).

## 7. Minimum Fix (enforcement path, NOT executed in this audit)

1. After every certification milestone: **update PROJECT_STATE.md + SESSION_REGISTRY.md** (one-line status section).
2. Extend SESSION_RULES Prio list: insert `docs/audit/MC-TC-*` and `docs/session_handovers/` as reading sources (Prio 2b).
3. Commit the audit wave (197 files) — restore Git-as-truth.
4. Add a "P0 blockers" section to PROJECT_STATE that mirrors the newest audit status.
5. Close the handover gap retroactively (28.–31.07 work items).

---

*Provenance: SESSION_RULES.md reading order; document mtimes; git log/status; handover contents; S2 31.07 chat status; audit dir listing.*
