from runtime.optimizer.base_pass import OptimizationPass, PassMetadata, VerificationResult
from runtime.optimizer.graph import ExecutionDAG


class DeadCodeElimination(OptimizationPass):
    name = "dead_node"
    version = "0.1"

    def optimize(self, dag: ExecutionDAG) -> ExecutionDAG:
        used_ids: set[str] = set()
        for u, v in dag.edges:
            used_ids.add(u)
            used_ids.add(v)

        if not used_ids and dag.num_nodes > 0:
            used_ids = {n.id for n in dag.nodes}

        ids_before = {n.id for n in dag.nodes}
        removed_ids = ids_before - used_ids

        new_nodes = [n for n in dag.nodes if n.id in used_ids]
        new_edges = [(u, v) for u, v in dag.edges if u in used_ids and v in used_ids]

        result = ExecutionDAG(nodes=new_nodes, edges=new_edges)

        for n in result.nodes:
            n.dependencies = [d for d in n.dependencies if d in used_ids]

        for rid in sorted(removed_ids):
            pass

        return result

    def metadata(self) -> PassMetadata:
        return PassMetadata(
            name=self.name,
            version=self.version,
            cost=0.01,
            gain=0.15,
        )
