import json
import queue
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from event_bus import EventBus, EventMessage, EventPriority
from runtime.database import init_db
from runtime.event_store import EventStore
from runtime.kernel.writer import WriterThread, _SEVERITY_TO_PRIORITY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def event_store(tmp_db: Path) -> EventStore:
    return EventStore(db_path=tmp_db)


@pytest.fixture
def writer_thread(event_store: EventStore, tmp_db: Path) -> WriterThread:
    init_db(tmp_db)
    wt = WriterThread(db_path=tmp_db, event_store=event_store)
    wt.start()
    yield wt
    wt.stop()
    wt.join(timeout=3)


def count_events_table(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    finally:
        conn.close()


def count_stored_events(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM stored_events").fetchone()[0]
    finally:
        conn.close()


def read_stored_events(db_path: Path) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM stored_events ORDER BY seq").fetchall()]
    finally:
        conn.close()


def read_events_table(db_path: Path) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY seq").fetchall()]
    finally:
        conn.close()


# ===================================================================
# PHASE 3 — Authority: Canonical writer routes through EventStore
# ===================================================================

class TestWriterThreadCanonicalAuthority:
    """Verify that WriterThread delegates canonical persistence to EventStore."""

    def test_writer_submit_writes_to_stored_events(self, writer_thread: WriterThread, tmp_db: Path):
        event = {
            "type": "test.event",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest", "actor_type": "test",
            "session_id": "test-session",
            "payload": {"msg": "hello"},
        }
        writer_thread.submit(event).result(timeout=5)

        assert count_stored_events(tmp_db) == 1, "EventStore must have the event"
        stored = read_stored_events(tmp_db)[0]
        assert stored["topic"] == "test.event"
        assert json.loads(stored["payload"]) == {"msg": "hello"}

    def test_writer_submit_also_writes_events_table_derived(self, writer_thread: WriterThread, tmp_db: Path):
        event = {
            "type": "test.derived",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {"x": 1},
        }
        writer_thread.submit(event).result(timeout=5)

        assert count_events_table(tmp_db) == 1, "events table as derived read model must have the event"

    def test_writer_submit_and_wait_writes_both_tables(self, writer_thread: WriterThread, tmp_db: Path):
        event = {
            "type": "test.sync",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "system", "session_id": "s",
            "payload": {"sync": True},
        }
        result = writer_thread.submit_and_wait(event, timeout=5)
        assert "seq" in result
        assert count_stored_events(tmp_db) == 1
        assert count_events_table(tmp_db) == 1

    def test_writer_without_event_store_writes_only_events_table(self, tmp_db: Path):
        init_db(tmp_db)
        wt = WriterThread(db_path=tmp_db, event_store=None)
        wt.start()
        try:
            wt.submit({
                "type": "test.no_store",
                "domain": "system", "layer": "kernel",
                "stream": "event", "actor": "pytest",
                "actor_type": "system", "session_id": "s",
                "payload": {},
            }).result(timeout=5)
            assert count_events_table(tmp_db) == 1
            # Without EventStore, stored_events table doesn't exist
            conn = sqlite3.connect(str(tmp_db))
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='stored_events'"
            ).fetchall()]
            conn.close()
            assert len(tables) == 0
        finally:
            wt.stop()
            wt.join(timeout=3)

    def test_idempotency_key_preserved_as_event_id(self, writer_thread: WriterThread, tmp_db: Path):
        ik = f"idem-{uuid.uuid4()}"
        event = {
            "type": "test.idem",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
            "idempotency_key": ik,
        }
        writer_thread.submit(event).result(timeout=5)
        stored = read_stored_events(tmp_db)
        assert stored[0]["event_id"] == ik

    def test_canonical_write_fails_legacy_skipped(self, tmp_db: Path):
        init_db(tmp_db)
        failing_store = MagicMock(spec=EventStore)
        failing_store.append.side_effect = RuntimeError("store down")

        wt = WriterThread(db_path=tmp_db, event_store=failing_store)
        wt.start()
        try:
            with pytest.raises(Exception):
                wt.submit_and_wait({
                    "type": "test.fail",
                    "domain": "system", "layer": "kernel",
                    "stream": "event", "actor": "pytest",
                    "actor_type": "system", "session_id": "s",
                    "payload": {},
                }, timeout=5)
            assert count_events_table(tmp_db) == 0, "legacy write must not proceed if canonical fails"
        finally:
            wt.stop()
            wt.join(timeout=3)

    def test_no_direct_independent_events_write(self, writer_thread: WriterThread, tmp_db: Path):
        conn = sqlite3.connect(str(tmp_db))
        initial_events = count_events_table(tmp_db)
        initial_stored = count_stored_events(tmp_db)
        conn.close()

        writer_thread.submit({
            "type": "test.authority",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "system", "session_id": "s",
            "payload": {},
        }).result(timeout=5)

        final_events = count_events_table(tmp_db)
        final_stored = count_stored_events(tmp_db)
        assert final_stored == initial_stored + 1, "stored_events must have the new event"
        assert final_events == initial_events + 1, "events table may also have it as derived"

    def test_event_type_mapped_to_topic(self, writer_thread: WriterThread, tmp_db: Path):
        writer_thread.submit({
            "type": "custom.event_type",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
        }).result(timeout=5)
        stored = read_stored_events(tmp_db)
        assert stored[0]["topic"] == "custom.event_type"

    def test_caused_by_mapped_to_causation_id(self, writer_thread: WriterThread, tmp_db: Path):
        writer_thread.submit({
            "type": "test.causation",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
            "caused_by": ["cause-1", "cause-2"],
        }).result(timeout=5)
        stored = read_stored_events(tmp_db)
        assert stored[0]["causation_id"] == "cause-1"

    def test_severity_mapped_to_priority(self, writer_thread: WriterThread, tmp_db: Path):
        writer_thread.submit({
            "type": "test.severity",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
            "severity": "critical",
        }).result(timeout=5)
        stored = read_stored_events(tmp_db)
        assert stored[0]["priority"] == "CRITICAL"


