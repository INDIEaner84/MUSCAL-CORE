# DECISION_REGISTRY — MUSCAL/ALITA Decisions extracted from S1 + S2 + S4

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** STRUCTURED KNOWLEDGE
**Purpose:** Base for future Source-of-Truth consolidation and the 20-doc Knowledge Foundation (Decision Graph).

**Status legend:** implemented · documented · planned · abandoned · conflicting

---

## A. Architecture Decisions

| ID | Decision | Date | Source | Category | Status | Confidence |
|----|----------|------|--------|----------|--------|------------|
| D-001 | Execution Graph Compiler instead of MCXF interpreter (MAS-0301; target <50ms) | 2026-07-04 | `docs/DECISIONS.md`, `spec/ADR-001-kernel.md`, `archive/history/rfcs/MAS-0301.md` | Architecture | implemented | C0 |
| D-002 | 7-layer architecture (L0 Storage – L6 Frontend) with 4 sub-kernels + System Spine validation | 2026-07-04 | DECISIONS.md, `spec/ADR-002-memory.md` | Architecture | implemented | C0 |
| D-003 | Capability-First routing (tasks vs capabilities, not model names) | 2026-07-04 | DECISIONS.md, `spec/ADR-003-events.md`, MAS-0001 | Architecture | implemented | C0 |
| D-004 | Lazy initialization replacing module-level import side effects | 2026-07-06 | DECISIONS.md | Stabilization | implemented | C0 |
| D-005 | Graph/Memory/Event bounding (5000/10000 nodes-edges, 10000 rows, 50000 events) | 2026-07-06 | DECISIONS.md | Stabilization | implemented | C0 |
| D-006 | All extensions as plugins in `features/`; core immutable | 2026-07-06 | DECISIONS.md, IMMUTABILITY_CONTRACT.md | Governance | implemented | C0 |
| D-007 | Verification layer as plugin (`features/event_sourcing/`), NOT core | 2026-07-11 | DECISIONS.md, `spec/ADR-011-verification.md` | Architecture | implemented | C0 |
| D-008 | EventBus / EventStore / AuditLog semantic separation (do NOT merge) | 2026-07-21 | S2 `Reconciliation Report Bewertung` | Architecture | implemented (EventStore exists) | C1 |
| D-009 | EventStore.append() signature must be verified before integration (bridge callback mismatch) | 2026-07-21 | S2 `Reconciliation Report Bewertung` | Integration | validated true | C1 |
| D-010 | MUSCAL 2.0: hybrid architecture wins MC-015 tournament (durable execution + hierarchical multi-agent + event-driven verification) | 2026-07-25 | S2 `MUSCAL 2.0 Architektur-Turnier` | Architecture (future) | planned (chat-only, no ADR) | C2 |
| D-011 | Cognitive Kernel + Authoritative Runtime on edge hardware (signed actions, verified event store) | 2026-07-25 | S2 `Cognitive Kernel Proposal` | Architecture (future) | planned (chat-only) | C2 |
| D-012 | Agent Architecture principles P1–P5 (Modularity, Specialization, Observability, Replaceability, **Human Sovereignty**) | 2026-07-30 | S2 `MUSCAL Agent Architecture` | Architecture (future) | planned (spec draft chat-only) | C2 |
| D-013 | Prompts as declarative cognitive programs (Cognitive Compiler v1.0) | 2026-07-30 | S2 `MUSCAL Compiler Spezifikation` | Architecture (future) | planned (chat-only) | C2 |
| D-014 | Formal Specification RFC-series (implementierungsunabhängig; no code) | 2026-07-29 | S2 `formale Spezifikation` | Specification | planned (chat-only) | C2 |
| D-015 | E3.2 Trust Boundary Closure: 9 bypasses closed (7 CLOSED, 1 MITIGATED B-07), OVERRIDE-067..073 | 2026-07-23 | S2 `E3.2 Trust Boundary Abschluss`, `docs/engineering/D-E3.2-001-*`, `spec/OVERRIDE.md` | Security/Architecture | implemented | C1 |
| D-016 | MC-TC-004 ARB Decision: **CERTIFIED** (33/33 criteria, 431/431 tests, 14/16 invariants) | 2026-07-30 | `docs/audit/MC-TC-004_ARB_DECISION.md` (untracked), S2 31.07 | Certification | implemented (not in git) | C1 |
| D-017 | MC-TC-007: **CONDITIONAL GO** — Graph-OS layer not certified; 2 P0 blockers | 2026-07-31 | S2 `MUSCAL CORE Audit Status` (chat-only) | Certification | conflicting (vs PROJECT_STATE "READY WITH RISKS") | C2 |
| D-018 | ADR-014: Unified Tool Runtime consolidation | 2026-07-28 | `spec/ADR-014-tool-runtime.md` | Architecture | **conflicting** (PROPOSED in PROJECT_STATE 20.07 vs updated file 28.07) | C1 |

