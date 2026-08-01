import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from runtime.database import get_connection

log = logging.getLogger("muscal.provenance.decision")


def write_decision(
    db_path: Path,
    decision_id: str,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    governance_action: Optional[str] = None,
    decision_status: str = "active",
    reasoning: Optional[str] = None,
    decision_type: str = "governance",
    task_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    confidence: Optional[float] = None,
    model_id: Optional[str] = None,
    parent_decision_id: Optional[str] = None,
) -> bool:
    conn = get_connection(db_path)
    try:
        conn.execute("""
            INSERT INTO decisions (
                id, trace_id, span_id,
                decision_type, decision_status, governance_action,
                reasoning, made_at,
                task_id, worker_id, confidence, model_id,
                parent_decision_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            decision_id,
            trace_id,
            span_id,
            decision_type,
            decision_status,
            governance_action,
            reasoning,
            datetime.now(timezone.utc).isoformat(),
            task_id,
            worker_id,
            confidence,
            model_id,
            parent_decision_id,
        ])
        conn.commit()
        return True
    except Exception as e:
        log.warning("Failed to write decision %s: %s", decision_id, e)
        return False
    finally:
        conn.close()


def get_decision(db_path: Path, decision_id: str) -> Optional[dict]:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM decisions WHERE id = ?", [decision_id]
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    except Exception as e:
        log.warning("Failed to read decision %s: %s", decision_id, e)
        return None
    finally:
        conn.close()


def get_decisions_by_trace(db_path: Path, trace_id: str) -> list[dict]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM decisions WHERE trace_id = ? ORDER BY made_at",
            [trace_id]
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        log.warning("Failed to read decisions for trace %s: %s", trace_id, e)
        return []
    finally:
        conn.close()
