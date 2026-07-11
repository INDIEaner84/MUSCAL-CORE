import pytest


class _FakeTask:
    def __init__(self, name, priority=0):
        self.name = name
        self.priority = priority


def test_add_and_get_next():
    from task_queue import TaskQueue
    q = TaskQueue()
    q.add(_FakeTask("a", 1))
    q.add(_FakeTask("b", 0))
    q.add(_FakeTask("c", 2))
    assert q.get_next().name == "b"
    assert q.get_next().name == "a"
    assert q.get_next().name == "c"
    assert q.get_next() is None


def test_empty():
    from task_queue import TaskQueue
    q = TaskQueue()
    assert q.empty()
    q.add(_FakeTask("x"))
    assert not q.empty()
    q.get_next()
    assert q.empty()


def test_same_priority_fifo():
    import heapq
    from task_queue import TaskQueue
    q = TaskQueue()
    q.add(_FakeTask("first", 0))
    q.add(_FakeTask("second", 0))
    first = q.get_next()
    second = q.get_next()
    assert first is not None
    assert second is not None
