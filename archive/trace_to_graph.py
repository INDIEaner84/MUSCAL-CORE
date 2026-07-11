from graph_node import GraphNode


class TraceToGraph:
    def __init__(self, store):
        self.store = store

    def ingest(self, trace_event):
        node = GraphNode(
            node_id=trace_event["id"],
            node_type=trace_event["type"],
            payload=trace_event["data"]
        )

        self.store.add_node(node)

        if "parent" in trace_event:
            self.store.add_edge(trace_event["parent"], node.id)