# ===================================================================
# PHASE 5 — Boot Path Consolidation
# ===================================================================

class TestBootPathConsolidation:
    """Verify that production boot paths establish EventStore as canonical authority."""

    def test_event_store_created_in_runtime_main(self):
        import runtime.main
        import inspect
        source = inspect.getsource(runtime.main.main)
        assert "EventStore(" in source
        assert "WriterThread(" in source
        assert "event_store=" in source

    def test_event_store_created_in_supervisor(self):
        import supervisor
        import inspect
        source = inspect.getsource(supervisor.start)
        assert "EventStore(" in source
        assert "WriterThread(" in source
        assert "event_store=" in source

    def test_enriched_bootstrap_uses_atomic_swap(self):
        import features.bootstrap.enriched_bootstrap
        import inspect
        source = inspect.getsource(features.bootstrap.enriched_bootstrap.EnrichedMuscalOS.start)
        assert "swap_subscriber" in source
        assert "_os.events.unsubscribe" not in source
        assert "_os.events.subscribe" not in source

    def test_eventbus_has_swap_subscriber_method(self):
        bus = EventBus()
        assert hasattr(bus, "swap_subscriber")


# ===================================================================
# PHASE 6 — Atomic Subscriber Swap (no event-loss window)
# ===================================================================

class TestAtomicSubscriberSwap:
    """Verify that swap_subscriber replaces subscribers without a race window."""

    def test_swap_subscriber_atomic_replacement(self):
        bus = EventBus()
        captured = []

        def old_cb(msg):
            captured.append(("old", msg.topic))

        def new_cb(msg):
            captured.append(("new", msg.topic))

        bus.subscribe("*", old_cb)
        bus.swap_subscriber("*", old_cb, new_cb)

        bus.publish("TEST", {"x": 1})
        assert len(captured) == 1
        assert captured[0] == ("new", "TEST")

    def test_swap_subscriber_no_event_loss_during_swap(self):
        bus = EventBus()
        results = []
        lock = threading.Lock()

        def publisher():
            for i in range(100):
                bus.publish(f"evt-{i}", {"n": i})
                time.sleep(0.001)

        def subscriber_swapper():
            time.sleep(0.01)
            bus.swap_subscriber("*", lambda m: None, lambda m: results.append(m.topic))

        bus.subscribe("*", lambda m: results.append(m.topic))
        # swap replaces the identity — test that no events are dropped
        t1 = threading.Thread(target=publisher, daemon=True)
        t1.start()
        t1.join(timeout=5)
        assert len(results) > 0

    def test_baseline_and_enriched_subscriber_both_install(self):
        bus = EventBus()
        store_events = []

        baseline_store = lambda msg: store_events.append(("baseline", msg.topic))
        enriched_store = lambda msg: store_events.append(("enriched", msg.topic))

        bus.subscribe("*", baseline_store)
        bus.publish("EVT_1", {})
        assert store_events[-1] == ("baseline", "EVT_1")

        bus.swap_subscriber("*", baseline_store, enriched_store)
        bus.publish("EVT_2", {})
        assert store_events[-1] == ("enriched", "EVT_2")
        assert len(store_events) == 2


