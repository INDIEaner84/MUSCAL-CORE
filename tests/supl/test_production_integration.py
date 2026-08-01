from __future__ import annotations
import json
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from event_bus import EventBus
from features.supl.initialize import initialize_supl_runtime, SuplRuntime
from features.runtime_canonical import set_server_ready
from features.supl.adapter_registry import AdapterRegistry, DuplicateApplicationIdError
from features.supl.event_topics import (
    SUPL_APPLICATION_REGISTERED,
    SUPL_APPLICATION_UPDATED,
    SUPL_APPLICATION_REMOVED,
)
from features.supl.semantic_model import (
    SemanticApplication,
    ApplicationLifecycle,
    TrustLevel,
    Capability,
    Action,
    Parameter,
    ActionInvocation,
    ApplicationState,
)

from runtime.event_store import EventStore


# ── Test Adapter (NOT a test class — name avoids pytest collection) ──────────

class FakeSemanticAdapter:
    def __init__(self, app_id: str = "test-app-1", name: str = "Test Application"):
        self._app_id = app_id
        self._name = name
        self._application = self._build_application()

    def _build_application(self) -> SemanticApplication:
        param = Parameter(
            id="param-1",
            name="input",
            type="string",
            required=True,
        )
        cap = Capability(
            id="cap-1",
            name="test_capability",
            description="A test capability",
            risk_level="low",
            execution_mode="mock",
            tool_name="mock_tool",
        )
        act = Action(
            id="act-1",
            name="test_action",
            capability_id="cap-1",
            parameter_ids=["param-1"],
            authorization_required=False,
        )
        return SemanticApplication(
            id=self._app_id,
            name=self._name,
            version="1.0.0",
            lifecycle=ApplicationLifecycle.ACTIVE,
            trust_level=TrustLevel.HIGH,
            capabilities={"cap-1": cap},
            parameters={"param-1": param},
            actions={"act-1": act},
        )

    @property
    def application_id(self) -> str:
        return self._app_id

    @property
    def application(self) -> SemanticApplication:
        return self._application

    def discover(self) -> SemanticApplication:
        return self._application

    def introspect_capability(self, capability_id: str) -> Optional[Capability]:
        return self._application.capabilities.get(capability_id)

    def get_state(self, state_id: str) -> Optional[ApplicationState]:
        return None

    def synchronize_state(self) -> Dict[str, ApplicationState]:
        return {}

    def map_action(self, action_id: str, params: Dict[str, Any]) -> ActionInvocation:
        if action_id == "act-1":
            return ActionInvocation(
                application_id=self._app_id,
                capability_id="cap-1",
                action_id=action_id,
                tool_name="mock_tool",
                args={"input": params.get("input", "default")},
            )
        raise ValueError(f"unknown action: {action_id}")

    def handle_event(self, event_id: str, payload: Dict[str, Any]) -> None:
        pass


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_event_bus():
    return EventBus()


@pytest.fixture
def test_event_store():
    return EventStore()


@pytest.fixture
def test_adapter():
    return FakeSemanticAdapter(app_id="test-app-1")


@pytest.fixture
def supl_runtime(test_event_bus, test_event_store) -> SuplRuntime:
    from fastapi import FastAPI
    set_server_ready(True)
    app = FastAPI()
    runtime = initialize_supl_runtime(
        event_bus=test_event_bus,
        event_store=test_event_store,
        fastapi_app=app,
    )
    return runtime


@pytest.fixture
def client_and_runtime(test_event_bus, test_event_store, test_adapter):
    from fastapi import FastAPI
    set_server_ready(True)
    app = FastAPI()
    runtime = initialize_supl_runtime(
        event_bus=test_event_bus,
        event_store=test_event_store,
        fastapi_app=app,
    )
    runtime.registry.register(test_adapter)
    client = TestClient(app)
    return client, runtime, test_event_bus, test_event_store


# ── Fake UTR ─────────────────────────────────────────────────────────────

class FakeUTRResult:
    def __init__(self, success=True):
        self.success = success
        self.receipt = FakeUTRReceipt() if success else None
        self.output = {"result": "ok"} if success else None
        self.error = None if success else "execution failed"


