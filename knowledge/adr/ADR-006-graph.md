# ADR-006: Graph/Sphere — Event-Driven Execution Graph

**Status:** PROPOSED  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 uses two tightly coupled components for graph state:

### GraphState (`graph.py`)

| Property   | Value |
|------------|-------|
| Lines      | 219 |
| Nodes      | `dict[str, Node]` (id, type, payload, status, confidence) |
| Edges      | `dict[str, Edge]` (source, target, type, metadata) |
| Events     | `_event_listeners: dict[str, list[callable]]` — type-keyed pub-sub |
| Pruning    | FIFO eviction at MAX_NODES=5000 / MAX_EDGES=10000 |
| Focus      | `set_focus(node_id)` — marks the current node |
| Snapshot   | `get_snapshot()` returns dict with all nodes/edges |

### SphereState (`sphere.py`)

| Property | Value |
|----------|-------|
| Lines    | ~120 |
| Rings    | Inner (active), Middle (reference), Outer (archive) |
| Focus    | Single node at center — `get_snapshot()` returns center + rings |
| Sync     | `sync()` is called on every graph event via lambda callback |
| Path     | `active_path` tracks the sequence of focused nodes |

### How They Wire Together

In `MuscalKernel.__init__()`:

```python
all_events = [NODE_CREATED, NODE_UPDATED, EDGE_CREATED,
              EXECUTION_STARTED, EXECUTION_FINISHED,
              SYSTEM_ACTION_STARTED, SYSTEM_ACTION_COMPLETED,
              SYSTEM_ACTION_FAILED]

for evt in all_events:
    self.graph.on(evt, lambda _e: self.sphere.sync())
```

Every graph event triggers `sphere.sync()`, which repartitions nodes into the three rings based on recency and connectedness to the current focus.

### Identified Issues

1. **Sphere sync is O(n)**: `sync()` iterates all graph nodes every time — at 5000 nodes, 8 events per run, this is 40K iterations per run
2. **No incremental sync**: Tiny graph changes (one node added) trigger the same full scan as a bulk import
3. **Graph is the event source**: `g.emit()` fires listeners including sphere.sync — but sphere has no direct event subscription, only the kernel-wired lambda
4. **Event cascade**: `on_action_event` calls `add_node()` which emits NODE_CREATED which triggers sphere.sync again — system action events cause 2-3 sync calls per event

---

## Decision

**Keep the Graph-State pattern for v0.8. GraphState is the event source AND state store.**

### Why Not Separate CQRS

| Approach           | Pros                                      | Cons |
|--------------------|-------------------------------------------|------|
| **Current**        | Simple, tested, 2 components              | O(n) sync, cascade |
| **CQRS**           | Read/write separation, scalable           | Over-engineering for single-user |
| **Separate Graph** | Graph as pure event log, separate state   | Dual-write problem |

### Optimization: Incremental Sync (v0.8)

Instead of full scan, sphere maintains a running delta:

```python
def sync(self, changed_node_ids: list[str] = None):
    if changed_node_ids:
        for nid in changed_node_ids:
            self._reclassify_node(nid)
    else:
        self._full_sync()  # fallback
```

GraphState tracks changed nodes per emit:

```python
def emit(self, event_type, payload):
    changed = payload.get("_changed_nodes", [])
    self._push_event(event_type, payload)
    for cb in self._event_listeners.get(event_type, []):
        cb(payload)  # sphere receives changed_node_ids
```

### Optimization: Debounce Sphere Sync

If 3 events fire in 10ms, batch sync once:

```python
def _debounced_sync(self):
    if self._sync_timer:
        self._sync_timer.cancel()
    self._sync_timer = threading.Timer(0.05, self.sphere.sync)
    self._sync_timer.start()
```

### Cascade Mitigation

System action handler (`on_action_event`) sets a flag to prevent recursive sync:

```python
def on_action_event(self, event):
    if getattr(self, '_handling_action', False):
        return  # prevent recursion
    self._handling_action = True
    try:
        # ... add_node, add_edge, update_node
    finally:
        self._handling_action = False
```

---

## Migration Plan

### Phase 1: Incremental sync (v0.8)

- Add `_dirty_nodes: set[str]` to GraphState
- Set dirty flag in `add_node()`, `update_node()`, `remove_node()`
- Pass dirty set to sphere.sync()
- Sphere reclassifies only dirty nodes

### Phase 2: Debounce (v0.8)

- Add threading.Timer-based debounce in kernel event wiring
- Configurable delay (default 50ms)

### Phase 3: Cascade guard (v0.8)

- Add recursion guard in SystemModule.on_action_event()

---

## Consequences

### Positive
- Incremental sync reduces O(n) to O(changed) for common case
- Debounce prevents 3-4 sync calls for cascading events
- Cascade guard prevents infinite recursion

### Negative
- Dirty tracking adds ~5 LOC to add_node/update_node/remove_node
- Debounce introduces 50ms latency (acceptable for interactive use)
- Threading.Timer is a new dependency for graph.py

---

## Compliance Check

- [ ] Phase 1: Incremental sync implemented
- [ ] Phase 2: Debounce implemented (configurable)
- [ ] Phase 3: Cascade guard in on_action_event
- [ ] Sphere.sync call count per run <= event count (prevents cascades)
- [ ] 18/18 tests pass after each phase
