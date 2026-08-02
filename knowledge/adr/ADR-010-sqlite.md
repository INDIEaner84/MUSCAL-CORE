# ADR-010: SQLite Consolidation — Unified Single Database

**Status:** PROPOSED  
**Date:** 2026-07-10  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 hat **3 aktive SQLite-Datenbanken** + 1 JSONL-Audit-File:

| DB | Path | Tables | Owner | Nutzer |
|----|------|--------|-------|--------|
| **memory.db** | `storage/memory.db` | `memory`, `mcxf_store` (2) | `memory.py` | Kernel, Pipeline |
| **muscal.db** | `storage/muscal.db` | `events`, `workers`, `tasks`, `decisions`, `snapshots`, `intent_documents`, `intent_unknowns`, `routing_policy`, `kernel_config`, `trigger_state`, `sequences` (11) | `runtime/database.py` | Runtime API, Worker, Observer |
| **mcxf.db** | CWD (`mcxf.db`) | `mcxf` (1) | `mcxf_sql.py` | Dashboard (legacy) |
| **logs.jsonl** | `storage/logs.jsonl` | — (JSONL append-only) | `memory.log_jsonl()` | Audit Trail |

### Probleme

1. **Drei separate DBs** — keine einheitliche Backup-/Snapshot-Strategie
2. **memory.db Pfad hardcoded** — `memory.py` nutzt `"storage/memory.db"` direkt, ignoriert `os_config.memory_db`
3. **Keine Transaktionskonsistenz** — `muscal.db` und `memory.db` können inkonsistent sein (z.B. Event geloggt aber MCXF-Snapshot fehlt)
4. **JSONL vs SQLite** — Audit-Trail in JSONL, nicht in DB; kein integrierter Replay-Schutz
5. **mcxf.db** — Dashboard-only; wird nie von der Pipeline genutzt
6. **Kein Schema-Versioning** — keine Migrationen, keine rollback-fähigen Änderungen

### Daten-Overlap

Die DBs speichern **disjunkte Daten** (kein Overlap):

| Daten | memory.db | muscal.db |
|-------|-----------|-----------|
| MCXF-Snapshots (input, mcxf, result, feedback) | ✅ `mcxf_store` | ❌ |
| Plan/Result-Paare | ✅ `memory` | ❌ |
| Audit-Logs (JSONL) | ✅ `logs.jsonl` | ❌ |
| CQRS Event-Log | ❌ | ✅ `events` |
| Worker/Task/Decision Tracking | ❌ | ✅ `workers`, `tasks`, `decisions` |
| Kernel-Config/Snapshots | ❌ | ✅ `kernel_config`, `snapshots` |
| Routing-Policy | ❌ | ✅ `routing_policy` |
| Sequences/Trigger-State | ❌ | ✅ `sequences`, `trigger_state` |

---

## Decision

### Unified Database: `muscal.db` wird die einzige SQLite-Datenbank

```
Vorher:                        Nachher:
memory.db  muscal.db  mcxf.db  →  muscal.db (unified)
   │           │         │             │
   │           │         │       ┌─────┴──────┐
   │           │         │       events       mcxf_snapshots
   │           │         │       workers      audit_log
   │           │         │       tasks        kernel_config
   │           │         │       decisions    sequences
   │           │         │       snapshots    trigger_state
   │           │         │       intent_*     routing_policy
```

### Schema-Änderungen

**Neue Tabellen in `muscal.db`:**

```sql
CREATE TABLE IF NOT EXISTS mcxf_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT,
    mcxf_json TEXT,
    result_json TEXT,
    feedback_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);
```

### API-Änderungen

`memory.py` wird umgestellt von `sqlite3.connect("storage/memory.db")` auf
Nutzung von `runtime.database.get_connection(config.DB_PATH)`:

```python
# Vorher (hardcoded):
_conn = sqlite3.connect("storage/memory.db", ...)

# Nachher (über config):
from config import DB_PATH
_conn = get_connection(DB_PATH)
```

Die Funktionen `store()`, `store_snapshot()`, `retrieve_by_id()`,
`search_by_keyword()`, `get_recent()` bleiben API-kompatibel, schreiben aber
in `muscal.db.mcxf_snapshots` statt `memory.db.mcxf_store`.

### Eviction-Policy

Die bestehende FIFO-Eviction (10K Einträge in `memory.py`) wird auf
`mcxf_snapshots` übertragen. `audit_log` bekommt eine 7-Tage-Retention.

---

## Migration Plan

### Phase 1: Schema vorbereiten (v0.8)

- [ ] `runtime/database.py`: `init_db()` erstellt neue Tabellen `mcxf_snapshots`, `audit_log`, `schema_version`
- [ ] `schema_version` auf `1` setzen

### Phase 2: Migration Script

- [ ] `scripts/migrate_sqlite.py` — Einmal-Migration:
  1. Liest alle rows aus `memory.db.mcxf_store`
  2. Schreibt sie in `muscal.db.mcxf_snapshots`
  3. Liest `storage/logs.jsonl` und schreibt in `muscal.db.audit_log`
  4. Setzt `schema_version` auf `2`
  5. Optional: löscht `memory.db` und `logs.jsonl`

### Phase 3: memory.py umstellen

- [ ] `memory.py` nutzt `runtime.database.get_connection(config.DB_PATH)` statt `sqlite3.connect("storage/memory.db")`
- [ ] Alle Queries auf `mcxf_snapshots`-Table umgestellt
- [ ] `memory.log()` schreibt in `audit_log` statt `logs.jsonl`
- [ ] `MAX_MEMORY_ENTRIES` = 10000 bleibt, aber in `mcxf_snapshots`
- [ ] Alte `memory`-Table (`plan`/`result`-Paare) weglassen (wird nicht mehr von der Pipeline genutzt)

### Phase 4: Cleanup

- [ ] `os_config.memory_db` als DEPRECATED markieren
- [ ] `mcxf_sql.py` als DEPRECATED markieren (Dashboard kann muscal.db direkt lesen)
- [ ] `entrypoint.sh` aktualisieren: initialisiert nur `muscal.db`, nicht mehr `memory.db`

---

## Consequences

### Positive
- Einheitliche Backup-/Restore-Strategie: `storage/muscal.db` sichern reicht
- Transaktionale Konsistenz zwischen MCXF-Snapshots und Runtime-Events möglich
- Weniger File-Descriptoren (3 DB-Connections → 1)
- Schema-Versioning erlaubt zukünftige Migrationen
- Audit-Trail in SQLite (abfragbar, indexierbar) statt rohem JSONL

### Negative
- `muscal.db` wird größer (alle Daten in einer Datei)
- Migration erfordert Koordination mit Deployment
- `memory.py` ist ein Core-File — Änderung braucht OVERRIDE
- Dashboard (`mcxf_sql.py`) muss auf `muscal.db` umgestellt werden

---

## Compliance Check

- [x] Schema-Versioning implementiert (`schema_version`-Table)
- [x] `memory.py` nutzt `runtime.database.get_connection()`
- [x] `memory.log_jsonl()` schreibt in `audit_log` statt JSONL
- [x] Migration Script erstellt (`scripts/migrate_sqlite.py`)
- [ ] Migration Script getestet (braucht alte memory.db)
- [ ] Alle Tests passieren nach Migration
- [x] `os_config.memory_db` als DEPRECATED markiert
- [x] `mcxf_sql.py` als DEPRECATED markiert