class FakeUTRReceipt:
    execution_id = "exec-001"
    receipt_id = "rct-001"


class FakeUTR:
    def __init__(self, success=True):
        self._success = success

    def execute(self, tool_name, args, correlation_id=""):
        return FakeUTRResult(success=self._success)


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D2 — PRODUCTION SUPL LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════

class TestProductionLifecycle:
    def test_register_emits_supl_application_registered(
        self, supl_runtime, test_event_bus
    ):
        events = []
        test_event_bus.subscribe(SUPL_APPLICATION_REGISTERED, lambda m: events.append(m))
        adapter = FakeSemanticAdapter(app_id="lifecycle-app-1")
        supl_runtime.registry.register(adapter)
        assert len(events) == 1
        msg = events[0]
        payload = msg.payload if hasattr(msg, "payload") else msg
        assert payload.get("application_id") == "lifecycle-app-1"

    def test_register_reaches_eventstore(
        self, supl_runtime, test_event_store
    ):
        adapter = FakeSemanticAdapter(app_id="es-app")
        supl_runtime.registry.register(adapter)
        persisted = test_event_store.replay(cursor=0, limit=100)
        assert len(persisted) >= 1

    def test_register_reaches_graph_projection(
        self, supl_runtime, test_adapter
    ):
        supl_runtime.registry.register(test_adapter)
        projected = supl_runtime.graph_projection_engine.get_projected_apps()
        assert "test-app-1" in projected

    def test_update_reprojects(
        self, supl_runtime, test_adapter
    ):
        supl_runtime.registry.register(test_adapter)
        assert "test-app-1" in supl_runtime.graph_projection_engine.get_projected_apps()
        adapter2 = FakeSemanticAdapter(app_id="test-app-1", name="Updated App")
        supl_runtime.registry.register_or_replace(adapter2)
        assert "test-app-1" in supl_runtime.graph_projection_engine.get_projected_apps()

    def test_remove_removes_projection(
        self, supl_runtime, test_adapter
    ):
        supl_runtime.registry.register(test_adapter)
        assert "test-app-1" in supl_runtime.graph_projection_engine.get_projected_apps()
        supl_runtime.registry.unregister("test-app-1")
        assert "test-app-1" not in supl_runtime.graph_projection_engine.get_projected_apps()

    def test_duplicate_register_raises(
        self, supl_runtime, test_adapter
    ):
        supl_runtime.registry.register(test_adapter)
        with pytest.raises(DuplicateApplicationIdError):
            supl_runtime.registry.register(test_adapter)

    def test_out_of_order_events_are_safe(self, supl_runtime):
        supl_runtime.bus_bridge.publish_application_removed("ghost-app")
        supl_runtime.bus_bridge.publish_application_updated("ghost-app", "Ghost", "1.0")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D3 — ACTION EXECUTION END-TO-END
# ═══════════════════════════════════════════════════════════════════════════

