from __future__ import annotations
import time
import pytest

from features.supl.event_topics import (
    SUPL_APPLICATION_REGISTERED,
    SUPL_ACTION_REQUESTED,
    SUPL_ACTION_AUTHORIZED,
    SUPL_ACTION_REJECTED,
    SUPL_EXECUTION_COMPLETED,
    SUPL_EXECUTION_FAILED,
    SUPL_EXECUTION_LINKED,
    SUPL_INTERACTION_CREATED,
    SUPL_INTERACTION_UPDATED,
    SUPL_PROVENANCE_LINKED,
    SUPL_TOPICS,
)


class TestEventTopics:
    def test_topics_defined(self):
        assert len(SUPL_TOPICS) >= 7
        assert SUPL_APPLICATION_REGISTERED == "supl.application.registered"
        assert SUPL_ACTION_REQUESTED == "supl.action.requested"
        assert SUPL_ACTION_AUTHORIZED == "supl.action.authorized"
        assert SUPL_ACTION_REJECTED == "supl.action.rejected"
        assert SUPL_EXECUTION_COMPLETED == "supl.execution.completed"
        assert SUPL_EXECUTION_FAILED == "supl.execution.failed"

    def test_topics_have_metadata(self):
        for topic, meta in SUPL_TOPICS.items():
            assert topic.startswith("supl.")
            assert "producer" in meta
            assert "consumer" in meta
            assert "payload_schema" in meta


class TestBridgePublishing:
    def test_publish_application_registered(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_APPLICATION_REGISTERED, lambda m: received.append(m))
        bridge.publish_application_registered("app1", "Test App", "1.0")
        assert len(received) == 1
        payload = received[0].payload
        assert payload["application_id"] == "app1"
        assert payload["name"] == "Test App"
        assert payload["version"] == "1.0"

    def test_publish_action_requested(self, bridge, event_bus, calc_adapter):
        received = []
        event_bus.subscribe(SUPL_ACTION_REQUESTED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test_calc", action_id="add"
        )
        bridge.publish_action_requested(interaction)
        assert len(received) == 1
        assert received[0].payload["application_id"] == "test_calc"

    def test_publish_action_authorized(self, bridge, event_bus, calc_adapter):
        received = []
        event_bus.subscribe(SUPL_ACTION_AUTHORIZED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test_calc", action_id="add"
        )
        bridge.publish_action_authorized(interaction)
        assert len(received) == 1
        assert received[0].payload["allowed"] is True

    def test_publish_action_rejected(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_ACTION_REJECTED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test_calc", action_id="add"
        )
        bridge.publish_action_rejected(interaction, reason="not allowed")
        assert len(received) == 1
        assert received[0].payload["reason"] == "not allowed"

    def test_publish_execution_completed(self, bridge, event_bus, calc_adapter):
        received = []
        event_bus.subscribe(SUPL_EXECUTION_COMPLETED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test_calc", action_id="add"
        )
        bridge.publish_execution_completed(interaction)
        assert len(received) == 1
        assert received[0].payload["interaction_id"] == interaction.interaction_id

    def test_publish_execution_failed(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_EXECUTION_FAILED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test_calc", action_id="add"
        )
        bridge.publish_execution_failed(interaction, error="something broke")
        assert len(received) == 1
        assert "something broke" in received[0].payload["error"]

    def test_publish_provenance_linked(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_PROVENANCE_LINKED, lambda m: received.append(m))
        bridge.publish_provenance_linked("int-1", "exec-1", "receipt-1")
        assert len(received) == 1
        p = received[0].payload
        assert p["interaction_id"] == "int-1"
        assert p["execution_id"] == "exec-1"

    def test_publish_execution_linked(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_EXECUTION_LINKED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test_calc", action_id="add"
        )
        bridge.publish_execution_linked(interaction, "exec-1")
        assert len(received) == 1
        assert received[0].payload["execution_id"] == "exec-1"


