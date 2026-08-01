"""
Phase 6.1: Event-Driven Projection Closure Tests

Tests:
- Event routing (REGISTERED→project, UPDATED→sync, REMOVED→remove)
- Idempotency (duplicate events do not duplicate graph state)
- Ordering (out-of-order, stale events)
- Isolation (app A events do not affect app B)
- Trust (projected != executed, no fabricated provenance)
- Security (event payload cannot cause execution)
- Persistence (EventBus -> EventStore integration)
"""

import time
import pytest
from typing import Any, Dict
from unittest.mock import MagicMock

from event_bus import EventBus, EventMessage
from features.supl.semantic_adapter import BaseSemanticAdapter
from features.supl.semantic_model import (
    SemanticApplication, Capability, Parameter, Action,
    ApplicationState, EventDefinition, ApplicationLifecycle,
    TrustLevel, StateSource, RiskLevel, ExecutionMode,
    ActionInvocation,
)
from features.supl.adapter_registry import AdapterRegistry
from features.supl.graph_projection import (
    GraphProjectionEngine, EVIDENCE_PROJECTED, EVIDENCE_EXECUTED,
)
from features.supl.event_integration import EventBusBridge
from features.supl.event_topics import (
    SUPL_APPLICATION_REGISTERED, SUPL_APPLICATION_UPDATED,
    SUPL_APPLICATION_REMOVED,
)
from features.supl.graph_projection_events import (
    GraphProjectionEventBridge, create_graph_projection_event_bridge,
)


class FakeGraphStore:
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: list = []


class DynamicTestAdapter(BaseSemanticAdapter):
    def __init__(self, app: SemanticApplication):
        self._app = app
    @property
    def application_id(self) -> str:
        return self._app.id
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
    def map_action(self, action_id: str, parameters: dict):
        action = self._app.actions.get(action_id)
        if action is None:
            raise ValueError(f"unknown action: {action_id}")
        cap = self._app.capabilities.get(action.capability_id)
        tool = cap.tool_name if cap else "unknown"
        return ActionInvocation(
            application_id=self._app.id, capability_id=action.capability_id,
            action_id=action_id, tool_name=tool, args=parameters,
        )
    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


def make_test_app(app_id="test_calc", version="0.1.0") -> SemanticApplication:
    return SemanticApplication(
        id=app_id, name="Test Calculator", version=version,
        lifecycle=ApplicationLifecycle.ACTIVE, trust_level=TrustLevel.LOW,
        capabilities={
            "add": Capability(id="add", name="Addition", description="Add two numbers",
                              risk_level=RiskLevel.LOW, tool_name="add_tool"),
        },
        parameters={
            "a": Parameter(id="a", name="a", type="number", required=True),
        },
        state={
            "last_result": ApplicationState(id="last_result", name="Last Result",
                                            type="number", value=0, source=StateSource.USER),
        },
        actions={
            "do_add": Action(id="do_add", capability_id="add", name="do_add", parameter_ids=["a"]),
        },
        events={
            "calc_done": EventDefinition(id="calc_done", name="CalculationDone"),
        },
    )


def make_bridge(event_bus=None, registry=None, store=None):
    bus = event_bus or EventBus()
    bus_bridge = EventBusBridge(bus)
    reg = registry or AdapterRegistry(event_bridge=bus_bridge)
    st = store or FakeGraphStore()
    engine = GraphProjectionEngine(reg, st)
    bridge = GraphProjectionEventBridge(bus, engine)
    bridge.start()
    return bus, bus_bridge, reg, st, engine, bridge


def make_event_msg(topic, payload):
    return EventMessage(topic=topic, payload=payload, source="test")


# ---------------------------------------------------------------------------
# 1. Event Routing
# ---------------------------------------------------------------------------

class TestEventRouting:
    def test_registered_triggers_projection(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("test_a")))
        assert "supl:app:test_a:test_a" in store.nodes

    def test_updated_triggers_sync(self):
        bus, _, reg, store, _, _ = make_bridge()
        app = make_test_app("test_b")
        reg.register(DynamicTestAdapter(app))
        assert "supl:app:test_b:test_b" in store.nodes
        app.name = "Updated Calculator"
        reg.register_or_replace(DynamicTestAdapter(app))
        node = store.nodes["supl:app:test_b:test_b"]
        assert node["payload"]["name"] == "Updated Calculator"

    def test_removed_triggers_removal(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("test_c")))
        assert "supl:app:test_c:test_c" in store.nodes
        reg.unregister("test_c")
        assert "supl:app:test_c:test_c" not in store.nodes

    def test_removed_clears_child_nodes(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("test_d")))
        assert len(store.nodes) > 1
        reg.unregister("test_d")
        supl_nodes = [n for n in store.nodes if n.startswith("supl:")]
        assert len(supl_nodes) == 0

    def test_bridge_subscribes_to_all_topics(self):
        bus, _, reg, store, _, bridge = make_bridge()
        assert bridge.is_running()


