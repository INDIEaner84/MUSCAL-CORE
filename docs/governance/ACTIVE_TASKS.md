# MUSCAL CORE — ACTIVE TASKS (MSCE)

**Zweck:** Aufgaben für die aktuelle Session. Wird bei Session-Start befüllt und bei Session-Ende geleert.
**Regel:** Nur eine Session ist aktiv. ACTIVE_TASKS ist der Working Set.

---

## Schema

| Task ID | Description | Status | Lock Level | Est. Impact | Notes |
|---------|-------------|--------|------------|-------------|-------|

---

## Status Definitionen

| Status | Beschreibung |
|--------|--------------|
| PENDING | Noch nicht begonnen |
| IN_PROGRESS | Aktiv in Arbeit |
| DONE | In dieser Session abgeschlossen |
| BLOCKED | Kann nicht fortfahren (Abhängigkeit) |
| DEFERRED | An WORK_QUEUE übergeben |

---

## Active Tasks

| Task ID | Description | Status | Lock Level | Est. Impact | Notes |
|---------|-------------|--------|------------|-------------|-------|
| HDR-001-DRA | HDR-001 Decision Readiness Audit | DONE | 0 | Global | Audit complete, awaiting human decision |
| CHECKPOINT-0.40 | Runner Integration Tests | PENDING | 1 | Local | Nächster Checkpoint laut Baseline v1.0 |
