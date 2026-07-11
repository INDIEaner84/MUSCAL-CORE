"""
ALITA SPHERE UI Layer v0.1

Projects flat Graph Runtime into a radial interactive cognitive sphere.

Structure:
  Center  = ACTIVE INTENT
  Inner   = active reasoning (MKC pipeline state)
  Middle  = execution graph (MEL + tasks)
  Outer   = memory + RAG + history

Usage:
    sphere = SphereState(graph)
    sphere.sync()                    # rebuild rings from graph
    snapshot = sphere.get_snapshot()
    sphere.rotate_focus("intent_1")  # change focus
    path = sphere.trace_path("tool_execution_5")
"""

import time

from schema import (
    EDGE_TYPE_EXECUTES,
    NODE_TYPE_CONFLICT,
    NODE_TYPE_EXECUTION_PLAN,
    NODE_TYPE_INTENT,
    NODE_TYPE_MCXF_SECTION,
    NODE_TYPE_MEMORY_ENTRY,
    NODE_TYPE_MKC_STEP,
    NODE_TYPE_RAG_CONTEXT,
    NODE_TYPE_TOOL_EXECUTION,
    Node,
)

INNER_TYPES = {NODE_TYPE_INTENT, NODE_TYPE_MKC_STEP, NODE_TYPE_MCXF_SECTION}
MIDDLE_TYPES = {NODE_TYPE_EXECUTION_PLAN, NODE_TYPE_TOOL_EXECUTION}
OUTER_TYPES = {NODE_TYPE_MEMORY_ENTRY, NODE_TYPE_RAG_CONTEXT, NODE_TYPE_CONFLICT}


