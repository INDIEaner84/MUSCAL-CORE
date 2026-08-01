import os
import tempfile
from pathlib import Path
from features.events.event_consolidation import (
    ConsolidatedEventWriter,
    EventConsolidationEngine,
    set_canonical_event_store,
    get_canonical_event_store,
)


class TestConsolidatedEventWriter:
    def test_c1_write_without_store_returns_none(self):
        cw = ConsolidatedEventWriter()
        seq = cw.write_event("test.topic", {"key": "val"})
        assert seq is None

    def test_c2_write_with_store_returns_seq(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            seq = cw.write_event("test.topic", {"msg": "hello"},
                                 source="test", priority="NORMAL")
            assert seq is not None
            assert isinstance(seq, int)
            assert seq >= 1

    def test_c3_replay_returns_events(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            cw.write_event("t1", {"a": 1})
            cw.write_event("t2", {"b": 2})
            events = cw.replay()
            assert len(events) == 2

    def test_c4_replay_with_topic_filter(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            cw.write_event("alpha", {"x": 1})
            cw.write_event("beta", {"y": 2})
            alpha_events = cw.replay(topic="alpha")
            assert len(alpha_events) == 1
            assert alpha_events[0]["topic"] == "alpha"

    def test_c5_replay_with_cursor(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            cw.write_event("t1", {"a": 1})
            cursor = cw.get_cursor()
            cw.write_event("t2", {"b": 2})
            after = cw.replay(cursor=cursor)
            assert len(after) == 1
            assert after[0]["topic"] == "t2"

    def test_c6_event_count(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            cw.write_event("t1", {"a": 1})
            cw.write_event("t2", {"b": 2})
            cw.write_event("t1", {"c": 3})
            assert cw.count() == 3
            assert cw.count(topic="t1") == 2
            assert cw.count(topic="t2") == 1

    def test_c7_get_cursor(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            assert cw.get_cursor() == 0
            cw.write_event("t", {"d": 4})
            assert cw.get_cursor() >= 1

    def test_c8_engine_emit_and_query(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            engine = EventConsolidationEngine(consolidated_writer=cw)
            engine.emit_event("sys.event", {"status": "ok"},
                              source="engine", priority="HIGH")
            events = engine.query_events()
            assert len(events) == 1
            assert events[0]["topic"] == "sys.event"

    def test_c9_canonical_store_set_and_get(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            set_canonical_event_store(store)
            retrieved = get_canonical_event_store()
            assert retrieved is store
            set_canonical_event_store(None)

    def test_c10_engine_count(self):
        from runtime.event_store import EventStore
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            store = EventStore(db_path=db)
            cw = ConsolidatedEventWriter(event_store=store)
            engine = EventConsolidationEngine(consolidated_writer=cw)
            engine.emit_event("e1", {"n": 1})
            engine.emit_event("e2", {"n": 2})
            assert engine.event_count("e1") == 1
            assert engine.event_count() == 2
