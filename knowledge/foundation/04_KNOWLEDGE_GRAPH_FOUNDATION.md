# 04 — Knowledge Graph Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only)
- Basis (ausschließlich): REFERENCE_GRAPH.md (MUSCAL-KRA-2026-08-01, Layer STRUCTURED KNOWLEDGE); DRAFT-Knoten zusätzlich aus ADR_REVIEW_MATRIX (G7-03)
- Prinzip: nur tatsächlich belegte Knoten und Beziehungen; keine Zukunftsarchitektur; CHAT_ONLY/PLANNED-Knoten explizit markiert, niemals als implementiert

## 1 Purpose

Darstellung des belegten Wissensgraphen (Knoten, Kanten, Eigenschaften) als Grundlage für Knowledge-Graph-Nutzung und GraphRAG-Evaluation. Keine neuen Knoten/Kanten; nur Wiedergabe von REFERENCE_GRAPH.md.

## 2 Scope

- Aufgenommen: alle 8 Knotentypen (Registry §1), die 12 Kernknoten (§2), die 17 belegten Kanten (§3), Graph-Charakteristik (§4), 5 Subgraphs (§5).
- Zusatz (belegt, G7-03): ADR-022…ADR-025 als DRAFT-Knoten.
- Nicht aufgenommen: die „~120 Knoten"-Gesamtschätzung als konkrete Knoten; Zukunftsarchitektur (MUSCAL 2.0, Cognitive Kernel, Agent P1…P5, Cognitive Compiler) nur als belegte PLANNED/CHAT_ONLY-Knoten (C2).

## 3 Node Model (belegt)

| Node type | ID-Prefix | Count | Quelle |
|---|---|---|---|
| Document | N-DOC | 12 | REFERENCE_GRAPH §1 |
| Chat conversation | N-CHAT | 44+ | REFERENCE_GRAPH §1 |
| Decision | D- | 26 (D-001…D-035) | REFERENCE_GRAPH §1 |
| Concept | C- | 19 | REFERENCE_GRAPH §1 |
| Code module | N-MOD | 14 | REFERENCE_GRAPH §1 |
| Session | N-SES | 16 | REFERENCE_GRAPH §1 |
| Audit milestone | N-AUD | 7 (MC-TC-002…007, E3.2) | REFERENCE_GRAPH §1 |
| Person/Role | N-PER | 2 | REFERENCE_GRAPH §1 |

## 4 Core Nodes (belegt, N-DOC-01…12)

| ID | Node | Kind | Kanonischer Ort |
|---|---|---|---|
| N-DOC-01 | PROJECT_STATE.md | Document | MUSCAL CORE/docs/PROJECT_STATE.md (20.07) |
| N-DOC-02 | SESSION_RULES.md | Document | MUSCAL CORE/.opencode/SESSION_RULES.md (20.07) |
| N-DOC-03 | TECHNICAL_BASELINE.md | Document | MUSCAL CORE/docs/TECHNICAL_BASELINE.md (12.07) |
| N-DOC-04 | DECISIONS.md | Document | MUSCAL CORE/docs/DECISIONS.md (12.07) |
| N-DOC-05 | CHANGE_JOURNAL.md | Document | MUSCAL CORE/docs/CHANGE_JOURNAL.md (13.07) |
| N-DOC-06 | ROADMAP.md | Document | MUSCAL CORE/docs/ROADMAP.md (08.07) |
| N-DOC-07 | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md | Document | MUSCAL CORE/docs/audit/ (31.07, untracked→committet 392734e) |
| N-DOC-08 | MC-TC-004_ARB_DECISION.md | Document | MUSCAL CORE/docs/audit/ (30.07, untracked→committet 392734e) |
| N-DOC-09 | ADR-001…014 | Documents | MUSCAL CORE/spec/ADR-*.md |
| N-DOC-10 | HANDOVER_S-2026-07-27-001.md | Document | docs/session_handovers/ |
| N-DOC-11 | TECHNICAL_MANUAL_v0.7.md | Document | MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md |
| N-DOC-12 | MC-TC-007 chat (31.07) | Chat | S2 `ChatGPT-MUSCAL CORE Audit Status.md` |

## 5 DRAFT-Knoten (belegt, ADR-022…025)

| Knoten | Status (unverändert) | Quelle |
|---|---|---|
| ADR-022 (MUSCAL 2.0 Hybrid) | DRAFT im Repo; Review NICHT GESTARTET (RC-4a) | ADR_REVIEW_MATRIX (G7-03), DECISION_CLOSURE_PACKAGE §RC-4 (NOT READY) |
| ADR-023 (Agent-Spezifikation) | DRAFT im Repo; Review NICHT GESTARTET (RC-4a) | ADR_REVIEW_MATRIX (G7-03) |
| ADR-024 (Compiler-Spezifikation) | DRAFT im Repo; Review NICHT GESTARTET (RC-4a) | ADR_REVIEW_MATRIX (G7-03) |
| ADR-025 (Tool-Integration / Nachfolge-Architektur) | DRAFT im Repo; Review NICHT GESTARTET (RC-4a) | ADR_REVIEW_MATRIX (G7-03) |

Kanten zu DRAFT-Knoten: nur belegt, sofern in REFERENCE_GRAPH oder G7-03; keine Ableitungs-Kanten neu erzeugt.

## 6 Edge Model (belegt)

