import uuid


class MCXFGraphBuilder:
    def __init__(self, graph):
        self.graph = graph

    def ingest(self, mcxf):
        node_id = str(uuid.uuid4())
        self.graph.add_node(node_id, mcxf)
        self._infer_relations(node_id, mcxf)
        return node_id

    def _infer_relations(self, node_id, mcxf):
        text = str(mcxf)
        if "DECISION" in text:
            self.graph.add_edge(node_id, "DECISIONS_HUB", "BELONGS_TO")
        if "TASK" in text:
            self.graph.add_edge(node_id, "TASKS_HUB", "BELONGS_TO")
        if "ARCHITECTURE" in text:
            self.graph.add_edge(node_id, "ARCH_HUB", "BELONGS_TO")


def store_mcxf_graph(mcxf):
    from mcxf_fusion import get_fusion_layer
    fusion = get_fusion_layer()
    if fusion is None or fusion.graph_builder is None:
        return None
    return fusion.graph_builder.ingest(mcxf)
