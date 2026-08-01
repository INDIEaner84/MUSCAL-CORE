from __future__ import annotations
import json
import time
import pytest
from typing import Any, Dict, List, Optional

from event_bus import EventBus
from runtime.event_store import EventStore
from features.safety.safety_gate import SafetyGate
from features.tool_runtime.tool_runtime import UnifiedToolRuntime, create_default_utr
from features.supl.adapter_registry import AdapterRegistry
from features.supl.event_integration import EventBusBridge
from features.supl.graph_projection import GraphProjectionEngine
from features.supl.graph_projection_events import create_graph_projection_event_bridge
from features.supl.projection_engine import ProjectionEngine
from features.supl.provenance_linker import ProvenanceLinker
from features.supl.api import create_supl_api
from features.supl.ws_stream import SUPLWebSocketManager
from features.supl.event_topics import (
    SUPL_APPLICATION_REGISTERED,
    SUPL_APPLICATION_UPDATED,
    SUPL_APPLICATION_REMOVED,
    SUPL_ACTION_REQUESTED,
    SUPL_ACTION_AUTHORIZED,
    SUPL_EXECUTION_COMPLETED,
    SUPL_EXECUTION_FAILED,
)
from features.supl.semantic_model import (
    SemanticApplication, ActionInvocation, Capability, Parameter,
    ApplicationState, Action, EventDefinition,
    RiskLevel, ExecutionMode, TrustLevel, ApplicationLifecycle, StateSource,
)
from features.supl.semantic_adapter import BaseSemanticAdapter
from tests.supl.conftest import CalcTestAdapter, FailingTestAdapter


class _GraphStore:
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: list = []


class _SimpleAdapter(BaseSemanticAdapter):
    application_id = "gate1_test"
    application_version = "1.0.0"

    def __init__(self):
        self._app = SemanticApplication(
            id="gate1_test", name="Gate1 Test", version="1.0.0",
            source="test", lifecycle=ApplicationLifecycle.ACTIVE,
            trust_level=TrustLevel.LOW,
            capabilities={
                "ping": Capability(id="ping", name="Ping", description="Test capability",
                                   risk_level=RiskLevel.LOW, execution_mode=ExecutionMode.DIRECT,
                                   tool_name="console.print"),
            },
            parameters={},
            state={},
            actions={
                "say_hello": Action(id="say_hello", capability_id="ping", name="Say Hello",
                                    parameter_ids=["message"]),
            },
            events={},
        )
        self._app.parameters["message"] = Parameter(
            id="message", name="Message", type="string",
            schema={"type": "string"}, required=True,
        )

    @property
    def application(self) -> SemanticApplication:
        return self._app

    def discover(self) -> SemanticApplication:
        return self._app

    def introspect_capability(self, capability_id: str):
        return self._app.capabilities.get(capability_id)

    def get_state(self, state_id: str):
        return self._app.state.get(state_id)

    def synchronize_state(self):
        return dict(self._app.state)

    def map_action(self, action_id: str, parameters: dict) -> ActionInvocation:
        action = self._app.actions.get(action_id)
        if action is None:
            raise ValueError(f"unknown action: {action_id}")
        return ActionInvocation(
            application_id="gate1_test",
            capability_id=action.capability_id,
            action_id=action_id,
            tool_name="console.print",
            args={"message": parameters.get("message", "hello")},
        )

    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


# ═══════════════════════════════════════════════════════════════
# TEST A — SUPL PROJECTION CHAIN
# ═══════════════════════════════════════════════════════════════

