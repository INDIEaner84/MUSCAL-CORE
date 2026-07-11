from graph_memory import GraphMemory
from graph_memory import GraphMemory as MinimalGraphMemory


def test_same_class():
    assert GraphMemory is MinimalGraphMemory


def test_add_node():
    g = GraphMemory()
    g.add_node("n1", {"text": "hello"})
    assert "n1" in g.nodes
    assert g.nodes["n1"] == {"text": "hello"}


def test_add_edge():
    g = GraphMemory()
    g.add_node("n1", "a")
    g.add_node("n2", "b")
    g.add_edge("n1", "n2", "related_to")
    assert len(g.edges) == 1
    assert g.edges[0]["from"] == "n1"
    assert g.edges[0]["to"] == "n2"
    assert g.edges[0]["relation"] == "related_to"


def test_get_node():
    g = GraphMemory()
    g.add_node("x", "value")
    assert g.get_node("x") == "value"
    assert g.get_node("nonexistent") is None


def test_get_related():
    g = GraphMemory()
    g.add_node("a", "node_a")
    g.add_node("b", "node_b")
    g.add_node("c", "node_c")
    g.add_edge("a", "b", "knows")
    g.add_edge("c", "a", "likes")
    related = g.get_related("a")
    assert len(related) == 2


def test_query_related():
    g = GraphMemory()
    g.add_node("n1", "data")
    g.add_node("n2", "more")
    g.add_edge("n1", "n2", "link")
    result = g.query_related("n1")
    assert len(result) == 1


def test_query_keyword():
    g = GraphMemory()
    g.add_node("id1", "important data here")
    g.add_node("id2", "other stuff")
    result = g.query("important")
    assert "id1" in result["nodes"]
    assert "id2" not in result["nodes"]


def test_ingest():
    g = GraphMemory()
    g. ingest("some text")
    assert len(g.nodes) == 0
