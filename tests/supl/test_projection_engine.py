import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from features.supl.projection_engine import (
    UIMode, ProjectionState, ProjectionContext, UIProjection, ProjectionEngine,
)
from features.supl.semantic_model import SemanticApplication, Capability, Action
from features.supl.adapter_registry import AdapterRegistry
from features.supl.test_adapter import TestCalculatorAdapter


@pytest.fixture
def registry():
    r = AdapterRegistry()
    r.register(TestCalculatorAdapter())
    return r


@pytest.fixture
def engine(registry):
    return ProjectionEngine(registry)


def test_ui_mode_values():
    assert UIMode.NATIVE.value == "native"
    assert UIMode.OVERLAY.value == "overlay"
    assert UIMode.GRAPH_NATIVE.value == "graph_native"


def test_projection_state_values():
    assert ProjectionState.SYNCED.value == "synced"
    assert ProjectionState.STALE.value == "stale"
    assert ProjectionState.ERROR.value == "error"
    assert ProjectionState.LOADING.value == "loading"


def test_projection_context_defaults():
    ctx = ProjectionContext()
    assert ctx.user == ""
    assert ctx.role == ""
    assert ctx.permissions == set()


def test_projection_context_serialization():
    ctx = ProjectionContext(user="alice", role="admin", task="add numbers",
                            permissions={"execute", "view"}, current_state={"a": 1})
    d = ctx.to_dict()
    assert d["user"] == "alice"
    assert "execute" in d["permissions"]
    restored = ProjectionContext.from_dict(d)
    assert restored.user == "alice"
    assert "execute" in restored.permissions


def test_ui_projection_defaults():
    proj = UIProjection(mode=UIMode.OVERLAY, application_id="test")
    assert proj.mode == UIMode.OVERLAY
    assert proj.projection_state == ProjectionState.SYNCED


def test_ui_projection_mark_stale():
    proj = UIProjection(mode=UIMode.OVERLAY, application_id="test")
    proj.mark_stale()
    assert proj.projection_state == ProjectionState.STALE


def test_ui_projection_mark_synced():
    proj = UIProjection(mode=UIMode.OVERLAY, application_id="test")
    proj.mark_stale()
    proj.mark_synced()
    assert proj.projection_state == ProjectionState.SYNCED
    assert proj.last_sync_timestamp > 0


def test_ui_projection_serialization():
    proj = UIProjection(mode=UIMode.GRAPH_NATIVE, application_id="app1",
                        application_name="App One", capabilities=[{"id": "cap1"}])
    proj.mark_stale()
    d = proj.to_dict()
    assert d["mode"] == "graph_native"
    assert d["projection_state"] == "stale"
    restored = UIProjection.from_dict(d)
    assert restored.mode == UIMode.GRAPH_NATIVE
    assert restored.projection_state == ProjectionState.STALE


def test_project_unknown_app(engine):
    proj = engine.project("nonexistent")
    assert proj.projection_state == ProjectionState.ERROR
    assert "not found" in proj.filter_reason


def test_project_overlay_mode(engine):
    proj = engine.project("test_calculator", None, UIMode.OVERLAY)
    assert proj.application_id == "test_calculator"
    assert proj.mode == UIMode.OVERLAY
    assert proj.projection_state == ProjectionState.SYNCED
    assert len(proj.capabilities) > 0
    assert len(proj.actions) > 0
    assert len(proj.parameters) > 0


def test_project_native_mode(engine):
    proj = engine.project("test_calculator", None, UIMode.NATIVE)
    assert proj.mode == UIMode.NATIVE
    assert proj.filtered is True
    assert len(proj.capabilities) == 0
    assert len(proj.parameters) == 0
    assert len(proj.actions) == 0


def test_project_graph_native_mode(engine):
    proj = engine.project("test_calculator", None, UIMode.GRAPH_NATIVE)
    assert proj.mode == UIMode.GRAPH_NATIVE
    assert len(proj.capabilities) > 0
    assert len(proj.parameters) > 0
    assert len(proj.actions) > 0


def test_context_aware_filtering(engine):
    ctx = ProjectionContext(task="add numbers")
    proj = engine.project("test_calculator", ctx, UIMode.OVERLAY)
    assert proj.filtered is True or len(proj.capabilities) > 0


def test_list_applications(engine):
    apps = engine.list_available_applications()
    assert len(apps) == 1
    assert apps[0]["application_id"] == "test_calculator"


def test_invalidate_cache(engine):
    engine._cache["test_calculator"] = {"data": "old"}
    engine.invalidate_cache("test_calculator")
    assert "test_calculator" not in engine._cache


def test_invalidate_all_cache(engine):
    engine._cache["a"] = {}
    engine._cache["b"] = {}
    engine.invalidate_cache()
    assert len(engine._cache) == 0


def test_projection_state_enum_values():
    assert ProjectionState.SYNCED != ProjectionState.STALE
    assert ProjectionState.STALE != ProjectionState.ERROR
    assert ProjectionState.ERROR != ProjectionState.LOADING


def test_mode_switching_preserves_semantics(engine):
    overlay = engine.project("test_calculator", None, UIMode.OVERLAY)
    native = engine.project("test_calculator", None, UIMode.NATIVE)
    graph = engine.project("test_calculator", None, UIMode.GRAPH_NATIVE)
    assert overlay.application_id == native.application_id == graph.application_id
    assert overlay.application_name == native.application_name == graph.application_name


def test_projection_sync_state(engine):
    proj = engine.project("test_calculator")
    assert proj.projection_state == ProjectionState.SYNCED
    assert proj.last_sync_timestamp > 0
    proj.mark_stale()
    assert proj.projection_state == ProjectionState.STALE
