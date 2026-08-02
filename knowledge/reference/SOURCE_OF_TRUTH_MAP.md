# SOURCE_OF_TRUTH_MAP — Authority across all MUSCAL knowledge sources

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** STRUCTURED KNOWLEDGE / INFERRED
**Sources:** S1–S5 · **Date:** 2026-08-01

---

## 1. Method

For 7 knowledge domains, the audit determines:
- **DE JURE authority** — what SESSION_RULES.md/CHANGE_JOURNAL.md declare as authoritative
- **DE FACTO authority** — where the data actually lives, and whether it is current
- **STALENESS** — last update date per authoritative document

Confidence tags per row: C0 (verified), C1 (high), C2 (medium), C3 (low), HYP (hypothesis).

## 2. Domain Authority Matrix

### 2.1 Architecture

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| Current architecture | `docs/TECHNICAL_BASELINE.md` (Prio 2) | `docs/TECHNICAL_BASELINE.md` — **updated 2026-07-12** | ⚠️ STALE (pre-dates v0.8 & all MC-TC audits) | C0 (mtime) |
| Architecture overview | `docs/ARCHITECTURE.md` (Prio 5) | updated **2026-07-12** | ⚠️ STALE | C0 |
| ADRs | `spec/ADR-*.md` (Prio 3) | 14 files, updated up to **2026-07-28** (ADR-014) | ✅ mostly current | C0 |
| Historical ADRs/RFCs | `archive/history/` (Prio 4, no authority) | 6 + 18 files | Historical only | C0 |
| **Real code state** | — | root `*.py` + `features/` + `runtime/` — **modified up to 2026-07-28** | ✅ current | C0 |

> **FINDING A1 [C0]:** The two top-priority architecture documents (`TECHNICAL_BASELINE.md`, `ARCHITECTURE.md`) date from **2026-07-12**. All architecture work since — v0.8, Graph-OS freeze, MC-TC-002→007 audits, EventStore layer, E3.2 trust boundary — is reflected **only in audit docs and code**, not in the baseline documents.