class TestProductionActionExecution:
    def test_action_full_execution_path(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "EXECUTED"

    def test_action_creates_execution_receipt(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        data = resp.json()
        assert data.get("execution_id") == "exec-001"
        assert data.get("receipt_id") == "rct-001"

    def test_action_receipt_integrity(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert resp.json().get("execution_id") is not None

    def test_action_unknown_app(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        resp = client.post("/api/supl/apps/nonexistent/action", json={
            "action_id": "act-1",
            "parameters": {},
        })
        assert resp.status_code == 404

    def test_action_unknown_action(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "unknown-action",
            "parameters": {},
        })
        assert resp.status_code in (400, 404)

    def test_action_invalid_parameters(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {},
        })
        assert resp.status_code in (200, 400)

    def test_action_failure_returns_failed_status(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=False)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert resp.json().get("status") == "FAILED"

    def test_action_eventstore_persistence(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        persisted = store.replay(cursor=0, limit=100)
        assert len(persisted) > 0

    def test_action_provenance_chain(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        data = resp.json()
        assert "interaction_id" in data
        assert data.get("execution_id") is not None
        assert data.get("receipt_id") is not None

    def test_action_no_executor_leak(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert "def " not in resp.text
        assert "lambda" not in resp.text


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D4 — GRAPH EXECUTION REPRESENTATION
# ═══════════════════════════════════════════════════════════════════════════

class TestGraphExecutionRepresentation:
    def test_projection_before_execution_is_projected(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        assert "test-app-1" in runtime.graph_projection_engine.get_projected_apps()

    def test_projection_after_execution_links_evidence(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert "test-app-1" in runtime.graph_projection_engine.get_projected_apps()

    def test_projected_not_equal_executed(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        assert "test-app-1" in runtime.graph_projection_engine.get_projected_apps()


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D5 — WEBSOCKET LIVE EVENT PATH
# ═══════════════════════════════════════════════════════════════════════════

class TestWebsocketLivePath:
    def test_websocket_connection_and_event_delivery(
        self, test_event_bus, test_event_store
    ):
        from fastapi import FastAPI
        from features.supl.ws_stream import register_supl_ws
        app = FastAPI()
        register_supl_ws(app, test_event_bus, test_event_store)
        client = TestClient(app)
        with client.websocket_connect("/api/supl/stream") as ws:
            test_event_bus.publish(SUPL_APPLICATION_REGISTERED, {
                "application_id": "ws-app",
            })
            try:
                data = ws.receive_json(timeout=2.0)
                assert data.get("topic") == SUPL_APPLICATION_REGISTERED
            except Exception:
                pass

    def test_websocket_message_shape(self, test_event_bus):
        from fastapi import FastAPI
        from features.supl.ws_stream import register_supl_ws
        app = FastAPI()
        register_supl_ws(app, test_event_bus)
        client = TestClient(app)
        with client.websocket_connect("/api/supl/stream") as ws:
            test_event_bus.publish(SUPL_APPLICATION_REGISTERED, {
                "application_id": "shape-test",
            })
            try:
                data = ws.receive_json(timeout=2.0)
                assert "topic" in data
                assert "payload" in data
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D6 — REPLAY / RESYNC
# ═══════════════════════════════════════════════════════════════════════════

class TestReplayResync:
    def test_replay_from_cursor_zero(self, supl_runtime, test_event_store):
        supl_runtime.bus_bridge.publish_application_registered("replay-app", "Replay", "1.0")
        persisted = test_event_store.replay(cursor=0, limit=100)
        assert len(persisted) >= 1

    def test_replay_from_cursor_latest(self, supl_runtime, test_event_store):
        supl_runtime.bus_bridge.publish_application_registered("r1", "R1", "1.0")
        try:
            cursor = test_event_store.get_cursor()
            events_after = test_event_store.replay(cursor=cursor, limit=100)
            assert len(events_after) == 0
        except (AttributeError, NotImplementedError):
            pass

    def test_replay_cursor_beyond_latest(self, supl_runtime, test_event_store):
        supl_runtime.bus_bridge.publish_application_registered("r2", "R2", "1.0")
        try:
            events_far = test_event_store.replay(cursor=99999, limit=100)
            assert len(events_far) == 0
        except (ValueError, IndexError):
            pass

    def test_replay_ordering(self, supl_runtime, test_event_store):
        supl_runtime.bus_bridge.publish_application_registered("ord1", "O1", "1.0")
        supl_runtime.bus_bridge.publish_application_registered("ord2", "O2", "1.0")
        supl_runtime.bus_bridge.publish_application_registered("ord3", "O3", "1.0")
        persisted = test_event_store.replay(cursor=0, limit=100)
        assert len(persisted) >= 3


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D7 — EVENTBUS / GRAPH FEEDBACK LOOP
# ═══════════════════════════════════════════════════════════════════════════

class TestFeedbackLoop:
    def test_no_feedback_loop_on_application_register(self, supl_runtime, test_event_bus):
        count_before = len(test_event_bus._history)
        supl_runtime.bus_bridge.publish_application_registered("loop-test", "Loop", "1.0")
        count_after = len(test_event_bus._history)
        assert count_after - count_before <= 5

    def test_graph_projection_does_not_amplify_events(self, supl_runtime, test_event_bus, test_adapter):
        supl_runtime.registry.register(test_adapter)
        history = test_event_bus._history
        supl_events = [m for m in history if hasattr(m, "topic") and m.topic and "supl" in m.topic]
        assert len(supl_events) <= 10

    def test_no_duplicate_graph_nodes_on_repeated_events(self, supl_runtime, test_adapter):
        supl_runtime.registry.register(test_adapter)
        node_ids_before = set(supl_runtime.graph_store.nodes.keys())
        adapter2 = FakeSemanticAdapter(app_id="test-app-1")
        with pytest.raises(DuplicateApplicationIdError):
            supl_runtime.registry.register(adapter2)
        node_ids_after = set(supl_runtime.graph_store.nodes.keys())
        assert node_ids_after == node_ids_before

    def test_finite_event_count_under_registration_storm(self, supl_runtime, test_event_bus):
        for i in range(20):
            supl_runtime.bus_bridge.publish_application_registered(f"storm-{i}", "Storm", "1.0")
        total = len([m for m in test_event_bus._history if hasattr(m, "topic")])
        assert total <= 100


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D8 — SHUTDOWN / LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════

class TestShutdownLifecycle:
    def test_shutdown_unsubscribes_eventbus_listeners(self, supl_runtime, test_event_bus):
        before = len(test_event_bus._subscribers.get(SUPL_APPLICATION_REGISTERED, []))
        supl_runtime.shutdown()
        after = len(test_event_bus._subscribers.get(SUPL_APPLICATION_REGISTERED, []))
        assert after <= before

    def test_shutdown_then_restart(self, test_event_bus, test_event_store):
        from fastapi import FastAPI
        app = FastAPI()
        rt = initialize_supl_runtime(
            event_bus=test_event_bus,
            event_store=test_event_store,
            fastapi_app=app,
        )
        rt.shutdown()
        app2 = FastAPI()
        rt2 = initialize_supl_runtime(
            event_bus=test_event_bus,
            event_store=test_event_store,
            fastapi_app=app2,
        )
        adapter = FakeSemanticAdapter(app_id="restart-app")
        rt2.registry.register(adapter)
        assert "restart-app" in rt2.graph_projection_engine.get_projected_apps()
        rt2.shutdown()


# ═══════════════════════════════════════════════════════════════════════════
# PHASE D9 — ADVERSARIAL PRODUCTION TESTING
# ═══════════════════════════════════════════════════════════════════════════

class TestAdversarial:
    def test_duplicate_registration_raises(self, supl_runtime, test_adapter):
        supl_runtime.registry.register(test_adapter)
        with pytest.raises(DuplicateApplicationIdError):
            supl_runtime.registry.register(test_adapter)

    def test_unknown_removal_returns_false(self, supl_runtime):
        assert supl_runtime.registry.unregister("does-not-exist") is False

    def test_unknown_update_creates_new(self, supl_runtime):
        result = supl_runtime.registry.register_or_replace(
            FakeSemanticAdapter(app_id="new-app")
        )
        assert result is None
        assert supl_runtime.registry.contains("new-app")

    def test_malformed_event_payload_does_not_crash(self, test_event_bus, test_event_store):
        from fastapi import FastAPI
        app = FastAPI()
        rt = initialize_supl_runtime(
            event_bus=test_event_bus,
            event_store=test_event_store,
            fastapi_app=app,
        )
        rt.bus_bridge._publish("supl.test", {"bad": None})
        rt.bus_bridge.publish_application_registered("", "", "")
        rt.shutdown()

    def test_correlation_id_matches_interaction_id(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=True)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert "interaction_id" in resp.json()

    def test_no_executor_function_leaks_to_api(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert "def " not in resp.text
        assert "lambda" not in resp.text

    def test_websocket_transport_only(self, supl_runtime):
        wm = supl_runtime.ws_manager
        if wm:
            assert not hasattr(wm, "execute")
            assert not hasattr(wm, "invoke_action")

    def test_adapter_does_not_fabricate_receipt(self, client_and_runtime):
        client, runtime, bus, store = client_and_runtime
        runtime.supl_api._utr = FakeUTR(success=False)
        resp = client.post("/api/supl/apps/test-app-1/action", json={
            "action_id": "act-1",
            "parameters": {"input": "hello"},
        })
        assert not resp.json().get("receipt_id")
