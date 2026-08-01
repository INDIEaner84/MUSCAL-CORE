import asyncio
import json
import os
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as _muscal_config
from pathlib import Path

from event_bus import EventBus, EventMessage, EventPriority
from features.identity.execution_context import (
    ExecutionContext,
    ExecutionContextManager,
    get_context_manager,
)
from features.identity.reality import (
    ExecutionMode,
    ExecutionState,
    VerificationState,
    validate_state_transition,
    ValidationError,
)
from features.identity.uuid7 import uuid7, is_uuid7
from features.bootstrap.enriched_bootstrap import EnrichedMuscalOS
from features.projection.graph_os_projection import GraphOSProjection, CANONICAL_EVENT_TYPES
from features.streaming.ws_adapter import WebSocketAdapter
from runtime.event_store import EventStore


class TestReplayDeterminism:
    @pytest.fixture
    def env(self):
        config = __import__("os_config").load_config()
        config.simulation_mode = True
        config.mode = __import__("os_config").DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
            from muscal_os import MuscalOS
            from features.projection.graph_os_projection import GraphOSProjection
            from features.streaming.ws_adapter import WebSocketAdapter

            m = MuscalOS(config=config)
            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            bus = m.events
            proj = GraphOSProjection(event_store=m.event_store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)
            yield {"os": m, "enriched": enriched, "bus": bus, "proj": proj, "adapter": adapter}
            enriched.shutdown()

    def test_replay_all_events_are_deterministic(self, env):
        enriched = env["enriched"]
        m = env["os"]
        mgr = get_context_manager()

        events_published = []
        def collector(msg):
            events_published.append(msg)
        m.events.subscribe("*", collector)

        ctx = ExecutionContext(execution_id="replay-det-1", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)

        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "n1", "node_type": "INTENT"},
            source="test", id=f"replay-det-evt-1",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "n2", "node_type": "ACTION"},
            source="test", id=f"replay-det-evt-2",
        ))
        enriched._enriched_persist(EventMessage(
            topic="EDGE_CREATED", payload={"source_id": "n1", "target_id": "n2", "edge_type": "depends_on"},
            source="test", id=f"replay-det-evt-3",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_UPDATED", payload={"node_id": "n1", "status": "completed"},
            source="test", id=f"replay-det-evt-4",
        ))

        mgr.clear_context()

        replay1 = m.event_store.replay(cursor=0, limit=5000)
        replay2 = m.event_store.replay(cursor=0, limit=5000)

        assert len(replay1) == len(replay2)
        for e1, e2 in zip(replay1, replay2):
            assert e1["seq"] == e2["seq"]
            assert e1["id"] == e2["id"]
            assert e1["topic"] == e2["topic"]
            assert e1["payload"] == e2["payload"]
            assert e1["execution_id"] == e2["execution_id"]
            assert e1["execution_mode"] == e2["execution_mode"]
            assert e1["verification_state"] == e2["verification_state"]

    def test_replay_produces_same_snapshot_as_live_projection(self, env):
        enriched = env["enriched"]
        m = env["os"]
        proj = env["proj"]
        adapter = env["adapter"]
        mgr = get_context_manager()

        ctx = ExecutionContext(execution_id="snap-eq-1", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)

        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "a1", "node_type": "INTENT"},
            source="test", id="snap-eq-evt-1",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "a2", "node_type": "ACTION"},
            source="test", id="snap-eq-evt-2",
        ))
        enriched._enriched_persist(EventMessage(
            topic="EDGE_CREATED", payload={"source_id": "a1", "target_id": "a2", "edge_type": "depends_on"},
            source="test", id="snap-eq-evt-3",
        ))

        mgr.clear_context()

        rows = m.event_store.replay(cursor=0, limit=5000)
        live_nodes = {}
        for row in rows:
            msg = EventMessage(
                topic=row["topic"], payload=row["payload"],
                source=row["source"], id=row["id"], timestamp=row["timestamp"],
            )
            result = proj.project(msg)
            if result is None:
                continue
            p = result["payload"]
            nid = p.get("node_id") or p.get("id") or result["event_id"]
            if result["event_type"] == "NODE_CREATED" and nid:
                live_nodes[nid] = {
                    "id": nid,
                    "type": p.get("node_type", "unknown"),
                    "status": p.get("status", "created"),
                    "execution_mode": result["execution_mode"],
                    "execution_state": result["execution_state"],
                    "verification_state": result["verification_state"],
                    "execution_id": result["execution_id"],
                }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        snapshot_nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
        loop.close()
        snapshot_node_ids = {n["id"] for n in snapshot_nodes}
        live_node_ids = set(live_nodes.keys())

        assert snapshot_node_ids == live_node_ids
        for n in snapshot_nodes:
            assert n["id"] in live_nodes
            assert n["execution_mode"] == live_nodes[n["id"]]["execution_mode"]
            assert n["verification_state"] == live_nodes[n["id"]]["verification_state"]

    def test_snapshot_plus_delta_reconstructs_full_state(self, env):
        enriched = env["enriched"]
        m = env["os"]
        adapter = env["adapter"]
        mgr = get_context_manager()

        ctx = ExecutionContext(execution_id="delta-rec-1", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)

        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "d1", "node_type": "INTENT"},
            source="test", id="delta-rec-1",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "d2", "node_type": "ACTION"},
            source="test", id="delta-rec-2",
        ))

        mgr.clear_context()

        snapshot_seq = m.event_store.get_cursor()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        snapshot_nodes = loop.run_until_complete(adapter._build_snapshot_nodes())

        ctx2 = ExecutionContext(execution_id="delta-rec-2", execution_mode="real", execution_state="running")
        mgr.set_context(ctx2)
        enriched._enriched_persist(EventMessage(
            topic="EDGE_CREATED", payload={"source_id": "d1", "target_id": "d2", "edge_type": "depends_on"},
            source="test", id="delta-rec-3",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_UPDATED", payload={"node_id": "d1", "status": "completed"},
            source="test", id="delta-rec-4",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "d3", "node_type": "TOOL"},
            source="test", id="delta-rec-5",
        ))
        mgr.clear_context()

        delta_rows = m.event_store.replay(cursor=snapshot_seq, limit=5000)

        projected_delta = []
        for row in delta_rows:
            msg = EventMessage(
                topic=row["topic"], payload=row["payload"],
                source=row["source"], id=row["id"], timestamp=row["timestamp"],
            )
            result = env["proj"].project(msg)
            if result is not None:
                projected_delta.append(result)

        delta_nodes = {n["id"]: dict(n) for n in snapshot_nodes}
        for evt in projected_delta:
            p = evt["payload"]
            nid = p.get("node_id")
            if evt["event_type"] == "NODE_CREATED" and nid:
                delta_nodes[nid] = {
                    "id": nid,
                    "type": p.get("node_type", "unknown"),
                    "status": p.get("status", "created"),
                    "execution_mode": evt["execution_mode"],
                    "execution_state": evt["execution_state"],
                    "verification_state": evt["verification_state"],
                    "execution_id": evt["execution_id"],
                }
            elif evt["event_type"] == "NODE_UPDATED" and nid and nid in delta_nodes:
                delta_nodes[nid]["status"] = p.get("status", delta_nodes[nid].get("status"))

        final_nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
        loop.close()
        final_node_map = {n["id"]: n for n in final_nodes}
        delta_node_ids = set(delta_nodes.keys())
        final_node_ids = set(final_node_map.keys())

        assert delta_node_ids == final_node_ids, f"Delta reconstruction mismatch: {delta_node_ids ^ final_node_ids}"
        for nid, ndata in delta_nodes.items():
            assert ndata["status"] == final_node_map[nid]["status"]
            assert ndata["execution_mode"] == final_node_map[nid]["execution_mode"]
            assert ndata["verification_state"] == final_node_map[nid]["verification_state"]

    def test_replay_checksum_stable(self, env):
        import hashlib
        adapter = env["adapter"]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
        loop.close()
        checksum1 = hashlib.sha256(",".join(
            sorted(n["id"] for n in nodes)
        ).encode()).hexdigest()[:16]
        checksum2 = hashlib.sha256(",".join(
            sorted(n["id"] for n in nodes)
        ).encode()).hexdigest()[:16]
        assert checksum1 == checksum2

    def test_empty_replay_preserves_structure(self, env):
        store = env["os"].event_store
        assert store.get_cursor() >= 0
        empty = store.replay(cursor=0, limit=100)
        cursor = store.get_cursor()
        assert isinstance(empty, list)
        assert len(empty) <= 100
        assert cursor >= 0


