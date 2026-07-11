from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from runtime.optimizer.cost_optimizer import CostVector


@dataclass
class DAGNode:
    id: str
    op: str
    cost_vector: CostVector = field(default_factory=CostVector)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionDAG:
    nodes: list[DAGNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @classmethod
    def from_plan(cls, plan: Any) -> ExecutionDAG:
        from runtime.optimizer.cost_optimizer import default_cost_estimator

        dag = cls()
        steps = getattr(plan, "steps", plan if isinstance(plan, list) else [])
        step_list = steps if isinstance(steps, list) else []

        prev_id: Optional[str] = None
        for i, step in enumerate(step_list):
            tool = step.get("tool", step.get("op", "unknown"))
            args = step.get("args", {})
            nid = step.get("id", f"step_{i}")
            op = tool

            cost_vector = default_cost_estimator(op)

            deps: list[str] = []
            if prev_id is not None:
                deps.append(prev_id)

            explicit_deps = step.get("depends_on", [])
            if explicit_deps:
                deps.extend(explicit_deps)

            node = DAGNode(
                id=nid,
                op=op,
                cost_vector=cost_vector,
                dependencies=list(set(deps)),
                metadata={"tool": tool, "args": args, "index": i},
            )
            dag.nodes.append(node)

            for dep in node.dependencies:
                if not dag._has_edge(dep, nid):
                    dag.edges.append((dep, nid))

            prev_id = nid

        return dag

    def _has_edge(self, u: str, v: str) -> bool:
        return any(a == u and b == v for a, b in self.edges)

    def get_node(self, nid: str) -> Optional[DAGNode]:
        for n in self.nodes:
            if n.id == nid:
                return n
        return None

    def remove_node(self, nid: str) -> None:
        self.nodes = [n for n in self.nodes if n.id != nid]
        self.edges = [(u, v) for u, v in self.edges if u != nid and v != nid]
        for n in self.nodes:
            n.dependencies = [d for d in n.dependencies if d != nid]

    def add_node(self, node: DAGNode) -> None:
        self.nodes.append(node)
        for dep in node.dependencies:
            edge = (dep, node.id)
            if not self._has_edge(*edge):
                self.edges.append(edge)

    def dependencies_of(self, nid: str) -> list[str]:
        for n in self.nodes:
            if n.id == nid:
                return list(n.dependencies)
        return []

    def topological_sort(self) -> list[list[DAGNode]]:
        visited: set[str] = set()
        temp: set[str] = set()
        order: list[DAGNode] = []

        def dfs(nid: str) -> None:
            if nid in temp:
                raise ValueError(f"Cycle detected at node {nid}")
            if nid in visited:
                return
            temp.add(nid)
            node = self.get_node(nid)
            if node:
                for dep_id in node.dependencies:
                    dfs(dep_id)
            temp.remove(nid)
            visited.add(nid)
            if node:
                order.append(node)

        for n in self.nodes:
            dfs(n.id)

        node_to_depth: dict[str, int] = {}
        for n in order:
            if not n.dependencies:
                node_to_depth[n.id] = 0
            else:
                node_to_depth[n.id] = max(node_to_depth.get(d, 0) for d in n.dependencies) + 1

        depth_groups: dict[int, list[DAGNode]] = {}
        for n in self.nodes:
            d = node_to_depth.get(n.id, 0)
            if d not in depth_groups:
                depth_groups[d] = []
            depth_groups[d].append(n)

        return [depth_groups[k] for k in sorted(depth_groups.keys())]

    def hash(self) -> str:
        return self._compute_hash()

    def _compute_hash(self) -> str:
        import hashlib
        import json
        data = {
            "nodes": sorted(
                [
                    {
                        "id": n.id,
                        "op": n.op,
                        "cost_vector": n.cost_vector.to_dict(),
                        "deps": sorted(n.dependencies),
                    }
                    for n in self.nodes
                ],
                key=lambda x: x["id"],
            ),
            "edges": sorted((u, v) for u, v in self.edges),
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()