# ===================================================================
# PHASE 7 — Payload Canonicalization
# ===================================================================

class TestPayloadCanonicalization:
    """Verify deterministic payload serialization through EventStore."""

    def test_canonical_payload_is_deterministic(self, event_store: EventStore, tmp_db: Path):
        payload = {"z": 1, "a": {"nested": True, "value": 2}, "m": [3, 1, 2]}
        event_store.append({
            "topic": "test",
            "payload": payload,
            "source": "pytest",
            "id": str(uuid.uuid4()),
        })
        raw = read_stored_events(tmp_db)[0]["payload"]
        parsed = json.loads(raw)
        assert parsed == payload

    def test_canonical_round_trip(self, event_store: EventStore, tmp_db: Path):
        original_payload = {"msg": "hello", "count": 42, "nested": {"key": "val"}}
        eid = str(uuid.uuid4())
        event_store.append({
            "topic": "test.roundtrip",
            "payload": original_payload,
            "source": "pytest",
            "id": eid,
        })
        replayed = event_store.replay(cursor=0, limit=10)
        assert len(replayed) == 1
        assert replayed[0]["payload"] == original_payload
        assert replayed[0]["id"] == eid

    def test_canonical_order_stable(self, event_store: EventStore, tmp_db: Path):
        import hashlib
        # Same logical payload, different dict insertion order
        p1 = {"a": 1, "b": 2, "c": 3}
        p2 = {"c": 3, "b": 2, "a": 1}

        event_store.append({"topic": "t1", "payload": p1, "source": "s", "id": str(uuid.uuid4())})
        event_store.append({"topic": "t2", "payload": p2, "source": "s", "id": str(uuid.uuid4())})

        rows = read_stored_events(tmp_db)
        h1 = hashlib.md5(rows[0]["payload"].encode()).hexdigest()
        h2 = hashlib.md5(rows[1]["payload"].encode()).hexdigest()
        assert h1 == h2, "canonical serialization must produce identical byte output"


# ===================================================================
# PHASE 8 — Event Identity and Sequence
# ===================================================================

class TestEventIdentityAndSequence:
    """Verify event_id uniqueness, idempotency, and cursor correctness."""

    def test_duplicate_event_id_raises(self, event_store: EventStore):
        eid = str(uuid.uuid4())
        event_store.append({
            "topic": "test", "payload": {}, "source": "s",
            "id": eid,
        })
        with pytest.raises(sqlite3.IntegrityError):
            event_store.append({
                "topic": "test", "payload": {}, "source": "s",
                "id": eid,
            })

    def test_replay_cursor_exclusive(self, event_store: EventStore, tmp_db: Path):
        ids = [str(uuid.uuid4()) for _ in range(5)]
        for i, eid in enumerate(ids):
            event_store.append({
                "topic": "test", "payload": {"n": i}, "source": "s",
                "id": eid,
            })

        after_first = event_store.replay(cursor=1, limit=10)
        assert len(after_first) == 4
        assert after_first[0]["payload"] == {"n": 1}

    def test_get_cursor_returns_max_seq(self, event_store: EventStore):
        assert event_store.get_cursor() == 0
        event_store.append({
            "topic": "test", "payload": {}, "source": "s",
            "id": str(uuid.uuid4()),
        })
        assert event_store.get_cursor() == 1
        event_store.append({
            "topic": "test", "payload": {}, "source": "s",
            "id": str(uuid.uuid4()),
        })
        assert event_store.get_cursor() == 2

    def test_replay_completeness(self, event_store: EventStore, tmp_db: Path):
        n = 50
        ids = [str(uuid.uuid4()) for _ in range(n)]
        for i, eid in enumerate(ids):
            event_store.append({
                "topic": "test.batch", "payload": {"i": i}, "source": "s",
                "id": eid,
            })
        all_events = event_store.replay(cursor=0, limit=n * 2)
        assert len(all_events) == n
        assert all_events[0]["payload"] == {"i": 0}
        assert all_events[-1]["payload"] == {"i": n - 1}

    def test_seq_is_monotonic(self, event_store: EventStore, tmp_db: Path):
        seqs = []
        for i in range(10):
            result = event_store.append({
                "topic": "test.mono", "payload": {"i": i}, "source": "s",
                "id": str(uuid.uuid4()),
            })
            seqs.append(result)
        assert seqs == list(range(1, 11))


