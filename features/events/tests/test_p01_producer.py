"""P0-1 Event Producer Adapter tests (T-P01-01..10).

Extends the existing features/events test suite. Covers:

T-P01-01 Event Creation          NormalizedEvent contract + defaults
T-P01-02 Validation              structural rules (required/type)
T-P01-03 Canonical Hash          same input ⇒ same hash
T-P01-04 Hash Verification       manipulated event rejected
T-P01-05 v2 Mapping              NormalizedEvent → store dict
T-P01-06 Persistence             publish → replay via existing reader
T-P01-07 Invalid Event           invalid event rejected by producer
T-P01-08 Metadata                source/actor/trace_id/version/...
T-P01-09 Replay Compatibility    reconstructed events stay valid
T-P01-10 Idempotency             duplicate event_id → DuplicateEventError

No Core changes; temp EventStore v2 only (production DB untouched).
"""

import os
import sqlite3
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    OBS_NODE_CREATED,
    OBS_NODE_UPDATED,
    OBS_OBSERVATION_CREATED,
    NormalizedEvent,
)
from features.events.event_hash import HashService, calculate_event_hash  # noqa: E402
from features.events.migrations.eventstore_v2_migration import run_migration  # noqa: E402
from features.events.producer.adapter import EventStoreV2Adapter  # noqa: E402
from features.events.producer.exceptions import (  # noqa: E402
    DuplicateEventError,
    EventHashMismatchError,
    EventValidationError,
)
from features.events.producer.factory import (  # noqa: E402
    create_producer,
    observer_producer_factory,
)
from features.events.validation.validator import (  # noqa: E402
    collect_errors,
    validate_event,
)
from features.events.state_model import validate_chain  # noqa: E402


@pytest.fixture
def v2_store(tmp_path):
    from runtime.event_store import EventStore

    db = Path(tmp_path) / "p01.db"
    store = EventStore(db_path=db)
    run_migration(db)
    return store


@pytest.fixture
def producer(v2_store):
    return EventStoreV2Adapter(
        event_store=v2_store,
        source="test",
        agent_id="t-agent",
        task_id="t-task",
        confidence=0.5,
    )


# ── T-P01-01 Event Creation ──────────────────────────────────────────

class TestT0101EventCreation:
    def test_from_dict_roundtrip(self):
        event = NormalizedEvent.from_dict(
            {
                "event_type": OBS_OBSERVATION_CREATED,
                "event_id": "evt-1",
                "producer": "p",
                "timestamp": 123.0,
                "payload": {"k": "v"},
                "metadata": {"source": "t"},
                "correlation_id": "c-1",
            }
        )
        assert event.event_type == OBS_OBSERVATION_CREATED
        assert event.event_id == "evt-1"
        assert event.payload == {"k": "v"}
        back = NormalizedEvent.from_dict(event.to_dict())
        assert back.to_dict() == event.to_dict()

    def test_autofields(self):
        event = NormalizedEvent(event_type=OBS_NODE_CREATED, payload={"id": "n1"})
        assert event.event_id
        assert event.producer == "eventstore_v2_adapter"
        assert isinstance(event.timestamp, float)
        assert isinstance(event.metadata, dict)


# ── T-P01-02 Validation ──────────────────────────────────────────────

class TestT0102Validation:
    def test_valid_event_passes(self, producer):
        event = producer.create_event(OBS_OBSERVATION_CREATED, {"obs": 1})
        assert producer.validate(event) is True
        assert collect_errors(event) == []

    def test_missing_required_fields(self):
        event = NormalizedEvent(event_type=OBS_NODE_CREATED)
        event.event_id = ""
        event.producer = ""
        with pytest.raises(EventValidationError):
            validate_event(event)

    def test_unknown_event_type_rejected(self):
        with pytest.raises(ValueError):
            NormalizedEvent(event_type="graph.nope", payload={})


# ── T-P01-03 Canonical Hash ──────────────────────────────────────────

class TestT0103CanonicalHash:
    def test_same_input_same_hash(self):
        svc = HashService()
        e1 = NormalizedEvent(
            event_type=OBS_NODE_CREATED, payload={"id": "n1"}, metadata={"source": "t"}
        )
        e2 = NormalizedEvent(
            event_type=OBS_NODE_CREATED, payload={"id": "n1"}, metadata={"source": "t"}
        )
        assert svc.calculate_hash(e1) == svc.calculate_hash(e2)

    def test_different_payload_different_hash(self):
        svc = HashService()
        a = NormalizedEvent(
            event_type=OBS_NODE_CREATED, payload={"id": "n1"}, metadata={"source": "t"}
        )
        b = NormalizedEvent(
            event_type=OBS_NODE_CREATED, payload={"id": "n2"}, metadata={"source": "t"}
        )
        assert svc.calculate_hash(a) != svc.calculate_hash(b)


# ── T-P01-04 Hash Verification ───────────────────────────────────────

