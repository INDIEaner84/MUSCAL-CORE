# MUSCAL CORE — Technisches Handbuch

**Version:** 0.6 (Juli 2026)
**Projektordner:** `/home/hz/AlitaProject/Codebase/MUSCAL CORE/`
**Sprache:** Python 3.12+
**Gesamtumfang:** ~184 Python-Dateien, ~10.744 Zeilen Code, ~225 Dateien gesamt
**Status:** Late Alpha / Early Beta (Kernpipeline funktionsfähig, ~45% Stubs)

---

## 1. PROJEKTÜBERSICHT

### 1.1 Was ist MUSCAL CORE?

MUSCAL CORE (Multi-Scale Context-Aware Learning) ist ein **kognitives Betriebssystem** — keine Bibliothek, kein Framework. Es orchestriert AI-Agents, führt Tasks aus, kompiliert natürliche Sprache in ausführbare Pläne und überwacht sich selbst durch einen mehrschichtigen Observability-Stack.

Anders als herkömmliche AI-Frameworks (LangChain, AutoGen, CrewAI) ist MUSCAL CORE als **eigenständiges System** konzipiert: Es hat einen Kernel, ein OS-Layer, Compiler, Optimierer, API-Server und Frontend — alles in einer Codebasis.

### 1.2 Entstehung

MUSCAL CORE wurde aus Code mehrerer AI-Modelle (Claude, ChatGPT, Mimo, Kimi, Minimax) in einer einzigartigen Symbiose entwickelt. Es vereint:
- **Compiler**-Architektur (MKC → Bridge → MEL)
- **OS**-Lifecycle (Boot → Health → Shutdown)
- **Optimizer** mit LLVM-artigen Passes
- **CQRS**-Datenhaltung (Command Query Responsibility Segregation)
- **Governance** mit Token/Iterations-Limits

### 1.3 Kern-Prinzipien

| Prinzip | Beschreibung |
|---------|-------------|
| **Determinismus** | L1-Routing ist regelbasiert, kein LLM, <1µs |
| **Single Writer** | Nur ein Thread schreibt in die DB (CQRS) |
| **Safety First** | Jeder LLM-Input wird auf Injection geprüft |
| **Layer-Trennung** | Jede Schicht hat genau eine Verantwortung |
| **Replayability** | Jeder Task ist deterministisch wiederholbar |

---

## 2. ARCHITEKTUR (7 Schichten)

### 2.1 Schichtenmodell

```
                    ┌─────────────────────────────────────┐
  L7 FRONTEND       │  React JSX (Dashboard, GraphView)   │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L6 API LAYER      │  Flask API (:5050)                  │
                    │  FastAPI  (:8080)                    │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L5 OS LAYER       │  BootManager, EventBus,             │
                    │  Deployment-Modi, Graceful Shutdown │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L4 COMPILER       │  MKC (MCXF), Bridge (Tool-Match),  │
                    │  Optimizer (DCE/Fusion/Parallel),   │
                    │  Feedback, CognitiveDiff            │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L3 EXECUTION      │  MEL (Tool-Dispatch),               │
                    │  Browser Engine, Desktop Tools      │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L2 KERNEL         │  WriterThread (CQRS), Scheduler,    │
                    │  Gate, Governance, Sanitizer,       │
                    │  RAG Index, ChromaDB                │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L1 STORAGE        │  SQLite (WAL, CQRS, 12 Tabellen),   │
                    │  JSONL Logs, FAISS, ChromaDB,       │
                    │  MCXF Memory Store                   │
                     └─────────────────────────────────────┘
```

#### 4-Kernel-Perspektive (horizontale Schnittebene)

Dieselben 7 Layer lassen sich in **4 logische Subkernel** gruppieren — dies ist die systemtheoretische Sicht:

```
┌─────────────────────────────────────────────────────────────────┐
│  L4 OBSERVABILITY KERNEL                                        │
│  EventBus, Observation Loop, Replay Engine, Dashboard, Metrics  │
│  Verantwortung: Systemüberwachung, Ereignis-Routing, Metriken   │
├─────────────────────────────────────────────────────────────────┤
│  L3 CONTROL KERNEL                                              │
│  MAS Scheduler, Policy Engine, Consensus (Byzantine/Weighted),  │
│  Governance, Gate, Cognitive Diff, Permission Engine            │
│  Verantwortung: Entscheidungen, Limits, Konsens, Strategie      │
├─────────────────────────────────────────────────────────────────┤
│  L2 COGNITIVE KERNEL                                            │
│  MKC Compiler, MCXF, Bridge, Optimizer, YAML Workflow Engine,  │
│  Agent Pipeline, Feedback, RAG Index / ChromaDB                 │
│  Verantwortung: NL→Plan-Kompilierung, Tool-Matching, Optimierung│
├─────────────────────────────────────────────────────────────────┤
│  L1 RUNTIME KERNEL                                              │
│  IPC Server/Client, Process Manager, Agent SDK, WriterThread,   │
│  Scheduler (L1), Gate, Sanitizer, MEL, Browser/Desktop Tools    │
│  Verantwortung: Ausführung, Prozess-Isolation, Safety, CQRS     │
├─────────────────────────────────────────────────────────────────┤
│  L0 STORAGE LAYER                                               │
│  SQLite (WAL), JSONL, ChromaDB, FAISS, Snapshots, RAG Cache    │
│  Verantwortung: Persistenz, Indizes, State-Recovery             │
└─────────────────────────────────────────────────────────────────┘
```

**Mapping Layer → Kernel:**

| Vertikaler Layer | Gehört zu Kernel | Begründung |
|-----------------|------------------|------------|
| L7 Frontend | L4 Observability | UI beobachtet, steuert nicht |
| L6 API | L4 Observability | API ist Tor nach außen |
| L5 OS | L3 Control + L4 Observability | Boot = Control, EventBus = Observability |
| L4 Compiler | L2 Cognitive | Kompilierung = kognitive Leistung |
| L3 Execution | L1 Runtime | Tool-Dispatch = Ausführung |
| L2 Kernel | L1 Runtime + L3 Control | WriterThread = Runtime, Gate = Control |
| L1 Storage | L0 Storage | Persistenz = Basis

```
User Input (Text)
    │
    ▼
┌─────────────────────────────┐
│ RAG Context Retrieval       │ ← memory.get_recent(5)
│ + RAG Enrich                │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ MKC Compile                 │ ← mkc.py + mkc_rules.py
│ Text → MCXF {decisions,     │
│   tasks, architecture,      │
│   constraints, glossary}    │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Bridge (Tool Matching)      │ ← bridge.py
│ 9 Regex-Matcher: NL → Tool  │
│ filesystem.write, browser.*,│
│ math.add, console.print     │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Optimizer Pipeline          │ ← runtime/optimizer/
│ DCE → Fusion → Parallel    │
│ + CostModel + Verification  │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ MEL Execute                 │ ← mel.py + tools.py
│ TOOL_REGISTRY Dispatch      │
│ oder SystemAgentRuntime     │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Feedback Analysis           │ ← feedback.py
│ Confidence Adjustments      │
│ UNMAPPED_TOOL / WRONG_ARG   │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Memory Store                │ ← memory.py
│ SQLite + JSONL + Graph      │
└──────────┬──────────────────┘
           ▼
      KernelResult
```

### 2.3 OS Boot-Lifecycle

```
[1] INIT ──────────────────► Config laden, Pfade setzen
[2] LOAD_CONFIG ───────────► os_config.py: deployment mode
[3] INIT_MODULES ──────────► MKC, Bridge, MEL, Feedback, Memory
[4] START_SERVICES ────────► EventBus, Scheduler, WriterThread
[5] HEALTH_CHECK ──────────► Ollama ping, DB integrity
[6] READY ◄────────────────► Normalbetrieb
       │
       ├── SIGINT/SIGTERM ──► SHUTDOWN → Snapshot → Exit
       └── FAILED ──────────► ERROR → Snapshot → Exit
```

---

## 3. KOMPLETTE DATEISTRUKTUR

### 3.1 Root-Dateien

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `kernel.py` | 414 | **Hauptorchestrator**: MuscalKernel mit 7 Modulen | ✅ |
| `muscal_os.py` | 349 | **OS Lifecycle**: start/shutdown/restart/run | ✅ |
| `main_boot.py` | 288 | **Haupt-Einstiegspunkt**: OS-Modus CLI | ✅ |
| `main.py` | 31 | Einfacher REPL-Einstieg | ✅ |
| `muscal_loop.py` | 562 | **Autonomer LLM-Loop**: Plan → Execute → Verify | ✅ |
| `boot_manager.py` | 99 | 8-Phasen Boot-Lifecycle | ✅ |
| `os_config.py` | 74 | 3 Deployment-Modi (local_dev/production/simulation) | ✅ |
| `event_bus.py` | 74 | Pub/Sub EventBus mit Prioritäten + Wildcards | ✅ |
| `mkc.py` | 102 | Regelbasierter MKC Compiler | ✅ |
| `mkc_rules.py` | 135 | SIGNAL_RULES + Confidence-Adjustments | ✅ |
| `bridge.py` | 171 | 9 Regex-Matcher: NL → Tool-Aufruf | ✅ |
| `mel.py` | 41 | Memory Execution Layer: Tool-Dispatch | ✅ |
| `feedback.py` | 94 | Feedback-Analyse (UNMAPPED_TOOL, WRONG_ARG_TYPE) | ✅ |
| `tools.py` | 99 | TOOL_REGISTRY (3) + TOOL_SCHEMAS (15) | ✅ |
| `memory.py` | 107 | SQLite + JSONL Persistenz | ✅ |
| `schema.py` | 245 | Alle Dataclasses + MCXF Validation | ✅ |
| `cognitive_diff.py` | 336 | 5-Dimensionen Diff-Engine | ✅ |
| `graph.py` | 190 | GraphState: passiver Observer | ✅ |
| `sphere.py` | 251 | Radiale Sphere-UI-Projektion | ✅ |
| `trace_engine.py` | 72 | Strukturiertes Trace-Logging (3 Layer, 4 Levels) | ✅ |
| `debugger.py` | 363 | Vollständige Debug-Engine mit Metriken | ✅ |
| `kernel_snapshot.py` | 122 | Read-Only Kernel-Introspection | ✅ |
| `config.py` | 20 | Pfade, Modelle, Ports | ✅ |
| `system_runtime.py` | 106 | Safety-Validation + Tool-Routing | ✅ |
| `Dockerfile` | 10 | Docker-Build (python:3.11-slim) | ✅ |
| `docker-compose.yml` | 10 | Docker-Compose (Port 8000) | ✅ |

### 3.2 MCXF-Schicht

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `mcxf_fusion.py` | 61 | Fusions-Layer (Memory+RAG+Graph+SQL) | ✅ |
| `mcxf_memory_store.py` | 28 | JSON-File Memory Store | ✅ |
| `mcxf_sql.py` | 30 | SQLite MCXF-Persistenz | ✅ |
| `mcxf_compression.py` | 64 | MCXF-Dokumenten-Kompression | ✅ |
| `mcxf_graph_builder.py` | 28 | Graph Builder für MCXF | ✅ |