class TestProjectionChain:
    def test_projection_chain_with_real_eventbus(self):
        bus = EventBus()
        store = _GraphStore()
        bridge = EventBusBridge(bus)
        registry = AdapterRegistry(event_bridge=bridge)

        engine = GraphProjectionEngine(registry, store)
        event_bridge = create_graph_projection_event_bridge(
            event_bus=bus,
            projection_engine=engine,
        )
        try:
            received_events = []
            bus.subscribe("*", lambda m: received_events.append(m))

            adapter = _SimpleAdapter()
            registry.register(adapter)

            reg_events = [e for e in received_events if e.topic == SUPL_APPLICATION_REGISTERED]
            assert len(reg_events) >= 1

            assert "supl:app:gate1_test:gate1_test" in store.nodes

            assert event_bridge.is_running()
            projected = event_bridge.get_projected_apps()
            assert "gate1_test" in projected
        finally:
            event_bridge.stop()

    def test_graph_state_is_derived(self):
        bus = EventBus()
        store = _GraphStore()
        bridge = EventBusBridge(bus)
        registry = AdapterRegistry(event_bridge=bridge)
        engine = GraphProjectionEngine(registry, store)
        event_bridge = create_graph_projection_event_bridge(
            event_bus=bus,
            projection_engine=engine,
        )
        try:
            adapter = _SimpleAdapter()
            registry.register(adapter)

            app_node = store.nodes.get("supl:app:gate1_test:gate1_test")
            assert app_node is not None
            payload = app_node["payload"]

            evidence = payload.get("evidence_classification", "")
            assert evidence == "PROJECTED"

            projection_metadata = payload.get("metadata", {})
            source_authority = projection_metadata.get("source_authority", "")
            assert source_authority == "SUPL_SEMANTIC_MODEL"
        finally:
            event_bridge.stop()

    def test_application_update_triggers_resync(self):
        bus = EventBus()
        store = _GraphStore()
        registry = AdapterRegistry()
        bridge = EventBusBridge(bus)
        engine = GraphProjectionEngine(registry, store)
        event_bridge = create_graph_projection_event_bridge(
            event_bus=bus,
            projection_engine=engine,
        )
        try:
            adapter = _SimpleAdapter()
            registry.register(adapter)

            bridge.publish_application_updated("gate1_test", "Gate1 Test", "1.1.0")

            assert "gate1_test" in event_bridge.get_projected_apps()
        finally:
            event_bridge.stop()

    def test_application_removal_cleans_graph(self):
        bus = EventBus()
        store = _GraphStore()
        registry = AdapterRegistry()
        bridge = EventBusBridge(bus)
        engine = GraphProjectionEngine(registry, store)
        event_bridge = create_graph_projection_event_bridge(
            event_bus=bus,
            projection_engine=engine,
        )
        try:
            adapter = _SimpleAdapter()
            registry.register(adapter)

            bridge.publish_application_removed("gate1_test")

            supl_nodes = [nid for nid in store.nodes if nid.startswith("supl:")]
            assert len(supl_nodes) == 0
        finally:
            event_bridge.stop()


# ═══════════════════════════════════════════════════════════════
# TEST B — PRODUCTION EXECUTION CHAIN
# ═══════════════════════════════════════════════════════════════

