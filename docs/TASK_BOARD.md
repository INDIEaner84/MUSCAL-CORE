# MUSCAL CORE — TASK_BOARD

**Zweck:** Tracking aller Aufgaben mit Architektur-Impact und Approval-Pflicht.
**Regel:** Jede neue Aufgabe MUSS die Pflichtfelder enthalten.

---

## Pflichtfelder pro Aufgabe

| Feld | Beschreibung |
|------|--------------|
| Task ID | Eindeutige Identifikation |
| Beschreibung | Was soll gemacht werden |
| Status | OPEN / IN_PROGRESS / BLOCKED / DONE |
| Architecture Impact | None / Local / Shared / Core |
| Required Approval | Keine / Review / Architecture Review / Core Approval |
| ADR Requirement | Kein ADR / ADR erforderlich |
| Lock Level | 0 / 1 / 2 / 3 |
| Zugewiesen an | Verantwortlich |

---

## Offene Aufgaben

| Task ID | Beschreibung | Status | Architecture Impact | Required Approval | ADR Requirement | Lock Level |
|---------|--------------|--------|---------------------|-------------------|-----------------|------------|
| T-001 | Governance Layer implementieren | DONE | Local | Keine | Kein ADR | 0 |
| T-002 | Pre-Commit Hook installieren | OPEN | None | Keine | Kein ADR | 0 |
| T-003 | Confidence Guard Auto-Reset | OPEN | Shared | Review | ADR erforderlich | 2 |
| T-004 | FIFO-Eviction Verbesserung | OPEN | Local | Keine | Kein ADR | 1 |
| T-005 | CHANGE_JOURNAL.md einführen | OPEN | Local | Keine | Kein ADR | 1 |
| T-006 | Governance CI/CD Pipeline | OPEN | Shared | Review | Kein ADR | 1 |
| T-007 | Automated Compliance Checks | OPEN | Shared | Review | Kein ADR | 1 |
| T-008 | Reconciliation Engine — Scanner implementation | OPEN | Local | Keine | Kein ADR | 1 |
| T-009 | Reconciliation Engine — Pre-Commit hook | OPEN | None | Keine | Kein ADR | 0 |
| T-010 | Reconciliation Engine — CI/CD integration | OPEN | Shared | Review | Kein ADR | 1 |
| T-011 | Governance Enforcement Layer v1.1 | OPEN | Shared | Architecture Review | Kein ADR | 2 |

**Betroffene Dateien:** guards/governance_validator.py, guards/pre_commit_hook.py, .github/workflows/governance-check.yml, .pre-commit-config.yaml

---

## Abgeschlossene Aufgaben

| Task ID | Beschreibung | Datum | Commit |
|---------|--------------|-------|--------|
| T-001 | Governance Layer (DOC-01 Audit) | 2026-07-11 | 708dddb |

---

## Architecture Impact Definitionen

| Level | Beschreibung | Beispiel |
|-------|--------------|----------|
| None | Keine Auswirkung | README.md, .gitignore |
| Local | Änderung in einem Feature | features/mkc/audit_plugin.py |
| Shared | Änderung an gemeinsamer Komponente | guards/*.py, docs/*.md |
| Core | Änderung an Core-Komponente | kernel.py, memory.py |

---

## Required Approval Definitionen

| Level | Beschreibung | Wer |
|-------|--------------|-----|
| Keine | Kein Review nötig | Jeder |
| Review | Code Review durch Kollege | Team Member |
| Architecture Review | Architektur-Review | Architect |
| Core Approval | Explizite Freigabe | Core Team + ADR |

---

## ADR Requirement Definitionen

| Level | Beschreibung |
|-------|--------------|
| Kein ADR | Kein Architecture Decision Record nötig |
| ADR erforderlich | ADR muss erstellt werden VOR Implementierung |