### 3.3 Browser/Desktop

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `browser_tools.py` | 72 | 7 Playwright-Tools (open/click/type/scroll/extract/screenshot/html) | ✅ |
| `browser_engine.py` | 52 | Playwright Browser-Controller | ✅ |
| `browser_pipeline.py` | 52 | Multi-Step Browser-Pipeline | ✅ |
| `browser_loop_engine.py` | 59 | Browser Automation Loop | ✅ |
| `desktop_tools.py` | 65 | 6 PyAutoGUI Desktop-Tools | ✅ |
| `safe_browser_agent.py` | 28 | Safety-Wrapped Browser Agent | ⚠️ Stub |
| `browser_planner.py` | 25 | UI-Plan-Generator | ⚠️ Stub |
| `browser_executor.py` | 8 | Browser Executor | ⚠️ Stub |
| `browser_node.py` | 13 | Swarm-Node mit Browser | ⚠️ Stub |
| `browser_router.py` | 8 | Browser-Routing | ⚠️ Stub |

### 3.4 Distributed / Swarm

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `swarm_system.py` | 28 | Swarm-Orchestrierung | ⚠️ Stub |
| `swarm_node.py` | 36 | Swarm-Node mit Nachrichten-Routing | ⚠️ Stub |
| `muscal_swarm.py` | 17 | Swarm-System | ⚠️ Stub |
| `event_bus_swarm.py` | 10 | EventBus-Wrapper für Swarm | ⚠️ Stub |
| `distributed_kernel.py` | 26 | Distributed Kernel | ⚠️ Stub |
| `distributed_muscal.py` | 20 | Distributed Node | ⚠️ Stub |
| `distributed_orchestrator.py` | 22 | Distributed Orchestrator | ⚠️ Stub |
| `distributed_bootstrap.py` | 13 | Bootstrap | ⚠️ Stub |
| `worker_pool.py` | 32 | Worker-Pool | ⚠️ Stub |
| `worker_node.py` | 13 | Worker-Node | ⚠️ Stub |

### 3.5 Consensus / Trust

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `consensus_engine.py` | 18 | Mehrheitsentscheid | ⚠️ Stub |
| `weighted_consensus.py` | 22 | Trust-gewichteter Konsens | ⚠️ Stub |
| `emergent_consensus.py` | 16 | Emergenter Konsens | ⚠️ Stub |
| `node_trust.py` | 24 | Node-Trust-Scoring | ⚠️ Stub |
| `self_healing_orchestrator.py` | 56 | Trust → Consensus → Routing → Healing | ✅ Teilw. |
| `adaptive_router.py` | 11 | Trust-basiertes Routing | ⚠️ Stub |

### 3.6 Evolution / Meta-Reasoning

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `evolution_kernel.py` | 36 | Self-Improvement Kernel | ⚠️ Stub |
| `evolution_loop.py` | 27 | Self-Evolution Loop | ⚠️ Stub |
| `meta_evolution_kernel.py` | 44 | Meta-Evolution Kernel | ⚠️ Stub |
| `meta_evolution_loop.py` | 38 | Meta-Evolution Loop | ⚠️ Stub |
| `meta_reasoning_kernel.py` | 27 | Meta-Reasoning + Self-Critique | ⚠️ Stub |
| `recursive_self_improver.py` | 27 | Rekursiver Self-Improver | ⚠️ Stub |
| `metric_registry.py` | 13 | Metrik-Gewichte | ⚠️ Stub |
| `metric_evolution_engine.py` | 9 | Metrik-Evolution | ⚠️ Stub |
| `performance_analyzer.py` | 6 | Performance-Scoring | ⚠️ Stub |
| `evolving_critique.py` | 18 | Evolving Critique | ⚠️ Stub |

### 3.7 Causality / Explanation

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `causality_engine.py` | 17 | Cause/Effect-Inference | ⚠️ Stub |
| `decision_autopsy.py` | 25 | Causal-Analyse + Explanation | ⚠️ Stub |
| `decision_analyzer.py` | 8 | Decision-Analyzer | ⚠️ Stub |
| `explanation_builder.py` | 9 | Explanation-Text-Builder | ⚠️ Stub |
| `explanation_refiner.py` | 9 | Explanation-Refiner | ⚠️ Stub |
| `counterfactual_engine.py` | 16 | What-If-Szenarien | ⚠️ Stub |
| `scenario_evaluator.py` | 8 | Scenario-Scoring | ⚠️ Stub |
| `self_critique.py` | 25 | Counterfactual Self-Critique | ⚠️ Stub |
| `replay_engine.py` | 16 | Graph Replay | ⚠️ Stub |
| `multi_hop_reasoner.py` | 35 | Multi-Hop Reasoning | ⚠️ Stub |

### 3.8 Vision / UI State

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `vision_loop.py` | 44 | Vision-Browser Loop | ⚠️ Stub |
| `vision_layer.py` | 12 | Vision-Analyse | ⚠️ Stub |
| `vision_planner.py` | 12 | Vision-Planner | ⚠️ Stub |
| `screenshot_engine.py` | 8 | Screenshot-Engine | ⚠️ Stub |
| `state_builder.py` | 13 | State-Builder | ⚠️ Stub |
| `ui_state.py` | 8 | UI-State | ⚠️ Stub |

### 3.9 Memory / RAG / Vector

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `rag.py` | 21 | Chronologisches RAG | ✅ |
| `simple_rag.py` | 38 | Hash-basiertes Cosine RAG | ✅ |
| `graph_rag.py` | 21 | Graph-basiertes RAG | ⚠️ Stub |
| `rag_minimal.py` | 15 | Keyword-basiertes RAG | ⚠️ Stub |
| `rag_vector.py` | 16 | Vector-RAG (FAISS) | ⚠️ Stub |
| `embedder.py` | 9 | SentenceTransformer Wrapper | ⚠️ Stub |
| `vector_memory.py` | 19 | FAISS Vector Memory | ⚠️ Stub |
| `graph_memory.py` | 21 | Simple Graph Memory | ⚠️ Stub |
| `global_memory.py` | 6 | Global Memory | ⚠️ Stub |
| `memory_system.py` | 12 | Memory-Abstraktion | ⚠️ Stub |
| `memory_compressor.py` | 16 | Graph-Edge Compressor | ⚠️ Stub |
| `memory_rewriter.py` | 20 | Memory Rewriter | ⚠️ Stub |

### 3.10 Scheduler / Task / Routing

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `scheduler.py` | 46 | Task-Scheduler | ⚠️ Stub |
| `task_queue.py` | 16 | Task-Queue | ⚠️ Stub |
| `task_model.py` | 6 | Task-Model | ⚠️ Stub |
| `task_router.py` | 12 | Task-Router | ⚠️ Stub |
| `execution_governor.py` | 38 | Execution-Governor | ⚠️ Stub |
| `permission_engine.py` | 70 | Tool-Permission-Engine | ✅ Teilw. |
| `open_code_runner.py` | 12 | OpenCode Subprocess Wrapper | ⚠️ Stub |

### 3.11 Minimal-Varianten

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `minimal.py` | 29 | Minimales MUSCAL-Demo | ✅ |
| `minimal_core.py` | 28 | Minimaler Executor | ✅ |
| `minimal_loop.py` | 36 | Minimaler Autonomous Loop | ✅ |
| `minimal_mkc.py` | 6 | Minimaler MKC | ✅ |
| `minimal_memory.py` | 6 | Minimales Memory | ✅ |
| `minimal_rag.py` | 13 | Minimales RAG | ✅ |
| `minimal_fusion.py` | 27 | Minimaler Fusion Pipeline | ✅ |
| `minimal_evaluator.py` | 15 | Minimaler Evaluator | ⚠️ Stub |
| `minimal_feedback.py` | 9 | Minimales Feedback | ⚠️ Stub |
| `minimal_router.py` | 26 | Minimaler Router | ⚠️ Stub |
| `minimal_context.py` | 3 | Minimaler Context Builder | ⚠️ Stub |
| `minimal_graph_memory.py` | 13 | Minimales Graph Memory | ⚠️ Stub |
| `minimal_mcxf_memory.py` | 9 | Minimales MCXF Memory | ⚠️ Stub |

### 3.12 API Server

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `api_server.py` | 95 | FastAPI Control Plane (:8080) | ✅ |
| `runtime/main.py` | 63 | Flask API Server (:5001) | ✅ |
| `runtime/__init__.py` | 0 | Package Marker | ✅ |
| `runtime/database.py` | 201 | SQLite Schema (12 Tabellen, WAL, CQRS) | ✅ |
| `runtime/api/__init__.py` | 75 | Flask App Factory + Global State | ✅ |
| `runtime/api/chat.py` | 159 | `/api/chat` mit Slash-Commands + RAG | ✅ |
| `runtime/api/state.py` | 60 | `/api/state` + `/api/health` | ✅ |
| `runtime/api/events.py` | 76 | `/api/events` Query + Timeline Stats | ✅ |
| `runtime/api/tasks.py` | 48 | Task Submission + Governance | ✅ |
| `runtime/api/workers.py` | 93 | Worker Pause/Resume | ✅ |
| `runtime/api/models.py` | 35 | Model Registry CRUD | ✅ |
| `runtime/api/rag.py` | 32 | RAG Search + Reload | ✅ |
| `runtime/api/fs.py` | 48 | File System CRUD | ✅ |
| `runtime/api/admin.py` | 81 | Admin Operations (Snapshot, HUD) | ✅ |
| `runtime/api/handoff.py` | 16 | Session Handoff | ✅ |

### 3.13 Runtime Kernel

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `runtime/kernel/writer.py` | 145 | **WriterThread**: Serialisierte DB-Writes (CQRS) | ✅ |
| `runtime/kernel/scheduler.py` | 34 | Deterministisches L1-Routing | ✅ |
| `runtime/kernel/gate.py` | 108 | **Atomares Task-Gate**: Blockiert Unknowns | ✅ |
| `runtime/kernel/governance.py` | 257 | Token/Iteration/Cost-Limits | ✅ |
| `runtime/kernel/sanitizer.py` | 79 | Injection-Schutz + Payload-Masking | ✅ |
| `runtime/kernel/bootstrap.py` | 57 | Cold-Start Seed (Worker + Routing) | ✅ |
| `runtime/kernel/rag_index.py` | 155 | Ollama-Embedding + Cosine-RAG + Disk-Cache | ✅ |
| `runtime/kernel/chroma_index.py` | 148 | ChromaDB Vector Index + Chunking | ✅ |
| `runtime/kernel/fs_api.py` | 95 | Sandboxed File System API | ✅ |
| `runtime/kernel/docs/alita_wissen.md` | — | Knowledge Base für RAG | ✅ |

### 3.14 Runtime LLM + Observation

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `runtime/llm/client.py` | 74 | Ollama HTTP-Client (urllib, async futures) | ✅ |
| `runtime/llm/models.py` | 60 | 3 spezialisierte LLM-Worker (Qwen/R1/Smol) | ✅ |
| `runtime/observation/loop.py` | 113 | **Observation Loop**: Stuck Worker, Drift, Governance | ✅ |

### 3.15 Runtime Optimizer

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `runtime/optimizer/pipeline.py` | 172 | **OptimizerPipeline**: Orchestriert alle Passes | ✅ |
| `runtime/optimizer/graph.py` | 160 | **ExecutionDAG**: Topologisches Sort, DAGNode | ✅ |
| `runtime/optimizer/base_pass.py` | 114 | ABC für Optimizer-Passes (hash, verify, DAG) | ✅ |
| `runtime/optimizer/dead_node.py` | 40 | Dead Code Elimination Pass | ✅ |
| `runtime/optimizer/node_fusion.py` | 99 | Tool-Fusion Pass (5 Regeln) | ✅ |
| `runtime/optimizer/parallelization.py` | 29 | Parallel Layer Assignment Pass | ✅ |
| `runtime/optimizer/cost_optimizer.py` | 91 | **CostVector**: 9-dimensionale Kosten | ✅ |
| `runtime/optimizer/report.py` | 122 | OptimizationReport Dataclass | ✅ |
| `runtime/optimizer/verification.py` | 106 | Full Pipeline Verification | ✅ |

