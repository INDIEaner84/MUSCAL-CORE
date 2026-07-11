from mkc import mkc


class TestMkcBasic:
    def test_simple_print_command(self):
        result = mkc("print hello world")
        assert isinstance(result, dict)
        assert "tasks" in result
        assert "decisions" in result
        assert len(result["tasks"]) >= 1
        assert result["tasks"][0]["predicate"] == "print"

    def test_filesystem_write_detected(self):
        result2 = mkc("write file /tmp/test.txt with content hello")
        assert any(t["predicate"] == "write file" for t in result2["tasks"])

    def test_math_add_detected(self):
        result3 = mkc("add 5 and 3")
        assert any(t["predicate"] == "add" for t in result3["tasks"])

    def test_confidence_field_present(self):
        result = mkc("print hello world")
        assert result["decisions"][0].get("confidence", 0) > 0

    def test_unknown_input_falls_back_to_print(self):
        result5 = mkc("some random text without tool match")
        assert any(t["predicate"] == "print" for t in result5["tasks"])

    def test_raw_input_handled_separately(self):
        result6 = mkc("print hello", raw_input="write file x with content y")
        assert isinstance(result6, dict)

    def test_all_sections_present(self):
        result = mkc("print hello world")
        for section in ["decisions", "tasks", "architecture", "constraints", "open_questions"]:
            assert section in result
