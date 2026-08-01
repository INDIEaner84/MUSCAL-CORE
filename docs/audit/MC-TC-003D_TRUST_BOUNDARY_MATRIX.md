# MC-TC-003D — Trust Boundary Matrix (L0–L10)

---

## Semantic Ladder

| Level | Name | Internal? | Authoritative? | Claim? | Evidence? | Proof? | Crypto-Attestable? |
|-------|------|-----------|----------------|--------|-----------|--------|-------------------|
| L0 | HYPOTHESIS | Internal (LLM output) | No | Yes | No | No | No |
| L1 | INTENT | Internal (MKC parse) | No | Yes | No | No | No |
| L2 | PLAN | Internal (Bridge → ExecutionPlan) | No | Derived | No | No | No |
| L3 | PREDICTION / SIMULATION | Internal (simulated mode) | No | Yes | No | No | No |
| L4 | REQUESTED ACTION | Internal (MEL dispatch) | No | Yes | No | No | No |
| L5 | TOOL INVOCATION | Internal (UTR.execute) | Yes (call record) | No | Partial (receipt) | No | Partial (hash) |
| L6 | ACTUAL EXECUTION | External (tool runtime) | External authority | No | Yes (receipt) | Conditional | Yes (hash) |
| L7 | STATE MUTATION | External (world) | External only | No | External only | Conditional | Yes (if observable) |
| L8 | EVIDENCE | Internal (ExecutionReceipt) | Yes | No | Yes | Conditional | Yes (SHA-256) |
| L9 | VERIFICATION | Internal/External | Independent | No | Yes | Conditional | Yes |
| L10 | EXTERNAL REALITY | External | Absolute | No | Independent | Best effort | External |

---

## Trust Classification

### MUSCAL can prove:
- Event was persisted (SQLite AUTOINCREMENT, UNIQUE event_id)
- ExecutionReceipt integrity (SHA-256 hash recomputation)
- State path validity (validate_state_transition triple check)
- Causal reference (causation_id links — if correctly populated)

### MUSCAL can strongly evidence:
- Tool was invoked (UTR.execute() → ExecutionReceipt)
- Verification was performed (VerificationResult with verifier identity)
- Execution mode at event time (execution_mode column)

### MUSCAL can infer:
- Execution completed (state sequence planned→queued→running→completed)
- Correlation group (shared correlation_id)
- Claim vs non-claim (source of event)

### MUSCAL cannot know:
- External reality state (no ground-truth observation)
- Whether tool actually modified external system (trusts tool self-report)
- Whether persisted event corresponds to real execution (identity can be forged)
- Whether verification result is correct (trusts registered verifier function)

---

## Semantic Collapse Risks

| Collapse | Source | Risk | Mitigation |
|----------|--------|------|------------|
| Claim → Evidence | Agent report treated as proof | HIGH | _is_claim marker (advisory only) |
| Request → Execution | EXECUTION_STARTED treated as execution | HIGH | State machine validation |
| Invocation → Execution | Tool call treated as execution | MEDIUM | Integrity hash + independent verifier |
| Verification flag → Verification evidence | String field set without process | CRITICAL | No enforcement (P0-C03) |
| Persistence → Execution | Event in store = real execution | MEDIUM | No existence validation (P1-F05) |
| Simulation → Real | execution_mode='real' hardcoded | HIGH | P1-F02, P1-F03 |
| Causation → Direction | Receipt records self as cause | HIGH | P1-F04 |

---

## Level-by-Level Analysis

### L0: HYPOTHESIS — Agent/LLM claim before any processing
- No identity tracking
- No evidence
- Pure claim

### L1: INTENT — MKC parses input into structured intent
- Graph node created (NODE_TYPE_INTENT)
- No execution_id on node (MC-TC-003B added execution_id propagation to add_node, but intent nodes may not carry it if created before execution context is available)

### L2: PLAN — Bridge maps tasks to ExecutionPlan
- ExecutionPlan dataclass
- No execution_id on plan structure
- Causal link to intent via graph edges (DERIVES_FROM)

### L3: SIMULATION — execution_mode='simulated'
- ExecutionContext carries mode
- But kernel pipeline is IDENTICAL for simulation and real
- Events differentiated only by execution_mode field
- EventStore has no mode-based segregation

### L4: REQUEST — MEL dispatches tool requests
- Graph event SYSTEM_ACTION_STARTED
- Event contains execution_id (if enriched wrapper used)
- No authorization link in event

### L5: INVOCATION — UTR.execute() called
- Tool name, args recorded
- ExecutionReceipt generated
- SHA-256 integrity hash of receipt
- UTR execution_id (may differ from EnrichedMuscalOS execution_id — P0-C01)

### L6: EXECUTION — Tool runtime actual operation
- External system operation
- No internal visibility into execution
- MUSCAL trusts tool's self-report

### L7: MUTATION — External world changed
- Not observable internally
- Ground truth unknown without independent verification

### L8: EVIDENCE — ExecutionReceipt persisted
- receipt_id (uuid7)
- execution_id (may be wrong identity)
- success flag (from tool self-report)
- result_data (from tool self-report)
- integrity_hash (SHA-256 of receipt fields)

### L9: VERIFICATION — VerificationResult
- verifier identity (which verifier ran)
- status (verified/failed)
- receipt_id (link to evidence)
- execution_id (may be wrong identity — P0-C01)

### L10: EXTERNAL REALITY — Ground truth
- NOT captured
- FilesystemVerifier can partially read back file state
- No general external reality verification
- No external confirmation mechanism exists
