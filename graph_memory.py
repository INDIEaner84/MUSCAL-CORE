from typing import Any, Dict, List, Optional


class GraphMemory:
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: List[Dict[str, str]] = []

    def add_node(self, node_id: str, content: Any) -> None:
        self.nodes[node_id] = content

    def add_edge(self, from_id: str, to_id: str, relation: str) -> None:
        self.edges.append({"from": from_id, "to": to_id, "relation": relation})

    def get_node(self, node_id: str) -> Optional[Any]:
        return self.nodes.get(node_id)

    def get_related(self, node_id: str) -> List[Dict[str, str]]:
        return [e for e in self.edges if e["from"] == node_id or e["to"] == node_id]

    def query(self, keyword: str) -> Dict[str, Any]:
        return {
            "nodes": {k: v for k, v in self.nodes.items() if keyword.lower() in str(v).lower()}
        }

    def query_related(self, node_id: str) -> List[Dict[str, str]]:
        return self.get_related(node_id)

    def ingest(self, text: str) -> None:
        pass
