# D-E3.0.2-005 — DEFINITIVE REACHABILITY AND DEAD-CODE AUDIT

**Status:** COMPLETE
**Date:** 2026-07-22

---

## 1. Classification Schema

| Classification | Definition |
|---------------|------------|
| **HOT_PATH** | Demonstrably reachable from `MuscalKernel.run()` — the canonical production execution path |
| **WARM_PATH** | Reachable through an alternate production entry point (`runtime/main.py`, `supervisor.py`, Flask API) |
| **COLD_PATH** | Implemented and potentially usable, but not currently reachable from normal production execution |
| **ORPHANED** | No production caller found after repository-wide search |
| **EXPERIMENTAL** | Standalone research/prototype utility |
| **DEAD** | Demonstrably unreachable with no intended supported entry point |

## 2. Production Entry Points

| Entry Point | Entry File | Classification |
|-------------|-----------|----------------|
| Kernel REPL | `main.py` → `MuscalKernel.run()` | **HOT_PATH** |
| OS Boot + interactive | `main_boot.py` → `MuscalOS` → `MuscalKernel.run()` | **HOT_PATH** |
| Flask API Server | `runtime/main.py` → Flask app | **WARM_PATH** |
| Supervisor | `supervisor.py` → Flask app | **WARM_PATH** |

## 3. Complete Component Classification

### HOT_PATH (reachable from MuscalKernel.run())

| Component | File | Role | Evidence |
|-----------|------|------|----------|
| Kernel Orchestrator | `kernel.py` | Main pipeline controller | Entry point |
| MKC Compiler | `mkc.py` | Input → MCXF | `kernel.py:31`: `from mkc import mkc` |
| Bridge | `bridge.py` | MCXF → ExecutionPlan | `kernel.py:24`: `from bridge import map_tasks, validate_plan` |
| MEL Executor | `mel.py` | Tool dispatch | `kernel.py:28`: `from mel import execute` |
| RAG (BM25) | `rag.py` | Keyword context retrieval | `kernel.py:34-35`: `from rag import enrich, retrieve` |
| Memory | `memory.py` | SQLite + JSONL persistence | `kernel.py:29-30`: `from memory import ...` |
| Feedback | `feedback.py` | Failure analysis | `kernel.py:26`: `from feedback import analyze_feedback` |
| Graph State | `graph.py` | DAG state management | `kernel.py:27`: `from graph import GraphState` |
| Schema Types | `schema.py` | KernelResult, MCXFDocument, etc. | `kernel.py:36-67`: imports |
| Sphere State | `sphere.py` | Visualization state | `kernel.py:68`: `from sphere import SphereState` |
| MKC Rules | `mkc_rules.py` | Feedback application | `kernel.py:32`: `from mkc_rules import apply_feedback` |
| Plugin Registry | `plugin_registry.py` | Hook system | `kernel.py:33`: `from plugin_registry import HOOKS, run_hooks` |
| Debugger | `debugger.py` | Step debugging | `kernel.py:25`: `from debugger import DebugEngine` |
| Optimizer Pipeline | `runtime/optimizer/pipeline.py` | Plan optimization | `kernel.py:398`: `from runtime.optimizer.pipeline import OptimizerPipeline` (dynamic) |
| Tool Registry | `tools.py` | TOOL_REGISTRY (3 executors) | `mel.py:3`: `from tools import TOOL_REGISTRY` |
| SystemAgentRuntime | `system_runtime.py` | Browser/desktop execution | `mel.py:13`: `from system_runtime import SystemAgentRuntime` (lazy) |
| Event Bus | `event_bus.py` | Pub/sub (via MuscalOS) | `muscal_os.py:9`: `from event_bus import EventBus` |
| Event Store | `runtime/event_store.py` | Append-only persistence (via MuscalOS) | `muscal_os.py:11`: `from runtime.event_store import EventStore` |
| Config | `config.py` | Global configuration | Imported transitively |
| Kernel Diff Engine | `kernel_diff_engine.py` | State diffing (via MuscalOS) | `muscal_os.py:12` |
| Cognitive Diff | `cognitive_diff.py` | MCXF diffing (via MuscalOS) | `muscal_os.py:8` |
| Trace Engine | `trace_engine.py` | Execution tracing (via MuscalOS) | `muscal_os.py:29` |
| Boot Manager | `boot_manager.py` | Boot lifecycle (via MuscalOS) | `muscal_os.py:7` |
| OS Config | `os_config.py` | Deployment configuration | `muscal_os.py:13` |
| Plugin Loader | `plugin_loader.py` | Plugin discovery (via MuscalOS) | `muscal_os.py:14` (imported in method) |

### WARM_PATH (reachable through Flask API)

