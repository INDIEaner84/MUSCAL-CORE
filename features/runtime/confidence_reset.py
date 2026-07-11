from mkc_rules import reset_state, get_signal_rules_snapshot

RESET_INTERVAL = 10


class Plugin:
    name = "confidence_reset"
    version = "1.0.0"

    def __init__(self):
        self._counter = 0

    def register(self, hooks):
        hooks.setdefault("kernel_after", []).append(self._check_reset)

    def _check_reset(self, ctx):
        self._counter += 1
        if self._counter >= RESET_INTERVAL:
            self._counter = 0
            snapshot = get_signal_rules_snapshot()
            total_drift = sum(abs(r["adjustment"]) for r in snapshot.values())
            if total_drift > 0.5:
                reset_state()

    def execute(self, context):
        pass
