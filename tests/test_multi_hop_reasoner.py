import pytest


class _FakeGraph:
    def __init__(self):
        self.nodes = {}

    def query_related(self, node_id):
        edges = []
        for e in self._edges:
            if e[0] == node_id:
                edges.append(e)
        return edges

    def _add_edge(self, source, rel, target):
        if not hasattr(self, "_edges"):
            self._edges = []
        self._edges.append((source, rel, target))


def test_expand_basic():
    from multi_hop_reasoner import MultiHopReasoner
    g = _FakeGraph()
    g.nodes["n1"] = "hello world"
    g.nodes["n2"] = "foo bar"
    g.nodes["n3"] = "baz qux"
    g._add_edge("n1", "related", "n2")
    g._add_edge("n2", "related", "n3")

    r = MultiHopReasoner(g)
    result = r.expand("hello", depth=2)
    assert len(result) == 2
    assert ("n1", "related", "n2") in result
    assert ("n2", "related", "n3") in result


def test_expand_no_match():
    from multi_hop_reasoner import MultiHopReasoner
    g = _FakeGraph()
    g.nodes["n1"] = "something"
    r = MultiHopReasoner(g)
    result = r.expand("nonexistent", depth=2)
    assert result == []


def test_expand_depth_zero():
    from multi_hop_reasoner import MultiHopReasoner
    g = _FakeGraph()
    g.nodes["n1"] = "hello"
    g._add_edge("n1", "related", "n2")
    r = MultiHopReasoner(g)
    result = r.expand("hello", depth=0)
    assert result == []


def test_expand_visit_each_once():
    from multi_hop_reasoner import MultiHopReasoner
    g = _FakeGraph()
    g.nodes["n1"] = "start"
    g.nodes["n2"] = "mid"
    g.nodes["n3"] = "end"
    g._add_edge("n1", "to", "n2")
    g._add_edge("n2", "to", "n3")
    g._add_edge("n1", "direct", "n3")

    r = MultiHopReasoner(g)
    result = r.expand("start", depth=3)
    assert len(result) == 3
    assert ("n1", "to", "n2") in result
    assert ("n2", "to", "n3") in result
    assert ("n1", "direct", "n3") in result
