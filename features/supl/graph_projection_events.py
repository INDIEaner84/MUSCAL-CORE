from __future__ import annotations
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from event_bus import EventBus
from features.supl.event_topics import (
    SUPL_APPLICATION_REGISTERED,
    SUPL_APPLICATION_UPDATED,
    SUPL_APPLICATION_REMOVED,
)
from features.supl.graph_projection import GraphProjectionEngine

logger = logging.getLogger(__name__)


class GraphProjectionEventBridge:
    """Subscribes to SUPL application lifecycle events via EventBus
    and drives the GraphProjectionEngine accordingly.

    Architecture:
        EventBus (supl.application.*)
            |
            v
        GraphProjectionEventBridge
            |
            v
        GraphProjectionEngine
            |
            v
        GraphState (store)

    Authority boundaries:
    - This bridge NEVER executes actions
    - This bridge NEVER fabricates execution evidence
    - This bridge projects from semantic truth only
    """

    def __init__(
        self,
        event_bus: EventBus,
        projection_engine: GraphProjectionEngine,
    ):
        self._bus = event_bus
        self._engine = projection_engine
        self._subscriptions: List[str] = []
        self._running = False
        self._projected_apps: Set[str] = set()

    def start(self) -> None:
        if self._running:
            return
        self._running = True

        self._bus.subscribe(SUPL_APPLICATION_REGISTERED, self._on_registered)
        self._subscriptions.append(SUPL_APPLICATION_REGISTERED)

        self._bus.subscribe(SUPL_APPLICATION_UPDATED, self._on_updated)
        self._subscriptions.append(SUPL_APPLICATION_UPDATED)

        self._bus.subscribe(SUPL_APPLICATION_REMOVED, self._on_removed)
        self._subscriptions.append(SUPL_APPLICATION_REMOVED)

    def stop(self) -> None:
        if not self._running:
            return
        for topic in self._subscriptions:
            try:
                self._bus.unsubscribe(topic, self._on_registered)
                self._bus.unsubscribe(topic, self._on_updated)
                self._bus.unsubscribe(topic, self._on_removed)
            except Exception:
                pass
        self._subscriptions.clear()
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def get_projected_apps(self) -> Set[str]:
        return self._engine.get_projected_apps()

    # ── Event Handlers ──────────────────────────────────────────────

    def _on_registered(self, msg: Any) -> None:
        if not self._running:
            return
        try:
            payload = self._extract_payload(msg)
            app_id = payload.get("application_id", "")
            if not app_id:
                return
            self._engine.project_application(app_id)
            self._projected_apps.add(app_id)
            logger.info("Projected application %s (registered event)", app_id)
        except ValueError as e:
            logger.warning("Projection failed for registered event: %s", e)
        except Exception as e:
            logger.error("Unexpected error in _on_registered: %s", e)

    def _on_updated(self, msg: Any) -> None:
        if not self._running:
            return
        try:
            payload = self._extract_payload(msg)
            app_id = payload.get("application_id", "")
            if not app_id:
                return
            self._engine.sync_application(app_id)
            self._projected_apps.add(app_id)
            logger.info("Synchronized application %s (updated event)", app_id)
        except ValueError as e:
            logger.warning("Projection sync failed for updated event: %s", e)
        except Exception as e:
            logger.error("Unexpected error in _on_updated: %s", e)

    def _on_removed(self, msg: Any) -> None:
        if not self._running:
            return
        try:
            payload = self._extract_payload(msg)
            app_id = payload.get("application_id", "")
            if not app_id:
                return
            count = self._engine.remove_application(app_id)
            self._projected_apps.discard(app_id)
            logger.info("Removed %d graph nodes for application %s (removed event)", count, app_id)
        except Exception as e:
            logger.error("Unexpected error in _on_removed: %s", e)

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _extract_payload(msg: Any) -> Dict[str, Any]:
        if hasattr(msg, "payload"):
            return msg.payload if isinstance(msg.payload, dict) else {}
        if isinstance(msg, dict):
            return msg.get("payload", msg)
        return {}


def create_graph_projection_event_bridge(
    event_bus: EventBus,
    projection_engine: GraphProjectionEngine,
) -> GraphProjectionEventBridge:
    bridge = GraphProjectionEventBridge(
        event_bus=event_bus,
        projection_engine=projection_engine,
    )
    bridge.start()
    return bridge
