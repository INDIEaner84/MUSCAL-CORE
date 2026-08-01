from __future__ import annotations
import os
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_HAS_PSUTIL = False
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    pass


@dataclass
class ResourceMetrics:
    latency: float = 0.0
    token_usage: int = 0
    cpu_time: float = 0.0
    ram_peak: int = 0
    cpu_percent: float = 0.0
    ram_current: int = 0


@dataclass
class MREILMetric:
    metric_id: str = ""
    execution_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    decision_id: str = ""
    agent_id: str = ""
    model_id: str = ""
    resources: ResourceMetrics = field(default_factory=ResourceMetrics)
    source: str = "mreil_capture"
    timestamp: float = 0.0


class MREILCapture:
    def __init__(self):
        self._start_time: float = 0.0
        self._start_cpu: float = 0.0
        self._process = None
        self._token_estimate: int = 0
        self._lock = threading.Lock()

        if _HAS_PSUTIL:
            try:
                self._process = psutil.Process(os.getpid())
            except Exception:
                pass

    def begin(self) -> None:
        self._start_time = time.time()
        if self._process is not None:
            try:
                self._start_cpu = self._process.cpu_times().user + self._process.cpu_times().system
            except Exception:
                self._start_cpu = 0.0

    def add_tokens(self, count: int) -> None:
        with self._lock:
            self._token_estimate += count

    def snapshot(self) -> ResourceMetrics:
        now = time.time()
        elapsed = now - self._start_time if self._start_time > 0 else 0.0
        cpu = 0.0
        ram_current = 0
        ram_peak = 0
        cpu_pct = 0.0

        if self._process is not None:
            try:
                cpu_times = self._process.cpu_times()
                cpu = (cpu_times.user + cpu_times.system) - self._start_cpu
                mem = self._process.memory_info()
                ram_current = mem.rss
                ram_peak = getattr(mem, "peak_wset", mem.rss)
                cpu_pct = self._process.cpu_percent(interval=0)
            except Exception:
                pass

        return ResourceMetrics(
            latency=elapsed,
            token_usage=self._token_estimate,
            cpu_time=max(0.0, cpu),
            ram_peak=ram_peak,
            cpu_percent=cpu_pct,
            ram_current=ram_current,
        )

    def build_metric(
        self,
        execution_id: str = "",
        trace_id: str = "",
        span_id: str = "",
        decision_id: str = "",
        agent_id: str = "",
        model_id: str = "",
    ) -> MREILMetric:
        import uuid
        resources = self.snapshot()
        return MREILMetric(
            metric_id=str(uuid.uuid4()),
            execution_id=execution_id,
            trace_id=trace_id,
            span_id=span_id,
            decision_id=decision_id,
            agent_id=agent_id,
            model_id=model_id,
            resources=resources,
            source="mreil_capture",
            timestamp=time.time(),
        )

    @staticmethod
    def available() -> bool:
        return _HAS_PSUTIL
