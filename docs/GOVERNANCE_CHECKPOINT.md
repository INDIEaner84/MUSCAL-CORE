# MUSCAL CORE — GOVERNANCE_CHECKPOINT

**Letzte Aktualisierung:** 2026-07-20
**Erstellt von:** Multi-Session Governance Plan

---

## 1. Aktueller Governance Status

| Komponente | Status |
|------------|--------|
| Core Immutability | ✅ AKTIV |
| Write Guard | ✅ AKTIV |
| Session Rules | ✅ ERWEITERT |
| Task Board | ✅ ERSTELLT |
| Lock Protocol | ✅ ERSTELLT |
| Session Registry | ✅ ERSTELLT |
| Governance Checkpoint | ✅ ERSTELLT |

---

## 2. Aktive Regeln

### Core Immutability
- 35 Core-Dateien sind IMMUTABLE
- 8 Core-Verzeichnisse sind IMMUTABLE
- Ausnahmen nur mit `--allow-core-write` Flag + OVERRIDE.md

### Lock Protocol
- **Level 0:** Documentation Lock — Keine Approval
- **Level 1:** Feature Lock — Review erforderlich
- **Level 2:** Shared Infrastructure Lock — Architecture Review
- **Level 3:** Core Lock — ADR + Architecture Review + Freigabe

### Session Rules
- SESSION_HANDOVER ist PFLICHT bei Dateiänderungen
- SESSION_REGISTRY ist Statusinformation (nicht autoriativ)
- Priorität der Wahrheit: Git History > CHANGE_JOURNAL > ADR > HANDOVER > REGISTRY

---

## 3. Session Lifecycle

```
Session Start
    ↓
PROJECT_STATE.md lesen
    ↓
 TASK_BOARD.md prüfen
    ↓
Lock Level bestimmen
    ↓
Approval einholen (falls nötig)
    ↓
Änderungen durchführen
    ↓
git diff kontrollieren
    ↓
SESSION_HANDOVER erstellen
    ↓
SESSION_REGISTRY aktualisieren
    ↓
TASK_BOARD aktualisieren
    ↓
Git Commit
    ↓
Session Ende
```

---

## 4. Lock-Level Übersicht

| Level | Name | Bereich | Approval | ADR |
|-------|------|---------|----------|-----|
| 0 | Documentation Lock | *.md, docs/*, spec/*.md | Keine | Nein |
| 1 | Feature Lock | features/* | Review | Nein |
| 2 | Shared Infrastructure Lock | guards/*, runtime/monitoring/*, runtime/services/*, .github/* | Architecture Review | Optional |
| 3 | Core Lock | kernel.py, memory.py, etc. | ADR + Review + Freigabe | Ja |

---

## 5. Approval Flow

```
Aufgabe definieren
    ↓
Architecture Impact bestimmen
    ↓
Required Approval prüfen
    ↓
┌─────────────────────────────────────┐
│ Level 0: Kein Approval nötig       │
│ Level 1: Code Review               │
│ Level 2: Architecture Review       │
│ Level 3: ADR + Architecture Review │
└─────────────────────────────────────┘
    ↓
Approval dokumentieren
    ↓
Implementierung
```

---

## 6. Änderungsverfolgung

| Datum | Änderung | Session ID | Commit |
|-------|----------|------------|--------|
| 2026-07-20 | HDR-001 Decision Readiness Audit abgeschlossen | S-2026-07-20-001 | — |
| 2026-07-11 | Governance Layer erstellt | S-2026-07-11-002 | — |
| 2026-07-11 | Initial Baseline | S-2026-07-11-001 | 708dddb |

---

## 7. Nächste Governance Evolution Steps

| # | Schritt | Priorität | Status |
|---|---------|-----------|--------|
| 1 | Pre-Commit Hook installieren | Hoch | OPEN |
| 2 | CHANGE_JOURNAL.md einführen | Mittel | OPEN |
| 3 | Governance CI/CD Pipeline | Niedrig | OPEN |
| 4 | Automated Compliance Checks | Niedrig | OPEN |

---

## 8. Verwandte Dokumente

| Dokument | Pfad | Zweck |
|----------|------|-------|
| SESSION_RULES | `.opencode/SESSION_RULES.md` | Session-Regeln |
| TASK_BOARD | `docs/TASK_BOARD.md` | Aufgaben-Tracking |
| LOCK_PROTOCOL | `docs/LOCK_PROTOCOL.md` | Lock-Level Definition |
| SESSION_REGISTRY | `docs/SESSION_REGISTRY.md` | Session-Übersicht |
| IMMUTABILITY_CONTRACT | `spec/IMMUTABILITY_CONTRACT.md` | Core Immutability |
| WRITE_GUARD | `guards/write_guard.py` | Technische Durchsetzung |
