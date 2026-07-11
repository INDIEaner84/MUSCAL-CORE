from runtime.optimizer.base_pass import OptimizationPass, PassMetadata
from runtime.optimizer.graph import DAGNode, ExecutionDAG


class NodeFusion(OptimizationPass):
    name = "node_fusion"
    version = "0.1"

    FUSION_RULES: list[tuple[str, str, str, str]] = [
        ("validate", "filesystem.write", "validate+filesystem.write", "write"),
        ("validate", "browser.open", "validate+browser.open", "open"),
        ("browser.open", "browser.click", "browser.open+click", "open_and_click"),
        ("browser.open", "browser.type", "browser.open+type", "open_and_type"),
        ("filesystem.write", "validate", "filesystem.write+validate", "write_and_validate"),
    ]

    def optimize(self, dag: ExecutionDAG) -> ExecutionDAG:
        fusion_map: dict[str, str] = {}
        skip: set[str] = set()
        new_nodes: list[DAGNode] = []
        new_edges: list[tuple[str, str]] = []

        sorted_ids = [n.id for n in dag.nodes]
        for i, nid in enumerate(sorted_ids):
            if nid in skip:
                continue
            node = dag.get_node(nid)
            if node is None:
                continue

            fused = False
            for src_op, dst_op, fused_op, fusion_type in self.FUSION_RULES:
                if node.op != src_op:
                    continue
                if i + 1 >= len(sorted_ids):
                    continue
                next_id = sorted_ids[i + 1]
                if next_id in skip:
                    continue
                next_node = dag.get_node(next_id)
                if next_node is None or next_node.op != dst_op:
                    continue

                fusion_id = f"fusion_{nid}_{next_id}"
                combined_cost = node.cost_vector + next_node.cost_vector
                combined_cost.tool_calls = 1
                combined_cost.latency = max(node.cost_vector.latency, next_node.cost_vector.latency) * 0.7

                fused_deps = list(set(node.dependencies + next_node.dependencies))
                if nid in fused_deps:
                    fused_deps.remove(nid)
                if next_id in fused_deps:
                    fused_deps.remove(next_id)

                fused_node = DAGNode(
                    id=fusion_id,
                    op=fused_op,
                    cost_vector=combined_cost,
                    dependencies=fused_deps,
                    metadata={
                        "fusion_type": fusion_type,
                        "source_nodes": [nid, next_id],
                        "original_ops": [node.op, next_node.op],
                    },
                )
                new_nodes.append(fused_node)
                skip.add(nid)
                skip.add(next_id)
                fusion_map[nid] = fusion_id
                fusion_map[next_id] = fusion_id
                fused = True
                break

            if not fused:
                new_nodes.append(node)

        for u, v in dag.edges:
            nu = fusion_map.get(u, u)
            nv = fusion_map.get(v, v)
            if nu != nv and nu not in skip and nv not in skip:
                edge = (nu, nv)
                if not any(a == nu and b == nv for a, b in new_edges):
                    new_edges.append(edge)

        for node in new_nodes:
            node.dependencies = [
                fusion_map.get(d, d) for d in node.dependencies
                if fusion_map.get(d, d) != node.id
            ]

        return ExecutionDAG(nodes=new_nodes, edges=new_edges)

    def metadata(self) -> PassMetadata:
        return PassMetadata(
            name=self.name,
            version=self.version,
            cost=0.02,
            gain=0.25,
        )
