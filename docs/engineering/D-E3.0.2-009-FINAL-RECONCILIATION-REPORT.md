# D-E3.0.2-009 — E3.0.2 FINAL CORRECTED RECONCILIATION REPORT

**Status:** CERTIFIED
**Date:** 2026-07-22
**Supersedes:** D-E3.0-001 through D-E3.0-014 (all — corrected versions in `docs/engineering/D-E3.0.2-*`)

---

## 1. Executive Summary

E3.0.2 performed an independent, repository-verified reconciliation of the MUSCAL CORE codebase against the E3.0 findings and the canonical AMS-001 v1.0 architecture.

**Key discovery:** Three production entry points exist, not one. The E3.0 reconciliation treated the codebase as a single execution context, when in fact there are two distinct runtimes (Kernel REPL/OS = HOT_PATH, Flask API = WARM_PATH) with overlapping but non-identical component usage. This is the root cause of most E3.0 factual errors.

**Result:** E3.0 contained 3 material factual errors and 2 significant omissions. All are corrected in this report. The codebase is now factually reconciled.

**E3.1 Readiness:** CONDITIONAL GO — achieved after E3.0 artifact corrections and Pipeline Stages decision.

---

## 2. Corrections to E3.0

### Correction 1: Vector RAG (was D-E3.0-012 §3.2)

| Aspect | E3.0 Claim | Corrected Claim |
|--------|-----------|-----------------|
| Status | Functioning component needing abstraction | Domain-specific utility for alita_wissen.md |
| Reachability | Blocking E3.1 | WARM_PATH (Flask API only), NOT in kernel hot path |
| Pipeline relevance | Core pipeline component | Not used by MuscalKernel.run() — kernel uses BM25 keyword RAG |
| E3.1 impact | Blocker | Non-blocker — post-E3.1 cleanup ticket |

### Correction 2: Router (was D-E3.0-005, D-E3.0-006)

| Aspect | E3.0 Claim | Corrected Claim |
|--------|-----------|-----------------|
| RoutingPolicy status | Partially implemented | Fully functional in WARM_PATH (Flask API via gate.py) |
| Kernel path | Needs generalization | **Absent** from HOT_PATH — no routing in MuscalKernel.run() |
| Router domain | Partially exists | Split: works in API, absent from kernel |

### Correction 3: Governance (was D-E3.0-005, D-E3.0-012 §5)

| Aspect | E3.0 Claim | Corrected Claim |
|--------|-----------|-----------------|
| Governance status | Partially wired | GovernanceSync works correctly in WARM_PATH; async Governance has a latent bug |
| Kernel path | Needs integration | **Absent** from HOT_PATH — no governance in MuscalKernel.run() |
| ExecutionGovernor | (not mentioned) | ORPHANED — 38-line stub with no callers |

### Correction 4: Pipeline Stages (not addressed by E3.0)

| Aspect | E3.0 | Corrected |
|--------|------|-----------|
| `features/pipeline/stages.py` | Not mentioned | 8 fully composed stage wrappers, ORPHANED (zero production imports) |
| `features/runtime/pipeline_builder.py` | Not mentioned | Alternate builder, also ORPHANED |
| Architectural value | Not assessed | HIGH — wrappers are architecturally sound foundation for E3.1 pipeline |

### Correction 5: Agent Detection (not addressed by E3.0)

| Aspect | E3.0 | Corrected |
|--------|------|-----------|
| `agent_detection.py` | Not mentioned | **Does not exist** in MUSCAL CORE |
| `router_agent_tasks.py` | Not mentioned | **Does not exist** in MUSCAL CORE |
| Agent registry/reasoning | Not mentioned | No agent detection capability exists |

---

## 3. Corrections to E3.0.1

| E3.0.1 Claim | Corrected | Evidence |
|-------------|-----------|----------|
| Vector RAG is "standalone experimental utility" | **WARM_PATH** — used by Flask API chat/rag endpoints | `runtime/api/chat.py:56`, `runtime/api/rag.py:23` |
| RouterPolicy is "dead code" | **WARM_PATH** — used by Flask API tasks endpoint | `runtime/api/tasks.py:10`, `runtime/main.py:33`, `supervisor.py:67` |
| Governance is "dead code" | **WARM_PATH** — GovernanceSync actively used by Flask API | `runtime/main.py:35`, `supervisor.py:68` |
| agent_detection.py exists | **File does not exist** in MUSCAL CORE | Repository search |
| router_agent_tasks.py exists | **File does not exist** in MUSCAL CORE | Repository search |

---

## 4. Verified Current-State Architecture

### Production Entry Points (3)

