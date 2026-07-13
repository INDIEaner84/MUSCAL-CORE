# MUSCAL CORE — CHANGE_JOURNAL

**Zweck:** Human-readable Change Log — fachliche Interpretation der Git History.
**Regel:** Git History + CHANGE_JOURNAL sind Quelle abgeschlossener Änderungen.
SESSION_REGISTRY ist Statusinformation, nicht absolute Wahrheit.

---

## Integrity Rule

Die Autoritätshierarchie lautet:

1. **Git History** — technische Wahrheit
2. **CHANGE_JOURNAL** — fachliche Interpretation
3. **SESSION_REGISTRY** — aktueller Status

---

## Journal

| Datum | Change ID | Session ID | Commit | Kategorie | Beschreibung |
|-------|-----------|------------|--------|-----------|--------------|
| 2026-07-11 | C-001 | S-2026-07-11-001 | 708dddb | Initial Baseline | 457 Dateien, 45.208 Zeilen, v0.7 |
| 2026-07-12 | C-003 | S-2026-07-12-005 | eb3f851 | Governance | Governance Enforcement Layer v1.1 — Validator + Pre-Commit + CI |
| 2026-07-13 | C-004 | S-2026-07-12-006 | 34a99e3 | Governance | Evidence & Reconciliation Layer v1.2 |

---

## Kategorien

| Kategorie | Beschreibung | Lock Level |
|-----------|--------------|------------|
| Initial Baseline | Erstcommit | — |
| Governance | Governance Layer Änderungen | 0 |
| Core | Core-Komponenten | 3 |
| Feature | Plugin/Feature-Entwicklung | 1 |
| Infrastructure | CI/CD, Guards | 2 |
| Documentation | Nur Dokumentation | 0 |