class SphereState:
    """Projects GraphState into a radial sphere structure."""

    def __init__(self, graph):
        self.graph = graph
        self.center_intent: str = ""
        self.inner_ring: list[str] = []
        self.middle_ring: list[str] = []
        self.outer_ring: list[str] = []
        self.focus_path: list[str] = []
        self._collapsed: set[str] = set()
        self._highlighted: set[str] = set()

    # ── Ring Mapping ─────────────────────────────────────────────

    def sync(self):
        """Rebuild ring assignment from current graph snapshot."""
        g = self.graph

        # Center = most recent INTENT node (active intent)
        intents = [nid for nid, n in g.nodes.items() if n.type == NODE_TYPE_INTENT]
        if intents:
            self.center_intent = sorted(intents)[-1]
        else:
            self.center_intent = ""

        # Assign every graph node to a ring
        inner, middle, outer = [], [], []
        for nid, node in g.nodes.items():
            if node.type in INNER_TYPES:
                inner.append(nid)
            elif node.type in MIDDLE_TYPES:
                middle.append(nid)
            elif node.type in OUTER_TYPES:
                outer.append(nid)

        self.inner_ring = sorted(inner)
        self.middle_ring = sorted(middle)
        self.outer_ring = sorted(outer)

        # Auto-highlight: nodes on the execution path from center
        self._auto_highlight()

    def _auto_highlight(self):
        """Highlight all nodes connected to center intent via any edge."""
        self._highlighted.clear()
        if not self.center_intent or self.center_intent not in self.graph.nodes:
            return
        g = self.graph
        visited = set()
        stack = [self.center_intent]
        while stack:
            nid = stack.pop()
            if nid in visited:
                continue
            visited.add(nid)
            for edge in g.edges:
                if edge.source_id == nid and edge.target_id not in visited:
                    stack.append(edge.target_id)
                if edge.target_id == nid and edge.source_id not in visited:
                    stack.append(edge.source_id)
        self._highlighted = visited

    # ── Interaction ──────────────────────────────────────────────

    def rotate_focus(self, node_id: str):
        """Change the center of attention to a specific node."""
        if node_id not in self.graph.nodes:
            return
        self.focus_path.append(self.center_intent)
        self.center_intent = node_id
        self.graph.set_focus(node_id)
        self.sync()

    def expand_node(self, node_id: str):
        """Remove node from collapsed set, making its children visible."""
        self._collapsed.discard(node_id)
        self.sync()

    def collapse_node(self, node_id: str):
        """Add node to collapsed set, hiding its children from immediate view."""
        self._collapsed.add(node_id)
        self.sync()

    def trace_path(self, node_id: str) -> list[dict]:
        """Find the path from center to the given node via graph edges."""
        if node_id not in self.graph.nodes:
            return []
        g = self.graph
        parent_map = {}

        # BFS from center outward
        visited = {self.center_intent}
        queue = [self.center_intent]
        while queue:
            current = queue.pop(0)
            if current == node_id:
                break
            for edge in g.edges:
                if edge.edge_type in ("DERIVES_FROM", "EXECUTES"):
                    if edge.source_id == current and edge.target_id not in visited:
                        visited.add(edge.target_id)
                        parent_map[edge.target_id] = current
                        queue.append(edge.target_id)

        # Reconstruct path
        path = []
        cur = node_id
        while cur in parent_map:
            node = g.nodes.get(cur)
            path.append({
                "id": cur,
                "type": node.type if node else "UNKNOWN",
                "status": node.status if node else ""
            })
            cur = parent_map[cur]
        # Add center
        center_node = g.nodes.get(self.center_intent)
        path.append({
            "id": self.center_intent,
            "type": center_node.type if center_node else "INTENT",
            "status": center_node.status if center_node else ""
        })
        path.reverse()
        return path

    def merge_branches(self, node_a: str, node_b: str) -> dict:
        """Find the common ancestor of two nodes in the graph."""
        if node_a not in self.graph.nodes or node_b not in self.graph.nodes:
            return {}
        g = self.graph

        def get_ancestors(nid):
            ancestors = set()
            stack = [nid]
            while stack:
                current = stack.pop()
                ancestors.add(current)
                for edge in g.edges:
                    if edge.edge_type in ("DERIVES_FROM", "EXECUTES"):
                        if edge.target_id == current and edge.source_id not in ancestors:
                            stack.append(edge.source_id)
            return ancestors

        anc_a = get_ancestors(node_a)
        anc_b = get_ancestors(node_b)
        common = anc_a & anc_b

        if not common:
            return {"common_ancestor": None, "distance_a": -1, "distance_b": -1}

        # Pick the "latest" common ancestor (highest node counter = most specific)
        common_id = sorted(common, key=lambda x: int(x.split("_")[-1]) if x.split("_")[-1].isdigit() else 0)[-1]
        anc_node = g.nodes.get(common_id)

        return {
            "common_ancestor": {
                "id": common_id,
                "type": anc_node.type if anc_node else "UNKNOWN"
            },
            "distance_a": len(self.trace_path(node_a)) - 1,
            "distance_b": len(self.trace_path(node_b)) - 1
        }

    # ── Relevance (Cognitive fade) ───────────────────────────────

    def get_relevance(self, node_id: str) -> float:
        """Return relevance score 0.0–1.0. Lower = more faded."""
        if node_id in self._highlighted:
            return 1.0
        g = self.graph
        node = g.nodes.get(node_id)
        if node is None:
            return 0.0
        if node_id == self.center_intent:
            return 1.0
        # Middle ring = moderate relevance
        if node_id in self.middle_ring:
            return 0.6
        # Outer ring = lower relevance unless highlighted
        if node_id in self.outer_ring:
            return 0.3
        return node.confidence * 0.5

    # ── Snapshot ─────────────────────────────────────────────────

    def get_snapshot(self) -> dict:
        """Full sphere state as JSON-serializable dict."""
        g = self.graph

        def node_dict(nid):
            node = g.nodes.get(nid)
            if node is None:
                return None
            return {
                "id": node.id,
                "type": node.type,
                "payload": node.payload,
                "confidence": node.confidence,
                "status": node.status,
                "relevance": self.get_relevance(nid),
                "collapsed": nid in self._collapsed,
                "highlighted": nid in self._highlighted,
                "timestamp": node.timestamp
            }

        return {
            "center": node_dict(self.center_intent),
            "rings": {
                "inner": [node_dict(nid) for nid in self.inner_ring if node_dict(nid) is not None],
                "middle": [node_dict(nid) for nid in self.middle_ring if node_dict(nid) is not None],
                "outer": [node_dict(nid) for nid in self.outer_ring if node_dict(nid) is not None]
            },
            "active_path": self.focus_path[-5:] if self.focus_path else [],
            "focus_history": self.focus_path[-10:],
            "collapsed_count": len(self._collapsed),
            "highlighted_count": len(self._highlighted)
        }