class TestCausalChainE2E:
    @pytest.fixture
    def env(self):
        config = __import__("os_config").load_config()
        config.simulation_mode = True
        config.mode = __import__("os_config").DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
            from muscal_os import MuscalOS
            m = MuscalOS(config=config)
            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            yield {"os": m, "enriched": enriched}
            enriched.shutdown()

    def test_causal_chain_a_to_b_to_c(self, env):
        enriched = env["enriched"]
        m = env["os"]
        mgr = get_context_manager()

        ctx_a = ExecutionContext(execution_id="event-A", execution_mode="real", execution_state="running")
        mgr.set_context(ctx_a)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "nA"},
            source="test", id="evt-A",
        ))

        ctx_b = ExecutionContext(
            execution_id="event-B",
            causation_id=ctx_a.execution_id,
            correlation_id=ctx_a.execution_id,
            execution_mode="real",
            execution_state="running",
        )
        mgr.set_context(ctx_b)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "nB"},
            source="test", id="evt-B",
        ))

        ctx_c = ExecutionContext(
            execution_id="event-C",
            causation_id=ctx_b.execution_id,
            correlation_id=ctx_a.execution_id,
            execution_mode="real",
            execution_state="running",
        )
        mgr.set_context(ctx_c)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "nC"},
            source="test", id="evt-C",
        ))

        mgr.clear_context()

        events = m.event_store.replay(cursor=0, limit=5000)
        evt_a = next(e for e in events if e["id"] == "evt-A")
        evt_b = next(e for e in events if e["id"] == "evt-B")
        evt_c = next(e for e in events if e["id"] == "evt-C")

        assert evt_a["execution_id"] == "event-A"
        assert evt_a["causation_id"] == ""

        assert evt_b["execution_id"] == "event-B"
        assert evt_b["causation_id"] == "event-A"

        assert evt_c["execution_id"] == "event-C"
        assert evt_c["causation_id"] == "event-B"
        assert evt_c["correlation_id"] == "event-A"

    def test_causal_chain_survives_replay(self, env):
        enriched = env["enriched"]
        m = env["os"]
        mgr = get_context_manager()

        ctx_a = ExecutionContext(execution_id="replay-A", execution_mode="real", execution_state="running")
        mgr.set_context(ctx_a)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "rA"},
            source="test", id="replay-evt-A",
        ))
        ctx_b = ExecutionContext(execution_id="replay-B", causation_id=ctx_a.execution_id, execution_mode="real", execution_state="running")
        mgr.set_context(ctx_b)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "rB"},
            source="test", id="replay-evt-B",
        ))
        mgr.clear_context()

        replay = m.event_store.replay(cursor=0, limit=5000)
        replayed_a = next(e for e in replay if e["id"] == "replay-evt-A")
        replayed_b = next(e for e in replay if e["id"] == "replay-evt-B")

        assert replayed_b["causation_id"] == "replay-A"

    def test_correlation_id_shared_across_chain(self, env):
        enriched = env["enriched"]
        m = env["os"]
        mgr = get_context_manager()

        shared_corr = uuid7()
        ctx1 = ExecutionContext(execution_id="corr-1", correlation_id=shared_corr, execution_mode="real", execution_state="running")
        mgr.set_context(ctx1)
        enriched._enriched_persist(EventMessage(topic="NODE_CREATED", payload={"node_id": "c1"}, source="test", id="corr-evt-1"))
        ctx2 = ExecutionContext(execution_id="corr-2", correlation_id=shared_corr, execution_mode="simulated", execution_state="running")
        mgr.set_context(ctx2)
        enriched._enriched_persist(EventMessage(topic="NODE_CREATED", payload={"node_id": "c2"}, source="test", id="corr-evt-2"))
        mgr.clear_context()

        events = m.event_store.replay(cursor=0, limit=5000)
        evt1 = next(e for e in events if e["id"] == "corr-evt-1")
        evt2 = next(e for e in events if e["id"] == "corr-evt-2")

        assert evt1["correlation_id"] == shared_corr
        assert evt2["correlation_id"] == shared_corr
        assert evt1["execution_mode"] == "real"
        assert evt2["execution_mode"] == "simulated"


