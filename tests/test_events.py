"""EventBus publish/subscribe/routing tests."""

from event_bus import EventBus, EventPriority


def test_publish_subscribe():
    bus = EventBus()
    received = []
    bus.subscribe("test.topic", lambda m: received.append(m))
    msg = bus.publish("test.topic", {"key": "value"})
    assert len(received) == 1
    assert received[0].topic == "test.topic"
    assert received[0].payload == {"key": "value"}


def test_publish_no_subscriber():
    bus = EventBus()
    msg = bus.publish("orphan.topic", {})
    assert msg.topic == "orphan.topic"


def test_unsubscribe():
    bus = EventBus()
    received = []

    def handler(msg):
        received.append(msg)

    bus.subscribe("test", handler)
    bus.publish("test", {"i": 1})
    bus.unsubscribe("test", handler)
    bus.publish("test", {"i": 2})
    assert len(received) == 1


def test_wildcard_subscriber():
    bus = EventBus()
    received = []
    bus.subscribe("*", lambda m: received.append(m))
    bus.publish("any.topic", {})
    bus.publish("other.topic", {})
    assert len(received) == 2


def test_priority_field():
    bus = EventBus()
    msg = bus.publish("urgent", {}, priority=EventPriority.HIGH)
    assert msg.priority == EventPriority.HIGH


def test_get_history():
    bus = EventBus()
    bus.publish("a", {"n": 1})
    bus.publish("b", {"n": 2})
    hist = bus.get_history(limit=10)
    assert len(hist) == 2


def test_get_history_filtered():
    bus = EventBus()
    bus.publish("a", {"n": 1})
    bus.publish("b", {"n": 2})
    bus.publish("a", {"n": 3})
    hist = bus.get_history(topic="a", limit=10)
    assert len(hist) == 2
    assert all(m.topic == "a" for m in hist)


def test_get_stats():
    bus = EventBus()
    bus.subscribe("x", lambda m: None)
    bus.publish("x", {"i": 1})
    bus.publish("y", {"i": 2})
    stats = bus.get_stats()
    assert stats["total_events"] == 2
    assert stats["subscriber_count"] == 1
    assert "x" in stats["topics"]


def test_history_max_limit():
    bus = EventBus()
    bus._max_history = 3
    for i in range(5):
        bus.publish("t", {"i": i})
    assert len(bus._history) == 3
    assert bus._history[0].payload["i"] == 2


def test_clear():
    bus = EventBus()
    bus.publish("a", {})
    bus.publish("b", {})
    bus.clear()
    assert len(bus._history) == 0
    assert len(bus._topic_counts) == 0


def test_source_field():
    bus = EventBus()
    msg = bus.publish("t", {}, source="test_src")
    assert msg.source == "test_src"


def test_timestamp_is_set():
    bus = EventBus()
    msg = bus.publish("t", {})
    assert msg.timestamp > 0


def test_multiple_subscribers():
    bus = EventBus()
    r1, r2 = [], []
    bus.subscribe("t", lambda m: r1.append(m))
    bus.subscribe("t", lambda m: r2.append(m))
    bus.publish("t", {})
    assert len(r1) == 1
    assert len(r2) == 1


def test_different_topics_independent():
    bus = EventBus()
    received = []
    bus.subscribe("a", lambda m: received.append("a"))
    bus.publish("b", {})
    assert len(received) == 0


def test_subscribe_idempotent():
    bus = EventBus()
    received = []
    bus.subscribe("t", lambda m: received.append(m))
    bus.subscribe("t", lambda m: received.append(m))
    bus.publish("t", {})
    assert len(received) == 2


def test_subscribe_same_callback_once():
    bus = EventBus()
    received = []

    def handler(m):
        received.append(m)

    bus.subscribe("t", handler)
    bus.subscribe("t", handler)
    bus.publish("t", {})
    assert len(received) == 1


def test_listener_isolation():
    bus = EventBus()
    received = []

    def failing(m):
        raise ValueError("boom")

    bus.subscribe("t", failing)
    bus.subscribe("t", lambda m: received.append(m))
    bus.publish("t", {})
    assert len(received) == 1


def test_clear_during_dispatch():
    bus = EventBus()

    def clr(m):
        bus.clear()

    bus.subscribe("t", clr)
    bus.subscribe("t", lambda m: bus.publish("t", {}))
    bus.publish("t", {})
    assert len(bus._history) == 0


def test_concurrent_publish_subscribe():
    import threading
    bus = EventBus()
    errors = []

    def publisher():
        for i in range(100):
            bus.publish("t", {"i": i})

    def subscriber():
        for i in range(100):
            bus.subscribe("t", lambda m: None)

    threads = [threading.Thread(target=publisher) for _ in range(4)]
    threads += [threading.Thread(target=subscriber) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    stats = bus.get_stats()
    assert stats["total_events"] == 400
    assert not errors


def test_history_50k_overflow():
    bus = EventBus()
    bus._max_history = 50000
    for i in range(50001):
        bus.publish("t", {"i": i})
    assert len(bus._history) == 50000
    assert bus._history[0].payload["i"] == 1
