from browser_engine import BrowserEngine
from browser_router import BrowserRouter
from safe_browser_agent import SafeBrowserAgent


class BrowserExecutionPipeline:
    def __init__(self, router, memory, rag):
        self.router = router
        self.memory = memory
        self.rag = rag

    def execute(self, tasks):
        results = []
        for task in tasks:
            result = self.router.run(task)
            if self.memory:
                self.memory.add({
                    "type": "BROWSER_RESULT",
                    "task": task,
                    "result": result,
                })
            if self.rag:
                self.rag.add(str(result))
            results.append(result)
        return results


_browser_engine = None
_safe_agent = None
_router = None
_pipeline = None


def init_browser_pipeline(memory=None, rag=None, headless=False):
    global _browser_engine, _safe_agent, _router, _pipeline
    if _pipeline is not None:
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
    _router = BrowserRouter(_safe_agent)
    _pipeline = BrowserExecutionPipeline(_router, mem, r)


def run_browser_tasks(mcxf_tasks):
    if _pipeline is None:
        init_browser_pipeline()
    return _pipeline.execute(mcxf_tasks)
