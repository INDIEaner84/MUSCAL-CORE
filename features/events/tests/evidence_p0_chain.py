"""P0-⑤ — collect evidence dump for P0_CHAIN_VALIDATION_REPORT.md / .yaml.

Reuses components; produces deterministic machine-readable evidence.
Prints JSON to stdout for ingestion by the verification documents.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.event_hash import HashService, calculate_event_hash  # noqa: E402
from features.events.graph_observer_adapter import GraphObserverAdapter  # noqa: E402
from features.events.migrations.eventstore_v2_migration import run_migration  # noqa: E402
from features.events.producer.adapter import EventStoreV2Adapter  # noqa: E402
from features.events.producer.factory import observer_producer_factory  # noqa: E402
from features.events.state_model import reconstruct_state, validate_chain  # noqa: E402
from features.replay.replay_service import ReplayService, SequenceIntegrityError  # noqa: E402
from graph import GraphState  # noqa: E402


def redact(event):
    return {
        "seq": event["seq"],
        "topic": event["topic"],
        "event_id": event["id"],
        "source": event["source"],
        "payload": event["payload"],
        "schema_version": event["schema_version"],
        "event_hash": event["metadata"].get("event_hash"),
        "previous_hash": event["metadata"].get("previous_hash"),
        "agent_id": event["metadata"].get("agent_id"),
        "task_id": event["metadata"].get("task_id"),
        "confidence": event["metadata"].get("confidence"),
    }


def main():
    db = Path(tempfile.mkdtemp()) / "evidence.db"
    from runtime.event_store import EventStore

    store = EventStore(db_path=db)
    run_migration(db)

    adapter = EventStoreV2Adapter(
        event_store=store, source="chain-validation", agent_id="p05-agent", task_id="p05-task"
    )
    observer = GraphObserverAdapter(
        producer=observer_producer_factory(adapter), agent_id="p05-agent", task_id="p05-task"
    )
    graph = GraphState()
    observer.attach(graph)
    graph.emit("NODE_CREATED", {"node_id": "n1", "type": "intent"})
    graph.emit("NODE_UPDATED", {"node_id": "n1", "status": "executing"})
    graph.emit("EDGE_CREATED", {"source_id": "n1", "target_id": "n2"})
    graph.emit("OBSERVATION_CREATED", {"observation_id": "o1"})
    graph.emit("EXECUTION_STARTED", {"task_id": "t1"})
    observer.detach(graph)

    replay = ReplayService(store=store)
    events = replay.load_events()
    report = replay.validate_sequence(events)
    chain = validate_chain(events)
    s1 = replay.rebuild_state().to_dict()
    s2 = replay.rebuild_state().to_dict()

    # error cases
    err_detail = {}
    tampered = [dict(e) for e in events]
    tampered[2]["payload"] = dict(tampered[2]["payload"])
    tampered[2]["payload"]["status"] = "TAMPERED"
    try:
        replay.validate_sequence(tampered)
    except SequenceIntegrityError as exc:
        err_detail["tampered"] = str(exc)
    missing = [dict(e) for e in events if e["seq"] != 3]
    try:
        replay.validate_sequence(missing)
    except SequenceIntegrityError as exc:
        err_detail["missing"] = str(exc)

    out = {
        "events": [redact(e) for e in events],
        "sequence_report": report,
        "chain_report": chain,
        "state1_summary": {k: v for k, v in s1.items() if k != "entities"},
        "replay_state_identical": s1 == s2,
        "errors_detected": err_detail,
        "genesis_prev_hash": events[0]["metadata"]["previous_hash"],
        "hash_chain_len": len(events),
        "schema_version": events[0]["schema_version"],
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    store.close()


if __name__ == "__main__":
    main()