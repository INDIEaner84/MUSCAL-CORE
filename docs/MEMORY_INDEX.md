# MUSCAL CORE — MEMORY_INDEX

**Zweck:** Navigation aller MUSCAL Wissensspeicher.

---

## docs/ — Projektdokumentation

| Datei | Zweck |
|-------|-------|
| PROJECT_STATE.md | Aktueller Projektstatus |
| TECHNICAL_BASELINE.md | Verbindliche Architektur |
| ARCHITECTURE.md | Layering-Übersicht |
| SESSION_REGISTRY.md | Session-Status (Statusinfo, nicht autoritativ) |
| TASK_BOARD.md | Aufgaben mit Architecture Impact |
| LOCK_PROTOCOL.md | Lock-Level Definition |
| GOVERNANCE_CHECKPOINT.md | Governance Status Übersicht |
| CHANGE_JOURNAL.md | Human-readable Changelog |
| SESSION_OWNERSHIP.md | Ownership-Modell |

---

## spec/ — Architecture Decision Records

→ `spec/ADR-INDEX.md`

| ADR | Titel | Status |
|-----|-------|--------|
| ADR-001 | Kernel Runtime | APPLIED |
| ADR-002 | Memory — GraphMemory | ACCEPTED |
| ADR-003 | Event System — EventBus | APPLIED |
| ADR-004 | Plugin System — Hook-Based | ACCEPTED |
| ADR-005 | Pipeline Architecture | ACCEPTED |
| ADR-006 | Graph/Sphere | ACCEPTED |
| ADR-007 | Core Immutability | ACCEPTED |
| ADR-008 | Deployment Runtime | ACCEPTED |
| ADR-009 | Observability Foundation | ACCEPTED |
| ADR-010 | SQLite Consolidation | APPLIED |
| ADR-011 | Verification Layer | ACCEPTED |
| ADR-012 | Event Persistence | APPLIED |

---

## archive/ — Historische Dokumente

- `archive/history/adrs/` — historische ADRs (ADR-001 bis ADR-006)
- `archive/history/rfcs/` — RFCs (MAS-0000 bis MAS-0500)
- `archive/stubs/` — deaktivierte Stub-Dateien
- `archive/*.py` — archivierte Module

---

## Runtime Memory Layer

| Speicher | Technologie | Zweck |
|----------|-------------|-------|
| SQLite | WAL, 5 Tabellen | Persistenz |
| JSONL | storage/logs.jsonl | Audit Log |
| ChromaDB | Vector Store | RAG-Embeddings |

---

## Memory Authority

Dokumente besitzen unterschiedliche Autorität:

| Tier | Enthält | Beispiele |
|------|---------|-----------|
| **Tier 1** | ADRs, Contracts, Governance Rules | ADR-001, IMMUTABILITY_CONTRACT, LOCK_PROTOCOL |
| **Tier 2** | Architecture Docs, Technical Baselines | ARCHITECTURE.md, TECHNICAL_BASELINE.md |
| **Tier 3** | Session Dokumentation, Historische Notizen | SESSION_REGISTRY, HANDOVER, history/* |
