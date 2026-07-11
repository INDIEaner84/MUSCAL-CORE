def test_route_sends_to_first_node():
    from task_router import TaskRouter
    received = []

    class FakeNode:
        def receive(self, msg):
            received.append(msg)

    r = TaskRouter()
    r.route([FakeNode(), FakeNode()], {"tool": "print", "args": ["hello"]})

    assert len(received) == 1
    assert received[0]["type"] == "TASK"
    assert received[0]["tool"] == "print"
    assert received[0]["args"] == ["hello"]


def test_send_direct():
    from task_router import TaskRouter
    received = []

    class FakeNode:
        def receive(self, msg):
            received.append(msg)

    r = TaskRouter()
    r.send(FakeNode(), {"tool": "add", "args": [1, 2]})

    assert len(received) == 1
    assert received[0]["tool"] == "add"
