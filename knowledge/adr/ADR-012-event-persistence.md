# ADR-012: Event Persistence — Audit Log + Replay

**Status:** APPLIED  
**Date:** 2026-07-11  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.8 hat ein funktionierendes Event-System (ADR-003, APPLIED) mit:

- `EventBus` — In-Memory-Event-Bus mit `_history` (max 50.000 Einträge)
- `EventMessage` — Standardisiertes Event-Format mit Topic, Payload, Source
- `audit_log`-Tabelle in `muscal.db` (ADR-010, APPLIED)

### Problem

**Events gehen bei Neustart verloren.** Der `EventBus._history` ist flüchtig:

- OS-Lifecycle-Events (`boot.init`, `kernel.initialized`, etc.) sind nach Neustart nicht mehr sichtbar
- Pipeline-Events (`os.executed`, `graph.*`) sind nicht über Sitzungen hinweg nachvollziehbar
- Kein Replay: Events können nicht erneut abgespielt werden
- `audit_log`-Tabelle existiert, wird aber nur von `memory.log_jsonl()` beschrieben — nicht vom EventBus

### Bestehende Infrastruktur

```text
muscal.db
  └── audit_log (id, entry_type, payload, created_at)
  └── schema_version (version, applied_at, description)
```

Die `audit_log`-Tabelle hat das benötigte Schema für Event-Persistence.

---

## Decision

### 1. Event-Persistence via EventBus-Listener

Ein neuer Listener (`EventPersistencePlugin`) subscribed auf `"*"` (alle Events) und schreibt jedes Event in die `audit_log`-Tabelle:

```python
# Pseudocode
bus.subscribe("*", persist_to_audit_log)

def persist_to_audit_log(msg: EventMessage):
    conn.execute("INSERT INTO audit_log (entry_type, payload) VALUES (?, ?)",
                 [msg.topic, json.dumps(msg.payload)])
```

### 2. Replay-Funktion

`EventBus` erhält eine `replay_from_db(db_path, topic_filter=None)`-Methode:

```python
bus.replay_from_db(muscal_db_path)  # → published alle audit_log-Einträge via bus.publish()
```

- Replay-Events erhalten `payload._replayed = True` zur Unterscheidung
- Optionaler `topic_filter` erlaubt selektives Replay

### 3. Retention-Konfiguration

Automatisches Pruning alter Events via `EVENT_RETENTION_DAYS` (Default: 30):

- Bei Plugin-Start: DELETE FROM audit_log WHERE created_at < datetime('now', '-N days')
- Konfigurierbar über `MUSCAL_EVENT_RETENTION_DAYS`-Env-Var

### 4. Plugin-Architektur

Das Event-Persistence wird als Plugin in `features/observability/event_persistence.py` implementiert:

- Plugin empfängt EventBus via `HOOKS["_event_bus"]`-Injection
- Bei `register()`: subscribed auf alle Topics
- Bei jedem Event: INSERT in `audit_log`
- Bei Plugin-Ladung: Pruning alter Events

---

## Migration Plan

### Phase 1: ADR-012 + OVERRIDE (v0.8)

- [x] `spec/ADR-012-event-persistence.md` — dieses Dokument
- [ ] `spec/OVERRIDE.md` — Core-Änderungen dokumentieren
- [ ] `plugin_registry.py` — `EVENT_BUS = None` hinzufügen
- [ ] `plugin_loader.py` — `HOOKS["_event_bus"]` injizieren
- [ ] `muscal_os.py` — `plugin_registry.EVENT_BUS = self.events` nach Plugin-Load setzen
- [ ] `event_bus.py` — `replay_from_db()` hinzufügen
- [ ] `config.py` — `EVENT_RETENTION_DAYS` hinzufügen

### Phase 2: Plugin (v0.8)

- [ ] `features/observability/event_persistence.py` — EventPersistencePlugin
- [ ] Plugin subscribed auf EventBus, schreibt in audit_log

### Phase 3: Tests (v0.8)

- [ ] `tests/system/test_event_persistence.py` — Persist, Replay, Retention

---

## Consequences

### Positive
- Events persistieren über Neustarts hinweg
- Audit-Trail vollständig in SQLite (abfragbar, indexierbar)
- Replay ermöglicht Wiederherstellung nach Crash
- Retention verhindert unbegrenztes DB-Wachstum
- Plugin-Architektur: kein Core-Change für Persistenz-Logik

### Negative
- Zusätzlicher DB-Write pro Event (~500 Byte pro Event bei typischer Payload)
- 30 Tage Retention bei 100 Events/s = ~130 GB (in Praxis < 1 MB/s)
- OVERRIDE nötig für 4 Core-Files (minimale, additive Änderungen)

---

## Compliance Check

- [ ] ADR-011 dokumentiert
- [ ] OVERRIDE dokumentiert
- [ ] EventPersistencePlugin subscribed auf EventBus
- [ ] Events werden in audit_log persistiert
- [ ] Replay via `EventBus.replay_from_db()`
- [ ] Retention via `EVENT_RETENTION_DAYS`
- [ ] Alle Tests passieren
