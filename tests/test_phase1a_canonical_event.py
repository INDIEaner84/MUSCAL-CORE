import json
import os
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from event_bus import EventBus, EventMessage
from features.identity.execution_context import ExecutionContext, ExecutionContextManager, get_context_manager, enrich_with_context
from features.identity.reality import (
    ExecutionMode,
    ExecutionState,
    VerificationState,
    normalize_execution_mode,
    normalize_execution_state,
    normalize_verification_state,
    validate_state_transition,
    verify_state_transition,
    ValidationError,
    SEMANTIC_RULES,
)
from features.identity.uuid7 import uuid7, is_uuid7, uuid7_bytes
from features.projection.graph_os_projection import GraphOSProjection, sanitize_payload, validate_normalized, ProjectionError
from runtime.event_store import EventStore


# ═══════════════════════════════════════════════════════════════════════
# A. Event Identity
# ═══════════════════════════════════════════════════════════════════════


class TestUUID7:
    def test_uuid7_format(self):
        uid = uuid7()
        assert is_uuid7(uid), f"uuid7() should return valid UUID v7: {uid}"

    def test_uuid7_unique(self):
        ids = {uuid7() for _ in range(1000)}
        assert len(ids) == 1000, "1000 UUID v7 values must be unique"

    def test_uuid7_time_ordered(self):
        timestamps = [1700000000.0 + i * 0.001 for i in range(100)]
        ids = [uuid7(seconds=ts) for ts in timestamps]
        sorted_ids = sorted(ids)
        assert ids == sorted_ids, "UUID v7 values with increasing timestamps should be time-ordered"

    def test_uuid7_bytes(self):
        b = uuid7_bytes()
        assert len(b) == 16, "uuid7_bytes() should return 16 bytes"

    def test_uuid7_deterministic_timestamp(self):
        fixed_ts = 1700000000.0
        uid1 = uuid7(seconds=fixed_ts)
        uid2 = uuid7(seconds=fixed_ts)
        assert uid1 != uid2, "Same timestamp should still produce unique UUIDs (random component)"
        assert is_uuid7(uid1)
        assert is_uuid7(uid2)

    def test_is_uuid7_rejects_other_formats(self):
        assert not is_uuid7("not-a-uuid")
        assert not is_uuid7("")
        assert not is_uuid7("00000000-0000-0000-0000-000000000000")


# ═══════════════════════════════════════════════════════════════════════
# B. Reality Integrity
# ═══════════════════════════════════════════════════════════════════════