class TestBridgeSubscribe:
    def test_subscribe_topic(self, bridge, event_bus):
        calls = []
        bridge.subscribe(SUPL_ACTION_REQUESTED, lambda m: calls.append(1))
        bridge.publish_action_requested(
            pytest.importorskip("features.supl.provenance").UIInteraction.create(
                application_id="test_calc", action_id="add"
            )
        )
        assert len(calls) == 1

    def test_subscribe_wildcard(self, bridge, event_bus):
        calls = []
        bridge.subscribe_wildcard(lambda m: calls.append(m.topic))
        bridge.publish_application_registered("a", "b", "c")
        assert len(calls) >= 1

    def test_unsubscribe_all(self, bridge, event_bus):
        calls = []
        bridge.subscribe_wildcard(lambda m: calls.append(1))
        bridge.unsubscribe_all()
        bridge.publish_application_registered("a", "b", "c")
        assert len(calls) == 0

    def test_get_history(self, bridge, event_bus):
        for i in range(5):
            bridge.publish_application_registered(f"app{i}", f"App{i}", "1.0")
        history = bridge.get_history(SUPL_APPLICATION_REGISTERED, limit=10)
        assert len(history) >= 5


class TestEventBusPersistence:
    def test_eventbus_keeps_history(self, event_bus):
        assert hasattr(event_bus, "_max_history")
        assert event_bus._max_history > 0

    def test_publish_multiple_topics(self, bridge, event_bus):
        received = []
        event_bus.subscribe("*", lambda m: received.append(m))
        bridge.publish_application_registered("a", "b", "c")
        bridge.publish_action_requested(
            pytest.importorskip("features.supl.provenance").UIInteraction.create(
                application_id="test_calc", action_id="add"
            )
        )
        bridge.publish_execution_completed(
            pytest.importorskip("features.supl.provenance").UIInteraction.create(
                application_id="test_calc", action_id="add"
            )
        )
        assert len(received) == 3

    def test_source_tag_on_bridge(self, bridge, event_bus):
        received = []
        event_bus.subscribe("*", lambda m: received.append(m))
        bridge.publish_application_registered("app1", "Test", "1.0")
        assert len(received) == 1
        assert received[0].source == "supl"

    def test_provenance_linked_payload(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_PROVENANCE_LINKED, lambda m: received.append(m))
        bridge.publish_provenance_linked("int-abc", "exec-xyz", "receipt-123")
        assert len(received) == 1
        p = received[0].payload
        assert p["interaction_id"] == "int-abc"
        assert p["execution_id"] == "exec-xyz"
        assert p["receipt_id"] == "receipt-123"


