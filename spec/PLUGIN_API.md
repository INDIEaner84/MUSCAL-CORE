# MUSCAL CORE — Plugin SDK

**Version:** 1.1
**Gültig ab:** MUSCAL CORE v0.8

---

## 1. Plugin Interface (Der Contract)

Jedes Plugin MUSS eine `Plugin`-Klasse mit folgendem Interface exportieren:

```python
class Plugin:
    name: str = "my_plugin"
    version: str = "0.1.0"       # Seit v1.1: Semantische Version

    def register(self, hooks: dict):
        """Called once at system startup.
        Use to attach handlers to hooks.
        """

    def execute(self, context: dict):
        """Called during runtime when triggered.
        Must NOT mutate core state.
        """
```

### 1.1 `name`
Eindeutiger Plugin-Name. Wird für Logging, Health-Monitoring und Fehlermeldungen verwendet.

### 1.2 `version` (seit v1.1)
Semantische Version des Plugins. Wird beim Laden geloggt und kann von anderen Tools ausgelesen werden.

### 1.3 `register(hooks)`
Wird genau einmal beim Systemstart aufgerufen. Der `hooks`-Parameter ist das zentrale `HOOKS`-Dict (siehe Abschnitt 2). Hier hängst du deine Handler-Funktionen an die gewünschten Hook-Punkte an:

```python
def register(self, hooks):
    hooks["mkc_after"].append(self._on_mkc_done)

def _on_mkc_done(self, ctx):
    print(f"MKC done for: {ctx['input_text'][:50]}")
```

**Hook-Priorität (seit v1.1):** Setze `hook_priority` auf der Handler-Funktion, um die Ausführungsreihenfolge zu steuern. Niedriger Wert = frühere Ausführung. Default: 100.

```python
def register(self, hooks):
    hooks["mkc_after"].append(self._early_handler)
    hooks["mkc_after"].append(self._late_handler)

def _early_handler(self, ctx):
    pass
_early_handler.hook_priority = 10

def _late_handler(self, ctx):
    pass
_late_handler.hook_priority = 200
```

### 1.4 `execute(context)`
Wird aufgerufen, wenn das Plugin über den `kernel_before`-Hook getriggert wird (Standard-Pipeline-Durchlauf). Kann auch leer bleiben, wenn das Plugin nur via `register()` Handler anmeldet.

---

## 2. Hook-Punkte (14 Stück)

Das System definiert genau 14 Hook-Punkte, einen vor und nach jeder Pipeline-Stufe:

| # | Hook-Name | Phase | Garantierte Context-Keys |
|---|-----------|-------|-------------------------|
| 1 | `kernel_before` | Vor Pipeline-Start | `input_text`, `kernel` |
| 2 | `mkc_before` | Vor MKC-Compiler | + `enriched_input` |
| 3 | `mkc_after` | Nach MKC-Compiler | + `mcxf_dict`, `mcxf` |
| 4 | `bridge_before` | Vor Bridge-Mapping | (gleicher Stand wie mkc_after) |
| 5 | `bridge_after` | Nach Bridge-Mapping | + `execution_plan`, `validation` |
| 6 | `optimizer_before` | Vor Optimizer | (gleicher Stand wie bridge_after) |
| 7 | `optimizer_after` | Nach Optimizer | + `optimized_plan`, `opt_report` |
| 8 | `mel_before` | Vor MEL-Execution | (gleicher Stand wie optimizer_after) |
| 9 | `mel_after` | Nach MEL-Execution | + `mel_result` |
| 10 | `feedback_before` | Vor Feedback-Analyse | + `exec_result` |
| 11 | `feedback_after` | Nach Feedback-Analyse | + `feedback` |
| 12 | `memory_before` | Vor Memory-Store | (gleicher Stand wie feedback_after) |
| 13 | `kernel_after` | Nach Pipeline-Ende (Happy Path) | + `mem_id` (alle 14 Keys) |
| 14 | `memory_after` | Nach Memory-Store | (gleicher Stand wie kernel_after) |

### 2.1 Context-Contract (garantierte Keys)

