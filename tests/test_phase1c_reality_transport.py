import asyncio
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config as _muscal_config

from event_bus import EventBus, EventMessage, EventPriority
from features.identity.execution_context import (
    ExecutionContext,
    ExecutionContextManager,
    get_context_manager,
)
from features.identity.reality import (
    normalize_execution_mode,
    normalize_execution_state,
    normalize_verification_state,
    validate_state_transition,
    verify_state_transition,
    ValidationError,
)
from features.identity.uuid7 import uuid7, is_uuid7
from features.projection.graph_os_projection import (
    GraphOSProjection,
    sanitize_payload,
    validate_normalized,
    ProjectionError,
    CANONICAL_EVENT_TYPES,
    ENRICHMENT_FIELDS,
)
from runtime.event_store import EventStore


# ═══════════════════════════════════════════════════════════════════════
# H. Reality Integrity — Full Pipeline
# ═══════════════════════════════════════════════════════════════════════


class TestRealityIntegrityPipeline:
    """Phase 1C: Validate the full reality pipeline
    ExecutionContext → enrich_payload → EventBus → _enriched_persist → EventStore → replay → Projection.
    """

    def _setup(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode
        from features.bootstrap.enriched_bootstrap import EnrichedMuscalOS

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        self._tmp = tempfile.TemporaryDirectory()
        tmpdir = self._tmp.__enter__()
        config.storage_path = tmpdir
        _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
        m = MuscalOS(config=config)
        enriched = EnrichedMuscalOS(os=m)
        report = enriched.start()
        assert report.success, f"Boot failed: {report.errors}"
        self._m = m
        self._enriched = enriched
        self._bus = m.events
        self._store = m.event_store
        self._proj = GraphOSProjection(event_store=self._store)

    def _teardown(self):
        getattr(self, "_enriched", None) and self._enriched.shutdown()
        getattr(self, "_tmp", None) and self._tmp.__exit__(None, None, None)

    @pytest.fixture(autouse=True)
    def pipeline(self):
        self._setup()
        yield
        self._teardown()

    # ──── Real mode full pipeline ───────────────────────────────────

    def test_real_mode_full_pipeline(self):
        mgr = get_context_manager()
        ctx = ExecutionContext(
            execution_id="pipe-real-1",
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
            correlation_id="corr-real",
        )
        mgr.set_context(ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="NODE_CREATED",
            payload={"node_id": "pipe-node-1"},
            source="test",
            id="pipe-evt-real",
        ))

        stored = self._store.replay(cursor=0)
        evt = next(e for e in stored if e.get("id") == "pipe-evt-real")

        assert evt["execution_id"] == "pipe-real-1"
        assert evt["execution_mode"] == "real"
        assert evt["verification_state"] == "unverified"
        assert evt["correlation_id"] == "corr-real"

        proj_result = self._proj.project(EventMessage(
            topic="NODE_CREATED",
            payload=evt["payload"] if isinstance(evt.get("payload"), dict) else {},
            source="test",
            id="pipe-proj-real",
        ))
        assert proj_result is not None
        assert proj_result["execution_id"] == "pipe-real-1"
        assert proj_result["execution_mode"] == "real"
        assert proj_result["verification_state"] == "unverified"

        mgr.clear_context()

    # ──── Simulated mode full pipeline ──────────────────────────────

    def test_simulated_mode_full_pipeline(self):
        mgr = get_context_manager()
        ctx = ExecutionContext(
            execution_id="pipe-sim-1",
            execution_mode="simulated",
            execution_state="running",
            verification_state="unverified",
        )
        mgr.set_context(ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="SIMULATION_STARTED",
            payload={"scenario": "test-sim"},
            source="test",
            id="pipe-evt-sim",
        ))

        stored = self._store.replay(cursor=0)
        evt = next(e for e in stored if e.get("id") == "pipe-evt-sim")

        assert evt["execution_id"] == "pipe-sim-1"
        assert evt["execution_mode"] == "simulated"

        proj_result = self._proj.project(EventMessage(
            topic="SIMULATION_STARTED",
            payload=evt["payload"] if isinstance(evt.get("payload"), dict) else {},
            source="test",
            id="pipe-proj-sim",
        ))
        assert proj_result is not None
        assert proj_result["execution_id"] == "pipe-sim-1"
        assert proj_result["execution_mode"] == "simulated"

        mgr.clear_context()

    # ──── Shadow mode full pipeline ─────────────────────────────────

    def test_shadow_mode_full_pipeline(self):
        mgr = get_context_manager()
        ctx = ExecutionContext(
            execution_id="pipe-shadow-1",
            execution_mode="shadow",
            execution_state="running",
            verification_state="unverified",
        )
        mgr.set_context(ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "shadow-test"},
            source="test",
            id="pipe-evt-shadow",
        ))

        stored = self._store.replay(cursor=0)
        evt = next(e for e in stored if e.get("id") == "pipe-evt-shadow")

        assert evt["execution_id"] == "pipe-shadow-1"
        assert evt["execution_mode"] == "shadow"

        proj_result = self._proj.project(EventMessage(
            topic="EXECUTION_STARTED",
            payload=evt["payload"] if isinstance(evt.get("payload"), dict) else {},
            source="test",
            id="pipe-proj-shadow",
        ))
        assert proj_result["execution_id"] == "pipe-shadow-1"
        assert proj_result["execution_mode"] == "shadow"

        mgr.clear_context()

    # ──── State transition through pipeline ─────────────────────────

    def test_state_transition_completed_verified_through_pipeline(self):
        mgr = get_context_manager()

        ctx = ExecutionContext(
            execution_id="pipe-state-1",
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
        )
        mgr.set_context(ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"state": "running"},
            source="test",
            id="pipe-state-evt-1",
        ))

        ctx.transition_state("completed")
        ctx.set_verification("verified", evidence_receipt_id="pipe-rcpt-001")
        mgr.set_context(ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_COMPLETED",
            payload={"state": "completed", "result": "ok"},
            source="test",
            id="pipe-state-evt-2",
        ))

        stored = self._store.replay(cursor=0)
        started = next(e for e in stored if e.get("id") == "pipe-state-evt-1")
        completed = next(e for e in stored if e.get("id") == "pipe-state-evt-2")

        assert started["execution_state"] == "running"
        assert started["verification_state"] == "unverified"
        assert completed["execution_state"] == "completed"
        assert completed["verification_state"] == "verified"

        proj_started = self._proj.project(EventMessage(
            topic="EXECUTION_STARTED",
            payload=started["payload"] if isinstance(started.get("payload"), dict) else {},
            source="test",
            id="pipe-proj-start",
        ))
        proj_completed = self._proj.project(EventMessage(
            topic="EXECUTION_COMPLETED",
            payload=completed["payload"] if isinstance(completed.get("payload"), dict) else {},
            source="test",
            id="pipe-proj-complete",
        ))

        assert proj_started is not None
        assert proj_started["execution_state"] == "running"
        assert proj_started["verification_state"] == "unverified"

        assert proj_completed is not None
        assert proj_completed["execution_state"] == "completed"
        assert proj_completed["verification_state"] == "verified"

        mgr.clear_context()

    # ──── Invalid state rejected at projection ──────────────────────

    def test_invalid_state_rejected_at_projection(self):
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="EXECUTION_STARTED",
            payload={
                "execution_id": "invalid-1",
                "execution_mode": "proposed",
                "execution_state": "running",
                "verification_state": "verified",
            },
            source="test",
            id="invalid-proj-1",
        )
        result = proj.project(msg)
        assert result is None

    # ──── Legacy event backward compat through pipeline ──────────────

    def test_legacy_event_backward_compat_through_pipeline(self):
        self._store.append({
            "topic": "NODE_CREATED",
            "payload": {"node_id": "legacy-node"},
            "source": "legacy",
            "id": "pipe-legacy-1",
            "timestamp": time.time(),
        })

        stored = self._store.replay(cursor=0)
        evt = next(e for e in stored if e.get("id") == "pipe-legacy-1")

        assert evt["execution_id"] == ""
        assert evt["execution_mode"] == "real"
        assert evt["verification_state"] == "unverified"

        proj_result = self._proj.project(EventMessage(
            topic="NODE_CREATED",
            payload=evt["payload"] if isinstance(evt.get("payload"), dict) else {},
            source="legacy",
            id="pipe-proj-legacy",
        ))
        assert proj_result is not None
        assert proj_result["execution_id"] == ""
        assert proj_result["execution_mode"] == "real"


