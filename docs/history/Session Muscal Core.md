# Session Transcript — MUSCAL Core

**Datum:** 2026-07-02
**Projekt:** MUSCAL BOOTSTRAP KIT v0.1 → MUSCAL OS Bootstrap
**Arbeitsverzeichnis:** `/home/hz/AlitaProject/Codebase/MUSCAL CORE`

---

## Übersicht

In dieser Session wurde das MUSCAL Core System von einem einfachen Kernel+Pipeline-Prototyp zu einem vollständigen Bootstrap-Betriebssystem mit 28 Dateien ausgebaut.

---

## Erstellte/Geänderte Dateien

### Phase 1: Bestehende Basis (vor Session)

| Datei | Beschreibung |
|---|---|
| `spec.yaml` | MUSCAL BOOTSTRAP KIT v0.1 Spezifikation |
| `schema.py` | Alle Dataclasses (KnowledgeTriple, MCXFDocument, ExecutionPlan, KernelResult, Node, Edge, etc.) |
| `tools.py` | TOOL_REGISTRY (3 tools) + TOOL_SCHEMAS (15 tools) |
| `mkc.py` | MKC — Klassifikation von Input in SIGNAL_RULES |
| `mel.py` | MEL — Ausführung von ExecutionPlan, routing browser.*/desktop.* → SystemAgentRuntime |
| `memory.py` | SQLite Memory-Persistenz (memory.db, logs.jsonl) |
| `rag.py` | RAG — Context Retrieval + Enrichment |
| `mkc_rules.py` | SIGNAL_RULES, IGNORED_KEYWORDS, classify_statement(), apply_feedback() |
| `feedback.py` | analyze_feedback() — UNMAPPED_TOOL, WRONG_ARG_TYPE, PARTIAL_EXECUTION |
| `bridge.py` | MCXF → MEL Bridge mit 9 Pattern-Matchern |
| `graph.py` | GraphState — passiver Observer mit Nodes/Edges/Events |
| `sphere.py` | SphereState — radiale Projektion (center/inner/middle/outer) |
| `kernel.py` | MuscalKernel — single entry point orchestrating MKC→RAG→Bridge→MEL→Feedback→Memory |
| `main.py` | REPL-Entry-Point für manuelle Eingabe |
| `system_runtime.py` | SystemAgentRuntime — safety validation, browser/desktop routing |
| `browser_tools.py` | BrowserRuntime (Playwright): 8 tools (open, click, type, scroll, extract_text, screenshot, get_html) |
| `desktop_tools.py` | DesktopRuntime (PyAutoGUI): 6 tools (open_app, type, click, screenshot, move, keypress) |

### Phase 2: Cognitive Diff Engine (neu in dieser Session)

| Datei | Zeilen | Beschreibung |
|---|---|---|
| `kernel_snapshot.py` | ~60 | `get_kernel_snapshot()` — Read-only Introspection von live kernel state (9 Parameter-Kategorien) |
| `cognitive_diff.py` | ~220 | `CognitiveDiffEngine` — Vergleicht 2 Snapshots in 5 Dimensionen (Logical, Behavioral, Architectural, Risk, Performance) + Recommendation Logic |

**Snapshot-Datei:** `storage/kernel_snapshot_v0.1.json` (4515 Bytes)

**Diff-Dimensionen im Detail:**

| Dimension | Erkannte Änderungen | Recommendation-Impact |
|---|---|---|
| **Logical** | KEYWORD_ADDED/REMOVED, BASE_CONFIDENCE_CHANGED, ADJUSTMENT_CHANGED, RANGE_CHANGED, SECTION_FALLBACK_CHANGED, THRESHOLD_CHANGED, IGNORE_ADDED/REMOVED | accuracy ±%, stability ±% |
| **Behavioral** | TOOL_ADDED/REMOVED, TOOL_INPUT/OUTPUT/CONSTRAINTS_CHANGED, PATTERN_ADDED/REMOVED, REGISTRY_SIZE_CHANGED | conflict_rate ±% |
| **Architectural** | MODULE_ADDED/REMOVED, EVENT_ADDED/REMOVED | stability ±% |
| **Risk** | CRITICAL (HALLUCINATION), HIGH (DETERMINISM), MEDIUM (AMBIGUITY, INSTABILITY), LOW (OVERSIGHT) | REJECT/REVIEW |
| **Performance** | accuracy, stability, conflict_rate, confidence (HIGH/LOW) | aggregiert in recommendation |

**Recommendation Logic:**
- CRITICAL risks → `REJECT`
- HIGH risks → `REVIEW`
- Negative accuracy + stability → `ROLLBACK`
- No changes, high confidence → `MERGE`

**Getestet:**
- Self-Comparison (v0.1 vs itself): 0 diffs, MERGE
- Simulated Upgrade (add keyword, change confidence, remove ignore, add tool): 3 logical + 2 behavioral diffs, REVIEW
- Risk: browser tool added → HIGH/DETERMINISM erkannt

### Phase 3: MUSCAL OS Bootstrap (neu in dieser Session)

| Datei | Zeilen | Beschreibung |
|---|---|---|
| `os_config.py` | ~65 | 3 Deployment-Modi Enum + `MuscalConfig` Dataclass + `load_config()` Factory mit Override-Support |
| `event_bus.py` | ~70 | Pub/Sub Event Bus mit Topics, Prioritäten (LOW/NORMAL/HIGH/CRITICAL), max 1000 History, Wildcard `*` |
| `boot_manager.py` | ~100 | 8 Boot-Phasen (INIT→LOAD_CONFIG→INIT_MODULES→START_SERVICES→HEALTH_CHECK→READY/SHUTDOWN/FAILED), `BootStepResult`, `BootReport` |
| `muscal_os.py` | ~220 | `MuscalOS`-Klasse: `start()`/`shutdown()`/`restart()`/`run()`/`get_status()`, orchestriert Kernel + EventBus + BootManager |
| `main_boot.py` | ~130 | CLI-Entry-Point: argparse, Signal-Handling, 3 Modi, `--eval`, `--status`, interaktiver REPL mit `/help`/`/status`/`/shutdown` |

