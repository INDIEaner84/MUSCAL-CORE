# MUSCAL Execution Integrity Contract v1.0

**CLAIM ≠ PROOF**
**RECEIPT ≠ VERIFICATION**
**VERIFICATION ≠ GROUND TRUTH**

---

## 1. Core Distinctions

| Concept | Definition | Authority | Mutable? | Example |
|---------|------------|-----------|----------|---------|
| **Intent** | What the agent wants to achieve | Agent (LLM) | Yes | "write file /tmp/x with content hello" |
| **Plan** | Structured steps to satisfy intent | Bridge/MKC | Yes | ExecutionPlan with steps |
| **Claim** | What the agent asserts happened | Agent (LLM) | Yes | "I wrote the file" |
| **Authorization** | System permission for an action | Governance + SafetyGate | No (after check) | GovernanceDecision, SafetyResult |
| **Execution Request** | Actual call to UTR.execute() | MEL/CU/Pipeline | No | UTR.execute("filesystem.write", args) |
| **Execution Result** | Raw executor return value | Executor function | No | {"status": "written", "path": "..."} |
| **Execution Receipt** | Immutable evidence of execution | UTR (canonical) | Tamper-evident | ExecutionReceipt with hash |
| **Verification Request** | Call to UTR.verify() | VerifierCU/Policy | No | UTR.verify(receipt_id=...) |
| **Verification Result** | Independent check result | Verifier function | No (canonical) | VerificationResult(status="VERIFIED") |
| **Ground Truth** | Authoritative external state | Filesystem/external system | External | File content on disk |

---

## 2. Trust Boundaries

```
    ┌──────────────────────────────────────────────────────┐
    │                   UNTRUSTED                           │
    │  Agent (LLM) → Intent → Claim                        │
    └────────────────────┬─────────────────────────────────┘
                         │ execution_request
                         ▼
    ┌──────────────────────────────────────────────────────┐
    │              TRUSTED BOUNDARY                         │
    │  Authorization (Governance + SafetyGate)              │
    │  Execution (UTR)                                      │
    │  Receipt Generation (UTR canonical)                   │
    │  Verification (Verifier functions)                    │
    └────────────────────┬─────────────────────────────────┘
                         │ verified?
                         ▼
    ┌──────────────────────────────────────────────────────┐
    │                EXTERNAL / GROUND TRUTH                │
    │  Filesystem, Browser state, OS state                  │
    └──────────────────────────────────────────────────────┘
```

**Rules:**
- Agent claims MUST NOT enter the trusted boundary as evidence
- Agent claims MAY enter as execution requests (authorized)
- Receipts MUST be generated only by UTR (canonical)
- Verification MUST be independent of agent claims
- Ground truth is the ONLY authoritative state source
- `INCONCLUSIVE` MUST NEVER be promoted to `VERIFIED`

---

## 3. ExecutionReceipt Immutability

Every `ExecutionReceipt` carries a `sha256` integrity hash computed over:

```
hash = sha256(
    receipt_id + "|" +
    tool_name + "|" +
    json(args, sort_keys) + "|" +
    json(result_data, sort_keys) + "|" +
    str(success) + "|" +
    str(timestamp) + "|" +
    execution_id + "|" +
    correlation_id
)
```

- The hash is computed once during `_finalize()` and frozen
- Any mutation of receipt fields invalidates the hash
- `verify_integrity()` recomputes the hash and compares
- A receipt with an invalid hash is treated as TAMPERED

---

## 4. VerificationResult Canonical Form

```
VerificationResult:
  verification_id: str (uuid)
  execution_id: str
  receipt_id: str
  verifier_id: str ("math.add", "filesystem.write", etc.)
  status: VerificationStatus (VERIFIED | FAILED | INCONCLUSIVE | NOT_SUPPORTED)
  expected_state: dict (what was expected — from verifier, NOT agent)
  observed_state: dict (what was actually observed)
  state_diff: dict (differences, machine-readable)
  evidence: dict (supporting evidence)
  verified_at: float (timestamp)
```

**Status semantics:**

| Status | Meaning | Can promote? |
|--------|---------|-------------|
| VERIFIED | Expected state matches observed | OK |
| FAILED | Expected state DOES NOT match observed | OK |
| INCONCLUSIVE | Cannot determine (verifier unavailable, timeout, etc.) | MUST NOT → VERIFIED |
| NOT_SUPPORTED | No verifier registered for this tool | OK |

---

## 5. Provenance Chain

```
execution_id (unique per execution attempt)
  ├── authorization_id (from Governance + SafetyGate)
  ├── parent_execution_id (for multi-step: previous step)
  └── correlation_id (shared across multi-step scenarios)
```

Every receipt binds to:
- execution_id (unique)
- tool_name (what was executed)
- input (args hash)
- output (result_data hash)
- authorization (safety + governance)

---

## 6. Idempotency

| Scenario | Detection | Action |
|----------|-----------|--------|
| Same execution_id | Match in _execution_store | Return DUPLICATE_DETECTED |
| Same tool + args (no execution_id) | Not detected (different receipt) | Execute again |
| Retry after timeout | New execution_id | Execute again |
| Replay of old receipt_id | Not matched | Not possible (receipt_id is UUID) |

---

## 7. Verification Independence

| Tool | Verifier | Source of Truth | Agent Influence |
|------|----------|-----------------|-----------------|
| math.add | Recomputation | Python computation | None (args are independent) |
| filesystem.write | File read-back | Filesystem content | Agent controls expected value |
| browser.screenshot | File existence | Filesystem | Agent controls path |
| opencode.run | Status check | Subprocess stdout | Agent controls command |

**Known limitation:** The filesystem.write verifier compares file content against agent-provided expected content. A truly independent verifier would need access to a separate specification of what content should have been written.

---

## 8. Trust Model Summary

```
Agent (LLM)                  — UNTRUSTED
MKC/Bridge                   — UNTRUSTED (LLM-generated content)
GovernanceSync               — TRUSTED (hardcoded limits)
SafetyGate                   — TRUSTED (hardcoded rules)
UTR Executors                — TRUSTED (compiled Python)
UTR Receipt Store            — TRUSTED (in-memory dict)
Verifier functions           — TRUSTED (compiled Python)
Plugin hooks                 — PARTIALLY TRUSTED (sandbox + static scan)
Filesystem (ground truth)    — AUTHORITATIVE
```

---

## 9. HARD RULES

1. Never set `verification = VERIFIED` without calling `UTR.verify()`
2. Never convert `INCONCLUSIVE` to `VERIFIED`
3. Never accept agent claims as evidence
4. Receipts are generated ONLY by UTR._build_receipt()
5. Verification functions MUST NOT trust agent-provided expected state
6. Every receipt MUST have a valid integrity hash
7. Every verification MUST have a canonical VerificationResult
8. SafetyGate MUST be checked before every UTR execution
9. Governance MUST be enforced on all execution paths
10. Bypass paths (muscal_loop, TOOL_REGISTRY) are deprecated and must emit warnings
