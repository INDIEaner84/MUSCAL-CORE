import os

os.makedirs("storage", exist_ok=True)


def test_core_imports():
    from config import BASE_DIR, DB_PATH, get_session_id
    from event_bus import EventBus, EventMessage, EventPriority
    from kernel import MuscalKernel
    from memory import (
        _get_conn,
        get_recent,
        init,
        retrieve_by_id,
        search_by_keyword,
        store,
        store_snapshot,
    )
    from mkc import mkc
    from mkc_rules import classify_statement, extract_tool, reset_state
    from plugin_loader import load_plugins, validate_plugin
    from plugin_registry import HOOKS, PLUGINS, STAGES, build_pipeline, register_stage, run_hooks
    from schema import detect_old_format, validate_mcxf


def test_config_lazy_init():
    from config import get_session_id
    sid = get_session_id()
    assert sid is not None
    assert sid.startswith("session_")
    assert len(sid) > 10


def test_memory_lazy_init():
    import memory
    memory._conn = None
    conn = memory._get_conn()
    assert conn is not None
    memory.init()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "memory" in tables
    assert "mcxf_snapshots" in tables
    cursor.execute("DELETE FROM memory")
    memory.store("test_plan", "test_result")
    cursor.execute("SELECT COUNT(*) FROM memory")
    assert cursor.fetchone()[0] == 1


def test_plugin_registry_stages():
    from plugin_registry import STAGES, build_pipeline, register_stage, run_hooks
    STAGES.clear()

    class StageA:
        name = "stage_a"
        order = 10
        def process(self, ctx): return ctx

    class StageB:
        name = "stage_b"
        order = 20
        def process(self, ctx): return ctx

    class StageC:
        name = "stage_c"
        order = 30
        def process(self, ctx): return ctx

    register_stage(StageA())
    register_stage(StageC())
    register_stage(StageB())

    pipeline = build_pipeline()
    assert len(pipeline) == 3
    assert pipeline[0].name == "stage_a"
    assert pipeline[1].name == "stage_b"
    assert pipeline[2].name == "stage_c"


def test_plugin_registry_stage_before_after():
    from plugin_registry import STAGES, build_pipeline, register_stage
    STAGES.clear()

    class BaseStage:
        name = "base"
        order = 100
        def process(self, ctx): return ctx

    class BeforeStage:
        name = "before_base"
        order = 0
        def process(self, ctx): return ctx

    class AfterStage:
        name = "after_base"
        order = 0
        def process(self, ctx): return ctx

    register_stage(BaseStage())
    before = BeforeStage()
    register_stage(before, before="base")
    after = AfterStage()
    register_stage(after, after="base")

    pipeline = build_pipeline()
    names = [s.name for s in pipeline]
    assert names == ["before_base", "base", "after_base"], f"Got {names}"


def test_plugin_registry_stage_raises_on_both():
    from plugin_registry import register_stage
    class S:
        name = "bad"
        order = 0
        def process(self, ctx): return ctx
    import pytest
    with pytest.raises(ValueError, match="both"):
        register_stage(S(), before="x", after="y")


def test_plugin_registry_build_pipeline_filter():
    from plugin_registry import STAGES, build_pipeline, register_stage
    STAGES.clear()
    class S:
        name = "only_me"
        order = 1
        def process(self, ctx): return ctx
    register_stage(S())
    filtered = build_pipeline(["only_me"])
    assert len(filtered) == 1
    assert filtered[0].name == "only_me"
    filtered = build_pipeline(["nonexistent"])
    assert len(filtered) == 0


def test_plugin_registry_hooks():
    from plugin_registry import HOOKS, PLUGINS, run_hooks
    PLUGINS.clear()
    for k in HOOKS:
        HOOKS[k].clear()
    expected = {
        "kernel_before", "kernel_after",
        "mkc_before", "mkc_after",
        "bridge_before", "bridge_after",
        "optimizer_before", "optimizer_after",
        "mel_before", "mel_after",
        "feedback_before", "feedback_after",
        "memory_before", "memory_after",
    }
    # Remove any keys added by prior plugin loads (e.g. check_auth)
    for k in list(HOOKS.keys()):
        if k not in expected:
            del HOOKS[k]
    assert set(HOOKS.keys()) == expected, f"Hooks: {set(HOOKS.keys())}"
    from plugin_loader import load_plugins
    load_plugins()
    assert len(PLUGINS) >= 1, f"Plugins loaded: {len(PLUGINS)}"
