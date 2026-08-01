# ADR-021: Agent Detection and Task Classification Formalization

**Status:** DRAFT
**Date:** 2026-07-22

---

## Context

The canonical MUSCAL architecture (AMS-001 v1.0) specifies that a Router component should detect the Agent type from task analysis and dispatch the task to the appropriate CognitiveUnit. No such mechanism exists in the current codebase.

The E3.0.2 independent reconciliation verified:

| Claim | Evidence |
|-------|----------|
| `agent_detection.py` exists | **FALSE** — file not found on disk |
| `router_agent_tasks.py` exists | **FALSE** — file not found on disk |
| Any agent registry or detection logic exists | **FALSE** — `agents/Agent.py` and `agents/AIAgent.py` are data types only |
| Any task-to-agent routing exists | **FALSE** — no code references agents in any production entry point |

## Current State

**No Agent Detection capability exists.** The `MuscalKernel.run()` pipeline has no step for classifying tasks or detecting which Agent should handle them. The only routing mechanism is `runtime/kernel/scheduler.py:RoutingPolicy`, which maps `task_type` to `worker_id` — a static DB-backed lookup, not an Agent detection system.

## Decision

**ADD A NEW ARCHITECTURAL DOMAIN: AGENT DETECTION**

This is a distinct architectural decision that cannot be cleanly covered by existing ADRs:

| ADR | Covers Agent Detection? | Reason |
|-----|------------------------|--------|
| ADR-001 (Kernel) | No | Kernel is entry point, not routing |
| ADR-005 (Pipeline) | No | Pipeline composition, not agent types |
| ADR-014 (Tool Runtime) | No | Tool execution, not task classification |
| ADR-020 (Pipeline Stages) | No | Pipeline adoption, not detection logic |

### CURRENT (what exists today)

- Router domain: `scheduler.py:RoutingPolicy` — static `task_type → worker_id` mapping from DB
- No agent types: Agents are data classes in `agents/`, never instantiated or routed to
- No task classification: MKC produces MCXF tasks but no code analyzes task semantics for agent suitability

### TARGET (what should exist in canonical architecture)

- **Router** component in the kernel pipeline analyzes task output from MKC
- Router determines **Agent type** (analytical, creative, research, operational, etc.)
- Router dispatches to the appropriate **CognitiveUnit** (Worker + Memory + Tools + Governance)
- Agent detection uses a combination of: task keyword analysis, task complexity scoring, historical success rates

### MIGRATION (how existing implementation could evolve)

1. **Phase 1** (E3.1): Extend `RoutingPolicy` to return an Agent type instead of a worker_id. Seed with keyword-based classification (same pattern as `muscal_loop.py:STUB_KEYWORDS`).
2. **Phase 2** (E3.2): Implement model-based Agent detection using the existing LLM providers (`runtime/llm/models.py`).
3. **Phase 3** (E3.3): Full CU-based dispatch with historical learning.

## Consequences

- **+** Fills a genuine architectural gap in the canonical pipeline
- **+** Reuses existing RoutingPolicy infrastructure
- **+** Enables dynamic Agent-CU binding
- **-** Requires new code in `features/` (no core modification except pipeline integration)
- **-** Adds complexity to the kernel pipeline (another stage)
- **-** ML-based detection may require new providers

## Compliance

- Agent Detection implementation lives in `features/agent_detection/` (plugin zone)
- Pipeline integration requires adding a stage to the pipeline (via ADR-020's `register_stage()`)
- No immutable files modified except `kernel.py` (for stage method addition, covered by ADR-020 override)
