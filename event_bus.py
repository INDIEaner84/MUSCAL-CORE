import copy
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class EventMessage:
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    id: str = ""


class EventBus:
    """OS-weites Event-System (ADR-003).

    Verwendung:
    - OS-Lifecycle-Events (Boot, Init, Shutdown)
    - Plugin-Kommunikation
    - Dashboard/Externe Subscriber

    Für pipeline-interne Events (Execution, Sync) siehe graph.on/emit.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[EventMessage] = []
        self._max_history: int = 50000
        self._topic_counts: Dict[str, int] = {}

    def publish(self, topic: str, payload: Optional[Dict[str, Any]] = None, source: str = "",
                priority: EventPriority = EventPriority.NORMAL) -> EventMessage:
        with self._lock:
            from features.identity.uuid7 import uuid7
            msg = EventMessage(
                topic=topic,
                payload=copy.deepcopy(payload) if payload else {},
                source=source,
                priority=priority,
                id=uuid7()
            )
            self._history.append(msg)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            self._topic_counts[topic] = self._topic_counts.get(topic, 0) + 1
            topic_subs = list(self._subscribers.get(topic, []))
            wild_subs = list(self._subscribers.get("*", []))
        for cb in topic_subs:
            try:
                cb(msg)
            except Exception:
                pass
        for cb in wild_subs:
            try:
                cb(msg)
            except Exception:
                pass
        return msg

    def subscribe(self, topic: str, callback: Callable) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if callback not in self._subscribers[topic]:
                self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable) -> None:
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic] = [cb for cb in self._subscribers[topic] if cb != callback]

    def swap_subscriber(self, topic: str, remove: Callable, add: Callable) -> None:
        """Atomically replace one subscriber with another — no event-loss window."""
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic] = [
                    cb for cb in self._subscribers[topic] if cb != remove
                ]
            self._subscribers.setdefault(topic, []).append(add)

    def get_history(self, topic: Optional[str] = None, limit: int = 10) -> List[EventMessage]:
        with self._lock:
            if topic is None:
                return list(self._history[-limit:])
            return [m for m in self._history if m.topic == topic][-limit:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_events": len(self._history),
                "topic_counts": dict(self._topic_counts),
                "subscriber_count": sum(len(v) for v in self._subscribers.values()),
                "topics": list(self._subscribers.keys()),
            }

    def clear(self) -> None:
        with self._lock:
            self._history.clear()
            self._topic_counts.clear()
