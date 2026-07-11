from event_bus import EventBus, EventPriority


def test_publish_subscribe():
    bus = EventBus()
    received = []
    def handler(msg):
        received.append(msg)
    bus.subscribe("test.topic", handler)
    msg = bus.publish("test.topic", {"key": "value"}, source="test")
    assert len(received) == 1
    assert received[0] is msg
    assert received[0].topic == "test.topic"
    assert received[0].payload == {"key": "value"}
    assert received[0].source == "test"
    assert received[0].priority == EventPriority.NORMAL


def test_unsubscribe():
    bus = EventBus()
    calls = []
    def handler(msg):
        calls.append(msg)
    bus.subscribe("test.topic", handler)
    bus.publish("test.topic", {})
    assert len(calls) == 1
    bus.unsubscribe("test.topic", handler)
    bus.publish("test.topic", {})
    assert len(calls) == 1


def test_wildcard_subscriber():
    bus = EventBus()
    wildcard_calls = []
    def wildcard(msg):
        wildcard_calls.append(msg.topic)
    bus.subscribe("*", wildcard)
    bus.publish("alpha", {})
    bus.publish("beta", {})
    bus.publish("gamma", {})
    assert wildcard_calls == ["alpha", "beta", "gamma"]


def test_history_and_stats():
    bus = EventBus()
    bus.publish("a", {})
    bus.publish("b", {})
    bus.publish("a", {})
    history_all = bus.get_history(limit=10)
    assert len(history_all) == 3
    history_a = bus.get_history(topic="a", limit=10)
    assert len(history_a) == 2
    for msg in history_a:
        assert msg.topic == "a"
    stats = bus.get_stats()
    assert stats["total_events"] == 3
    assert stats["topic_counts"]["a"] == 2
    assert stats["topic_counts"]["b"] == 1
    assert stats["subscriber_count"] == 0
    assert stats["topics"] == []


def test_clear():
    bus = EventBus()
    bus.publish("a", {})
    bus.publish("b", {})
    assert bus.get_stats()["total_events"] == 2
    bus.clear()
    assert bus.get_stats()["total_events"] == 0
    assert bus.get_stats()["topic_counts"] == {}
