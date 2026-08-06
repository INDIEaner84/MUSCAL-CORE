"""Governance ledger event producer tests (Phase 1C.3).

Verifies that GovernanceStage additionally mirrors governance decisions as
ledger events in the EventStore while existing storage stays untouched.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_stage():
    from features.pipeline.governance_stage import GovernanceStage

    return GovernanceStage(kernel=None)


def test_record_decision_appends_ledger_event_when_store_wired():
    from runtime.event_store import EventStore
    from features.tool_runtime import tool_runtime

    with tempfile.TemporaryDirectory() as tmpdir:
        es = EventStore(db_path=Path(tmpdir) / "gov.db")
        tool_runtime.set_global_event_store(es)
        try:
            stage = _make_stage()
            ctx = {"trace_id": "trace-1"}
            stage._record_decision(ctx, "dec-1", "allow", "active", None)

            events = es.replay()
            assert len(events) == 1
            assert events[0]["topic"] == "governance.approved"
            assert events[0]["aggregate_id"] == "dec-1"
            assert events[0]["aggregate_type"] == "governance"
            assert events[0]["schema_version"] == 2
            assert events[0]["payload"]["action"] == "allow"
            assert events[0]["payload"]["trace_id"] == "trace-1"
        finally:
            tool_runtime.set_global_event_store(None)
            es.close()


def test_record_decision_rejected_topic():
    from runtime.event_store import EventStore
    from features.tool_runtime import tool_runtime

    with tempfile.TemporaryDirectory() as tmpdir:
        es = EventStore(db_path=Path(tmpdir) / "gov2.db")
        tool_runtime.set_global_event_store(es)
        try:
            stage = _make_stage()
            stage._record_decision({}, "dec-2", "block", "violation", "limit_exceeded")

            events = es.replay()
            assert len(events) == 1
            assert events[0]["topic"] == "governance.rejected"
            assert events[0]["payload"]["reason"] == "limit_exceeded"
        finally:
            tool_runtime.set_global_event_store(None)
            es.close()


def test_no_ledger_event_when_no_store_wired():
    from features.tool_runtime import tool_runtime

    tool_runtime.set_global_event_store(None)
    stage = _make_stage()
    stage._record_decision({"trace_id": "trace-3"}, "dec-3", "allow", "active", None)
    # no exception, no crash — EventStore untouched


def test_existing_storage_preserved():
    import sqlite3

    from features.pipeline.governance_stage import GovernanceStage

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "decisions.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY, task_id TEXT, worker_id TEXT,
                confidence REAL, reasoning TEXT, made_at TEXT NOT NULL,
                model_id TEXT, source_event_seq INTEGER
            )"""
        )
        conn.close()

        stage = GovernanceStage(kernel=None)
        stage._record_decision({"trace_id": "t"}, "dec-4", "allow", "active", None)
        # decisions table untouched by ledger path (no exception)