### 3.16 Frontend (React JSX)

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `frontend/Dashboard.jsx` | 35 | Haupt-Dashboard | ⚠️ Proto |
| `frontend/GraphView.jsx` | 23 | Graph-Visualisierung (SVG) | ⚠️ Proto |
| `frontend/NodePanel.jsx` | 11 | Node-Liste | ⚠️ Proto |
| `frontend/TraceViewer.jsx` | 9 | Trace-Logs | ⚠️ Proto |
| `frontend/TaskBox.jsx` | 20 | Task-Eingabe | ⚠️ Proto |
| `frontend/Explain.jsx` | 24 | Decision Autopsy UI | ⚠️ Proto |
| `frontend/MetaExplain.jsx` | 30 | Meta-Reasoning UI | ⚠️ Proto |
| `frontend/Replay.jsx` | 22 | Replay-UI | ⚠️ Proto |

### 3.17 Optimizer (Root-level, ältere Version)

| Datei | Zeilen | Rolle | Status |
|-------|--------|-------|--------|
| `optimized_executor.py` | — | Optimierter Executor | ⚠️ Fehlt |
| `execution_graph.py` | — | Execution-Graph | ⚠️ Fehlt |
| `dead_code_elimination.py` | — | DCE-Pass | ⚠️ Fehlt |
| `tool_fusion_pass.py` | — | Fusion-Pass | ⚠️ Fehlt |
| `cost_model.py` | — | Cost-Model | ⚠️ Fehlt |
| `parallelization_pass.py` | — | Parallel-Pass | ⚠️ Fehlt |
| `graph_optimizer.py` | — | Graph-Optimizer | ⚠️ Fehlt |
| `self_optimizing_compiler.py` | — | Self-Optimizing Compiler | ⚠️ Fehlt |

---

## 4. KERNMODULE IM DETAIL

### 4.1 `kernel.py` — Hauptorchestrator (414 Zeilen)

**Klasse:** `MuscalKernel`

Der zentrale Orchestrator, der alle Subsysteme importiert und die vollständige Pipeline steuert.

```python
class MuscalKernel:
    def __init__(self, debugger=None):
        self.modules = {
            "mkc": MKCModule(self),
            "rag": RAGModule(self),
            "bridge": BridgeModule(self),
            "mel": MELModule(self),
            "feedback": FeedbackModule(self),
            "memory": MemoryModule(self),
            "system": SystemModule(self),
            "graph": GraphState(),
        }

    def run(self, user_input: str) -> KernelResult:
        # 1. RAG Kontext abrufen
        context = self.modules["rag"].run(user_input)
        # 2. MKC kompilieren
        mcxf = self.modules["mkc"].run(context)
        # 3. MCXF mit Context anreichern
        enriched = self.modules["rag"].run(mcxf)
        # 4. Bridge: MCXF → Tool-Pläne
        plan = self.modules["bridge"].run(enriched)
        # 5. MEL: Ausführung
        results = self.modules["mel"].run(plan)
        # 6. Feedback generieren
        feedback = self.modules["feedback"].run(results)
        # 7. Speichern
        memory_id = self.modules["memory"].run(feedback)
        # 8. GraphState aktualisieren
        self.modules["graph"].record(mcxf, plan, results, feedback)
        # 9. Ergebnis
        return KernelResult(mcxf, plan, results, feedback, memory_id)
```

**Module im Detail:**

| Modul | Klasse | Aufgabe |
|-------|--------|---------|
| `MKCModule` | `MKCModule(kernel)` | Ruft `mkc()` auf, gibt MCXF-Dict zurück |
| `RAGModule` | `RAGModule(kernel)` | Ruft `rag.retrieve()` + `rag.enrich()` |
| `BridgeModule` | `BridgeModule(kernel)` | Ruft `bridge.match_tool()` für jedes MCXF-Triple |
| `MELModule` | `MELModule(kernel)` | Ruft `mel.execute()` mit Tool-Plan |
| `FeedbackModule` | `FeedbackModule(kernel)` | Ruft `feedback.analyze()` |
| `MemoryModule` | `MemoryModule(kernel)` | Ruft `memory.store()` |
| `SystemModule` | `SystemModule(kernel)` | System-Routing (browser/desktop) |
| `GraphState` | `GraphState()` | Passiver Observer, tracked alle Stages |

**KernelResult:**
```python
@dataclass
class KernelResult:
    mcxf: dict          # {decisions, tasks, architecture, constraints, open_questions}
    plan: dict          # Gematchte Tool-Pläne
    results: list       # Ausführungsergebnisse
    feedback: dict      # Feedback-Analyse
    memory_id: int      # SQLite-ID
```

### 4.2 `mkc.py` + `mkc_rules.py` — MKC Compiler (102 + 135 Zeilen)

**Funktion:** `mkc(user_input: str) -> dict`

Regelbasierte Klassifikation von Benutzereingaben in MCXF-Struktur.

```python
SIGNAL_RULES = {
    "decisions": ["entscheid", "will", "soll", "choose", "decide", "select"],
    "tasks": ["erstell", "schreib", "create", "write", "implement", "build"],
    "architecture": ["architektur", "structure", "design", "pattern", "layer"],
    "constraints": ["nicht", "muss", "darf", "must", "must not", "never"],
    "glossary": ["definiere", "define", "nennen", "call", "term"],
}
```

**Pipeline:**
1. `classify(text)` → SIGNAL_RULES-Matching → initiale MCXF-Kategorien
2. `ensure_mcxf(mcxf)` → Struktur validieren (5 Felder müssen existieren)
3. Confidence-Berechnung pro Kategorie

### 4.3 `bridge.py` — Tool-Matching (171 Zeilen)

**Funktion:** `match_tool(triple: dict) -> ToolMatch`

9 Regex-Matcher, die natürliche Sprache in Tool-Aufrufe übersetzen:

```python
MATCHERS = [
    ("filesystem.write", r"(write|create|save|speicher|erstell).*(file|datei)"),
    ("filesystem.read", r"(read|lade|öffne|open).*(file|datei)"),
    ("filesystem.delete", r"(delete|lösche|remove).*(file|datei)"),
    ("math.add", r"(add|sum|plus|addiere|summiere)"),
    ("math.subtract", r"(subtract|minus|subtrahiere)"),
    ("console.print", r"(print|ausgabe|zeige|display|show)"),
    ("browser.open", r"(open|öffne|navigate|gehe zu).*(url|http|https|seite)"),
    ("browser.click", r"(click|klicke|drücke)"),
    ("browser.type", r"(type|schreibe|eingabe|tippe)"),
]
```

**Return:**
```python
@dataclass
class ToolMatch:
    tool: str          # z.B. "filesystem.write"
    confidence: float  # 0.0 - 1.0
    params: dict       # Extrahierte Parameter
    raw: str           # Originaltext
```

### 4.4 `mel.py` + `tools.py` — Execution Layer (41 + 99 Zeilen)

**Funktion:** `execute(plan: dict) -> list`

Dispatch an `TOOL_REGISTRY` oder `SystemAgentRuntime`.

```python
TOOL_REGISTRY = {
    "math.add": lambda a, b: {"result": a + b},
    "console.print": lambda text: {"printed": text},
    "filesystem.write": lambda path, content: write_file(path, content),
}
```

**15 Tool-Schemas** in `tools.py` definiert (inkl. Input/Output-Validierung).

### 4.5 `runtime/kernel/writer.py` — WriterThread (145 Zeilen)

**CQRS-Prinzip:** Nur der WriterThread schreibt in die Datenbank.

```python
class WriterThread(threading.Thread):
    def __init__(self):
        self.queue = queue.Queue()
        self.futures = {}

    def write(self, table, data) -> Future:
        future = Future()
        self.queue.put((table, data, future))
        return future

    def run(self):
        while self.running:
            table, data, future = self.queue.get()
            with self.lock:
                self.conn.execute(f"INSERT INTO {table} VALUES ...")
                future.set_result(cursor.lastrowid)
```

### 4.6 `runtime/kernel/gate.py` — Atomares Task-Gate (108 Zeilen)

**Prüfungen (atomar mit BEGIN IMMEDIATE):**
1. **Governance-Limits** → max_iterations/tokens/cost
2. **Routing** → Ist ein Worker verfügbar?
3. **Blocking Unknowns** → Unbekannte Tasks blockieren, bis ein Admin sie freigibt

```python
class Gate:
    def check(self, task_type: str, payload: dict) -> GateResult:
        with self.lock:
            # 1. Governance prüfen
            if not self.governance.check_limits():
                return GateResult.DENIED("Governance limit exceeded")
            # 2. Routing prüfen
            worker = self.scheduler.route(task_type)
            if not worker:
                return GateResult.DENIED("No worker available")
            # 3. Unknown-Check
            if task_type in self.blocking_unknowns:
                return GateResult.BLOCKED("Unknown task type")
            # 4. Task atomisch starten
            return GateResult.PASS(worker)
```

### 4.7 `runtime/governance.py` — Governance Engine (257 Zeilen)

**Limits:**
- `MAX_ITERATIONS = 25` (Tasks pro Session)
- `MAX_TOKENS = 100000` (Gesamt-Token)
- `MAX_COST = 1000` (Simulierte Kosten)
- `HUMAN_IN_LOOP_ACTIONS = ["filesystem.write", "shell.exec"]`

```python
class Governance:
    def record_usage(self, worker_id, tokens, cost):
        self.usage[worker_id] += tokens
        self.total_cost += cost

    def check_limits(self, worker_id) -> bool:
        return self.usage[worker_id] < self.max_tokens
```

### 4.8 `runtime/kernel/scheduler.py` — L1 Router (34 Zeilen)

**Deterministisches Routing** — kein LLM, <1µs

```python
class Scheduler:
    def __init__(self):
        self.routing_policy = {}  # task_type -> worker_id

    def route(self, task_type: str) -> str:
        return self.routing_policy.get(task_type, "unknown")
```

### 4.9 `runtime/kernel/rag_index.py` — RAG Index (155 Zeilen)

```python
class RAGIndex:
    def __init__(self):
        self.documents = self._load_knowledge_base()
        self.cache = self._load_cache()

    def search(self, query: str, top_k=3):
        query_emb = self._embed(query)
        scores = [cosine_similarity(query_emb, doc["embedding"])
                  for doc in self.documents]
        return [self.documents[i] for i in argsort(scores)[:top_k]]
```

### 4.10 `runtime/kernel/chroma_index.py` — ChromaDB Index (148 Zeilen)

```python
class ChromaIndex:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="kernel/data/chroma/")
        self.collection = self.client.get_or_create_collection("muscal")

    def search(self, query: str, top_k=5):
        return self.collection.query(query_texts=[query], n_results=top_k)
```

### 4.11 `runtime/observation/loop.py` — Observation Loop (113 Zeilen)

**L2 Monitor:** Tickt alle 5 Sekunden und prüft:

