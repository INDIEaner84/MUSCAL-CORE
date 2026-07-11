import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from runtime.optimizer.graph import ExecutionDAG


@dataclass
class PassMetadata:
    name: str
    version: str
    cost: float
    gain: float


@dataclass
class VerificationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    before_hash: str = ""
    after_hash: str = ""


class OptimizationPass(ABC):
    name: str = "base"
    version: str = "0.1"

    @abstractmethod
    def optimize(self, dag: ExecutionDAG) -> ExecutionDAG:
        ...

    def verify(self, before: ExecutionDAG, after: ExecutionDAG) -> VerificationResult:
        errors: list[str] = []
        before_hash = self._hash_dag(before)
        after_hash = self._hash_dag(after)

        before_ids = {n.id for n in before.nodes}
        after_ids = {n.id for n in after.nodes}

        after_node_ids = {n.id for n in after.nodes}
        for u, v in after.edges:
            if u not in after_node_ids:
                errors.append(f"Edge references missing source node: {u}")
            if v not in after_node_ids:
                errors.append(f"Edge references missing target node: {v}")

        common_ids = before_ids & after_ids
        for nid in common_ids:
            before_deps = before.dependencies_of(nid)
            after_deps = after.dependencies_of(nid)
            if before_deps and after_deps:
                if before_deps != after_deps:
                    errors.append(
                        f"Dependency changed for node {nid}: "
                        f"before={before_deps} after={after_deps}"
                    )

        if not self._is_valid_dag(after):
            errors.append("DAG validation failed: cycle detected")

        return VerificationResult(
            passed=len(errors) == 0,
            errors=errors,
            before_hash=before_hash,
            after_hash=after_hash,
        )

    @abstractmethod
    def metadata(self) -> PassMetadata:
        ...

    def _hash_dag(self, dag: ExecutionDAG) -> str:
        data = {
            "nodes": sorted(
                [
                    {
                        "id": n.id,
                        "op": n.op,
                        "cost_vector": n.cost_vector.to_dict() if hasattr(n.cost_vector, "to_dict") else str(n.cost_vector),
                        "deps": sorted(n.dependencies),
                    }
                    for n in dag.nodes
                ],
                key=lambda x: x["id"],
            ),
            "edges": sorted((u, v) for u, v in dag.edges),
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def _is_valid_dag(self, dag: ExecutionDAG) -> bool:
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
