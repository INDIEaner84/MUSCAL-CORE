import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@pytest.fixture(autouse=True)
def reset_state():
    from plugin_registry import PLUGINS, HOOKS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update({
        "kernel_before": [], "kernel_after": [],
        "mkc_before": [], "mkc_after": [],
        "bridge_before": [], "bridge_after": [],
        "optimizer_before": [], "optimizer_after": [],
        "mel_before": [], "mel_after": [],
        "feedback_before": [], "feedback_after": [],
        "memory_before": [], "memory_after": [],
    })
    yield


class TestEventPersistence:
    def test_plugin_wires_to_eventbus(self):
        import config
        from event_bus import EventBus
        from features.observability.event_persistence import Plugin
        from runtime.database import init_db
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            old_db = config.DB_PATH
            config.DB_PATH = type(config.DB_PATH)(os.path.join(tmpdir, "muscal.db"))
            init_db()
            bus = EventBus()
            plugin = Plugin()
            plugin._conn = None
            plugin._wire_bus(bus)
            bus.publish("boot.init", {"ok": True}, source="test")
            conn = plugin._get_conn()
            rows = conn.execute("SELECT * FROM audit_log").fetchall()
            assert len(rows) == 1
            assert rows[0]["entry_type"] == "boot.init"
            conn.close()
            config.DB_PATH = old_db
            os.chdir(original)

    def test_plugin_persists_multiple_events(self):
        import config
        from runtime.database import init_db
        from event_bus import EventBus
        from features.observability.event_persistence import Plugin

        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            old_db = config.DB_PATH
            config.DB_PATH = type(config.DB_PATH)(os.path.join(tmpdir, "muscal.db"))
            init_db()
            bus = EventBus()
            plugin = Plugin()
            plugin._wire_bus(bus)

            for i in range(5):
                bus.publish(f"event.{i}", {"n": i}, source="test")
            conn = plugin._get_conn()
            rows = conn.execute("SELECT * FROM audit_log").fetchall()
            assert len(rows) == 5
            conn.close()
            config.DB_PATH = old_db
            os.chdir(original)

    def test_plugin_payload_contains_source_and_priority(self):
        import config
        from runtime.database import init_db
        from event_bus import EventBus, EventPriority
        from features.observability.event_persistence import Plugin

        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            old_db = config.DB_PATH
            config.DB_PATH = type(config.DB_PATH)(os.path.join(tmpdir, "muscal.db"))
            init_db()
            bus = EventBus()
            plugin = Plugin()
            plugin._wire_bus(bus)
            bus.publish("test.high", {"msg": "urgent"}, source="svc",
                        priority=EventPriority.HIGH)
            conn = plugin._get_conn()
            row = conn.execute("SELECT * FROM audit_log").fetchone()
            payload = json.loads(row["payload"])
            assert payload["source"] == "svc"
            assert payload["priority"] == "HIGH"
            assert payload["payload"]["msg"] == "urgent"
            conn.close()
            config.DB_PATH = old_db
            os.chdir(original)

    def test_replay_returns_count(self):
        import time
        from runtime.event_store import EventStore
        from event_bus import EventBus
        from features.replay.replay_service import ReplayService

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "muscal.db")
            store = EventStore(db_path=db_path)
            bus = EventBus()

            for i in range(3):
                store.append({
                    "topic": f"replay.{i}",
                    "payload": {},
                    "source": "test",
                    "priority": "NORMAL",
                    "timestamp": time.time(),
                    "id": f"evt-replay-{i}",
                })

            service = ReplayService(store=store, bus=bus)
            count = service.replay_all()
            assert count == 3
            store.close()

    def test_replay_with_topic_filter(self):
        import time
        from runtime.event_store import EventStore
        from event_bus import EventBus
        from features.replay.replay_service import ReplayService

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "muscal.db")
            store = EventStore(db_path=db_path)
            bus = EventBus()

            store.append({
                "topic": "keep.me",
                "payload": {"id": 1},
                "source": "t",
                "priority": "NORMAL",
                "timestamp": time.time(),
                "id": "evt-keep-1",
            })
            store.append({
                "topic": "skip.me",
                "payload": {"id": 2},
                "source": "t",
                "priority": "NORMAL",
                "timestamp": time.time(),
                "id": "evt-skip-1",
            })

            service = ReplayService(store=store, bus=bus)
            count = service.replay_topic("keep.me")
            assert count == 1
            store.close()

    def test_system_boot_wires_event_persistence(self):
        from plugin_registry import PLUGINS
        from plugin_loader import load_plugins
        load_plugins()

        names = [p.name for p in PLUGINS]
        assert "event_persistence" in names, f"Plugins: {names}"

    def test_pruning_does_not_crash_with_empty_db(self):
        from features.observability.event_persistence import Plugin
        plugin = Plugin()
        plugin._prune_old_events()