| Component | File | Role | Evidence |
|-----------|------|------|----------|
| WriterThread | `runtime/kernel/writer.py` | 22-column atomic event writer | `runtime/main.py:27`, `supervisor.py:61` |
| RoutingPolicy | `runtime/kernel/scheduler.py` | DB-backed task routing | `runtime/main.py:33`, `supervisor.py:67` |
| Gate | `runtime/kernel/gate.py` | Task atomic start | `runtime/api/tasks.py:10` |
| GovernanceSync | `runtime/kernel/governance.py` | Sync governance | `runtime/main.py:35`, `supervisor.py:68` |
| ObservationLoop | `runtime/observation/loop.py` | Health monitoring | `runtime/main.py:44-45`, `supervisor.py:76-77` |
| RAGIndex | `runtime/kernel/rag_index.py` | Vector embedding search | `runtime/api/chat.py:56`, `runtime/api/rag.py:23,35` |
| LLM Client | `runtime/llm/client.py` | Ollama keepalive/health | `runtime/observation/loop.py:53` |
| LLM Models | `runtime/llm/models.py` | Qwen + SMOL | `runtime/api/chat.py:9` |
| API: State | `runtime/api/state.py` | System state endpoint | Registered via blueprints |
| API: Tasks | `runtime/api/tasks.py` | Task submission endpoint | WARM_PATH (calls gate + scheduler) |
| API: Workers | `runtime/api/workers.py` | Worker management endpoints | WARM_PATH |
| API: Events | `runtime/api/events.py` | Event browsing | WARM_PATH |
| API: Chat | `runtime/api/chat.py` | Chat interface | WARM_PATH (calls RAGIndex + LLM) |
| API: Models | `runtime/api/models.py` | Model listing | WARM_PATH |
| API: RAG | `runtime/api/rag.py` | RAG search/reload | WARM_PATH (calls RAGIndex) |
| API: Filesystem | `runtime/api/fs.py` | File operations | WARM_PATH |
| API: Admin | `runtime/api/admin.py` | Admin operations | WARM_PATH |
| API: Handoff | `runtime/api/handoff.py` | Session handoff | WARM_PATH |
| Snapshot Service | `runtime/services/snapshot.py` | State snapshots | `runtime/api/chat.py:144` (via /snapshot command) |
| Rate Limiter | `runtime/api/__init__.py` | Request rate limiting | WARM_PATH (in middleware) |

### COLD_PATH (implemented, potentially reachable)

| Component | File | Evidence |
|-----------|------|----------|
| Governance (async) | `runtime/kernel/governance.py:Governance` | Called by gate.py without await (bug); never instantiated in production |
| PermissionEngine | `permission_engine.py` | `mel_execute` imported by orphaned `scheduler.py`; `run_muscal` references orphaned `ExecutionGovernor` |

### ORPHANED (no production caller found)

| Component | File | Evidence |
|-----------|------|----------|
| Pipeline Stages (×8) | `features/pipeline/stages.py` | Zero imports from production code |
| PipelineBuilder | `features/runtime/pipeline_builder.py` | Zero production imports |
| PluginSandbox | `features/sandbox/plugin_sandbox.py` | Zero production imports |
| ResourceWatchdog | `features/sandbox/resource_watchdog.py` | Only imported by PluginSandbox (also orphaned) |
| ReplayService | `features/replay/replay_service.py` | Only imported by tests |
| Scheduler (root) | `scheduler.py` | `muscal_runtime()` never called |
| WorkerNode | `worker_node.py` | Only imported by `archive/distributed_bootstrap.py` |
| WorkerPool | `worker_pool.py` | Same as above |
| AdaptiveRouter | `adaptive_router.py` | Zero imports |
| TaskRouter | `task_router.py` | Zero imports |
| DistributedOrchestrator | `distributed_orchestrator.py` | Imports consensus_engine, result_collector, safe_executor — all also orphaned |
| LoopController | `loop_controller.py` | Only imported by ExecutionGovernor (orphaned) |
| ExecutionGovernor | `execution_governor.py` | Only imported by permission_engine.run_muscal (orphaned) |

### EXPERIMENTAL

| Component | File | Evidence |
|-----------|------|----------|
| MuscalLoop | `muscal_loop.py` | Standalone LLM-driven autonomous loop. Runs as `python muscal_loop.py`. Has 6 executors, BrowserAgent, and its own LLM compiler. Not wired into any production entry point. Has its own `TOOL_SCHEMAS` (6) and `EXECUTORS` (6) that partially overlap with `tools.py`. |

### DEAD

No components classified as DEAD. All orphaned components could theoretically be reached if wired.

## 4. Summary Counts

| Classification | Count |
|---------------|-------|
| HOT_PATH | 27 root/runtime modules |
| WARM_PATH | 19 modules (including 10 API blueprints) |
| COLD_PATH | 2 implementations |
| ORPHANED | 14 files (including 8 stage wrappers) |
| EXPERIMENTAL | 1 standalone loop |
| DEAD | 0 |