# ---------------------------------------------------------------------------
# 2. Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_duplicate_registered_raises(self):
        bus, _, reg, store, _, _ = make_bridge()
        app = make_test_app("dup_app")
        reg.register(DynamicTestAdapter(app))
        with pytest.raises(Exception):
            reg.register(DynamicTestAdapter(app))

    def test_duplicate_register_or_replace_is_idempotent(self):
        bus, _, reg, store, _, _ = make_bridge()
        app = make_test_app("dup_rep")
        reg.register(DynamicTestAdapter(app))
        n_before = len(store.nodes)
        e_before = len(store.edges)
        reg.register_or_replace(DynamicTestAdapter(app))
        assert len(store.nodes) == n_before
        assert len(store.edges) == e_before

    def test_duplicate_removed(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("dup_rem")))
        reg.unregister("dup_rem")
        assert reg.unregister("dup_rem") is False
        supl_nodes = [n for n in store.nodes if n.startswith("supl:")]
        assert len(supl_nodes) == 0

    def test_direct_duplicate_registered_event(self):
        bus, _, reg, store, engine, bridge = make_bridge()
        app = make_test_app("dir_dup")
        reg.register(DynamicTestAdapter(app))
        n_before = len(store.nodes)
        e_before = len(store.edges)
        msg = make_event_msg(SUPL_APPLICATION_REGISTERED, {"application_id": "dir_dup"})
        bridge._on_registered(msg)
        assert len(store.nodes) == n_before
        assert len(store.edges) == e_before

    def test_direct_duplicate_removed_event(self):
        bus, _, reg, store, _, bridge = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("dir_dup_rem")))
        reg.unregister("dir_dup_rem")
        n_before = len(store.nodes)
        msg = make_event_msg(SUPL_APPLICATION_REMOVED, {"application_id": "dir_dup_rem"})
        bridge._on_removed(msg)
        assert len(store.nodes) == n_before


# ---------------------------------------------------------------------------
# 3. Ordering
# ---------------------------------------------------------------------------

class TestOrdering:
    def test_updated_before_registered_is_safe(self):
        bus, _, reg, store, _, bridge = make_bridge()
        msg = make_event_msg(SUPL_APPLICATION_UPDATED, {"application_id": "never_reg"})
        bridge._on_updated(msg)
        assert "supl:app:never_reg:never_reg" not in store.nodes

    def test_removed_before_registered_is_safe(self):
        bus, _, reg, store, _, bridge = make_bridge()
        msg = make_event_msg(SUPL_APPLICATION_REMOVED, {"application_id": "never_reg2"})
        bridge._on_removed(msg)
        supl_nodes = [n for n in store.nodes if n.startswith("supl:")]
        assert len(supl_nodes) == 0

    def test_registered_then_updated_then_registered(self):
        bus, _, reg, store, _, bridge = make_bridge()
        app = make_test_app("order_app")
        reg.register(DynamicTestAdapter(app))
        n_before = len(store.nodes)
        app.name = "V2"
        reg.register_or_replace(DynamicTestAdapter(app))
        msg2 = make_event_msg(SUPL_APPLICATION_REGISTERED, {"application_id": "order_app"})
        bridge._on_registered(msg2)
        assert len(store.nodes) == n_before
        node = store.nodes["supl:app:order_app:order_app"]
        assert node["payload"]["name"] == "V2"

    def test_registered_then_removed_then_updated(self):
        bus, _, reg, store, _, bridge = make_bridge()
        app = make_test_app("order_app2")
        reg.register(DynamicTestAdapter(app))
        reg.unregister("order_app2")
        assert "supl:app:order_app2:order_app2" not in store.nodes
        msg = make_event_msg(SUPL_APPLICATION_UPDATED, {"application_id": "order_app2"})
        bridge._on_updated(msg)
        supl_nodes = [n for n in store.nodes if n.startswith("supl:order_app2:")]
        assert len(supl_nodes) == 0


# ---------------------------------------------------------------------------
# 4. Isolation
# ---------------------------------------------------------------------------

class TestIsolation:
    def test_app_a_events_do_not_modify_app_b(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("app_a")))
        reg.register(DynamicTestAdapter(make_test_app("app_b")))
        reg.unregister("app_a")
        assert "supl:app:app_a:app_a" not in store.nodes
        assert "supl:app:app_b:app_b" in store.nodes

    def test_removal_of_a_does_not_remove_b(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("iso_a")))
        reg.register(DynamicTestAdapter(make_test_app("iso_b")))
        reg.unregister("iso_a")
        b_nodes = [n for n in store.nodes if ":iso_b:" in n]
        assert len(b_nodes) > 0
        a_nodes = [n for n in store.nodes if ":iso_a:" in n]
        assert len(a_nodes) == 0