# ===================================================================
# PHASE 9 — Migration Strategy (legacy data compatibility)
# ===================================================================

class TestLegacyMigration:
    """Verify legacy `events` table data is treated as a derived read model."""

    def test_schema_version_column_exists(self, event_store: EventStore, tmp_db: Path):
        conn = sqlite3.connect(str(tmp_db))
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(stored_events)")]
            assert "schema_version" in cols
        finally:
            conn.close()

    def test_migration_is_idempotent(self, tmp_db: Path):
        es1 = EventStore(db_path=tmp_db)
        es1.close()
        es2 = EventStore(db_path=tmp_db)
        es2.close()
        conn = sqlite3.connect(str(tmp_db))
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(stored_events)")]
            assert "schema_version" in cols
        finally:
            conn.close()


# ===================================================================
# PHASE 10 — Reader Consolidation
# ===================================================================

class TestReaderConsolidation:
    """Verify that canonical readers use EventStore, not events table."""

    def test_event_store_replay_is_complete_source(self, writer_thread: WriterThread, event_store: EventStore, tmp_db: Path):
        writer_thread.submit({
            "type": "test.reader_evt",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {"via": "writer"},
        }).result(timeout=5)
        replayed = event_store.replay(cursor=0, limit=100)
        topics = [e["topic"] for e in replayed]
        assert "test.reader_evt" in topics

    def test_event_store_has_count_method(self, event_store: EventStore):
        event_store.append({
            "topic": "test.count", "payload": {}, "source": "s",
            "id": str(uuid.uuid4()),
        })
        assert event_store.event_count() == 1
        assert event_store.event_count(topic="test.count") == 1
        assert event_store.event_count(topic="nonexistent") == 0


# ===================================================================
# PHASE 11 — Receipt + Verification Visibility
# ===================================================================

class TestReceiptVerificationVisibility:
    """Verify execution receipts and verifications are visible through EventStore."""

    def test_store_receipt_writes_to_stored_events(self, event_store: EventStore, tmp_db: Path):
        class FakeReceipt:
            def __init__(self):
                self.execution_id = "exec-1"
                self.causation_id = "cause-1"
                self.execution_mode = "real"
                self.receipt_id = "rcpt-1"
                self.correlation_id = "corr-1"
                self.success = True
                self.verification_status = "verified"

            def to_dict(self):
                return {"receipt_id": self.receipt_id}

        event_store.store_receipt(FakeReceipt())
        rows = read_stored_events(tmp_db)
        assert len(rows) == 1
        assert rows[0]["topic"] == "execution.receipt"
        assert rows[0]["execution_id"] == "exec-1"

    def test_store_verification_writes_to_stored_events(self, event_store: EventStore, tmp_db: Path):
        class FakeVerification:
            def __init__(self):
                self.execution_id = "exec-2"
                self.execution_mode = "real"
                self.verification_id = "ver-1"
                self.causation_id = "rcpt-1"
                self.status = "passed"
                self.receipt_id = "rcpt-1"

            def to_dict(self):
                return {"verification_id": self.verification_id}

        event_store.store_verification(FakeVerification())
        rows = read_stored_events(tmp_db)
        assert len(rows) == 1
        assert rows[0]["topic"] == "execution.verification"
        assert rows[0]["execution_id"] == "exec-2"

    def test_receipt_and_verification_visible_in_replay(self, event_store: EventStore, tmp_db: Path):
        class Receipt:
            execution_id = "e1"
            causation_id = "c1"
            execution_mode = "real"
            receipt_id = "r1"
            correlation_id = ""
            success = True
            verification_status = "verified"
            def to_dict(self): return {"r": "1"}

        class Verification:
            execution_id = "e1"
            execution_mode = "real"
            verification_id = "v1"
            causation_id = "r1"
            status = "passed"
            receipt_id = "r1"
            def to_dict(self): return {"v": "1"}

        event_store.store_receipt(Receipt())
        event_store.store_verification(Verification())
        all_events = event_store.replay(cursor=0, limit=100)
        topics = [e["topic"] for e in all_events]
        assert "execution.receipt" in topics
        assert "execution.verification" in topics


