"""
MUSCAL Graph Runtime Layer v0.1

Passive observer of the kernel pipeline.
Maintains a real-time interactive graph of all system activity.

Usage:
    graph = GraphState()
    graph.on(EVENT_NODE_CREATED, lambda e: print(e))
    graph.emit(EVENT_NODE_CREATED, {"type": "INTENT", "payload": {...}})
    snapshot = graph.get_snapshot()
"""

import threading
import time
from collections import defaultdict

from schema import (
    EDGE_TYPE_CONFLICTS_WITH,
    EDGE_TYPE_DEPENDS_ON,
    EDGE_TYPE_DERIVES_FROM,
    EDGE_TYPE_EXECUTES,
    EDGE_TYPE_RETRIEVES_FROM,
    EVENT_EDGE_CREATED,
    EVENT_EXECUTION_FINISHED,
    EVENT_EXECUTION_STARTED,
    EVENT_NODE_CREATED,
    EVENT_NODE_UPDATED,
    NODE_TYPE_CONFLICT,
    NODE_TYPE_EXECUTION_PLAN,
    NODE_TYPE_INTENT,
    NODE_TYPE_MCXF_SECTION,
    NODE_TYPE_MEMORY_ENTRY,
    NODE_TYPE_MKC_STEP,
    NODE_TYPE_RAG_CONTEXT,
    NODE_TYPE_TOOL_EXECUTION,
    Edge,
    Node,
)

MAX_NODES = 5000
MAX_EDGES = 10000


class GraphState:
    """Holds the full graph state and manages events."""

    def __init__(self):
        self._lock = threading.RLock()
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.active_focus_node: str = ""
        self._event_listeners: dict = defaultdict(list)
        self._update_stream: list = []
        self._node_counter: int = 0
        self._replaying: bool = False
        self._dispatch_depth: int = 0

    # ── Node Management ──────────────────────────────────────────────

    def add_node(self, node_type: str, payload: dict,
                 confidence: float = 1.0, status: str = "created") -> str:
        with self._lock:
            self._node_counter += 1
            node_id = f"{node_type.lower()}_{self._node_counter}"
            node = Node(
                id=node_id,
                type=node_type,
                payload=payload,
                timestamp=time.time(),
                confidence=confidence,
                status=status
            )
            self.nodes[node_id] = node
        self._push_event(EVENT_NODE_CREATED, {
            "node_id": node_id,
            "type": node_type,
            "payload": payload,
            "timestamp": node.timestamp
        })
        with self._lock:
            if not self.active_focus_node:
                self.active_focus_node = node_id
        self.prune_graph()
        return node_id

    def update_node(self, node_id: str, status: str = None,
                    confidence: float = None, payload: dict = None):
        with self._lock:
            node = self.nodes.get(node_id)
            if node is None:
                return
            if status is not None:
                node.status = status
            if confidence is not None:
                node.confidence = confidence
            if payload is not None:
                node.payload.update(payload)
        self._push_event(EVENT_NODE_UPDATED, {
            "node_id": node_id,
            "status": node.status,
            "confidence": node.confidence
        })

    # ── Edge Management ──────────────────────────────────────────────

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str, payload: dict = None):
        with self._lock:
            if source_id not in self.nodes or target_id not in self.nodes:
                return
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                payload=payload or {}
            )
            self.edges.append(edge)
        self._push_event(EVENT_EDGE_CREATED, {
            "source_id": source_id,
            "target_id": target_id,
            "edge_type": edge_type
        })
        self.prune_graph()

    # ── Pruning ──────────────────────────────────────────────────────

    def remove_node(self, node_id: str):
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                self.edges[:] = [e for e in self.edges
                                 if e.source_id != node_id and e.target_id != node_id]

    def remove_edge(self, index: int):
        with self._lock:
            if 0 <= index < len(self.edges):
                self.edges.pop(index)

    def prune_graph(self):
        with self._lock:
            if self._dispatch_depth > 0:
                return
            if len(self.nodes) > MAX_NODES:
                sorted_nodes = sorted(self.nodes.items(), key=lambda x: x[1].timestamp)
                to_remove = len(self.nodes) - MAX_NODES
                for i in range(to_remove):
                    self.remove_node(sorted_nodes[i][0])

            if len(self.edges) > MAX_EDGES:
                to_remove = len(self.edges) - MAX_EDGES
                for _ in range(to_remove):
                    self.edges.pop(0)

    # ── Focus ────────────────────────────────────────────────────────

    def set_focus(self, node_id: str):
        with self._lock:
            if node_id in self.nodes:
                self.active_focus_node = node_id

    # ── Tracing ──────────────────────────────────────────────────────

    def trace_dependencies(self, node_id: str) -> list[dict]:
        result = []
        visited = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            node = self.nodes.get(current)
            if node:
                result.append({
                    "id": current,
                    "type": node.type,
                    "status": node.status,
                    "confidence": node.confidence
                })
            for edge in self.edges:
                if edge.source_id == current and edge.target_id not in visited:
                    stack.append(edge.target_id)
                if edge.edge_type == EDGE_TYPE_EXECUTES and edge.target_id == current:
                    if edge.source_id not in visited:
                        stack.append(edge.source_id)
        return result

    def trace_execution_path(self) -> list[dict]:
        path = []
        for edge in self.edges:
            if edge.edge_type == EDGE_TYPE_EXECUTES:
                src = self.nodes.get(edge.source_id)
                tgt = self.nodes.get(edge.target_id)
                if src and tgt:
                    path.append({
                        "from": {"id": src.id, "type": src.type, "status": src.status},
                        "to": {"id": tgt.id, "type": tgt.type, "status": tgt.status},
                        "edge_type": edge.edge_type
                    })
        return path

    # ── Event System ─────────────────────────────────────────────────

    # ── Event System (ADR-003) ─────────────────────────────────────
    # Graph Events sind für pipeline-interne Abläufe (Execution, Sync).
    # Für OS-Lifecycle/Plugin-Events siehe event_bus.EventBus.
    # Alle Graph-Events werden via _wire_event_bus() an EventBus gespiegelt.

    def on(self, event_type: str, callback):
        with self._lock:
            if callback not in self._event_listeners[event_type]:
                self._event_listeners[event_type].append(callback)

    def _push_event(self, event_type: str, payload: dict):
        with self._lock:
            entry = {"type": event_type, "payload": payload, "timestamp": time.time()}
            self._update_stream.append(entry)
            listeners = list(self._event_listeners.get(event_type, []))
            self._dispatch_depth += 1
        if self._replaying:
            with self._lock:
                self._dispatch_depth -= 1
            return
        for cb in listeners:
            cb(entry)
        with self._lock:
            self._dispatch_depth -= 1

    def emit(self, event_type: str, payload: dict):
        self._push_event(event_type, payload)

    def get_event_stream(self, limit: int = 50) -> list:
        with self._lock:
            return list(self._update_stream[-limit:])

    def reset_event_listeners(self, event_type: str = None):
        with self._lock:
            if event_type is None:
                self._event_listeners.clear()
            else:
                self._event_listeners[event_type].clear()

    # ── Snapshot ─────────────────────────────────────────────────────

    def get_snapshot(self) -> dict:
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "payload": n.payload,
                    "timestamp": n.timestamp,
                    "confidence": n.confidence,
                    "status": n.status
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type,
                    "payload": e.payload
                }
                for e in self.edges
            ],
            "focus": self.active_focus_node,
            "event_count": len(self._update_stream)
        }