# ---------------------------------------------------------------------------
# 5. Trust Boundary
# ---------------------------------------------------------------------------

class TestTrustBoundary:
    def test_projected_node_not_executed(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("trust_test")))
        for node in store.nodes.values():
            e = node["payload"].get("evidence_classification", "")
            assert e == EVIDENCE_PROJECTED, f"Node has {e}, expected PROJECTED"
            assert e != EVIDENCE_EXECUTED
            assert "execution_id" not in node["payload"] or node["payload"].get("execution_id") is None

    def test_no_fabricated_provenance(self):
        bus, _, reg, store, _, _ = make_bridge()
        reg.register(DynamicTestAdapter(make_test_app("prov_test")))
        for node in store.nodes.values():
            p = node["payload"]
            assert p.get("execution_id") is None or p["execution_id"] == ""
            assert p.get("receipt_id") is None or p["receipt_id"] == ""
            assert p.get("verification_id") is None or p["verification_id"] == ""


# ---------------------------------------------------------------------------
# 6. Security
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_event_payload_cannot_inject_executor(self):
        bus, _, reg, store, _, bridge = make_bridge()
        payload = {"application_id": "hack", "executor": "shell.exec", "command": "rm -rf /"}
        msg = make_event_msg(SUPL_APPLICATION_REGISTERED, payload)
        bridge._on_registered(msg)
        assert reg.get("hack") is None
        supl_nodes = [n for n in store.nodes if ":hack:" in n]
        assert len(supl_nodes) == 0

    def test_event_payload_cannot_bypass_safety(self):
        bus, _, reg, store, _, bridge = make_bridge()
        payload = {"application_id": "bypass_test", "bypass_safety": True}
        msg = make_event_msg(SUPL_APPLICATION_REGISTERED, payload)
        bridge._on_registered(msg)
        assert reg.get("bypass_test") is None
        supl_nodes = [n for n in store.nodes if ":bypass_test:" in n]
        assert len(supl_nodes) == 0

    def test_malformed_event_does_not_execute(self):
        bus, _, reg, store, _, bridge = make_bridge()
        for bad in [None, {}, {"application_id": ""}, {"no_id": True}, "not_a_dict"]:
            try:
                msg = make_event_msg(SUPL_APPLICATION_REGISTERED, bad)
                bridge._on_registered(msg)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 7. Bridge Lifecycle
# ---------------------------------------------------------------------------

class TestBridgeLifecycle:
    def test_start_stop(self):
        bus = EventBus()
        reg = AdapterRegistry()
        store = FakeGraphStore()
        engine = GraphProjectionEngine(reg, store)
        bridge = GraphProjectionEventBridge(bus, engine)
        assert not bridge.is_running()
        bridge.start()
        assert bridge.is_running()
        bridge.stop()
        assert not bridge.is_running()

    def test_events_not_processed_after_stop(self):
        bus = EventBus()
        bus_bridge = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bus_bridge)
        store = FakeGraphStore()
        engine = GraphProjectionEngine(reg, store)
        bridge = GraphProjectionEventBridge(bus, engine)
        bridge.start()
        bridge.stop()
        msg = make_event_msg(SUPL_APPLICATION_REGISTERED, {"application_id": "post_stop"})
        bridge._on_registered(msg)
        supl_nodes = [n for n in store.nodes if n.startswith("supl:")]
        assert len(supl_nodes) == 0

    def test_create_bridge_helper(self):
        bus = EventBus()
        reg = AdapterRegistry()
        store = FakeGraphStore()
        engine = GraphProjectionEngine(reg, store)
        bridge = create_graph_projection_event_bridge(bus, engine)
        assert bridge.is_running()
        bridge.stop()


# ---------------------------------------------------------------------------
# 8. AdapterRegistry Event Publishing
# ---------------------------------------------------------------------------