```
┌─────────────────────────────────────────────────────────────────┐
│ HOT_PATH: MuscalKernel.run() via main.py or main_boot.py       │
├─────────────────────────────────────────────────────────────────┤
│ kernel.py:run()                                                 │
│   ├── [1] RAG (keyword BM25) — rag.py                           │
│   ├── [2] MKC Compile — mkc.py                                  │
│   ├── [3] MCXF Section — inline graph ops                       │
│   ├── [4] Bridge — bridge.py → ExecutionPlan                    │
│   ├── [5] Optimizer — runtime/optimizer/pipeline.py             │
│   ├── [6] MEL Execute — mel.py → tools.py + system_runtime.py   │
│   ├── [7] Feedback — feedback.py                                │
│   └── [8] Memory — memory.py                                    │
│                                                                  │
│ MuscalOS wraps kernel.run() with EventBus + EventStore           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ WARM_PATH: Flask API via runtime/main.py or supervisor.py       │
├─────────────────────────────────────────────────────────────────┤
│ writer = WriterThread()                                          │
│ policy = RoutingPolicy()                                         │
│ governance = GovernanceSync()                                    │
│ obs_loop = ObservationLoop(writer)                               │
│                                                                  │
│ POST /api/task → gate.start_task_atomic() → policy.route()      │
│ POST /api/chat  → RAGIndex.get_context() → LLM models           │
│ POST /api/rag/search → RAGIndex.search()                        │
│                                                                  │
│ Does NOT use MuscalKernel at all                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ EXPERIMENTAL: muscal_loop.py (standalone)                       │
├─────────────────────────────────────────────────────────────────┤
│ MuscalLoop.run() → LLM → parse_mcxf() → validate → execute      │
│ Has own BrowserAgent, own EXECUTORS (6 tools), own LLM loop     │
│ Not wired into any production entry point                       │
└─────────────────────────────────────────────────────────────────┘
```

### Component Inventory (all 70+ major components)

See D-E3.0.2-005 for the definitive classification of every component.

---

## 5. Hot/Warm/Cold/Orphaned/Experimental/Dead Classification

| Classification | Count | Key Examples |
|---------------|-------|-------------|
| **HOT_PATH** | 27 | kernel.py, mkc.py, bridge.py, mel.py, rag.py, memory.py, feedback.py, graph.py, tools.py, system_runtime.py, muscal_os.py, event_bus.py, event_store.py |
| **WARM_PATH** | 19 | WriterThread, RoutingPolicy, Gate, GovernanceSync, ObservationLoop, RAGIndex, all 10 API blueprints |
| **COLD_PATH** | 2 | Governance (async), PermissionEngine |
| **ORPHANED** | 14 | Pipeline Stages (×8), PipelineBuilder, PluginSandbox, ResourceWatchdog, ReplayService, Scheduler (root), WorkerNode, WorkerPool, AdaptiveRouter, TaskRouter, DistributedOrchestrator, LoopController, ExecutionGovernor |
| **EXPERIMENTAL** | 1 | MuscalLoop |
| **DEAD** | 0 | — |

---

## 6. Pipeline Stages Decision

**Decision: ADOPT WITH REFACTORING** (per ADR-020)

The 8 stage wrappers in `features/pipeline/stages.py` are architecturally sound and become the migration foundation for E3.1. However, the `self.k.stage_*()` methods they depend on do not exist on `MuscalKernel` and must be created.

### Adoption Scope

| Stage | Status | Action Required |
|-------|--------|----------------|
| RAGStage | Adopt | Add `kernel.stage_rag()` |
| MKCStage | Adopt | Add `kernel.stage_mkc()` |
| MCXFStage | Adopt | Add `kernel.stage_mcxf_section()` |
| BridgeStage | Adopt | Add `kernel.stage_bridge()` |
| OptimizerStage | Adopt | Add `kernel.stage_optimizer()` |
| MELStage | Adopt | Add `kernel.stage_mel()` |
| FeedbackStage | Adopt | Add `kernel.stage_feedback()` |
| MemoryStage | Adopt | Add `kernel.stage_memory()` |

All 8 refactorings are pure extractions of existing inline code — zero behavioral change.

---

## 7. Tool Runtime Consolidation Surface

**Decision: ADR-014 updated to DRAFT** with expanded scope (4 systems, not 2).

| System | Executors | Reachability | Fate |
|--------|-----------|-------------|------|
| tools.py TOOL_REGISTRY | 3 (write, add, print_console) | HOT_PATH | Migrate to UTR |
| muscal_loop.py EXECUTORS | 6 | EXPERIMENTAL | Migrate to UTR, then remove inline |
| system_runtime.py SART | 0 (both stubs missing) | HOT_PATH (silent fallback) | Deprecate → redirect to UTR |
| permission_engine.py | Reuses muscal_loop | COLD_PATH | Deprecate (merge risk levels into SafetyGate) |