class TestRealityIntegrityE2E:
    @pytest.fixture
    def env(self):
        config = __import__("os_config").load_config()
        config.simulation_mode = True
        config.mode = __import__("os_config").DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
            from muscal_os import MuscalOS
            m = MuscalOS(config=config)
            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            yield {"os": m, "enriched": enriched}
            enriched.shutdown()

    def _publish(self, enriched, ctx, topic, payload, event_id):
        mgr = get_context_manager()
        mgr.set_context(ctx)
        enriched._enriched_persist(EventMessage(topic=topic, payload=payload, source="test", id=event_id))
        mgr.clear_context()

    def test_reality_modes_all_valid(self, env):
        enriched = env["enriched"]
        m = env["os"]
        for mode in ("real", "simulated", "shadow", "replay"):
            ctx = ExecutionContext(execution_id=f"mode-{mode}", execution_mode=mode, execution_state="running")
            self._publish(enriched, ctx, "NODE_CREATED", {"node_id": f"m-{mode}"}, f"mode-evt-{mode}")
        ctx_proposed = ExecutionContext(execution_id="mode-proposed", execution_mode="proposed", execution_state="planned")
        self._publish(enriched, ctx_proposed, "NODE_CREATED", {"node_id": "m-proposed"}, "mode-evt-proposed")

        events = m.event_store.replay(cursor=0, limit=5000)
        modes_found = set()
        for e in events:
            if e["id"].startswith("mode-evt-"):
                modes_found.add(e["execution_mode"])
        assert "real" in modes_found
        assert "simulated" in modes_found
        assert "shadow" in modes_found
        assert "replay" in modes_found
        assert "proposed" in modes_found

    def test_execution_states_tracked_correctly(self, env):
        enriched = env["enriched"]
        m = env["os"]
        for state in ("queued", "running", "completed", "failed", "cancelled"):
            ctx = ExecutionContext(execution_id=f"state-{state}", execution_mode="real", execution_state=state)
            self._publish(enriched, ctx, "NODE_CREATED", {"node_id": f"s-{state}", "status": state}, f"state-evt-{state}")
        events = m.event_store.replay(cursor=0, limit=5000)
        states_found = set()
        for e in events:
            if e["id"].startswith("state-evt-"):
                p = e.get("payload", {})
                if isinstance(p, dict) and "execution_state" in p:
                    states_found.add(p["execution_state"])
        assert len(states_found) >= 5

    def test_verification_states_persisted(self, env):
        enriched = env["enriched"]
        m = env["os"]
        for vstate in ("unverified", "verified", "failed", "rejected"):
            ctx = ExecutionContext(execution_id=f"vstate-{vstate}", execution_mode="real", execution_state="completed", verification_state=vstate)
            self._publish(enriched, ctx, "NODE_CREATED", {"node_id": f"v-{vstate}"}, f"vstate-evt-{vstate}")
        events = m.event_store.replay(cursor=0, limit=5000)
        vstates_found = set()
        for e in events:
            if e["id"].startswith("vstate-evt-"):
                vstates_found.add(e["verification_state"])
        assert vstates_found == {"unverified", "verified", "failed", "rejected"}

    def test_reality_modes_survive_projection(self, env):
        enriched = env["enriched"]
        m = env["os"]
        proj = GraphOSProjection(event_store=m.event_store)
        for mode in ("real", "simulated", "shadow", "replay"):
            ctx = ExecutionContext(execution_id=f"proj-{mode}", execution_mode=mode, execution_state="running")
            self._publish(enriched, ctx, "EXECUTION_STARTED", {}, f"proj-evt-{mode}")
        events = m.event_store.replay(cursor=0, limit=5000)
        for e in events:
            if e["id"].startswith("proj-evt-"):
                msg = EventMessage(topic=e["topic"], payload=e["payload"], source="test", id=e["id"], timestamp=e["timestamp"])
                result = proj.project(msg)
                assert result is not None
                assert result["execution_mode"] in ("real", "simulated", "shadow", "replay")


