"""
Phase 6O-P: Graph Projection Tests

Tests:
- Basic projection (APPLICATION, CAPABILITY, PARAMETER, ACTION, STATE, EVENT)
- Relationships (correct edges, no duplicates, deterministic)
- Identity (stable node IDs, semantic source references)
- Idempotency (repeated projection, sync)
- Lifecycle (register, project, update, reproject, remove)
- Trust boundaries (PROJECTED != EXECUTED, no fabricated IDs)
- Adversarial cases
"""

import inspect
import pytest
from typing import Any, Dict

from features.supl.semantic_adapter import BaseSemanticAdapter
from features.supl.semantic_model import (
    SemanticApplication, Capability, Parameter, Action,
    ApplicationState, EventDefinition, ApplicationLifecycle,
    TrustLevel, StateSource, RiskLevel, ExecutionMode,
)
from features.supl.adapter_registry import AdapterRegistry
from features.supl.graph_projection import (
    GraphProjectionEngine,
    NODE_TYPE_APPLICATION,
    NODE_TYPE_CAPABILITY,
    NODE_TYPE_PARAMETER,
    NODE_TYPE_ACTION,
    NODE_TYPE_STATE,
    NODE_TYPE_EVENT,
    EDGE_TYPE_HAS_CAPABILITY,
    EDGE_TYPE_HAS_PARAMETER,
    EDGE_TYPE_HAS_ACTION,
    EDGE_TYPE_HAS_STATE,
    EDGE_TYPE_HAS_EVENT,
    EDGE_TYPE_SUPPORTS_ACTION,
    EDGE_TYPE_USES_PARAMETER,
    EVIDENCE_PROJECTED,
    EVIDENCE_EXECUTED,
    EVIDENCE_SIMULATED,
    EVIDENCE_VERIFIED,
    LIFECYCLE_PROJECTED,
    LIFECYCLE_UPDATED,
    LIFECYCLE_REPROJECTED,
    LIFECYCLE_REMOVED,
    SOURCE_AUTHORITY,
    GRAPH_PROJECTION_VERSION,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeGraphStore:
    """Minimal store mimicking GraphMemory/GraphStore interface."""
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: list = []

    def add_node(self, node_id: str, content: Any) -> None:
        self.nodes[node_id] = content

    def add_edge(self, from_id: str, to_id: str, relation: str) -> None:
        self.edges.append({"from": from_id, "to": to_id, "relation": relation})


class DynamicTestAdapter(BaseSemanticAdapter):
    """Adapter that wraps an arbitrary SemanticApplication for testing."""
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
        from features.supl.semantic_model import ActionInvocation
        action = self._app.actions.get(action_id)
        if action is None:
            raise ValueError(f"unknown action: {action_id}")
        cap = self._app.capabilities.get(action.capability_id)
        tool = cap.tool_name if cap else "unknown"
        return ActionInvocation(
            application_id=self._app.id,
            capability_id=action.capability_id,
            action_id=action_id,
            tool_name=tool,
            args=parameters,
        )

    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


SUPL_NODE_ID_PATTERNS = [
    ("application", NODE_TYPE_APPLICATION, "supl:app:{app_id}:{app_id}"),
    ("capability", NODE_TYPE_CAPABILITY, "supl:cap:{app_id}:{cap_id}"),
    ("parameter", NODE_TYPE_PARAMETER, "supl:param:{app_id}:{param_id}"),
    ("action", NODE_TYPE_ACTION, "supl:act:{app_id}:{action_id}"),
    ("state", NODE_TYPE_STATE, "supl:state:{app_id}:{state_id}"),
    ("event", NODE_TYPE_EVENT, "supl:evt:{app_id}:{event_id}"),
]


def make_test_app(app_id="test_calc", version="0.1.0") -> SemanticApplication:
    return SemanticApplication(
        id=app_id,
        name="Test Calculator",
        version=version,
        lifecycle=ApplicationLifecycle.ACTIVE,
        trust_level=TrustLevel.LOW,
        capabilities={
            "add": Capability(id="add", name="Addition", description="Add two numbers",
                              risk_level=RiskLevel.LOW, tool_name="add_tool"),
            "multiply": Capability(id="multiply", name="Multiplication", description="Multiply two numbers",
                                   risk_level=RiskLevel.MEDIUM, tool_name="mul_tool"),
        },
        parameters={
            "a": Parameter(id="a", name="a", type="number", required=True),
            "b": Parameter(id="b", name="b", type="number", required=True),
        },
        state={
            "last_result": ApplicationState(id="last_result", name="Last Result", type="number", value=0,
                                            source=StateSource.USER),
            "operation_count": ApplicationState(id="operation_count", name="Operation Count", type="integer", value=42),
        },
        actions={
            "do_add": Action(id="do_add", capability_id="add", name="do_add", parameter_ids=["a", "b"]),
            "do_mul": Action(id="do_mul", capability_id="multiply", name="do_multiply", parameter_ids=["a", "b"]),
        },
        events={
            "calc_done": EventDefinition(id="calc_done", name="CalculationDone"),
        },
    )


def make_registry(adapters=None):
    reg = AdapterRegistry()
    if adapters:
        for adapter in adapters.values():
            reg.register(adapter)
    return reg


# ---------------------------------------------------------------------------
# 6A-D: Basic Projection — Node types
# ---------------------------------------------------------------------------

class TestBasicProjection:
    def test_application_node_created(self):
        store = FakeGraphStore()
        app = make_test_app()
        adapter = DynamicTestAdapter(app)
        reg = make_registry({"test_calc": adapter})
        engine = GraphProjectionEngine(reg, store)
        result = engine.project_application("test_calc")

        assert len(result["nodes"]) > 0
        app_node_id = "supl:app:test_calc:test_calc"
        assert app_node_id in store.nodes
        assert store.nodes[app_node_id]["type"] == NODE_TYPE_APPLICATION

    def test_capability_nodes_created(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        assert "supl:cap:test_calc:add" in store.nodes
        assert "supl:cap:test_calc:multiply" in store.nodes
        assert store.nodes["supl:cap:test_calc:add"]["type"] == NODE_TYPE_CAPABILITY

    def test_parameter_nodes_created(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        assert store.nodes["supl:param:test_calc:a"]["type"] == NODE_TYPE_PARAMETER
        assert store.nodes["supl:param:test_calc:b"]["type"] == NODE_TYPE_PARAMETER

    def test_action_nodes_created(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        assert store.nodes["supl:act:test_calc:do_add"]["type"] == NODE_TYPE_ACTION
        assert store.nodes["supl:act:test_calc:do_mul"]["type"] == NODE_TYPE_ACTION

    def test_state_nodes_created(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        assert store.nodes["supl:state:test_calc:last_result"]["type"] == NODE_TYPE_STATE
        assert store.nodes["supl:state:test_calc:operation_count"]["type"] == NODE_TYPE_STATE

    def test_event_nodes_created(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        assert store.nodes["supl:evt:test_calc:calc_done"]["type"] == NODE_TYPE_EVENT


# ---------------------------------------------------------------------------
# 6E: Edge mapping
# ---------------------------------------------------------------------------

class TestEdgeMapping:
    def test_has_capability_edges(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        edges = [e for e in store.edges if e.get("edge_type") == EDGE_TYPE_HAS_CAPABILITY]
        assert len(edges) == 2
        assert {e["target_id"] for e in edges} == {"supl:cap:test_calc:add", "supl:cap:test_calc:multiply"}

    def test_supports_action_edges(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        edges = [e for e in store.edges if e.get("edge_type") == EDGE_TYPE_SUPPORTS_ACTION]
        assert len(edges) == 2

    def test_uses_parameter_edges(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        edges = [e for e in store.edges if e.get("edge_type") == EDGE_TYPE_USES_PARAMETER]
        assert len(edges) == 4  # do_add uses a,b; do_mul uses a,b

    def test_has_state_edges(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        edges = [e for e in store.edges if e.get("edge_type") == EDGE_TYPE_HAS_STATE]
        assert len(edges) == 2

    def test_no_duplicate_edges(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")

        edge_set = set()
        for e in store.edges:
            key = (e.get("source_id"), e.get("target_id"), e.get("edge_type"))
            assert key not in edge_set, f"Duplicate edge: {key}"
            edge_set.add(key)

    def test_deterministic_edge_count(self):
        store1 = FakeGraphStore()
        store2 = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine1 = GraphProjectionEngine(reg, store1)
        engine2 = GraphProjectionEngine(reg, store2)
        engine1.project_application("test_calc")
        engine2.project_application("test_calc")
        assert len(store1.edges) == len(store2.edges)


# ---------------------------------------------------------------------------
# 6G: Projection Lifecycle
# ---------------------------------------------------------------------------

class TestProjectionLifecycle:
    def test_register_then_project(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        assert engine.get_projected_apps() == set()
        engine.project_application("test_calc")
        assert "test_calc" in engine.get_projected_apps()

    def test_lifecycle_projected(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        assert engine.get_lifecycle("test_calc") == LIFECYCLE_PROJECTED

    def test_lifecycle_updated_on_reproject(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        engine.project_application("test_calc")
        assert engine.get_lifecycle("test_calc") == LIFECYCLE_UPDATED

    def test_remove_application(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        removed = engine.remove_application("test_calc")
        assert removed > 0
        assert "test_calc" not in engine.get_projected_apps()
        assert engine.get_lifecycle("test_calc") == LIFECYCLE_REMOVED
        supl_nodes = [nid for nid in store.nodes if nid.startswith("supl:")]
        assert len(supl_nodes) == 0

    def test_remove_non_existent(self):
        store = FakeGraphStore()
        reg = make_registry({})
        engine = GraphProjectionEngine(reg, store)
        assert engine.remove_application("ghost") == 0

    def test_reproject_after_remove(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        engine.remove_application("test_calc")
        engine.project_application("test_calc")
        assert engine.get_lifecycle("test_calc") == LIFECYCLE_REPROJECTED
        supl_nodes = [nid for nid in store.nodes if nid.startswith("supl:")]
        assert len(supl_nodes) > 0

    def test_reset_clears_all_supl_nodes(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        engine.reset()
        supl_nodes = [nid for nid in store.nodes if nid.startswith("supl:")]
        assert len(supl_nodes) == 0
        assert engine.get_projected_apps() == set()


# ---------------------------------------------------------------------------
# 6N: Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_repeated_projection_no_duplicate_nodes(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        n_before = len(store.nodes)
        engine.project_application("test_calc")
        assert len(store.nodes) == n_before

    def test_repeated_projection_same_edge_count(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        e_before = len(store.edges)
        engine.project_application("test_calc")
        assert len(store.edges) == e_before

    def test_sync_application_idempotent(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        n, e = len(store.nodes), len(store.edges)
        engine.sync_application("test_calc")
        assert len(store.nodes) == n
        assert len(store.edges) == e

    def test_multiple_applications_dont_collide(self):
        store = FakeGraphStore()
        app1 = make_test_app("app1")
        app2 = make_test_app("app2")
        reg = make_registry({
            "app1": DynamicTestAdapter(app1),
            "app2": DynamicTestAdapter(app2),
        })
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("app1")
        engine.project_application("app2")
        assert "supl:app:app1:app1" in store.nodes
        assert "supl:app:app2:app2" in store.nodes


# ---------------------------------------------------------------------------
# 6H: Identity / Semantic Source
# ---------------------------------------------------------------------------

class TestProjectionIdentity:
    def test_stable_node_ids(self):
        store1, store2 = FakeGraphStore(), FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine1 = GraphProjectionEngine(reg, store1)
        engine2 = GraphProjectionEngine(reg, store2)
        engine1.project_application("test_calc")
        engine2.project_application("test_calc")
        assert sorted(store1.nodes.keys()) == sorted(store2.nodes.keys())

    def test_semantic_source_metadata(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        meta = store.nodes["supl:app:test_calc:test_calc"]["payload"]["metadata"]
        assert meta["semantic_source"]["application_id"] == "test_calc"
        assert meta["projection_id"] == GRAPH_PROJECTION_VERSION
        assert meta["source_authority"] == SOURCE_AUTHORITY

    def test_projection_id_stable(self):
        store1, store2 = FakeGraphStore(), FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        GraphProjectionEngine(reg, store1).project_application("test_calc")
        GraphProjectionEngine(reg, store2).project_application("test_calc")
        id1 = store1.nodes["supl:app:test_calc:test_calc"]["payload"]["metadata"]["projection_id"]
        id2 = store2.nodes["supl:app:test_calc:test_calc"]["payload"]["metadata"]["projection_id"]
        assert id1 == id2


# ---------------------------------------------------------------------------
# 6J: Trust boundary — PROJECTED != EXECUTED
# ---------------------------------------------------------------------------

class TestTrustBoundary:
    def test_all_nodes_are_projected_not_executed(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        for nid, node in store.nodes.items():
            evidence = node["payload"].get("evidence_classification", "")
            assert evidence == EVIDENCE_PROJECTED, (
                f"Node {nid} has evidence {evidence}, expected PROJECTED"
            )

    def test_no_execution_evidence_in_payload(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        for node in store.nodes.values():
            p = node["payload"]
            assert "execution_id" not in p or p.get("execution_id") is None
            assert "receipt_id" not in p or p.get("receipt_id") is None

    def test_simulated_not_executed(self):
        store = FakeGraphStore()
        app = make_test_app("sim_app")
        reg = make_registry({"sim_app": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("sim_app")
        for node in store.nodes.values():
            e = node["payload"].get("evidence_classification", "")
            assert e != EVIDENCE_EXECUTED
            assert e != EVIDENCE_SIMULATED
            assert e != EVIDENCE_VERIFIED


# ---------------------------------------------------------------------------
# 6M: Provenance — no fabricated IDs
# ---------------------------------------------------------------------------

class TestProvenanceBoundary:
    def test_no_fabricated_execution_id(self):
        store = FakeGraphStore()
        reg = make_registry({"test_calc": DynamicTestAdapter(make_test_app())})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        for node in store.nodes.values():
            p = node["payload"]
            assert p.get("execution_id") is None or p["execution_id"] == ""
            assert p.get("receipt_id") is None or p["receipt_id"] == ""
            assert p.get("verification_id") is None or p["verification_id"] == ""

    def test_absent_evidence_is_none(self):
        store = FakeGraphStore()
        reg = make_registry({"test_calc": DynamicTestAdapter(make_test_app())})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        for node in store.nodes.values():
            p = node["payload"]
            assert "receipt_id" not in p or p.get("receipt_id") is None


# ---------------------------------------------------------------------------
# 6P: Adversarial tests
# ---------------------------------------------------------------------------

class TestAdversarial:
    def test_duplicate_application_registration(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        engine.project_application("test_calc")
        app_nodes = [n for n in store.nodes.values() if n["type"] == NODE_TYPE_APPLICATION]
        assert len(app_nodes) == 1

    def test_missing_capability(self):
        store = FakeGraphStore()
        app = make_test_app()
        app.capabilities = {}
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        cap_nodes = [n for n in store.nodes.values() if n["type"] == NODE_TYPE_CAPABILITY]
        assert len(cap_nodes) == 0

    def test_missing_action(self):
        store = FakeGraphStore()
        app = make_test_app()
        app.actions = {}
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        act_nodes = [n for n in store.nodes.values() if n["type"] == NODE_TYPE_ACTION]
        assert len(act_nodes) == 0

    def test_unknown_adapter_projection(self):
        store = FakeGraphStore()
        reg = make_registry({})
        engine = GraphProjectionEngine(reg, store)
        with pytest.raises(ValueError, match="adapter not found"):
            engine.project_application("unknown_app")

    def test_projection_after_adapter_unregister(self):
        store = FakeGraphStore()
        app = make_test_app()
        adapter = DynamicTestAdapter(app)
        reg = make_registry({"test_calc": adapter})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        reg.unregister("test_calc")
        with pytest.raises(ValueError, match="adapter not found"):
            engine.project_application("test_calc")

    def test_projection_replay_consistency(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        r1 = engine.project_application("test_calc")
        r2 = engine.project_application("test_calc")
        assert len(r1["nodes"]) == len(r2["nodes"])
        assert len(r1["edges"]) == len(r2["edges"])

    def test_stale_app_does_not_affect_other_apps(self):
        store = FakeGraphStore()
        app1 = make_test_app("app1")
        app2 = make_test_app("app2")
        reg = make_registry({
            "app1": DynamicTestAdapter(app1),
            "app2": DynamicTestAdapter(app2),
        })
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("app1")
        engine.project_application("app2")
        engine.remove_application("app1")
        app1_nodes = [nid for nid in store.nodes if ":app1:" in nid]
        app2_nodes = [nid for nid in store.nodes if ":app2:" in nid]
        assert len(app1_nodes) == 0
        assert len(app2_nodes) > 0

    def test_graph_mutation_does_not_affect_semantic_model(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        orig_cap_count = len(app.capabilities)
        store.nodes["supl:cap:test_calc:add"]["payload"]["fabricated"] = True
        assert len(app.capabilities) == orig_cap_count


# ---------------------------------------------------------------------------
# 6L: No direct executor access
# ---------------------------------------------------------------------------

class TestNoExecutorAccess:
    def test_engine_has_no_executor_reference(self):
        source = inspect.getsource(GraphProjectionEngine)
        for forbidden in ["UnifiedToolRuntime", "SafetyGate", "executor", "tool_runtime"]:
            lines = [l for l in source.splitlines()
                     if forbidden in l and not l.strip().startswith("#")]
            assert len(lines) == 0, (
                f"GraphProjectionEngine references executor authority '{forbidden}'"
            )


# ---------------------------------------------------------------------------
# 6Q: Adapter API boundary
# ---------------------------------------------------------------------------

class TestAdapterBoundary:
    def test_project_via_adapter(self):
        store = FakeGraphStore()
        app = make_test_app()
        adapter = DynamicTestAdapter(app)
        reg = make_registry({"test_calc": adapter})
        engine = GraphProjectionEngine(reg, store)
        result = engine.project_adapter(adapter)
        assert len(result["nodes"]) > 0
        assert "supl:app:test_calc:test_calc" in store.nodes

    def test_projection_contains_all_expected_types(self):
        store = FakeGraphStore()
        app = make_test_app()
        reg = make_registry({"test_calc": DynamicTestAdapter(app)})
        engine = GraphProjectionEngine(reg, store)
        engine.project_application("test_calc")
        types_in_store = set(n["type"] for n in store.nodes.values())
        expected = {NODE_TYPE_APPLICATION, NODE_TYPE_CAPABILITY, NODE_TYPE_PARAMETER,
                    NODE_TYPE_ACTION, NODE_TYPE_STATE, NODE_TYPE_EVENT}
        missing = expected - types_in_store
        assert not missing, f"Missing node types in projection: {missing}"
