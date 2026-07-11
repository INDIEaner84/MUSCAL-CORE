# MUSCAL CORE — IMMUTABILITY CONTRACT

**Version:** 1.0
**Gültig ab:** v0.7

---

## 1. PURPOSE

Dieser Vertrag definiert die Grenzen zwischen **Core** (immutable) und **Features** (plugin-basiert).
Jede Verletzung wird durch `guards/write_guard.py` technisch erzwungen.

---

## 2. CORE (IMMUTABLE)

Die folgenden Dateien und Verzeichnisse dürfen NACH der einmaligen Hook-Injection
(v0.7 → v1.0) NICHT MEHR verändert werden:

### Root-Dateien

```
api_server.py
boot_manager.py  Boot-Phasen
bridge.py  Tool-Mapping
chat_compiler.py
cognitive_diff.py  Diff-Engine
compiler_state.py
compiler_updater.py
compiler_validator.py
compiler_version.py
config.py  Konfiguration
dashboard.py
debugger.py  Debug-Engine
event_bus.py  Event-System
feedback.py  Feedback-Analyse
graph.py  Graph-State
kernel.py  Hauptorchestrator — letzte Änderung: Hook-Injection
kernel_diff_engine.py
loop_controller.py
main.py  Simple Entrypoint — letzte Änderung: Plugin-Loading
main_boot.py  OS Entrypoint
mel.py  Execution Layer
memory.py  Persistenz (SQLite + JSONL)
mkc.py  Compiler
mkc_rules.py  Compiler-Regeln
muscal_loop.py  Autonomer Loop
muscal_os.py  OS-Lifecycle — letzte Änderung: Plugin-Loading
os_config.py  OS-Konfiguration
plugin_loader.py  NEU: Plugin-Discovery
plugin_registry.py  NEU: Hook-Registry
rag.py  RAG-Abfrage
schema.py  Datentypen (KernelResult, MCXFDocument, ...)
sphere.py  Sphere-State
system_runtime.py
tools.py  Tool-Registry
trace_engine.py  Tracing
```


### Runtime-Verzeichnisse

```
guards/
runtime/api/  API-Routen
runtime/kernel/  WriterThread, Scheduler, Gate, Governance
runtime/llm/  LLM-Client
runtime/observation/  Watchdog
runtime/optimizer/  Optimizer-Pipeline
runtime/services/  Snapshot, Handoff
spec/
```


---

## 3. FEATURES (PLUGIN-ZONE)

Alle Erweiterungen GEHÖREN nach `/features/`.

### Erlaubte Aktionen

- Neue Plugins in `features/*/` erstellen
- Context lesen (input_text, mcxf, result)
- Metadata anreichern
- Logs schreiben
- Output transformieren (lesend)

### Verbotene Aktionen

- Core-Dateien verändern
- Direkter `sqlite3.connect` auf memory.db
- Globalen State mutieren
- Kernel-Executionsfluss ändern
- Core-Imports in Plugin-Code (Plugins importieren NIE core)

---

## 4. PLUGIN-CONTRACT

Jedes Plugin MUSS implementieren:

```python
class Plugin:
    name: str
    def register(self, hooks: dict): ...
    def execute(self, context: dict): ...
```

- `register()` wird genau einmal beim Boot aufgerufen
- `execute()` wird bei jedem Pipeline-Durchlauf gerufen
- Plugins dürfen keine Exceptions werfen (werden gekapselt)

---

## 5. VIOLATION HANDLING

| Verletzung | Reaktion |
|-----------|----------|
| Write auf Core-Datei | `write_guard.py` wirft `PermissionError` |
| Plugin importiert Core-Modul | `validate_plugin()` blockt |
| Plugin schreibt `global` | `validate_plugin()` blockt |
| Plugin ruft `sqlite3.connect` | `validate_plugin()` blockt |

---

## 6. AUSNAHMEN

Ausnahmen zu diesem Vertrag erfordern:

1. Eintrag in `spec/OVERRIDE.md` (Begründung)
2. Explizite Freigabe durch `--allow-core-write` Flag
3. Core-Änderung wird als separater Commit deklariert
