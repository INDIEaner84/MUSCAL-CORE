class MetricsCollector:
    def __init__(self):
        self._counters = {}
        self._gauges = {}

    def increment(self, name: str, value: int = 1):
        self._counters[name] = self._counters.get(name, 0) + value

    def gauge(self, name: str, value: float):
        self._gauges[name] = value

    def snapshot(self):
        return {"counters": dict(self._counters), "gauges": dict(self._gauges)}