```python
class ObservationLoop:
    def tick(self):
        # 1. Blocking Unknowns prüfen
        unknowns = self.gate.get_blocking_unknowns()
        # 2. Stuck Workers (>5 min running)
        stuck = [w for w in self.workers if w.running_time > 300]
        # 3. Confidence Drift (>0.3 variance)
        drift = [w for w in self.workers if w.confidence_variance > 0.3]
        # 4. Governance Violations
        violations = self.governance.get_violations()
        # 5. Ollama Health
        if not self.llm_health.ping():
            self.event_bus.emit("observation.llm_down")
```

### 4.12 `runtime/optimizer/` — Optimizer Pipeline

**Architektur:**

```
ExecutionDAG
    │
    ▼
DeadCodeElimination ────► Entfernt ungenutzte Nodes
    │
    ▼
NodeFusion ──────────────► Kombiniert validate+write, browser.open+click
    │
    ▼
ParallelizationPass ─────► Topologisches Sort + Layer-Zuweisung
    │
    ▼
CostVector ──────────────► 9-dim. Kosten (cpu, ram, latency, tokens, ...)
    │
    ▼
Verification ────────────► DAG-Validierung, Hash-Check, Replay-Kompatibilität
    │
    ▼
OptimizationReport
```

**CostVector (9 Dimensionen):**

```python
@dataclass
class CostVector:
    cpu: float = 1.0
    ram: float = 1.0
    latency: float = 1.0
    tokens: int = 0
    retries: int = 0
    estimated_cost: float = 0.0
    risk: float = 0.0
    tool_calls: int = 0
    graph_complexity: int = 0
```

### 4.13 `cognitive_diff.py` — 5D Diff-Engine (336 Zeilen)

Vergleicht zwei MCXF-Zustände in 5 Dimensionen:

| Dimension | Skala | Erkenntnis |
|-----------|-------|------------|
| **Logical** | REJECT / ACCEPT | Logische Widersprüche |
| **Behavioral** | IDENTICAL / SIMILAR / DIVERGENT | Verhaltensänderungen |
| **Architectural** | SAME / MODIFIED / RESTRUCTURED | Strukturänderungen |
| **Risk** | 0.0 - 1.0 | Risikobewertung |
| **Performance** | IMPROVED / DEGRADED / STABLE | Performance-Trend |

**Empfehlungen:**
- `REJECT` bei CRITICAL Risk
- `REVIEW` bei HIGH Risk
- `ROLLBACK` bei negativem Trend
- `MERGE` bei cleanem Diff

---

## 5. DATENMODELL

### 5.1 Zentrale Dataclasses (`schema.py`)

```python
@dataclass
class KernelResult:
    mcxf: dict
    plan: dict
    results: list
    feedback: dict
    memory_id: int

@dataclass
class MCXFTriple:
    subject: str
    predicate: str
    object: str
    confidence: float

@dataclass
class ToolMatch:
    tool: str
    confidence: float
    params: dict
    raw: str

@dataclass
class ExecutionStep:
    tool: str
    params: dict
    status: str  # pending | running | success | failed | timeout
    result: any
    duration: float
```

### 5.2 SQLite Schema (`runtime/database.py`) — 12 Tabellen

| Tabelle | Zweck |
|---------|-------|
| `events` | Alle System-Events (event_id, type, payload, timestamp) |
| `workers` | Worker-Registry (worker_id, name, model, status) |
| `tasks` | Task-Queue (task_id, type, status, worker_id, created_at) |
| `decisions` | Entscheidungen (decision_id, task_id, action, reason) |
| `snapshots` | DB-Snapshots (snapshot_id, timestamp, state) |
| `routing_policy` | Task-Type → Worker-Mapping |
| `kernel_config` | Schlüssel-Wert-Konfiguration |
| `trigger_state` | Auto-Trigger-Zustand |
| `intent_documents` | Intents für RAG |
| `intent_unknowns` | Blockierte Unknown-Intents |
| `memory` | Memory-Einträge |
| `governance_log` | Governance-Verstöße |

### 5.3 Events

```python
@dataclass
class Event:
    event_id: str      # UUID
    type: str          # z.B. "task.submitted", "kernel.initialized"
    payload: dict      # Beliebiges JSON
    timestamp: str     # ISO 8601
    priority: int      # 0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL
```

---

## 6. API-REFERENZ

### 6.1 Flask API (:5050) — `runtime/api/`

| Methode | Pfad | Input | Response |
|---------|------|-------|----------|
| GET | `/` | — | Dashboard HTML |
| GET | `/ide` | — | IDE HTML |
| GET | `/api/state` | — | System-Status (Events, Workers, Gate, GPU, Ollama) |
| GET | `/api/health` | — | `{"status": "ok"}` |
| POST | `/api/chat` | `{"message": "..."}` | Chat-Antwort + RAG-Kontext |
| GET | `/api/events` | `?type=&worker_id=&limit=` | Gefilterte Events |
| GET | `/api/events/stats` | — | Timeline-Statistiken |
| POST | `/api/task` | `{"type": "…", "payload": {…}}` | Task-ID + Status |
| GET | `/api/governance` | — | Governance-Limits + Usage |
| POST | `/api/governance/reset` | — | Limits zurücksetzen |
| POST | `/api/unknown/<id>/resolve` | `{"action": "allow"}` | Unknown freigeben |
| POST | `/api/worker/<id>/pause` | — | Worker pausieren |
| POST | `/api/worker/<id>/resume` | — | Worker fortsetzen |
| POST | `/api/workers/pause` | — | Alle Worker pausieren |
| POST | `/api/workers/resume` | — | Alle Worker fortsetzen |
| GET | `/api/models` | — | Modelle auflisten |
| POST | `/api/models` | `{"name": "…", "endpoint": "…"}` | Modell registrieren |
| DELETE | `/api/models/<name>` | — | Modell löschen |
| GET | `/api/models/<name>/health` | — | Modell-Health |
| POST | `/api/rag/search` | `{"query": "…", "top_k": 3}` | RAG-Suchergebnisse |
| POST | `/api/rag/reload` | — | Wissen neu laden |
| POST | `/api/rag/chroma/search` | `{"query": "…"}` | ChromaDB-Suche |
| POST | `/api/rag/chroma/bootstrap` | — | ChromaDB initialisieren |
| GET | `/api/fs/list` | `?path=` | Dateien auflisten |
| GET | `/api/fs/read` | `?path=` | Datei lesen |
| POST | `/api/fs/write` | `{"path": "…", "content": "…"}` | Datei schreiben |
| POST | `/api/fs/delete` | `{"path": "…"}` | Datei löschen |
| POST | `/api/snapshot` | — | Snapshot erstellen |
| POST | `/api/compact` | — | DB kompaktieren |
| GET | `/api/replay` | — | Replay-Status |
| GET | `/api/benchmark` | — | Benchmark starten |
| POST | `/api/hud-action` | `{"action": "screenshot"}` | HUD-Aktion |
| GET | `/api/handoff` | — | Session-State als Markdown |

### 6.2 FastAPI (:8080) — `api_server.py`

| Methode | Pfad | Input | Response |
|---------|------|-------|----------|
| POST | `/task` | `{"input": "…"}` | Swarm-Execution-Results |
| GET | `/nodes` | — | `[{"id": "A"}, …]` |
| GET | `/graph` | — | `{"nodes": […], "edges": […]}` |
| GET | `/replay/{node_id}` | — | Lineage-Pfad |
| GET | `/explain/{node_id}` | — | `{analysis, explanation}` |
| GET | `/meta-explain/{node_id}` | — | `{original, critique, refined}` |
| GET | `/self-improve/{node_id}` | — | `{evaluation, metrics, performance}` |
| WS | `/stream` | — | Heartbeat-Events |
| WS | `/graph/stream` | — | Graph-Updates |

---

## 7. INTEGRATIONSKARTE (Cross-Projekt)

### 7.1 Feature-Übernahme aus anderen Projekten

Nach Priorität gestaffelt. Jedes Feature wird mit Quelle, Komplexität und Implementierungshinweis beschrieben.

#### P1 — Kritische Lücken

| # | Feature | Quelle | Dateien | Komplexität | Implementierung |
|---|---------|--------|---------|-------------|----------------|
| 1 | **Async IPC + Process Manager** | `MUSCAL/code/kernel/` | `ipc_server.py`, `ipc_client.py`, `ipc_protocol.py`, `process_manager.py` | Mittel | Unix Socket + JSON-Protokoll. Agents als echte OS-Prozesse spawnen. Heartbeat-Monitor mit 30s Timeout, Auto-Restart (3x). Ersetzt `message_broker.py` + `distributed_*.py` Stubs. |
| 2 | **MAS Scheduler** (Multi-Strategy) | `ALITAGPT/muscal-mas/scheduler/` | `mas.py`, `dag_bridge.py` | Mittel | Strategy-Selection: single/parallel/cascade/ensemble/dag + Cost-Scoring. Ersetzt `scheduler.py` + `task_router.py`. |
| 3 | **Async EventBus** (Wildcards) | `MUSCAL/code/kernel/` | `event_bus.py` | Einfach | Topic-Wildcards (`task.*`), `asyncio.Lock`, UUID-Events. Kann parallel zum sync EventBus existieren. |
| 4 | **RAG Index + ChromaDB** | `ALITA 0.9/kernel/` | `rag_index.py`, `chroma_index.py` | Einfach | Ollama-Embedding + Cosine-Search + Disk-Cache. Direkter Port, ersetzt `rag.py` + `rag_minimal.py`. |
| 5 | **Process-Level Agent SDK** | `MUSCAL/code/agents/` | `base_agent.py`, `agent_sdk.py` | Einfach | Lifecycle: connect → register → heartbeat → run → shutdown. Context Manager (`async with`). |

#### P2 — Produktionshärte

| # | Feature | Quelle | Komplexität | Implementierung |
|---|---------|--------|-------------|----------------|
| 6 | **MCXF Compiler + Replay** | `ALITAGPT/muscal-mas/compiler/` | Mittel | Hash-basierte Replay-Verifikation. Ergänzt `mcxf_*.py`. |
| 7 | **Observation Loop** | `ALITA 0.9/runtime/observation/` | Einfach | 5s-Tick: Unknowns, Stuck Workers, Drift, Governance. Port nach `runtime/observation/loop.py`. |
| 8 | **Streamlit Dashboard** | `ALITAGPT/muscal-mas/dashboard/` | Einfach | 4 Tabs: Metrics, Worker Graph, MCXF Inspector, Persona. API-URL auf MUSCAL CORE umbiegen. |
| 9 | **YAML Workflow Engine** | `MUSCAL/code/runtime/` | Mittel | DAG-Steps mit `depends_on`/`parallel_with`. Workflows in YAML definieren. |
| 10 | **SQLite DAG** | `ALITAGPT/muscal/core/` | Einfach | Thread-sichere DAG-Persistenz mit WAL. Ersetzt `graph_memory.py`. |
| 11 | **Byzantine Consensus** | `ALITAGPT/muscal/consensus/` | Mittel | PBFT-simplified: FaultModel, Quorum, Gossip. Ersetzt `consensus_engine.py`. |

#### P3 — Feature-Reichweite

