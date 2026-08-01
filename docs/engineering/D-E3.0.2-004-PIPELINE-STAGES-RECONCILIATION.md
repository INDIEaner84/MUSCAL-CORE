# D-E3.0.2-004 — PIPELINE STAGES RECONCILIATION

**Status:** NEW FINDING (not addressed by E3.0)
**Date:** 2026-07-22

---

## 1. Background

E3.0 did not address `features/pipeline/`. The directory contains 8 pipeline stage wrappers that were designed as composable alternatives to `MuscalKernel.run()`'s inline 8-step sequence. They are fully implemented but never wired into any production entry point.

## 2. Inventory of `features/pipeline/stages.py`

| Stage | Class | Order | Purpose | Calls on Kernel |
|-------|-------|-------|---------|-----------------|
| RAG | `RAGStage` | 10 | Context retrieval + enrichment | `self.k.stage_rag()` |
| MKC | `MKCStage` | 20 | MCXF compilation | `self.k.stage_mkc()` |
| MCXF | `MCXFStage` | 30 | MCXF section graph node | `self.k.stage_mcxf_section()` |
| Bridge | `BridgeStage` | 40 | MCXF → ExecutionPlan | `self.k.stage_bridge()` |
| Optimizer | `OptimizerStage` | 50 | Plan optimization | `self.k.stage_optimizer()` |
| MEL | `MELStage` | 60 | Tool execution | `self.k.stage_mel()` |
| Feedback | `FeedbackStage` | 70 | Failure analysis | `self.k.stage_feedback()` |
| Memory | `MemoryStage` | 80 | Memory persistence | `self.k.stage_memory()` |

## 3. Repository Evidence

| Evidence | Source |
|----------|--------|
| 8 stage classes defined | `features/pipeline/stages.py` (117 lines) |
| Stages call `self.k.stage_*()` methods | Lines 25, 37, 49, 61, 80, 92, 104, 116 |
| These methods do NOT exist on MuscalKernel | `kernel.py` has no `stage_rag()`, `stage_mkc()`, etc. |
| Zero imports from production code | `grep "from features.pipeline"` returns no results |
| `plugin_registry.py` supports stage registration | `register_stage()`, `build_pipeline()`, `STAGES` dict |
| Tests use `register_stage()`/`build_pipeline()` | `tests/test_boot_contract.py` (37 matches) |
| ADR-013-pipeline.md discusses pipeline vs plugin tension | `spec/ADR-013-pipeline.md` |
| `features/runtime/pipeline_builder.py` provides alternate builder | 56 lines, zero production imports |

## 4. Stage-Kernel Interface Mismatch

Each stage calls a `self.k.stage_*()` method that does not exist:

```python
class RAGStage:       ctx["context"], ... = self.k.stage_rag(...)        # DOES NOT EXIST
class MKCStage:       ctx["mcxf_dict"], ... = self.k.stage_mkc(...)      # DOES NOT EXIST
class MCXFStage:      ctx["section_id"] = self.k.stage_mcxf_section(...) # DOES NOT EXIST
class BridgeStage:    execution_plan, ... = self.k.stage_bridge(...)     # DOES NOT EXIST
class OptimizerStage: ctx["optimized_plan"] = self.k.stage_optimizer(...)# DOES NOT EXIST
class MELStage:       ctx["mel_result"] = self.k.stage_mel(...)          # DOES NOT EXIST
class FeedbackStage:  ctx["feedback"] = self.k.stage_feedback(...)       # DOES NOT EXIST
class MemoryStage:    ctx["mem_id"] = self.k.stage_memory(...)           # DOES NOT EXIST
```

The inline logic exists in `kernel.py:run()` lines 240–530 but is not extracted into named methods.

## 5. Classification

**ORPHANED** — no production caller found after full repository search.

## 6. Decision: PARTIALLY ADOPT

**Recommendation: ADOPT WITH REFACTORING**

The stage wrappers represent a sound architectural decomposition that aligns with the canonical pipeline model. However, they cannot be adopted as-is because:

1. The `self.k.stage_*()` methods do not exist on `MuscalKernel`
2. The wrappers don't handle Governance, Routing, or Agent detection (not part of the original kernel design)
3. The `features/` location is correct (plugin zone per immutability contract)

### Adoption Scope

| Stage | Adopt As-Is? | Refactoring Needed |
|-------|-------------|-------------------|
| RAGStage | No | Add `stage_rag()` to kernel; adopt wrapper in features/ |
| MKCStage | No | Add `stage_mkc()` to kernel; adopt wrapper in features/ |
| MCXFStage | No | Add `stage_mcxf_section()` to kernel; adopt wrapper in features/ |
| BridgeStage | No | Add `stage_bridge()` to kernel; adopt wrapper in features/ |
| OptimizerStage | No | Add `stage_optimizer()` to kernel; adopt wrapper in features/ |
| MELStage | No | Add `stage_mel()` to kernel; adopt wrapper in features/ |
| FeedbackStage | No | Add `stage_feedback()` to kernel; adopt wrapper in features/ |
| MemoryStage | No | Add `stage_memory()` to kernel; adopt wrapper in features/ |

### Migration Path

1. Extract `kernel.py:run()` each sequential block into `stage_*()` methods on MuscalKernel
2. Register the existing stage wrappers via `plugin_registry.register_stage()`
3. Replace the hard-coded 8-step sequence in `run()` with `build_pipeline()` iteration
4. Add new stages (Governance, Router, Agent Detection) as additional wrappers in `features/`
5. Deprecate the old inline sequence but keep it as fallback

### Compatibility

| Constraint | Status |
|------------|--------|
| ADR-001 (kernel as single entry) | Compatible — pipeline wraps kernel methods |
| Immutability contract | Requires core modification to add `stage_*()` methods to kernel.py |
| Plugin system | Compatible — stages are plugins in `features/` |
| Future MREIL | Compatible — stages can be replaced/ordered by MREIL commands |

## 7. E3.1 Consequence

**REQUIRES CORRECTIVE ACTION.** The `self.k.stage_*()` method gap must be closed. This is the recommended first task of E3.1 Phase 1 (Foundation) because all other E3.1 work depends on a modular pipeline.
