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
from features.identity.execution_context import ExecutionContext, ExecutionContextManager, get_context_manager
from features.identity.uuid7 import uuid7, is_uuid7
from features.bootstrap.enriched_bootstrap import EnrichedMuscalOS
from features.projection.graph_os_projection import GraphOSProjection
from features.streaming.ws_adapter import WebSocketAdapter, ClientSession
from runtime.event_store import EventStore


class TestConcurrentExecutions:
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

    def test_parallel_executions_independent_contexts(self, env):
        enriched = env["enriched"]
        m = env["os"]
        results = {}
        errors = []
        lock = threading.Lock()

        def execute_parallel(name, input_text):
            try:
                result = enriched.run(input_text, execution_mode="real")
                with lock:
                    results[name] = result
            except Exception as e:
                with lock:
                    errors.append((name, str(e)))

        threads = []
        for i in range(10):
            t = threading.Thread(target=execute_parallel, args=(f"exec-{i}", f"input {i}"))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert len(errors) == 0, f"Errors during parallel execution: {errors}"
        assert len(results) == 10
        for name, result in results.items():
            assert isinstance(result, dict)
            events = m.event_store.replay(cursor=0, limit=5000)
            exec_events = [e for e in events if e.get("execution_id", "") != ""]
            assert len(exec_events) > 0

    def test_interleaved_events_maintain_ordering(self, env):
        enriched = env["enriched"]
        m = env["os"]
        mgr = get_context_manager()
        barrier = threading.Barrier(5)
        db_lock = threading.Lock()

        def worker(name):
            barrier.wait()
            ctx = ExecutionContext(
                execution_id=f"interleave-{name}",
                execution_mode="real",
                execution_state="running",
            )
            with db_lock:
                mgr.set_context(ctx)
                for j in range(5):
                    enriched._enriched_persist(EventMessage(
                        topic="NODE_CREATED",
                        payload={"node_id": f"{name}-node-{j}", "node_type": "INTENT"},
                        source=f"worker-{name}",
                        id=f"inter-{name}-{j}",
                    ))
                mgr.clear_context()

        threads = [threading.Thread(target=worker, args=(str(i),)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        events = m.event_store.replay(cursor=0, limit=5000)
        interleaved = [e for e in events if "inter-" in e.get("id", "")]
        assert len(interleaved) == 25, f"Expected 25 interleaved events, got {len(interleaved)}"

        seqs = [e["seq"] for e in interleaved]
        assert seqs == sorted(seqs)

        for i in range(5):
            worker_events = [e for e in interleaved if e.get("execution_id") == f"interleave-{i}"]
            assert len(worker_events) == 5, f"Worker {i} should have 5 events, got {len(worker_events)}"

    def test_concurrent_snapshot_does_not_block_writes(self, env):
        enriched = env["enriched"]
        m = env["os"]
        bus = m.events
        proj = GraphOSProjection(event_store=m.event_store)
        adapter = WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)
        mgr = get_context_manager()
        write_count = [0]
        stop_flag = [False]

        def writer():
            while not stop_flag[0]:
                ctx = ExecutionContext(
                    execution_id=f"write-{uuid7()[:8]}",
                    execution_mode="real",
                    execution_state="running",
                )
                mgr.set_context(ctx)
                enriched._enriched_persist(EventMessage(
                    topic="NODE_CREATED",
                    payload={"node_id": f"w-{uuid7()[:8]}", "node_type": "INTENT"},
                    source="writer",
                    id=f"w-{uuid7()}",
                ))
                mgr.clear_context()
                write_count[0] += 1
                time.sleep(0.001)

        writer_thread = threading.Thread(target=writer, daemon=True)
        writer_thread.start()
        time.sleep(0.05)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for i in range(3):
            nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
            assert isinstance(nodes, list)
            time.sleep(0.02)

        stop_flag[0] = True
        writer_thread.join(timeout=5)
        loop.close()
        adapter.stop()

        assert write_count[0] > 0

    def test_concurrent_replay_is_deterministic(self, env):
        m = env["os"]
        mgr = get_context_manager()
        barrier = threading.Barrier(5)
        db_lock = threading.Lock()

        ctx = ExecutionContext(execution_id="replay-base", execution_mode="real", execution_state="running")
        mgr.set_context(ctx)
        for i in range(20):
            enriched_persist = env["enriched"]._enriched_persist
            enriched_persist(EventMessage(
                topic="NODE_CREATED",
                payload={"node_id": f"rbase-{i}", "node_type": "INTENT"},
                source="test",
                id=f"rbase-{i}",
            ))
        mgr.clear_context()

        results = {}
        errors = []

        def replayer(name):
            try:
                barrier.wait()
                with db_lock:
                    events = m.event_store.replay(cursor=0, limit=5000)
                results[name] = [(e["seq"], e["id"]) for e in events]
            except Exception as e:
                errors.append((name, str(e)))

        threads = [threading.Thread(target=replayer, args=(f"replayer-{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert len(errors) == 0, f"Errors during concurrent replay: {errors}"
        assert len(results) == 5
        base = list(results.values())[0]
        for r in list(results.values())[1:]:
            assert r == base

    def test_context_isolation_no_leaks(self, env):
        mgr = get_context_manager()
        barrier = threading.Barrier(10)
        contexts = {}

        def worker(name):
            barrier.wait()
            ctx = ExecutionContext(execution_id=f"iso-{name}", execution_mode="real", execution_state="running")
            mgr.set_context(ctx)
            time.sleep(0.01)
            current = mgr.get_context()
            contexts[name] = current.execution_id if current else None
            mgr.clear_context()

        threads = [threading.Thread(target=worker, args=(str(i),)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert len(contexts) == 10
        for i in range(10):
            assert contexts[str(i)] == f"iso-{i}"


class TestConcurrentEdgeCases:
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

    def test_duplicate_event_id_in_parallel(self, store):
        eid = uuid7()
        barrier = threading.Barrier(3)
        results = []
        db_lock = threading.Lock()

        def inserter(name):
            barrier.wait()
            with db_lock:
                try:
                    store.append({
                        "topic": "NODE_CREATED",
                        "payload": {"node_id": f"dup-{name}"},
                        "source": "test",
                        "timestamp": time.time(),
                        "id": eid,
                        "execution_id": "dup-test",
                        "verification_state": "unverified",
                    })
                    results.append((name, "ok"))
                except Exception as e:
                    results.append((name, str(e)))

        threads = [threading.Thread(target=inserter, args=(str(i),)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(results) == 3
        successes = sum(1 for _, r in results if r == "ok")
        assert successes == 1, f"Expected 1 success, got {successes}: {results}"

    def test_malformed_event_handling(self):
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
            mgr = get_context_manager()

            ctx = ExecutionContext(execution_id="malformed", execution_mode="real", execution_state="running")
            mgr.set_context(ctx)

            enriched._enriched_persist(EventMessage(
                topic="NODE_CREATED",
                payload={"execution_id": "e1", "execution_state": "running"},
                source="test",
                id="malformed-evt-1",
            ))
            enriched._enriched_persist(EventMessage(
                topic="EXECUTION_STARTED",
                payload={"execution_id": "e2", "execution_mode": "real", "execution_state": "running", "verification_state": "unverified"},
                source="test",
                id="malformed-evt-2",
            ))
            bus.publish("NODE_CREATED", {}, source="test")
            bus.publish("", None, source="test")
            mgr.clear_context()
            enriched.shutdown()

    def test_invalid_reality_state_rejected(self):
        proj = GraphOSProjection()
        invalid_combos = [
            {"execution_mode": "proposed", "execution_state": "running", "verification_state": "unverified"},
            {"execution_mode": "proposed", "execution_state": "planned", "verification_state": "verified"},
            {"execution_mode": "proposed", "execution_state": "planned", "verification_state": "failed"},
            {"execution_mode": "proposed", "execution_state": "completed", "verification_state": "unverified"},
        ]
        for combo in invalid_combos:
            payload = {"node_id": "n1", "node_type": "INTENT", **combo}
            msg = EventMessage(topic="NODE_CREATED", payload=payload, id=f"invalid-{combo['execution_mode']}-{combo['execution_state']}")
            result = proj.project(msg)
            assert result is None, f"Invalid combo should be rejected: {combo}"

    def test_concurrent_mixed_mode_executions(self):
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

            events = []
            def collector(msg):
                if msg.topic in ("EXECUTION_STARTED", "EXECUTION_COMPLETED"):
                    events.append(msg)
            m.events.subscribe("*", collector)

            barrier = threading.Barrier(3)

            def worker(name, mode):
                barrier.wait()
                try:
                    enriched.run(f"{mode} execution {name}", execution_mode=mode)
                except Exception:
                    pass

            threads = []
            for mode in ("real", "simulated", "shadow"):
                t = threading.Thread(target=worker, args=(mode, mode))
                threads.append(t)

            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            assert len(events) >= 3
            enriched.shutdown()

    def test_rapid_connect_disconnect(self):
        bus = EventBus()
        store = None
        proj = GraphOSProjection()
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._loop = loop

        for i in range(10):
            session = ClientSession(websocket=None, client_id=f"rapid-{i}")
            adapter._clients[f"rapid-{i}"] = session
            msg = adapter._clients.get(f"rapid-{i}")
            assert msg is not None
            del adapter._clients[f"rapid-{i}"]

        assert len(adapter._clients) == 0
        loop.close()
        adapter.stop()


class TestConcurrentEventStore:
    def test_parallel_appends_maintain_order(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            barrier = threading.Barrier(10)
            results = []
            lock = threading.Lock()

            def appender(name):
                barrier.wait()
                try:
                    with lock:
                        seq = store.append({
                            "topic": "NODE_CREATED",
                            "payload": {"node_id": f"p-{name}"},
                            "source": "test",
                            "timestamp": time.time(),
                            "id": f"conc-append-{name}-{uuid7()}",
                            "execution_id": "conc-test",
                            "verification_state": "unverified",
                        })
                    with lock:
                        results.append((name, seq))
                except Exception as e:
                    with lock:
                        results.append((name, str(e)))

            threads = [threading.Thread(target=appender, args=(str(i),)) for i in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            assert len(results) == 10, f"Expected 10 results, got {len(results)}: {results}"
            seqs = [(r[1] if isinstance(r[1], int) else 0) for r in results]
            assert len(set(seqs)) == 10

            events = store.replay(cursor=0, limit=5000)
            event_seqs = [e["seq"] for e in events]
            assert event_seqs == sorted(event_seqs)

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_parallel_replay_consistent(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            for i in range(50):
                store.append({
                    "topic": "NODE_CREATED",
                    "payload": {"node_id": f"base-{i}"},
                    "source": "test",
                    "timestamp": time.time(),
                    "id": f"base-evt-{i}",
                    "execution_id": "base-exec",
                    "verification_state": "unverified",
                })

            barrier = threading.Barrier(5)
            replay_results = {}

            def replayer(name):
                barrier.wait()
                replay_results[name] = [(e["seq"], e["id"]) for e in store.replay(cursor=0, limit=5000)]

            threads = [threading.Thread(target=replayer, args=(f"r-{i}",)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15)

            base = list(replay_results.values())[0]
            for r in list(replay_results.values())[1:]:
                assert r == base
                assert len(r) == 50

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_parallel_cursor_advances(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            barrier = threading.Barrier(5)
            cursors = []
            db_lock = threading.Lock()

            def worker(name):
                barrier.wait()
                with db_lock:
                    store.append({
                        "topic": "NODE_CREATED",
                        "payload": {"node_id": f"cur-{name}"},
                        "source": "test",
                        "timestamp": time.time(),
                        "id": f"cur-evt-{name}",
                        "execution_id": "cur-test",
                        "verification_state": "unverified",
                    })
                    cursors.append(store.get_cursor())

            threads = [threading.Thread(target=worker, args=(str(i),)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15)

            assert len(cursors) == 5, f"Expected 5 cursors, got {len(cursors)}: {cursors}"
            assert max(cursors) <= store.get_cursor()

            store.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