class TestEventStorePersistence:
    def test_bridge_publishes_to_eventbus(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_ACTION_REQUESTED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        bridge.publish_action_requested(interaction)
        assert len(received) == 1

    def test_eventbus_wildcard_captures_supl(self, bridge, event_bus):
        received = []
        event_bus.subscribe("*", lambda m: received.append(m))
        bridge.publish_application_registered("app-store", "Test App", "1.0")
        assert any("supl.application.registered" in str(m.topic) for m in received)

    def test_event_order_preserved(self, bridge, event_bus):
        received = []
        event_bus.subscribe("*", lambda m: received.append(m))
        topics = []
        bridge.publish_application_registered("a", "A", "1.0")
        topics.append("supl.application.registered")
        bridge.publish_action_requested(
            pytest.importorskip("features.supl.provenance").UIInteraction.create(
                application_id="test", action_id="add"
            )
        )
        topics.append("supl.action.requested")
        assert len(received) >= 2
        assert received[0].topic == "supl.application.registered"
        assert received[1].topic == "supl.action.requested"

    def test_event_provenance_metadata_preserved(self, bridge, event_bus):
        received = []
        event_bus.subscribe(SUPL_INTERACTION_UPDATED, lambda m: received.append(m))
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test-provenance", action_id="add"
        )
        interaction.mark_authorized()
        bridge.publish_interaction_updated(interaction)
        assert len(received) == 1
        msg = received[0]
        assert hasattr(msg, "id")
        assert hasattr(msg, "timestamp")
        assert hasattr(msg, "source")

    def test_eventbus_to_store_bridge_persists_supl(self, event_bus):
        from runtime.event_store import EventStore
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            store = EventStore(db_path=tmp)
            event_bus.subscribe("*", lambda m: store.append({
                "id": m.id, "topic": m.topic, "payload": m.payload,
                "source": m.source, "priority": m.priority.name if hasattr(m.priority, "name") else str(m.priority),
                "timestamp": m.timestamp,
            }))
            event_bus.publish("supl.test.persist", {"msg": "hello"}, source="supl")
            cursor = store.get_cursor()
            assert cursor >= 1
            events = store.replay(cursor=0, limit=10)
            assert len(events) >= 1
            assert events[0]["topic"] == "supl.test.persist"
            assert events[0]["payload"]["msg"] == "hello"
            store.close()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_cursor_replay_ordering(self, event_bus):
        from runtime.event_store import EventStore
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            store = EventStore(db_path=tmp)
            event_bus.subscribe("*", lambda m: store.append({
                "id": m.id, "topic": m.topic, "payload": m.payload,
                "source": m.source, "priority": m.priority.name if hasattr(m.priority, "name") else str(m.priority),
                "timestamp": m.timestamp,
            }))
            for i in range(5):
                event_bus.publish(f"supl.test.{i}", {"idx": i}, source="supl")
            events = store.replay(cursor=0, limit=10)
            assert len(events) == 5
            for i, ev in enumerate(events):
                assert ev["payload"]["idx"] == i
            store.close()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_cursor_replay_after_seq(self, event_bus):
        from runtime.event_store import EventStore
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            store = EventStore(db_path=tmp)
            event_bus.subscribe("*", lambda m: store.append({
                "id": m.id, "topic": m.topic, "payload": m.payload,
                "source": m.source, "priority": m.priority.name if hasattr(m.priority, "name") else str(m.priority),
                "timestamp": m.timestamp,
            }))
            for i in range(5):
                event_bus.publish(f"supl.test.{i}", {"idx": i}, source="supl")
            events_after_2 = store.replay(cursor=2, limit=10)
            assert len(events_after_2) == 3
            assert events_after_2[0]["payload"]["idx"] == 2
            assert events_after_2[1]["payload"]["idx"] == 3
            assert events_after_2[2]["payload"]["idx"] == 4
            store.close()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_cursor_zero_returns_all(self, event_bus):
        from runtime.event_store import EventStore
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            store = EventStore(db_path=tmp)
            event_bus.subscribe("*", lambda m: store.append({
                "id": m.id, "topic": m.topic, "payload": m.payload,
                "source": m.source, "priority": m.priority.name if hasattr(m.priority, "name") else str(m.priority),
                "timestamp": m.timestamp,
            }))
            for i in range(3):
                event_bus.publish(f"supl.test.{i}", {"idx": i}, source="supl")
            events = store.replay(cursor=0, limit=10)
            assert len(events) == 3
            store.close()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_latest_cursor_increases(self, event_bus):
        from runtime.event_store import EventStore
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            store = EventStore(db_path=tmp)
            assert store.get_cursor() == 0
            event_bus.subscribe("*", lambda m: store.append({
                "id": m.id, "topic": m.topic, "payload": m.payload,
                "source": m.source, "priority": m.priority.name if hasattr(m.priority, "name") else str(m.priority),
                "timestamp": m.timestamp,
            }))
            event_bus.publish("supl.test.cursor", {"x": 1}, source="supl")
            c1 = store.get_cursor()
            assert c1 >= 1
            event_bus.publish("supl.test.cursor2", {"x": 2}, source="supl")
            c2 = store.get_cursor()
            assert c2 > c1
            store.close()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