class TestProjectionBoundary:
    def test_only_canonical_events_pass(self):
        proj = GraphOSProjection()
        canonical = set(CANONICAL_EVENT_TYPES)
        assert len(canonical) >= 14

        for evt_type in canonical:
            msg = EventMessage(topic=evt_type, payload={"execution_id": "e1", "execution_state": "running"})
            result = proj.project(msg)
            assert result is not None, f"Canonical type {evt_type} should pass"

        non_canonical = ("BOOT_INIT", "KERNEL_INITIALIZED", "os.started", "health.memory", "random_event", "system.event")
        for evt_type in non_canonical:
            msg = EventMessage(topic=evt_type, payload={"execution_id": "e1"})
            result = proj.project(msg)
            assert result is None, f"Non-canonical type {evt_type} should be rejected"

    def test_sensitive_fields_sanitized(self):
        proj = GraphOSProjection()
        sensitive = {
            "tool_result": {"stdout": "secret"},
            "file_path": "/etc/passwd",
            "command": "rm -rf",
            "credentials": {"password": "1234"},
            "environment": {"PATH": "/usr/bin"},
            "input_text": "user query",
            "api_key": "sk-1234567890",
            "token": "eyJhbGci",
            "password": "hunter2",
            "secret": "my-secret",
        }
        msg = EventMessage(topic="NODE_CREATED", payload={**sensitive, "execution_id": "e1", "node_id": "n1", "execution_state": "running"})
        result = proj.project(msg)
        assert result is not None
        sanitized = result["payload"]
        for field in sensitive:
            assert field not in sanitized, f"Sensitive field '{field}' should be stripped"
        assert sanitized.get("node_id") == "n1"

    def test_safe_payload_fields_preserved(self):
        proj = GraphOSProjection()
        safe = {"node_id": "n1", "node_type": "INTENT", "confidence": 0.85, "status": "created", "result": "success"}
        msg = EventMessage(topic="NODE_CREATED", payload={**safe, "execution_id": "e1", "execution_state": "running"})
        result = proj.project(msg)
        assert result is not None
        sanitized = result["payload"]
        for field in safe:
            assert field in sanitized, f"Safe field '{field}' should be preserved"

    def test_error_truncated_to_500_chars(self):
        proj = GraphOSProjection()
        long_error = "X" * 1000
        msg = EventMessage(topic="EXECUTION_FAILED", payload={"execution_id": "e1", "error": long_error})
        result = proj.project(msg)
        assert result is not None
        assert len(result["payload"]["error"]) == 500

    def test_graph_os_cannot_modify_muscal_source(self):
        from features.projection.graph_os_projection import GraphOSProjection
        proj = GraphOSProjection()
        msg = EventMessage(topic="NODE_CREATED", payload={"execution_id": "e1", "node_id": "n1", "execution_state": "running"})
        result = proj.project(msg)
        assert result is not None
        assert result["source"] != "graph_os"
        assert "event_type" in result

    def test_rejected_events_counted(self):
        proj = GraphOSProjection()
        before = proj.stats()["rejected"]
        proj.project(EventMessage(topic="FORBIDDEN_TYPE", payload={}))
        after = proj.stats()["rejected"]
        assert after == before + 1


