# MUSCAL CORE — LOCK_PROTOCOL

**Zweck:** Definition der Lock-Level für Änderungen am Codebase.
**Regel:** Jede Änderung muss dem passenden Lock-Level entsprechen.

---

## Lock-Level Übersicht

| Level | Name | Beschreibung | Approval | ADR |
|-------|------|--------------|----------|-----|
| 0 | Documentation Lock | Nur Dokumentationsänderungen | Keine erforderlich | Nein |
| 1 | Feature Lock | Neue Features innerhalb bestehender Grenzen | Review erforderlich | Nein |
| 2 | Shared Infrastructure Lock | Änderungen an gemeinsam genutzten Komponenten | Architecture Review | Optional |
| 3 | Core Lock | Änderungen an Core-Komponenten | ADR + Architecture Review + Explizite Freigabe | Ja |

---

## Level 0 — Documentation Lock

**Bereich:** `*.md`, `docs/*`, `spec/*.md`, `.opencode/*`

**Beispiele:**
- README.md aktualisieren
- SESSION_REGISTRY.md pflegen
- ADR dokumentieren
- Task Board führen

**Approval:** Keine erforderlich.
**Voraussetzung:** Keine.

---

## Level 1 — Feature Lock

**Bereich:** `features/*`

**Beispiele:**
- Neues Plugin in `features/mkc/` erstellen
- Feature in `features/bridge/` erweitern
- Test in `tests/` hinzufügen

**Approval:** Code Review durch Kollege erforderlich.
**Voraussetzung:** Plugin-Contract muss eingehalten werden.

---

## Level 2 — Shared Infrastructure Lock

**Bereich:** `guards/*`, `runtime/monitoring/*`, `runtime/services/*`, `.github/*`

**Beispiele:**
- Governance-Script in `guards/` ändern
- CI/CD Pipeline anpassen
- Monitoring-Plugin erstellen

**Approval:** Architecture Review erforderlich.
**Voraussetzung:** Auswirkungen auf gemeinsame Komponenten müssen dokumentiert werden.

---

## Level 3 — Core Lock

**Bereich:** `kernel.py`, `memory.py`, `mkc.py`, `bridge.py`, `schema.py`, `config.py`, `event_bus.py`, `graph.py`, `runtime/kernel/*`, `runtime/llm/*`, `runtime/optimizer/*`, `runtime/api/*`

**Beispiele:**
- Kernel-Pipeline ändern
- Memory-Management ändern
- Event-System erweitern

**Approval:**
1. ADR erstellen (spec/ADR-XXX-*.md)
2. Architecture Review
3. Explizite Freigabe VOR Merge

**Voraussetzung:**
- ADR muss `ACCEPTED` sein
- `--allow-core-write` Flag muss gesetzt sein
- Core-Änderung muss als separater Commit deklariert werden

---

## Verstöße

| Verstoß | Reaktion |
|---------|----------|
| Level 0 auf Level 1 | STOP — Review einholen |
| Level 1 auf Level 2 | STOP — Architecture Review einholen |
| Level 2 auf Level 3 | STOP — ADR + Freigabe einholen |
| Level 3 ohne ADR | STOP — ADR erstellen |
| Core-Write ohne Flag | `write_guard.py` blockt |

---

## Exception Handling

Ausnahmen zu diesem Protocol erfordern:

1. Eintrag in `spec/OVERRIDE.md` (Begründung)
2. Explizite Freigabe durch verantwortliche Person
3. Dokumentation in SESSION_HANDOVER
