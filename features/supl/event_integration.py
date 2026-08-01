from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional

from event_bus import EventBus, EventPriority
from features.supl.event_topics import (
    SUPL_APPLICATION_REGISTERED,
    SUPL_APPLICATION_UPDATED,
    SUPL_APPLICATION_REMOVED,
    SUPL_ACTION_REQUESTED,
    SUPL_ACTION_AUTHORIZED,
    SUPL_ACTION_REJECTED,
    SUPL_INTERACTION_CREATED,
    SUPL_INTERACTION_UPDATED,
    SUPL_EXECUTION_LINKED,
    SUPL_EXECUTION_COMPLETED,
    SUPL_EXECUTION_FAILED,
    SUPL_PROVENANCE_LINKED,
)


class EventBusBridge:
    def __init__(self, event_bus: EventBus, source: str = "supl"):
        self._bus = event_bus
        self._source = source
        self._callbacks: Dict[str, List[Callable]] = {}

    # ── Subscriptions ──

    def subscribe(self, topic: str, callback: Callable) -> None:
        self._bus.subscribe(topic, callback)
        if topic not in self._callbacks:
            self._callbacks[topic] = []
        self._callbacks[topic].append(callback)

    def subscribe_wildcard(self, callback: Callable) -> None:
        self._bus.subscribe("*", callback)
        self._callbacks.setdefault("*", []).append(callback)

    def unsubscribe_all(self) -> None:
        for topic, cbs in self._callbacks.items():
            for cb in cbs:
                self._bus.unsubscribe(topic, cb)
        self._callbacks.clear()

    # ── Publishing helpers ──

    def _publish(self, topic: str, payload: Dict[str, Any],
                 priority: EventPriority = EventPriority.NORMAL) -> None:
        self._bus.publish(topic, payload, source=self._source, priority=priority)

    def publish_application_registered(self, app_id: str, name: str, version: str) -> None:
        self._publish(SUPL_APPLICATION_REGISTERED, {
            "application_id": app_id, "name": name, "version": version,
        })

    def publish_application_updated(self, app_id: str, name: str, version: str) -> None:
        self._publish(SUPL_APPLICATION_UPDATED, {
            "application_id": app_id, "name": name, "version": version,
        })

    def publish_application_removed(self, app_id: str) -> None:
        self._publish(SUPL_APPLICATION_REMOVED, {
            "application_id": app_id,
        })

    def publish_action_requested(self, interaction: Any) -> None:
        self._publish(SUPL_ACTION_REQUESTED, {
            "interaction_id": interaction.interaction_id,
            "application_id": interaction.application_id,
            "capability_id": interaction.capability_id,
            "action_id": interaction.action_id,
            "source_mode": interaction.source_mode.value if hasattr(interaction.source_mode, "value") else str(interaction.source_mode),
        })

    def publish_action_authorized(self, interaction: Any) -> None:
        self._publish(SUPL_ACTION_AUTHORIZED, {
            "interaction_id": interaction.interaction_id,
            "allowed": True,
        })

    def publish_action_rejected(self, interaction: Any, reason: str = "") -> None:
        self._publish(SUPL_ACTION_REJECTED, {
            "interaction_id": interaction.interaction_id,
            "reason": reason,
        })

    def publish_interaction_created(self, interaction: Any) -> None:
        self._publish(SUPL_INTERACTION_CREATED, {
            "interaction_id": interaction.interaction_id,
            "status": interaction.status.value if hasattr(interaction.status, "value") else str(interaction.status),
        })

    def publish_interaction_updated(self, interaction: Any) -> None:
        self._publish(SUPL_INTERACTION_UPDATED, {
            "interaction_id": interaction.interaction_id,
            "status": interaction.status.value if hasattr(interaction.status, "value") else str(interaction.status),
        })

    def publish_execution_linked(self, interaction: Any, execution_id: str) -> None:
        self._publish(SUPL_EXECUTION_LINKED, {
            "interaction_id": interaction.interaction_id,
            "execution_id": execution_id,
        })

    def publish_execution_completed(self, interaction: Any, receipt: Any = None) -> None:
        payload: Dict[str, Any] = {
            "interaction_id": interaction.interaction_id,
            "execution_id": interaction.execution_id or "",
            "status": "completed",
        }
        if receipt is not None:
            payload["receipt_id"] = receipt.receipt_id if hasattr(receipt, "receipt_id") else str(receipt)
            payload["success"] = receipt.success if hasattr(receipt, "success") else True
        self._publish(SUPL_EXECUTION_COMPLETED, payload)

    def publish_execution_failed(self, interaction: Any, error: str = "") -> None:
        self._publish(SUPL_EXECUTION_FAILED, {
            "interaction_id": interaction.interaction_id,
            "execution_id": interaction.execution_id or "",
            "error": error,
        })

    def publish_provenance_linked(self, interaction_id: str, execution_id: str, receipt_id: str) -> None:
        self._publish(SUPL_PROVENANCE_LINKED, {
            "interaction_id": interaction_id,
            "execution_id": execution_id,
            "receipt_id": receipt_id,
        })

    def get_history(self, topic: str, limit: int = 50) -> List[Any]:
        return self._bus.get_history(topic, limit)
