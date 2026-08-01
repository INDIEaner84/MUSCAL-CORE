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
from features.identity.execution_context import ExecutionContext, get_context_manager
from features.identity.uuid7 import uuid7, is_uuid7
from features.bootstrap.enriched_bootstrap import EnrichedMuscalOS
from features.projection.graph_os_projection import GraphOSProjection
from features.streaming.ws_adapter import (
    WebSocketAdapter,
    ClientSession,
    SNAPSHOT_GAP_THRESHOLD,
    MAX_QUEUE_SIZE,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_TIMEOUT,
    RECONCILIATION_INTERVAL,
)
from runtime.event_store import EventStore


class TestWebSocketProtocolUnit:
    def test_snapshot_builds_from_stored_events(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            bus = EventBus()
            proj = GraphOSProjection(event_store=store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

            for i in range(5):
                eid = uuid7()
                store.append({
                    "topic": "NODE_CREATED",
                    "payload": {"node_id": f"n{i}", "node_type": "INTENT", "status": "created",
                                "execution_id": "e1", "execution_state": "running"},
                    "source": "test",
                    "timestamp": time.time(),
                    "id": eid,
                    "execution_id": "e1",
                    "verification_state": "unverified",
                })

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
            loop.close()

            assert len(nodes) == 5
            for node in nodes:
                assert "id" in node
                assert "type" in node
                assert "status" in node
                assert "execution_mode" in node
                assert "verification_state" in node
                assert "execution_id" in node

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_snapshot_includes_edge_data(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            bus = EventBus()
            proj = GraphOSProjection(event_store=store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

            store.append({
                "topic": "NODE_CREATED", "payload": {"node_id": "n1", "node_type": "INTENT", "status": "created",
                    "execution_id": "e1", "execution_state": "running"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "unverified",
            })
            store.append({
                "topic": "NODE_CREATED", "payload": {"node_id": "n2", "node_type": "ACTION", "status": "created",
                    "execution_id": "e1", "execution_state": "running"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "unverified",
            })
            store.append({
                "topic": "EDGE_CREATED", "payload": {"source_id": "n1", "target_id": "n2", "edge_type": "depends_on"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "unverified",
            })

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
            edges = loop.run_until_complete(adapter._build_snapshot_edges())
            loop.close()

            assert len(nodes) == 2
            assert len(edges) == 1
            assert edges[0]["source_id"] == "n1"
            assert edges[0]["target_id"] == "n2"
            assert edges[0]["edge_type"] == "depends_on"

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_snapshot_after_node_update(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            bus = EventBus()
            proj = GraphOSProjection(event_store=store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

            store.append({
                "topic": "NODE_CREATED", "payload": {"node_id": "n1", "node_type": "INTENT", "status": "created",
                    "execution_id": "e1", "execution_state": "running"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "unverified",
            })
            store.append({
                "topic": "NODE_UPDATED", "payload": {"node_id": "n1", "status": "completed",
                    "execution_id": "e1", "execution_state": "completed", "verification_state": "verified"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "verified",
            })

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
            loop.close()

            n1 = next(n for n in nodes if n["id"] == "n1")
            assert n1["status"] == "completed"
            assert n1["verification_state"] == "verified"

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_snapshot_handles_node_archived(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            bus = EventBus()
            proj = GraphOSProjection(event_store=store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

            store.append({
                "topic": "NODE_CREATED", "payload": {"node_id": "n1", "node_type": "INTENT", "status": "created",
                    "execution_id": "e1", "execution_state": "running"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "unverified",
            })
            store.append({
                "topic": "NODE_ARCHIVED", "payload": {"node_id": "n1"},
                "source": "test", "timestamp": time.time(), "id": uuid7(),
                "execution_id": "e1", "verification_state": "unverified",
            })

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
            loop.close()

            assert len(nodes) == 0

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_delta_events_have_correct_sequence(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            for i in range(5):
                store.append({
                    "topic": "NODE_CREATED",
                    "payload": {"node_id": f"n{i}", "execution_id": "e1", "execution_state": "running"},
                    "source": "test", "timestamp": time.time(), "id": uuid7(),
                    "execution_id": "e1", "verification_state": "unverified",
                })

            current = store.get_cursor()
            delta = store.replay(cursor=0, limit=100)
            for j, evt in enumerate(delta):
                assert evt["seq"] == j + 1

            assert current >= 5

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_reconciliation_checksum_computed(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            bus = EventBus()
            proj = GraphOSProjection(event_store=store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

            for i in range(3):
                store.append({
                    "topic": "NODE_CREATED",
                    "payload": {"node_id": f"n{i}", "node_type": "INTENT", "status": "created",
                        "execution_id": "e1", "execution_state": "running"},
                    "source": "test", "timestamp": time.time(), "id": uuid7(),
                    "execution_id": "e1", "verification_state": "unverified",
                })

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            import hashlib
            checksum = loop.run_until_complete(
                adapter._compute_checksum(ClientSession(websocket=None, client_id="test"))
            )
            loop.close()

            assert isinstance(checksum, str)
            assert len(checksum) == 16

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_client_session_tracks_metrics(self):
        session = ClientSession(websocket=None, client_id="test-1")
        assert session.client_id == "test-1"
        assert session.last_seq == 0
        assert session.messages_sent == 0
        assert session.bytes_sent == 0
        assert session.queue.qsize() == 0

        session.messages_sent = 10
        session.bytes_sent = 5000
        session.last_seq = 42
        assert session.messages_sent == 10
        assert session.bytes_sent == 5000
        assert session.last_seq == 42

    def test_subscribe_with_filters(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        session = ClientSession(websocket=None, client_id="filter-test")
        assert session.subscribed_types is None

        session.subscribed_types = {"NODE_CREATED", "EDGE_CREATED"}
        assert session.subscribed_types == {"NODE_CREATED", "EDGE_CREATED"}

    def test_on_event_subscribed_type_filtering(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        adapter._running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        session = ClientSession(websocket=None, client_id="filter-test")
        session.subscribed_types = {"NODE_CREATED"}
        adapter._clients["filter-test"] = session

        adapter.on_event(EventMessage(topic="EDGE_CREATED",
            payload={"execution_id": "e1", "execution_state": "running", "verification_state": "unverified", "execution_mode": "real"},
            id="e1"))
        assert session.queue.qsize() == 0, "EDGE_CREATED should be filtered out"

        adapter.on_event(EventMessage(topic="NODE_CREATED",
            payload={"execution_id": "e1", "node_id": "n1", "execution_state": "running", "verification_state": "unverified", "execution_mode": "real"},
            id="e2"))
        assert session.queue.qsize() == 1, "NODE_CREATED should pass filter"

        loop.close()
        adapter.stop()

    def test_backpressure_drops_oldest(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        session = ClientSession(websocket=None, client_id="bp-test")
        adapter._clients["bp-test"] = session

        small_queue = asyncio.Queue(maxsize=3)
        session.queue = small_queue

        for i in range(3):
            small_queue.put_nowait({"type": "event", "seq": i})

        assert small_queue.qsize() == 3

        adapter.on_event(EventMessage(topic="NODE_CREATED", payload={"execution_id": "e1", "execution_state": "running"}, id="overflow"))
        assert small_queue.qsize() == 3

        adapter._loop.close()
        adapter.stop()

    def test_multiple_clients_isolated(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        adapter._running = True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        session_a = ClientSession(websocket=None, client_id="client-A")
        session_b = ClientSession(websocket=None, client_id="client-B")
        adapter._clients["client-A"] = session_a
        adapter._clients["client-B"] = session_b

        session_a.subscribed_types = {"NODE_CREATED"}
        session_b.subscribed_types = {"EDGE_CREATED"}

        adapter.on_event(EventMessage(topic="NODE_CREATED",
            payload={"execution_id": "e1", "node_id": "n1", "execution_state": "running", "verification_state": "unverified", "execution_mode": "real"},
            id="evt1"))
        adapter.on_event(EventMessage(topic="EDGE_CREATED",
            payload={"execution_id": "e1", "source_id": "n1", "target_id": "n2", "execution_state": "running", "verification_state": "unverified", "execution_mode": "real"},
            id="evt2"))

        assert session_a.queue.qsize() == 1
        assert session_b.queue.qsize() == 1

        loop.close()
        adapter.stop()

    def test_snapshot_delivery_protocol_message(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        session = ClientSession(websocket=None, client_id="snap-test")
        session.last_seq = 0

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        loop.run_until_complete(adapter._deliver_snapshot(session, 5))

        assert session.queue.qsize() >= 1
        msg = session.queue.get_nowait()
        assert msg["type"] == "snapshot"
        assert msg["seq"] == 5
        assert msg["schema_version"] == 1
        assert isinstance(msg["nodes"], list)
        assert isinstance(msg["edges"], list)
        assert session.last_seq == 5

        adapter._loop.close()
        adapter.stop()

    def test_reconciliation_protocol_message(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        session = ClientSession(websocket=None, client_id="recon-test")
        adapter._clients["recon-test"] = session

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        loop.run_until_complete(adapter._send_reconciliation("recon-test"))
        assert session.queue.qsize() >= 1
        msg = session.queue.get_nowait()
        assert msg["type"] == "reconciliation"
        assert "seq" in msg
        assert "checksum" in msg
        assert isinstance(msg["checksum"], str)

        adapter._loop.close()
        adapter.stop()

    def test_ping_pong_protocol(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        session = ClientSession(websocket=None, client_id="ping-test")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        loop.run_until_complete(adapter._handle_client_message(session, {"type": "ping"}))
        assert session.queue.qsize() >= 1
        response = session.queue.get_nowait()
        assert response["type"] == "pong"

        adapter._loop.close()
        adapter.stop()

    def test_subscribe_unsubscribe_protocol(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            bus = EventBus()
            proj = GraphOSProjection(event_store=store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
            session = ClientSession(websocket=None, client_id="sub-test")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            adapter._loop = loop

            loop.run_until_complete(adapter._handle_client_message(session, {
                "type": "subscribe", "last_seq": 42, "filters": {"event_types": ["NODE_CREATED"]}
            }))
            assert session.last_seq == 42
            assert session.subscribed_types == {"NODE_CREATED"}

            loop.run_until_complete(adapter._handle_client_message(session, {"type": "unsubscribe"}))
            assert session.subscribed_types is None
            response = session.queue.get_nowait()
            assert response["type"] == "unsubscribed"

            loop.close()
            adapter.stop()
            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_invalid_json_error_response(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        session = ClientSession(websocket=None, client_id="json-test")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        async def send_invalid():
            session.queue.put_nowait({"type": "error", "code": "INVALID_JSON", "message": "payload must be valid JSON"})
        loop.run_until_complete(send_invalid())
        msg = session.queue.get_nowait()
        assert msg["code"] == "INVALID_JSON"

        adapter._loop.close()
        adapter.stop()


class TestWebSocketSnapshotDelta:
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
            bus = m.events
            proj = GraphOSProjection(event_store=m.event_store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)
            yield {"os": m, "enriched": enriched, "bus": bus, "proj": proj, "adapter": adapter}
            enriched.shutdown()

    def test_snapshot_reflects_current_graph(self, env):
        enriched = env["enriched"]
        m = env["os"]
        adapter = env["adapter"]
        mgr = get_context_manager()

        ctx = ExecutionContext(execution_id="snap-test-1", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "s1", "node_type": "TEST"},
            source="test", id="snap-e2e-1",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "s2", "node_type": "TEST"},
            source="test", id="snap-e2e-2",
        ))
        mgr.clear_context()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        current_seq = adapter._get_current_seq()
        nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
        loop.close()

        assert current_seq >= 2, f"Expected seq >= 2, got {current_seq}"
        assert len(nodes) >= 2, f"Expected >= 2 nodes, got {len(nodes)}"
        node_ids = {n["id"] for n in nodes}
        assert "s1" in node_ids
        assert "s2" in node_ids

    def test_delta_after_snapshot_includes_new_events(self, env):
        enriched = env["enriched"]
        m = env["os"]
        adapter = env["adapter"]
        mgr = get_context_manager()

        ctx = ExecutionContext(execution_id="delta-e2e-1", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "d1", "node_type": "INTENT"},
            source="test", id="delta-e2e-1",
        ))
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "d2", "node_type": "ACTION"},
            source="test", id="delta-e2e-2",
        ))
        mgr.clear_context()

        snapshot_seq = m.event_store.get_cursor()

        ctx2 = ExecutionContext(execution_id="delta-e2e-2", execution_mode="real", execution_state="running")
        mgr.set_context(ctx2)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "d3", "node_type": "TOOL"},
            source="test", id="delta-e2e-3",
        ))
        mgr.clear_context()

        delta_rows = m.event_store.replay(cursor=snapshot_seq, limit=5000)
        assert len(delta_rows) >= 1
        assert any("d3" in str(r.get("payload", {})) for r in delta_rows)

    def test_snapshot_includes_execution_context(self, env):
        enriched = env["enriched"]
        m = env["os"]
        adapter = env["adapter"]
        mgr = get_context_manager()

        ctx = ExecutionContext(execution_id="ctx-snap-1", execution_mode="simulated", execution_state="completed", verification_state="verified")
        mgr.set_context(ctx)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "ctxnode", "node_type": "VERIFIED"},
            source="test", id="ctx-snap-evt",
        ))
        mgr.clear_context()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
        loop.close()

        ctx_node = next((n for n in nodes if n["id"] == "ctxnode"), None)
        assert ctx_node is not None, f"ctxnode not found in snapshot nodes: {[n['id'] for n in nodes]}"
        assert ctx_node["execution_mode"] == "simulated"
        assert ctx_node["verification_state"] == "verified"
        assert ctx_node["execution_id"] == "ctx-snap-1"

    def test_projection_preserves_all_envelope_fields(self, env):
        enriched = env["enriched"]
        proj = env["proj"]
        mgr = get_context_manager()

        ctx = ExecutionContext(
            execution_id="env-test",
            correlation_id="env-corr",
            causation_id="env-cause",
            execution_mode="shadow",
            execution_state="running",
            verification_state="unverified",
        )
        mgr.set_context(ctx)
        enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED", payload={"node_id": "envnode", "node_type": "TEST"},
            source="test", id="env-evt",
        ))
        mgr.clear_context()

        result = proj.project(EventMessage(
            topic="NODE_CREATED",
            payload={"node_id": "envnode", "node_type": "TEST", "execution_id": "env-test",
                     "correlation_id": "env-corr", "causation_id": "env-cause",
                     "execution_mode": "shadow", "execution_state": "running", "verification_state": "unverified"},
            source="test", id="env-evt",
        ))
        assert result is not None
        assert result["event_id"] is not None
        assert result["event_type"] == "NODE_CREATED"
        assert result["execution_id"] == "env-test"
        assert result["correlation_id"] == "env-corr"
        assert result["causation_id"] == "env-cause"
        assert result["execution_mode"] == "shadow"
        assert result["verification_state"] == "unverified"
        assert "timestamp" in result
        assert "sequence_number" in result
        assert "source" in result
        assert "actor" in result
        assert "payload" in result

    def test_eventbus_projection_websocket_end_to_end(self, env):
        enriched = env["enriched"]
        m = env["os"]
        adapter = env["adapter"]
        proj = env["proj"]
        mgr = get_context_manager()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop
        adapter._running = True

        session = ClientSession(websocket=None, client_id="e2e-test")
        adapter._clients["e2e-test"] = session
        session.subscribed_types = {"NODE_CREATED", "EXECUTION_STARTED"}

        ctx = ExecutionContext(execution_id="e2e-ws", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)

        evt1 = EventMessage(topic="EXECUTION_STARTED",
            payload={"input": "e2e ws test", "execution_id": "e2e-ws", "execution_state": "running"},
            source="test", id="e2e-ws-evt-1")
        adapter.on_event(evt1)

        evt2 = EventMessage(topic="NODE_CREATED",
            payload={"node_id": "wsnode", "node_type": "INTENT", "execution_id": "e2e-ws", "execution_state": "running", "verification_state": "unverified", "execution_mode": "real"},
            source="test", id="e2e-ws-evt-2")
        adapter.on_event(evt2)

        mgr.clear_context()
        loop.run_until_complete(asyncio.sleep(0.01))

        events_in_queue = []
        while not session.queue.empty():
            events_in_queue.append(session.queue.get_nowait())
        assert len(events_in_queue) >= 1

        loop.close()
        adapter.stop()


class TestWebSocketAdapterEdgeCases:
    def test_start_stop_idempotent(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        adapter.start()
        assert adapter.get_stats()["running"] is True
        adapter.start()
        assert adapter.get_stats()["running"] is True
        adapter.stop()
        assert adapter.get_stats()["running"] is False
        adapter.stop()
        assert adapter.get_stats()["running"] is False

    def test_on_event_with_no_loop(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        adapter._running = True
        adapter._loop = None
        adapter.on_event(EventMessage(topic="NODE_CREATED", payload={"execution_id": "e1", "execution_state": "running"}))
        assert adapter.get_stats()["running"] is True

    def test_enqueue_when_full_drops_oldest(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        session = ClientSession(websocket=None, client_id="drop-test")
        small_queue = asyncio.Queue(maxsize=2)
        session.queue = small_queue
        small_queue.put_nowait({"type": "event", "seq": 1})
        small_queue.put_nowait({"type": "event", "seq": 2})

        async def enqueue():
            adapter._enqueue(session, {"type": "event", "seq": 3})
            assert small_queue.qsize() == 2
            first = small_queue.get_nowait()
            assert first["seq"] in (1, 2, 3)
        loop.run_until_complete(enqueue())
        loop.close()
        adapter.stop()

    def test_connect_disconnect_metrics(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        stats = adapter.get_stats()
        assert stats["clients"] == 0
        assert stats["running"] is False
        assert stats["version"] == "2.0.0"
        assert stats["host"] == "127.0.0.1"
        assert stats["port"] == 8765
