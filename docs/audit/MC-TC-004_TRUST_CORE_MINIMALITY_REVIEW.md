# MC-TC-004 — Trust Core Minimality Review

---

## Purpose

Determine whether MC-TC-003E remediation added any components or complexity
beyond what the Trust Core minimally requires. The guiding principle:

> The Trust Core must be the minimal set of components and guarantees
> sufficient to ensure execution identity integrity.

---

## Trust Core Definition

The Trust Core minimally consists of:

| Component | File | Purpose |
|-----------|------|---------|
| ExecutionContext | `features/identity/execution_context.py` | Identity container, state management, enrichment |
| State validation | `features/identity/reality.py` | Execution mode, state, verification state enums and transition validation |
| UUID generation | `features/identity/uuid7.py` | Time-ordered unique IDs |
| EventBus (identity) | `event_bus.py` | Event ID generation (uuid7), routing |
| EventStore | `runtime/event_store.py` | Append-only persistence with identity columns |
| Identity propagation | `muscal_os.py` | `_extract_identity()`, `_persist_to_store()` |
| Enriched bootstrap | `features/bootstrap/enriched_bootstrap.py` | `_enriched_persist()`, nested execution support |
| Graph identity bridge | `muscal_os.py` | `enrich_with_context()` in Graph→EventBus path |

---

## Component-by-Component Review

### ExecutionContext — ESSENTIAL

All members are required for the Trust Core:
- `execution_id`, `correlation_id`, `causation_id`: Identity fields
- `execution_mode`: REAL vs SIMULATED distinction
- `execution_state`, `verification_state`: Trust state machine
- Property guards (`@execution_state.setter`, `@verification_state.setter`): P0-C03 enforcement
- `transition_state()`, `set_verification()`: Regulated state mutation
- `enrich_payload()`, `extract_from_payload()`: Identity propagation
- `to_dict()`, `validate()`: Serialization and consistency check
- `ExecutionContextManager`: Thread-local context isolation

**Verdict: ALL ESSENTIAL. No unused methods identified.**

### Claim/Evidence Boundary — NOT ESSENTIAL

`EventIdentity` (line 262), `ProvenanceTag` (line 303), and `enrich_with_claim_boundary()` (line 312) in `execution_context.py` are:

- **Defined** and **exported** via `features/identity/__init__.py`
- **NOT used** by any production code path
- **NOT used** by any test code
- **NOT referenced** outside `execution_context.py` and `__init__.py`

These are dead code — they were anticipated for MC-TC-004 or later claim/evidence
enforcement but were never wired into EventBus, EventStore, or any consumer.

**Verdict: NOT ESSENTIAL. Add to MC-TC-004 for either removal or wiring.**

### State Validation Matrices (reality.py) — ESSENTIAL

All enums (`ExecutionMode`, `ExecutionState`, `VerificationState`) and validation
functions (`validate_state_transition`, `validate_execution_state_change`,
`validate_verification_state_change`, `verify_state_transition`, `normalize_*`)
are used by ExecutionContext.

**Verdict: ALL ESSENTIAL.**

### UUID7 (uuid7.py) — ESSENTIAL

Used by EventBus (`event_bus.py:46-52`) and ExecutionContext constructor
(`execution_context.py:65`).

**Verdict: ESSENTIAL.**

### EventBus (event_bus.py) — ESSENTIAL

uuid7 event ID generation, topic-based routing, `_persist_to_store` subscription.

**Verdict: ALL ESSENTIAL.**

### EventStore (event_store.py) — ESSENTIAL

`append()`, `store_receipt()`, `store_verification()`, `replay()`, `_migrate_add_columns()`.

One method is arguably unnecessary for the Trust Core: `event_count()` (line 245)
is a convenience query method not used by any trust-critical path.

**Verdict: ONE NOT ESSENTIAL (event_count). Acceptable as utility method — not a complexity concern.**

### Identity Propagation (muscal_os.py) — ESSENTIAL

`_extract_identity()`, `_persist_to_store()`, `enrich_with_context()` are the
identity propagation backbone. All essential.

**Verdict: ALL ESSENTIAL.**

### Enriched Bootstrap — ESSENTIAL

`_enriched_persist()`, `run()` with execution_context parameter. Required for
nested execution support (P0-C01 resolution).

**Verdict: ALL ESSENTIAL.**

---

## Findings

### Finding M-01: Unused dead code — EventIdentity, ProvenanceTag, enrich_with_claim_boundary

| Dimension | Detail |
|-----------|--------|
| **Location** | `features/identity/execution_context.py:262-316` |
| **Discovered** | After MC-TC-003E remediation — these were added as preparation for future claim/evidence enforcement but never wired |
| **Impact** | Code complexity without functional benefit. Increases maintenance surface. |
| **Risk** | Future developers may rely on these unused components, believing they are part of the Trust Core, when they are not actually enforced anywhere. |
| **Recommendation** | **MC-TC-004 should either: (a) remove them, or (b) wire them into EventBus/EventStore.** Leaving them unused creates confusion about which components are actually active. |

### Finding M-02: Single unused method — EventStore.event_count()

| Dimension | Detail |
|-----------|--------|
| **Location** | `runtime/event_store.py:245-257` |
| **Impact** | Negligible — single method, well-documented, no dependencies. |
| **Recommendation** | No action needed for MC-TC-004. Acceptable as utility. |

---

## MC-TC-004 Minimality Recommendations

| Component | Current Status | MC-TC-004 Recommendation |
|-----------|---------------|--------------------------|
| ExecutionContext (core) | ESSENTIAL | **Keep** |
| EventIdentity dataclass | NOT ESSENTIAL (unused) | **Remove or wire** |
| ProvenanceTag enum | NOT ESSENTIAL (unused) | **Remove or wire** |
| enrich_with_claim_boundary() | NOT ESSENTIAL (unused) | **Remove or wire** |
| EventStore.event_count() | NOT ESSENTIAL | **Keep** — acceptable utility |
| Everything else | ESSENTIAL | **Keep** |

---

## Conclusion

**The Trust Core is minimally sound.** Only one area of dead code was identified:
the claim/evidence boundary API (`EventIdentity`, `ProvenageTag`,
`enrich_with_claim_boundary`) which was added in anticipation of future
enforcement but never wired. MC-TC-004 should resolve this by either removing
the dead code or completing the wiring.

No unnecessary complexity was introduced by MC-TC-003E remediation.
