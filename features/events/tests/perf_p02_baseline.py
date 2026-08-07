"""P0-2 performance baseline: 100 / 1000 events replay.

Measures load_events + validate_sequence + rebuild_state:
time (s), peak memory (MB via tracemalloc), error count.
"""
import os
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import OBS_OBSERVATION_CREATED
from features.events.migrations.eventstore_v2_migration import run_migration
from features.events.producer.factory import create_producer
from features.replay.replay_service import ReplayService


def bench(n: int) -> dict:
    from runtime.event_store import EventStore

    db = Path("/tmp/opencode") / f"perf_{n}.db"
    store = EventStore(db_path=db)
    run_migration(db)
    producer = create_producer(store, source="perf", agent_id="perf", task_id="t")
    replay = ReplayService(store=store)

    errors = 0
    t_start = time.perf_counter()
    for i in range(n):
        try:
            ev = producer.create_event(OBS_OBSERVATION_CREATED, {"observation_id": f"o{i}", "i": i})
            producer.publish(ev)
        except Exception:
            errors += 1
    write_seconds = time.perf_counter() - t_start

    tracemalloc.start()
    t0 = time.perf_counter()
    events = replay.load_events()
    report = replay.validate_sequence(events)
    state = replay.rebuild_state(events)
    replay_seconds = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    result = {
        "events": n,
        "write_seconds": round(write_seconds, 4),
        "replay_seconds": round(replay_seconds, 4),
        "peak_mb": round(peak / 1e6, 2),
        "errors": errors,
        "loaded": len(events),
        "valid": report.get("valid"),
        "processed": state.events_processed,
    }
    store.close()
    return result


if __name__ == "__main__":
    for n in (100, 1000):
        r = bench(n)
        print(
            f"{r['events']:>5} events | write {r['write_seconds']}s | replay {r['replay_seconds']}s "
            f"| peak {r['peak_mb']}MB | errors {r['errors']} | loaded {r['loaded']} "
            f"| valid {r['valid']} | processed {r['processed']}"
        )
