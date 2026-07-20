# MUSCAL CORE — WORK QUEUE (MSCE)

**Zweck:** Persistenter Backlog von Aufgaben über Sessions hinweg.
**Regel:** Items werden aus ACTIVE_TASKS übergeben oder manuell hinzugefügt. Items werden von ACTIVE_TASKS aufgenommen.
**Hinweis:** Für cross-projektische offene Punkte (Wissenslücken, Architektur-Konflikte) siehe `MUSCAL_KNOWLEDGE_SYSTEM/07_PENDING_REVIEW/PENDING_ITEMS.yaml`.

---

## Schema

| Queue ID | Task ID | Description | Priority | Added | Status | Blocked By |
|----------|---------|-------------|----------|-------|--------|------------|

---

## Priority Definitionen

| Priority | Beschreibung |
|----------|--------------|
| CRITICAL | Muss vor nächstem Meilenstein erledigt werden |
| HIGH | Sollte bald erledigt werden |
| MEDIUM | Normalpriorität |
| LOW | Wenn bequem |
| DEFERRED | Explizit verschoben |

---

## Status Definitionen

| Status | Beschreibung |
|--------|--------------|
| QUEUED | Wartet auf Aufnahme |
| IN_PROGRESS | Jemand arbeitet daran (in ACTIVE_TASKS) |
| BLOCKED | Kann nicht starten (Abhängigkeit) |
| DONE | Abgeschlossen |
| CANCELLED | Nicht mehr benötigt |

---

## Work Queue

| Queue ID | Task ID | Description | Priority | Added | Status | Blocked By |
|----------|---------|-------------|----------|-------|--------|------------|
| WQ-000 | HDR-001-DECISION | Human Operator decides on HDR-001 questions | CRITICAL | 2026-07-20 | QUEUED | — |
| WQ-001 | CHECKPOINT-0.40 | Runner Integration Tests | HIGH | 2026-07-15 | QUEUED | — |
| WQ-002 | CHECKPOINT-0.41 | Import Finding Optimization | MEDIUM | 2026-07-15 | QUEUED | — |
| WQ-003 | CHECKPOINT-0.42 | CI/CD Integration | MEDIUM | 2026-07-15 | QUEUED | — |
| WQ-004 | CHECKPOINT-0.43 | Config-driven Scanner Registry | LOW | 2026-07-15 | QUEUED | — |
