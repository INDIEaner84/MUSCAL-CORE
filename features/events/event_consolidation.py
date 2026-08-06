import json
import time
import uuid
from typing import Any, Dict, List, Optional

EVENT_CONSOLIDATION_VERSION = "1.0.0"

_canonical_event_store = None


def get_canonical_event_store():
    global _canonical_event_store
    return _canonical_event_store


def set_canonical_event_store(store):
    global _canonical_event_store
    _canonical_event_store = store


class ConsolidatedEventWriter:
    def __init__(self, event_store=None, writer_thread=None):
        self._event_store = event_store or _canonical_event_store
        self._writer_thread = writer_thread

    def write_event(self, topic: str, payload: dict,
                    source: str = "system",
                    priority: str = "NORMAL",
                    event_id: Optional[str] = None,
                    execution_id: str = "",
                    correlation_id: str = "",
                    causation_id: str = "",
                    execution_mode: str = "real",
                    verification_state: str = "unverified",
                    **extra) -> Optional[int]:
        if self._event_store is None:
            return None

        es_event = {
            "topic": topic,
            "payload": payload,
            "source": source,
            "priority": priority,
            "timestamp": time.time(),
            "id": event_id or str(uuid.uuid4()),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S",
                                        time.gmtime()),
            "execution_id": execution_id,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "execution_mode": execution_mode,
            "verification_state": verification_state,
        }
        if extra:  # additive P0-2: forward observer fields to the store
            es_event.update(extra)

        seq = self._event_store.append(es_event)

        if self._writer_thread is not None:
            writer_event = {
                "type": topic,
                "actor": source,
                "actor_type": "worker",
                "domain": "system",
                "layer": "L1",
                "stream": "event",
                "session_id": "default",
                "payload": payload,
                "severity": _priority_to_severity(priority),
                "idempotency_key": es_event["id"],
                "ts": es_event["timestamp"],
                "occurred_at": es_event["created_at"],
                "schema_version": 1,
                "trust_level": 1,
                "replayable": 1,
            }
            try:
                self._writer_thread.submit(writer_event)
            except Exception:
                pass

        return seq

    def replay(self, cursor: Optional[int] = None,
               topic: Optional[str] = None,
               limit: int = 100) -> List[Dict[str, Any]]:
        if self._event_store is None:
            return []
        return self._event_store.replay(cursor=cursor, topic=topic,
                                        limit=limit)

    def get_cursor(self) -> int:
        if self._event_store is None:
            return 0
        return self._event_store.get_cursor()

    def count(self, topic: Optional[str] = None) -> int:
        if self._event_store is None:
            return 0
        return self._event_store.event_count(topic=topic)


def _priority_to_severity(priority: str) -> str:
    mapping = {"LOW": "debug", "NORMAL": "info",
               "HIGH": "warn", "CRITICAL": "error"}
    return mapping.get(priority.upper(), "info")


class EventConsolidationEngine:
    def __init__(self, consolidated_writer=None):
        self._writer = consolidated_writer or ConsolidatedEventWriter()

    @property
    def writer(self):
        return self._writer

    def emit_event(self, topic: str, payload: dict, **kwargs) -> Optional[int]:
        return self._writer.write_event(topic=topic, payload=payload, **kwargs)

    def query_events(self, cursor: Optional[int] = None,
                     topic: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        return self._writer.replay(cursor=cursor, topic=topic, limit=limit)

    def latest_cursor(self) -> int:
        return self._writer.get_cursor()

    def event_count(self, topic: Optional[str] = None) -> int:
        return self._writer.count(topic=topic)
