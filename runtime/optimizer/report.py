from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.optimizer.graph import ExecutionDAG
from runtime.optimizer.verification import FullVerificationResult


@dataclass
class OptimizationReport:
    timestamp: str = ""
    pass_count: int = 0
    passes_applied: list[dict] = field(default_factory=list)
    node_count_before: int = 0
    node_count_after: int = 0
    edge_count_before: int = 0
    edge_count_after: int = 0
    removed_nodes: int = 0
    fusion_count: int = 0
    parallel_layers: int = 0
    estimated_cost_reduction: float = 0.0
    graph_hash_before: str = ""
    graph_hash_after: str = ""
    replay_compatible: bool = True
    determinism: str = "PASS"
    verification: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_pipeline(
        cls,
        before: ExecutionDAG,
        after: ExecutionDAG,
        pass_results: list[dict],
        ver: FullVerificationResult,
    ) -> "OptimizationReport":
        removed = before.num_nodes - after.num_nodes
        fusion_count = sum(
            1 for pr in pass_results
            if pr.get("name") == "node_fusion" and pr.get("passed")
        )

        estimated_removed_cost = 0.0
        if removed > 0 and before.nodes:
            avg_cost_before = sum(n.cost_vector.total() for n in before.nodes) / max(before.num_nodes, 1)
            estimated_removed_cost = avg_cost_before * removed * 0.5

        parallel_layers = 0
        for n in after.nodes:
            layer = n.metadata.get("parallel_layer", 0)
            if layer + 1 > parallel_layers:
                parallel_layers = layer + 1

        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            pass_count=len(pass_results),
            passes_applied=pass_results,
            node_count_before=before.num_nodes,
            node_count_after=after.num_nodes,
            edge_count_before=len(before.edges),
            edge_count_after=len(after.edges),
            removed_nodes=removed,
            fusion_count=fusion_count,
            parallel_layers=parallel_layers,
            estimated_cost_reduction=round(estimated_removed_cost, 4),
            graph_hash_before=ver.before_hash,
            graph_hash_after=ver.after_hash,
            replay_compatible=ver.replay_compatible,
            determinism="PASS" if ver.deterministic else "FAIL",
            verification={
                "passed": ver.passed,
                "errors": ver.errors,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "pass_count": self.pass_count,
            "passes_applied": self.passes_applied,
            "node_count": {
                "before": self.node_count_before,
                "after": self.node_count_after,
                "removed": self.removed_nodes,
            },
            "edges": {
                "before": self.edge_count_before,
                "after": self.edge_count_after,
            },
            "fusion_count": self.fusion_count,
            "parallel_layers": self.parallel_layers,
            "estimated_cost_reduction": self.estimated_cost_reduction,
            "graph_hash": {
                "before": self.graph_hash_before,
                "after": self.graph_hash_after,
            },
            "replay_compatible": self.replay_compatible,
            "determinism": self.determinism,
            "verification": self.verification,
        }

    def __str__(self) -> str:
        lines = [
            "=" * 50,
            "  MUSCAL Optimization Report",
            "=" * 50,
            f"  Timestamp         : {self.timestamp}",
            f"  Passes Applied    : {self.pass_count}",
            f"  Nodes             : {self.node_count_before} -> {self.node_count_after} ({self.removed_nodes} removed)",
            f"  Edges             : {self.edge_count_before} -> {self.edge_count_after}",
            f"  Fusion Count      : {self.fusion_count}",
            f"  Parallel Layers   : {self.parallel_layers}",
            f"  Cost Reduction    : {self.estimated_cost_reduction}",
            f"  Graph Hash Before : {self.graph_hash_before[:16]}...",
            f"  Graph Hash After  : {self.graph_hash_after[:16]}...",
            f"  Replay Compatible : {self.replay_compatible}",
            f"  Determinism       : {self.determinism}",
            f"  Verification      : {'PASS' if self.verification.get('passed') else 'FAIL'}",
        ]
        if self.verification.get("errors"):
            for err in self.verification["errors"]:
                lines.append(f"    ERROR: {err}")
        return "\n".join(lines)
