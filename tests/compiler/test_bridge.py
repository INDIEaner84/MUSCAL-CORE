from bridge import map_tasks, match_tool, validate_plan
from schema import ExecutionPlan, KnowledgeTriple, ToolMatch, Unmapped


class TestBridgeToolMatching:
    def test_filesystem_write_match(self):
        t1 = KnowledgeTriple("06_TASKS", "system", "write file", "/tmp/test.txt with content hello")
        m1 = match_tool(t1)
        assert isinstance(m1, ToolMatch)
        assert m1.name == "filesystem.write"
        assert "path" in m1.args

    def test_math_add_match(self):
        t2 = KnowledgeTriple("06_TASKS", "system", "add", "5 and 3")
        m2 = match_tool(t2)
        assert isinstance(m2, ToolMatch)
        assert m2.name == "math.add"

    def test_console_print_match(self):
        t3 = KnowledgeTriple("06_TASKS", "system", "print", "hello world")
        m3 = match_tool(t3)
        assert isinstance(m3, ToolMatch)
        assert m3.name == "console.print"

    def test_browser_open_match(self):
        t4 = KnowledgeTriple("06_TASKS", "system", "open url", "https://example.com")
        m4 = match_tool(t4)
        assert isinstance(m4, ToolMatch)
        assert m4.name == "browser.open"

    def test_unmatched_input(self):
        t5 = KnowledgeTriple("06_TASKS", "system", "do something", "undefined")
        m5 = match_tool(t5)
        assert isinstance(m5, Unmapped)
        assert "No" in m5.reason


class TestBridgeMapTasks:
    def test_map_multiple_tasks(self):
        t1 = KnowledgeTriple("06_TASKS", "system", "write file", "/tmp/test.txt with content hello")
        t2 = KnowledgeTriple("06_TASKS", "system", "add", "5 and 3")
        t3 = KnowledgeTriple("06_TASKS", "system", "print", "hello world")
        t5 = KnowledgeTriple("06_TASKS", "system", "do something", "undefined")
        plan = map_tasks([t1, t2, t3, t5])
        assert hasattr(plan, 'steps')
        assert len(plan.steps) == 4
        assert plan.steps[0]["tool"] == "filesystem.write"
        assert plan.steps[1]["tool"] == "math.add"
        assert plan.steps[2]["tool"] == "console.print"
        assert plan.steps[3]["tool"] == "UNMAPPED"


class TestBridgeValidatePlan:
    def test_valid_plan(self):
        t1 = KnowledgeTriple("06_TASKS", "system", "write file", "/tmp/test.txt with content hello")
        t2 = KnowledgeTriple("06_TASKS", "system", "add", "5 and 3")
        t3 = KnowledgeTriple("06_TASKS", "system", "print", "hello world")
        valid_plan = map_tasks([t1, t2, t3])
        validation = validate_plan(valid_plan)
        assert validation.valid
        assert len(validation.errors) == 0

    def test_empty_plan_invalid(self):
        empty_plan = ExecutionPlan(intent="test", steps=[])
        v2 = validate_plan(empty_plan)
        assert not v2.valid
        assert "no steps" in v2.errors[0].lower()
