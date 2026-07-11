# MUSCAL CORE — Technical Baseline

**Version:** 1.0.0
**Basiert auf:** TECHNICAL_MANUAL_v0.7.md
**Status:** ✅ Authoritative (Stand 2026-07-07)

---

## 1. System Purpose

MUSCAL CORE (Multi-Scale Context-Aware Learning) ist ein kognitives
Betriebssystem — keine Bibliothek, kein Framework. Es orchestriert
AI-Agents, führt Tasks aus, kompiliert natürliche Sprache in ausführbare
Pläne und überwacht sich selbst durch einen Observability-Stack.

## 2. Kernel-Prinzipien

| Prinzip | Beschreibung |
|---------|-------------|
| Determinismus | L1-Routing ist regelbasiert, kein LLM, <1µs |
| Single Writer | Nur ein Thread schreibt in die DB (CQRS) |
| Safety First | Jeder LLM-Input wird auf Injection geprüft |
| Layer-Trennung | Jede Schicht hat genau eine Verantwortung |
| Replayability | Jeder Task ist deterministisch wiederholbar |
| Bounded Growth | Graph (5000 Nodes), Memory (10000 Einträge), Events (50000) |

## 3. Pipeline

```
User Input
  → RAG Context Retrieval (memory.get_recent)
  → MKC Compile (mkc.py + mkc_rules.py: Text → MCXF)
  → Bridge Tool Matching (bridge.py: 9 Regex-Matcher)
  → Optimizer Pipeline (runtime/optimizer/: DCE → Fusion → Parallel)
  → MEL Execute (mel.py + tools.py + SystemAgentRuntime)
  → Feedback Analysis (feedback.py: Confidence Adjustments)
  → Memory Store (memory.py: SQLite + JSONL + Pruning)
  → KernelResult
```

## 4. 7-Schichten-Architektur

```
L7 FRONTEND      React JSX (Dashboard, GraphView)
L6 API LAYER     Flask API (:5050), FastAPI (:8080)
L5 OS LAYER      BootManager, EventBus, Deployment-Modi
L4 COMPILER      MKC (MCXF), Bridge (Tool-Match), Optimizer, Feedback
L3 EXECUTION     MEL (Tool-Dispatch), Browser Engine, Desktop Tools
L2 KERNEL        WriterThread (CQRS), Scheduler, Gate, Governance, RAG
L1 STORAGE       SQLite (WAL, 12 Tabellen), JSONL, ChromaDB
```

## 5. Kernmodule

### `kernel.py` — Hauptorchestrator
- Klasse: `MuscalKernel`
- Orchestriert: RAG → MKC → Bridge → Optimizer → MEL → Feedback → Memory
- Safety Guard: Auto-Prune bei >10000 Graph-Nodes

### `mkc.py` — Compiler
- Klasse: `mkc()` Funktion
- Rule-based classification via `mkc_rules.py`
- Output: MCXF dict mit decisions/tasks/architecture/constraints

### `bridge.py` — Tool-Mapping
- 9 Regex-Matcher: filesystem.write, math.add, console.print, browser.*, desktop.*
- Output: ExecutionPlan (intent + steps)

### `mel.py` — Execution Layer
- Lazy Runtime (`_get_runtime()`)
- TOOL_REGISTRY Dispatch + SystemAgentRuntime

### `memory.py` — Persistenz
- Lazy Connection (`_get_conn()`)
- SQLite + JSONL
- MAX_MEMORY_ENTRIES = 10000

### `graph.py` — Graph State
- MAX_NODES = 5000, MAX_EDGES = 10000
- FIFO-Eviction
- Event-driven (node_created, edge_created, ...)

### `feedback.py` — Feedback-Analyse
- Erkennt UNMAPPED_TOOL, WRONG_ARG_TYPE, PARTIAL_EXECUTION
- Passt Confidence in `mkc_rules.py` an

## 6. Stabilitäts-Patches (v0.7)

- Import Chain stabil (memory.py, mel.py, config.py lazy)
- Graph/Memory/Event bounded
- Stress-Test bestanden (100 Iterationen, 0 Crashes)
- Plugin-System v1 aktiv

## 7. Ressourcen-Grenzen

| Ressource | Max | Datei | Eviction |
|-----------|-----|-------|----------|
| Graph Nodes | 5000 | graph.py | FIFO (Timestamp) |
| Graph Edges | 10000 | graph.py | FIFO |
| Memory DB | 10000 Zeilen | memory.py | ORDER BY id DESC |
| Event History | 50000 | event_bus.py | POP(0) |
| SIGNAL_RULES Adjustment | -0.3 bis +0.1 | mkc_rules.py | Clamped |
| Keyword Additions | max 5 | mkc_rules.py | Capped |

## 8. Entrypoints

| Befehl | Beschreibung |
|--------|-------------|
| `pip install -r requirements.txt` | Installation |
| `python3 main.py` | REPL |
| `python3 main_boot.py` | OS-Modus |
| `python3 runtime/main.py` | Flask API (:5050) |
| `python3 api_server.py` | FastAPI (:8080) |
| `docker compose up` | Containerisiert |

## 9. Technical Debt (bekannt)

1. ~80 Stub-Dateien (<20 Zeilen) — Consensus, Distributed, Evolution
2. SIGNAL_RULES Confidence-Drift ohne Auto-Reset
3. FIFO-Eviction ohne semantische Bewertung
4. Keine DB-Migrationen
5. Keine CI/CD
