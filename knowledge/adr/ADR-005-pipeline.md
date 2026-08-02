# ADR-005: Pipeline Architecture — Monolithic Data Flow

**Status:** ACCEPTED  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 has a single sequential pipeline in `kernel.py` (`MuscalKernel.run()`):

```
Input
  │
  ▼
┌──────────────┐
│  1. RAG      │  rag.retrieve() + rag.enrich()
│  Enrichment  │  → context = [memory entries]
└──────┬───────┘
       │ enriched_input (str)
       ▼
┌──────────────┐
│  2. MKC      │  mkc.compile() → MCXF dict
│  Compile     │  → mcxf = MCXFDocument (validated)
└──────┬───────┘
       │ mcxf (MCXFDocument)
       ▼
┌──────────────┐
│  3. Bridge   │  map_tasks() → ExecutionPlan
│  Mapping     │  validate_plan() → ValidationResult
└──────┬───────┘
       │ execution_plan (ExecutionPlan)
       ▼
┌──────────────┐
│  4. Optimizer│  OptimizerPipeline.optimize()
│  Optimization│  → OptimizedPlan (DAG + layers)
└──────┬───────┘
       │ optimized_plan (OptimizedPlan)
       ▼
┌──────────────┐
│  5. MEL      │  execute() → list of results
│  Execution   │  per-step execution via TOOL_REGISTRY
└──────┬───────┘
       │ execution_results (list[dict])
       ▼
┌──────────────┐
│  6. Feedback │  analyze_feedback()
│  Analysis    │  → FeedbackReport
└──────┬───────┘
       │ feedback (FeedbackReport)
       ▼
┌──────────────┐
│  7. Memory   │  store_snapshot()
│  Storage     │  → memory_id (int)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  KernelResult│  mcxf + execution + memory_id
│              │  + feedback + success + errors
└──────────────┘
```

### Key Characteristics

- **Monolithic**: All 7 stages in one method (448 LOC), sequential
- **Synchronous**: Each stage blocks until complete
- **Single-threaded**: No parallelism within a single run
- **Error boundary**: If MKC fails (invalid MCXF), the entire run fails
- **Plugin hooks**: 14 hooks woven between stages via `run_hooks()`
- **Graph side-effects**: Most stages write to `GraphState` (nodes, edges, events)

### Identified Risks

1. **Stage coupling**: Optimizer expects ExecutionPlan; Bridge expects MCXF — error recovery requires type knowledge across stages
2. **No stage isolation**: A crash in any stage corrupts the entire kernel object state (graph nodes in inconsistent state)
3. **Hard to test in isolation**: `kernel.run()` spawns all 7 stages — no lightweight path for single-stage testing
4. **Plugin hook timing**: Hooks fire at fixed points; a plugin that needs data between Optimizer and MEL has no hook

---

## Decision

**Keep the monolith for v0.8. Do NOT decompose into micro-pipeline services.**

### Rationale

| Option | Pros | Cons |
|--------|------|------|
| **Monolith (current)** | Simple, tested, 18/18 pass | Stage coupling, no isolation |
| **Micro-pipeline** | Stage isolation, independent scaling | Async overhead, state sync, no clear benefit for single-user |
| **Pipeline DAG** | Flexible stage wiring | Over-engineering, 7 stages don't need DAG yet |

The monolith is not beautiful, but it is:
- **Correct**: 18 tests confirm end-to-end behavior
- **Measured**: Stress test (100 iterations, 0 crashes)
- **Comprehensible**: One method, 7 commented stages, 448 LOC
- **Extensible**: Plugin hooks at every stage boundary

### Guardrails for Monolith Stability

| Guard | Mechanism | Since |
|-------|-----------|-------|
| **Write Guard** | Blocks modifications to kernel.py | v0.7 |
| **Plugin hooks** | All extensions go to features/ | v0.7 |
| **Stress test** | CI fails if 100 iter crashes | v0.7 |
| **Hook coverage** | CI checks all 14 hooks fire | v0.7 |

### When to Re-evaluate

Trigger conditions for pipeline decomposition:

- Pipeline exceeds **1,000 LOC** (currently 448)
- More than **3 parallel execution paths** needed (e.g., multi-model, multi-agent)
- Plugin count exceeds **20** (currently 6)
- Latency requirement below **50ms per run** (currently ~100ms for simple inputs)

---

## Migration Plan

### Phase 1: Stage Error Boundaries (v0.8)

Wrap each stage in try/except to log + continue:

```python
def run(self, input_text):
    try:
        self._stage_rag(input_text)
    except Exception as e:
        return KernelResult(success=False, errors=[f"RAG failed: {e}"])
    # ...
```

Currently, any exception propagates to the caller.

### Phase 2: Lightweight Per-Stage Test Entry Points

Expose `_stage_mkc`, `_stage_bridge`, etc. as public methods so they can be tested in isolation without running the full pipeline.

### Phase 3: Stage Metrics

Each stage reports:
- Duration (ms)
- Input/output sizes (bytes, node counts)
- Error count

Aggregated into `KernelResult.stage_metrics: dict`.

---

## Consequences

### Positive
- Zero refactoring cost for v0.8
- Stage error boundaries prevent total pipeline crash
- Per-stage metrics enable performance monitoring

### Negative
- Stage coupling remains — `_stage_bridge` still expects `mcxf` from `_stage_mkc`
- No parallel execution possible
- Plugin hooks remain fixed-position (no custom hook injection)

---

## Compliance Check

- [ ] Phase 1: try/except per stage with graceful fallback
- [ ] Phase 2: Public per-stage methods (`_stage_mkc()`, `_stage_bridge()`, etc.)
- [ ] Phase 3: Stage metrics in `KernelResult`
- [ ] Monolith LOC < 1,000
- [ ] Plugin count < 20
- [ ] 18/18 tests pass after each phase
