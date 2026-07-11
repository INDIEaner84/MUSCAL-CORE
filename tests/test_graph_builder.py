import pytest


class _FakeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, nid, text):
        self.nodes[nid] = text

    def add_edge(self, a, b, rel):
        self.edges.append((a, b, rel))


def test_ingest_basic():
    from graph_builder import GraphBuilder
    g = _FakeGraph()
    b = GraphBuilder(g)
    b.ingest("MUSCAL is a cognitive architecture")
    assert len(g.nodes) == 2
    assert len(g.edges) == 1


def test_ingest_counter_increments():
    from graph_builder import GraphBuilder
    g = _FakeGraph()
    b = GraphBuilder(g)
    b.ingest("first sentence")
    nid1 = list(g.nodes.keys())
    b.ingest("second sentence")
    nid2 = list(g.nodes.keys())
    assert len(set(nid1) & set(nid2)) == 0


def test_ingest_empty_text():
    from graph_builder import GraphBuilder
    g = _FakeGraph()
    b = GraphBuilder(g)
    b.ingest("")
    assert len(g.nodes) <= 2
