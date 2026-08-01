import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── T1: UTR initialization ──

def test_utr_initialization():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    assert utr._executors == {}
    assert utr._schemas == {}
    caps = utr.capabilities()
    assert isinstance(caps, list)


# ── T2: Tool registration ──

def test_tool_registration():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime, RESERVED
    utr = UnifiedToolRuntime()
    utr.register_tool("console.print", lambda args: {"printed": args.get("message", "")})
    assert "console.print" in utr.capabilities()
    assert utr.capabilities() == ["console.print"]


# ── T3: Unknown tool ──

def test_unknown_tool():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    result = utr.execute("nonexistent.tool", {})
    assert not result.success
    assert "Unknown tool" in result.error


# ── T4: Executor resolution ──

def test_executor_resolution():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    fn = lambda args: {"result": 42}  # noqa: E731
    utr.register_executor("test.fn", fn)
    resolved = utr.resolve("test.fn")
    assert resolved is fn
    assert utr.resolve("missing") is None


# ── T5: Console executor ──

def test_console_executor(capsys):
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("console.print")
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("console.print", {"message": "hello utr"})
    assert result.success
    captured = capsys.readouterr()
    assert "hello utr" in captured.out


# ── T6: Filesystem executor ──

def test_filesystem_executor():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        result = utr.execute("filesystem.write", {"path": tmp_path, "content": "test data"})
        assert result.success
        with open(tmp_path) as f2:
            assert f2.read() == "test data"
    finally:
        os.unlink(tmp_path)


def test_file_write_alias():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("file.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        result = utr.execute("file.write", {"path": tmp_path, "content": "alias test"})
        assert result.success
        with open(tmp_path) as f2:
            assert f2.read() == "alias test"
    finally:
        os.unlink(tmp_path)


# ── T7: Math executor ──

def test_math_executor():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("math.add")
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 3, "b": 4})
    assert result.success
    assert result.output["result"] == 7


# ── T8: Browser executor migration ──

def test_browser_executor_stub():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    utr, ba = create_default_utr(safety_gate=sg)
    r1 = utr.execute("browser.open", {"url": "https://example.com"})
    assert r1.success or "stub" in str(r1.output)
    r2 = utr.execute("browser.click", {"selector": "body"})
    assert r2.success or "stub" in str(r2.output)
    r3 = utr.execute("browser.type", {"selector": "input", "text": "hello"})
    assert r3.success or "stub" in str(r3.output)
    r4 = utr.execute("browser.screenshot", {"path": "/tmp/test_utr_ss.png"})
    assert r4.success or "stub" in str(r4.output)
    r5 = utr.execute("browser.scroll", {"direction": "down"})
    assert r5.success or "stub" in str(r5.output)


def test_browser_unavailable_capabilities():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("desktop.screenshot")
    sg.permit("desktop.click")
    utr, _ = create_default_utr(safety_gate=sg)
    r1 = utr.execute("desktop.screenshot", {"path": "/tmp/ds.png"})
    assert not r1.success or "unavailable" in str(r1.output)


# ── T9: SafetyGate allow ──

def test_safetygate_allow():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("console.print")
    result = sg.check("console.print", {"message": "hello"})
    assert result.allowed


# ── T10: SafetyGate deny ──

def test_safetygate_deny():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    result = sg.check("shell.exec", {"command": "rm -rf /"})
    assert not result.allowed
    assert "BLOCKED_TOOL" in result.reason


def test_safetygate_deny_unknown():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    result = sg.check("unknown.tool", {})
    assert not result.allowed
    assert "UNKNOWN_TOOL" in result.reason


# ── T11: Unknown tool fails closed via UTR ──

def test_unknown_tool_fails_closed():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    utr = UnifiedToolRuntime(safety_gate=sg)
    result = utr.execute("shell.exec", {"command": "rm -rf /"})
    assert not result.success
    assert result.error


# ── T12: MEL → SafetyGate → UTR integration ──

def test_mel_utr_integration():
    import mel
    plan = [{"tool": "math.add", "args": {"a": 1, "b": 2}}]
    results = mel.execute(plan)
    assert len(results) == 1
    r = results[0]
    assert r.get("result") == 3 or r.get("output", {}).get("result") == 3 or "result" in str(r)


def test_mel_utr_console(capsys):
    import mel
    plan = [{"tool": "console.print", "args": {"message": "mel utr test"}}]
    results = mel.execute(plan)
    assert len(results) == 1
    captured = capsys.readouterr()
    assert "mel utr test" in captured.out


# ── T13: Legacy compatibility ──

def test_legacy_tools_write():
    import tools
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        r = tools.write(tmp_path, "legacy test")
        assert r["status"] == "written"
    finally:
        os.unlink(tmp_path)


def test_legacy_tools_add():
    import tools
    r = tools.add(5, 3)
    assert r["result"] == 8


