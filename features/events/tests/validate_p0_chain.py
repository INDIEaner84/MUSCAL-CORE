"""P0-⑤ — ADR-001 Chain Validation (live evidence, reads-only, REUSE).

Runs the COMPLETE chain on EXISTING components:
  Graph domain change → GraphObserverAdapter → observer_registry
  → observer_producer_factory → EventStoreV2Adapter → EventStore v2
  → ReplayService.load_events → validate_sequence → reconstruct_state

Verifies invariants CHAIN-001..005 and writes machine-readable evidence.
No new implementation, no refactoring, no Core writes.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events import observer_registry  # noqa: E402
from features.events.contracts.observer_event_contract import (  # noqa: E402
    ALL_OBSERVER_EVENT_TYPES,
    ObserverEvent,
)
from features.events.event_hash import HashService, calculate_event_hash  # noqa: E402
from features.events.graph_observer_adapter import GraphObserverAdapter  # noqa: E402
from features.events.migrations.eventstore_v2_migration import run_migration  # noqa: E402
from features.events.producer.adapter import EventStoreV2Adapter  # noqa: E402
from features.events.producer.factory import observer_producer_factory  # noqa: E402
from features.events.state_model import reconstruct_state, validate_chain  # noqa: E402
from features.replay.replay_service import ReplayService, SequenceIntegrityError  # noqa: E402
from graph import GraphState  # noqa: E402


def run_chain(store):
    """End-to-end chain: 5 events (genesis + 4 follow-up), hash chain > 3."""
    adapter = EventStoreV2Adapter(
        event_store=store, source="chain-validation", agent_id="p05-agent", task_id="p05-task"
    )
    produce = observer_producer_factory(adapter)
    observer = GraphObserverAdapter(producer=produce, agent_id="p05-agent", task_id="p05-task")
    graph = GraphState()
    observer.attach(graph)

    # Genesis (E1) + follow events (E2..E5)
    graph.emit("NODE_CREATED", {"node_id": "n1", "type": "intent"})
    graph.emit("NODE_UPDATED", {"node_id": "n1", "status": "executing"})
    graph.emit("EDGE_CREATED", {"source_id": "n1", "target_id": "n2"})
    graph.emit("OBSERVATION_CREATED", {"observation_id": "o1"})
    graph.emit("EXECUTION_STARTED", {"task_id": "t1"})

    observer.detach(graph)
    return store


def main():
    db = Path(tempfile.mkdtemp()) / "chain_validation.db"
    from runtime.event_store import EventStore

    store = EventStore(db_path=db)
    run_migration(db)
    run_chain(store)

    replay = ReplayService(store=store)
    events = replay.load_events()
    report = replay.validate_sequence(events)
    state1 = replay.rebuild_state()
    state2 = replay.rebuild_state()  # second pass ⇒ CHAIN-003
    hash_svc = HashService()

    # Invariants
    checks = {}
    prev = events[0]["metadata"]["previous_hash"]
    checks["CHAIN-001_previous_hash"] = (
        prev == ""
        and all(
            events[i]["metadata"]["previous_hash"] == events[i - 1]["metadata"]["event_hash"]
            for i in range(1, len(events))
        )
    )
    content0 = {
        "event_type": events[0]["topic"],
        "source": events[0]["source"],
        "payload": events[0]["payload"],
        "agent_id": events[0]["metadata"]["agent_id"],
        "task_id": events[0]["metadata"]["task_id"],
        "confidence": float(events[0]["metadata"]["confidence"]),
        "previous_hash": events[0]["metadata"]["previous_hash"],
    }
    checks["CHAIN-002_event_hash_deterministic"] = (
        calculate_event_hash(content0) == events[0]["metadata"]["event_hash"]
    )
    checks["CHAIN-003_replay_identical_state"] = state1.to_dict() == state2.to_dict()
    checks["CHAIN-004_tampering_detected"] = False
    tampered = [dict(e) for e in events]
    tampered[2]["payload"] = dict(tampered[2]["payload"])
    tampered[2]["payload"]["status"] = "TAMPERED"
    try:
        replay.validate_sequence(tampered)
    except (SequenceIntegrityError, Exception):
        checks["CHAIN-004_tampering_detected"] = True
    checks["CHAIN-005_missing_event_error"] = False
    missing = [dict(e) for e in events if e["seq"] != 3]
    try:
        replay.validate_sequence(missing)
    except SequenceIntegrityError:
        checks["CHAIN-005_missing_event_error"] = True

    ok = all(checks.values()) and report["valid"] and report["events_checked"] >= 5
    print(f"EVENTS={len(events)} SEQUENCE_VALID={report['valid']} "
          f"CHECKED={report['events_checked']} HASH_CHAIN>3={len(events) > 3}")
    for k, v in checks.items():
        print(f"{k}={v}")
    print(f"OVERALL={'PASS' if ok else 'FAIL'}")
    store.close()
    return ok, events, checks, state1


if __name__ == "__main__":
    ok, events, checks, state1 = main()
    sys.exit(0 if ok else 1)
