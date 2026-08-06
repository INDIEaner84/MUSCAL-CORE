"""EventStore v2 schema migration tests (Phase 1C.2).

Covers the additive `_migrate_schema_v2()` contract:
- migration runnable multiple times (idempotent)
- old v1 events stay readable and unchanged
- new v2 fields are available (DB level and via replay)
- safety checks: missing table raises; no data loss
"""

import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

V2_COLUMNS = {
    "aggregate_id",
    "aggregate_type",
    "metadata",
    "payload_delta",
    "parent_event_id",
    "prev_hash",
    "logical_time",
}


def _make_store(tmpdir: str) -> "EventStore":
    from runtime.event_store import EventStore

    return EventStore(db_path=Path(tmpdir) / "test_migrate.db")


def _make_event(**overrides):
    ev = {
        "topic": "test.event",
        "payload": {"key": "value"},
        "source": "test",
        "priority": "NORMAL",
        "timestamp": time.time(),
        "id": f"evt-{int(time.time() * 1000)}",
    }
    ev.update(overrides)
    return ev


def _column_names(conn) -> set:
    return {r["name"] for r in conn.execute("PRAGMA table_info(stored_events)")}


# ── Migration läuft mehrfach (idempotent) ──────────────────────


def test_migration_idempotent_across_initializations():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store.append(_make_event(id="evt-a"))
        store.close()

        for _ in range(3):
            store2 = _make_store(tmpdir)
            assert V2_COLUMNS <= _column_names(store2._conn)
            store2.close()

        store3 = _make_store(tmpdir)
        assert store3.event_count() == 1
        store3.close()


def test_migration_noop_when_columns_exist():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store._migrate_schema_v2()
        store._migrate_schema_v2()
        cols = _column_names(store._conn)
        assert V2_COLUMNS <= cols
        assert cols == _column_names(store._conn)
        store.close()


# ── Alte v1 Events bleiben lesbar ───────────────────────────────


def test_v1_event_readable_after_migration():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store.append(_make_event(id="evt-v1", topic="unit.v1", payload={"a": 1}))
        store.close()

        store2 = _make_store(tmpdir)
        rows = store2.replay()
        assert len(rows) == 1
        assert rows[0]["topic"] == "unit.v1"
        assert rows[0]["payload"] == {"a": 1}
        assert rows[0]["schema_version"] == 1
        assert rows[0]["aggregate_id"] == ""
        assert rows[0]["logical_time"] == 0
        assert rows[0]["metadata"] == {}
        assert rows[0]["payload_delta"] == {}
        store2.close()


def test_legacy_v1_row_created_before_v2_columns_survives():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "legacy.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """CREATE TABLE stored_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}',
                source TEXT NOT NULL DEFAULT '', priority TEXT NOT NULL DEFAULT 'NORMAL',
                timestamp REAL NOT NULL, event_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            "INSERT INTO stored_events (topic, payload, source, timestamp, event_id, created_at)"
            " VALUES ('legacy.topic', '{\"k\": 1}', 'legacy', ?, 'evt-legacy-1', ?)",
            (time.time(), time.time()),
        )
        conn.commit()
        row = conn.execute("SELECT seq FROM stored_events").fetchone()
        conn.close()

        from runtime.event_store import EventStore

        store = EventStore(db_path=db_path)
        cols = _column_names(store._conn)
        assert V2_COLUMNS <= cols
        assert "schema_version" in cols

        rows = store.replay()
        assert len(rows) == 1
        assert rows[0]["topic"] == "legacy.topic"
        assert rows[0]["payload"] == {"k": 1}
        assert rows[0]["id"] == "evt-legacy-1"
        assert rows[0]["schema_version"] == 1
        store.close()


# ── Neue Felder verfügbar ───────────────────────────────────────


def test_new_fields_available_via_append_and_replay():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        ev = _make_event(
            id="evt-v2-1",
            topic="decision.created",
            schema_version=2,
            aggregate_id="dec-001",
            aggregate_type="decision",
            metadata={"tenant": "t1"},
            payload_delta={"confidence": 0.9},
            parent_event_id="",
            prev_hash="",
            logical_time=1,
        )
        store.append(ev)

        rows = store.replay()
        assert len(rows) == 1
        r = rows[0]
        assert r["schema_version"] == 2
        assert r["aggregate_id"] == "dec-001"
        assert r["aggregate_type"] == "decision"
        assert r["metadata"] == {"tenant": "t1"}
        assert r["payload_delta"] == {"confidence": 0.9}
        assert r["logical_time"] == 1
        store.close()


def test_append_without_v2_fields_gets_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store.append(_make_event(id="evt-defaults"))
        r = store.replay()[0]
        assert r["aggregate_id"] == ""
        assert r["aggregate_type"] == ""
        assert r["metadata"] == {}
        assert r["payload_delta"] == {}
        assert r["parent_event_id"] == ""
        assert r["prev_hash"] == ""
        assert r["logical_time"] == 0
        store.close()


# ── Sicherheitsprüfungen ────────────────────────────────────────


def test_migration_raises_when_table_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        from runtime.event_store import EventStore

        db_path = Path(tmpdir) / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()

        store = EventStore(db_path=db_path)
        store._conn.execute("DROP TABLE stored_events")
        store._conn.commit()
        try:
            store._migrate_schema_v2()
            assert False, "expected RuntimeError for missing table"
        except RuntimeError as exc:
            assert "does not exist" in str(exc)
        store.close()


def test_migration_does_not_touch_existing_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store.append(_make_event(id="evt-x", topic="unit.x", payload={"n": 42}))
        seq_before = store.get_cursor()
        store.close()

        store2 = _make_store(tmpdir)
        raw = store2._conn.execute(
            "SELECT payload, seq, event_id FROM stored_events"
        ).fetchall()
        assert len(raw) == 1
        assert raw[0]["seq"] == seq_before
        assert raw[0]["event_id"] == "evt-x"
        assert json.loads(raw[0]["payload"]) == {"n": 42}
        store2.close()