## B. Governance Decisions

| ID | Decision | Date | Source | Category | Status | Confidence |
|----|----------|------|--------|----------|--------|------------|
| D-020 | Core files IMMUTABLE; write only via OVERRIDE + `--allow-core-write` | 2026-07-06 | SESSION_RULES.md, IMMUTABILITY_CONTRACT.md | Governance | implemented | C0 |
| D-021 | Mandatory SESSION_HANDOVER for every session with changes | 2026-07-11 | SESSION_RULES.md, HANDOVER_TEMPLATE.md | Governance | partially enforced (14 handovers; none 28.–31.07) | C1 |
| D-022 | Authority hierarchy: Git History → CHANGE_JOURNAL → SESSION_REGISTRY | 2026-07-12 | CHANGE_JOURNAL.md | Governance | **violated** (197 uncommitted changes) | C0 |
| D-023 | HDR-001 (Architecture Council) — READY FOR HUMAN DECISION, blocks HDR-002..004 | 2026-07-20 | PROJECT_STATE.md | Governance | documented; unresolved since 20.07 | C1 |
| D-024 | `simulation_mode: bool` → `ExecutionMode` enum (MC-TC-003B override) | 2026-07-25 | `spec/OVERRIDE.md` (Codebase root) | Governance | implemented | C1 |
| D-025 | ADR authority: baseline docs > historical docs | 2026-07-20 | SESSION_RULES.md §HISTORICAL | Governance | implemented | C0 |

## C. Roadmap / Strategy Decisions

| ID | Decision | Date | Source | Category | Status | Confidence |
|----|----------|------|--------|----------|--------|------------|
| D-030 | Next milestone after E3.5.1: **E3.6 Knowledge Distillation** | 2026-07-27 | S2 `Reality Closure Review` | Roadmap | planned | C2 |
| D-031 | Reality score 55/100 — production-readiness indicator, not quality verdict | 2026-07-27 | S2 `Reality Closure Review` | Evaluation | documented (score chat-only) | C2 |
| D-032 | MUSCAL → agent-driven self-development transition ("MUSCAL entwickelt sich durch Agenten") | 2026-07-21 | S2 `Agenten-Orchestrierung` | Strategy | planned (vision) | C2 |
| D-033 | Closed-source strategy: release plugins only | 2026-07-23 | S2 `Closed-Source Projektplan` | Strategy | planned | C2 |
| D-034 | Benchmark framework: MUSCAL vs LangChain / AutoGen / CrewAI | 2026-07-29 | S2 `Benchmark Framework Planung` | Evaluation | planned | C2 |
| D-035 | SLM dataset strategy for specialization efficiency | 2026-07-29 | S2 `Datenstrategie für SLM` | Strategy | planned | C2 |

## D. Conflicting / Contradictory Decisions

| ID | Conflict | Sources | Severity |
|----|----------|---------|----------|
| D-017 | MC-TC-007 CONDITIONAL GO vs PROJECT_STATE "READY WITH RISKS" | S2 31.07 vs PROJECT_STATE 20.07 | HIGH — status authority undefined |
| D-018 | ADR-014 PROPOSED (20.07) vs modified ADR-014 file (28.07) | PROJECT_STATE vs spec file | MEDIUM |
| D-006/D-022 | "Core immutable" (D-006) vs 29 modified core files uncommitted (D-022 violation) | SESSION_RULES vs git status | **CRITICAL** |
| D-021 | "Every session creates handover" vs 28.–31.07 sessions without handover | SESSION_RULES vs SESSION_REGISTRY/handover dir | HIGH |
| D-014 vs D-013 | Formal spec says "keine Implementierung" vs compiler spec is implementation-oriented | S2 29.07 vs S2 30.07 | LOW (different scopes) |
| D-010 vs D-001 | MUSCAL 2.0 hybrid (multi-agent) vs current single-agent kernel (D-001 path) | S2 25.07 vs code | MEDIUM — migration path undefined |

## E. Missing / Undocumented Decisions (Knowledge Gaps)