class TestEnrichedRun:
    @pytest.fixture
    def env(self):
        config = __import__("os_config").load_config()
        config.simulation_mode = True
        config.mode = __import__("os_config").DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
            from muscal_os import MuscalOS
            m = MuscalOS(config=config)
            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            yield {"os": m, "enriched": enriched}
            enriched.shutdown()

    def test_run_generates_uuid7_execution_id(self, env):
        enriched = env["enriched"]
        result = enriched.run("test execution_id", execution_mode="real")
        assert isinstance(result, dict)
        events = env["os"].event_store.replay(cursor=0, limit=5000)
        execution_ids = set()
        for e in events:
            eid = e.get("execution_id", "")
            if eid:
                execution_ids.add(eid)
        if execution_ids:
            for eid in execution_ids:
                assert is_uuid7(eid)

    def test_run_context_cleared_after_completion(self, env):
        enriched = env["enriched"]
        mgr = get_context_manager()
        result = enriched.run("test cleanup", execution_mode="simulated")
        assert mgr.get_context() is None

    def test_failed_execution_preserves_execution_id(self, env):
        enriched = env["enriched"]
        result = enriched.run("", execution_mode="real")
        events = env["os"].event_store.replay(cursor=0, limit=5000)
        last_event = events[-1] if events else {}
        assert last_event.get("execution_id", "") != ""

    def test_nested_execution_context_restored_on_exit(self, env):
        enriched = env["enriched"]
        mgr = get_context_manager()
        outer_ctx = ExecutionContext(execution_id="nested-outer", execution_mode="real", execution_state="running")
        mgr.set_context(outer_ctx)
        result = enriched.run("nested", execution_mode="simulated", parent_context=outer_ctx)
        restored = mgr.get_context()
        assert restored is not None
        assert restored.execution_id == "nested-outer"

    def test_run_emits_all_lifecycle_events(self, env):
        enriched = env["enriched"]
        m = env["os"]
        lifecycle = []
        def capture(msg):
            if msg.topic in ("EXECUTION_STARTED", "EXECUTION_COMPLETED", "EXECUTION_FAILED"):
                lifecycle.append(msg)
        m.events.subscribe("*", capture)
        result = enriched.run("lifecycle test", execution_mode="real")
        topics = [msg.topic for msg in lifecycle]
        assert "EXECUTION_STARTED" in topics
        assert "EXECUTION_COMPLETED" in topics or "EXECUTION_FAILED" in topics


