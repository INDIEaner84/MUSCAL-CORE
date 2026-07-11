from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CostVector:
    cpu: float = 1.0
    ram: float = 1.0
    latency: float = 1.0
    tokens: int = 0
    retries: int = 0
    estimated_cost: float = 0.0
    risk: float = 0.0
    tool_calls: int = 1
    graph_complexity: float = 1.0

    def total(self) -> float:
        return (
            self.cpu * 0.15
            + self.ram * 0.10
            + self.latency * 0.25
            + self.tokens * 0.001
            + self.retries * 2.0
            + self.estimated_cost * 1.0
            + self.risk * 3.0
            + self.tool_calls * 0.5
            + self.graph_complexity * 0.05
        )

    def __add__(self, other: CostVector) -> CostVector:
        return CostVector(
            cpu=self.cpu + other.cpu,
            ram=self.ram + other.ram,
            latency=self.latency + other.latency,
            tokens=self.tokens + other.tokens,
            retries=self.retries + other.retries,
            estimated_cost=self.estimated_cost + other.estimated_cost,
            risk=max(self.risk, other.risk),
            tool_calls=self.tool_calls + other.tool_calls,
            graph_complexity=max(self.graph_complexity, other.graph_complexity),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu": self.cpu,
            "ram": self.ram,
            "latency": self.latency,
            "tokens": self.tokens,
            "retries": self.retries,
            "estimated_cost": self.estimated_cost,
            "risk": self.risk,
            "tool_calls": self.tool_calls,
            "graph_complexity": self.graph_complexity,
        }


TOOL_COST_MAP: dict[str, CostVector] = {
    "browser.open": CostVector(cpu=0.5, ram=2.0, latency=3.0, tokens=0, retries=1, estimated_cost=0.01, risk=0.3, tool_calls=1, graph_complexity=0.5),
    "browser.click": CostVector(cpu=0.3, ram=1.5, latency=2.0, tokens=0, retries=1, estimated_cost=0.005, risk=0.2, tool_calls=1, graph_complexity=0.3),
    "browser.type": CostVector(cpu=0.3, ram=1.5, latency=2.0, tokens=0, retries=1, estimated_cost=0.005, risk=0.2, tool_calls=1, graph_complexity=0.3),
    "browser.extract": CostVector(cpu=0.2, ram=1.0, latency=1.5, tokens=0, retries=1, estimated_cost=0.003, risk=0.1, tool_calls=1, graph_complexity=0.2),
    "browser.screenshot": CostVector(cpu=0.4, ram=1.5, latency=2.0, tokens=0, retries=1, estimated_cost=0.005, risk=0.1, tool_calls=1, graph_complexity=0.3),
    "desktop.screenshot": CostVector(cpu=0.4, ram=1.5, latency=2.0, tokens=0, retries=0, estimated_cost=0.003, risk=0.1, tool_calls=1, graph_complexity=0.3),
    "filesystem.write": CostVector(cpu=0.1, ram=0.2, latency=0.5, tokens=0, retries=0, estimated_cost=0.001, risk=0.0, tool_calls=1, graph_complexity=0.1),
    "filesystem.read": CostVector(cpu=0.05, ram=0.1, latency=0.3, tokens=0, retries=0, estimated_cost=0.000, risk=0.0, tool_calls=1, graph_complexity=0.05),
    "console.print": CostVector(cpu=0.05, ram=0.05, latency=0.1, tokens=0, retries=0, estimated_cost=0.000, risk=0.0, tool_calls=1, graph_complexity=0.05),
    "math.add": CostVector(cpu=0.05, ram=0.05, latency=0.05, tokens=0, retries=0, estimated_cost=0.000, risk=0.0, tool_calls=1, graph_complexity=0.05),
    "opencode.run": CostVector(cpu=2.0, ram=3.0, latency=5.0, tokens=500, retries=1, estimated_cost=0.05, risk=0.5, tool_calls=1, graph_complexity=1.0),
    "validate": CostVector(cpu=0.1, ram=0.2, latency=0.5, tokens=0, retries=0, estimated_cost=0.001, risk=0.0, tool_calls=1, graph_complexity=0.1),
    "validate+execute": CostVector(cpu=0.15, ram=0.3, latency=0.6, tokens=0, retries=0, estimated_cost=0.001, risk=0.0, tool_calls=1, graph_complexity=0.15),
    "reasoning": CostVector(cpu=1.0, ram=1.0, latency=3.0, tokens=200, retries=0, estimated_cost=0.02, risk=0.3, tool_calls=1, graph_complexity=0.5),
    "rag_filter": CostVector(cpu=0.5, ram=0.5, latency=1.0, tokens=100, retries=0, estimated_cost=0.01, risk=0.1, tool_calls=1, graph_complexity=0.3),
    "sql_generation": CostVector(cpu=1.0, ram=1.0, latency=2.0, tokens=150, retries=1, estimated_cost=0.02, risk=0.2, tool_calls=1, graph_complexity=0.4),
    "code_review": CostVector(cpu=1.0, ram=1.0, latency=3.0, tokens=300, retries=0, estimated_cost=0.03, risk=0.4, tool_calls=1, graph_complexity=0.6),
    "default": CostVector(cpu=1.0, ram=1.0, latency=1.0, tokens=0, retries=0, estimated_cost=0.01, risk=0.2, tool_calls=1, graph_complexity=0.5),
}


def default_cost_estimator(op: str) -> CostVector:
    for key, cv in TOOL_COST_MAP.items():
        if op == key or op.startswith(key):
            return CostVector(**cv.to_dict())
    if "browser" in op.lower():
        return CostVector(**TOOL_COST_MAP["browser.open"].to_dict())
    if "opencode" in op.lower():
        return CostVector(**TOOL_COST_MAP["opencode.run"].to_dict())
    if "filesystem" in op.lower() or "write" in op.lower() or "read" in op.lower():
        return CostVector(**TOOL_COST_MAP["filesystem.write"].to_dict())
    return CostVector(**TOOL_COST_MAP["default"].to_dict())
