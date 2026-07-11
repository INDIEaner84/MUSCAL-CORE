# MUSCAL CORE — OpenCode Governance Rules

## WICHTIG: Session-Regeln migriert

Die vollständigen Session-Regeln befinden sich jetzt in:
→ `.opencode/SESSION_RULES.md`

Diese Datei (`AGENTS.md`) wird nach der nächsten Migration
durch `.opencode/SESSION_RULES.md` ersetzt.

Bitte lesen Sie zuerst `docs/PROJECT_STATE.md`.

---

## CORE IS READ-ONLY

Diese Dateien sind IMMUTABLE und dürfen NICHT verändert werden:

kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py, mkc_rules.py,
config.py, event_bus.py, graph.py, feedback.py, muscal_os.py, main.py,
main_boot.py, boot_manager.py, os_config.py, sphere.py, debugger.py,
tools.py, rag.py, trace_engine.py, plugin_registry.py, plugin_loader.py

runtime/kernel/*, runtime/llm/*, runtime/optimizer/*, runtime/api/*, runtime/services/*

## ALL EXTENSIONS GO TO /features/

Jedes neue Feature MUSS als Plugin in `features/` implementiert werden.

## PLUGIN CONTRACT

```python
class Plugin:
    name: str
    def register(self, hooks: dict): ...
    def execute(self, context: dict): ...
```

## PRE-WRITE CHECK

Vor jedem Datei-Schreibzugriff MUSS `guards.write_guard.validate_write(path)`
geprüft werden.

## VIOLATION

Wenn eine Aufgabe Core-Änderung erfordert:

1. STOP — nicht ausführen
2. Als ARCHITECTURE CHANGE klassifizieren
3. In spec/OVERRIDE.md dokumentieren
4. Nur mit `--allow-core-write` Flag ausführen