| # | Feature | Quelle | Komplexität | Implementierung |
|---|---------|--------|-------------|----------------|
| 12 | **Policy Evolution Engine** | `ALITAGPT/muscal-mas/policy/` | Mittel | Thompson Sampling + Bayesian Weights + Reputation + Hierarchical Routing |
| 13 | **Snapshot Manager** | `ALITA 0.9/` | Einfach | Threshold-basierte Snapshots + Kompaktion |
| 14 | **WebSocket EventDaemon** | `ALITA 0.9/` | Mittel | Echtzeit-Push auf :9090, integriert mit EventBus |
| 15 | **Agent Pipeline** | `ALITAGPT/muscal/agents/` | Einfach | FilterStage → TransformStage → EnrichStage → LogStage |
| 16 | **Dual-Judge System** | `ALITAGPT/muscal-mas/judge/` | Einfach | Lösung A vs B auf correctness/clarity/efficiency |
| 17 | **MREIL Scoring** | `ALITAGPT/muscal-mas/core/` | Einfach | Weighted Composite: Korrektheit + Klarheit + Effizienz - Latenz/Token-Penalties |
| 18 | **Orchestrator Agent** | `MUSCAL/code/agents/` | Einfach | Routing Depth Limit (5), Cycle Prevention |

#### P4 — Vision

| # | Feature | Quelle | Komplexität | Implementierung |
|---|---------|--------|-------------|----------------|
| 19 | **MUSCAL IDE** (React/TS) | `BROWSEROS/CLAUDE_FAV_GUI_VSCODE/` | Hoch | Vollständiges Frontend mit API-Client, WebSocket, 12 Panels, Orchestrator |
| 20 | **Self-Improvement Loop** | `ALITAGPT/muscal/reflection/` | Mittel | Test → Analyze → Fix → Repeat mit DiffManager |

### 7.2 Code-Architektur für Integrationen

Jede Übernahme folgt diesem Muster:

```
1. QUELLCODE identifizieren (siehe Tabelle oben)
2. IMPORT-PATHS anpassen (von Projektspezifisch → MUSCAL CORE)
3. DATENTYPEN angleichen (Event vs EventMessage, Task vs MCTask)
4. EXISTIERENDE STUBS ersetzen oder ergänzen
5. TESTS schreiben (vorhandene Testpatterns aus ALITAGPT übernehmen)
```

**Beispiel: Integration des Async IPC aus MUSCAL v0.2**

```python
# 1. ipc_server.py kopieren nach runtime/ipc/ipc_server.py
# 2. Import anpassen: from runtime.ipc.ipc_protocol import MessageType
# 3. Event-Typen mappen: ipc_protocol.Event ↔ schema.Event
# 4. In runtime/kernel/daemon.py: IPC Server beim Boot starten
# 5. Tests aus MUSCAL/tests/test_ipc.py übernehmen
```

---

## 8. KONFIGURATION

### 8.1 `config.py` (20 Zeilen)

```python
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "runtime" / "muscal.db"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODELS = ["qwen2.5:1.5b", "deepseek-r1:8b", "smollm2:360m"]
DASHBOARD_PORT = 8501
API_PORT = 5050
FASTAPI_PORT = 8080
SNAPSHOT_THRESHOLD = 100  # Events bis Snapshot
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
```

### 8.2 `os_config.py` (74 Zeilen) — Deployment-Modi

```python
DEPLOYMENT_MODES = {
    "local_dev": {
        "ollama_required": False,     # LLM-Fallback erlaubt
        "log_level": "DEBUG",
        "auto_start_agents": True,
        "persistence": True,
    },
    "production": {
        "ollama_required": True,
        "log_level": "INFO",
        "auto_start_agents": True,
        "persistence": True,
    },
    "simulation": {
        "ollama_required": False,
        "log_level": "INFO",
        "auto_start_agents": False,   # Keine echten Agents
        "persistence": False,
    },
}
```

### 8.3 Umgebungsvariablen

| Variable | Default | Zweck |
|----------|---------|-------|
| `OLLAMA_HOST` | `localhost` | Ollama-Server |
| `MUSCAL_PORT` | `5050` | Flask API Port |
| `MUSCAL_FASTAPI_PORT` | `8080` | FastAPI Port |
| `MUSCAL_MODE` | `local_dev` | Deployment-Modus |
| `MUSCAL_DB_PATH` | `./runtime/muscal.db` | Datenbank-Pfad |

---

## 9. ABHÄNGIGKEITEN

### 9.1 Core (stdlib only — 0 externe Deps)

`sqlite3`, `json`, `re`, `time`, `os`, `sys`, `typing`, `dataclasses`, `enum`, `threading`, `queue`, `concurrent.futures`, `subprocess`, `hashlib`, `abc`, `uuid`, `copy`

### 9.2 API Server (`requirements_api.txt`)

| Package | Version | Zweck |
|---------|---------|-------|
| `fastapi` | >=0.100.0 | Control Plane API |
| `uvicorn` | >=0.23.0 | ASGI Server |
| `websockets` | >=11.0 | WebSocket Support |

### 9.3 Flask Runtime

| Package | Version | Zweck |
|---------|---------|-------|
| `flask` | >=3.0 | REST API |
| `flask-cors` | — | CORS |
| `streamlit` | >=1.58 | Dashboard |
| `requests` | — | HTTP Client |
| `aiosqlite` | >=0.19 | Async SQLite (EventDaemon) |

### 9.4 Optional

| Package | Zweck | Verwendung in |
|---------|-------|---------------|
| `playwright` | Browser-Automation | `browser_engine.py` |
| `pyautogui` | Desktop-Automation | `desktop_tools.py` |
| `chromadb` | Vector-Database | `runtime/kernel/chroma_index.py` |
| `numpy` + `faiss` + `sentence-transformers` | Vector-Suche | `rag_vector.py`, `embedder.py` |
| `ollama` (extern) | LLM-Backend | `runtime/llm/`, `runtime/kernel/rag_index.py` |

---

## 10. BEKANNTE PROBLEME

### 10.1 Kritisch

| # | Problem | Betroffene Dateien | Auswirkung |
|---|---------|-------------------|------------|
| 1 | **Keine Tests** (0 Test-Dateien) | Alle | Jede Änderung kann brechen |
| 2 | **~45% Stubs** (~80 Dateien <20 Zeilen) | Consensus, Distributed, Evolution, Vision, Scheduler | Feature-Versprechen nicht eingelöst |
| 3 | **Global Mutable State** | `memory.py` (global `conn`) | Nicht thread-save |
| 4 | **Keine DB-Migrationen** | `runtime/database.py` | Schema-Änderungen zerstören Daten |
| 5 | **Keine CI/CD** | — | Keine automatisierte Qualitätssicherung |

### 10.2 Mittel

| # | Problem | Details |
|---|---------|---------|
| 6 | Kein Auth/Authorization | Alle API-Endpoints offen |
| 7 | Kein Rate-Limiting | Kein Request-Throttling |
| 8 | Kein Caching (Redis) | Jeder Request triggert DB/LLM |
| 9 | Frontend nicht buildbar | React JSX ohne Bundler-Konfiguration |
| 10 | LLM nur via Ollama | Kein OpenAI/Anthropic-Support |
| 11 | Kein Streaming | Keine progressiven Responses |

### 10.3 Niedrig

| # | Problem | Details |
|---|---------|---------|
| 12 | JSON-File ohne Locking | `mcxf_memory.json` nicht concurrent-save |
| 13 | Kein Backup/Restore | Keine Snapshot-Wiederherstellung |
| 14 | Kein Health-Endpoint für FastAPI | Nur Flask hat `/api/health` |
| 15 | Magic Numbers in `mkc_rules.py` | Confidence-Werte hardcodiert |

---

## 11. ERWEITERUNGSPUNKTE

### 11.1 Neues Tool hinzufügen

```python
# 1. Tool-Funktion implementieren (tools.py oder neue Datei)
def my_tool(param1: str, param2: int) -> dict:
    return {"status": "ok", "result": ...}

# 2. In TOOL_REGISTRY eintragen
TOOL_REGISTRY["my_tool"] = my_tool

# 3. Schema in TOOL_SCHEMAS definieren
TOOL_SCHEMAS["my_tool"] = {
    "description": "Mein neues Tool",
    "input": {"param1": "string", "param2": "integer"},
    "output": {"status": "string", "result": "any"},
}

# 4. Matcher in bridge.py ergänzen
MATCHERS.append(("my_tool", r"(my_keyword|mein_schlagwort)"))
```

### 11.2 Neuen Optimizer-Pass hinzufügen

```python
# 1. Neue Pass-Klasse (runtime/optimizer/my_pass.py)
class MyPass(OptimizerPass):
    def optimize(self, dag: ExecutionDAG) -> ExecutionDAG:
        # Transformation
        return dag

# 2. In pipeline.py registrieren
class OptimizerPipeline:
    def __init__(self):
        self.passes = [
            DeadCodeElimination(),
            NodeFusion(),
            MyPass(),           # ← neuer Pass
            ParallelizationPass(),
        ]
```

### 11.3 Neuen Agent-Typ hinzufügen

```python
# 1. Agent-Klasse (agents/my_agent.py)
class MyAgent(BaseAgent):
    def evaluate(self, event: Event) -> dict:
        # Logik
        return {"action": "process", "confidence": 0.9}

# 2. Im AgentRegistry registrieren
registry.register("my_agent", MyAgent())

# 3. Routing-Regel in scheduler.py ergänzen
self.routing_policy["my_task_type"] = "my_agent"
```

### 11.4 Neue API-Route hinzufügen

```python
# Flask (runtime/api/meine_route.py)
from flask import Blueprint
bp = Blueprint("meine", __name__)

@bp.route("/api/meine-route")
def meine_route():
    return {"status": "ok"}

# In runtime/api/__init__.py registrieren
app.register_blueprint(bp)
```

---

## 12. EINSTIEGSPUNKTE

| Befehl | Beschreibung |
|--------|-------------|
| `python3 main.py` | Einfacher REPL-Modus |
| `python3 main_boot.py` | **Haupt-Einstieg**: OS-Modus mit CLI |
| `python3 muscal_loop.py` | Autonomer LLM-Loop |
| `python3 runtime/main.py` | Flask API Server (:5050) |
| `python3 api_server.py` | FastAPI Control Plane (:8080) |
| `python3 dashboard.py` | Streamlit Dashboard (:8501) |
| `docker compose up` | Containerisiert (Port 8000) |

---

## 13. PROJEKT-STATUS (Zusammenfassung)

```
Gesamt:    ~225 Dateien, ~13.182 Lines
Python:    ~184 Dateien, ~10.744 Lines
Docs:       6 .md-Dateien, ~1.387 Lines
Frontend:   7 JSX-Dateien, ~154 Lines

✅ Working:   Core Pipeline, OS Layer, Optimizer, Cognitive Diff,
              Browser/Desktop Tools, API Server, Safety System
⚠️ Stubs:     ~80 Dateien (Consensus, Distributed, Evolution,
              Causality, Vision, Memory-Subsysteme)
❌ Fehlt:     Tests, CI/CD, DB-Migrationen, Auth, Frontend-Build
```

---

## 14. SYSTEM SPINE & LAYER GOVERNANCE

### 14.1 System Spine — Zentraler Event-Validierungskern

Das System hat keinen einzelnen zentralen Datenflusskern. Dies wird durch die **System Spine** behoben — ein Modul, das *alle* Event-Transitionen validiert und Cross-Layer-Chaos verhindert.

#### Konzept: `system_spine.py`

