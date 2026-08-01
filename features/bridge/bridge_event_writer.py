from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from runtime.event_store import EventStore


BRIDGE_EXECUTION_TOPIC = "bridge.execution"


class BridgeEventWriter:

    def __init__(self, event_store: Optional[EventStore] = None,
                 db_path: Optional[Path] = None):
        if event_store is not None:
            self._store = event_store
        elif db_path is not None:
            self._store = EventStore(db_path)
        else:
            self._store = None

    @property
    def is_connected(self) -> bool:
        return self._store is not None

    def write_execution_event(
        self,
        task_id: str,
        project_id: str,
        execution_id: str,
        opencode_session: Optional[str],
        status: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> Optional[int]:
        if self._store is None:
            return None

        event_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).timestamp()
        correlation = correlation_id or event_id
        causation = causation_id or ""

        event: dict[str, Any] = {
            "topic": BRIDGE_EXECUTION_TOPIC,
            "payload": {
                "task_id": task_id,
                "project_id": project_id,
                "opencode_session": opencode_session or "",
                "status": status,
                "data": payload or {},
            },
            "source": "features/bridge/bridge_event_writer.py",
            "priority": "NORMAL",
            "timestamp": ts,
            "id": event_id,
            "execution_id": execution_id,
            "correlation_id": correlation,
            "causation_id": causation,
            "execution_mode": "real",
            "execution_state": status,
            "verification_state": "unverified",
            "receipt_id": "",
        }
        return self._store.append(event)
