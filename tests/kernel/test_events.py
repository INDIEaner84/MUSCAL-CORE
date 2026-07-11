from event_bus import EventBus


class TestEventBus:
    def setup_method(self):
        self.bus = EventBus()

    def test_publish_subscribe(self):
        received = []
        def handler(msg):
            received.append(msg)
        self.bus.subscribe("test.topic", handler)
        self.bus.publish("test.topic", {"key": "value"}, source="test")
        assert len(received) == 1
        assert received[0].topic == "test.topic"
        assert received[0].payload.get("key") == "value"

    def test_multi_topic(self):
        received = []
        received2 = []
        def handler(msg):
            received.append(msg)
        def handler2(msg):
            received2.append(msg)
        self.bus.subscribe("test.topic", handler)
        self.bus.subscribe("other.topic", handler2)
        self.bus.subscribe("*", handler2)
        self.bus.publish("test.topic", {"n": 1})
        self.bus.publish("other.topic", {"n": 2})
        # handler: only test.topic (1 event)
        # handler2: test.topic via * + other.topic directly + other.topic via * = 3
        assert len(received) == 1
        assert len(received2) == 3

    def test_history(self):
        received = []
        def handler(msg):
            received.append(msg)
        self.bus.subscribe("test.topic", handler)
        self.bus.publish("test.topic", {"key": "value"})
        hist = self.bus.get_history(limit=5)
        assert len(hist) >= 1
        filtered = self.bus.get_history(topic="test.topic", limit=5)
        assert len(filtered) >= 1

    def test_stats(self):
        received = []
        def handler(msg):
            received.append(msg)
        self.bus.subscribe("test.topic", handler)
        self.bus.publish("test.topic", {"n": 1})
        self.bus.publish("other.topic", {"n": 2})
        stats = self.bus.get_stats()
        assert stats["total_events"] >= 2
        assert len(stats["topic_counts"]) >= 2

    def test_unsubscribe(self):
        received = []
        def handler(msg):
            received.append(msg)
        self.bus.subscribe("test.topic", handler)
        self.bus.publish("test.topic", {"first": True})
        self.bus.unsubscribe("test.topic", handler)
        self.bus.publish("test.topic", {"final": True})
        assert len(received) == 1