```python
# system_spine.py — MUSCAL System Spine

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

class Layer(Enum):
    STORAGE      = 0   # L0
    RUNTIME      = 1   # L1  — Runtime Kernel
    COGNITIVE    = 2   # L2  — Cognitive Kernel
    CONTROL      = 3   # L3  — Control Kernel
    OBSERVABILITY = 4  # L4  — Observability Kernel
    API          = 5   # L5  — API Layer
    FRONTEND     = 6   # L6  — UI Layer

class TransitionVerdict(Enum):
    ALLOWED      = auto()
    FORBIDDEN    = auto()
    NEEDS_BRIDGE = auto()  # Erlaubt, aber nur durch explizite Bridge

@dataclass
class SpineEvent:
    event_id: str
    event_type: str
    origin_layer: Layer
    payload: dict
    timestamp: float
    target_layer: Optional[Layer] = None

    def transition_to(self, target: Layer) -> TransitionVerdict:
        return SystemSpine.validate_transition(self.origin_layer, target)

class SystemSpine:
    """Zentrale Event-Validierung. Singleton."""

    _instance = None

    # Layer-Transition-Matrix
    # Zeile = origin, Spalte = target
    # ALLOWED / FORBIDDEN / NEEDS_BRIDGE
    TRANSITION_MATRIX = {
        Layer.STORAGE: {
            Layer.RUNTIME:      TransitionVerdict.ALLOWED,
            Layer.COGNITIVE:    TransitionVerdict.FORBIDDEN,
            Layer.CONTROL:      TransitionVerdict.FORBIDDEN,
            Layer.OBSERVABILITY: TransitionVerdict.NEEDS_BRIDGE,
        },
        Layer.RUNTIME: {
            Layer.STORAGE:      TransitionVerdict.ALLOWED,
            Layer.COGNITIVE:    TransitionVerdict.ALLOWED,
            Layer.CONTROL:      TransitionVerdict.ALLOWED,
            Layer.OBSERVABILITY: TransitionVerdict.ALLOWED,
        },
        Layer.COGNITIVE: {
            Layer.RUNTIME:      TransitionVerdict.ALLOWED,
            Layer.STORAGE:      TransitionVerdict.NEEDS_BRIDGE,
            Layer.CONTROL:      TransitionVerdict.ALLOWED,
            Layer.OBSERVABILITY: TransitionVerdict.ALLOWED,
        },
        Layer.CONTROL: {
            Layer.RUNTIME:      TransitionVerdict.ALLOWED,
            Layer.COGNITIVE:    TransitionVerdict.ALLOWED,
            Layer.STORAGE:      TransitionVerdict.NEEDS_BRIDGE,
            Layer.OBSERVABILITY: TransitionVerdict.ALLOWED,
        },
        Layer.OBSERVABILITY: {
            Layer.STORAGE:      TransitionVerdict.ALLOWED,
            Layer.RUNTIME:      TransitionVerdict.FORBIDDEN,
            Layer.COGNITIVE:    TransitionVerdict.FORBIDDEN,
            Layer.CONTROL:      TransitionVerdict.FORBIDDEN,
        },
        Layer.API: {
            Layer.OBSERVABILITY: TransitionVerdict.ALLOWED,
            Layer.CONTROL:      TransitionVerdict.NEEDS_BRIDGE,
            Layer.COGNITIVE:    TransitionVerdict.FORBIDDEN,
            Layer.RUNTIME:      TransitionVerdict.FORBIDDEN,
            Layer.STORAGE:      TransitionVerdict.FORBIDDEN,
        },
        Layer.FRONTEND: {
            Layer.API:          TransitionVerdict.ALLOWED,
            Layer.OBSERVABILITY: TransitionVerdict.ALLOWED,
            Layer.CONTROL:      TransitionVerdict.FORBIDDEN,
            Layer.COGNITIVE:    TransitionVerdict.FORBIDDEN,
            Layer.RUNTIME:      TransitionVerdict.FORBIDDEN,
        },
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def validate_transition(cls, origin: Layer, target: Layer) -> TransitionVerdict:
        """Prüft, ob eine Event-Transition von origin → target erlaubt ist."""
        if origin == target:
            return TransitionVerdict.ALLOWED
        row = cls.TRANSITION_MATRIX.get(origin, {})
        return row.get(target, TransitionVerdict.FORBIDDEN)

    @classmethod
    def emit(cls, event: SpineEvent) -> bool:
        """Event auslösen. Gibt False zurück, wenn die Transition verboten ist."""
        if event.target_layer:
            verdict = cls.validate_transition(event.origin_layer, event.target_layer)
            if verdict == TransitionVerdict.FORBIDDEN:
                return False
            if verdict == TransitionVerdict.NEEDS_BRIDGE:
                # Bridge-Komponente muss registriert sein
                if not cls._bridge_exists(event):
                    return False
        return True
```

**Transition-Matrix als Tabelle:**

| Origin ↓ → Target → | L0 Storage | L1 Runtime | L2 Cognitive | L3 Control | L4 Observ. | L5 API | L6 Frontend |
|---------------------|-----------|------------|--------------|------------|------------|--------|-------------|
| **L0 Storage** | ✅ | ✅ | ❌ | ❌ | ⛓️ | ❌ | ❌ |
| **L1 Runtime** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **L2 Cognitive** | ⛓️ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **L3 Control** | ⛓️ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **L4 Observability** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **L5 API** | ❌ | ❌ | ❌ | ⛓️ | ✅ | ✅ | ✅ |
| **L6 Frontend** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |

**Legende:** ✅ = ALLOWED, ❌ = FORBIDDEN, ⛓️ = NEEDS_BRIDGE

**Kernregeln:**
1. **Storage** darf nur zu Runtime — alle anderen Layer müssen über Bridges gehen
2. **Observability** darf NICHT in Runtime/Cognitive/Control eingreifen (read-only)
3. **API** darf nur Observability direkt — Control nur über Bridge
4. **Frontend** darf nur API und Observability — niemals Kernel-Layer
5. **Runtime** ist der einzige Layer, der in alle Richtungen kommunizieren darf

---

### 14.2 Die 4 Subkernel (Systemtheoretische Modellierung)

Das System besteht aus **4 logischen Subkerneln**, die als eigenständige Module modelliert werden sollten:

#### L1 — Runtime Kernel

| Komponente | Aktuelle Datei | Aufgabe |
|-----------|---------------|---------|
| **WriterThread** | `runtime/kernel/writer.py` | Serialisierte DB-Schreibvorgänge (CQRS) |
| **IPC Server** | *(aus MUSCAL v0.2 zu portieren)* | Unix Socket für Agenten-Kommunikation |
| **IPC Client** | *(aus MUSCAL v0.2 zu portieren)* | Auto-Reconnect, Heartbeat, Events |
| **Process Manager** | *(aus MUSCAL v0.2 zu portieren)* | OS-Prozess-Spawning, Heartbeat-Monitor |
| **Agent SDK** | *(aus MUSCAL v0.2 zu portieren)* | Standardisierte Agenten-Lifecycle-API |
| **MEL** | `mel.py` | Tool-Dispatch |
| **TOOL_REGISTRY** | `tools.py` | Tool-Registry + Schemas |
| **Browser Engine** | `browser_engine.py` | Playwright-Controller |
| **Desktop Tools** | `desktop_tools.py` | PyAutoGUI-Tools |
| **Sanitizer** | `runtime/kernel/sanitizer.py` | Injection-Schutz |

**Verantwortung:** Ausführung, Prozess-Isolation, Safety, CQRS, Tool-Dispatch

#### L2 — Cognitive Kernel

| Komponente | Aktuelle Datei | Aufgabe |
|-----------|---------------|---------|
| **MKC** | `mkc.py` | Regelbasierte NL→MCXF-Kompilierung |
| **MKC Rules** | `mkc_rules.py` | SIGNAL_RULES, Confidence-Adjustments |
| **Bridge** | `bridge.py` | 9 Regex-Matcher: NL → Tool |
| **Optimizer Pipeline** | `runtime/optimizer/pipeline.py` | DCE → Fusion → Parallel |
| **Feedback** | `feedback.py` | Ausführungs-Feedback |
| **YAML Workflow Engine** | *(aus MUSCAL v0.2 zu portieren)* | Deklarative DAG-Workflows |
| **Agent Pipeline** | *(aus ALITAGPT zu portieren)* | Filter→Transform→Enrich→Log |
| **RAG Index** | `runtime/kernel/rag_index.py` | Ollama-Embedding + Cosine-RAG |
| **Chroma Index** | `runtime/kernel/chroma_index.py` | ChromaDB Vektor-Suche |

**Verantwortung:** Kompilierung, Planung, Optimierung, Wissensabruf

#### L3 — Control Kernel

| Komponente | Aktuelle Datei | Aufgabe |
|-----------|---------------|---------|
| **MAS Scheduler** | *(aus ALITAGPT/muscal-mas zu portieren)* | Multi-Strategy Task-Planung |
| **Policy Engine** | *(aus ALITAGPT/muscal-mas zu portieren)* | Thompson Sampling, Bayesian Weights |
| **Consensus** | `consensus_engine.py` + `weighted_consensus.py` | Entscheidungsfindung |
| **Byzantine Consensus** | *(aus ALITAGPT/muscal zu portieren)* | Fault-Tolerant Konsens |
| **Governance** | `runtime/kernel/governance.py` | Token/Iteration/Cost-Limits |
| **Gate** | `runtime/kernel/gate.py` | Atomares Task-Gate |
| **Cognitive Diff** | `cognitive_diff.py` | 5D Diff-Engine |
| **Permission Engine** | `permission_engine.py` | Tool-Berechtigungen |
| **Execution Governor** | `execution_governor.py` | Loop-Governor |

**Verantwortung:** Entscheidungen, Limits, Konsens, Strategie, Routing

#### L4 — Observability Kernel

| Komponente | Aktuelle Datei | Aufgabe |
|-----------|---------------|---------|
| **EventBus** | `event_bus.py` | Pub/Sub mit Prioritäten + Wildcards |
| **Observation Loop** | `runtime/observation/loop.py` | 5s-Tick: Stuck Workers, Drift, Anomalien |
| **Replay Engine** | *(aus ALITAGPT/muscal-mas zu portieren)* | Deterministische Replay-Verifikation |
| **WebSocket EventDaemon** | *(aus ALITA 0.9 zu portieren)* | Echtzeit-Push auf :9090 |
| **Dashboard** | `dashboard.py` | Streamlit Dashboard |
| **Frontend** | `frontend/*.jsx` | React-Komponenten |
| **GraphState** | `graph.py` | Passiver Observer |
| **Sphere** | `sphere.py` | Radiale UI-Projektion |
| **Trace Engine** | `trace_engine.py` | Strukturiertes Logging |
| **Debugger** | `debugger.py` | Metrik-Debugging |
| **Kernel Snapshot** | `kernel_snapshot.py` | Read-Only Introspection |

**Verantwortung:** Systemüberwachung, Ereignis-Routing, Metriken, UI, Replay

---

### 14.3 Layer-Invarianten

#### Invariante A: Directionality (Richtungsgarantie)

Der primäre Datenfluss ist strikt **Bottom-Up** (L0 → L1 → L2 → L3 → L4):

```
L0 Storage ──► L1 Runtime ──► L2 Cognitive ──► L3 Control ──► L4 Observability
     ▲              │               │                │
     └──(Bridge)────┘               └──(Bridge)───────┘
```

- **Aufwärts** (L0→L1→L2→L3→L4): Immer erlaubt, primärer Pfad
- **Abwärts** (L4→L3→L2→L1→L0): NUR durch explizite Bridges
- **Seitwärts** innerhalb desselben Kernels: Immer erlaubt
- **Cross-Kernel** ohne Layer-Ordnung: VERBOTEN (Spine blockiert)

#### Invariante B: Event Ownership

