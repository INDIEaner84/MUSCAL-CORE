import os
import time
from features.runtime_canonical import (
    init_canonical_runtime,
    get_auth_token,
    is_auth_required,
    is_server_ready,
    set_server_ready,
    get_security_headers,
    check_tool_via_kernel,
    RUNTIME_CANONICAL_STATUS,
)


class TestCanonicalRuntimeInit:
    def test_r1_canonical_initializes(self):
        init_canonical_runtime()
        state = get_security_headers()
        assert "Strict-Transport-Security" in state
        assert RUNTIME_CANONICAL_STATUS == "ACTIVE"

    def test_r2_server_ready_state(self):
        init_canonical_runtime()
        assert is_server_ready() is False
        set_server_ready(True)
        assert is_server_ready() is True
        set_server_ready(False)

    def test_r3_auth_check(self):
        init_canonical_runtime()
        assert is_auth_required("/health", "GET") is False
        assert is_auth_required("/state", "GET") is False
        assert is_auth_required("/live", "GET") is False
        assert is_auth_required("/api/tasks", "OPTIONS") is False

    def test_r4_security_headers_consistency(self):
        init_canonical_runtime()
        headers = get_security_headers()
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-XSS-Protection"] == "0"
        assert "Content-Security-Policy" in headers
        assert "Referrer-Policy" in headers

    def test_r5_kernel_tool_check_no_runtime(self):
        init_canonical_runtime()
        result = check_tool_via_kernel("console.print", {"message": "hello"})
        assert result["status"] == "no_runtime"

    def test_r6_kernel_tool_check_with_runtime(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        init_canonical_runtime(tool_runtime=utr, safety_gate=sg)
        result = check_tool_via_kernel("console.print", {"message": "hi"})
        assert result["status"] == "success"

    def test_r7_kernel_safety_blocks(self):
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        init_canonical_runtime(safety_gate=sg)
        result = check_tool_via_kernel("opencode.run", {"command": "ls"})
        assert result["status"] == "blocked_by_safety"

    def test_r8_auth_token_consistency(self):
        init_canonical_runtime()
        expected = os.environ.get("MUSCAL_API_KEY", "")
        if not expected:
            try:
                import config
                expected = getattr(config, "SESSION_ID", "")
            except (ImportError, AttributeError):
                expected = ""
        if expected:
            assert get_auth_token() == expected

    def test_r9_api_server_imports(self):
        try:
            from api_server import app, health, ready, live, version
            assert app.title == "MUSCAL Control Plane"
        except (ImportError, Exception) as e:
            assert False, f"api_server import failed: {e}"

    def test_r10_dual_runtime_no_conflict(self):
        from features.runtime_canonical import get_shared_state
        init_canonical_runtime()
        state1 = get_shared_state()
        time.sleep(0.01)
        init_canonical_runtime()
        state2 = get_shared_state()
        assert state2["start_time"] >= state1["start_time"]