| Key | Typ | Verfügbar ab | Beschreibung |
|-----|-----|-------------|-------------|
| `input_text` | `str` | Immer | Originaler User-Input |
| `kernel` | `MuscalKernel` | Immer | Kernel-Referenz (lesend) |
| `_hook_name` | `str` | Immer | Name des aktuellen Hooks (z. B. `"mkc_before"`) |
| `enriched_input` | `str` | **mkc_before**+ | RAG-angereicherter Input |
| `mcxf_dict` | `dict` | **mkc_after**+ | Roh-MCXF-Dict |
| `mcxf` | `MCXFDocument` | **mkc_after**+ | Strukturiertes MCXF |
| `execution_plan` | `ExecutionPlan` | **bridge_after**+ | Gemappte Tool-Liste |
| `validation` | `ValidationResult` | **bridge_after**+ | Bridge-Validierung |
| `optimized_plan` | `OptimizedPlan` | **optimizer_after**+ | Optimierter Ausführungsplan |
| `opt_report` | `OptimizationReport` | **optimizer_after**+ | Optimizer-Report |
| `mel_result` | `list` | **mel_after**+ | Tool-Ergebnisse |
| `exec_result` | `dict` | **feedback_before**+ | Aufbereitete Ergebnisse |
| `feedback` | `FeedbackReport` | **feedback_after**+ | Feedback-Analyse |
| `mem_id` | `int` | **kernel_after**+ (Happy Path) | Memory-DB-ID |

### 2.2 Wichtige Hinweise

- Context-Keys **akkumulieren**: Spätere Hooks sehen alle Keys früherer Hooks.
- Der **Error-Path** (bei Bridge-Validierungsfehler) hat NUR Keys bis `execution_plan`. `mel_result`, `feedback`, `mem_id` fehlen.
- Der **MKC-Error-Path** hat nur Keys bis `enriched_input`.
- `_hook_name` wird automatisch von `run_hooks()` gesetzt. **Nicht manuell setzen.**

---

## 3. Plugin-Struktur

Jedes Plugin lebt in einem Unterverzeichnis von `features/`:

```
features/
├── mkc/
│   ├── audit_plugin.py
│   ├── trace_plugin.py
│   ├── confidence_plugin.py
│   └── rag_enrich_plugin.py
├── bridge/
│   └── input_classifier_plugin.py
├── runtime/
│   └── health_monitor.py
├── auth/
│   └── plugin.py
└── examples/
    └── summary_plugin.py
```

Namenskonvention: `<domain>_<funktion>.py`

---

## 4. Safety-Validator (Automatisch)

Beim Laden eines Plugins wird `validate_plugin(module)` ausgeführt.
Folgende Patterns sind **verboten**:

| Pattern | Grund |
|---------|-------|
| `sqlite3.connect` | Direkter DB-Zugriff umgeht Memory-Layer |
| `import kernel` | Core-Import |
| `from kernel import` | Core-Import |
| `import muscal_os` | Core-Import |
| `from muscal_os import` | Core-Import |
| `import main_boot` | Core-Import |
| `from main_boot import` | Core-Import |
| `MuscalKernel` | Direct kernel class access |
| `SystemAgentRuntime` | Direct runtime access |
| `global ` | Global state |
| `__builtins__` | Builtins-Manipulation |
| `ctypes.` | C-FFI |
| `import socket` | Network |
| `importlib.import_module` | Dynamic import |

Zusätzlich via Regex blockiert: `__import__(`, `exec(`, `eval(`, `compile(`, `subprocess.`, `os.system`, `os.popen`, `os.fork`, `__builtins__`, `ctypes.`, `importlib.import_module`.

---

## 5. Best Practices

### 5.1 Handler gezielt registrieren, nicht alle

```python
def register(self, hooks):
    hooks["mkc_after"].append(self._on_mkc)
    hooks["feedback_after"].append(self._on_feedback)
```

### 5.2 Hook-Priorität nutzen

```python
def register(self, hooks):
    hooks["mkc_after"].append(self._early)
    hooks["mkc_after"].append(self._late)

_early = lambda self, ctx: None
_early.hook_priority = 10
_late = lambda self, ctx: None
_late.hook_priority = 200
```

