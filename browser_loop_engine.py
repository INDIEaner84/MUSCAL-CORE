from browser_engine import BrowserEngine
from browser_executor import BrowserExecutor
from browser_planner import BrowserPlanner
from safe_browser_agent import SafeBrowserAgent


class BrowserLoopEngine:
    def __init__(self, planner, executor, memory, rag):
        self.planner = planner
        self.executor = executor
        self.memory = memory
        self.rag = rag

    def run(self, task):
        plan = self.planner.create_plan(task)
        results = []
        step = plan.next()
        while step:
            result = self.executor.run_step(step)
            results.append({"step": step, "result": result})
            if result.get("status") == "BLOCKED":
                break
            step = plan.next()
        if self.memory:
            self.memory.add({
                "type": "BROWSER_PLAN_EXECUTION",
                "task": task,
                "results": results,
            })
        if self.rag:
            self.rag.add(str(results))
        return results


_browser_engine = None
_safe_agent = None
_loop = None


def init_browser_loop_engine(memory=None, rag=None, headless=False):
    global _browser_engine, _safe_agent, _loop
    if _loop is not None:
        return
    from mcxf_fusion import get_fusion_layer, init_fusion
    fusion = get_fusion_layer()
    if fusion is None:
        init_fusion()
    fusion = get_fusion_layer()
    mem = memory or (fusion.memory if fusion else None)
    r = rag or (fusion.rag if fusion else None)
    _browser_engine = BrowserEngine(headless=headless)
    _safe_agent = SafeBrowserAgent(_browser_engine)
    planner = BrowserPlanner()
    executor = BrowserExecutor(_safe_agent)
    _loop = BrowserLoopEngine(planner, executor, mem, r)


def run_browser_planning(task):
    if _loop is None:
        init_browser_loop_engine()
    return _loop.run(task)
