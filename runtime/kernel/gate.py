import logging
from datetime import datetime, timezone
from typing import Any, Optional

import config
from runtime.kernel.scheduler import RoutingPolicy
from runtime.kernel.writer import WriterThread

log = logging.getLogger("muscal.gate")


def start_task_atomic(writer: WriterThread, task_id: str, task_type: str,
                       document_id: str, policy: RoutingPolicy,
                       governance: Any = None) -> dict:
    if governance is not None and not governance.consume_iteration(task_type):
        writer.submit({
            "type": "kernel.governance_violation", "domain": "system", "layer": "kernel",
            "stream": "event", "trust_level": 2, "severity": "warn",
            "actor": "governance", "actor_type": "kernel", "session_id": config.SESSION_ID,
            "payload": {"task_id": task_id, "task_type": task_type, "reason": "iteration_limit"},
        })
        return {"status": "gate_blocked", "reason": "governance_blocked"}

    worker_id = policy.route(task_type)
    now = datetime.now(timezone.utc).isoformat()

    def transaction(conn):
        if document_id:
            blocking = conn.execute("""
                SELECT COUNT(*) as n FROM intent_unknowns
                WHERE document_id = ? AND is_blocking = 1 AND resolved = 0
            """, [document_id]).fetchone()["n"]
            if blocking > 0:
                return False

        existing = conn.execute("SELECT id FROM tasks WHERE id = ?", [task_id]).fetchone()
        if existing:
            return "duplicate"

        conn.execute("""
            INSERT INTO tasks (id, type, status, worker_id, document_id, created_at, started_at)
            VALUES (?, ?, 'active', ?, ?, ?, ?)
        """, [task_id, task_type, worker_id, document_id, now, now])

        conn.execute("UPDATE workers SET status='running', current_task=?, started_at=? WHERE id=?",
                     [task_id, now, worker_id])
        return worker_id

    result = writer.submit_and_wait({
        "type": "worker.task_started",
        "domain": "execution", "layer": "L1",
        "stream": "event", "trust_level": 1,
        "actor": worker_id, "actor_type": "worker",
        "session_id": config.SESSION_ID,
        "aggregate_id": task_id, "aggregate_type": "task",
        "payload": {"task_id": task_id, "task_type": task_type, "worker_id": worker_id},
        "idempotency_key": f"task_start_{task_id}",
    }, transaction_fn=transaction)

    if result.get("blocked"):
        writer.submit({
            "type": "kernel.gate_violation", "domain": "system", "layer": "kernel",
            "stream": "event", "trust_level": 2, "severity": "warn",
            "actor": "kernel", "actor_type": "kernel", "session_id": config.SESSION_ID,
            "payload": {"task_id": task_id, "document_id": document_id},
        })
        return {"status": "gate_blocked"}

    if result.get("duplicate") or result.get("tx_result") == "duplicate":
        return {"status": "duplicate"}

    tx = result.get("tx_result")
    if not tx:
        return {"status": "error", "detail": "unexpected tx_result"}
    return {"status": "started", "worker_id": tx}


def resolve_unknown(writer: WriterThread, unknown_id: str, document_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    def transaction(conn):
        conn.execute("""
            UPDATE intent_unknowns SET resolved=1, resolved_at=?
            WHERE id=?
        """, [now, unknown_id])
        remaining = conn.execute("""
            SELECT COUNT(*) as n FROM intent_unknowns
            WHERE document_id=? AND is_blocking=1 AND resolved=0
        """, [document_id]).fetchone()["n"]
        return remaining

    result = writer.submit_and_wait({
        "type": "gate.unknown_resolved", "domain": "system", "layer": "kernel",
        "stream": "event", "trust_level": 2,
        "actor": "kernel", "actor_type": "kernel", "session_id": config.SESSION_ID,
        "aggregate_id": unknown_id, "aggregate_type": "unknown",
        "payload": {"unknown_id": unknown_id, "document_id": document_id},
    }, transaction_fn=transaction)

    remaining = result.get("tx_result", 1)
    if remaining == 0:
        writer.submit({
            "type": "gate.reopened", "domain": "system", "layer": "kernel",
            "stream": "event", "trust_level": 2, "severity": "info",
            "actor": "kernel", "actor_type": "kernel", "session_id": config.SESSION_ID,
            "payload": {"document_id": document_id},
        })
    return {"remaining_blocking": remaining, "gate_open": remaining == 0}
