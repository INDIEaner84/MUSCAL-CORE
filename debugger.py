import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from schema import (
    DEBUG_BRIDGE_EXECUTION,
    DEBUG_CONFLICT_DETECTED,
    DEBUG_MCXF_BUILD,
    DEBUG_MEL_TOOL_CALL,
    DEBUG_MEMORY_STORE,
    DEBUG_MKC_CLASSIFY,
    DEBUG_MKC_EXTRACT,
    DEBUG_MKC_PARSE_START,
    DEBUG_RAG_INJECTION,
)


@dataclass
class DebugNode:
    id: str
    type: str
    input_state: Dict[str, Any] = field(default_factory=dict)
    output_state: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    duration_ms: float = 0.0
    confidence: float = 1.0
    parent_nodes: List[str] = field(default_factory=list)
    severity: Optional[float] = None
    status: str = "completed"


@dataclass
class DebugEdge:
    source_id: str
    target_id: str
    edge_type: str = "causal"
    payload: Dict[str, Any] = field(default_factory=dict)


STAGE_TO_DEBUG_EVENT = {
    "rag_inject": DEBUG_RAG_INJECTION,
    "mkc_classify": DEBUG_MKC_CLASSIFY,
    "mkc_extract": DEBUG_MKC_EXTRACT,
    "mcxf_build": DEBUG_MCXF_BUILD,
    "bridge_exec": DEBUG_BRIDGE_EXECUTION,
    "mel_tool_call": DEBUG_MEL_TOOL_CALL,
    "memory_store": DEBUG_MEMORY_STORE,
    "conflict_detected": DEBUG_CONFLICT_DETECTED,
}

STAGE_DISPLAY_NAMES = {
    "rag_inject": "RAG Injection",
    "mkc_classify": "MKC Classification",
    "mkc_extract": "MKC Tool Extraction",
    "mcxf_build": "MCXF Build",
    "bridge_exec": "Bridge Execution",
    "mel_tool_call": "MEL Tool Call",
    "memory_store": "Memory Store",
    "conflict_detected": "Conflict Detection",
}


class DebugGraph:
    def __init__(self):
        self.nodes: Dict[str, DebugNode] = {}
        self.edges: List[DebugEdge] = []
        self.execution_trace: List[str] = []
        self.active_step: str = ""
        self.runtime_metrics: Dict[str, Any] = {
            "total_execution_time": 0.0,
            "per_stage": {},
            "bottlenecks": [],
            "memory_writes_per_second": 0.0,
            "tool_execution_durations": {},
            "stage_counts": {},
        }

    def add_node(self, node: DebugNode) -> str:
        self.nodes[node.id] = node
        self.execution_trace.append(node.id)
        self.active_step = node.id
        return node.id

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str = "causal", payload: Optional[Dict] = None):
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append(DebugEdge(
                source_id=source_id, target_id=target_id,
                edge_type=edge_type, payload=payload or {}
            ))

    def get_execution_path(self) -> List[Dict]:
        path = []
        for nid in self.execution_trace:
            node = self.nodes.get(nid)
            if node:
                path.append({
                    "id": nid,
                    "type": node.type,
                    "duration_ms": node.duration_ms,
                    "status": node.status,
                    "confidence": node.confidence,
                })
        return path

    def get_node_list(self) -> List[Dict]:
        return [
            {
                "id": n.id,
                "type": n.type,
                "input_state": n.input_state,
                "output_state": n.output_state,
                "duration_ms": n.duration_ms,
                "confidence": n.confidence,
                "parent_nodes": n.parent_nodes,
                "severity": n.severity,
                "status": n.status,
            }
            for n in self.nodes.values()
        ]

    def get_edge_list(self) -> List[Dict]:
        return [
            {
                "source_id": e.source_id,
                "target_id": e.target_id,
                "edge_type": e.edge_type,
                "payload": e.payload,
            }
            for e in self.edges
        ]


