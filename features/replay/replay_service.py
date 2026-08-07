from typing import Any, Dict, List, Optional

from event_bus import EventBus
from runtime.event_store import EventStore


class SequenceIntegrityError(RuntimeError):
    """Raised when a replay sequence violates integrity (P0-2)."""


class ReplayService:
    """Replay-Orchestrierung: liest aus EventStore, rebuilds state.

    EventStore = Basis-Persistenz (append-only, cursor-basiert replay).
    EventBus   = In-Memory Transport (publish/subscribe) [optional].
    ReplayService = Orchestrierung + Cursor-Management + State-Rebuild.

    Functional API (P0-2): load_events / order_events / rebuild_state /
    validate_sequence — deterministisch, reproduzierbar, keine Seiteneffekte.

    Ein ReplayService = Ein Consumer. Keine Consumer-Group-Architektur.
    """

    def __init__(self, store: EventStore, bus: Optional[EventBus] = None):
        self._store = store
        self._bus = bus
        self._last_replayed_seq: int = 0

    # ── Functional Replay API (P0-2) ─────────────────────────────────

    def load_events(
        self,
        cursor: Optional[int] = None,
        topic: Optional[str] = None,
        limit: int = 2**31 - 1,
    ) -> List[Dict[str, Any]]:
        """Load events from the store (passive read, no side effects).

        Deterministic baseline for replay: returns raw stored rows.
        """
        return self._store.replay(cursor=cursor, topic=topic, limit=limit)

    def order_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order events by seq ascending (deterministic, no mutation)."""
        return sorted(events, key=lambda e: e.get("seq", 0))

    def rebuild_state(self, events: Optional[List[Dict[str, Any]]] = None):
        """Rebuild the ReconstructedState from an (ordered) event stream.

        Loads all events if not provided, orders them, validates the hash
        chain, then folds them deterministically via state_model. Returns
        the resulting ReconstructedState (no side effects on the store).
        """
        from features.events.state_model import reconstruct_state

        if events is None:
            events = self.load_events()
        ordered = self.order_events(events)
        self.validate_sequence(ordered)
        return reconstruct_state(ordered)

    def validate_sequence(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate sequence integrity before/after rebuild.

        Checks (P0-2):
        * monotonic ascending seq (missing order / wrong order / duplicates)
        * duplicated event_ids
        * hash chain via existing state_model.validate_chain (invalid hashes)

        Returns a report dict; raises ReplayError on violation.
        """
        from features.events.state_model import ChainIntegrityError
        from features.events.state_model import validate_chain as validate_hash_chain

        seen_seq: set = set()
        seen_ids: set = set()
        prev_seq: Optional[int] = None
        issues: List[str] = []

        for ev in events:
            seq = ev.get("seq")
            if seq is None:
                issues.append(f"missing seq in event {ev.get('id', '?')!r}")
                continue
            if prev_seq is not None and seq <= prev_seq:
                issues.append(f"seq {seq} out of order (after {prev_seq})")
            if prev_seq is not None and seq != prev_seq + 1:
                issues.append(f"seq gap detected: expected {prev_seq + 1}, got {seq}")
            if seq in seen_seq:
                issues.append(f"duplicate seq {seq}")
            seen_seq.add(seq)
            eid = ev.get("id")
            if eid:
                if eid in seen_ids:
                    issues.append(f"duplicate event_id {eid!r}")
                seen_ids.add(eid)
            prev_seq = seq

        if issues:
            raise SequenceIntegrityError("; ".join(issues))

        try:
            return validate_hash_chain(events)
        except ChainIntegrityError as exc:
            raise SequenceIntegrityError(str(exc)) from exc

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
        payload["_replayed"] = True
        return payload

    def _build_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Build event dict for EventStore.append with is_replayed flag."""
        ev = dict(event)
        ev["is_replayed"] = 1
        return ev
