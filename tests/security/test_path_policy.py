import os
from tools import write, ALLOWED_WRITE_PATHS


class TestPathPolicy:
    def test_path_traversal_denied(self):
        result = write("../../etc/passwd", "evil")
        assert result["status"] == "blocked"

    def test_system_path_denied(self):
        result2 = write("/etc/cron.d/evil", "evil")
        assert result2["status"] == "blocked"

    def test_allowed_tmp_path_succeeds(self):
        tmp_path = "/tmp/muscal_test_write.txt"
        result3 = write(tmp_path, "hello security test")
        assert result3["status"] == "written"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    def test_oversized_content_blocked(self):
        result4 = write("/tmp/muscal_test_big.txt", "x" * (1_048_576 + 1))
        assert result4["status"] == "blocked"

    def test_blocked_write_returns_dict(self):
        result = write("../../etc/passwd", "evil")
        assert isinstance(result, dict)
        assert "status" in result

    def test_allowed_write_paths_contain_storage(self):
        assert any("storage" in p for p in ALLOWED_WRITE_PATHS)