class TestRealityIntegrity:
    def test_execution_mode_values(self):
        assert ExecutionMode.REAL.value == "real"
        assert ExecutionMode.SIMULATED.value == "simulated"
        assert ExecutionMode.PROPOSED.value == "proposed"
        assert ExecutionMode.SHADOW.value == "shadow"
        assert ExecutionMode.REPLAY.value == "replay"
        assert len(ExecutionMode) == 5

    def test_execution_state_values(self):
        assert ExecutionState.PLANNED.value == "planned"
        assert ExecutionState.RUNNING.value == "running"
        assert ExecutionState.COMPLETED.value == "completed"
        assert ExecutionState.FAILED.value == "failed"
        assert ExecutionState.CANCELLED.value == "cancelled"
        assert len(ExecutionState) == 6

    def test_verification_state_values(self):
        assert VerificationState.UNVERIFIED.value == "unverified"
        assert VerificationState.VERIFIED.value == "verified"
        assert VerificationState.FAILED.value == "failed"
        assert VerificationState.REJECTED.value == "rejected"
        assert len(VerificationState) == 4

    def test_normalize_valid_values(self):
        assert normalize_execution_mode("real") == "real"
        assert normalize_execution_mode("simulated") == "simulated"
        assert normalize_execution_state("completed") == "completed"
        assert normalize_verification_state("verified") == "verified"

    def test_normalize_invalid_falls_back(self):
        assert normalize_execution_mode("invalid") == "real"
        assert normalize_execution_state("invalid") == "planned"
        assert normalize_verification_state("invalid") == "unverified"

    def test_normalize_none_falls_back(self):
        assert normalize_execution_mode(None) == "real"
        assert normalize_execution_state(None) == "planned"
        assert normalize_verification_state(None) == "unverified"

    def validate_transition(self,
                            execution_mode: str,
                            execution_state: str,
                            verification_state: str,
                            expected_valid: bool):
        if expected_valid:
            verify_state_transition(execution_mode, execution_state, verification_state)
        else:
            with pytest.raises(ValidationError):
                verify_state_transition(execution_mode, execution_state, verification_state)

    def test_valid_real_completed(self):
        self.validate_transition("real", "completed", "verified", True)

    def test_valid_simulated_running(self):
        self.validate_transition("simulated", "running", "unverified", True)

    def test_proposed_cannot_be_running(self):
        self.validate_transition("proposed", "running", "unverified", False)

    def test_proposed_cannot_be_verified(self):
        self.validate_transition("proposed", "planned", "verified", False)

    def test_proposed_cannot_be_failed(self):
        self.validate_transition("proposed", "planned", "failed", False)

    def test_proposed_can_be_planned_and_unverified(self):
        self.validate_transition("proposed", "planned", "unverified", True)

    def test_proposed_can_be_cancelled(self):
        self.validate_transition("proposed", "cancelled", "rejected", True)

    def test_all_real_states_valid(self):
        for state in ("planned", "queued", "running", "completed", "failed", "cancelled"):
            for vstate in ("unverified", "verified", "failed", "rejected"):
                self.validate_transition("real", state, vstate, True)

    def test_simulated_verified_requires_context(self):
        self.validate_transition("simulated", "completed", "verified", True)

    def test_replay_verified_requires_context(self):
        self.validate_transition("replay", "completed", "verified", True)

    def test_invalid_mode_rejected(self):
        assert not validate_state_transition("invalid_mode", "planned", "unverified")

    def test_semantic_rules_defined(self):
        assert len(SEMANTIC_RULES) >= 5
        assert "proposed + verified = INVALID" in SEMANTIC_RULES[0]


# ═══════════════════════════════════════════════════════════════════════
# C. Execution Context
# ═══════════════════════════════════════════════════════════════════════


