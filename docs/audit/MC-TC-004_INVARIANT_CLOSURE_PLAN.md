# MC-TC-004 — Invariant Closure Plan

---

## Purpose

Define a closure plan for the 4 invariants that remain non-ENFORCED after MC-TC-003F,
determining for each whether MC-TC-004 should:
- Enforce it
- Defer it to a later phase
- Accept it as intentional

---

## Closure Plan

### I-01: execution_id is unique

| Dimension | Detail |
|-----------|--------|
| **Current status** | PARTIALLY ENFORCED — UUID v7 provides probabilistic uniqueness. No DB UNIQUE constraint on `execution_id` column. |
| **Risk** | Collision probability is ~2⁻¹²² per pair (UUID v7 — 122 random bits). At 1B executions, collision probability is ~10⁻¹⁸ (negligible). `event_id` UNIQUE constraint already prevents duplicate events. |
| **Enforcement cost** | Adding `UNIQUE` on `execution_id` in `stored_events` would break existing events with duplicate execution_ids (currently allowed). Requires migration or schema versioning. |
| **Recommendation** | **DEFER** — probabilistic uniqueness is sufficient for current scale. MC-TC-004 should not add execution_id UNIQUE constraint. If needed, add in a future schema migration phase. |
| **Closure action** | Accept PARTIALLY ENFORCED status. Document that execution_id uniqueness is probabilistic via UUID v7. Add monitoring to detect collisions post-hoc (optional). |

### I-06: Correlation groups are isolated

| Dimension | Detail |
|-----------|--------|
| **Current status** | DOCUMENTED ONLY — correlation_id is user-supplied with no format or existence validation. EnrichedMuscalOS defaults to parent execution_id but any caller can override. |
| **Risk** | Correlation groups can be intentionally or accidentally merged by reusing the same correlation_id across unrelated executions. This affects query grouping but not correctness — events are still individually identified by event_id/execution_id. |
| **Enforcement cost** | Enforcing correlation isolation would require: (a) schema-level NOT NULL or UNIQUE within correlation groups, (b) runtime validation that correlation_id matches the execution hierarchy, (c) rejection of misaligned correlation_ids. This adds complexity with limited benefit — correlation_id is a grouping convenience, not a trust property. |
| **Recommendation** | **DEFER** — correlation isolation is a query convenience feature, not a correctness invariant. Enforcing it would add architectural complexity disproportionate to the trust benefit. |
| **Closure action** | Accept DOCUMENTED ONLY status. Document that correlation_id is an advisory grouping field with no isolation guarantees. Consumers should not rely on correlation_id for security decisions. |

### I-10: Replay events are distinguishable

| Dimension | Detail |
|-----------|--------|
| **Current status** | PARTIALLY ENFORCED — `_replayed=True` marker is checked in `EventStore.append()` (returns None for replayed events). Marker is set by ReplayService. But this is an opt-in marker — not enforced at schema level. |
| **Risk** | If ReplayService fails to set `_replayed=True`, the event would be persisted as a normal event. This would require a ReplayService bug or intentional bypass. The marker is advisory at the append boundary. |
| **Enforcement cost** | Schema-level enforcement (e.g., separate `replayed_events` table, or a `replayed` boolean column with NOT NULL default FALSE) would make the distinction structural. However, this requires a schema migration and changes to all append paths. |
| **Recommendation** | **DEFER to MC-TC-004 schema improvements** — MC-TC-004 could add a `replayed` BOOLEAN NOT NULL DEFAULT 0 column to `stored_events`. This makes the distinction structural without changing behavior. The ReplayService would set it to 1 instead of (or in addition to) the payload marker. |
| **Closure action** | Add to MC-TC-004 scope: Schema improvement — add `is_replayed` BOOLEAN NOT NULL DEFAULT 0 column. ReplayService sets `is_replayed=1` in event payload for append(), EventStore maps to column. |

### I-05 (referential sub-gap): Causation referential integrity

| Dimension | Detail |
|-----------|--------|
| **Current status** | ENFORCED for correct direction (P1-F04 resolves the broken causation by setting causation_id to the cause, not self) — WEAKENED for referential integrity (no validation that causation_id points to an existing event). |
| **Risk** | A causation_id can point to a non-existent event_id. This breaks causal chain reconstruction but does not create false state — the event is still valid, just unreferenceable. |
| **Enforcement cost** | Referential integrity on causation_id would require: (a) FK constraint on event_id (requires event_id to be a PK or UNIQUE — it already is UNIQUE), (b) runtime check that causation_id exists before append. This would break the current pattern where causation_id can be an execution_id or a receipt_id (not just an event_id). |
| **Recommendation** | **DEFER** — causation referential integrity is a data quality improvement, not a correctness requirement. The current design intentionally allows causation_id to reference any identifier (execution_id, receipt_id, event_id), not just event_ids. Adding FK constraints would restrict this flexibility. |
| **Closure action** | Accept the referential gap. Document that causation_id can reference any identifier in the execution hierarchy. Consumers should validate causation_id references during analysis, not at write time. |

---

## Summary

| # | Invariant | Status | MC-TC-004 Action | Effort |
|---|-----------|--------|------------------|--------|
| I-01 | execution_id unique | PARTIALLY ENFORCED | Accept — probabilistic is sufficient | None |
| I-06 | Correlation isolation | DOCUMENTED ONLY | Accept — advisory grouping field | None |
| I-10 | Replay distinguishable | PARTIALLY ENFORCED | **Improve** — add `is_replayed` schema column | Low |
| I-05 ref | Causation referential integrity | WEAKENED (sub-gap) | Accept — intentionally flexible | None |

---

## Conclusion

**Only 1 of 4 non-enforced invariants warrants MC-TC-004 action:**

- **I-10 (schema column):** Add `is_replayed BOOLEAN NOT NULL DEFAULT 0` to `stored_events`. This is a low-effort schema improvement that makes the replay/permanent distinction structural.

The remaining 3 (I-01 uniqueness, I-06 correlation isolation, I-05 referential integrity) are acceptable by design for the current architecture phase.
