# ADR-EVENT-001 — EventStore Authority Boundary

**Status:** PROPOSED → APPROVED
**Date:** 2026-07-27
**Authority:** RC-02 Gate 1

## Context

The system has two persistence paths for events:

1. **MuscalOS → EventStore → `stored_events` table** — OS lifecycle events, Graph events, health events
2. **WriterThread → EventStore.append() → `stored_events` table + `events` table (derived)** — Kernel events, observation events, governance events

Per MC-TC-005.3, the WriterThread was already made a "Compatibility Adapter" that writes to EventStore FIRST (canonical), then to the `events` table (derived read model).

The remaining nuance: `supervisor.py` creates TWO EventStore Python objects:
- One inside `MuscalOS._init_event_store()` — subscribes to EventBus wildcard
- One in Phase 2 — passed to WriterThread

Both point to the same SQLite file (`storage/muscal.db`) and same `stored_events` table. They are independent SQLite connections, not independent data authorities.

## Decision

SUPL MUST use the `MuscalOS.event_store` instance — NOT create a new EventStore.

Rationale:
1. `MuscalOS.event_store` already has the EventBus wildcard subscriber for OS event persistence
2. Using the same instance avoids SQLite connection proliferation
3. Event identity (execution_id, correlation_id, etc.) is handled consistently
4. No data migration needed
5. No schema change needed

## SUPL EventStore Usage

| Component | EventStore Access | Authority |
|-----------|-------------------|-----------|
| SUPL API (execute_action) | Via production UTR receipt/verification callbacks | Canonical MuscalOS EventStore |
| SUPL WebSocket (replay) | Direct EventStore reference | Canonical MuscalOS EventStore |
| EventBusBridge | Uses EventBus (not EventStore directly) | Event Authority, not Persistence Authority |
| GraphProjectionEventBridge | Uses EventBus (not EventStore directly) | Event Authority, not Persistence Authority |

## What is NOT changing in Gate 1

- WriterThread remains a separate connection (but points to same DB)
- `events` table remains as derived read model
- No data migration between `stored_events` and `events`
- No schema changes
- No removal of existing persistence mechanisms
- No EventStore consolidation (deferred to RC-06)

## Verification

The integration test MUST verify that the SUPL EventStore reference is the same instance as `MuscalOS.event_store` (or at minimum writes to the same physical database with the same authority).
