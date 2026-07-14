import datetime
import json
import os

from runtime.database import get_connection


RETENTION_DAYS = int(os.environ.get("MUSCAL_EVENT_RETENTION_DAYS", "30"))


class Plugin:
    name = "event_persistence"
    version = "1.0.0"
    _bus = None
    _conn = None

    def register(self, hooks):
        hooks.setdefault("_event_bus", None)
        self._prune_old_events()

    def execute(self, context):
        return {"persisted_events": None}

    def _get_conn(self):
        if self._conn is None:
            self._conn = get_connection()
        return self._conn

    def _prune_old_events(self):
        try:
            conn = self._get_conn()
            cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=RETENTION_DAYS)).isoformat()
            deleted = conn.execute("DELETE FROM audit_log WHERE created_at < ?", (cutoff,)).rowcount
            conn.commit()
            if deleted:
                print(f"EVENT_PERSISTENCE: pruned {deleted} events older than {RETENTION_DAYS}d")
        except Exception as e:
            print(f"EVENT_PERSISTENCE: prune failed: {e}")

    def _persist_event(self, msg):
        try:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO audit_log (entry_type, payload) VALUES (?, ?)",
                (msg.topic, json.dumps({
                    "id": msg.id,
                    "source": msg.source,
                    "priority": msg.priority.name if msg.priority else "NORMAL",
                    "timestamp": msg.timestamp,
                    "payload": msg.payload,
                }))
            )
            conn.commit()
        except Exception as e:
            print(f"EVENT_PERSISTENCE: write failed: {e}")

    def _wire_bus(self, bus):
        self._bus = bus
        bus.subscribe("*", self._persist_event)
        print(f"EVENT_PERSISTENCE: subscribed to EventBus, retention={RETENTION_DAYS}d")