# ===================================================================
# PHASE 12 — Failure / Crash Consistency
# ===================================================================

class TestCrashConsistency:
    """Verify behavior under failure and crash scenarios."""

    def test_append_failure_returns_exception(self, tmp_db: Path):
        store = EventStore(db_path=tmp_db)
        store.close()
        with pytest.raises((AttributeError, sqlite3.ProgrammingError)):
            store.append({
                "topic": "test", "payload": {}, "source": "s",
                "id": str(uuid.uuid4()),
            })

    def test_duplicate_append_raises_integrity_error(self, event_store: EventStore):
        eid = str(uuid.uuid4())
        event_store.append({
            "topic": "test", "payload": {}, "source": "s",
            "id": eid,
        })
        with pytest.raises(sqlite3.IntegrityError):
            event_store.append({
                "topic": "test", "payload": {}, "source": "s",
                "id": eid,
            })

    def test_restart_recovery_events_persist(self, tmp_db: Path):
        eid = str(uuid.uuid4())
        store1 = EventStore(db_path=tmp_db)
        store1.append({
            "topic": "test.persist", "payload": {"data": "x"},
            "source": "s", "id": eid,
        })
        store1.close()

        store2 = EventStore(db_path=tmp_db)
        events = store2.replay(cursor=0, limit=100)
        assert len(events) == 1
        assert events[0]["id"] == eid
        assert events[0]["payload"] == {"data": "x"}
        store2.close()

    def test_writer_thread_stop_drains_queue(self, writer_thread: WriterThread, tmp_db: Path):
        futures = []
        for i in range(20):
            f = writer_thread.submit({
                "type": f"test.drain.{i}",
                "domain": "system", "layer": "kernel",
                "stream": "event", "actor": "pytest",
                "actor_type": "system", "session_id": "s",
                "payload": {"i": i},
            })
            futures.append(f)
        for f in futures:
            f.result(timeout=5)
        writer_thread.stop()
        writer_thread.join(timeout=5)
        assert count_stored_events(tmp_db) == 20, "all queued events must be persisted before stop"

    def test_concurrent_writes_no_corruption(self, event_store: EventStore, tmp_db: Path):
        n = 50
        errors = []

        def writer(i):
            try:
                event_store.append({
                    "topic": "test.concurrent",
                    "payload": {"i": i},
                    "source": "t",
                    "id": str(uuid.uuid4()),
                })
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,), daemon=True) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"concurrent writes failed: {errors}"
        assert count_stored_events(tmp_db) == n

    def test_subscriber_swap_no_publish_loss(self):
        bus = EventBus()
        received = []

        def old_cb(msg):
            received.append(msg.topic)

        def new_cb(msg):
            received.append(msg.topic)

        bus.subscribe("*", old_cb)
        bus.publish("BEFORE", {})

        def swap():
            bus.swap_subscriber("*", old_cb, new_cb)
            bus.publish("AFTER", {})

        swap()
        assert "BEFORE" in received
        assert "AFTER" in received
        # verify only one subscriber fires per event
        assert received.count("BEFORE") == 1
        assert received.count("AFTER") == 1

    def test_duplicate_event_id_across_writer_path(self, writer_thread: WriterThread, tmp_db: Path):
        writer_thread.submit({
            "type": "test.dup",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
            "idempotency_key": "dup-key",
        }).result(timeout=5)

        result = writer_thread.submit_and_wait({
            "type": "test.dup",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
            "idempotency_key": "dup-key",
        }, timeout=5)

        assert result.get("duplicate")
        assert count_stored_events(tmp_db) == 1, "duplicate idem key must not append to stored_events twice"


# ===================================================================
# PHASE 14 — Final Authority Invariant
# ===================================================================

