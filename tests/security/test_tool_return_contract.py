import os
from tools import write, add, print_console


class TestToolReturnContract:
    def test_blocked_tool_returns_dict(self):
        result = write("/etc/passwd", "evil")
        assert isinstance(result, dict)
        assert "status" in result
        assert "error" in result

    def test_successful_tool_returns_dict(self):
        tmp = "/tmp/muscal_contract_test.txt"
        result2 = write(tmp, "ok")
        assert isinstance(result2, dict)
        assert result2["status"] == "written"
        if os.path.exists(tmp):
            os.remove(tmp)

    def test_math_add_returns_dict(self):
        result3 = add(2, 3)
        assert isinstance(result3, dict)
        assert "result" in result3

    def test_console_print_returns_dict(self):
        result4 = print_console("contract test")
        assert isinstance(result4, dict)
        assert "printed" in result4
