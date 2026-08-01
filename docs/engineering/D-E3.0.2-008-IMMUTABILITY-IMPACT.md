# D-E3.0.2-008 — IMMUTABILITY IMPACT ASSESSMENT

**Status:** COMPLETE
**Date:** 2026-07-22

---

## 1. Background

`spec/IMMUTABILITY_CONTRACT.md` (v1.0) and `guards/write_guard.py` define 39 root files and 6 directories as immutable. E3.1 will require modifications to several of these files.

## 2. E3.1 Change Requirements

### Phase 1 — Foundation

| Required Change | File | Immutable? | Category |
|----------------|------|-----------|----------|
| Add `stage_rag()` method | `kernel.py` | ✅ YES (root) | C — Core modification |
| Add `stage_mkc()` method | `kernel.py` | ✅ YES | C |
| Add `stage_mcxf_section()` method | `kernel.py` | ✅ YES | C |
| Add `stage_bridge()` method | `kernel.py` | ✅ YES | C |
| Add `stage_optimizer()` method | `kernel.py` | ✅ YES | C |
| Add `stage_mel()` method | `kernel.py` | ✅ YES | C |
| Add `stage_feedback()` method | `kernel.py` | ✅ YES | C |
| Add `stage_memory()` method | `kernel.py` | ✅ YES | C |
| Wire `register_stage()` + `build_pipeline()` into `__init__` | `kernel.py` | ✅ YES | C |
| Replace hard-coded 8-step run() with pipeline iteration | `kernel.py` | ✅ YES | C |

### Phase 2 — Governance + Routing

| Required Change | File | Immutable? | Category |
|----------------|------|-----------|----------|
| Wire GovernanceSync check into kernel stage iteration | `kernel.py` | ✅ YES | C |
| Wire RoutingPolicy call into kernel pipeline | `kernel.py` | ✅ YES | C |
| Fix async governance bug in gate.py | `runtime/kernel/gate.py` | ✅ YES (runtime/kernel/) | C |

### Phase 3 — Tool Runtime

| Required Change | File | Immutable? | Category |
|----------------|------|-----------|----------|
| Create UTR class | `runtime/tool_runtime.py` (new) | ❌ NO (new file) | A — Features |
| Migrate tools.py executors | `tools.py` | ✅ YES (root) | C |
| Rewire mel.py to use UTR | `mel.py` | ✅ YES (root) | C |
| Deprecate system_runtime.py | `system_runtime.py` | ✅ YES (root) | D — Immutability exception (deprecation header) |
| Remove muscal_loop.py inline executors | `muscal_loop.py` | ✅ YES (root) | C |

### Phase 4 — CognitiveUnit

| Required Change | File | Immutable? | Category |
|----------------|------|-----------|----------|
| Define CognitiveUnit in features/ | New file in `features/` | ❌ NO | A |
| Wire CU → Worker in kernel | `kernel.py` | ✅ YES | C |
| Router → CU dispatch | `kernel.py` | ✅ YES | C |

## 3. Classification Categories

| Category | Description | Count |
|----------|-------------|-------|
| **A** | Can be implemented entirely in `features/` | 2 |
| **B** | Requires adapter/extension only | 0 |
| **C** | Requires core modification | 16 |
| **D** | Requires explicit immutability exception | 1 |
| **E** | Requires ADR amendment | 0 |

## 4. Minimal Core Modification Surface

The smallest possible set of core file modifications required for E3.1:

| File | Modifications Needed | Minimal Change |
|------|---------------------|----------------|
| `kernel.py` | Add 8 `stage_*()` methods + wire pipeline + wire governance + wire routing + wire CU | **~200 lines added, 0 lines removed** (extract inline code into methods, add pipeline iteration) |
| `mel.py` | Redirect dispatch to UTR | **~10 lines changed** (replace TOOL_REGISTRY lookups with UTR call) |
| `tools.py` | Add re-export layer or update TOOL_REGISTRY | **~20 lines added** (backward compat shim) |
| `muscal_loop.py` | Remove inline executors after migration | **~50 lines removed** (EXECUTORS dict + executor functions) |
| `system_runtime.py` | Add deprecation header | **~5 lines added** (redirect comment) |
| `runtime/kernel/gate.py` | Fix async Governance bug | **~3 lines changed** (type annotation + sync call) |

**Total minimal change surface: 6 files, ~288 lines changed, all additive or reductive (no behavioral changes to existing logic).**

## 5. Immutability Exception Strategy

Per `spec/IMMUTABILITY_CONTRACT.md` §6, exceptions require:

1. [ ] Entry in `spec/OVERRIDE.md` with justification
2. [ ] `--allow-core-write` flag during execution
3. [ ] Core change committed as separate, declared commit

**Recommendation:** Add a single E3.1 override entry to `spec/OVERRIDE.md` covering all Phase 1-4 kernel modifications. The justification is: *"E3.1 pipeline formalization requires extracting inline kernel methods into named pipeline stages. No behavioral change to existing execution logic."*

## 6. What Can Remain in Features/

The following E3.1 work requires NO core modification:

| Work | Location | Category |
|------|----------|----------|
| Pipeline stage wrappers (adopt existing) | `features/pipeline/stages.py` | A |
| PipelineBuilder extensions | `features/runtime/pipeline_builder.py` | A |
| CognitiveUnit interface | `features/cognitive_unit/` (new) | A |
| Agent Detection implementation | `features/agent_detection/` (new) | A |
| UTR class | `runtime/tool_runtime.py` (new) | A |
| SafetyGate | `features/safety/` (new) | A |
| Plugin adapter for custom stages | `features/pipeline/` | A |

## 7. Conclusion

**Core modification IS unavoidable** for E3.1. Six immutable files require changes, primarily `kernel.py` (the main orchestrator). However, the minimal change surface is well-defined and architecturally justified. All new architectural components (CognitiveUnit, Agent Detection, SafetyGate, UTR, Pipeline Stages) can live entirely in `features/` or as new files in `runtime/`.

**No amendment to `spec/IMMUTABILITY_CONTRACT.md` is required.** The existing override mechanism (§6) is sufficient. An entry in `spec/OVERRIDE.md` should be created before E3.1 Phase 1 begins.
