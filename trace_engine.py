import datetime
import threading

TRACE_LEVEL_NAMES = {
    0: "CRITICAL",
    1: "STATE",
    2: "DEBUG",
    3: "NOISE",
}

LAYER_NAMES = {
    "COMPUTE": "COMPUTE",
    "EXECUTION": "EXECUTION",
    "OBSERVABILITY": "OBSERVABILITY",
}


class TraceEngine:
    def __init__(self, max_size=10000):
        self.events = []
        self.max_size = max_size
        self._lock = threading.RLock()

    def log(self, layer, event_type, payload, trace_level=1, meta=None):
        with self._lock:
            if len(self.events) >= self.max_size:
                self._drop_oldest_below_priority(trace_level)

            self.events.append({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "layer": layer,
                "type": event_type,
                "trace_level": trace_level,
                "payload": payload,
                "meta": meta or {},
            })

    def _drop_oldest_below_priority(self, current_level):
        for i in reversed(range(len(self.events))):
            ev = self.events[i]
            if ev["trace_level"] >= 3:
                self.events.pop(i)
                return
        for i in reversed(range(len(self.events))):
            ev = self.events[i]
            if ev["trace_level"] >= 2:
                self.events.pop(i)
                return
        self.events.pop(0)

    def snapshot(self):
        with self._lock:
            return list(self.events)

    def clear(self):
        with self._lock:
            self.events = []

    def print(self, title="MUSCAL KERNEL TRACE"):
        with self._lock:
            if not self.events:
                return
            print(f"\n=== {title} ===")
            for i, e in enumerate(self.events):
                lvl = TRACE_LEVEL_NAMES.get(e["trace_level"], str(e["trace_level"]))
                print(f"  [{i}] {lvl} {e['layer']}.{e['type']} -> {e['payload']}")


_TRACE = TraceEngine()
log_step = _TRACE.log
log = _TRACE.log
print_trace = _TRACE.print
reset_trace = _TRACE.clear


def trace(event, data):
    _TRACE.log("OBSERVABILITY", event, data, trace_level=0)
