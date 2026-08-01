from features.events.event_adapter import (
    writer_to_eventstore,
    eventstore_to_writer,
    EventStoreAdapter,
    EVENT_ADAPTER_VERSION,
)


class TestEventAdapterVersion:
    def test_version_defined(self):
        assert EVENT_ADAPTER_VERSION == "1.0.0"


class TestWriterToEventStore:
    def test_converts_basic_event(self):
        writer_event = {
            "type": "execution.complete",
            "actor": "kernel",
            "actor_type": "worker",
            "domain": "execution",
            "layer": "L1",
            "payload": {"result": "ok"},
            "ts": "2026-07-23T12:00:00",
            "severity": "info",
        }
        es = writer_to_eventstore(writer_event)
        assert es["topic"] == "execution.complete"
        assert es["source"] == "kernel"
        assert es["payload"] == {"result": "ok"}

    def test_converts_string_payload(self):
        writer_event = {
            "type": "test",
            "payload": '{"key": "value"}',
            "ts": "2026-07-23T12:00:00",
        }
        es = writer_to_eventstore(writer_event)
        assert es["payload"] == {"key": "value"}

    def test_converts_with_idempotency_key(self):
        writer_event = {
            "type": "test",
            "idempotency_key": "abc-123",
            "ts": "2026-07-23T12:00:00",
        }
        es = writer_to_eventstore(writer_event)
        assert es["id"] == "abc-123"

    def test_handles_empty_event(self):
        es = writer_to_eventstore({})
        assert es["topic"] == "system"


class TestEventStoreToWriter:
    def test_converts_basic_event(self):
        es_event = {
            "topic": "execution.complete",
            "payload": {"result": "ok"},
            "source": "kernel",
            "priority": "NORMAL",
            "id": "evt-001",
            "created_at": "2026-07-23T12:00:00",
        }
        w = eventstore_to_writer(es_event)
        assert w["type"] == "execution.complete"
        assert w["actor"] == "kernel"
        assert w["severity"] == "info"

    def test_converts_high_priority(self):
        es_event = {"priority": "CRITICAL"}
        w = eventstore_to_writer(es_event)
        assert w["severity"] == "error"

    def test_roundtrip(self):
        original = {
            "type": "test.event",
            "actor": "kernel",
            "actor_type": "worker",
            "domain": "execution",
            "layer": "L1",
            "payload": {"value": 42},
            "ts": "2026-07-23T12:00:00",
            "severity": "info",
            "idempotency_key": "rt-001",
        }
        es = writer_to_eventstore(original)
        w = eventstore_to_writer(es)
        assert w["type"] == original["type"]
        assert w["actor"] == original["actor"]
        assert w["severity"] == original["severity"]
        assert w["idempotency_key"] == original["idempotency_key"]


class TestEventStoreAdapter:
    def test_adapter_accepts_event_store(self):
        adapter = EventStoreAdapter(event_store=None)
        assert adapter._event_store is None

    def test_adapter_append_without_writer(self):
        from features.events.event_adapter import writer_to_eventstore

        class MockStore:
            def __init__(self):
                self.events = []

            def append(self, event):
                self.events.append(event)
                return len(self.events)

        store = MockStore()
        adapter = EventStoreAdapter(event_store=store)
        seq = adapter.append_writer_event({"type": "test"})
        assert seq == 1
        assert len(store.events) == 1
        assert store.events[0]["topic"] == "test"

    def test_adapter_append_with_writer(self):
        class MockStore:
            def __init__(self):
                self.events = []

            def append(self, event):
                self.events.append(event)
                return len(self.events)

        class MockWriter:
            def __init__(self):
                self.submitted = []

            def submit(self, event):
                self.submitted.append(event)

        store = MockStore()
        writer = MockWriter()
        adapter = EventStoreAdapter(event_store=store, writer_thread=writer)
        seq = adapter.append_writer_event({"type": "test"})
        assert seq == 1
        assert len(store.events) == 1
        assert len(writer.submitted) == 1
