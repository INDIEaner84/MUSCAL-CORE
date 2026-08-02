# REFERENCE_GRAPH — Cross-source reference network

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** STRUCTURED KNOWLEDGE
**Purpose:** Machine-readable node/edge model for the future Knowledge Graph (20-doc plan, doc 04) and GraphRAG evaluation (doc 17).

**ID conventions:** `N-` nodes, `E-` edges, `D-` decisions (see DECISION_REGISTRY), `C-` concepts (see CONCEPT_EVOLUTION_MAP).

---

## 1. Node Types (registry)

| Node type | ID prefix | Count | Examples |
|-----------|-----------|------:|----------|
| Document | N-DOC | 12 | PROJECT_STATE, SESSION_RULES, ADR-001, MC-TC-004_ARB, HANDOVER-07-27 |
| Chat conversation | N-CHAT | 44+ | S2 files (by link ID), S1 IDs |
| Decision | D- | 26 | D-001…D-035 |
| Concept | C- | 19 | MUSCAL, EventStore, Cognitive Kernel |
| Code module | N-MOD | 14 | kernel.py, event_store.py |
| Session | N-SES | 16 | S-2026-07-11-001 … S-2026-07-27-001 |
| Audit milestone | N-AUD | 7 | MC-TC-002…007, E3.2 |
| Person/Role | N-PER | 2 | MASTER ORCHESTRATOR (ADR author), [user] |

## 2. Core Nodes

| ID | Node | Kind | Canonical location |
|----|------|------|--------------------|
| N-DOC-01 | PROJECT_STATE.md | Document | `MUSCAL CORE/docs/PROJECT_STATE.md` (20.07) |
| N-DOC-02 | SESSION_RULES.md | Document | `MUSCAL CORE/.opencode/SESSION_RULES.md` (20.07) |
| N-DOC-03 | TECHNICAL_BASELINE.md | Document | `MUSCAL CORE/docs/TECHNICAL_BASELINE.md` (12.07) |
| N-DOC-04 | DECISIONS.md | Document | `MUSCAL CORE/docs/DECISIONS.md` (12.07) |
| N-DOC-05 | CHANGE_JOURNAL.md | Document | `MUSCAL CORE/docs/CHANGE_JOURNAL.md` (13.07) |
| N-DOC-06 | ROADMAP.md | Document | `MUSCAL CORE/docs/ROADMAP.md` (08.07) |
| N-DOC-07 | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md | Document | `MUSCAL CORE/docs/audit/` (31.07, untracked) |
| N-DOC-08 | MC-TC-004_ARB_DECISION.md | Document | `MUSCAL CORE/docs/audit/` (30.07, untracked) |
| N-DOC-09 | ADR-001…014 | Documents | `MUSCAL CORE/spec/ADR-*.md` |
| N-DOC-10 | HANDOVER_S-2026-07-27-001.md | Document | `docs/session_handovers/` |
| N-DOC-11 | TECHNICAL_MANUAL_v0.7.md | Document | `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md` |
| N-DOC-12 | MC-TC-007 chat (31.07) | Chat | S2 `ChatGPT-MUSCAL CORE Audit Status.md` |

## 3. Edges (selected — full set in extraction index)

| ID | From | Relation | To | Evidence | Confidence |
|----|------|----------|----|----------|------------|
| E-001 | N-DOC-01 | DECLARES_AUTHORITY_OF | N-DOC-02..06, ADRs | SESSION_RULES Prio list | C0 |
| E-002 | N-DOC-02 | REQUIRES_READING | N-DOC-01 | "MUST read PROJECT_STATE first" | C0 |
| E-003 | N-DOC-05 | DEFINES_HIERARCHY | git history | "Git History → CHANGE_JOURNAL → SESSION_REGISTRY" | C0 |
| E-004 | git history | VIOLATED_BY | N-DOC-08, N-DOC-07, 29 core mods | 197 uncommitted (20.07–31.07) | C0 |
| E-005 | N-DOC-04 (D-001) | SUPERSEDES | MCXF interpreter | ADR-001 | C0 |
| E-006 | N-DOC-12 (D-017) | CONFLICTS_WITH | N-DOC-01 | CONDITIONAL GO vs READY WITH RISKS | C1 |
| E-007 | N-DOC-12 | REPORTS_ON | N-DOC-07 + N-DOC-08 | chat input = audit summaries | C1 |
| E-008 | N-DOC-10 | REPORTS_ON | MC-TC-004 phases | handover lists 10 phases + impl S-01..S-04 | C0 |
| E-009 | N-SES-16 | LAST_HANDOVER | 27.07 | registry gap 28.–31.07 | C0 |
| E-010 | D-010 | DERIVED_FROM | MC-015 tournament chat (25.07) | S2 | C2 |
| E-011 | D-012/D-013 | CHAT_ONLY | Agent/Compiler spec chats (30.07) | no repo artifact | C2 |
| E-012 | N-DOC-11 | REFERENCES | kernel.py/memory.py/graph.py/event_bus.py (line counts) | M-0.7 §4 vs actual | C0 |
| E-013 | N-DOC-09 (ADR-013 file) | MISLABELED_AS | ADR-007 content | filename ≠ content | C0 |
| E-014 | C-EventStore | IMPLEMENTED_IN | runtime/event_store.py + commits | git log b9b17f3… | C0 |
| E-015 | C-CognitiveKernel | PLANNED_BY | D-011 | proposal chat | C2 |
| E-016 | C-MUSCAL2.0 | PLANNED_BY | D-010 | tournament chat | C2 |
| E-017 | N-DOC-03 | STALE_SINCE | 12.07 (baseline) | mtime | C0 |

## 4. Graph Characteristics (for GraphRAG evaluation)

| Metric | Value |
|--------|-------|
| Node count (draft) | ~120 (12 DOC + 44 CHAT + 26 D + 19 C + 14 MOD + 16 SES + 7 AUD + 2 PER) |
| Edge types | 12 (DECLARES_AUTHORITY, REQUIRES_READING, SUPERSEDES, CONFLICTS_WITH, REPORTS_ON, DERIVED_FROM, CHAT_ONLY, IMPLEMENTED_IN, PLANNED_BY, STALE_SINCE, MISLABELED_AS, VIOLATED_BY) |
| Density | low–medium; hub = N-DOC-01 (PROJECT_STATE) and D- nodes |
| Temporal dimension | available via create/mtime on all nodes [C0] → Temporal RAG compatible |
| Confidence per edge | available (C0–C2) → confidence-weighted retrieval possible |

## 5. High-Value Subgraphs for Retrieval

1. **Status subgraph:** N-DOC-01 → conflicts → N-DOC-12 → N-DOC-07/08 (newest truth is chat-only) — **critical retrieval path** for any agentic RAG.
2. **Decision lineage:** D-001 → D-002 … D-018 + supersession edges (interpreter→compiler→cognitive compiler).
3. **Implementation mapping:** C- concepts → N-MOD modules → git commits → sessions → handovers.
4. **Chat→Repo mapping:** S2 chats → claimed artifacts → verified existence (CHAT_CODE_DOC_RECONCILIATION §3).

---

*Provenance: derived from all audit documents + raw sources. Full edge table (≈120 edges) is reproducible from the extraction index; selected high-value edges shown above.*