**Confirmed: 11/14 schemas in tools.py have no executor.** (This was stated in ADR-014 and confirmed independently.)

---

## 8. Routing Status

| Entry Point | Routing | Status |
|-------------|---------|--------|
| **Kernel (HOT_PATH)** | **None** | Gap — E3.1 must add |
| **Flask API (WARM_PATH)** | `scheduler.py:RoutingPolicy` (DB-backed) | Working |
| **Standalone (EXPERIMENTAL)** | None (muscal_loop routes by tool name only) | N/A |

E3.1 must add Router functionality to `MuscalKernel.run()`. The existing `RoutingPolicy` can serve as the reference implementation pattern.

---

## 9. Governance Status

| Entry Point | Governance | Status |
|-------------|-----------|--------|
| **Kernel (HOT_PATH)** | **None** | Gap — E3.1 must add |
| **Flask API (WARM_PATH)** | `GovernanceSync` (sync, threading.Lock) | Working |
| **Async Governance** | Has bug if instantiated (called without await) | Latent issue |

E3.1 must wire `GovernanceSync` (or equivalent) into `MuscalKernel.run()`. The `gate.py` async bug must be fixed.

---

## 10. Model-Binding Audit

| Location | Binding | Classification |
|----------|---------|----------------|
| `rag_index.py:19` | `nomic-embed-text` | WARM_PATH |
| `rag_index.py:18` | `http://localhost:11434` | WARM_PATH |
| `scheduler.py:29` | `"qwen_router"` | WARM_PATH |
| `muscal_loop.py:18` | `qwen2.5:7b-instruct` | EXPERIMENTAL |
| `muscal_loop.py:17` | `http://localhost:11434/api/generate` | EXPERIMENTAL |

No model-binding violations exist in the kernel hot path. The violations that exist are in WARM_PATH (API) and EXPERIMENTAL (standalone loop) components.

---

## 11. Agent Detection Status

**Not implemented.** `agent_detection.py` and `router_agent_tasks.py` do not exist on disk. No agent classification or detection mechanism exists in the codebase.

ADR-021 (Agent Detection Formalization) is justified as a distinct architectural decision.

---

## 12. Immutability Impact

E3.1 requires modifying **6 immutable files** (primarily `kernel.py`). All changes are extractive or additive — existing execution logic is preserved. The override mechanism (`spec/OVERRIDE.md` §6 + `--allow-core-write`) is sufficient.

**Prefer the smallest possible core modification surface:**
- `kernel.py`: ~200 lines added (8 stage methods + pipeline wiring)
- `mel.py`: ~10 lines changed (UTR dispatch)
- `tools.py`: ~20 lines added (backward compat shim)
- `muscal_loop.py`: ~50 lines removed (EXECUTORS after migration)
- `system_runtime.py`: ~5 lines added (deprecation header)
- `runtime/kernel/gate.py`: ~3 lines changed (fix async bug)

All new architectural components (UTR, SafetyGate, CognitiveUnit, Agent Detection) live in `features/` or as new files in `runtime/`.

---

## 13. Canonical Target Architecture

The canonical architecture (AMS-001 v1.0) remains unchanged:

```
Input → Router → Agent Detection → CognitiveUnit → Worker → Tool Execution → Memory
         │            │                    │            │          │
         └── Governance checks at every stage ──────────┘──────────┘
```

What E3.0.2 adds is the clear separation between:
- **CURRENT STATE:** Two runtimes (Kernel + API), no CU, no Router in kernel, no Governance in kernel, orphaned pipeline stages
- **TARGET STATE:** Single unified pipeline with Router → CU → Worker dispatch, Governance at every stage, unified tool runtime

---

## 14. Remaining Contradictions

1. **Two runtimes, one architecture**: The Kernel REPL and Flask API serve the same purpose with zero shared code. E3.1 must either unify them or explicitly accept architectural divergence.
2. **Pipeline stages exist but don't work**: The 8 wrappers are defined but the interface they depend on was never built. This is half-completed work.
3. **Browser/desktop tools are stubs**: `browser_tools.py` and `desktop_tools.py` don't exist. `system_runtime.py` silently fails for all browser/desktop operations.

---

## 15. Remaining Open Questions

1. **Should the Kernel REPL and Flask API converge?** Or is the Flask API a separate administrative interface?
2. **What is the `muscal/` directory project?** Referenced in documentation but not present alongside MUSCAL CORE.
3. **Should MuscalLoop be deprecated or adopted?** Its 6 executors are the only complete browser implementation.

---

## 16-17. E3.1 Blockers and Non-Blockers

