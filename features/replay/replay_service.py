from typing import Any, Dict, Optional

from event_bus import EventBus
from runtime.event_store import EventStore


class ReplayService:
    """Replay-Orchestrierung: liest aus EventStore, republish über EventBus.

    EventStore = passive Persistence API (append-only, cursor-basiert replay).
    EventBus   = In-Memory Transport (publish/subscribe).
    ReplayService = Orchestrierung + Cursor-Management.

    Ein ReplayService = Ein Consumer. Keine Consumer-Group-Architektur.
    """

    def __init__(self, store: EventStore, bus: EventBus):
        self._store = store
        self._bus = bus
        self._last_replayed_seq: int = 0

    def replay_all(self, limit: int = 100) -> int:
        """Replay next batch of events from Store to Bus.

        Advances global cursor. Returns count of republished events.
        Cursor is set to highest seq in the batch (forward-only).
        """
        events = self._store.replay(
            cursor=self._last_replayed_seq, limit=limit
        )
        count = 0
        max_seq = self._last_replayed_seq
        for ev in events:
            self._bus.publish(
                topic=ev["topic"],
                payload=self._build_payload(ev),
                source=ev.get("source", ""),
            )
            seq = ev.get("seq", 0)
            if seq > max_seq:
                max_seq = seq
            count += 1
        self._last_replayed_seq = max_seq
        return count

    def replay_topic(self, topic: str, limit: int = 100) -> int:
        """Replay events filtered by topic.

        Does NOT advance global cursor (query-only).
        Returns count of republished events.
        """
        events = self._store.replay(topic=topic, limit=limit)
        count = 0
        for ev in events:
            self._bus.publish(
                topic=ev["topic"],
                payload=self._build_payload(ev),
                source=ev.get("source", ""),
            )
            count += 1
        return count

    def replay_since(self, seq: int, limit: int = 100) -> int:
        """Replay events after a specific seq.

        Advances global cursor. Returns count of republished events.
        """
        events = self._store.replay(cursor=seq, limit=limit)
        count = 0
        max_seq = seq
        for ev in events:
            self._bus.publish(
                topic=ev["topic"],
                payload=self._build_payload(ev),
                source=ev.get("source", ""),
            )
            s = ev.get("seq", 0)
            if s > max_seq:
                max_seq = s
            count += 1
        self._last_replayed_seq = max_seq
        return count

    def get_cursor(self) -> int:
        """Return last successfully replayed seq."""
        return self._last_replayed_seq

    def reset_cursor(self) -> None:
        """Reset cursor to 0. Next replay starts from beginning."""
        self._last_replayed_seq = 0

    def _build_payload(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Build replay payload. Preserves original event_id as metadata."""
        payload = dict(event.get("payload", {}))
        if isinstance(payload, str):
            try:
                import json
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                payload = {"_raw": payload}
        original_id = event.get("id", "")
        if original_id:
            payload["_original_event_id"] = original_id
        return payload