### 2.2 Implementation

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| What is implemented | Git history + code (CHANGE_JOURNAL hierarchy #1) | **Last commit 2026-07-20; 197 uncommitted changes** | ❌ 11 days of work invisible to git | C0 |
| Feature status | `docs/governance/ACTIVE_TASKS.md`, `WORK_QUEUE.md` | updated **2026-07-20** | ⚠️ STALE | C0 |
| Test status | `docs/PROJECT_STATE.md` (547/547) | claims from **2026-07-20**; test functions now 2,869 | ❌ STALE + scope mismatch | C1 |

### 2.3 Roadmap

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| Roadmap | `docs/ROADMAP.md` | updated **2026-07-08** — "Next (v0.8): feature plugins, stub cleanup, semantic eviction" | ❌ STALE (v0.8 largely done, no v0.9+ plan) | C0 |
| Active direction | chats S1/S2 (e.g. MUSCAL 2.0 tournament, Cognitive Kernel proposal) | **26.07–31.07 chats only in S2** | ✅ current but NOT in repo docs | C1 |

### 2.4 Session State

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| Session state | `docs/PROJECT_STATE.md` (Prio 1) | **2026-07-20** | ⚠️ STALE vs audits (30.07) & handovers (27.07) | C0 |
| Session registry | `docs/SESSION_REGISTRY.md` | **2026-07-28** (last session entry 07-27) | ⚠️ no entries for 28.–31.07 | C0 |
| Handovers | `docs/session_handovers/` | newest **2026-07-27** | ⚠️ no handover for 28.–31.07 work | C0 |

### 2.5 Project Status

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| Project status | `docs/PROJECT_STATE.md` | "READY WITH RISKS", HDR-001 BLOCKING (9 deps) — **2026-07-20** | ⚠️ STALE | C0 |
| Audit status | `docs/audit/MC-TC-*.md` | **up to 2026-07-30** (MC-TC-004 CERTIFIED) | ✅ current but UNTRACKED in git | C0 |
| Latest chat claim | S2 `ChatGPT-MUSCAL CORE Audit Status` (31.07): "MC-TC-007 CONDITIONAL GO, Graph-OS not certified, 2 P0 blockers" | **2026-07-31** | ✅ newest status statement | C2 (chat-based) |

> **FINDING A2 [C1]:** The **newest, most complete project-status statement exists only in a chat export (S2, 31.07)** — not in any repository document. A fresh session following SESSION_RULES would read PROJECT_STATE (20.07) and miss: MC-TC-004 certification, MC-TC-007 conditional-go, the two P0 blockers, and the entire E3.2 closure. See SESSION_CONTINUITY_AUDIT.md.

### 2.6 Historical Decisions

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| Decisions | `docs/DECISIONS.md` + ADRs + CHANGE_JOURNAL | `DECISIONS.md` updated **2026-07-12**; CHANGE_JOURNAL ends **2026-07-13** | ⚠️ STALE — missing 2 weeks of decisions | C0 |
| ADR-014 (Tool Runtime) | `spec/ADR-014-tool-runtime.md` | updated **2026-07-28** — but marked **PROPOSED** in PROJECT_STATE (20.07) | ⚠️ conflicting status | C1 |

### 2.7 Future Plans

| Aspect | DE JURE | DE FACTO | Current? | Confidence |
|--------|---------|----------|----------|------------|
| Future plans | `docs/ROADMAP.md` | stale (07-08) | ❌ | C0 |
| MUSCAL 2.0 direction | S2 chat `MUSCAL 2.0 Architektur-Turnier` (25.07) | **MC-015: hybrid winner (durable execution + hierarchical multi-agent + event-driven verification)** | ✅ current, chat-only | C2 |
| Cognitive Kernel | S2 chat `Cognitive Kernel Proposal` (25.07) | hardware-partnership proposal, "authoritative runtime" | ✅ current, chat-only | C2 |

## 3. Authority Gap Summary

| Domain | Authority exists? | Current? | Git-visible? | Chat-only content |
|--------|-------------------|----------|--------------|-------------------|
| Architecture | ✅ (baseline+ADRs) | ⚠️ baseline stale | ⚠️ partially | MC-015 2.0 tournament, Cognitive Kernel |
| Implementation | ✅ (code) | ✅ code, ❌ git | ❌ 197 changes | Agent Architecture spec (30.07) |
| Roadmap | ✅ (ROADMAP.md) | ❌ stale 07-08 | ✅ | MUSCAL 2.0, E3.6 Knowledge Distillation |
| Session state | ✅ (PROJECT_STATE) | ⚠️ stale 07-20 | ⚠️ | OC Session-State Test (20.07) |
| Project status | ✅ (PROJECT_STATE) | ❌ **chat has newest** | ❌ audits untracked | MC-TC-007 status (31.07) |
| Historical decisions | ✅ (DECISIONS/ADR/JOURNAL) | ⚠️ journal ends 07-13 | ⚠️ | Decision Registry chat outputs |
| Future plans | ✅ (ROADMAP) | ❌ | ✅ | Benchmark framework, Data strategy SLM |

## 4. Recommendation (input to MASTER_INDEX)

**SO-1 [HIGH]:** Establish a single machine-readable SOURCE_OF_TRUTH manifest (`docs/SOURCE_OF_TRUTH.md`) listing for each domain: document, owner, last-update-check, and sync-gate (update PROJECT_STATE after every audit milestone).
**SO-2 [HIGH]:** Commit the 197 pending changes and close the 11-day git gap — per CHANGE_JOURNAL's own hierarchy, Git History is the technical truth, and it is currently missing the entire audit wave.
**SO-3 [MEDIUM]:** Migrate the two highest-value chat-only statuses (MC-TC-007 status 31.07, MUSCAL 2.0 direction 25.07) into repo documents (PROJECT_STATE + DECISIONS) — chat is not an authoritative document store.
**SO-4 [MEDIUM]:** Resolve ADR location duplication (4 sites) — declare `spec/` canonical, archive the rest.
**SO-5 [LOW]:** Version-align the manuals (v0.5 root / v0.6 history / v0.7 current) — see TECHNICAL_MANUAL_CONFLICT_REPORT.md.

---

*Provenance: document mtimes from file system; chat dates from S2 headers; status claims from PROJECT_STATE.md, MC-TC-007_STATUS_ZUSAMMENFASSUNG.md, HANDOVER_S-2026-07-27-001.md.*
