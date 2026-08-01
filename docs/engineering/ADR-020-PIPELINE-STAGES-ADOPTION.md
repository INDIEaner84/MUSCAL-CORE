# ADR-020: Pipeline Stages Adoption

**Status:** DRAFT
**Date:** 2026-07-22
**Supersedes:** ADR-013-pipeline.md (extends)

---

## Context

`features/pipeline/stages.py` contains 8 fully composed pipeline stage wrappers (RAGStage, MKCStage, MCXFStage, BridgeStage, OptimizerStage, MELStage, FeedbackStage, MemoryStage) that are currently orphaned — no production code imports or calls them. They were designed as composable alternatives to the hard-coded 8-step sequence in `MuscalKernel.run()`.

The E3.0.2 independent reconciliation verified:
- The wrappers are architecturally sound (each maps 1:1 to a step in `kernel.py:run()`)
- The interface they depend on (`self.k.stage_*()` methods) does NOT exist on `MuscalKernel`
- `plugin_registry.py` already supports `register_stage()` and `build_pipeline()` but has never been wired into `kernel.py`

## Current State

`MuscalKernel.run()` (lines 240–530 of `kernel.py`) implements an 8-step pipeline as hard-coded sequential method calls:

```python
# 1. RAG context retrieval + enrichment  (lines 242-267)
# 2. MKC compile → MCXF dict             (lines 270-308)
# 3. MCXF document section node           (lines 311-327)
# 4. Bridge: MCXF → ExecutionPlan         (lines 330-391)
# 5. Optimizer: ExecutionPlan → Optimized (lines 394-416)
# 6. MEL execute                          (lines 419-452)
# 7. Feedback analysis                    (lines 455-483)
# 8. Memory persist                       (lines 486-516)
```

Each step has its own error handling, debugger hooks, and graph operations. The code is functional but monolithic — plugins cannot add, remove, or reorder stages without modifying `kernel.py` directly.

## Decision

**ADOPT WITH REFACTORING.**

The 8 existing stage wrappers in `features/pipeline/stages.py` become the migration foundation for E3.1 pipeline formalization.

### Scope of Adoption

| Stage Wrapper | Status | Refactoring Needed |
|---------------|--------|-------------------|
| `RAGStage` | Adopt as foundation | Add `kernel.stage_rag()` method |
| `MKCStage` | Adopt as foundation | Add `kernel.stage_mkc()` method |
| `MCXFStage` | Adopt as foundation | Add `kernel.stage_mcxf_section()` method |
| `BridgeStage` | Adopt as foundation | Add `kernel.stage_bridge()` method |
| `OptimizerStage` | Adopt as foundation | Add `kernel.stage_optimizer()` method |
| `MELStage` | Adopt as foundation | Add `kernel.stage_mel()` method |
| `FeedbackStage` | Adopt as foundation | Add `kernel.stage_feedback()` method |
| `MemoryStage` | Adopt as foundation | Add `kernel.stage_memory()` method |

### Migration Path

1. Extract each block in `kernel.py:run()` into a `stage_*()` method on `MuscalKernel`
2. Register the 8 existing stage wrappers via `plugin_registry.register_stage()`
3. Replace the hard-coded 8-step sequence with `build_pipeline()` iteration
4. Add Governance, Routing, and Agent Detection stages as new wrappers in `features/pipeline/`
5. Keep the inline sequence as a fallback for backward compatibility

### Compatibility

| Constraint | Assessment |
|------------|------------|
| ADR-001 (Kernel as single entry point) | Compatible — pipeline wraps kernel methods, does not replace kernel |
| ADR-004 (Plugins) | Compatible — stages are registered via existing plugin_registry |
| ADR-005 (Pipeline) | Compatible — extends ADR-005's plugin hook model to full pipeline composition |
| ADR-007 (Immutability) | Compatible — requires core modification exception for adding `stage_*()` methods to kernel.py |
| Future MREIL | Compatible — pipeline stages can be individually addressed and reordered by MREIL commands |

### Rollback Strategy

If pipeline adoption causes instability:
1. `kernel.py` retains the original inline code until E3.2
2. Set `MUSCAL_PIPELINE_MODE=inline` environment variable to bypass pipeline
3. The pipeline implementation can be toggled via a flag in `MuscalKernel.__init__()`

## Consequences

- **+** Modular pipeline: stages can be added, removed, or reordered by plugins
- **+** Stage isolation: each stage has its own error handling (no cascade failures)
- **+** Testability: stages can be unit-tested independently
- **+** Migration reuses existing code: the stage wrappers already exist, only the kernel methods need to be extracted
- **-** `kernel.py` must be modified (requires `--allow-core-write` and `spec/OVERRIDE.md` entry)
- **-** Pipeline overhead: context dict passing between stages adds indirection
- **-** Learning curve: developers must understand stage registration ordering

## Compliance

- Pipeline stages live in `features/pipeline/` (plugin zone)
- `kernel.py` modification requires `spec/OVERRIDE.md` entry + `--allow-core-write`
- No existing tests break (inline code is preserved until E3.2)
- This ADR supersedes ADR-013-pipeline.md's unresolved tension between pipeline and immutability
