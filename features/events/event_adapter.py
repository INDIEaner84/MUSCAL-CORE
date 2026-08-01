import json
import time
from typing import Any, Dict, Optional

EVENT_ADAPTER_VERSION = "1.0.0"


def writer_to_eventstore(writer_event: Dict[str, Any]) -> Dict[str, Any]:
    payload_raw = writer_event.get("payload", {})
    if isinstance(payload_raw, str):
        try:
            payload = json.loads(payload_raw)
        except (json.JSONDecodeError, TypeError):
            payload = {"_raw": payload_raw}
    else:
        payload = payload_raw

    return {
        "topic": writer_event.get("type", "system"),
        "payload": payload,
        "source": writer_event.get("actor", "kernel"),
        "priority": writer_event.get("severity", "info").upper(),
        "timestamp": _parse_timestamp(writer_event.get("ts", time.time())),
        "id": writer_event.get("idempotency_key", "") or str(uuid_for_event(writer_event)),
        "created_at": writer_event.get("occurred_at", writer_event.get("ts", "")),
    }


def eventstore_to_writer(es_event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": es_event.get("topic", "event"),
        "actor": es_event.get("source", "system"),
        "actor_type": "worker",
        "domain": "system",
        "layer": "L1",
        "stream": "event",
        "session_id": "default",
        "payload": json.dumps(es_event.get("payload", {}), ensure_ascii=False),
        "severity": _map_priority_to_severity(es_event.get("priority", "NORMAL")),
        "idempotency_key": es_event.get("id", ""),
        "ts": es_event.get("created_at", ""),
        "occurred_at": es_event.get("created_at", ""),
        "replayable": 1,
        "trust_level": 1,
        "schema_version": 1,
    }


def _parse_timestamp(ts: Any) -> float:
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            return time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z"))
        except (ValueError, TypeError):
            pass
        try:
            return time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))
        except (ValueError, TypeError):
            pass
    return time.time()


def _map_priority_to_severity(priority: str) -> str:
    mapping = {"LOW": "debug", "NORMAL": "info", "HIGH": "warn", "CRITICAL": "error"}
    return mapping.get(priority.upper(), "info")


def uuid_for_event(event: Dict[str, Any]) -> str:
    raw = f"{event.get('type', '')}_{event.get('ts', time.time())}_{event.get('actor', '')}"
    import hashlib
    return hashlib.md5(raw.encode()).hexdigest()[:16]


class EventStoreAdapter:
    def __init__(self, event_store, writer_thread=None):
        self._event_store = event_store
        self._writer_thread = writer_thread

    def append_writer_event(self, writer_event: Dict[str, Any]) -> Optional[int]:
        es_event = writer_to_eventstore(writer_event)
        seq = self._event_store.append(es_event)
        if self._writer_thread is not None:
            self._writer_thread.submit(writer_event)
        return seq
