# MUSCAL CORE — Architecture Map (Baseline)

**Erstellt:** 2026-07-08

---

## Layer Overview

```
L7 FRONTEND      React JSX (Dashboard, GraphView)
L6 API LAYER     Flask API (:5050), FastAPI (:8080)
L5 OS LAYER      MuscalOS, BootManager, EventBus
L4 COMPILER      MKC → Bridge → Optimizer → Feedback
L3 EXECUTION     MEL, Browser Engine, Desktop Tools
L2 KERNEL        WriterThread, Scheduler, Gate, Governance, RAG
L1 STORAGE       SQLite (WAL), JSONL, ChromaDB
```

## Pipeline

```
Input → RAG → MKC → Bridge → Optimizer → MEL → Feedback → Memory → Output
```

## Module Groups

### Kernel Group (21 core files)
`kernel.py`, `mkc.py`, `bridge.py`, `memory.py`, `mel.py`, `schema.py`,
`mkc_rules.py`, `config.py`, `event_bus.py`, `graph.py`, `feedback.py`,
`muscal_os.py`, `main.py`, `main_boot.py`, `boot_manager.py`, `os_config.py`,
`plugin_registry.py`, `plugin_loader.py`, `sphere.py`, `debugger.py`,
`tools.py`, `rag.py`, `trace_engine.py`, `cognitive_diff.py`, `muscal_loop.py`

### Runtime Group (immutable)
`runtime/kernel/*`, `runtime/llm/*`, `runtime/optimizer/*`,
`runtime/api/*`, `runtime/services/*`, `runtime/observation/*`

### Plugin Group (features/)
```
features/mkc/       (audit, trace, confidence, rag_enrich)
features/bridge/
features/memory/
features/runtime/   (health_monitor)
```

### Stub Groups (84 files <20 lines)

| Group | Count | Status |
|-------|-------|--------|
| INIT (__init__.py) | 10 | ✅ Package markers |
| CORE (imported) | 22 | ✅ Aktiv genutzt |
| DEAD (0 imports) | 9 | 💀 Ungenutzt |
| MINIMAL (alt.impl.) | 8 | ⚠️ Teils genutzt |
| PLUGIN_CANDIDATE | 35 | 🟡 Klein/Eigenständig |

## Memory Implementations (ADR-001 relevant)

| Klasse | Datei | Status |
|--------|-------|--------|
| `memory._get_conn()` | `memory.py` | ✅ Aktiv (SQLite, lazy, bounded) |
| `GraphMemory` | `graph_memory.py` | ✅ Aktiv (In-Memory Graph) |
| `MinimalGraphMemory` | `minimal_graph_memory.py` | ✅ Alias für GraphMemory |
| `RAGStore` | `minimal_rag.py` | ✅ Aktiv (Keyword-basiert) |
| `MCXFMemory` | `minimal_mcxf_memory.py` | 🟡 Unklar |
| `VectorMemory` | `vector_memory.py` | 💀 Nur von DEAD rag_vector.py importiert |

## Kernel Implementations (ADR-002 relevant)

| Klasse | Datei | Status |
|--------|-------|--------|
| `MuscalKernel` | `kernel.py` | ✅ **Haupt-Kernel** (414 Zeilen) |
| `KernelCore` | `kernel_core.py` | 🟡 68 Zeilen, von distributed_boot.py genutzt |
| `MinimalKernel` (implizit) | `minimal.py`, `minimal_core.py` | 🟡 Experimentell |
