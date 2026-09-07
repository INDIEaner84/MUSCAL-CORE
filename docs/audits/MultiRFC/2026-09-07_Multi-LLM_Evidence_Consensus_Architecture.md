# Multi-LLM Evidence & Consensus Architecture — Session Audit

**Date:** 2026-09-07
**Session:** Multi-LLM Evidence & Consensus Architecture Design & Implementation
**Status:** COMPLETE — All 4 Phases + Enhancements Merged to Main

---

## Executive Summary

This session designed and implemented a complete Multi-LLM Evidence & Consensus Architecture for MUSCAL CORE, integrating specialized LLM agents (Auditor, Architect, Implementation Reviewer, Judge) via provider-agnostic abstractions with versioned, commit-bound evidence.

---

## Architecture Overview

### Phase 1: Evidence Foundation (Commit `5e036c8`)
- **Files:** 9 | **Tests:** 10
- Schemas: `ReviewTask`, `ReviewFinding`, `TechnicalVerification`, `Consensus`
- Evidence Store: Wrapper around existing EventStore (append-only, hash-chained)
- Deterministic components: TechnicalVerifier, ConsensusBuilder
- Reused existing: EventStore, MCPL, EvaluationClaim, EvidenceRef, Hash-Chain

### Phase 1b: Provider Abstraction (Commit `6702ea8`)
- **Files:** 8 | **Tests:** 21
- `LLMProvider` protocol (analyze, chat, capabilities, metrics)
- `LLMProviderRegistry` with role-based routing + `TaskFit`
- Env-based config: `LLM_{ROLE}_PROVIDER_ID`, `_TYPE`, `_MODEL`, `_API_KEY`
- No hardcoded models — all via env vars
- Roles: auditor, architect, reviewer, judge, orchestrator

### Phase 2: Review Agents (Commit `63fedb2`, PR #2)
- **Files:** 8 | **Tests:** 18
- **AuditorAgent** (auditor): Security, gaps, stubs, execution gap — temp 0.1
- **ArchitectAgent** (architect): Architecture, contracts, invariants — temp 0.2
- **ImplementationReviewerAgent** (reviewer): Correctness, quality, standards — temp 0.1
- **JudgeAgent** (judge): Synthesis, conflict resolution, dissent — temp 0.0
- Base class: structured JSON schema output, EvidenceRef parsing, lazy provider loading
- Factory: `create_agent(role)`, `create_all_agents()`

### Phase 3: Arena/Consensus Pipeline (Commit `868defe`)
- **Files:** 6 | **Tests:** 14
- `ReviewOrchestrator`: Evidence → Agents → Consensus pipeline
- `PipelineReviewIntegration`: MUSCAL pipeline hooks (`on_execution_completed`, `on_pull_request`)
- CLI: `run --commit <sha> --type <type>`, `pr-comment`
- Evidence hierarchy enforced: **Technical Verification > Model Consensus**

### Phase 4: GitHub CI Integration (Commit `30122ea`)
- **Files:** 2 (workflow + CLI extension)
- `.github/workflows/multi-llm-review.yml`: push/PR/dispatch triggers
- GitHub Secrets for all LLM provider configs
- Evidence artifacts (90-day retention), PR auto-comments
- Fails on CONTRADICTION/UNVERIFIED

### Phase 4-5: Cost/Retention/Metrics (Commit `3158c18`)
- **Cost Tracking**: Per-agent + total cost/token tracking in orchestrator & agents
- **Budget Monitoring**: GitHub workflow with budget alerts, Step Summary
- **Evidence Retention**: CLI `cleanup` command + weekly scheduled cleanup job
- **Metrics**: Cost reporting in GitHub Step Summary, budget alerts

---

## Architecture Compliance

| Principle | Implementation |
|-----------|----------------|
| No duplicate Store/Provenance | Reuses EventStore, MCPL, EvaluationClaim, EvidenceRef, Hash-Chain |
| write_guard.py consistent | All 33 files in `features/` or `.github/` |
| Model Consensus ≠ Technical Verification | Separated pipelines, Technical > Model priority |
| Provider abstraction FIRST | Phase 1b before Phase 2/3/4 |
| No hardcoded models | All via `LLM_{ROLE}_*` env vars |
| No parallel systems | Reuses EventStore, MCPL, OutcomeRecord pattern |

---

## Validations (All Passing)