| ID | From | Relation | To | Evidence | Confidence |
|---|---|---|---|---|---|
| E-001 | N-DOC-01 | DECLARES_AUTHORITY_OF | N-DOC-02..06, ADRs | SESSION_RULES Prio list | C0 |
| E-002 | N-DOC-02 | REQUIRES_READING | N-DOC-01 | „MUST read PROJECT_STATE first" | C0 |
| E-003 | N-DOC-05 | DEFINES_HIERARCHY | git history | „Git History → CHANGE_JOURNAL → SESSION_REGISTRY" | C0 |
| E-004 | git history | VIOLATED_BY | N-DOC-08, N-DOC-07, 29 core mods | 197 uncommitted (20.07–31.07) | C0 |
| E-005 | N-DOC-04 (D-001) | SUPERSEDES | MCXF interpreter | ADR-001 | C0 |
| E-006 | N-DOC-12 (D-017) | CONFLICTS_WITH | N-DOC-01 | CONDITIONAL GO vs READY WITH RISKS | C1 |
| E-007 | N-DOC-12 | REPORTS_ON | N-DOC-07 + N-DOC-08 | chat input = audit summaries | C1 |
| E-008 | N-DOC-10 | REPORTS_ON | MC-TC-004 phases | Handover listet 10 Phasen + impl S-01..S-04 | C0 |
| E-009 | N-SES-16 | LAST_HANDOVER | 27.07 | Registry-Lücke 28.–31.07 | C0 |
| E-010 | D-010 | DERIVED_FROM | MC-015-Turnier-Chat (25.07) | S2 | C2 |
| E-011 | D-012/D-013 | CHAT_ONLY | Agent/Compiler-Spec-Chats (30.07) | kein Repo-Artefakt | C2 |
| E-012 | N-DOC-11 | REFERENCES | kernel.py/memory.py/graph.py/event_bus.py (Zeilenzahlen) | M-0.7 §4 vs. Ist | C0 |
| E-013 | N-DOC-09 (ADR-013-Datei) | MISLABELED_AS | ADR-007-Inhalt | Dateiname ≠ Inhalt | C0 |
| E-014 | C-EventStore | IMPLEMENTED_IN | runtime/event_store.py + Commits | git log b9b17f3… | C0 |
| E-015 | C-CognitiveKernel | PLANNED_BY | D-011 | Proposal-Chat | C2 |
| E-016 | C-MUSCAL2.0 | PLANNED_BY | D-010 | Turnier-Chat | C2 |
| E-017 | N-DOC-03 | STALE_SINCE | 12.07 (Baseline) | mtime | C0 |

Edge-Typen gesamt (12): DECLARES_AUTHORITY, REQUIRES_READING, SUPERSEDES, CONFLICTS_WITH, REPORTS_ON, DERIVED_FROM, CHAT_ONLY, IMPLEMENTED_IN, PLANNED_BY, STALE_SINCE, MISLABELED_AS, VIOLATED_BY (REFERENCE_GRAPH §4).

## 7 Graph Characteristics (belegt)

- Knoten-Schätzung: ~120 (12 DOC + 44 CHAT + 26 D + 19 C + 14 MOD + 16 SES + 7 AUD + 2 PER) — **Schätzung** (REFERENCE_GRAPH §4), konkrete Knoten nur aus §2/§3.
- Dichte: low–medium; Hub = N-DOC-01 (PROJECT_STATE) und D-Knoten.
- Zeitdimension: create/mtime auf allen Knoten [C0] → Temporal-RAG-kompatibel.
- Confidence je Kante: C0–C2 vorhanden → confidence-gewichtetes Retrieval möglich.

## 8 Subgraphs (belegt)

1. **Status-Subgraph:** N-DOC-01 → CONFLICTS_WITH → N-DOC-12 → N-DOC-07/08 (neueste Wahrheit chat-only) — kritischer Retrieval-Pfad (REFERENCE_GRAPH §5).
2. **Decision-Lineage:** D-001 → D-002 … D-018 + Supersession-Kanten (Interpreter → Compiler → Cognitive Compiler).
3. **Implementation-Mapping:** C-Konzepte → N-MOD-Module → git-Commits → Sessions → Handovers.
4. **Chat→Repo-Mapping:** S2-Chats → behauptete Artefakte → verifizierte Existenz (CHAT_CODE_DOC_RECONCILIATION §3).

## 9 Known Limits

- Vollständige Kantentabelle (~120 Kanten) ist aus dem Extraction-Index reproduzierbar, in REFERENCE_GRAPH nicht enthalten — hier nur die 17 belegten Edges.
- N-CHAT (44+), C- (19), N-MOD (14), N-SES (16): nur Typzählung belegt; Einzelknoten nur beispielhaft (REFERENCE_GRAPH §1).
- Zukunftsarchitektur: C-MUSCAL2.0 (E-016), C-CognitiveKernel (E-015), D-012/D-013 (E-011) nur als PLANNED_BY/CHAT_ONLY (C2) — **nicht IMPLEMENTED** (kein Repo-Artefakt, DECISION_REGISTRY).

## 10 Validation

- Read-only: keine Datei verändert, keine neuen Knoten/Kanten, keine Statusänderung, kein Code.
- Quellenprüfung: alle Tabellenzeilen wörtlich aus REFERENCE_GRAPH.md (IDs, Relationen, Confidence, Evidence); ADR-022…025-DRAFT aus ADR_REVIEW_MATRIX (G7-03).
- Statusprüfung: DRAFT bleibt DRAFT (RC-4a NICHT GESTARTET); CHAT_ONLY (D-010…D-014, D-030…D-035) bleibt CHAT_ONLY; IMPLEMENTED nur bei C0/C1 (E-014, C0).
- Confidence-Prüfung: je Kante aus Quelle übernommen (C0…C2), keine Aufwertung.
- Widerspruchsprüfung: E-013 (ADR-013 MISLABELED_AS) konsistent mit PA-06-Korrektur (KF-1.1: behoben — Datei bewusst behalten, F-001/F-002); kein Widerspruch zu KF-Docs.