class DebugEngine:
    def __init__(self, debug_mode: bool = False):
        self.graph = DebugGraph()
        self._mode = debug_mode
        self._running = False
        self._node_counter = 0
        self._stage_timers: Dict[str, float] = {}
        self._stage_inputs: Dict[str, Any] = {}
        self._last_parent: Optional[str] = None
        self._warnings: List[str] = []
        self._step_event = threading.Event()
        self._step_event.set()
        self._memory_write_count = 0
        self._execution_start_time = 0.0

    @property
    def debug_mode(self) -> bool:
        return self._mode

    def start_execution(self, input_text: str):
        self._running = True
        self._last_parent = None
        self._warnings.clear()
        self._memory_write_count = 0
        self._execution_start_time = time.time()

    def finish_execution(self):
        if self._execution_start_time > 0:
            total = (time.time() - self._execution_start_time) * 1000
            self.graph.runtime_metrics["total_execution_time"] = round(total, 2)
        self._running = False

    def stage_enter(self, stage: str, input_state: Optional[Dict] = None):
        self._stage_timers[stage] = time.time()
        self._stage_inputs[stage] = input_state or {}
        if self._mode:
            self._step_event.clear()

    def stage_exit(self, stage: str, output_state: Optional[Dict] = None,
                   confidence: float = 1.0, severity: Optional[float] = None,
                   extra_input: Optional[Dict] = None):
        if stage not in self._stage_timers:
            return
        start = self._stage_timers.pop(stage, time.time())
        duration_ms = round((time.time() - start) * 1000, 2)

        input_state = dict(self._stage_inputs.pop(stage, {}))
        if extra_input:
            input_state.update(extra_input)

        event_type = STAGE_TO_DEBUG_EVENT.get(stage, stage)
        self._node_counter += 1
        nid = f"debug_{stage}_{self._node_counter}"

        node = DebugNode(
            id=nid,
            type=event_type,
            input_state=input_state,
            output_state=output_state or {},
            timestamp=start,
            duration_ms=duration_ms,
            confidence=confidence,
            parent_nodes=[self._last_parent] if self._last_parent else [],
            severity=severity,
        )
        self.graph.add_node(node)

        if self._last_parent:
            edge_type = "conflict" if stage == "conflict_detected" else "causal"
            self.graph.add_edge(self._last_parent, nid, edge_type=edge_type)

        self._last_parent = nid

        st = stage
        m = self.graph.runtime_metrics
        if st not in m["per_stage"]:
            m["per_stage"][st] = {"count": 0, "total_ms": 0.0, "avg_ms": 0.0}
        m["per_stage"][st]["count"] += 1
        m["per_stage"][st]["total_ms"] += duration_ms
        m["per_stage"][st]["avg_ms"] = round(
            m["per_stage"][st]["total_ms"] / m["per_stage"][st]["count"], 2
        )
        m["stage_counts"][st] = m["stage_counts"].get(st, 0) + 1

        if duration_ms > 500:
            self._warnings.append(
                f"Stage '{stage}' took {duration_ms}ms (threshold: 500ms)"
            )

        if self._mode:
            pass

    def emit_tool_call(self, tool_name: str, args: Dict, result: Any,
                       duration_ms: float, confidence: float = 1.0):
        self._node_counter += 1
        nid = f"debug_mel_tool_call_{self._node_counter}"
        node = DebugNode(
            id=nid,
            type=DEBUG_MEL_TOOL_CALL,
            input_state={"tool": tool_name, "args": args},
            output_state={"result": str(result)},
            timestamp=time.time(),
            duration_ms=duration_ms,
            confidence=confidence,
            parent_nodes=[self._last_parent] if self._last_parent else [],
        )
        self.graph.add_node(node)
        if self._last_parent:
            self.graph.add_edge(self._last_parent, nid, edge_type="executes")
        self._last_parent = nid

        m = self.graph.runtime_metrics
        if tool_name not in m["tool_execution_durations"]:
            m["tool_execution_durations"][tool_name] = []
        m["tool_execution_durations"][tool_name].append(duration_ms)

    def emit_memory_write(self, memory_id: int):
        self._memory_write_count += 1
        self._node_counter += 1
        nid = f"debug_memory_store_{self._node_counter}"
        node = DebugNode(
            id=nid,
            type=DEBUG_MEMORY_STORE,
            input_state={},
            output_state={"memory_id": memory_id},
            timestamp=time.time(),
            duration_ms=0.0,
            confidence=1.0,
            parent_nodes=[self._last_parent] if self._last_parent else [],
        )
        self.graph.add_node(node)
        if self._last_parent:
            self.graph.add_edge(self._last_parent, nid, edge_type="causal")

    def emit_conflict(self, section: str, delta: float, patterns: List[str],
                      severity: float = 0.5):
        self._node_counter += 1
        nid = f"debug_conflict_{self._node_counter}"
        node = DebugNode(
            id=nid,
            type=DEBUG_CONFLICT_DETECTED,
            input_state={},
            output_state={"section": section, "delta": delta, "patterns": patterns},
            timestamp=time.time(),
            duration_ms=0.0,
            confidence=max(0.0, 1.0 - severity),
            parent_nodes=[self._last_parent] if self._last_parent else [],
            severity=severity,
        )
        self.graph.add_node(node)
        if self._last_parent:
            self.graph.add_edge(self._last_parent, nid, edge_type="conflict",
                                payload={"severity": severity})
        self._warnings.append(
            f"Conflict detected in '{section}' (delta={delta}, severity={severity})"
        )

    def wait_for_step(self):
        if self._mode:
            self._step_event.wait()

    def release_step(self):
        if self._mode:
            self._step_event.set()

    def get_debug_snapshot(self) -> Dict[str, Any]:
        m = self.graph.runtime_metrics

        elapsed = m["total_execution_time"] / 1000.0 if m["total_execution_time"] > 0 else 0.001
        mem_writes_per_sec = round(self._memory_write_count / elapsed, 2) if elapsed > 0 else 0.0
        m["memory_writes_per_second"] = mem_writes_per_sec

        bottlenecks = []
        for stage, data in m["per_stage"].items():
            if data["avg_ms"] > 200:
                bottlenecks.append({
                    "stage": stage,
                    "avg_ms": data["avg_ms"],
                    "count": data["count"],
                    "reason": f"avg {data['avg_ms']}ms exceeds 200ms threshold",
                })
        m["bottlenecks"] = bottlenecks

        snapshot = {
            "active_node": self.graph.active_step,
            "execution_path": self.graph.get_execution_path(),
            "graph_state": {
                "nodes": self.graph.get_node_list(),
                "edges": self.graph.get_edge_list(),
            },
            "metrics": {
                "total_execution_time": f"{m['total_execution_time']}ms",
                "mkc_latency": self._format_latency(m, "mkc_classify"),
                "mel_latency": self._format_latency(m, "mel_tool_call"),
                "rag_latency": self._format_latency(m, "rag_inject"),
                "bridge_latency": self._format_latency(m, "bridge_exec"),
                "per_stage": dict(m["per_stage"]),
                "bottlenecks": bottlenecks,
                "memory_writes_per_second": mem_writes_per_sec,
                "tool_execution_durations": {
                    k: {"count": len(v), "avg_ms": round(sum(v) / len(v), 2) if v else 0}
                    for k, v in m["tool_execution_durations"].items()
                },
            },
        }
        return snapshot

    def get_full_output(self) -> Dict[str, Any]:
        return {
            "status": "running" if self._running else "idle",
            "debug_snapshot": self.get_debug_snapshot(),
            "warnings": list(self._warnings),
            "performance_summary": {
                "total_execution_time": self.graph.runtime_metrics["total_execution_time"],
                "stages_monitored": list(self.graph.runtime_metrics["per_stage"].keys()),
                "total_nodes": len(self.graph.nodes),
                "total_edges": len(self.graph.edges),
                "bottleneck_count": len(self.graph.runtime_metrics["bottlenecks"]),
            },
        }

    def reset(self):
        self.graph = DebugGraph()
        self._stage_timers.clear()
        self._stage_inputs.clear()
        self._last_parent = None
        self._warnings.clear()
        self._memory_write_count = 0
        self._node_counter = 0

    @staticmethod
    def _format_latency(metrics: Dict, stage: str) -> str:
        data = metrics.get("per_stage", {}).get(stage)
        if not data or data["count"] == 0:
            return "0ms"
        return f"{data['avg_ms']}ms (avg, {data['count']} calls)"
