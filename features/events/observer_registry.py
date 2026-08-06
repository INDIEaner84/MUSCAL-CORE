"""Observer registry (P0-2, Phase 2).

Central registration point for observer callbacks:

* ``register(observer)``      — add an observer
* ``unregister(observer)``    — remove an observer
* ``emit(event)``             — dispatch an event to all registered observers
* ``list_observers()``        — current observer list

Observers are callables taking a single ``ObserverEvent`` (or dict). Thread-safe.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List

from .contracts.observer_event_contract import ObserverEvent

REGISTRY_VERSION = "1.0.0"

Observer = Callable[[Any], None]

_lock = threading.Lock()
_observers: List[Observer] = []


def register(observer: Observer) -> None:
    if not callable(observer):
        raise TypeError("observer must be callable")
    with _lock:
        if observer not in _observers:
            _observers.append(observer)


def unregister(observer: Observer) -> bool:
    with _lock:
        try:
            _observers.remove(observer)
            return True
        except ValueError:
            return False


def list_observers() -> List[Observer]:
    with _lock:
        return list(_observers)


def emit(event: ObserverEvent | Dict[str, Any]) -> List[Any]:
    """Dispatch an event to all observers; returns their results."""
    if isinstance(event, dict):
        event = ObserverEvent.from_dict(event)
    if not isinstance(event, ObserverEvent):
        raise TypeError(f"expected ObserverEvent or dict, got {type(event).__name__}")

    results: List[Any] = []
    with _lock:
        observers = list(_observers)
    for observer in observers:
        try:
            results.append(observer(event))
        except Exception:
            # observer isolation: a failing observer must not break the chain
            continue
    return results


def clear() -> None:
    with _lock:
        _observers.clear()
