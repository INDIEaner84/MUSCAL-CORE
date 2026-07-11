import json
import os
import time

MAX_FAILURES = 3
WINDOW_SECONDS = 300


class Plugin:
    name = "health_monitor"

    def __init__(self):
        self._failures = {}
        self._hooks = {}

    def register(self, hooks):
        self._hooks = hooks
        add_listener = hooks.get("_add_health_listener")
        if add_listener:
            add_listener(self._on_plugin_failure)
        hooks.setdefault("kernel_before", []).append(self._check_health)

    def _on_plugin_failure(self, event):
        hook = event.get("hook", "?")
        plugin = event.get("plugin", "?")
        now = time.time()
        key = f"{hook}:{plugin}"
        if key not in self._failures:
            self._failures[key] = []
        self._failures[key].append(now)
        self._failures[key] = [t for t in self._failures[key] if now - t < WINDOW_SECONDS]
        count = len(self._failures[key])
        os.makedirs("storage", exist_ok=True)
        entry = {
            "timestamp": now,
            "hook": hook,
            "plugin": plugin,
            "failures_in_window": count,
            "action": "logged",
        }
        if count >= MAX_FAILURES:
            self._auto_disable(event)
            entry["action"] = "disabled"
        with open("storage/health.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _auto_disable(self, event):
        hook = event.get("hook", "?")
        if hook in self._hooks:
            self._hooks[hook].clear()

    def _check_health(self, ctx):
        stale = [k for k, v in self._failures.items()
                 if time.time() - v[-1] > WINDOW_SECONDS * 2]
        for k in stale:
            del self._failures[k]

    def execute(self, context):
        pass
