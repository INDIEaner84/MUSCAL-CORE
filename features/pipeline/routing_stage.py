import threading

from runtime.kernel.scheduler import RoutingPolicy


_TASK_TYPE_KEYWORDS = {
    "write": "filesystem_write",
    "print": "print_console",
    "add": "arithmetic",
    "calculate": "arithmetic",
    "search": "web_search",
    "browse": "browser_navigation",
    "click": "browser_interaction",
    "screenshot": "browser_screenshot",
    "extract": "data_extraction",
    "summarize": "text_summarization",
    "translate": "translation",
    "shell": "shell_execute",
    "execute": "shell_execute",
}


class RoutingStage:
    name = "routing"
    order = 25

    def __init__(self, kernel):
        self.k = kernel
        self._policy = None
        self._lock = threading.Lock()

    def _get_policy(self):
        if self._policy is None:
            self._policy = RoutingPolicy()
        return self._policy

    def _derive_task_type(self, ctx):
        mcxf_dict = ctx.get("mcxf_dict", {})
        tasks = mcxf_dict.get("tasks", [])
        if not tasks:
            tasks = mcxf_dict.get("decisions", [])
        for task in tasks:
            predicate = (task.get("predicate", "") if isinstance(task, dict)
                         else getattr(task, "predicate", ""))
            obj = (task.get("object", "") if isinstance(task, dict)
                   else getattr(task, "object", ""))
            combined = f"{predicate} {obj}".lower()
            for keyword, task_type in _TASK_TYPE_KEYWORDS.items():
                if keyword in combined:
                    return task_type, True
        return "general", False

    def _detect_agent(self, ctx):
        from features.agent_detection.detector import DEFAULT_DETECTOR
        task_type = ctx.get("routing_task_type", "general")
        result = DEFAULT_DETECTOR.detect(
            task_type=task_type,
            mcxf_dict=ctx.get("mcxf_dict", {}),
            routing_metadata={"worker": ctx.get("routing_worker", "")},
        )
        return result

    def process(self, ctx):
        policy = self._get_policy()
        task_type, known = self._derive_task_type(ctx)
        worker = policy.route(task_type)
        detection = self._detect_agent(ctx)

        ctx["routing_task_type"] = task_type
        ctx["routing_decision"] = worker
        ctx["routing_worker"] = worker
        ctx["routing_status"] = "routed" if known else "unknown"
        ctx["agent_type"] = detection.agent_type
        ctx["agent_detection"] = detection
        return ctx
