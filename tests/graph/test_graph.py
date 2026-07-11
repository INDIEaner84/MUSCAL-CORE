from unittest import mock
from kernel import MuscalKernel
import graph as graph_mod
from schema import (
    EDGE_TYPE_DERIVES_FROM,
    EDGE_TYPE_EXECUTES,
    EVENT_EDGE_CREATED,
    EVENT_EXECUTION_FINISHED,
    EVENT_EXECUTION_STARTED,
    EVENT_NODE_CREATED,
    EVENT_NODE_UPDATED,
    EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
    EVENT_SYSTEM_ACTION_STARTED,
    NODE_TYPE_INTENT,
    NODE_TYPE_TOOL_EXECUTION,
)

ALL_EVENTS = [
    EVENT_NODE_CREATED, EVENT_NODE_UPDATED, EVENT_EDGE_CREATED,
    EVENT_EXECUTION_STARTED, EVENT_EXECUTION_FINISHED,
    EVENT_SYSTEM_ACTION_STARTED, EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
]

SYSTEM_ACTION_EVENTS = {
    EVENT_SYSTEM_ACTION_STARTED, EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
}

NON_SYSTEM_EVENTS = [e for e in ALL_EVENTS if e not in SYSTEM_ACTION_EVENTS]


class TestGraphLambdaClosure:
    def test_listener_counts(self):
        k = MuscalKernel(enable_graph=True, enable_sphere=True)
        g = k.graph
        for evt in ALL_EVENTS:
            listener_count = len(g._event_listeners.get(evt, []))
            expected = 2 if evt in SYSTEM_ACTION_EVENTS else 1
            assert listener_count == expected, f"{evt}: {listener_count} (expected {expected})"

    def test_distinct_lambda_objects(self):
        k = MuscalKernel(enable_graph=True, enable_sphere=True)
        g = k.graph
        all_listeners = []
        for evt in ALL_EVENTS:
            all_listeners.extend(g._event_listeners.get(evt, []))
        unique_count = len(set(id(fn) for fn in all_listeners))
        assert unique_count == 11


class TestGraphEventRouting:
    def test_sphere_sync_called_for_each_event(self):
        k1 = MuscalKernel(enable_graph=True, enable_sphere=True)
        g1 = k1.graph
        with mock.patch.object(k1.system, 'on_action_event'):
            with mock.patch.object(k1.sphere, 'sync') as mock_sync:
                for evt in ALL_EVENTS:
                    g1.emit(evt, {})
        assert mock_sync.call_count == 8

    def test_system_action_routing(self):
        k2 = MuscalKernel(enable_graph=True, enable_sphere=True)
        g2 = k2.graph
        with mock.patch.object(k2.system, 'on_action_event') as mock_handler:
            for evt in NON_SYSTEM_EVENTS:
                g2.emit(evt, {"type": evt, "payload": {"tool": "test"}})
            assert mock_handler.call_count == 0
            for evt in SYSTEM_ACTION_EVENTS:
                g2.emit(evt, {"type": evt, "payload": {"tool": "test"}})
            assert mock_handler.call_count == 3


class TestGraphNodeEdgeOperations:
    def test_add_node_and_edge(self):
        k3 = MuscalKernel(enable_graph=True)
        g3 = k3.graph
        n1 = g3.add_node(NODE_TYPE_INTENT, {"text": "hello"})
        assert n1 is not None
        assert n1 in g3.nodes
        n2 = g3.add_node(NODE_TYPE_INTENT, {"text": "world"})
        g3.add_edge(n1, n2, EDGE_TYPE_DERIVES_FROM)
        assert len(g3.edges) == 1

    def test_remove_node(self):
        k3 = MuscalKernel(enable_graph=True)
        g3 = k3.graph
        n1 = g3.add_node(NODE_TYPE_INTENT, {"text": "hello"})
        n2 = g3.add_node(NODE_TYPE_INTENT, {"text": "world"})
        g3.add_edge(n1, n2, EDGE_TYPE_DERIVES_FROM)
        node_count_before = len(g3.nodes)
        g3.remove_node(n1)
        assert len(g3.nodes) == node_count_before - 1
        assert n1 not in g3.nodes


class TestGraphPruning:
    SMALL_N = 100

    def test_prune_nodes(self):
        orig_nodes = graph_mod.MAX_NODES
        orig_edges = graph_mod.MAX_EDGES
        graph_mod.MAX_NODES = self.SMALL_N
        graph_mod.MAX_EDGES = self.SMALL_N * 2
        try:
            k4 = MuscalKernel(enable_graph=True)
            g4 = k4.graph
            for i in range(self.SMALL_N + 1):
                g4.add_node(NODE_TYPE_INTENT, {"i": i})
            assert len(g4.nodes) <= self.SMALL_N
        finally:
            graph_mod.MAX_NODES = orig_nodes
            graph_mod.MAX_EDGES = orig_edges

    def test_prune_edges(self):
        orig_nodes = graph_mod.MAX_NODES
        orig_edges = graph_mod.MAX_EDGES
        graph_mod.MAX_NODES = self.SMALL_N
        graph_mod.MAX_EDGES = self.SMALL_N * 2
        try:
            k4 = MuscalKernel(enable_graph=True)
            g4 = k4.graph
            ids = list(g4.nodes.keys())
            for i in range(min(len(ids), self.SMALL_N * 2)):
                g4.add_edge(ids[i % len(ids)], ids[(i + 1) % len(ids)], EDGE_TYPE_EXECUTES)
            g4.prune_graph()
            assert len(g4.edges) <= self.SMALL_N * 2
        finally:
            graph_mod.MAX_NODES = orig_nodes
            graph_mod.MAX_EDGES = orig_edges