class TestT0104HashVerification:
    def test_verify_ok(self):
        svc = HashService()
        event = NormalizedEvent(
            event_type=OBS_NODE_CREATED, payload={"id": "n"}, metadata={"source": "t"}
        )
        digest = svc.calculate_hash(event)
        assert svc.verify_hash(event, digest) is True

    def test_manipulated_payload_rejected(self, producer):
        event = producer.create_event(OBS_NODE_CREATED, {"id": "n"})
        digest = calculate_event_hash(event)
        event.payload["id"] = "TAMPERED"
        with pytest.raises(EventHashMismatchError):
            producer.verify_hash(event, digest)


# ── T-P01-05 v2 Mapping ──────────────────────────────────────────────

class TestT0105V2Mapping:
    def test_mapping_fields(self, producer):
        event = producer.create_event(
            OBS_NODE_CREATED,
            {"id": "n1"},
            correlation_id="corr-1",
        )
        mapping = producer.to_v2_mapping(event)
        assert mapping["topic"] == OBS_NODE_CREATED
        assert mapping["source"] == "test"
        assert mapping["event_id"] == event.event_id
        assert mapping["correlation_id"] == "corr-1"
        assert mapping["schema_version"] == 2
        assert mapping["metadata"]["previous_hash"] == ""
        assert mapping["metadata"]["event_hash"]
        assert mapping["prev_hash"] == ""


# ── T-P01-06 Persistence ─────────────────────────────────────────────

class TestT0106Persistence:
    def test_publish_roundtrip(self, producer, v2_store):
        event = producer.create_event(OBS_OBSERVATION_CREATED, {"obs": "o1"})
        seq = producer.publish(event)
        assert seq is not None
        rows = v2_store.replay(topic=OBS_OBSERVATION_CREATED, limit=10)
        assert len(rows) == 1
        assert rows[0]["payload"] == {"obs": "o1"}
        assert rows[0]["metadata"]["event_hash"] == event.metadata["event_hash"]


# ── T-P01-07 Invalid Event ───────────────────────────────────────────

class TestT0107InvalidEvent:
    def test_producer_rejects_invalid(self, producer):
        event = NormalizedEvent(event_type=OBS_NODE_CREATED, payload={})  # no producer id
        event.producer = ""
        with pytest.raises(EventValidationError):
            producer.validate(event)

    def test_publish_invalid_rejected(self, producer):
        event = NormalizedEvent(event_type=OBS_NODE_CREATED, payload={})
        event.producer = ""
        event.event_id = ""
        with pytest.raises(EventValidationError):
            producer.publish(event)


# ── T-P01-08 Metadata ────────────────────────────────────────────────

class TestT0108Metadata:
    def test_metadata_forwarded(self, producer, v2_store):
        md = {
            "source": "special",
            "actor": "agent-A",
            "trace_id": "trace-abc",
            "version": 7,
            "schema_version": 2,
        }
        event = producer.create_event(OBS_NODE_CREATED, {"id": "n"}, metadata=md)
        producer.publish(event)
        rows = v2_store.replay(topic=OBS_NODE_CREATED, limit=10)
        stored_md = rows[0]["metadata"]
        assert stored_md["source"] == "special"
        assert stored_md["actor"] == "agent-A"
        assert stored_md["trace_id"] == "trace-abc"
        assert stored_md["version"] == 7
        assert stored_md["schema_version"] == 2


# ── T-P01-09 Replay Compatibility ────────────────────────────────────

class TestT0109ReplayCompatibility:
    def test_replay_validates_and_reconstructs(self, producer, v2_store):
        for i in range(3):
            event = producer.create_event(OBS_NODE_CREATED, {"id": f"n{i}"})
            producer.publish(event)

        events = v2_store.replay(topic=OBS_NODE_CREATED, limit=10)
        assert len(events) == 3
        report = validate_chain(events)
        assert report["valid"] is True

        # from_stored → still a valid producer contract
        normalized = EventStoreV2Adapter.from_stored(events[0])
        assert normalized.event_type == OBS_NODE_CREATED
        collect_errors(normalized) == []


# ── T-P01-10 Idempotency ─────────────────────────────────────────────

class TestT0110Idempotency:
    def test_duplicate_event_id_rejected(self, producer):
        event = producer.create_event(OBS_NODE_CREATED, {"id": "n"})
        first = producer.publish(event)
        assert first is not None
        with pytest.raises(DuplicateEventError):
            producer.publish(event)


# ── Wire-in: observer factory (integration, no new pipeline) ─────────

class TestObserverWiring:
    def test_observer_event_bridge(self, v2_store):
        from features.events.contracts.observer_event_contract import ObserverEvent

        adapter = EventStoreV2Adapter(
            event_store=v2_store, source="graph", agent_id="obs", task_id="t"
        )
        produce = observer_producer_factory(adapter)
        obs = ObserverEvent(event_type=OBS_OBSERVATION_CREATED, payload={"x": 1})
        seq = produce(obs)
        assert seq is not None
        rows = v2_store.replay(topic=OBS_OBSERVATION_CREATED, limit=10)
        assert len(rows) == 1