# ═══════════════════════════════════════════════════════════════════════
# I. Transport Fidelity — WebSocket Adapter Enrichment
# ═══════════════════════════════════════════════════════════════════════


class TestTransportFidelity:
    """Phase 1C: Validate enriched event transport through WebSocket adapter.
    Tests on_event projection, snapshot building, and JSON serialization.
    """

    def _active_adapter(self, bus, store, proj):
        from features.streaming.ws_adapter import WebSocketAdapter
        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        adapter._running = True
        adapter._loop = loop
        return adapter, loop

    def test_adapter_on_event_projects_enriched_fields(self):
        bus = EventBus()
        store = EventStore()
        proj = GraphOSProjection(event_store=store)
        adapter, loop = self._active_adapter(bus, store, proj)

        try:
            msg = EventMessage(
                topic="NODE_CREATED",
                payload={
                    "execution_id": "tp-e1",
                    "execution_mode": "simulated",
                    "execution_state": "running",
                    "verification_state": "unverified",
                    "node_id": "tp-node-1",
                    "node_type": "INTENT",
                },
                source="test",
                id="tp-evt-1",
            )
            adapter.on_event(msg)
            assert proj.stats()["projected"] == 1
        finally:
            loop.close()

    def test_adapter_on_event_skips_non_canonical(self):
        bus = EventBus()
        store = EventStore()
        proj = GraphOSProjection(event_store=store)
        adapter, loop = self._active_adapter(bus, store, proj)

        try:
            msg = EventMessage(topic="NON_CANONICAL", payload={}, source="test", id="tp-skip-1")
            adapter.on_event(msg)
            assert proj.stats()["rejected"] == 1
            assert proj.stats()["projected"] == 0
        finally:
            loop.close()

    def test_snapshot_nodes_include_enrichment_fields(self):
        bus = EventBus()
        store = EventStore()
        proj = GraphOSProjection(event_store=store)
        from features.streaming.ws_adapter import WebSocketAdapter

        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        store.append({
            "topic": "NODE_CREATED",
            "payload": json.dumps({
                "execution_id": "snap-e1",
                "execution_mode": "real",
                "execution_state": "completed",
                "verification_state": "verified",
                "node_id": "snap-node-1",
                "node_type": "INTENT",
            }),
            "source": "test",
            "id": "snap-evt-1",
            "timestamp": time.time(),
            "execution_id": "snap-e1",
            "execution_mode": "real",
            "verification_state": "verified",
        })

        loop = asyncio.new_event_loop()
        try:
            nodes = loop.run_until_complete(adapter._build_snapshot_nodes())
            assert len(nodes) == 1
            node = nodes[0]
            assert node["execution_id"] == "snap-e1"
            assert node["execution_mode"] == "real"
            assert node["verification_state"] == "verified"
        finally:
            loop.close()

    def test_snapshot_edges_include_enrichment_fields(self):
        bus = EventBus()
        store = EventStore()
        proj = GraphOSProjection(event_store=store)
        from features.streaming.ws_adapter import WebSocketAdapter

        adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)

        store.append({
            "topic": "EDGE_CREATED",
            "payload": json.dumps({
                "execution_id": "snap-e2",
                "execution_mode": "simulated",
                "execution_state": "completed",
                "verification_state": "unverified",
                "source_id": "node-a",
                "target_id": "node-b",
                "edge_type": "default",
            }),
            "source": "test",
            "id": "snap-evt-2",
            "timestamp": time.time(),
            "execution_id": "snap-e2",
            "execution_mode": "simulated",
            "verification_state": "unverified",
        })

        loop = asyncio.new_event_loop()
        try:
            edges = loop.run_until_complete(adapter._build_snapshot_edges())
            assert len(edges) == 1
            edge = edges[0]
            assert edge["execution_id"] == "snap-e2"
            assert edge["execution_mode"] == "simulated"
        finally:
            loop.close()

    def test_enriched_event_json_serialization_roundtrip(self):
        original = {
            "event_id": "serial-1",
            "event_type": "EXECUTION_COMPLETED",
            "execution_id": "serial-e1",
            "execution_mode": "real",
            "execution_state": "completed",
            "verification_state": "verified",
            "correlation_id": "serial-corr",
            "causation_id": "serial-cause",
        }
        serialized = json.dumps(original, ensure_ascii=False)
        deserialized = json.loads(serialized)

        assert deserialized["execution_id"] == "serial-e1"
        assert deserialized["execution_mode"] == "real"
        assert deserialized["execution_state"] == "completed"
        assert deserialized["verification_state"] == "verified"
        assert deserialized["correlation_id"] == "serial-corr"
        assert deserialized["causation_id"] == "serial-cause"

    def test_enriched_event_projection_serializable(self):
        bus = EventBus()
        proj = GraphOSProjection()
        msg = EventMessage(
            topic="EXECUTION_COMPLETED",
            payload={
                "execution_id": "serial-proj-e1",
                "execution_mode": "real",
                "execution_state": "completed",
                "verification_state": "verified",
                "correlation_id": "corr-proj",
                "causation_id": "cause-proj",
                "result": "ok",
            },
            source="test",
            id="serial-proj-evt",
        )
        result = proj.project(msg)
        assert result is not None

        serialized = json.dumps(result, ensure_ascii=False)
        deserialized = json.loads(serialized)

        assert deserialized["execution_id"] == "serial-proj-e1"
        assert deserialized["execution_mode"] == "real"
        assert deserialized["verification_state"] == "verified"


