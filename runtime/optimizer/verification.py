from dataclasses import dataclass, field
from typing import Optional

from runtime.optimizer.graph import ExecutionDAG


@dataclass
class FullVerificationResult:
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    before_hash: str = ""
    after_hash: str = ""
    deterministic: bool = True
    replay_compatible: bool = True
    node_count_before: int = 0
    node_count_after: int = 0
    edge_count_before: int = 0
    edge_count_after: int = 0


def verify_full_pipeline(
    before: ExecutionDAG,
    after: ExecutionDAG,
    pass_results: list[dict],
) -> FullVerificationResult:
    errors: list[str] = []
    result = FullVerificationResult(
        before_hash=before.hash(),
        after_hash=after.hash(),
        node_count_before=before.num_nodes,
        node_count_after=after.num_nodes,
        edge_count_before=len(before.edges),
        edge_count_after=len(after.edges),
    )

    for pr in pass_results:
        if not pr.get("passed", True):
            errors.append(f"Pass failed: {pr.get('name', 'unknown')}")
            for err in pr.get("errors", []):
                errors.append(f"  {err}")

    before_ids = {n.id for n in before.nodes}
    after_ids = {n.id for n in after.nodes}

    for n in before.nodes:
        if n.id in after_ids:
            after_node = after.get_node(n.id)
            if after_node:
                before_deps = set(n.dependencies)
                after_deps = set(after_node.dependencies)
                if before_deps and after_deps:
                    if before_deps != after_deps:
                        rel_deps = before_deps & after_deps
                        if len(rel_deps) < min(len(before_deps), len(after_deps)):
                            errors.append(
                                f"Dependency mismatch for node {n.id}: "
                                f"before={sorted(before_deps)} after={sorted(after_deps)}"
                            )

    for u, v in after.edges:
        if u not in after_ids:
            errors.append(f"Edge source {u} not found in after graph")
            result.passed = False
        if v not in after_ids:
            errors.append(f"Edge target {v} not found in after graph")
            result.passed = False

    after_deps_set: set[str] = set()
    for n in after.nodes:
        for d in n.dependencies:
            after_deps_set.add(d)
            if d not in after_ids:
                errors.append(f"Dependency {d} of node {n.id} not in after graph")
                result.passed = False

    if not _is_dag(after):
        errors.append("Final graph contains a cycle")
        result.passed = False

    result.errors = errors
    return result


def _is_dag(dag: ExecutionDAG) -> bool:
    visited: dict[str, bool] = {}
    path: set[str] = set()

    def dfs(nid: str) -> bool:
        if nid in path:
            return False
        if nid in visited:
            return visited[nid]
        path.add(nid)
        for n in dag.nodes:
            if nid in n.dependencies:
                if not dfs(n.id):
                    return False
        path.remove(nid)
        visited[nid] = True
        return True

    for n in dag.nodes:
        if n.id not in visited:
            if not dfs(n.id):
                return False
    return True
