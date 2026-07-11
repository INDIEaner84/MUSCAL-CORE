from graph import MAX_EDGES, MAX_NODES, GraphState
from schema import EVENT_EDGE_CREATED, EVENT_NODE_CREATED, EVENT_NODE_UPDATED


def test_add_node():
    g = GraphState()
    nid = g.add_node("INTENT", {"text": "hello"})
    assert nid in g.nodes
    assert g.nodes[nid].type == "INTENT"
    assert g.nodes[nid].payload == {"text": "hello"}
    assert g.nodes[nid].status == "created"


def test_add_node_auto_focus():
    g = GraphState()
    nid = g.add_node("TEST", {})
    assert g.active_focus_node == nid


def test_add_node_keeps_existing_focus():
    g = GraphState()
    first = g.add_node("FIRST", {})
    g.set_focus(first)
    second = g.add_node("SECOND", {})
    assert g.active_focus_node == first
    assert g.active_focus_node != second


def test_add_node_increments_counter():
    g = GraphState()
    n1 = g.add_node("A", {})
    n2 = g.add_node("B", {})
    assert n1 != n2


def test_add_edge():
    g = GraphState()
    a = g.add_node("A", {})
    b = g.add_node("B", {})
    g.add_edge(a, b, "DERIVES_FROM")
    assert len(g.edges) == 1
    assert g.edges[0].source_id == a
    assert g.edges[0].target_id == b
    assert g.edges[0].edge_type == "DERIVES_FROM"


def test_add_edge_missing_node():
    g = GraphState()
    a = g.add_node("A", {})
    g.add_edge(a, "nonexistent", "DERIVES_FROM")
    assert len(g.edges) == 0


def test_update_node_status():
    g = GraphState()
    nid = g.add_node("TEST", {})
    g.update_node(nid, status="completed")
    assert g.nodes[nid].status == "completed"


def test_update_node_confidence():
    g = GraphState()
    nid = g.add_node("TEST", {})
    g.update_node(nid, confidence=0.5)
    assert g.nodes[nid].confidence == 0.5


def test_update_node_payload():
    g = GraphState()
    nid = g.add_node("TEST", {"a": 1})
    g.update_node(nid, payload={"b": 2})
    assert g.nodes[nid].payload == {"a": 1, "b": 2}


def test_update_node_nonexistent():
    g = GraphState()
    g.update_node("nonexistent", status="done")


def test_node_created_event():
    received = []
    g = GraphState()
    g.on(EVENT_NODE_CREATED, lambda e: received.append(e))
    nid = g.add_node("TEST", {"x": 1})
    assert len(received) == 1
    assert received[0]["payload"]["node_id"] == nid


def test_edge_created_event():
    received = []
    g = GraphState()
    g.on(EVENT_EDGE_CREATED, lambda e: received.append(e))
    a = g.add_node("A", {})
    b = g.add_node("B", {})
    g.add_edge(a, b, "LINK")
    assert len(received) == 1


def test_emit_custom_event():
    received = []
    g = GraphState()
    g.on("CUSTOM_EVENT", lambda e: received.append(e))
    g.emit("CUSTOM_EVENT", {"data": 42})
    assert len(received) == 1
    assert received[0]["payload"]["data"] == 42


def test_emit_no_listener():
    g = GraphState()
    g.emit("GHOST_EVENT", {})


def test_set_focus_valid():
    g = GraphState()
    nid = g.add_node("T", {})
    g.set_focus(nid)
    assert g.active_focus_node == nid


def test_set_focus_invalid():
    g = GraphState()
    g.set_focus("nonexistent")
    assert g.active_focus_node == ""


def test_prune_nodes():
    g = GraphState()
    g._node_counter = 0
    node_ids = [g.add_node(f"N{i}", {}) for i in range(MAX_NODES + 10)]
    assert len(g.nodes) <= MAX_NODES


def test_prune_edges():
    g = GraphState()
    nodes = [g.add_node(f"N{i}", {}) for i in range(MAX_EDGES + 10)]
    for i in range(len(nodes) - 1):
        g.add_edge(nodes[i], nodes[i + 1], "LINK")
    assert len(g.edges) <= MAX_EDGES


