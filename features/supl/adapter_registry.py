from __future__ import annotations
import threading
from typing import Any, Dict, List, Optional

from features.supl.semantic_adapter import SemanticAdapter


class AdapterRegistry:
    def __init__(self, event_bridge: Any = None):
        self._lock = threading.RLock()
        self._adapters: Dict[str, SemanticAdapter] = {}
        self._bridge = event_bridge

    def set_event_bridge(self, bridge: Any) -> None:
        self._bridge = bridge

    def register(self, adapter: SemanticAdapter) -> None:
        app_id = adapter.application_id
        if not app_id:
            raise ValueError("adapter must have a non-empty application_id")
        with self._lock:
            if app_id in self._adapters:
                raise DuplicateApplicationIdError(
                    f"adapter with application_id '{app_id}' is already registered"
                )
            self._adapters[app_id] = adapter
        self._publish_registered(adapter)

    def register_or_replace(self, adapter: SemanticAdapter) -> Optional[SemanticAdapter]:
        app_id = adapter.application_id
        if not app_id:
            raise ValueError("adapter must have a non-empty application_id")
        with self._lock:
            previous = self._adapters.get(app_id)
            self._adapters[app_id] = adapter
        if previous is not None:
            self._publish_updated(adapter)
        else:
            self._publish_registered(adapter)
        return previous

    def unregister(self, application_id: str) -> bool:
        with self._lock:
            if application_id in self._adapters:
                del self._adapters[application_id]
                removed = True
            else:
                removed = False
        if removed:
            self._publish_removed(application_id)
        return removed

    def _publish_registered(self, adapter: SemanticAdapter) -> None:
        if self._bridge is None:
            return
        try:
            app = adapter.application
            name = app.name if hasattr(app, "name") else adapter.application_id
            version = app.version if hasattr(app, "version") else ""
        except Exception:
            name = adapter.application_id
            version = ""
        self._bridge.publish_application_registered(adapter.application_id, name, version)

    def _publish_updated(self, adapter: SemanticAdapter) -> None:
        if self._bridge is None:
            return
        try:
            app = adapter.application
            name = app.name if hasattr(app, "name") else adapter.application_id
            version = app.version if hasattr(app, "version") else ""
        except Exception:
            name = adapter.application_id
            version = ""
        self._bridge.publish_application_updated(adapter.application_id, name, version)

    def _publish_removed(self, application_id: str) -> None:
        if self._bridge is None:
            return
        self._bridge.publish_application_removed(application_id)

    def get(self, application_id: str) -> Optional[SemanticAdapter]:
        with self._lock:
            return self._adapters.get(application_id)

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "application_id": adapter.application_id,
                    "name": adapter.application.name if hasattr(adapter.application, "name") else "",
                }
                for adapter in self._adapters.values()
            ]

    def contains(self, application_id: str) -> bool:
        with self._lock:
            return application_id in self._adapters

    def __len__(self) -> int:
        with self._lock:
            return len(self._adapters)

    def clear(self) -> None:
        with self._lock:
            self._adapters.clear()


class DuplicateApplicationIdError(ValueError):
    pass