| Gap | Evidence | Implication |
|-----|----------|-------------|
| No ADR for EventStore/ReplayService introduction (commits 07-19/20, ADR-EVENT-001 only in `spec/ADRs/`) | `spec/ADRs/ADR-EVENT-001-eventstore-boundary.md` exists but not in canonical `spec/` set | ADR numbering inconsistency |
| No ADR for v0.8 (CHANGELOG_v0.8.md exists, no ADR-015+) | CHANGELOG_v0.8.md | Version documentation gap |
| No documented MC-015 → ADR conversion | S2 25.07 | Architecture direction invisible to repo |
| MKSD (MUSCAL Kernel Specification Document) explicitly missing | S2 `Spezifikation offen` 28.07 | Spec gap confirmed |

---

*Provenance: DECISIONS.md, SESSION_RULES.md, CHANGE_JOURNAL.md, PROJECT_STATE.md, spec/ADRs, docs/audit files, S2 chats (file + link IDs), git log. Confidence per AUDIT_SCOPE §5.*

## PB-02. Phase-B Konsolidierung (added 2026-08-01, Phase B)

| ID | Hinweis |
|----|---------|
| PB-02 | D-010…D-035 in 10-Feld-Format konsolidiert (Status-Normalisierung auf IMPLEMENTED/DOCUMENTED/PLANNED/ABANDONED/CONFLICTING/UNKNOWN): `MUSCAL CORE/docs/audit/PB02_DECISION_REGISTRY_CONSOLIDATED_D010_D035.md` (committet). Registry bleibt autoritativ.

## F. G2 Adjudication Decisions (added 2026-08-01, G2 gate approval)

| ID | Decision | Date | Source | Category | Status | Confidence |
|----|----------|------|--------|----------|--------|------------|
| D-036 | **G2-01**: C1 EventStore/Replay cluster (4 files) SANCTIONED — keep as-is; MC-TC-004/006 certification is the decision record | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-01 | Adjudication | applied (committed) | C1 |
| D-037 | **G2-02**: C2 Phase 1A execution-identity cluster (7 files) SANCTIONED-CONDITIONAL — keep + governance update; OVERRIDE.md truth correction | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-02 | Adjudication | applied (committed + OVERRIDE.md corrected) | C1 |
| D-038 | **G2-03/04/06**: C3 UTR (5 files), C4 Phase 1b (4 files), 6 swept files SANCTIONED; ADR-014 finalized DRAFT→ACCEPTED | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-03/G2-04/G2-06 | Adjudication | applied (committed + ADR-014 updated) | C1 |
| D-039 | **G2-05/07**: OVERRIDE.md reconstructed from baseline + Phase 1A wave sections + truth correction; OVERRIDE-052 mechanism restored | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-05/G2-07 | Governance | applied | C0 |
| D-040 | **FL-01a**: 19 order-dependent flaky tests NOT fixed — documented as register; global-singleton root cause (`tools._UTR`, `set_global_utr`, `set_global_event_store`); fix (test fixtures) deferred | 2026-08-01 | G2_ADJUDICATION_REPORT.md FL-01a | Test governance | documented (open) | C1 |
| D-041 | **FL-01b**: 4 deterministic baseline-drift failures — EXPECTED_TOTAL recalibrated to verified reconciliation counts (test-only) | 2026-08-01 | G2_ADJUDICATION_REPORT.md FL-01b | Test governance | applied (test-only commit) | C0 |
| D-042 | Global-state ownership ADR as Phase B follow-up (singleton policy for `_UTR`/event-store globals) | 2026-08-01 | G2_ADJUDICATION_REPORT.md FL-01a → D | Roadmap | planned (Phase B) | C2 |

## G. G2 Conflict Resolutions (updates to §D)

| Old conflict | Resolution (G2) |
|--------------|-----------------|
| D-006/D-022 "Core immutable" vs 29 modified files | **RESOLVED** — 22 files adjudicated (G2-01..04: SANCTIONED, committed per cluster) + 6 swept files retroactively sanctioned (D-038); OVERRIDE.md truth correction closes the documentation gap (D-039) |
| D-018 ADR-014 PROPOSED vs modified file | **RESOLVED** — ADR-014 finalized ACCEPTED with governance links (D-038) |
| D-017 MC-TC-007 CONDITIONAL GO vs PROJECT_STATE | **RESOLVED (doc-level)** — PROJECT_STATE.md updated 01.08 with MC-TC-004/006/007 audit status + P0 section (commit d5f5ce7); D-017 remains an operational P0-mitigation item |
| OVERRIDE-052 mechanism deactivated (new conflict) | **RESOLVED** — baseline registry restored in OVERRIDE.md (D-039) |