| Check | Status |
|-------|--------|
| Tests (63) | ✅ Pass |
| Guards (sync/drift/confidence) | ✅ OK |
| Ruff Lint | ✅ Clean |
| write_guard.py | ✅ 33/33 files allowed |

---

## Final Deliverables

| Phase | Component | Path |
|-------|-----------|------|
| 1 | Evidence Foundation | `features/multi_llm_review/` |
| 1b | Provider Abstraction | `features/llm_provider/` |
| 2 | Review Agents | `features/multi_llm_review/agents/` |
| 3 | Arena Pipeline | `features/multi_llm_review/orchestrator/` |
| 4 | GitHub CI | `.github/workflows/multi-llm-review.yml` + `cli.py` |
| 5 | Cost/Retention/Metrics | Integrated in all above |

---

## Key Architectural Decisions

1. **Evidence ≠ LLM Opinion** — LLM output = Observation → Evidence → Claim → Conflict → Consensus → Action
2. **Evidence Hierarchy** (strongest first):
   1. Runtime Observables
   2. Executable Test Results
   3. Repository Code
   4. Cryptographic Integrity
   5. EventStore/MCPL Events
   6. Configuration
   7. ADRs
   8. SSOT
   9. LLM Analysis (weakest)
   10. LLM Consensus (weakest)
3. **Arena ≠ Root of Trust** — Consensus → Proposed Actions → Governance Gate → SSOT/AKO
4. **Evidence Immutability** — Original evidence never overwritten; contradictions add new evidence + status transition
5. **Provider-Agnostic** — All LLMs swappable via `LLMProvider` protocol + registry
6. **Read-Only Agents** — Review agents: `repo.read`, `repo.history.read`, `evidence.write.own` only

---

## Secrets Required for Production

```bash
LLM_AUDITOR_PROVIDER, LLM_AUDITOR_MODEL, LLM_AUDITOR_API_KEY
LLM_ARCHITECT_PROVIDER, LLM_ARCHITECT_MODEL, LLM_ARCHITECT_API_KEY
LLM_REVIEWER_PROVIDER, LLM_REVIEWER_MODEL, LLM_REVIEWER_API_KEY
LLM_JUDGE_PROVIDER, LLM_JUDGE_MODEL, LLM_JUDGE_API_KEY
LLM_ORCHESTRATOR_PROVIDER, LLM_ORCHESTRATOR_MODEL, LLM_ORCHESTRATOR_API_KEY
MUSCAL_COST_BUDGET_MONTHLY (default: 50)
MUSCAL_EVIDENCE_RETENTION_DAYS (default: 90)
```

---

## Test Coverage

| Module | Tests |
|--------|-------|
| `features/multi_llm_review/tests/` | 10 |
| `features/multi_llm_review/agents/tests/` | 18 |
| `features/multi_llm_review/orchestrator/tests/` | 14 |
| `features/llm_provider/tests/` | 21 |
| **Total** | **63** |

---

## Next Steps (Future Phases)

| Phase | Description |
|-------|-------------|
| **Phase 6** | GitHub Integration Deepening — Auto-merge on VERIFIED, branch protection, review assignment |
| **Phase 7** | ADR Automation — Auto-generate ADR drafts from consensus, link findings to ADRs |
| **Phase 8** | Metrics & Observability — Review latency, cost tracking, agent accuracy dashboard |
| **Phase 9** | Multi-Repo Support — Cross-repository reviews, dependency analysis |

---

## Git History

| Commit | Message |
|--------|---------|
| `3158c18` | feat: Phase 4-5 enhancements - Cost monitoring, evidence retention, metrics |
| `30122ea` | feat: Phase 4 GitHub CI Integration for Multi-LLM Evidence Architecture |
| `868defe` | feat: Phase 3 Arena/Consensus Pipeline for Multi-LLM Evidence Architecture |
| `63fedb2` | Merge pull request #2 from INDIEaner84/feature/phase2-review-agents |
| `d582e6d` | feat: Phase 2 Review Agents for Multi-LLM Evidence Architecture |
| `6702ea8` | feat: Phase 1b Provider Abstraction for Multi-LLM Architecture |
| `5e036c8` | feat: Phase 1 Multi-LLM Evidence & Consensus Architecture |

---

**Audit Complete** — All phases implemented, tested, validated, and merged to `main` (`3158c18`).