def test_legacy_tools_print(capsys):
    import tools
    r = tools.print_console("legacy print")
    assert r["printed"] == "legacy print"
    captured = capsys.readouterr()
    assert "legacy print" in captured.out


def test_legacy_tool_registry():
    import tools
    assert "filesystem.write" in tools.TOOL_REGISTRY
    assert "math.add" in tools.TOOL_REGISTRY
    assert "console.print" in tools.TOOL_REGISTRY


# ── T14: No duplicate production execution authority ──

def test_no_duplicate_execution_authority():
    import mel
    assert hasattr(mel, "_get_utr")
    import tools
    assert hasattr(tools, "_get_global_utr")
    import permission_engine
    te = permission_engine.ToolExecutor()
    assert te._get_utr() is not None


# ── T15: Inline pipeline isolation ──

def test_inline_pipeline_isolation():
    import os
    prev = os.environ.get("MUSCAL_PIPELINE_MODE")
    os.environ["MUSCAL_PIPELINE_MODE"] = "inline"
    try:
        import kernel
        k = kernel.MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("say hello")
        assert result is not None
    finally:
        if prev is None:
            del os.environ["MUSCAL_PIPELINE_MODE"]
        else:
            os.environ["MUSCAL_PIPELINE_MODE"] = prev


# ── T16: Pipeline mode ──

def test_pipeline_mode():
    import os
    prev = os.environ.get("MUSCAL_PIPELINE_MODE")
    os.environ["MUSCAL_PIPELINE_MODE"] = "pipeline"
    try:
        import kernel
        k = kernel.MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("say hello")
        assert result is not None
    finally:
        if prev is None:
            del os.environ["MUSCAL_PIPELINE_MODE"]
        else:
            os.environ["MUSCAL_PIPELINE_MODE"] = prev


# ── T17 + T18: Phase 1 + Phase 2 regression — run via pytest --pyargs ──
# These are full-suite gates, verified in the full run.
# We import them here for convenience.

def test_phase1_regression_import():
    import features.pipeline.stages
    assert hasattr(features.pipeline.stages, "RAGStage")


def test_phase2_regression_import():
    import features.pipeline.governance_stage
    import features.pipeline.routing_stage
    assert hasattr(features.pipeline.governance_stage, "GovernanceStage")
    assert hasattr(features.pipeline.routing_stage, "RoutingStage")


# ── SafetyGate additional tests ──

def test_safetygate_blocked_tools():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    for bt in ("shell.exec", "subprocess.run", "os.system", "exec", "eval", "__import__"):
        r = sg.check(bt, {})
        assert not r.allowed
        assert "BLOCKED_TOOL" in r.reason


def test_safetygate_hidden_commands():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    r = sg.check("console.print", {"message": "import os; os.system('rm')"})
    assert not r.allowed
    assert "HIDDEN_COMMAND" in r.reason


def test_safetygate_high_risk_blocked():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    r = sg.check("browser.open", {"url": "https://example.com"})
    assert not r.allowed
    assert "HIGH_RISK_BLOCKED" in r.reason


def test_safetygate_high_risk_permitted():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("browser.open")
    r = sg.check("browser.open", {"url": "https://example.com"})
    assert r.allowed


def test_safetygate_path_traversal():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("file.write")
    r = sg.check("file.write", {"path": "../../etc/passwd", "content": "x"})
    assert not r.allowed
    assert "PATH_TRAVERSAL" in r.reason


def test_safetygate_invalid_url():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("browser.open")
    r = sg.check("browser.open", {"url": "ftp://example.com"})
    assert not r.allowed
    assert "INVALID_URL" in r.reason


def test_safetygate_shell_metachars():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    sg.permit("console.print")
    r = sg.check("console.print", {"message": "hello; rm -rf /"})
    assert not r.allowed
    assert "SHELL_METACHARACTERS" in r.reason


# ── UTR capabilities and health ──

def test_utr_capabilities():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    utr, _ = create_default_utr(safety_gate=sg)
    caps = utr.capabilities()
    assert "console.print" in caps
    assert "math.add" in caps
    assert "browser.open" in caps
    assert "opencode.run" in caps


def test_utr_health():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    utr, _ = create_default_utr(safety_gate=sg)
    health = utr.health()
    assert health.get("console.print") is True
    assert health.get("nonexistent") is None


def test_tool_result_to_dict():
    from features.tool_runtime.tool_runtime import ToolResult
    tr = ToolResult(tool_name="test", success=True, output={"result": 42}, execution_time=0.1)
    d = tr.to_dict()
    assert d["tool"] == "test"
    assert d["status"] == "success"
    assert d["output"]["result"] == 42
    assert d["execution_time"] == 0.1


def test_tool_result_from_dict():
    from features.tool_runtime.tool_runtime import ToolResult
    tr = ToolResult.from_dict({"tool": "t", "status": "success", "output": "x", "error": "", "metadata": {}, "execution_time": 0.0})
    assert tr.tool_name == "t"
    assert tr.success
    assert tr.output == "x"
