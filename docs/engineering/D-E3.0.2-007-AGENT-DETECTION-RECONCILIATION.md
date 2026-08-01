# D-E3.0.2-007 — AGENT DETECTION RECONCILIATION

**Status:** CORRECTED (NEW FINDING — not addressed by E3.0)
**Date:** 2026-07-22

---

## 1. Background

E3.0 did not address Agent Detection. The canonical architecture (AMS-001 v1.0) specifies that a Router component should detect Agent type from task analysis. No such mechanism exists in the current codebase.

## 2. Repository Evidence

| Claim | Evidence |
|-------|----------|
| `agent_detection.py` exists in MUSCAL CORE | **FALSE** — file not found on disk |
| `router_agent_tasks.py` exists in MUSCAL CORE | **FALSE** — file not found on disk |
| Any agent registry exists | **FALSE** — `agents/` directory has `Agent.py`, `AIAgent.py` but no registry or detection logic |
| Any task classification → agent routing exists | **FALSE** — `MuscalKernel.run()` has no agent classification step |

## 3. What Exists

The `agents/` directory contains:

| File | Purpose |
|------|---------|
| `agents/Agent.py` | Base Agent class |
| `agents/AIAgent.py` | AI-powered Agent subclass |
| `agents/__init__.py` | Package init |

These are data/type definitions, not routing or detection logic. No code in the hot path references them.

## 4. Classification

**NOT IMPLEMENTED.** No Agent Detection component exists in the current codebase.

## 5. Architectural Impact

- The canonical Router → Agent detection → CognitiveUnit → Worker pipeline has a gap at the first step
- Without Agent detection, E3.1 cannot implement dynamic task routing based on Agent capability
- This is a genuine architectural gap that E3.1 must address

## 6. ADR-021 Justification

**ADR-021 IS JUSTIFIED.** Agent Detection / Task Classification is a distinct architectural decision that cannot be cleanly covered by existing ADRs:

| ADR | Covers Agent Detection? |
|-----|------------------------|
| ADR-001 (Kernel) | No — kernel is entry point, not routing |
| ADR-005 (Pipeline) | No — pipeline composition, not agent types |
| ADR-014 (Tool Runtime) | No — tool execution, not task classification |

ADR-021 should formalize:
- **CURRENT:** No agent detection exists
- **TARGET:** Router analyzes task → determines Agent type → dispatches to appropriate CU
- **MIGRATION:** Start with a simple task-type → worker mapping (leveraging existing `scheduler.py:RoutingPolicy` pattern), evolve to ML-based classification

## 7. E3.1 Consequence

**REQUIRES NEW CONTRACT.** Agent Detection is a genuine E3.1 gap. It should be addressed in E3.1 Phase 4 (CognitiveUnit) after the pipeline, governance, routing, and tool runtime foundations are in place.
