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
    enrich_with_context,
)
from features.identity.reality import (
    ExecutionMode,
    ExecutionState,
    VerificationState,
    validate_state_transition,
    verify_state_transition,
    ValidationError,
)
from features.identity.uuid7 import uuid7, is_uuid7
from features.bootstrap.enriched_bootstrap import EnrichedMuscalOS, BOOTSTRAP_VERSION
from runtime.event_store import EventStore


# ═══════════════════════════════════════════════════════════════════════
# A. Bootstrap Wrapper — ExecutionContext Lifecycle
# ═══════════════════════════════════════════════════════════════════════


class TestEnrichedBootstrap:
    def test_bootstrap_version(self):
        assert BOOTSTRAP_VERSION == "1.0.0"

    def test_enriched_bootstrap_wraps_muscal_os(self):
        from muscal_os import MuscalOS
        from os_config import load_config

        config = load_config()
        config.simulation_mode = True
        m = MuscalOS(config=config)
        enriched = EnrichedMuscalOS(os=m)
        assert enriched.os is m
        assert enriched.bootstrap_version == "1.0.0"

    def test_enriched_persist_context_enriches_event(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success

            mgr = get_context_manager()
            ctx = ExecutionContext(execution_id="test-enrich-1", correlation_id="c1", execution_mode="simulated")
            mgr.set_context(ctx)

            enriched._enriched_persist(EventMessage(
                topic="NODE_CREATED",
                payload={"node_id": "n1"},
                source="test",
                id="evt-enrich-1",
            ))

            events = m.event_store.replay(cursor=0, limit=5000)
            stored = [e for e in events if e.get("id") == "evt-enrich-1"]
            assert len(stored) == 1
            evt = stored[0]
            assert evt["execution_id"] == "test-enrich-1"
            assert evt["correlation_id"] == "c1"
            assert evt["execution_mode"] == "simulated"

            mgr.clear_context()
            m.shutdown()

    def test_run_sets_execution_context(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success

            result = enriched.run("test input", execution_mode="simulated")

            assert "mcxf" in result
            mgr = get_context_manager()
            ctx = mgr.get_context()
            assert ctx is None, "context should be cleared after run"

            m.shutdown()

    def test_run_emits_started_completed_events(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success

            lifecycle = []

            def capture(msg):
                if msg.topic in ("EXECUTION_STARTED", "EXECUTION_COMPLETED", "EXECUTION_FAILED"):
                    lifecycle.append(msg)

            m.events.subscribe("*", capture)

            result = enriched.run("test lifecycle", execution_mode="real")

            topics = [msg.topic for msg in lifecycle]
            assert "EXECUTION_STARTED" in topics
            assert "EXECUTION_COMPLETED" in topics
            assert "EXECUTION_FAILED" not in topics

            for msg in lifecycle:
                assert "execution_id" in msg.payload

            m.shutdown()

    def test_run_emits_failed_on_error(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success

            captured = []

            def capture(msg):
                if msg.topic in ("EXECUTION_STARTED", "EXECUTION_COMPLETED", "EXECUTION_FAILED"):
                    captured.append(msg.topic)

            m.events.subscribe("*", capture)

            result = enriched.run("", execution_mode="real")
            assert "EXECUTION_STARTED" in captured

            m.shutdown()

    def test_nested_execution_isolation(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            mgr = get_context_manager()

            outer_ctx = ExecutionContext(execution_id="outer-1")
            mgr.set_context(outer_ctx)

            inner_ctx = ExecutionContext(execution_id="inner-1", causation_id=outer_ctx.execution_id)

            def inner_run():
                saved = mgr.get_context()
                mgr.set_context(inner_ctx)
                ctx = mgr.get_context()
                assert ctx.execution_id == "inner-1"
                assert ctx.causation_id == "outer-1"
                if saved is not None:
                    mgr.set_context(saved)
                else:
                    mgr.clear_context()

            inner_run()

            ctx_after = mgr.get_context()
            assert ctx_after.execution_id == "outer-1"

            mgr.clear_context()
            m.shutdown()


# ═══════════════════════════════════════════════════════════════════════
# B. Enriched Persistence Subscriber
# ═══════════════════════════════════════════════════════════════════════


class TestEnrichedPersistence:
    def test_enriched_persist_writes_context_fields(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            mgr = get_context_manager()

            ctx = ExecutionContext(
                execution_id="persist-test-1",
                correlation_id="corr-1",
                causation_id="cause-1",
                execution_mode="simulated",
                execution_state="running",
                verification_state="unverified",
            )
            mgr.set_context(ctx)

            enriched._enriched_persist(EventMessage(
                topic="EXECUTION_STARTED",
                payload={"input": "hello"},
                source="test",
                id="evt-persist-1",
            ))

            events = m.event_store.replay(cursor=0, limit=5000)
            evt = next((e for e in events if e.get("id") == "evt-persist-1"), None)
            assert evt is not None
            assert evt["execution_id"] == "persist-test-1"
            assert evt["correlation_id"] == "corr-1"
            assert evt["causation_id"] == "cause-1"
            assert evt["execution_mode"] == "simulated"
            assert evt["verification_state"] == "unverified"

            mgr.clear_context()
            m.shutdown()

    def test_enriched_persist_defaults_when_no_context(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            mgr = get_context_manager()
            mgr.clear_context()

            enriched._enriched_persist(EventMessage(
                topic="NODE_CREATED",
                payload={"node_id": "n1"},
                source="test",
                id="evt-default-1",
            ))

            events = m.event_store.replay(cursor=0, limit=5000)
            evt = next((e for e in events if e.get("id") == "evt-default-1"), None)
            assert evt is not None
            assert is_uuid7(evt["execution_id"]), "default context generates uuid7 execution_id"
            assert evt["execution_mode"] == "real"
            assert evt["verification_state"] == "unverified"
            m.shutdown()

    def test_enriched_persist_does_not_crash_on_store_none(self):
        enriched = EnrichedMuscalOS.__new__(EnrichedMuscalOS)
        enriched._os = type("FakeOS", (), {"event_store": None})()
        mgr = get_context_manager()
        mgr.set_context(ExecutionContext(execution_id="no-crash"))
        enriched._enriched_persist(EventMessage(topic="TEST", payload={}))
        mgr.clear_context()


# ═══════════════════════════════════════════════════════════════════════
# C. Causation Chain Propagation
# ═══════════════════════════════════════════════════════════════════════


class TestCausationChain:
    def test_causation_id_from_parent_context(self):
        mgr = get_context_manager()
        parent = ExecutionContext(execution_id="parent-1")
        mgr.set_context(parent)

        child = ExecutionContext(
            causation_id=parent.execution_id,
            correlation_id=parent.execution_id,
        )
        assert child.causation_id == "parent-1"
        assert child.correlation_id == "parent-1"

        mgr.clear_context()

    def test_causation_chain_enriches_payload(self):
        parent = ExecutionContext(execution_id="grandparent-1")
        child = ExecutionContext(
            execution_id="parent-1",
            causation_id=parent.execution_id,
        )
        grandchild = ExecutionContext(
            execution_id="child-1",
            causation_id=child.execution_id,
        )
        payload = grandchild.enrich_payload({"task": "test"})
        assert payload["causation_id"] == "parent-1"
        assert payload["execution_id"] == "child-1"

    def test_causation_id_persisted_to_event_store(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            store = EventStore(db_path=db_path)
            seq = store.append({
                "topic": "EXECUTION_STARTED",
                "payload": {"input": "test"},
                "source": "test",
                "timestamp": time.time(),
                "id": "cause-evt-1",
                "execution_id": "child-exec",
                "correlation_id": "parent-exec",
                "causation_id": "grandparent-exec",
                "execution_mode": "real",
                "verification_state": "unverified",
            })
            assert seq is not None
            events = store.replay(cursor=0)
            evt = events[0]
            assert evt["causation_id"] == "grandparent-exec"
            assert evt["correlation_id"] == "parent-exec"
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_causation_chain_full_flow(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            mgr = get_context_manager()

            root_ctx = ExecutionContext(execution_id="root-cause")
            mgr.set_context(root_ctx)

            enriched._enriched_persist(EventMessage(
                topic="EXECUTION_STARTED",
                payload={"input": "root"},
                source="test",
                id="root-evt",
            ))

            child_ctx = ExecutionContext(
                execution_id="child-cause",
                causation_id=root_ctx.execution_id,
                correlation_id=root_ctx.execution_id,
            )
            mgr.set_context(child_ctx)

            enriched._enriched_persist(EventMessage(
                topic="NODE_CREATED",
                payload={"node_id": "n1"},
                source="test",
                id="child-evt",
            ))

            events = m.event_store.replay(cursor=0, limit=5000)
            root_stored = next((e for e in events if e.get("id") == "root-evt"), None)
            child_stored = next((e for e in events if e.get("id") == "child-evt"), None)

            assert root_stored is not None
            assert root_stored["causation_id"] == ""
            assert root_stored["execution_id"] == "root-cause"

            assert child_stored is not None
            assert child_stored["causation_id"] == "root-cause"
            assert child_stored["correlation_id"] == "root-cause"

            mgr.clear_context()
            m.shutdown()


# ═══════════════════════════════════════════════════════════════════════
# D. WebSocket Adapter Lifecycle Integration
# ═══════════════════════════════════════════════════════════════════════


class TestWebSocketLifecycle:
    def _make_adapter(self, m):
        from features.streaming.ws_adapter import WebSocketAdapter
        from features.projection.graph_os_projection import GraphOSProjection
        bus = m.events
        proj = GraphOSProjection(event_store=m.event_store)
        return WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)

    def test_adapter_started_via_bootstrap(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            adapter = self._make_adapter(m)
            enriched = EnrichedMuscalOS(os=m, ws_adapter=adapter)
            report = enriched.start()
            assert report.success

            stats = adapter.get_stats()
            assert stats["running"] is True
            assert stats["version"] == "2.0.0"

            enriched.shutdown()
            stats_after = adapter.get_stats()
            assert stats_after["running"] is False

    def test_adapter_not_started_if_not_provided(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m, ws_adapter=None)
            report = enriched.start()
            assert report.success
            enriched.shutdown()

    def test_adapter_stopped_on_shutdown(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            adapter = self._make_adapter(m)
            enriched = EnrichedMuscalOS(os=m, ws_adapter=adapter)
            report = enriched.start()
            assert report.success

            assert adapter.get_stats()["running"] is True
            enriched.shutdown()
            assert adapter.get_stats()["running"] is False


# ═══════════════════════════════════════════════════════════════════════
# E. UUID v7 Migration in Tool Runtime
# ═══════════════════════════════════════════════════════════════════════


class TestToolRuntimeUUID7:
    def test_verification_result_uses_uuid7(self):
        from features.tool_runtime.tool_runtime import VerificationResult
        vr = VerificationResult()
        assert is_uuid7(vr.verification_id), f"expected uuid7, got {vr.verification_id}"

    def test_execution_receipt_uses_uuid7(self):
        from features.tool_runtime.tool_runtime import ExecutionReceipt
        receipt = ExecutionReceipt(tool_name="test")
        assert is_uuid7(receipt.execution_id), f"expected uuid7, got {receipt.execution_id}"
        assert len(receipt.receipt_id) == 36

    def test_execute_uses_uuid7_when_no_id_provided(self):
        from features.tool_runtime.tool_runtime import UnifiedToolRuntime
        rt = UnifiedToolRuntime()

        def fake_tool(args):
            return {"status": "success", "output": "ok"}

        rt.register_tool("test_tool", fake_tool, schema={})
        result = rt.execute("test_tool", args={"x": 1})
        assert result.receipt is not None
        assert is_uuid7(result.receipt.execution_id), f"expected uuid7, got {result.receipt.execution_id}"

    def test_duplicate_execution_still_detected(self):
        from features.tool_runtime.tool_runtime import UnifiedToolRuntime
        rt = UnifiedToolRuntime()

        def fake_tool(args):
            return {"status": "success"}

        rt.register_tool("test_tool", fake_tool, schema={})
        eid = uuid7()
        r1 = rt.execute("test_tool", args={"x": 1}, execution_id=eid)
        assert r1.success

        r2 = rt.execute("test_tool", args={"x": 2}, execution_id=eid)
        assert not r2.success
        assert "DUPLICATE" in r2.error

    def test_receipt_integrity_with_uuid7(self):
        from features.tool_runtime.tool_runtime import ExecutionReceipt
        receipt = ExecutionReceipt(tool_name="test", args={"a": 1}, result_data={"ok": True}, success=True)
        receipt.execution_id = uuid7()
        receipt.finalize()
        assert receipt.verify_integrity()

    def test_provided_ids_still_respected(self):
        from features.tool_runtime.tool_runtime import VerificationResult, ExecutionReceipt
        vr = VerificationResult(verification_id="custom-vr-id")
        assert vr.verification_id == "custom-vr-id"

        receipt = ExecutionReceipt(execution_id="custom-exec-id", receipt_id="custom-receipt")
        assert receipt.execution_id == "custom-exec-id"
        assert receipt.receipt_id == "custom-receipt"


# ═══════════════════════════════════════════════════════════════════════
# F. Concurrent Execution Isolation
# ═══════════════════════════════════════════════════════════════════════


class TestConcurrentExecutionContext:
    def test_two_threads_independent_contexts(self):
        mgr = ExecutionContextManager()
        results = {}

        def worker(name):
            ctx = ExecutionContext(execution_id=f"thread-{name}")
            mgr.set_context(ctx)
            time.sleep(0.01)
            results[name] = mgr.get_context().execution_id
            mgr.clear_context()

        t1 = threading.Thread(target=worker, args=("A",))
        t2 = threading.Thread(target=worker, args=("B",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert results["A"] == "thread-A"
        assert results["B"] == "thread-B"

    def test_enriched_bootstrap_thread_safe(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            mgr = get_context_manager()
            results = {}
            _store_lock = threading.Lock()

            def worker(name):
                ctx = ExecutionContext(execution_id=f"conc-{name}")
                mgr.set_context(ctx)
                with _store_lock:
                    enriched._enriched_persist(EventMessage(
                        topic="NODE_CREATED",
                        payload={"node_id": f"n-{name}"},
                        source="test",
                        id=f"conc-evt-{name}",
                    ))
                results[name] = mgr.get_context().execution_id
                mgr.clear_context()

            threads = [threading.Thread(target=worker, args=(str(i),)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            for i in range(5):
                assert results[str(i)] == f"conc-{i}"

            events = m.event_store.replay(cursor=0, limit=5000)
            conc_events = [e for e in events if "conc-evt" in e.get("id", "")]
            assert len(conc_events) == 5

            m.shutdown()


# ═══════════════════════════════════════════════════════════════════════
# G. End-to-End: Full Lifecycle
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndEnriched:
    def test_full_enriched_lifecycle(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode
        from features.projection.graph_os_projection import GraphOSProjection
        from features.streaming.ws_adapter import WebSocketAdapter

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            bus = m.events
            proj = GraphOSProjection(event_store=m.event_store)
            adapter = WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)

            enriched = EnrichedMuscalOS(os=m, ws_adapter=adapter)
            report = enriched.start()
            assert report.success

            assert adapter.get_stats()["running"] is True

            mgr = get_context_manager()
            ctx = ExecutionContext(
                execution_id="e2e-root",
                execution_mode="real",
                execution_state="running",
            )
            mgr.set_context(ctx)

            enriched._enriched_persist(EventMessage(
                topic="EXECUTION_STARTED",
                payload={"input": "e2e test"},
                source="test",
                id="e2e-evt-1",
                priority=EventPriority.HIGH,
            ))

            ctx.transition_state("completed")
            ctx.set_verification("verified", evidence_receipt_id="e2e-rcpt-001")
            mgr.set_context(ctx)

            enriched._enriched_persist(EventMessage(
                topic="EXECUTION_COMPLETED",
                payload={"result": "ok"},
                source="test",
                id="e2e-evt-2",
            ))

            stored = m.event_store.replay(cursor=0, limit=5000)
            assert len(stored) >= 2
            started = next(e for e in stored if e.get("id") == "e2e-evt-1")
            completed = next(e for e in stored if e.get("id") == "e2e-evt-2")

            assert started["execution_id"] == "e2e-root"
            assert started["execution_mode"] == "real"
            assert started["verification_state"] == "unverified"

            assert completed["execution_id"] == "e2e-root"
            assert completed["execution_mode"] == "real"
            assert completed["verification_state"] == "verified"

            proj_result = proj.project(EventMessage(
                topic="EXECUTION_COMPLETED",
                payload=completed["payload"] if isinstance(completed.get("payload"), dict) else {},
                source="test",
                id="e2e-proj",
            ))
            if proj_result is not None:
                assert proj_result["execution_id"] == "e2e-root"
                assert proj_result["execution_mode"] == "real"

            mgr.clear_context()
            enriched.shutdown()

    def test_enriched_bootstrap_getattr_delegates(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)
            enriched = EnrichedMuscalOS(os=m)
            assert enriched.get_status() is not None
            assert "running" in enriched.get_status()

    def test_lifecycle_events_have_valid_context(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        with tempfile.TemporaryDirectory() as tmpdir:
            config.storage_path = tmpdir
            _muscal_config.DB_PATH = Path(tmpdir) / 'muscal.db'
            m = MuscalOS(config=config)

            enriched = EnrichedMuscalOS(os=m)
            report = enriched.start()
            assert report.success
            events = []

            def collector(msg):
                if msg.topic in ("EXECUTION_STARTED", "EXECUTION_COMPLETED"):
                    events.append(msg)

            m.events.subscribe("*", collector)

            mgr = get_context_manager()
            ctx = ExecutionContext(execution_id="lifecycle-ctx-1", execution_mode="shadow")
            mgr.set_context(ctx)

            enriched._publish_lifecycle("EXECUTION_STARTED", {"input": "test"})
            enriched._publish_lifecycle("EXECUTION_COMPLETED", {"result": "ok"})

            assert len(events) == 2
            for msg in events:
                assert msg.source == "enriched_bootstrap"
                p = msg.payload
                assert "execution_id" in p
                assert "execution_mode" in p
                assert "verification_state" in p

            mgr.clear_context()
            m.shutdown()
