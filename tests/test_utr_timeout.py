import time

from features.tool_runtime.tool_runtime import UnifiedToolRuntime, ToolResult


class TestUTimeout:
    def test_execute_with_timeout_honored(self):
        utr = UnifiedToolRuntime()

        def slow(args):
            time.sleep(10)
            return {"status": "success"}

        utr.register_tool("slow.tool", slow, schema={"type": "object"})
        start = time.time()
        result = utr.execute("slow.tool", timeout=0.1)
        elapsed = time.time() - start
        assert elapsed < 5
        assert not result.success
        assert "TIMEOUT" in result.error

    def test_execute_without_timeout_still_works(self):
        utr = UnifiedToolRuntime()

        def fast(args):
            return {"status": "success", "value": args.get("x", 0) * 2}

        utr.register_tool("fast.tool", fast, schema={"type": "object"})
        result = utr.execute("fast.tool", args={"x": 21}, timeout=None)
        assert result.success
        assert result.output["value"] == 42

    def test_timeout_does_not_break_normal_execution(self):
        utr = UnifiedToolRuntime()

        def fn(args):
            return {"status": "success"}

        utr.register_tool("normal.tool", fn, schema={"type": "object"})
        result = utr.execute("normal.tool", timeout=5)
        assert result.success