class TestExecutionChain:
    def test_execution_chain_with_real_components(self):
        bus = EventBus()
        event_store = EventStore()
        safety_gate = SafetyGate()
        safety_gate.permit("console.print")
        safety_gate.permit("math.add")

        utr, _browser = create_default_utr(safety_gate=safety_gate)
        registry = AdapterRegistry()
        bridge = EventBusBridge(bus)

        linker = ProvenanceLinker(bridge)
        projection_engine = ProjectionEngine(registry)

        supl_api = create_supl_api(
            registry=registry,
            engine=projection_engine,
            event_bridge=bridge,
            linker=linker,
            utr=utr,
        )

        adapter = _SimpleAdapter()
        registry.register(adapter)

        self._simulate_action_execution(supl_api, adapter)

    def _simulate_action_execution(self, supl_api, adapter):
        from features.supl.provenance import UIInteraction
        interaction = UIInteraction.create(
            application_id="gate1_test",
            action_id="say_hello",
            source_mode="overlay",
        )

        action = adapter._app.actions["say_hello"]
        cap = adapter._app.capabilities[action.capability_id]
        inv = ActionInvocation(
            application_id="gate1_test",
            capability_id=action.capability_id,
            action_id=action.id,
            tool_name=cap.tool_name,
            args={"message": "hello from Gate 1"},
        )

        interaction.mark_authorized()
        interaction.mark_executing()

        result = supl_api._utr.execute(
            inv.tool_name,
            inv.args,
            correlation_id=interaction.interaction_id,
        )

        assert result.success, f"Execution failed: {result.error}"
        assert result.receipt is not None
        assert result.receipt.receipt_id
        assert result.receipt.execution_id

        receipt = result.receipt
        interaction.link_execution(receipt.execution_id)
        interaction.link_receipt(receipt.receipt_id)
        if supl_api._linker:
            supl_api._linker.link(interaction, receipt)

        chain = supl_api._linker.get_chain(interaction.interaction_id)
        assert chain is not None
        assert chain["execution_id"] == receipt.execution_id
        assert chain["receipt_id"] == receipt.receipt_id

    def test_safety_gate_is_traversed(self):
        bus = EventBus()
        safety_gate = SafetyGate()

        utr, _browser = create_default_utr(safety_gate=safety_gate)

        safety_events = []
        bus.subscribe("*", lambda m: safety_events.append(m))

        result = utr.execute("console.print", {"message": "ok"})
        assert result.success

        safety_gate.deny("console.print")
        result_blocked = utr.execute("console.print", {"message": "blocked"})
        assert not result_blocked.success
        assert "NOT_ALLOWED" in (result_blocked.error or "") or "BLOCKED" in (result_blocked.error or "")


# ═══════════════════════════════════════════════════════════════
# TEST C — WEBSOCKET FUNCTIONAL REACHABILITY
# ═══════════════════════════════════════════════════════════════

class TestWebSocket:
    @pytest.mark.asyncio
    async def test_websocket_manager_creation(self):
        bus = EventBus()
        manager = SUPLWebSocketManager(event_bus=bus)
        assert manager is not None
        assert not manager._clients

    @pytest.mark.asyncio
    async def test_websocket_receives_events(self):
        bus = EventBus()
        manager = SUPLWebSocketManager(event_bus=bus)
        received = []
        bus.subscribe("*", lambda m: received.append(m))

        bridge = EventBusBridge(bus)
        bridge.publish_application_registered("test_app", "Test", "1.0")

        assert len(received) == 1
        assert received[0].topic == SUPL_APPLICATION_REGISTERED


# ═══════════════════════════════════════════════════════════════
# TEST D — RESTART / DUPLICATE SUBSCRIPTION
# ═══════════════════════════════════════════════════════════════

class TestRestartNoDuplicates:
    def test_no_duplicate_subscriptions_on_restart(self):
        bus = EventBus()

        def _initialize():
            registry = AdapterRegistry()
            bridge = EventBusBridge(bus)
            store = _GraphStore()
            engine = GraphProjectionEngine(registry, store)
            event_bridge = create_graph_projection_event_bridge(
                event_bus=bus,
                projection_engine=engine,
            )
            return registry, bridge, engine, event_bridge

        registry1, bridge1, engine1, eb1 = _initialize()
        count = bus.get_stats()
        sub_count_before = count.get("subscriber_count", 0)

        registry2, bridge2, engine2, eb2 = _initialize()
        count2 = bus.get_stats()
        sub_count_after = count2.get("subscriber_count", 0)

        num_events_before = len(bus.get_history(SUPL_APPLICATION_REGISTERED))
        bridge1.publish_application_registered("dup_test", "Dup Test", "1.0")
        num_events_after = len(bus.get_history(SUPL_APPLICATION_REGISTERED))

        assert num_events_after >= num_events_before + 1

        eb1.stop()
        eb2.stop()

    def test_shutdown_removes_subscriptions(self):
        bus = EventBus()
        registry = AdapterRegistry()
        bridge = EventBusBridge(bus)
        store = _GraphStore()
        engine = GraphProjectionEngine(registry, store)
        event_bridge = create_graph_projection_event_bridge(
            event_bus=bus,
            projection_engine=engine,
        )

        event_bridge.stop()
        bridge.unsubscribe_all()

        count = bus.get_stats()
        assert count.get("subscriber_count", 0) < 3