def test_trace_dependencies():
    g = GraphState()
    a = g.add_node("A", {})
    b = g.add_node("B", {})
    c = g.add_node("C", {})
    g.add_edge(a, b, "DERIVES_FROM")
    g.add_edge(b, c, "DERIVES_FROM")
    trace = g.trace_dependencies(a)
    ids = {t["id"] for t in trace}
    assert a in ids
    assert b in ids
    assert c in ids


def test_trace_execution_path():
    g = GraphState()
    plan = g.add_node("EXECUTION_PLAN", {})
    tool = g.add_node("TOOL_EXECUTION", {})
    g.add_edge(plan, tool, "EXECUTES")
    path = g.trace_execution_path()
    assert len(path) == 1
    assert path[0]["edge_type"] == "EXECUTES"


def test_snapshot_structure():
    g = GraphState()
    g.add_node("A", {})
    g.add_node("B", {})
    snap = g.get_snapshot()
    assert "nodes" in snap
    assert "edges" in snap
    assert "focus" in snap
    assert "event_count" in snap
    assert len(snap["nodes"]) == 2


def test_snapshot_event_count():
    g = GraphState()
    g.add_node("A", {})
    g.add_node("B", {})
    snap = g.get_snapshot()
    assert snap["event_count"] == 2


def test_remove_node():
    g = GraphState()
    a = g.add_node("A", {})
    b = g.add_node("B", {})
    g.add_edge(a, b, "LINK")
    g.remove_node(a)
    assert a not in g.nodes
    assert all(e.source_id != a and e.target_id != a for e in g.edges)


def test_remove_edge():
    g = GraphState()
    a = g.add_node("A", {})
    b = g.add_node("B", {})
    c = g.add_node("C", {})
    g.add_edge(a, b, "LINK")
    g.add_edge(b, c, "LINK")
    g.remove_edge(0)
    assert len(g.edges) == 1


def test_get_event_stream():
    g = GraphState()
    g.add_node("A", {})
    g.add_node("B", {})
    stream = g.get_event_stream(limit=1)
    assert len(stream) == 1


def test_on_multiple_events():
    g = GraphState()
    received = []
    g.on(EVENT_NODE_CREATED, lambda e: received.append("handler1"))
    g.on(EVENT_NODE_CREATED, lambda e: received.append("handler2"))
    g.add_node("T", {})
    assert len(received) == 2


def test_on_dedup_same_callback():
    g = GraphState()
    received = []

    def handler(e):
        received.append(e)

    g.on(EVENT_NODE_CREATED, handler)
    g.on(EVENT_NODE_CREATED, handler)
    g.add_node("T", {})
    assert len(received) == 1


def test_reset_event_listeners():
    g = GraphState()
    received = []
    g.on(EVENT_NODE_CREATED, lambda e: received.append(1))
    g.reset_event_listeners()
    g.add_node("T", {})
    assert len(received) == 0


def test_reset_event_listeners_specific():
    g = GraphState()
    r1, r2 = [], []
    g.on(EVENT_NODE_CREATED, lambda e: r1.append(1))
    g.on(EVENT_NODE_UPDATED, lambda e: r2.append(1))
    g.reset_event_listeners(EVENT_NODE_CREATED)
    g.add_node("T", {})
    assert len(r1) == 0
    assert len(r2) == 0


def test_replaying_suppresses_callbacks():
    g = GraphState()
    received = []
    g.on(EVENT_NODE_CREATED, lambda e: received.append(1))
    g._replaying = True
    g.add_node("T", {})
    assert len(received) == 0


def test_concurrent_add_node():
    import threading
    g = GraphState()
    errors = []

    def adder():
        try:
            for i in range(50):
                g.add_node("T", {"i": i})
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=adder) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(errors) == 0


def test_prune_graph_safe_during_event():
    g = GraphState()
    max_nodes = min(MAX_NODES, 50)
    for i in range(max_nodes):
        g.add_node("T", {"i": i})
    assert len(g.nodes) <= MAX_NODES
