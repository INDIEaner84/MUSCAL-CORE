from event_bus import EventBus


# ─── Test 1: Listener Isolation ─────────────────────────────
# OVERRIDE-025.1: Listener Failure → Continue → alle weiteren Listener werden aufgerufen.

def test_listener_isolation():
    bus = EventBus()
    called = []

    def failing(_msg):
        raise RuntimeError("BOOM")

    def working(msg):
        called.append(msg.payload["step"])

    bus.subscribe("test", failing)
    bus.subscribe("test", working)

    bus.publish("test", {"step": 1})
    bus.publish("test", {"step": 2})

    assert called == [1, 2]


# ─── Test 2: Event Ordering ─────────────────────────────────
# FIFO-Garantie: Listener werden in Registrierungsreihenfolge aufgerufen.

def test_event_ordering():
    bus = EventBus()
    order = []

    def first(_msg):
        order.append("first")

    def second(_msg):
        order.append("second")

    bus.subscribe("test", first)
    bus.subscribe("test", second)
    bus.publish("test")

    assert order == ["first", "second"]


# ─── Test 3a: Duplicate Registration (current) ──────────────
# OVERRIDE-025.2: subscribe() idempotent → selbes Callback 2× registriert → 1× aufgerufen.

def test_duplicate_registration_current():
    bus = EventBus()
    calls = []

    def handler(_msg):
        calls.append(1)

    bus.subscribe("test", handler)
    bus.subscribe("test", handler)
    bus.publish("test")

    assert len(calls) == 1


# ─── Test 3b: Duplicate Registration (idempotent) ───────────
# OVERRIDE-025.2: subscribe() prüft auf Duplikate → selbes Callback 1× aufgerufen.

def test_duplicate_registration_idempotent():
    bus = EventBus()
    calls = []

    def handler(_msg):
        calls.append(1)

    bus.subscribe("test", handler)
    bus.subscribe("test", handler)
    bus.publish("test")

    assert len(calls) == 1


# ─── Test 4: Replay Compatibility ───────────────────────────
# Events aus History müssen reproduzierbar sein:
# Payload + Metadaten (topic, source, timestamp) bleiben erhalten.

def test_replay_compatibility():
    bus = EventBus()
    results = []

    def handler(msg):
        results.append({
            "step": msg.payload["step"],
            "topic": msg.topic,
            "source": msg.source,
            "timestamp": msg.timestamp,
            "id": msg.id,
        })

    bus.subscribe("replay", handler)
    bus.publish("replay", {"step": 1}, source="test")

    history = bus.get_history(topic="replay", limit=1)
    orig = history[0]

    bus.publish(orig.topic, payload=orig.payload, source=orig.source)

    assert results[0]["step"] == results[1]["step"]
    assert results[0]["topic"] == results[1]["topic"]
    assert results[0]["source"] == results[1]["source"]
    assert results[0]["timestamp"] < results[1]["timestamp"]
    assert results[0]["id"] != results[1]["id"]


# ─── Test 5: Payload Mutation ────────────────────────────────
# OVERRIDE-025.3: publish() → deepcopy → immutable history.

def test_payload_mutation():
    bus = EventBus()
    captured = []

    def capture(msg):
        captured.append(msg)

    bus.subscribe("mutation", capture)
    payload = {"a": 1}
    bus.publish("mutation", payload)

    payload["a"] = 99

    stored = bus.get_history(topic="mutation", limit=1)[0]
    assert stored.payload["a"] == 1
