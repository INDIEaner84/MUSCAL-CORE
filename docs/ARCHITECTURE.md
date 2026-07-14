# MUSCAL CORE — Architecture Overview

## Layer Diagram

```
  ┌─────────────────────────────────────────────────────────────┐
  │ L7 FRONTEND      React JSX (Dashboard, GraphView)          │
  ├─────────────────────────────────────────────────────────────┤
  │ L6 API LAYER     Flask API (:5050), FastAPI (:8080)         │
  ├─────────────────────────────────────────────────────────────┤
  │ L5 OS LAYER      BootManager, EventBus, Deployment-Modi     │
  ├─────────────────────────────────────────────────────────────┤
  │ L4 COMPILER      MKC (MCXF), Bridge (Tool-Match),          │
  │                  Optimizer (DCE/Fusion/Parallel), Feedback   │
  ├─────────────────────────────────────────────────────────────┤
  │ L3 EXECUTION     MEL (Tool-Dispatch), Browser Engine,       │
  │                  Desktop Tools                              │
  ├─────────────────────────────────────────────────────────────┤
  │ L2 KERNEL        WriterThread (CQRS), Scheduler, Gate,     │
  │                  Governance, RAG Index, ChromaDB            │
  ├─────────────────────────────────────────────────────────────┤
  │ L1 STORAGE       SQLite (WAL, 12 Tabellen), JSONL, ChromaDB│
  └─────────────────────────────────────────────────────────────┘
```

## 5 Kernel Perspectives

| Kernel | Layers | Responsibility |
|--------|--------|---------------|
| Observability | L7+L6+L5 | Monitoring, metrics, UI, replay |
| Control | L5+L2 | Decisions, limits, consensus, strategy |
| Cognitive | L4 | NL→Plan compilation, optimization |
| Runtime | L3+L2 | Execution, process isolation, safety |
| Storage | L1 | Persistence, indices, state recovery |

## Pipeline Data Flow

```
Input → RAG → MKC → Bridge → Optimizer → MEL → Feedback → Memory → Output
```

## Module Dependency Map

```
MuscalKernel (kernel.py)
  ├── mkc.py → mkc_rules.py → bridge.py
  │     └── bridge.py → tools.py, schema.py
  ├── mel.py → tools.py, system_runtime.py
  ├── feedback.py → schema.py, mkc_rules.py
  ├── memory.py (lazy SQLite)
  ├── rag.py → memory.py
  ├── graph.py (bounded 5000/10000)
  └── sphere.py → graph.py
```

## See Also

- `docs/TECHNICAL_BASELINE.md` — detailed module descriptions
- `spec/` — architecture decisions
- `archive/history/rfcs/` — specifications