Jedes Event hat genau einen **Origin Layer** und einen **Target Layer**:

```python
@dataclass
class OwnedEvent:
    event_id: str
    event_type: str
    origin_layer: Layer       # Wer hat das Event erzeugt?
    target_layer: Layer       # Wer soll es verarbeiten?
    allowed_bridges: list[str]  # Explizite Bridge-Namen
    payload: dict
```

**Regeln:**
1. Ein Event darf nur von `origin_layer` erzeugt werden
2. Es darf nur zu `target_layer` gesendet werden (Spine validiert)
3. Wenn `origin_layer != target_layer` → muss `target_layer` in der Transition-Matrix ALLOWED sein
4. Wenn NEEDS_BRIDGE → muss `allowed_bridges` eine registrierte Bridge enthalten

**Beispiele für Bridge-Komponenten:**

| Bridge | Von | Nach | Aufgabe |
|--------|-----|------|---------|
| `StorageBridge` | L2 Cognitive | L0 Storage | Erlaubt dem Compiler, auf Disk-Cache zuzugreifen |
| `StateBridge` | L3 Control | L0 Storage | Erlaubt Control, gespeicherte Policen zu laden |
| `APIBridge` | L5 API | L3 Control | Erlaubt API, Tasks zu submiten (sonst verboten) |

#### Invariante C: Determinismus-Zonen

| Zone | Layer | Darf LLM? | Deterministisch? | Beispiele |
|------|-------|-----------|-----------------|-----------|
| **Hart deterministisch** | L0 Storage | Nein | Ja (100%) | SQL-Queries, JSON-Lesen |
| **Hart deterministisch** | L1 Runtime | Nein | Ja (100%) | Tool-Dispatch, IPC, CQRS |
| **Deterministisch + LLM** | L2 Cognitive | Ja, aber gecaged | Ja (RAG-Context fest) | MKC-Regeln, Bridge-Matcher |
| **Strategisch** | L3 Control | Optional | Nein (probabilistisch) | Policy, Consensus |
| **Read-only** | L4 Observability | Nein | N/A | Logging, Metriken, UI |

**Konsequenz:**
- L1 Runtime enthält **kein LLM**, kein `random`, keine Zustands-Mutation
- L2 Cognitive darf LLM nur mit **deterministischem RAG-Context** aufrufen
- L3 Control ist der **einzige nicht-deterministische Layer** — dort leben Policy-Evolution und probabilistischer Konsens
- L4 Observability ist **read-only** — darf niemals Events in L1-L3 auslösen

---

### 14.4 Dependency Graph Enforcer (Architektur-Tool)

Erzwungene Einhaltung der Layer-Regeln durch ein automatisiertes Tool:

```python
# enforce_architecture.py — Dependency Graph Enforcer

import ast
import os
from pathlib import Path

LAYER_MAP = {
    "runtime/kernel/writer.py":        Layer.RUNTIME,
    "runtime/kernel/scheduler.py":     Layer.RUNTIME,
    "runtime/kernel/gate.py":          Layer.CONTROL,
    "runtime/kernel/governance.py":    Layer.CONTROL,
    "runtime/kernel/sanitizer.py":     Layer.RUNTIME,
    "runtime/kernel/rag_index.py":     Layer.COGNITIVE,
    "runtime/kernel/chroma_index.py":  Layer.COGNITIVE,
    "mkc.py":                          Layer.COGNITIVE,
    "bridge.py":                       Layer.COGNITIVE,
    "mel.py":                          Layer.RUNTIME,
    "feedback.py":                     Layer.COGNITIVE,
    "cognitive_diff.py":               Layer.CONTROL,
    "event_bus.py":                    Layer.OBSERVABILITY,
    "graph.py":                        Layer.OBSERVABILITY,
    "debugger.py":                     Layer.OBSERVABILITY,
    "api_server.py":                   Layer.API,
    "runtime/api/*.py":                Layer.API,
    "frontend/*.jsx":                  Layer.FRONTEND,
}

class ArchitectureEnforcer:
    def __init__(self, root: Path):
        self.root = root
        self.violations = []

    def check_file(self, filepath: Path):
        file_layer = self._classify_file(filepath)
        with open(filepath) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_layer = self._classify_import(alias.name)
                    if imported_layer and imported_layer.value > file_layer.value + 1:
                        self.violations.append(
                            f"{filepath}: Import von {alias.name} "
                            f"({imported_layer.name}) aus Layer {file_layer.name} "
                            f"überschreitet Layer-Grenze"
                        )

    def report(self) -> list[str]:
        return self.violations

    def _classify_file(self, path: Path) -> Layer:
        rel = path.relative_to(self.root)
        for pattern, layer in LAYER_MAP.items():
            if rel.match(pattern):
                return layer
        return Layer.RUNTIME

    def _classify_import(self, name: str) -> Layer:
        for pattern, layer in LAYER_MAP.items():
            if name in pattern:
                return layer
        return None
```

**Geplanter Einsatz:**
1. `python3 enforce_architecture.py` → Listet alle Layer-Verstöße
2. Als Pre-Commit-Hook (verhindert Cross-Layer-Imports)
3. Als CI-Step (blockiert PRs mit Verstößen)
4. Generiert Architektur-Drift-Report (Grafik: welche Imports weichen ab)

---

### 14.5 Konsequenzen für die System-Entwicklung

| Maßnahme | Beschreibung | Priorität |
|----------|-------------|-----------|
| **`system_spine.py` erstellen** | Singleton mit Transition-Matrix, validiert jedes Event | P0 — vor jeder Integration |
| **`enforce_architecture.py` erstellen** | AST-basierter Layer-Checker als Pre-Commit-Hook | P0 |
| **Event Ownership einführen** | Jedes Event deklariert origin/target Layer | P1 |
| **4 Kernel als Verzeichnisse** | `runtime/kernel/`, `cognitive/`, `control/`, `observability/` | P1 |
| **Storage Bridges definieren** | Explizite Bridge-Klasse für Storage-Zugriff aus L2/L3 | P1 |
| **Determinismus-Zonen dokumentieren** | Welcher Layer darf LLM? Welcher nicht? (Tabelle in 14.3) | P1 |
| **Cross-Layer-Tests schreiben** | Tests, die verbotene Transitionen nachweisen | P2 |

---

## 15. MAS RFC-ARCHITEKTUR

### 15.1 Was ist MAS?

MAS = **Multi-Agent System** — die formale Spezifikationsreihe für MUSCAL, kein laufender Code. MAS definiert, *wie* MUSCAL gebaut werden soll. Analog zu Rust RFCs, IETF RFCs oder Kubernetes KEPs.

Jedes Feature durchläuft 6 Phasen:

```
DRAFT → RFC → ADR → SPEC → REFERENCE IMPLEMENTATION → TEST SUITE
```

| Status | Bedeutung |
|--------|-----------|
| DRAFT | Ideenskizze (1–2 Seiten, Problem + Lösungsrichtung) |
| RFC | Lösungsvorschlag (Motivation, Design, API-Contracts, Data Models, Failure Cases, Security, MREIL) |
| ADR | Entscheidung (getroffene Entscheidung, Consequences, Rationale) |
| SPEC | Vollständige Spezifikation (implementierbar ohne Rückfragen) |
| IMPL | Referenzimplementierung (stdlib-only, keine Optimierungen) |
| TEST | Test Suite (Unit, Integration, Property-Based, Performance) |
| FINAL | RFC ist abgeschlossen |

### 15.2 RFC-Übersicht

| RFC | Titel | Status |
|-----|-------|--------|
| MAS-0000 | Governance & Entwicklungsregeln | SPEC |
| MAS-0001 | Architecture Principles (10 Prinzipien) | SPEC |
| MAS-0002 | Core Task Scheduler & Parallel Execution Layer | SPEC |
| MAS-0003 | Context Graph Memory System | SPEC |
| MAS-0004 | MPIR Compiler & AST Transformation Layer | SPEC |
| MAS-0005 | Execution Semantics & Deterministic Runtime Layer | SPEC |
| MAS-0006 | Capability System & Permissioned Tool Execution Layer | SPEC |
| MAS-0007 | MREIL Core Metric Engine & Evaluation Kernel | SPEC |
| MAS-0008 | System-wide Orchestration Layer (MAS Kernel Coordinator) | SPEC |
| MAS-0009 | Distributed MAS Runtime & Multi-Agent Execution Fabric | SPEC |
| MAS-0010 | Full System Closure — MAS Cognitive Operating System | SPEC |
| MAS-0011 | State Equivalence Layer (SEL) & Reducer Confluence Kernel | SPEC |
| MAS-0012 | Observability System — Trace, Replay & Diff Graph | SPEC |
| MAS-0100 | Storage API — Checkpoint v1.5 | SPEC |
| MAS-0300 | MAS Virtual Machine — Deterministischer Execution Simulator | SPEC |
| MAS-0301 | Execution Graph Compiler | SPEC |
| MAS-0400 | Distributed Execution Fabric (Production System) | SPEC |
| MAS-0500 | Self-Evolving Optimization Kernel | SPEC |

### 15.3 ADR-Übersicht

| ADR | Titel | Status |
|-----|-------|--------|
| ADR-001 | Execution Graph Compiler statt Interpreter | ACCEPTED |
| ADR-002 | Layer-Architektur mit Spine-Validierung | ACCEPTED |
| ADR-003 | Capability-First statt Model-First | ACCEPTED |

### 15.4 Verzeichnisstruktur

```
specs/
├── rfcs/           # MAS-0001 bis MAS-0600 (18 RFCs)
├── adrs/           # ADR-001 bis ADR-003
├── schemas/json/   # JSON-Schemas
├── templates/      # RFC_TEMPLATE.md
└── ORDER.md        # Governance-Regeln
```

---

## 16. CAPABILITY SYSTEM

### 16.1 Capability-First-Prinzip

MUSCAL routet nicht nach Modell-Namen, sondern nach **Capabilities**. Jeder Task deklariert, welche Fähigkeit er benötigt. Der Scheduler wählt den optimalen Worker basierend auf Capability-Match + MREIL-Score + Resource-Fit.

**Constraint:** Keine Systemkomponente darf von einem Modellnamen abhängen.

### 16.2 Capability Registry

```json
{
  "tool.math":    { "description": "mathematical computation", "risk": "low" },
  "tool.search":  { "description": "information retrieval", "risk": "medium" },
  "tool.network": { "description": "external IO", "risk": "high" },
  "memory.read":  { "description": "read memory graph", "risk": "low" },
  "memory.write": { "description": "write memory graph", "risk": "medium" }
}
```

### 16.3 Capability Lifecycle

```
REGISTER → GRANT → REVOKE → EXPIRED
```

### 16.4 Execution Gating Pipeline

```
Node Request → Capability Validator → Policy Engine → Sandbox Allocator → Execution Runtime → Result Commit
```

### 16.5 Policy Engine Rules

- Default deny
- Explicit allow required
- No implicit inheritance
- No capability escalation during runtime

---

## 17. MPIR COMPILER PIPELINE & MREIL

### 17.1 MPIR-Pipeline-Überblick

```
MBL (Natürliche Sprache)
  → MPES (Prompt Execution Specification)
    → MPIR (Intermediate Representation)
      → MSL (System Language)
        → Execution DAG
```

### 17.2 Compiler-Stages