**Architektur:**

```
main_boot.py
    │
    ▼
MuscalOS
    ├── MuscalConfig     (os_config.py)
    ├── EventBus         (event_bus.py)    ← inter-component publish/subscribe
    ├── BootManager      (boot_manager.py) ← boot lifecycle + health checks
    └── MuscalKernel     (kernel.py)       ← MKC→RAG→Bridge→MEL→Feedback→Memory
         ├── GraphState  (graph.py)        ← passive observer
         ├── SphereState (sphere.py)       ← radial UI layer
         └── SystemAgentRuntime            ← browser/desktop runtime
```

**Boot-Phasen:**

| Phase | Steps | Verhalten bei Fehler |
|---|---|---|
| `INIT` | create_storage, init_event_bus | Hard Fail → Abbruch |
| `LOAD_CONFIG` | validate_config, resolve_paths | Hard Fail → Abbruch |
| `INIT_MODULES` | init_kernel, init_system_runtime | Hard Fail → Abbruch |
| `START_SERVICES` | wire_event_bus, load_snapshot | Soft |
| `HEALTH_CHECK` | memory_db, graph, sphere, tools | Soft (Warnung, kein Fail) |
| `READY` | — | Nur bei 0 Fehlern |
| `SHUTDOWN` | save_snapshot, close_storage, flush_events | Cleanup immer |

**Deployment-Modi:**

| Mode | Browser | Desktop | Simulation | Verbose | Boot-Timeout |
|---|---|---|---|---|---|
| `local_dev` | ON | ON | OFF | ON | 60s |
| `production` | OFF | OFF | OFF | OFF | 10s |
| `simulation` | ON | ON | ON | ON | 30s |

**CLI Usage:**
```bash
python3 main_boot.py --mode simulation --eval "add 5 and 3"
python3 main_boot.py --mode local_dev --status
python3 main_boot.py --mode production          # interaktiver REPL
python3 main_boot.py --no-graph --no-sphere -m simulation -e "print hello"
```

**Getestet:**
- `os_config.py` Unit-Tests: alle 3 Modi + Overrides ✓
- `event_bus.py` Unit-Tests: publish/subscribe/wildcard/history/clear ✓
- `boot_manager.py` Unit-Tests: fehlschlagende/successvolle Phasen ✓
- LOCAL_DEV boot (12 steps, 0 errors) ✓
- PRODUCTION boot (12 steps, 0 errors) ✓
- SIMULATION boot + run (12 steps, add/print) ✓
- Shutdown in allen Modi erfolgreich ✓
- CLI `--status`, `--eval`, interaktiv (piped) ✓
- Legacy `main.py` Pfad weiterhin funktionsfähig ✓

---

## Architektur-Entscheidungen

1. **Flat Project Structure** — Keine Unterordner (außer `storage/`), einfache Imports
2. **Graph = passiver Observer** — Liest Events, modifiziert niemals Kernel-Verhalten
3. **Sphere Center = letzter INTENT-Node** — Nicht graph's focus_node; `focus_path` trackt Rotationen
4. **RAG enriched MKC input, nicht MCXF** — Context wird mit `---` vor classification prepended
5. **Tool-Extraction nutzt rohen Input** — RAG enrichment beeinflusst nur classification
6. **Browser/Desktop = optional** — System läuft vollständig ohne playwright/pyautogui
7. **Feedback Confidence clamped** — [-0.3, 0.1] verhindert Drift
8. **MCXF v0.3** — 13 Sections (00-12) mit execution model, tool schema, conflict model
9. **SIMULATION = dry-run** — Tools geben simulierte Ergebnisse ohne Side Effects
10. **EventBus = eigener Bus** — Nicht graph.on(), sondern separater pub/sub für OS-weite Events
11. **Boot Health-Checks soft** — Degradierte Services erlauben Boot, nur harte Fehler brechen ab
12. **Shutdown immer cleanup** — Auch bei Fehlern wird snapshot gespeichert

---

## Nächste Schritte (priorisiert)

1. **MCXF → ExecutionPlan Bridge für Browser-Tasks** — Natural Language → browser.open/click/type
2. **LLM Integration (MKC v0.2)** — Ollama/OpenAI für non-rule-based Classification
3. **Weitere Tests** — Vollständige Boot-Sequenz inkl. browser/desktop mit installierten Dependencies

---

## Dateistruktur (28 Einträge)

```
MUSCAL CORE/
├── __pycache__/
├── storage/
│   ├── kernel_snapshot_v0.1.json
│   ├── logs.jsonl
│   └── memory.db
├── boot_manager.py        ← NEU
├── bridge.py
├── browser_tools.py
├── cognitive_diff.py      ← NEU
├── desktop_tools.py
├── event_bus.py           ← NEU
├── feedback.py
├── graph.py
├── kernel_snapshot.py     ← NEU
├── kernel.py
├── main_boot.py           ← NEU
├── main.py
├── mcxf_demo.md
├── mcxf_demo_002.md
├── mel.py
├── memory.py
├── mkc.py
├── mkc_rules.py
├── muscal_os.py           ← NEU
├── os_config.py           ← NEU
├── rag.py
├── schema.py
├── spec.yaml
├── sphere.py
├── system_runtime.py
├── tools.py
└── Session Muscal Core.md ← NEU (dieses Dokument)
```
