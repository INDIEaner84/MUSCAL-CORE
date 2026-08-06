# MUSCAL CORE — SESSION_REGISTRY

**Zweck:** Statusinformation über Sessions — keine autoriative Quelle.
**Priorität der Wahrheit:** 1. Git History → 2. CHANGE_JOURNAL → 3. ADR Records → 4. SESSION_HANDOVER → 5. SESSION_REGISTRY

---

## Letzte Sessions

| Session ID | Datum | Status | Geänderte Dateien | Kategorie |
|------------|-------|--------|-------------------|-----------|
| S-2026-07-11-001 | 2026-07-11 | ABGESCHLOSSEN | 457 | Initial Baseline |
| S-2026-07-11-002 | 2026-07-11 | ABGESCHLOSSEN | 8 | Multi-Session Governance |
| S-2026-07-12-001 | 2026-07-12 | ABGESCHLOSSEN | 14 | Checkpoint 0.25 — Reconciliation Execution |
| S-2026-07-12-002 | 2026-07-12 | ABGESCHLOSSEN | 17 | Checkpoint 0.26 — Reconciliation Engine Foundation |
| S-2026-07-12-003 | 2026-07-12 | ABGESCHLOSSEN | 5 | Checkpoint 0.27 — Category B Reconciliation |
| S-2026-07-12-004 | 2026-07-12 | ABGESCHLOSSEN | 5 | Checkpoint 0.28 — Repository Cleanup |
| S-2026-07-12-005 | 2026-07-12 | ABGESCHLOSSEN | 11 | Governance Enforcement v1.1 |
| S-2026-07-12-006 | 2026-07-12 | AKTUELL | 10 | Checkpoint 0.29.1 — Reconciliation Runtime Kernel |
| S-2026-07-12-006 | 2026-07-13 | ABGESCHLOSSEN | 10 | Evidence & Reconciliation v1.2 |
| S-2026-07-14-001 | 2026-07-14 | ABGESCHLOSSEN | 6 | Checkpoint 0.30 — ScanContext Migration & Snapshot Integration |
| S-2026-07-14-002 | 2026-07-14 | ABGESCHLOSSEN | 5 | Checkpoint 0.31 — Rule Engine Implementation |
| S-2026-07-14-003 | 2026-07-14 | ABGESCHLOSSEN | 2 | Checkpoint 0.32 — BrokenLinkScanner Implementation |
| S-2026-07-15-001 | 2026-07-15 | ABGESCHLOSSEN | 2 | Checkpoint 0.33 — ADR Validator Scanner |
| S-2026-07-20-001 | 2026-07-20 | ABGESCHLOSSEN | 1 | HDR-001 Decision Readiness Audit |
| S-2026-07-27-001 | 2026-07-27 | ABGESCHLOSSEN | 15 | MC-TC-004 Pre-Gate (Phases 4-10) + Implementation (S-01..S-04) |
| S-2026-07-28-001 | 2026-07-28 | ABGESCHLOSSEN | 1 | MC-TC-007 Status Zusammenfassung |
| S-2026-07-30-001 | 2026-07-30 | ABGESCHLOSSEN | 10 | MC-TC-004 Certification + ARB Decision |
| S-2026-07-31-001 | 2026-07-31 | ABGESCHLOSSEN | — | MC-TC-007 Reality Closure (CONDITIONAL GO) |
| S-2026-08-04-001 | 2026-08-04 | ABGESCHLOSSEN | 15 | Browser Intelligence Feature (features/browser_intelligence) |

**Hinweis (2026-08-01):** Duplikat `docs/governance/SESSION_REGISTRY.md` (MSCE-Format-Entwurf, Stand 15.07, nie committet) als superseded entfernt — kanonisch bleibt dieses Dokument.

**Hinweis (Phase B, PB-01, 2026-08-01):** Handover-Backfill abgeschlossen:
`HANDOVER_S-2026-07-28-001.md`, `HANDOVER_S-2026-07-30-001.md`,
`HANDOVER_S-2026-07-31-001.md` erstellt (evidenzbasiert aus Audit-Artefakten;
S-2026-07-31-001 = Registry-only, Detailinhalt UNKNOWN).

---

## Session-Status Definitionen

| Status | Beschreibung |
|--------|--------------|
| AKTUELL | Session aktiv |
| ABGESCHLOSSEN | Commit erstellt, Handover vorhanden |
| BLOCKIERT | Warte auf Freigabe |
| ABGEBROCHEN | Abgebrochen ohne Commit |

---

## Hinweis

Dieses Dokument dient ausschließlich der Übersicht.
Bei Widersprüchen gilt immer die Git History.