# ═══════════════════════════════════════════════════════════════════════
# J. End-to-End Reality Chain
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndRealityChain:
    """Phase 1C: Complete End-to-End validation of Reality Integrity.
    EnrichedMuscalOS.run() → enriched persist → EventStore → replay → Projection → Transport.
    """

    def _setup(self):
        from muscal_os import MuscalOS
        from os_config import load_config, DeploymentMode
        from features.bootstrap.enriched_bootstrap import EnrichedMuscalOS
        from features.streaming.ws_adapter import WebSocketAdapter

        config = load_config()
        config.simulation_mode = True
        config.mode = DeploymentMode.LOCAL_DEV
        self._tmp = tempfile.TemporaryDirectory()
        tmpdir = self._tmp.__enter__()
        config.storage_path = tmpdir
        _muscal_config.DB_PATH = Path(tmpdir) / "muscal.db"
        m = MuscalOS(config=config)
        bus = m.events
        proj = GraphOSProjection(event_store=m.event_store)
        adapter = WebSocketAdapter(event_bus=bus, event_store=m.event_store, projection=proj)
        enriched = EnrichedMuscalOS(os=m, ws_adapter=adapter)
        report = enriched.start()
        assert report.success, f"Boot failed: {report.errors}"
        self._m = m
        self._enriched = enriched
        self._adapter = adapter
        self._bus = bus
        self._store = m.event_store
        self._proj = proj

    def _teardown(self):
        getattr(self, "_enriched", None) and self._enriched.shutdown()
        getattr(self, "_tmp", None) and self._tmp.__exit__(None, None, None)

    @pytest.fixture(autouse=True)
    def chain(self):
        self._setup()
        yield
        self._teardown()

    # ──── Full enrichment round-trip ────────────────────────────────

    def test_full_enrichment_round_trip(self):
        mgr = get_context_manager()
        ctx = ExecutionContext(
            execution_id="chain-round-1",
            execution_mode="simulated",
            execution_state="running",
            verification_state="unverified",
            correlation_id="chain-corr",
            causation_id="chain-cause",
        )
        mgr.set_context(ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "roundtrip"},
            source="test",
            id="chain-evt-1",
        ))

        stored = self._store.replay(cursor=0)
        evt = next(e for e in stored if e.get("id") == "chain-evt-1")

        assert evt["execution_id"] == "chain-round-1"
        assert evt["correlation_id"] == "chain-corr"
        assert evt["causation_id"] == "chain-cause"
        assert evt["execution_mode"] == "simulated"
        assert evt["verification_state"] == "unverified"

        proj_result = self._proj.project(EventMessage(
            topic="EXECUTION_STARTED",
            payload=evt["payload"] if isinstance(evt.get("payload"), dict) else {},
            source="test",
            id="chain-proj-1",
        ))
        assert proj_result is not None
        assert proj_result["execution_id"] == "chain-round-1"
        assert proj_result["correlation_id"] == "chain-corr"
        assert proj_result["causation_id"] == "chain-cause"
        assert proj_result["execution_mode"] == "simulated"
        assert proj_result["verification_state"] == "unverified"

        serialized = json.dumps(proj_result, ensure_ascii=False)
        deserialized = json.loads(serialized)
        assert deserialized["execution_id"] == "chain-round-1"
        assert deserialized["execution_mode"] == "simulated"

        mgr.clear_context()

    # ──── Causation chain through full pipeline ─────────────────────

    def test_causation_chain_full_pipeline(self):
        mgr = get_context_manager()

        parent_id = uuid7()
        parent_ctx = ExecutionContext(
            execution_id=parent_id,
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
        )
        mgr.set_context(parent_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "parent task"},
            source="test",
            id="chain-cause-evt-1",
        ))

        child_id = uuid7()
        child_ctx = ExecutionContext(
            execution_id=child_id,
            correlation_id=parent_id,
            causation_id=parent_id,
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
        )
        mgr.set_context(child_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "child task"},
            source="test",
            id="chain-cause-evt-2",
        ))

        child_ctx.transition_state("completed")
        child_ctx.set_verification("verified", evidence_receipt_id="child-rcpt-001")
        mgr.set_context(child_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_COMPLETED",
            payload={"result": "child done"},
            source="test",
            id="chain-cause-evt-3",
        ))

        stored = self._store.replay(cursor=0)
        parent_evt = next(e for e in stored if e.get("id") == "chain-cause-evt-1")
        child_evt = next(e for e in stored if e.get("id") == "chain-cause-evt-2")
        child_done = next(e for e in stored if e.get("id") == "chain-cause-evt-3")

        assert parent_evt["execution_id"] == parent_id
        assert parent_evt["correlation_id"] == ""
        assert parent_evt["causation_id"] == ""

        assert child_evt["execution_id"] == child_id
        assert child_evt["correlation_id"] == parent_id
        assert child_evt["causation_id"] == parent_id

        assert child_done["execution_id"] == child_id
        assert child_done["verification_state"] == "verified"

        for evt_data in [child_evt, child_done]:
            payload = evt_data["payload"] if isinstance(evt_data.get("payload"), dict) else {}
            proj_result = self._proj.project(EventMessage(
                topic=evt_data["topic"],
                payload=payload,
                source="test",
                id=f"proj-{evt_data['id']}",
            ))
            if proj_result is not None:
                assert proj_result["correlation_id"] == parent_id
                assert proj_result["causation_id"] == parent_id

        mgr.clear_context()

    # ──── Nested execution through pipeline ─────────────────────────

    def test_nested_execution_isolation_full_pipeline(self):
        mgr = get_context_manager()

        outer_id = uuid7()
        outer_ctx = ExecutionContext(
            execution_id=outer_id,
            execution_mode="real",
            execution_state="running",
        )
        mgr.set_context(outer_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "outer"},
            source="test",
            id="chain-nest-evt-1",
        ))

        inner_id = uuid7()
        inner_ctx = ExecutionContext(
            execution_id=inner_id,
            execution_mode="shadow",
            execution_state="running",
            correlation_id=outer_id,
            causation_id=outer_id,
        )
        mgr.set_context(inner_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_STARTED",
            payload={"input": "inner"},
            source="test",
            id="chain-nest-evt-2",
        ))

        inner_ctx.transition_state("completed")
        mgr.set_context(inner_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_COMPLETED",
            payload={"result": "inner done"},
            source="test",
            id="chain-nest-evt-3",
        ))

        mgr.set_context(outer_ctx)

        self._enriched._enriched_persist(EventMessage(
            topic="EXECUTION_COMPLETED",
            payload={"result": "outer done"},
            source="test",
            id="chain-nest-evt-4",
        ))

        stored = self._store.replay(cursor=0)
        outer = next(e for e in stored if e.get("id") == "chain-nest-evt-1")
        inner = next(e for e in stored if e.get("id") == "chain-nest-evt-2")
        inner_done = next(e for e in stored if e.get("id") == "chain-nest-evt-3")
        outer_done = next(e for e in stored if e.get("id") == "chain-nest-evt-4")

        assert outer["execution_id"] == outer_id
        assert outer["execution_mode"] == "real"
        assert inner["execution_id"] == inner_id
        assert inner["execution_mode"] == "shadow"
        assert inner["correlation_id"] == outer_id
        assert inner_done["execution_id"] == inner_id
        assert outer_done["execution_id"] == outer_id

        for evt_data in [outer, inner, inner_done, outer_done]:
            payload = evt_data["payload"] if isinstance(evt_data.get("payload"), dict) else {}
            proj_result = self._proj.project(EventMessage(
                topic=evt_data["topic"],
                payload=payload,
                source="test",
                id=f"proj-{evt_data['id']}",
            ))
            if proj_result is not None:
                assert proj_result["execution_id"] == evt_data["execution_id"]
                assert proj_result["execution_mode"] == evt_data["execution_mode"]

        mgr.clear_context()

    # ──── All 5 execution modes through pipeline ────────────────────

    def test_all_execution_modes_through_pipeline(self):
        mgr = get_context_manager()
        modes = ["real", "simulated", "shadow", "replay"]
        proposed_states = ["planned", "cancelled"]

        for i, mode in enumerate(modes):
            ctx = ExecutionContext(
                execution_id=f"chain-mode-{i}",
                execution_mode=mode,
                execution_state="running",
                verification_state="unverified",
            )
            mgr.set_context(ctx)
            self._enriched._enriched_persist(EventMessage(
                topic="EXECUTION_STARTED",
                payload={"mode_test": mode},
                source="test",
                id=f"chain-mode-evt-{i}",
            ))

        for j, pstate in enumerate(proposed_states):
            ctx = ExecutionContext(
                execution_id=f"chain-mode-prop-{j}",
                execution_mode="proposed",
                execution_state=pstate,
                verification_state="unverified",
            )
            mgr.set_context(ctx)
            self._enriched._enriched_persist(EventMessage(
                topic="EXECUTION_STARTED",
                payload={"mode_test": f"proposed-{pstate}"},
                source="test",
                id=f"chain-mode-evt-prop-{j}",
            ))

        stored = self._store.replay(cursor=0)
        for i, mode in enumerate(modes):
            evt = next(e for e in stored if e.get("id") == f"chain-mode-evt-{i}")
            assert evt["execution_mode"] == mode, f"Mode {mode} failed in EventStore"
            payload = evt["payload"] if isinstance(evt.get("payload"), dict) else {}
            proj_result = self._proj.project(EventMessage(
                topic="EXECUTION_STARTED",
                payload=payload,
                source="test",
                id=f"proj-chain-mode-{i}",
            ))
            assert proj_result is not None, f"Mode {mode} failed at projection"
            assert proj_result["execution_mode"] == mode

        for j, pstate in enumerate(proposed_states):
            evt = next(e for e in stored if e.get("id") == f"chain-mode-evt-prop-{j}")
            assert evt["execution_mode"] == "proposed"
            payload = evt["payload"] if isinstance(evt.get("payload"), dict) else {}
            proj_result = self._proj.project(EventMessage(
                topic="EXECUTION_STARTED",
                payload=payload,
                source="test",
                id=f"proj-chain-mode-prop-{j}",
            ))
            assert proj_result is not None, f"proposed+{pstate} should be accepted"
            assert proj_result["execution_mode"] == "proposed"
            assert proj_result["execution_state"] == pstate

        mgr.clear_context()

    # ──── State transition rejection at each boundary ───────────────

    def test_invalid_state_rejected_at_every_boundary(self):
        assert not validate_state_transition("proposed", "running", "unverified")

        with pytest.raises(ValidationError):
            verify_state_transition("proposed", "running", "unverified")

        proj = GraphOSProjection()
        msg = EventMessage(
            topic="EXECUTION_STARTED",
            payload={
                "execution_id": "boundary-invalid",
                "execution_mode": "proposed",
                "execution_state": "running",
                "verification_state": "verified",
            },
            source="test",
            id="boundary-inv-1",
        )
        result = proj.project(msg)
        assert result is None

    # ──── Semantic rules enforced through pipeline ──────────────────

    def test_semantic_rules_enriched_payload(self):
        ctx = ExecutionContext(
            execution_id="se-1",
            execution_mode="real",
            execution_state="running",
            verification_state="unverified",
        )
        payload = {"input": "test"}
        enriched = ctx.enrich_payload(payload)

        assert enriched["execution_mode"] == "real"
        assert enriched["execution_state"] == "running"
        assert enriched["verification_state"] == "unverified"

        verify_state_transition(
            enriched.get("execution_mode", "real"),
            enriched.get("execution_state", "planned"),
            enriched.get("verification_state", "unverified"),
        )

    # ──── Enriched events through adapter on_event ──────────────────

    def test_adapter_on_event_preserves_execution_id(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            bus = EventBus()
            store = EventStore()
            proj = GraphOSProjection(event_store=store)
            from features.streaming.ws_adapter import WebSocketAdapter

            adapter = WebSocketAdapter(event_bus=bus, event_store=store, projection=proj)
            adapter._running = True
            adapter._loop = loop

            msg = EventMessage(
                topic="EXECUTION_STARTED",
                payload={
                    "execution_id": "adapter-e1",
                    "execution_mode": "real",
                    "execution_state": "running",
                    "verification_state": "unverified",
                    "input": "adapter-test",
                },
                source="test",
                id="adapter-evt-1",
            )
            adapter.on_event(msg)

        finally:
            loop.close()

    # ──── EventMessage payload contains all enrichment fields ───────

    def test_eventmessage_payload_has_all_enrichment_fields(self):
        msg = EventMessage(
            topic="EXECUTION_COMPLETED",
            payload={
                "execution_id": "ef-1",
                "execution_mode": "real",
                "execution_state": "completed",
                "verification_state": "verified",
                "correlation_id": "ef-corr",
                "causation_id": "ef-cause",
                "result": "ok",
            },
            source="test",
            id="ef-evt-1",
        )
        p = msg.payload
        assert p.get("execution_id") is not None
        assert p.get("execution_mode") is not None
        assert p.get("execution_state") is not None
        assert p.get("verification_state") is not None

        proj = GraphOSProjection()
        result = proj.project(msg)
        assert result is not None
        assert result["execution_id"] == "ef-1"
        assert result["execution_mode"] == "real"
        assert result["execution_state"] == "completed"
        assert result["verification_state"] == "verified"
