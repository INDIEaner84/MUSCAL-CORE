from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BenchmarkMeasurement:
    operation: str
    latency: float
    success: bool
    approval_overhead: float
    verification_cost: float
    resource_usage: dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "benchmark": {
                "operation": self.operation,
                "latency": self.latency,
                "success": self.success,
                "approval_overhead": self.approval_overhead,
                "verification_cost": self.verification_cost,
                "resource_usage": self.resource_usage,
                "timestamp": self.timestamp,
            }
        }


class InterfaceBenchmarkHooks:

    def __init__(self):
        self._measurements: list[BenchmarkMeasurement] = []

    def record(self, operation: str, latency: float, success: bool,
               approval_overhead: float = 0.0, verification_cost: float = 0.0,
               resource_usage: Optional[dict[str, float]] = None) -> None:
        self._measurements.append(BenchmarkMeasurement(
            operation=operation,
            latency=latency,
            success=success,
            approval_overhead=approval_overhead,
            verification_cost=verification_cost,
            resource_usage=resource_usage or {},
        ))

    def get_all(self) -> list[BenchmarkMeasurement]:
        return list(self._measurements)

    def summary(self) -> dict[str, Any]:
        if not self._measurements:
            return {"count": 0}
        total = len(self._measurements)
        successes = sum(1 for m in self._measurements if m.success)
        latencies = [m.latency for m in self._measurements]
        approvals = [m.approval_overhead for m in self._measurements]
        verifications = [m.verification_cost for m in self._measurements]
        return {
            "count": total,
            "success_rate": successes / total if total else 0.0,
            "avg_latency": sum(latencies) / total if total else 0.0,
            "max_latency": max(latencies) if latencies else 0.0,
            "min_latency": min(latencies) if latencies else 0.0,
            "avg_approval_overhead": sum(approvals) / total if total else 0.0,
            "avg_verification_cost": sum(verifications) / total if total else 0.0,
            "total_resource_usage": self._total_resource_usage(),
        }

    def _total_resource_usage(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for m in self._measurements:
            for k, v in m.resource_usage.items():
                totals[k] = totals.get(k, 0.0) + v
        return totals

    def clear(self) -> None:
        self._measurements.clear()