### 5.3 Context lesen, nicht schreiben

```python
# ✅ OK: Lesender Zugriff
input_text = ctx.get("input_text", "")

# ✅ OK: Metadata anreichern (Plugin-eigener Key)
ctx["my_tags"] = {"word_count": len(input_text.split())}

# ❌ VERBOTEN: Core-Daten manipulieren
# ctx["input_text"] = "geändert"
# ctx["kernel"].graph = None
```

### 5.4 Fehlerbehandlung

Exceptions in Plugins werden von `run_hooks()` abgefangen:

```python
def _on_mkc(self, ctx):
    try:
        # ... normale Arbeit
    except Exception as e:
        log_error(e)
```

Der Handler wird nach einem Fehler **dauerhaft entfernt** (Auto-Heal). Bei flüchtigen Fehlern selbst abfangen.

### 5.5 Keine Side-Effects auf Core

| Erlaubt | Verboten |
|---------|----------|
| Dateien in `storage/` schreiben | Dateien in `/` schreiben |
| Context-Keys lesen | Core-Context-Keys ändern |
| Metadata anreichern (`ctx["my_key"]`) | Core-Felder überschreiben |
| Loggen in eigene JSONL-Dateien | `sqlite3.connect()` aufrufen |
| Exceptions werfen (werden gefangen) | `sys.exit()` oder `os._exit()` |

---

## 6. Testen

Benutze den Test-Helper aus `tests/helpers.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("storage", exist_ok=True)

from tests.helpers import reload_plugins, run_pipeline_with_plugins

reload_plugins()
result = run_pipeline_with_plugins("print hello")
assert result["result"].success
```

### Test-Helper API

| Funktion | Beschreibung |
|----------|-------------|
| `reset_plugins()` | Leert HOOKS und PLUGINS |
| `reload_plugins()` | reset + load_plugins() |
| `count_hooks(name=None)` | Anzahl registrierter Handler |
| `assert_ctx_has(ctx, keys)` | Prüft Context-Keys |
| `run_pipeline_with_plugins(text)` | Führt Pipeline aus, gibt Ergebnis |

---

## 7. Beispiel-Vollständiges Plugin

Siehe `features/examples/summary_plugin.py`:

```python
import json, os, time

class Plugin:
    name = "pipeline_summary"
    version = "1.0.0"

    def register(self, hooks):
        hooks["kernel_before"].append(self._on_start)
        hooks["kernel_after"].append(self._on_end)

    def _on_start(self, ctx):
        ctx["_pipeline_start"] = time.time()

    def _on_end(self, ctx):
        duration = round((time.time() - ctx["_pipeline_start"]) * 1000, 2)
        with open("storage/pipeline_summary.jsonl", "a") as f:
            f.write(json.dumps({
                "duration_ms": duration,
                "success": ctx.get("feedback") is not None,
                "input_preview": ctx.get("input_text", "")[:100],
            }) + "\n")

    def execute(self, context):
        return {"last_summary": context.get("_pipeline_start")}
```

---

## 8. Plugin-Übersicht (Aktuelle Plugins)

| Plugin | Domain | Version | Hooks | Output |
|--------|--------|---------|-------|--------|
| `audit_logger` | `mkc/` | — | Alle 14 | `storage/audit.jsonl` |
| `execution_trace` | `mkc/` | — | 8 Stufen | `storage/trace.jsonl` |
| `confidence_metrics` | `mkc/` | — | `mkc_after`, `feedback_after` | `storage/confidence.jsonl` |
| `rag_enrichment` | `mkc/` | — | `mkc_before` | `storage/rag_enrich.jsonl` + `ctx["rag_tags"]` |
| `input_classifier` | `bridge/` | — | `mkc_after` | `storage/input_classifier.jsonl` + `ctx["input_class"]` |
| `health_monitor` | `runtime/` | — | Kernel + Health-Listener | `storage/health.jsonl` |
| `auth` | `auth/` | — | Custom `check_auth` | API-Key-Verifikation |
| `pipeline_summary` | `examples/` | 1.0.0 | `kernel_before`, `kernel_after` | `storage/pipeline_summary.jsonl` |