| Stage | Eingabe | Ausgabe | Transformation |
|-------|---------|---------|---------------|
| Tokenize | Prompt (NL) | Token-Stream | Lexikalische Analyse |
| Parse AST | Token-Stream | AST (Syntax-Baum) | Grammatik-Regeln |
| Normalize AST | AST | NAST | Intent-Canonicalization, Flattening |
| Validate | NAST | Validated AST | Semantik-Prüfung |
| Compile MPIR | NAST | MPIR-Graph | Node-Mapping |
| Optimize | MPIR | Optimized MPIR | Fusion, DCE, Pruning |

### 17.3 Normalization Rules

- **Regel 1** — Intent Canonicalization: Alle Synonyme → standardisierte Intent-Tags
- **Regel 2** — Operation Flattening: Verschachtelte Befehle → lineare IR Nodes
- **Regel 3** — Context Binding: Implizite Referenzen → explizite Graph Edges

### 17.4 MREIL 5D Metric Engine

| Dimension | Bedeutung | Formel | Skala |
|-----------|-----------|--------|-------|
| **M**emory | Kontext-Nutzung | retained_context / total_context | 0.0–1.0 |
| **R**easoning | Logische Konsistenz | correct_outputs / reasoning_steps | 0.0–1.0 |
| **E**xecution | Tool-Erfolgsrate, Latenz | avg(node_execution_time) | 0.0–1.0 |
| **I**ntegrity | Validation, Safety | deviation(reference, actual) | 0.0–1.0 |
| **L**oad | Systemauslastung | cpu/ram/network utilization | 0.0–1.0 |

### 17.5 Scoring Function

```
MREIL_score = (0.25*M + 0.25*R + 0.2*(1/E) + 0.2*(1-I) + 0.1*L)
```

---

## 18. STATE EQUIVALENCE LAYER (SEL)

### 18.1 Problemstellung

MUSCAL hat ein Event-System + Reducer, aber keine formale Äquivalenzrelation über Zustände. Damit fehlt die Closure-Ebene des Systems: Zwei Ausführungen können nicht formal verglichen werden.

### 18.2 Formale Definition

- `ℰ` = Menge aller Events
- `S` = Menge aller System States
- `canonical: S → S` = CanonicalState-Funktion (Normierung)
- `~ ⊆ S × S`: `s1 ~ s2 ⇔ canonical(s1) = canonical(s2)`
- `S/~` = Quotient Space (Zustandsäquivalenzklassen)
- `cl: 2^S → 2^S` = Closure Operator (kleinste abgeschlossene Obermenge)

### 18.3 Event Stream Equivalence

```
E1 ≈ E2 ⇔ Fold(E1) ~ Fold(E2)
```

Zwei Event-Streams sind äquivalent, wenn ihre gefalteten Zustände äquivalent sind.

### 18.4 Canonical State Function

1. Normalisiere Node-IDs (deterministisches UUID-Mapping)
2. Sortiere Adjazenzlisten (Graph-Kanonisierung)
3. Normalisiere Metadaten-Reihenfolge
4. Kollabiere kommutative Event-Effekte
5. Löse Version-Chains auf (nur letzte gültige Version)

### 18.5 Reducer Confluence Condition

Der Reducer muss garantieren: Unabhängigkeit von Event-Permutation innerhalb kausaler Ordnung.

| Klasse | Events | Verhalten |
|--------|--------|-----------|
| Kommutativ | MetadataPatched, EdgeCreated (distinkt), NodeCreated (distinkt) | Order-independent merge |
| Nicht-kommutativ | NodeUpdated (selber Node), RelationChanged, VersionOverride | Causal serialization erzwingen |

### 18.6 Snapshot Invariance Theorem (SIT)

Zwei Snapshots S(t1), S(t2) sind äquivalent genau dann wenn eine Bijektion f: Nodes(t1) → Nodes(t2) existiert, sodass Struktur, Relations-Graph und Version-Chains erhalten bleiben.

---

## 19. MAS-VM & FORMAL VERIFICATION

### 19.1 MAS-VM (Deterministischer Execution Simulator)

Die MAS-VM spielt Execution-Graphen deterministisch ab (ohne LLM), berechnet Soll-Zustände und vergleicht sie mit Ist-Zuständen.

**Verwendung:** Replay, Audit, Debug, Formal Verification.

### 19.2 VM-Architektur

| Komponente | Aufgabe |
|-----------|---------|
| Scheduler (VM-intern) | Node-Reihenfolge deterministisch festlegen |
| Executor | Node-Funktion ausführen (pure) |
| Memory Manager | Isolierten Context pro Node bereitstellen |
| Trace Recorder | Jeden Schritt aufzeichnen |
| Trap Handler | Fehler/Verstöße abfangen |

### 19.3 Execution Graph Compiler Pipeline

```
1. INPUT PARSING — MCXF → Intermediate Graph
2. NORMALIZATION — Node Typisierung, Event Standardisierung, Layer Annotation
3. STATIC VALIDATION — Cycle detection, Layer rule enforcement
4. SPINE VALIDATION — Transition legality, Event origin verification
5. OPTIMIZATION — Node fusion, Parallelization tagging, Cost estimation
6. EXECUTION GRAPH EMISSION — DAG ready for runtime engine
```

### 19.4 Formal Verification Layer

| Prüfung | Beschreibung | Methode |
|---------|-------------|---------|
| Type Proofs | Korrekte Input/Output-Typen pro Node | AST-Analyse |
| Acyclicity Proofs | Graph enthält keine Zyklen | Topologisches Sort |
| Determinism Proofs | Gleicher Input → Gleicher Output | Hash-Vergleich |
| Execution Certificates | Kryptografische Signatur jedes Pfads | Merkle-Tree |

---

## 20. MUSCAL PRODUCTION SYSTEM

### 20.1 6-Layer Production Stack

| Layer | Komponente | Aufgabe |
|-------|-----------|---------|
| L6 | UI / Dashboard | Steuerung & Visualisierung |
| L5 | API Gateway | Auth, Rate-Limit, Routing |
| L4 | Policy Engine | Capability-Check, Governance |
| L3 | Sandbox | Process-Isolation, Resource-Limits |
| L2 | Execution Graph | DAG-Runtime, MAS-VM |
| L1 | Storage / Persistence | SQLite, Snapshots, Backup |

### 20.2 Sandbox-Architektur (Podman)

- Container-Isolation pro Agent
- Resource Limits: CPU-Shares, RAM-Limit, Network-Block
- Read-Only Root FS mit beschreibbaren Volumes
- Kein direkter Host-Zugriff
- Deterministisches Logging aller Container-Aktionen

### 20.3 Control Model

```
Input → Policy Gate → Resource Check → Sandbox Execution → Validated Output
```

### 20.4 Policy & Governance

- Rate-Limiting pro Capability
- Budget-Management (Token/Cost)
- Audit-Log + Compliance-Reporting
- Selbstheilung: Test → Diagnose → Patch → Rebuild (closed-loop)

---

## 21. OBSERVABILITY SYSTEM

### 21.1 Vier-Ebenen-Modell

```
Execution Graph (Soll) → Trace Graph (Ist) → Replay Graph (Wiederholung) → Diff Graph (Vergleich)
```

Das System beantwortet vier Fragen:
1. **Was sollte passieren?** — Execution Graph
2. **Was ist passiert?** — Trace Graph
3. **Kann es reproduziert werden?** — Replay Graph
4. **Warum unterscheiden sich zwei Ausführungen?** — Diff Graph

### 21.2 Trace Graph

```json
{
  "node_id": "n1",
  "status": "success | failed | skipped | timeout | unknown",
  "input_hash": "abc",
  "output_hash": "def",
  "duration_ms": 150,
  "seed": 42,
  "mreil_snapshot": {}
}
```

### 21.3 Replay Graph

Deterministische Wiederholung eines Traces mit identischem Seed:
- Gleicher Input + Seed → identischer Output
- Alle Side Effects werden blockiert
- Timeout wird auf 0 gesetzt (kein Warten)

### 21.4 Diff Graph

| Dimension | Vergleichsgrundlage |
|-----------|-------------------|
| Structural | Graph-Struktur (Nodes, Edges) |
| Hash | Input/Output-Hashes |
| MREIL | Metrik-Vektoren |
| Temporal | Timing/Reihenfolge |

### 21.5 Snapshot-Regeln

- Snapshot bei: Run-Start, Run-Ende, Fehler
- Inhalt: Trace Graph + MREIL Score + SEL Canonical State
- Retention: letzte 100 Snapshots, dann Kompaktierung

---

## 22. AUSBLICK & ROADMAP

### 22.1 Aktuelle Lücken vs. RFC-Anforderungen

| RFC | MUSCAL CORE | Benötigt |
|-----|-------------|----------|
| MAS-0002 (Scheduler) | ⚠️ Stub (46 Zeilen) | Multi-Strategy + Capability-Routing |
| MAS-0003 (Memory Graph) | ⚠️ Stub-Sammlung | Context Graph mit Versioning |
| MAS-0004 (MPIR Compiler) | ✅ MKC (102 Zeilen) | Pipeline ausbauen |
| MAS-0005 (Runtime) | ✅ MEL + Tools | Deterministische Traces |
| MAS-0006 (Capabilities) | ⚠️ permission_engine.py | Vollständige Registry |
| MAS-0007 (MREIL) | ⚠️ GAR NICHT vorhanden | Neue Implementierung |
| MAS-0008 (Orchestration) | ✅ kernel.py | Coordinator-Erweiterungen |
| MAS-0009 (Distributed) | ⚠️ Stubs (13 Dateien) | Fabric-Protokoll |
| MAS-0011 (SEL) | ⚠️ GAR NICHT vorhanden | CanonicalState + Quotient Space |
| MAS-0012 (Observability) | ✅ EventBus + Observation Loop | Trace/Replay/Diff |
| MAS-0300 (MAS-VM) | ⚠️ GAR NICHT vorhanden | Execution Simulator |
| MAS-0301 (EG Compiler) | ⚠️ GAR NICHT vorhanden | MCXF → DAG |
| MAS-0400 (Production) | ⚠️ Dockerfile existiert | Sandbox + Policy |
| MAS-0500 (Self-Evolution) | ⚠️ Stubs (9 Dateien) | Geschlossener Regelkreis |

### 22.2 Priorisierte Reihenfolge

| Priorität | RFC | Aufwand | Abhängigkeit |
|-----------|-----|---------|-------------|
| P0 | MAS-0301 (EG Compiler) | ~500 Zeilen | Keine |
| P0 | MAS-0011 (SEL) | ~200 Zeilen | MAS-0005 |
| P1 | MAS-0007 (MREIL) | ~300 Zeilen | MAS-0301 |
| P1 | MAS-0300 (MAS-VM) | ~400 Zeilen | MAS-0301 |
| P1 | MAS-0012 (Observability) | ~250 Zeilen | MAS-0011 |
| P2 | MAS-0006 (Capabilities) | ~300 Zeilen | MAS-0001 |
| P2 | MAS-0100 (Storage) | ~200 Zeilen | MAS-0010 |
| P3 | MAS-0002 (Scheduler) | ~400 Zeilen | MAS-0006 |
| P3 | MAS-0400 (Production) | ~500 Zeilen | MAS-0300 |
| P4 | MAS-0500 (Self-Evolution) | ~600 Zeilen | MAS-0007 |
| P4 | MAS-0009 (Distributed) | ~800 Zeilen | MAS-0008 |

---

*Generiert 2026-07-04. Basis: Vollständige Codeanalyse von MUSCAL CORE, 5 Schwesterprojekte und 18 MAS-RFCs.*
