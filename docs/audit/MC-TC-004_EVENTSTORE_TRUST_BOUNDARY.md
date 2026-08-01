# MC-TC-004 — EventStore Trust Boundary Analysis

---

## Current Architecture: Who Writes to EventStore?

| Write Path | Code Path | Access Control | Authentication |
|------------|-----------|---------------|----------------|
| `_persist_to_store` (EventBus subscriber) | `muscal_os.py:279-295` | Registered via `events.subscribe("*", ...)` | NONE — any EventBus message triggers write |
| `_enriched_persist` (EnrichedMuscalOS subscriber) | `enriched_bootstrap.py:189-207` | Replaces `_persist_to_store` via `swap_subscriber` | NONE — code insertion via EventBus subscription |
| `store_receipt` (UTR callback) | `event_store.py:131-147` | Registered as `receipt_callback` | NONE — UTR calls directly |
| `store_verification` (UTR callback) | `event_store.py:158-173` | Registered as `verification_callback` | NONE — UTR calls directly |
| Direct `event_store.append()` | Any code with EventStore reference | No restriction | NONE — any caller |
| Direct SQLite access | `stored_events` table on disk | File permissions | NONE — file system only |

---

## Who is Allowed?

| Question | Current Answer | Architectural Classification |
|----------|---------------|---------------------------|
| Who is allowed to write to EventStore? | Any code with access to an EventStore instance | NO ACCESS CONTROL |
| Who is allowed to read from EventStore? | Any code with access to an EventStore instance | NO ACCESS CONTROL |
| Who is allowed to append events? | Any code that can call `append()` | NO ACCESS CONTROL |
| Who is allowed to create execution identities? | Any code that can create `ExecutionContext(...)` | NO ACCESS CONTROL |
| Who is allowed to verify? | Any code that creates `VerificationResult` and calls `store_verification` | NO ACCESS CONTROL |
| Who is allowed to mutate state? | Any code with reference to an `ExecutionContext` | ACCESS CONTROL VIA PROPERTY GUARDS (P0-C03) — only for execution_state and verification_state |

---

## Trust Model Questions

### 1. Can a compromised process write directly to EventStore?
**YES.** Any code with access to `event_store.append()` can write any event. No authentication, no authorization check. The only constraints are:
- `event_id` UNIQUE constraint (prevents duplicates)
- `execution_id` required for execution-required topics (P1-F05)
- No semantic validation of any field

### 2. Can a malicious agent bypass the Kernel?
**YES.** Direct `event_store.append()` bypasses ALL kernel processing, identity enrichment, state machine validation, and verification. A single call:
```python
event_store.append({
    "topic": "EXECUTION_COMPLETED",
    "payload": {"result": "success"},
    "id": uuid7(),
    "execution_id": "malicious-eid",
})
```
writes an event indistinguishable from a legitimate one at the persistence layer.

### 3. Can a malicious runtime bypass the EventStore?
**YES.** Any component with access to the SQLite database file can write directly to `stored_events` table, bypassing even the EventStore Python API.

### 4. Can an external process inject fake events?
**Only if** the external process has file-system access to the SQLite database file. In the current in-process architecture, EventStore is not network-exposed. External injection requires local file access.

---

## Distinguishing Trust Properties

| Property | Definition | Current Status |
|----------|-----------|---------------|
| **PROVENANCE** | Origin and history of data | PARTIALLY ENFORCED — identity fields track origin; enrichment adds context |
| **INTEGRITY** | Data has not been tampered with | PARTIALLY ENFORCED — event_id UNIQUE prevents duplicates; no hash chain |
| **AUTHENTICITY** | Data was created by a known, verified source | **NOT ENFORCED** — no identity verification on event source |
| **AUTHORIZATION** | Data creation is permitted by policy | **NOT ENFORCED** — no access control on append |
| **CONFIDENTIALITY** | Data is not readable by unauthorized parties | **NOT ENFORCED** — file-system permissions only |

**Critical distinction:** Provenance tracks WHERE data came from (execution_id, source field). It does NOT prove WHO created it (authentication) or whether they were ALLOWED to (authorization). The current architecture provides provenance but NOT authenticity or authorization for EventStore writes.

---

## Should EventStore Authentication Be in MC-TC-004?

### Analysis

**Arguments FOR:**
1. EventStore is declared as "the SINGLE CANONICAL EVENT AUTHORITY" — authority implies trust, which implies authentication
2. Without authentication, fake events are indistinguishable from real events at the persistence layer
3. Any compromised component can forge execution history, verification records, receipts
4. Current syntactic validation (execution_id required) is trivially bypassed with any non-empty string

**Arguments AGAINST:**
1. MUSCAL is an in-process, single-tenant architecture — all components run in the same process space
2. In-process authentication is inherently limited (any code can create objects with any identity)
3. True authentication requires either: (a) cryptographic signing at the caller, (b) IPC with authenticated channels, or (c) network-level authentication — none of which exist in the current architecture
4. Adding authentication would change the fundamental architecture from in-process to distributed
5. The current architecture already has P0-C03 state mutation protection, P1-F05 orphan prevention, and provenance enrichment — these provide sufficient trust guarantees for the current phase

### Recommendation

**EventStore authentication should NOT be in MC-TC-004.**

It belongs in a later security hardening phase that transitions MUSCAL from in-process to authenticated IPC architecture. The current scope boundary is architecturally correct for the following reasons:

1. **In-process architecture limitation:** Authentication in the same process space is inherently weak — any Python code can import and call any function. Adding API tokens or signing would create security theater without architectural change.
2. **Provenance over authentication:** For the current phase, provenance (tracking which execution_id generated which event) is more valuable than authentication (proving which code module called append). Provenance enables reconstruction and audit; authentication only provides caller identity.
3. **The real attack surface is external:** The most impactful attack vector is an external process writing to the SQLite file, not an in-process component calling append(). This is addressed by file-system permissions, not in-process authentication.

### Future Direction

When MUSCAL transitions to multi-process or multi-tenant:
- EventStore should become a separate service with gRPC/REST API
- Each caller authenticates via API keys or mTLS
- Each event is signed by the caller
- EventStore validates signatures before persistence

For MC-TC-004, the current EventStore trust model is **acceptable by design** for an in-process single-tenant architecture.

---

## Decision

| Question | Answer |
|----------|--------|
| Should EventStore authentication be in MC-TC-004? | **NO** — deferred to later security hardening phase |
| Is the current trust model acceptable? | **YES** — for in-process single-tenant architecture |
| Does the lack of authentication create a P0/P1 vulnerability? | **NO** — it is an architectural scope boundary, not a remediation defect |
| What replaces authentication for MC-TC-004? | **Provenance enrichment** (current) + **schema constraints** (P1-F05) + **state mutation protection** (P0-C03) |

**EventStore Authentication Boundary: ARCHITECTURAL SCOPE BOUNDARY — Deferred to future security hardening.**