### Blockers (must resolve before E3.1 contracts can be written)
1. ~~E3.0 factual corrections~~ ✅ **DONE** (this report)
2. ~~Pipeline Stages decision~~ ✅ **DONE** (ADR-020: ADOPT WITH REFACTORING)
3. ~~Tool runtime consolidation surface~~ ✅ **DONE** (ADR-014 updated)
4. ~~Core-change override documented~~ ✅ **DONE** (OVERRIDE-060)

### Non-Blockers (can be addressed during E3.1)
1. Vector RAG model abstraction (post-E3.1 cleanup)
2. async Governance bug in gate.py (fix during governance formalization)
3. Browser/desktop tool implementation (during UTR build)
4. Agent detection (during E3.1 Phase 4 — CognitiveUnit)

---

## 18. Recommended E3.1 Implementation Sequence

```
Phase 1 — Foundation (E3.1 entry, ~2 weeks)
  P1.1  Add 8 stage_*() methods to kernel.py  [OVERRIDE-060]
  P1.2  Wire register_stage() + build_pipeline() into kernel.__init__()
  P1.3  Replace inline 8-step run() with pipeline iteration
  P1.4  Register features/pipeline/stages.py as default pipeline
  P1.5  Add GovernanceSync check as new stage
  P1.6  Add RoutingPolicy call as new stage

Phase 2 — Governance + Routing (~1 week)
  P2.1  Fix async Governance bug in gate.py
  P2.2  Formalize Governance contract in kernel pipeline
  P2.3  Formalize Router contract in kernel pipeline

Phase 3 — Tool Runtime (~2 weeks)
  P3.1  Create UnifiedToolRuntime (UTR) in runtime/tool_runtime.py
  P3.2  Migrate muscal_loop.py EXECUTORS (6) → UTR
  P3.3  Migrate tools.py TOOL_REGISTRY (3) → UTR
  P3.4  Add missing browser/desktop executors (11)
  P3.5  Create SafetyGate (consolidate 3 validators)
  P3.6  Rewire mel.py → UTR
  P3.7  Deprecate system_runtime.py

Phase 4 — CognitiveUnit (~3 weeks)
  P4.1  Define CognitiveUnit interface in features/
  P4.2  Implement CU = Worker + Memory + Tools + Governance
  P4.3  Wire Router → CU → Worker in kernel pipeline
  P4.4  Implement Agent Detection (ADR-021)
  P4.5  Add Agent Detection stage to pipeline

Phase 5 — Integration (~2 weeks)
  P5.1  Unified Runtime: merge Kernel REPL + Flask API
  P5.2  Event system consolidation (WriterThread + EventStore)
  P5.3  End-to-end certification tests
```

**Total estimated effort: ~10 weeks** (5 phases × 2 weeks average)

---

## E3.1 READINESS: CONDITIONAL GO

### Certification Checklist

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Current-state architecture factually reconciled | ✅ | D-E3.0.2-001 through D-E3.0.2-009 |
| 2 | Hot-path reachability documented | ✅ | D-E3.0.2-005 (27 HOT_PATH + 19 WARM_PATH components) |
| 3 | Pipeline Stages adopted, partially adopted, or deprecated | ✅ | ADR-020: ADOPT WITH REFACTORING |
| 4 | Tool runtime consolidation surface understood | ✅ | ADR-014 (updated to DRAFT) + D-E3.0.2-006 |
| 5 | Routing status factually established | ✅ | D-E3.0.2-002 (WARM_PATH working, HOT_PATH gap) |
| 6 | Governance status factually established | ✅ | D-E3.0.2-003 (GovernanceSync working, HOT_PATH gap) |
| 7 | Model-binding violations inventoried | ✅ | D-E3.0.2-001 §8 (5 bindings, none in HOT_PATH) |
| 8 | Immutability impact understood | ✅ | D-E3.0.2-008 (6 immutable files affected, override mechanism sufficient) |
| 9 | Canonical target model clearly separated | ✅ | §13 of this report |
| 10 | No unresolved factual contradiction | ✅ | All E3.0 errors corrected |

### Conditions

1. Begin with E3.1 Phase 1 (Pipeline Foundation) — do NOT skip to Phase 4 (CognitiveUnit)
2. Use `--allow-core-write` flag and commit kernel.py changes with explicit declaration (per OVERRIDE-060)
3. All existing tests must continue to pass after each Phase

### Next Action

**Start E3.1 Phase 1: Pipeline Foundation.**
1. Extract `kernel.py:run()` blocks into `stage_*()` methods
2. Wire `register_stage()` + `build_pipeline()` into `MuscalKernel.__init__()`
3. Adopt `features/pipeline/stages.py` as the default pipeline

---

*E3.0.2 certification complete. Repository is ready for E3.1 contract implementation.*