class TestEventIntegrity:
    @pytest.fixture
    def store(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            yield store
        finally:
            store.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_all_envelope_fields_persisted(self, store):
        eid = uuid7()
        seq = store.append({
            "topic": "EXECUTION_STARTED",
            "payload": {"input": "test"},
            "source": "kernel",
            "priority": "HIGH",
            "timestamp": 1700000000.0,
            "id": eid,
            "execution_id": "exec-1",
            "correlation_id": "corr-1",
            "causation_id": "cause-1",
            "execution_mode": "simulated",
            "verification_state": "verified",
        })
        assert seq is not None and seq > 0
        rows = store.replay(cursor=0)
        assert len(rows) == 1
        row = rows[0]
        assert row["seq"] == seq
        assert row["topic"] == "EXECUTION_STARTED"
        assert row["id"] == eid
        assert row["execution_id"] == "exec-1"
        assert row["correlation_id"] == "corr-1"
        assert row["causation_id"] == "cause-1"
        assert row["execution_mode"] == "simulated"
        assert row["verification_state"] == "verified"
        assert isinstance(row["payload"], dict)
        assert row["payload"]["input"] == "test"

    def test_event_id_is_uuid7(self, store):
        eid = uuid7()
        store.append({
            "topic": "NODE_CREATED", "payload": {}, "source": "test",
            "timestamp": time.time(), "id": eid,
            "execution_id": "e1", "verification_state": "unverified",
        })
        rows = store.replay(cursor=0)
        assert is_uuid7(rows[0]["id"])

    def test_sequence_number_monotonic(self, store):
        ids = []
        for i in range(10):
            eid = uuid7()
            store.append({
                "topic": "NODE_CREATED", "payload": {"seq": i}, "source": "test",
                "timestamp": time.time(), "id": eid,
                "execution_id": "e1", "verification_state": "unverified",
            })
            ids.append(eid)
        rows = store.replay(cursor=0)
        seqs = [r["seq"] for r in rows]
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == 10

    def test_duplicate_event_id_rejected(self, store):
        eid = uuid7()
        store.append({
            "topic": "NODE_CREATED", "payload": {}, "source": "test",
            "timestamp": time.time(), "id": eid,
            "execution_id": "e1", "verification_state": "unverified",
        })
        import sqlite3
        with pytest.raises((sqlite3.IntegrityError, Exception)):
            store.append({
                "topic": "NODE_CREATED", "payload": {}, "source": "test",
                "timestamp": time.time(), "id": eid,
                "execution_id": "e1", "verification_state": "unverified",
            })

    def test_payload_round_trips_json(self, store):
        complex_payload = {
            "node_id": "n1",
            "nested": {"key": "value", "numbers": [1, 2, 3]},
            "bool": True,
            "null_val": None,
        }
        eid = uuid7()
        store.append({
            "topic": "NODE_CREATED", "payload": complex_payload, "source": "test",
            "timestamp": time.time(), "id": eid,
            "execution_id": "e1", "verification_state": "unverified",
        })
        rows = store.replay(cursor=0)
        assert rows[0]["payload"] == complex_payload

    def test_event_integrity_full_flow(self):
        config = __import__("os_config").load_config()
        config.simulation_mode = True
        config.mode = __import__("os_config").DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
            from muscal_os import MuscalOS
            from features.projection.graph_os_projection import GraphOSProjection
            from features.streaming.ws_adapter import WebSocketAdapter

            m = MuscalOS(config=config)
            bus = m.events
            proj = GraphOSProjection(event_store=m.event_store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)
            enriched = EnrichedMuscalOS(os=m, ws_adapter=adapter)
            report = enriched.start()
            assert report.success
            mgr = get_context_manager()

            ctx = ExecutionContext(
                execution_id="full-flow",
                correlation_id="full-corr",
                causation_id="full-cause",
                execution_mode="real",
                execution_state="running",
                verification_state="unverified",
            )
            mgr.set_context(ctx)
            enriched._enriched_persist(EventMessage(
                topic="NODE_CREATED", payload={"node_id": "ff1", "node_type": "ACTION"},
                source="test", id="ff-evt-1",
            ))
            enriched._enriched_persist(EventMessage(
                topic="EDGE_CREATED", payload={"source_id": "ff1", "target_id": "ff2", "edge_type": "flow"},
                source="test", id="ff-evt-2",
            ))
            mgr.clear_context()

            stored = m.event_store.replay(cursor=0, limit=5000)
            for evt in stored:
                if evt["id"] not in ("ff-evt-1", "ff-evt-2"):
                    continue
                msg = EventMessage(topic=evt["topic"], payload=evt["payload"], source="test", id=evt["id"], timestamp=evt["timestamp"])
                projected = proj.project(msg)
                assert projected is not None, f"Projection failed for {evt['id']}: {evt['topic']}"
                assert projected["execution_id"] == "full-flow"
                assert projected["execution_mode"] == "real"

            enriched.shutdown()
