import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from runtime.event_store import EventStore


class TestCanonicalAuthority:
    @pytest.fixture
    def db_path(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        try:
            os.unlink(f.name)
        except OSError:
            pass

    @pytest.fixture
    def store(self, db_path):
        return EventStore(db_path=db_path)

    def test_c001_stored_events_is_canonical_authority(self, store: EventStore):
        store.append({
            "topic": "execution.receipt",
            "payload": {"receipt_id": "r1", "tool": "console.print", "success": True},
            "source": "UnifiedToolRuntime",
            "id": "evt-001",
            "execution_id": "ex-001",
            "correlation_id": "corr-001",
            "execution_mode": "real",
            "execution_state": "completed",
            "verification_state": "unverified",
        })
        store.append({
            "topic": "execution.verification",
            "payload": {"verification_id": "vr1", "status": "verified"},
            "source": "VerificationOrchestrator",
            "id": "evt-002",
            "execution_id": "ex-001",
            "correlation_id": "",
            "causation_id": "r1",
            "execution_mode": "real",
            "execution_state": "completed",
            "verification_state": "verified",
        })
        events = store.replay(cursor=0, limit=100)
        assert len(events) == 2
        assert events[0]["topic"] == "execution.receipt"
        assert events[1]["topic"] == "execution.verification"
        assert events[0]["payload"]["receipt_id"] == "r1"
        assert events[1]["payload"]["verification_id"] == "vr1"

    def test_c001_stored_events_survives_reopen(self, db_path: Path, store: EventStore):
        store.append({
            "topic": "execution.receipt",
            "payload": {"receipt_id": "r2", "execution_id": "ex-003"},
            "source": "UnifiedToolRuntime",
            "id": "evt-003",
            "execution_state": "completed",
            "execution_id": "ex-003",
        })
        store.close()
        store2 = EventStore(db_path=db_path)
        events = store2.replay(cursor=0, limit=100)
        assert len(events) == 1
        assert events[0]["payload"]["receipt_id"] == "r2"
        store2.close()

    def test_c001_store_receipt_persists(self, db_path, store: EventStore):
        class FakeReceipt:
            receipt_id = "r3"
            execution_id = "ex-003"
            correlation_id = "corr-003"
            causation_id = "caus-003"
            success = True

            @property
            def verification_status(self):
                return "verified"

            def to_dict(self):
                return {"receipt_id": "r3", "success": True}

        seq = store.store_receipt(FakeReceipt())
        assert seq is not None
        events = store.replay(topic="execution.receipt", limit=100)
        assert len(events) == 1
        assert events[0]["payload"]["receipt_id"] == "r3"

    def test_c001_store_verification_persists(self, db_path, store: EventStore):
        class FakeVerification:
            verification_id = "vr2"
            execution_id = "ex-003"
            receipt_id = "r3"
            status = "verified"

            def to_dict(self):
                return {"verification_id": "vr2", "status": "verified"}

        seq = store.store_verification(FakeVerification())
        assert seq is not None
        events = store.replay(topic="execution.verification", limit=100)
        assert len(events) == 1
        assert events[0]["payload"]["verification_id"] == "vr2"

    def test_c001_execution_state_recovery(self, db_path, store: EventStore):
        store.append({
            "topic": "EXECUTION_STARTED",
            "payload": {"input": "test"},
            "source": "EnrichedMuscalOS",
            "id": "evt-100",
            "execution_id": "ex-100",
            "execution_state": "running",
        })
        store.append({
            "topic": "EXECUTION_COMPLETED",
            "payload": {"result": "ok"},
            "source": "EnrichedMuscalOS",
            "id": "evt-101",
            "execution_id": "ex-100",
            "execution_state": "completed",
        })
        events = store.replay(cursor=0, limit=100)
        running = [e for e in events if e.get("execution_state") == "running"]
        completed = [e for e in events if e.get("execution_state") == "completed"]
        assert len(running) == 1
        assert len(completed) == 1
        assert running[0]["execution_id"] == completed[0]["execution_id"]
        assert running[0]["execution_id"] == "ex-100"

    def test_c001_no_events_table_write_from_canonical_path(self, db_path, store: EventStore):
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        tables = [
            r["name"]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        conn.close()
        assert "stored_events" in tables
        assert "events" not in tables