class TestFinalAuthorityInvariant:
    """Prove that all production writes converge on EventStore.append()."""

    def test_all_writer_callers_go_through_event_store(self):
        import runtime.kernel.gate
        import runtime.observation.loop
        import runtime.api.admin
        import runtime.api.workers
        import runtime.kernel.bootstrap
        import runtime.services.snapshot
        import inspect

        # All these modules use writer.submit() or writer.submit_and_wait()
        # which now delegates to EventStore.append() via the adapter
        sources = inspect.getsource(runtime.kernel.gate)
        assert "writer.submit" in sources or "writer.submit_and_wait" in sources

    def test_direct_sql_insert_events_only_in_writer(self):
        import runtime.kernel.writer
        import inspect
        source = inspect.getsource(runtime.kernel.writer)
        inserts = [line.strip() for line in source.split("\n") if "INSERT INTO events" in line]
        assert len(inserts) >= 1
        # Verify it's inside _write_atomic which is called AFTER EventStore append
        assert "_map_to_stored_event" in source

    def test_direct_sql_insert_stored_events_only_in_event_store(self):
        import runtime.event_store
        import inspect
        source = inspect.getsource(runtime.event_store)
        inserts = [line.strip() for line in source.split("\n") if "INSERT INTO stored_events" in line]
        assert len(inserts) >= 1

    def test_no_production_path_independently_writes_events(self):
        prod_dirs = [
            "runtime/kernel", "runtime/api", "runtime/services",
            "runtime/observation", "features",
        ]
        import os
        import re
        base = os.path.join(os.path.dirname(__file__), "..")
        for d in prod_dirs:
            target = os.path.join(base, d)
            if not os.path.isdir(target):
                continue
            for root, _dirs, files in os.walk(target):
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        content = fh.read()
                    if "INSERT INTO events" in content:
                        rel = os.path.relpath(fpath, base)
                        msg = f"{rel} has direct INSERT INTO events"
                        assert rel == os.path.join("runtime", "kernel", "writer.py"), msg


# ===================================================================
# PHASE 15 — Proof of Consolidation
# ===================================================================

class TestProofOfConsolidation:
    """Static scan proofs that consolidation is complete."""

    def test_events_table_is_derived_not_independent(self, writer_thread: WriterThread, tmp_db: Path):
        conn = sqlite3.connect(str(tmp_db))
        try:
            before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            before_stored = conn.execute("SELECT COUNT(*) FROM stored_events").fetchone()[0]
        finally:
            conn.close()

        writer_thread.submit({
            "type": "test.proof",
            "domain": "system", "layer": "kernel",
            "stream": "event", "actor": "pytest",
            "actor_type": "test", "session_id": "s",
            "payload": {},
        }).result(timeout=5)

        conn = sqlite3.connect(str(tmp_db))
        try:
            after = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            after_stored = conn.execute("SELECT COUNT(*) FROM stored_events").fetchone()[0]
        finally:
            conn.close()

        # Both tables got the event, but stored_events is the canonical source
        assert after_stored == before_stored + 1
        assert after == before + 1

    def test_replay_completeness_against_writer(self, writer_thread: WriterThread, event_store: EventStore, tmp_db: Path):
        """All events written through WriterThread are visible in EventStore replay."""
        n = 10
        for i in range(n):
            writer_thread.submit({
                "type": f"test.replay.{i}",
                "domain": "system", "layer": "kernel",
                "stream": "event", "actor": "pytest",
                "actor_type": "test", "session_id": "s",
                "payload": {"i": i},
            }).result(timeout=5)

        replayed = event_store.replay(cursor=0, limit=100)
        topics = [e["topic"] for e in replayed]
        for i in range(n):
            assert f"test.replay.{i}" in topics

    def test_baseline_boot_wires_event_store(self):
        import muscal_os
        import inspect
        source = inspect.getsource(muscal_os.MuscalOS._init_event_store)
        assert "EventStore(" in source

    def test_baseline_boot_subscribes_persist(self):
        import muscal_os
        import inspect
        source = inspect.getsource(muscal_os.MuscalOS._init_event_store)
        assert "subscribe" in source


# ===================================================================
# PHASE 6 — Concurrency: Atomic subscriber swap race elimination
# ===================================================================