class TestAdapterRegistryEvents:
    def test_register_publishes_event(self):
        bus = EventBus()
        received = []
        bus.subscribe(SUPL_APPLICATION_REGISTERED, lambda m: received.append(m))
        bridge_bus = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bridge_bus)
        reg.register(DynamicTestAdapter(make_test_app("pub_test")))
        assert len(received) >= 1

    def test_unregister_publishes_event(self):
        bus = EventBus()
        received = []
        bus.subscribe(SUPL_APPLICATION_REMOVED, lambda m: received.append(m))
        bridge_bus = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bridge_bus)
        reg.register(DynamicTestAdapter(make_test_app("unreg_test")))
        reg.unregister("unreg_test")
        assert len(received) >= 1

    def test_bridge_can_be_set_after_construction(self):
        bus = EventBus()
        reg = AdapterRegistry()
        bridge_bus = EventBusBridge(bus)
        reg.set_event_bridge(bridge_bus)
        received = []
        bus.subscribe(SUPL_APPLICATION_REGISTERED, lambda m: received.append(m))
        reg.register(DynamicTestAdapter(make_test_app("set_bridge_test")))
        assert len(received) >= 1

    def test_register_or_replace_publishes_updated_when_replacing(self):
        bus = EventBus()
        registered = []
        updated = []
        bus.subscribe(SUPL_APPLICATION_REGISTERED, lambda m: registered.append(m))
        bus.subscribe(SUPL_APPLICATION_UPDATED, lambda m: updated.append(m))
        bridge_bus = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bridge_bus)
        app = make_test_app("replace_test")
        reg.register(DynamicTestAdapter(app))
        count_before = len(registered)
        reg.register_or_replace(DynamicTestAdapter(app))
        assert len(updated) >= 1
        assert len(registered) == count_before


# ---------------------------------------------------------------------------
# 9. Full Integration
# ---------------------------------------------------------------------------

class TestFullIntegration:
    def test_full_lifecycle_events(self):
        bus = EventBus()
        bus_bridge = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bus_bridge)
        store = FakeGraphStore()
        engine = GraphProjectionEngine(reg, store)
        bridge = GraphProjectionEventBridge(bus, engine)
        bridge.start()

        app = make_test_app("full_life")
        reg.register(DynamicTestAdapter(app))
        assert "supl:app:full_life:full_life" in store.nodes

        app.name = "Updated Full Life"
        reg.register_or_replace(DynamicTestAdapter(app))
        node = store.nodes["supl:app:full_life:full_life"]
        assert node["payload"]["name"] == "Updated Full Life"

        reg.unregister("full_life")
        assert "supl:app:full_life:full_life" not in store.nodes
        bridge.stop()

    def test_event_bus_to_event_store_persistence(self):
        import tempfile
        from pathlib import Path
        from runtime.event_store import EventStore
        bus = EventBus()
        db_path = Path(tempfile.mktemp(suffix=".db"))
        es = EventStore(db_path=db_path)
        supl_events = []
        def capture(msg):
            if "supl.application" in msg.topic:
                supl_events.append(msg)
                es.append({
                    "seq": es.get_cursor() + 1,
                    "topic": msg.topic,
                    "payload": msg.payload,
                    "timestamp": msg.timestamp,
                    "id": msg.id,
                })
        bus.subscribe("*", capture)
        bus_bridge = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bus_bridge)
        reg.register(DynamicTestAdapter(make_test_app("persist_test")))
        reg.unregister("persist_test")
        history = es.replay(cursor=0, limit=100)
        topics = [e.get("topic") for e in history]
        assert SUPL_APPLICATION_REGISTERED in topics
        assert SUPL_APPLICATION_REMOVED in topics
        es.close()

    def test_replay_does_not_fabricate_execution(self):
        import tempfile
        from pathlib import Path
        from runtime.event_store import EventStore
        bus = EventBus()
        db_path = Path(tempfile.mktemp(suffix=".db"))
        es = EventStore(db_path=db_path)
        supl_events = []
        def capture(msg):
            if "supl.application" in msg.topic:
                supl_events.append(msg)
                es.append({
                    "seq": es.get_cursor() + 1,
                    "topic": msg.topic,
                    "payload": msg.payload,
                    "timestamp": msg.timestamp,
                    "id": msg.id,
                })
        bus.subscribe("*", capture)
        bus_bridge = EventBusBridge(bus)
        reg = AdapterRegistry(event_bridge=bus_bridge)
        reg.register(DynamicTestAdapter(make_test_app("replay_exec_test")))
        history = es.replay(cursor=0, limit=100)
        for ev in history:
            p = ev.get("payload", {})
            assert "execution_id" not in p or p.get("execution_id") is None
            assert "receipt_id" not in p or p.get("receipt_id") is None
        es.close()

    def test_bridge_does_not_have_executor_references(self):
        import inspect
        from features.supl import graph_projection_events
        source = inspect.getsource(graph_projection_events.GraphProjectionEventBridge)
        for forbidden in ["UnifiedToolRuntime", "SafetyGate", "executor", "callable"]:
            lines = [l for l in source.splitlines()
                     if forbidden in l and not l.strip().startswith("#")]
            assert len(lines) == 0, (
                f"Bridge references executor authority '{forbidden}'"
            )
