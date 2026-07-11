from mel import execute
from schema import ExecutionPlan


class TestMelBasicExecution:
    def test_console_print_via_execution_plan(self):
        plan = ExecutionPlan(intent="print hello", steps=[
            {"tool": "console.print", "args": {"message": "hello world"}}
        ])
        results = execute(plan)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], dict)

    def test_unmapped_step_returns_skipped(self):
        plan2 = ExecutionPlan(intent="unknown", steps=[
            {"tool": "UNMAPPED", "original_task": "do something", "reason": "No match"}
        ])
        results2 = execute(plan2)
        assert len(results2) == 1
        assert results2[0].get("status") == "skipped"

    def test_mixed_steps(self):
        plan3 = ExecutionPlan(intent="mixed", steps=[
            {"tool": "console.print", "args": {"message": "first"}},
            {"tool": "UNMAPPED", "original_task": "do x", "reason": "No match"},
            {"tool": "console.print", "args": {"message": "third"}},
        ])
        results3 = execute(plan3)
        assert len(results3) == 3
        assert results3[0].get("status") in ("completed", "ok", "success", None)
        assert results3[1].get("status") == "skipped"

    def test_plan_as_list(self):
        plan4 = [
            {"tool": "math.add", "args": {"a": 2, "b": 3}},
        ]
        results4 = execute(plan4)
        assert len(results4) == 1
        assert results4[0].get("result") == 5