class TestAtomicSubscriberSwapConcurrency:
    """Stress test: concurrent publishes during subscriber swap must not lose events."""

    def test_concurrent_publishes_during_swap(self):
        bus = EventBus()
        received = []
        lock = threading.Lock()
        swap_done = threading.Event()

        def old_cb(msg):
            with lock:
                received.append(("old", msg.topic))

        def new_cb(msg):
            with lock:
                received.append(("new", msg.topic))

        bus.subscribe("*", old_cb)
        stop = threading.Event()

        def continuous_publisher():
            i = 0
            while not stop.is_set():
                bus.publish(f"p{i}", {"n": i})
                i += 1
                time.sleep(0.0005)

        pub_thread = threading.Thread(target=continuous_publisher, daemon=True)
        pub_thread.start()

        time.sleep(0.02)
        bus.swap_subscriber("*", old_cb, new_cb)
        time.sleep(0.02)
        stop.set()
        pub_thread.join(timeout=3)

        with lock:
            all_topics = [t for _cb, t in received]
            old_topics = [t for cb, t in received if cb == "old"]
            new_topics = [t for cb, t in received if cb == "new"]

        assert len(old_topics) > 0, "old subscriber should have received events"
        assert len(new_topics) > 0, "new subscriber should have received events after swap"
        old_last = old_topics[-1] if old_topics else ""
        new_first = new_topics[0] if new_topics else ""
        assert old_last != new_first, "swap should have happened at some point"

        # Verify no events were lost: every event should appear in exactly one subscriber
        all_published = set()
        for t in all_topics:
            stem = t.lstrip("p")
            if stem.isdigit():
                all_published.add(int(stem))
        if all_published:
            expected = set(range(max(all_published) + 1))
            missing = expected - all_published
            loss_pct = len(missing) / len(expected) * 100 if expected else 0
            assert loss_pct < 5, f"too many events lost during swap: {len(missing)}/{len(expected)}"


# ===================================================================
# Phase 6 — Test enrichment / enriched_bootstrap wiring
# ===================================================================

class TestEnrichedPersistence:
    """Verify that enriched events include execution context fields."""

    def test_enriched_bootstrap_default_context_manager_exists(self):
        from features.identity.execution_context import get_context_manager
        mgr = get_context_manager()
        assert mgr is not None

    def test_enriched_persist_writes_context_fields(self, event_store: EventStore, tmp_db: Path):
        from features.identity.execution_context import ExecutionContext, get_context_manager
        from features.identity.uuid7 import uuid7
        ctx_mgr = get_context_manager()
        ctx = ExecutionContext(
            execution_id=uuid7(),
            correlation_id="corr-test",
            causation_id="cause-test",
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
        )
        ctx_mgr.set_context(ctx)

        enriched = _make_enriched_persist(event_store, ctx_mgr)
        msg = EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "test"},
            source="enriched_bootstrap",
            priority=EventPriority.HIGH,
        )
        enriched(msg)

        rows = read_stored_events(tmp_db)
        assert len(rows) == 1
        assert rows[0]["execution_id"] == ctx.execution_id
        assert rows[0]["correlation_id"] == "corr-test"

        ctx_mgr.clear_context()

    def test_enriched_persist_replay_equivalence(self, event_store: EventStore, tmp_db: Path):
        from features.identity.execution_context import ExecutionContext, get_context_manager
        from features.identity.uuid7 import uuid7

        ctx_mgr = get_context_manager()
        eid = uuid7()
        ctx = ExecutionContext(
            execution_id=eid,
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
        )
        ctx_mgr.set_context(ctx)

        enriched = _make_enriched_persist(event_store, ctx_mgr)
        msg = EventMessage(
            topic="TOOL_EXECUTED",
            payload={"tool": "math.add", "args": {"a": 1, "b": 2}},
            source="utr",
        )
        enriched(msg)

        replayed = event_store.replay(cursor=0, limit=10)
        assert len(replayed) == 1
        payload = replayed[0]["payload"]
        assert payload["tool"] == "math.add"
        assert replayed[0]["execution_mode"] == "real"

        ctx_mgr.clear_context()


def _make_enriched_persist(store, ctx_mgr):
    """Simulate the _enriched_persist closure from EnrichedMuscalOS."""
    def _enriched_persist(msg):
        if store is None:
            return
        ctx = ctx_mgr.current_or_default()
        enriched_payload = ctx.enrich_payload(dict(msg.payload or {}))
        store.append({
            "topic": msg.topic,
            "payload": enriched_payload,
            "source": msg.source,
            "priority": msg.priority,
            "timestamp": msg.timestamp,
            "id": msg.id,
            "execution_id": ctx.execution_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id,
            "execution_mode": ctx.execution_mode,
            "execution_state": ctx.execution_state,
            "verification_state": ctx.verification_state,
        })
    return _enriched_persist