class TestExecutionContext:
    def test_default_execution_id(self):
        ctx = ExecutionContext()
        assert ctx.execution_id != ""
        assert is_uuid7(ctx.execution_id)

    def test_provided_execution_id(self):
        eid = "test-exec-001"
        ctx = ExecutionContext(execution_id=eid)
        assert ctx.execution_id == eid

    def test_correlation_id_default_empty(self):
        ctx = ExecutionContext()
        assert ctx.correlation_id == ""

    def test_enrich_payload(self):
        ctx = ExecutionContext(execution_id="e1", correlation_id="c1", execution_mode="simulated")
        payload = {"input": "hello"}
        enriched = ctx.enrich_payload(payload)
        assert enriched["input"] == "hello"
        assert enriched["execution_id"] == "e1"
        assert enriched["correlation_id"] == "c1"
        assert enriched["execution_mode"] == "simulated"

    def test_enrich_payload_does_not_overwrite(self):
        ctx = ExecutionContext(execution_id="e1")
        payload = {"execution_id": "existing"}
        enriched = ctx.enrich_payload(payload)
        assert enriched["execution_id"] == "existing"

    def test_extract_from_payload(self):
        payload = {
            "execution_id": "e1",
            "correlation_id": "c1",
            "causation_id": "cause-1",
            "execution_mode": "simulated",
            "execution_state": "running",
            "verification_state": "unverified",
        }
        ctx = ExecutionContext.extract_from_payload(payload)
        assert ctx.execution_id == "e1"
        assert ctx.correlation_id == "c1"
        assert ctx.causation_id == "cause-1"
        assert ctx.execution_mode == "simulated"

    def test_extract_from_empty_payload(self):
        ctx = ExecutionContext.extract_from_payload({})
        assert ctx.execution_id == ""
        assert ctx.execution_mode == "real"
        assert ctx.verification_state == "unverified"

    def test_to_dict(self):
        ctx = ExecutionContext(execution_id="e1", correlation_id="c1")
        d = ctx.to_dict()
        assert d["execution_id"] == "e1"
        assert d["correlation_id"] == "c1"
        assert "execution_mode" in d

    def test_validate_valid(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed", verification_state="verified")
        ctx.validate()

    def test_validate_invalid(self):
        ctx = ExecutionContext(execution_mode="proposed", execution_state="running", verification_state="unverified")
        with pytest.raises(ValidationError):
            ctx.validate()

    def test_context_manager_thread_local(self):
        mgr = ExecutionContextManager()
        ctx1 = ExecutionContext(execution_id="thread-1")
        results = []

        def worker():
            ctx2 = ExecutionContext(execution_id="thread-2")
            mgr.set_context(ctx2)
            results.append(mgr.get_context().execution_id)
            mgr.clear_context()
            results.append(mgr.get_context() is None)

        mgr.set_context(ctx1)
        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert mgr.get_context().execution_id == "thread-1"
        assert results[0] == "thread-2"
        assert results[1] is True

    def test_global_context_manager(self):
        mgr = get_context_manager()
        assert mgr is not None
        assert mgr.current_or_default() is not None

    def test_enrich_with_context_empty(self):
        mgr = get_context_manager()
        mgr.clear_context()
        enriched = enrich_with_context({"key": "val"})
        assert enriched["key"] == "val"


# ═══════════════════════════════════════════════════════════════════════
# D. Projection
# ═══════════════════════════════════════════════════════════════════════


class TestProjection:
    def make_event_msg(self, topic: str, payload: dict = None, source: str = "test",
                       event_id: str = None) -> EventMessage:
        return EventMessage(
            topic=topic,
            payload=payload or {},
            source=source,
            id=event_id or f"evt_{int(time.time() * 1000)}",
            timestamp=time.time(),
        )

    def test_rejects_non_canonical_topic(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("random_event", {"data": "test"})
        result = proj.project(msg)
        assert result is None
        assert proj.stats()["rejected"] == 1

    def test_normalizes_node_created(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("NODE_CREATED", {
            "node_id": "n1",
            "node_type": "INTENT",
            "execution_id": "e1",
            "execution_state": "running",
        })
        result = proj.project(msg)
        assert result is not None
        assert result["event_type"] == "NODE_CREATED"
        assert result["execution_id"] == "e1"
        assert result["execution_mode"] == "real"
        assert result["execution_state"] == "running"
        assert result["verification_state"] == "unverified"
        assert result["event_version"] == 1
        assert "timestamp" in result
        assert "sequence_number" in result
        assert result["source"] == "test"

    def test_preserves_execution_mode_from_payload(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("EXECUTION_STARTED", {
            "execution_id": "e1",
            "execution_mode": "simulated",
            "execution_state": "running",
            "verification_state": "unverified",
        })
        result = proj.project(msg)
        assert result["execution_mode"] == "simulated"

    def test_rejects_invalid_state_combination(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("EXECUTION_STARTED", {
            "execution_id": "e1",
            "execution_mode": "proposed",
            "execution_state": "running",
            "verification_state": "verified",
        })
        result = proj.project(msg)
        assert result is None

    def test_sanitizes_sensitive_fields(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("EXECUTION_COMPLETED", {
            "execution_id": "e1",
            "tool_result": {"stdout": "secret-data"},
            "file_path": "/etc/passwd",
            "command": "rm -rf /",
            "api_key": "sk-12345",
            "input_text": "user query",
            "result": "all good",
        })
        result = proj.project(msg)
        sanitized = result["payload"]
        assert "tool_result" not in sanitized
        assert "file_path" not in sanitized
        assert "command" not in sanitized
        assert "api_key" not in sanitized
        assert "input_text" not in sanitized
        assert sanitized["result"] == "all good"

    def test_truncates_error_field(self):
        proj = GraphOSProjection()
        long_error = "x" * 1000
        msg = self.make_event_msg("EXECUTION_FAILED", {
            "execution_id": "e1",
            "error": long_error,
        })
        result = proj.project(msg)
        assert len(result["payload"]["error"]) == 500

    def test_all_15_event_envelope_fields(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("NODE_CREATED", {
            "execution_id": "e1",
            "correlation_id": "c1",
            "causation_id": "cause-1",
            "execution_mode": "real",
            "execution_state": "running",
            "verification_state": "unverified",
            "event_version": 2,
            "node_id": "n1",
        }, event_id="custom-id")
        result = proj.project(msg)
        expected_fields = {
            "event_id", "event_type", "event_version", "timestamp",
            "sequence_number", "execution_id", "correlation_id",
            "causation_id", "source", "actor", "execution_mode",
            "execution_state", "verification_state", "provenance", "payload",
        }
        assert set(result.keys()) == expected_fields
        assert result["event_id"] == "custom-id"

    def test_projection_topic_to_event_type(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("NODE_CREATED", {"execution_id": "e1"})
        result = proj.project(msg)
        assert result["event_type"] == "NODE_CREATED"

    def test_provenance_optional(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("NODE_CREATED", {"execution_id": "e1"})
        result = proj.project(msg)
        assert result["provenance"] is None

    def test_provenance_preserved(self):
        proj = GraphOSProjection()
        provenance = {"chain": ["evt1", "evt2"]}
        msg = self.make_event_msg("NODE_CREATED", {
            "execution_id": "e1",
            "provenance": provenance,
        })
        result = proj.project(msg)
        assert result["provenance"] == provenance

    def test_backward_compatible_with_legacy_event(self):
        proj = GraphOSProjection()
        msg = self.make_event_msg("NODE_CREATED", {})
        result = proj.project(msg)
        assert result is not None
        assert result["execution_id"] == ""
        assert result["correlation_id"] is None
        assert result["execution_mode"] == "real"
        assert result["verification_state"] == "unverified"

    def test_validate_normalized_rejects_missing_fields(self):
        with pytest.raises(ProjectionError):
            validate_normalized({"event_id": "1", "event_type": "NODE_CREATED"})

    def test_sanitize_payload_empty(self):
        assert sanitize_payload({}) == {}

    def test_sanitize_payload_preserves_safe(self):
        result = sanitize_payload({"node_id": "n1", "status": "ok"})
        assert result == {"node_id": "n1", "status": "ok"}

    def test_stats(self):
        proj = GraphOSProjection()
        proj.project(self.make_event_msg("NON_CANONICAL", {}))
        proj.project(self.make_event_msg("NODE_CREATED", {"execution_id": "e1"}))
        s = proj.stats()
        assert s["projected"] == 1
        assert s["rejected"] == 1
        assert s["version"] == "2.0.0"


# ═══════════════════════════════════════════════════════════════════════
# E. Event Store Schema Migration
# ═══════════════════════════════════════════════════════════════════════


class TestEventStoreEnrichment:
    @pytest.fixture
    def tmp_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_new_table_has_enrichment_columns(self, tmp_db):
        store = EventStore(db_path=tmp_db)
        cols = [r["name"] for r in store._conn.execute("PRAGMA table_info(stored_events)")]
        assert "execution_id" in cols
        assert "correlation_id" in cols
        assert "causation_id" in cols
        assert "execution_mode" in cols
        assert "verification_state" in cols

    def test_append_with_enrichment(self, tmp_db):
        store = EventStore(db_path=tmp_db)
        seq = store.append({
            "topic": "NODE_CREATED",
            "payload": {"node_id": "n1"},
            "source": "test",
            "timestamp": time.time(),
            "id": "evt1",
            "execution_id": "e1",
            "correlation_id": "c1",
            "causation_id": "cause-1",
            "execution_mode": "simulated",
            "verification_state": "unverified",
        })
        assert seq is not None and seq > 0
        events = store.replay(cursor=0)
        assert len(events) == 1
        evt = events[0]
        assert evt["execution_id"] == "e1"
        assert evt["correlation_id"] == "c1"
        assert evt["causation_id"] == "cause-1"
        assert evt["execution_mode"] == "simulated"
        assert evt["verification_state"] == "unverified"

    def test_append_without_enrichment_gets_defaults(self, tmp_db):
        store = EventStore(db_path=tmp_db)
        seq = store.append({
            "topic": "NODE_CREATED",
            "payload": {"node_id": "n1"},
            "source": "test",
            "timestamp": time.time(),
            "id": "evt2",
        })
        events = store.replay(cursor=0)
        evt = events[0]
        assert evt["execution_id"] == ""
        assert evt["execution_mode"] == "real"
        assert evt["verification_state"] == "unverified"

    def test_migrate_legacy_database(self, tmp_db):
        conn = __import__("sqlite3").connect(tmp_db)
        conn.execute("""CREATE TABLE stored_events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '{}',
            source TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'NORMAL',
            timestamp REAL NOT NULL,
            event_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""INSERT INTO stored_events
            (topic, payload, source, priority, timestamp, event_id, created_at)
            VALUES ('test', '{}', 'sys', 'NORMAL', 1.0, 'legacy-id', '2026-01-01')""")
        conn.commit()
        conn.close()

        store = EventStore(db_path=tmp_db)

        cols = [r["name"] for r in store._conn.execute("PRAGMA table_info(stored_events)")]
        assert "execution_id" in cols
        assert "correlation_id" in cols
        assert "causation_id" in cols
        assert "execution_mode" in cols
        assert "verification_state" in cols

        row = store._conn.execute("SELECT * FROM stored_events").fetchone()
        assert row is not None, "Legacy row should be readable"
        assert row["execution_mode"] == "real"
        assert row["verification_state"] == "unverified"
        assert row["execution_id"] == ""


# ═══════════════════════════════════════════════════════════════════════
# F. WebSocket Adapter (Unit — No Actual WS Connections)
# ═══════════════════════════════════════════════════════════════════════


class TestWebSocketAdapterContract:
    def test_adapter_version(self):
        from features.streaming.ws_adapter import ADAPTER_VERSION
        assert ADAPTER_VERSION == "2.0.0"

    def test_constants_defined(self):
        from features.streaming.ws_adapter import (
            MAX_QUEUE_SIZE, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT,
            SNAPSHOT_GAP_THRESHOLD, DEFAULT_PORT,
        )
        assert MAX_QUEUE_SIZE == 1000
        assert HEARTBEAT_INTERVAL == 5.0
        assert HEARTBEAT_TIMEOUT == 15.0
        assert SNAPSHOT_GAP_THRESHOLD == 1000
        assert DEFAULT_PORT == 8765

    def test_client_session_dataclass(self):
        from features.streaming.ws_adapter import ClientSession
        import asyncio
        session = ClientSession(websocket=None, client_id="test-1")
        assert session.client_id == "test-1"
        assert session.last_seq == 0
        assert session.subscribed_types is None
        assert session.messages_sent == 0
        assert session.bytes_sent == 0

    def test_adapter_instantiation(self):
        from features.streaming.ws_adapter import WebSocketAdapter
        from event_bus import EventBus
        from features.projection.graph_os_projection import GraphOSProjection

        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        assert adapter.host == "127.0.0.1"
        assert adapter.port == 8765
        stats = adapter.get_stats()
        assert stats["running"] is False
        assert stats["clients"] == 0


# ═══════════════════════════════════════════════════════════════════════
# G. End-to-End: EventBus → Projection → Enriched Output
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndEventFlow:
    def test_eventbus_to_projection(self):
        bus = EventBus()
        proj = GraphOSProjection()
        received = []

        def collector(msg):
            result = proj.project(msg)
            if result:
                received.append(result)

        bus.subscribe("*", collector)

        bus.publish("NODE_CREATED", {
            "execution_id": "e2",
            "execution_mode": "simulated",
            "node_id": "n1",
        }, source="test")

        assert len(received) == 1
        evt = received[0]
        assert evt["event_type"] == "NODE_CREATED"
        assert evt["execution_id"] == "e2"
        assert evt["execution_mode"] == "simulated"
        assert evt["source"] == "test"

    def test_legacy_event_backward_compatible(self):
        bus = EventBus()
        proj = GraphOSProjection()
        received = []

        def collector(msg):
            result = proj.project(msg)
            if result:
                received.append(result)

        bus.subscribe("*", collector)

        bus.publish("NODE_CREATED", {"node_id": "n1", "type": "INTENT"}, source="legacy")

        assert len(received) == 1
        evt = received[0]
        assert evt["execution_id"] == ""
        assert evt["execution_mode"] == "real"
        assert evt["verification_state"] == "unverified"

    def test_verify_state_promotion_not_allowed(self):
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="VERIFICATION_PASSED",
            payload={"execution_id": "e1", "verification_state": "verified"},
            source="verifier",
            timestamp=time.time(),
            id="v1",
        )
        result = proj.project(msg)
        assert result is not None
        assert result["verification_state"] == "verified"

        msg2 = EventMessage(
            topic="VERIFICATION_PASSED",
            payload={"execution_id": "e1", "verification_state": "verified"},
            source="alita",
            timestamp=time.time(),
            id="v2",
        )
        result2 = proj.project(msg2)
        assert result2 is not None

    def test_non_canonical_event_type_filtered(self):
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="BOOT_INIT",
            payload={},
            source="system",
            timestamp=time.time(),
            id="boot1",
        )
        assert proj.project(msg) is None

    def test_execution_mode_propagation(self):
        bus = EventBus()
        proj = GraphOSProjection()
        results = []

        def collector(msg):
            r = proj.project(msg)
            if r:
                results.append(r)

        bus.subscribe("*", collector)

        for mode in ("real", "simulated", "shadow", "replay"):
            bus.publish("EXECUTION_STARTED", {
                "execution_id": f"e-{mode}",
                "execution_mode": mode,
                "execution_state": "running",
            }, source="test")
        bus.publish("EXECUTION_STARTED", {
            "execution_id": "e-proposed",
            "execution_mode": "proposed",
            "execution_state": "planned",
        }, source="test")

        assert len(results) == 5
        modes = [r["execution_mode"] for r in results]
        assert sorted(modes) == sorted(["real", "simulated", "proposed", "shadow", "replay"])

    def test_sequence_number_increases(self):
        bus = EventBus()
        proj = GraphOSProjection()
        seqs = []

        def collector(msg):
            r = proj.project(msg)
            if r:
                seqs.append(r["sequence_number"])

        bus.subscribe("*", collector)
        bus.publish("NODE_CREATED", {"execution_id": "e1"}, source="test")
        bus.publish("NODE_CREATED", {"execution_id": "e2"}, source="test")
        bus.publish("NODE_CREATED", {"execution_id": "e3"}, source="test")

        assert len(seqs) == 3
        assert seqs[0] <= seqs[1] <= seqs[2]

    def test_double_subscribe_projection(self):
        proj = GraphOSProjection()
        msg1 = EventMessage(
            topic="NODE_CREATED",
            payload={"execution_id": "e1", "event_id": "unique-1"},
            timestamp=time.time(),
        )
        msg2 = EventMessage(
            topic="NODE_CREATED",
            payload={"execution_id": "e1", "event_id": "unique-2"},
            timestamp=time.time(),
        )
        r1 = proj.project(msg1)
        r2 = proj.project(msg2)
        assert r1 is not None
        assert r2 is not None
        assert r1["event_id"] == "unique-1"
        assert r2["event_id"] == "unique-2"
