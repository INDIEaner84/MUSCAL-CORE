from runtime.optimizer.base_pass import OptimizationPass, PassMetadata
from runtime.optimizer.graph import ExecutionDAG


class ParallelizationPass(OptimizationPass):
    name = "parallelization"
    version = "0.1"

    def optimize(self, dag: ExecutionDAG) -> ExecutionDAG:
        layers = dag.topological_sort()

        for node in dag.nodes:
            node.metadata["parallel_layer"] = 0

        for layer_idx, layer_nodes in enumerate(layers):
            for node in layer_nodes:
                existing = dag.get_node(node.id)
                if existing:
                    existing.metadata["parallel_layer"] = layer_idx

        return dag

    def metadata(self) -> PassMetadata:
        return PassMetadata(
            name=self.name,
            version=self.version,
            cost=0.01,
            gain=0.35,
        )
