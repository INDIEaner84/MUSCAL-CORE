from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
from features.identity.uuid7 import uuid7
from features.provenance.mcpl_schema import (
    Intent,
    Task,
    Agent,
    Model,
    ModelOutput,
    Decision,
    AgentDecision,
    PolicyDecision,
    HumanDecision,
    Execution,
    Attempt,
    ToolCall,
    Artifact,
    State,
    Verification,
    Join,
    ProvenanceRecord,
)

log = logging.getLogger("muscal.mcpl.store")

MCPL_DB_TABLES = {
    "mcpl_intents", "mcpl_tasks", "mcpl_agents", "mcpl_models",
    "mcpl_model_outputs", "mcpl_decisions", "mcpl_executions",
    "mcpl_attempts", "mcpl_tool_calls", "mcpl_artifacts",
    "mcpl_states", "mcpl_verifications", "mcpl_joins",
    "mcpl_provenance_events",
}


class MCPLStore:
    """SQLite-backed persistence for MCPL entities and provenance events."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or config.DB_PATH
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._db_path), timeout=10.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ------------------------------------------------------------------
    # Intent CRUD
    # ------------------------------------------------------------------

    def save_intent(self, intent: Intent) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_intents
               (intent_id, description, created_at, correlation_id, causation_id, tenant_id, status, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (intent.intent_id, intent.description, intent.created_at,
             intent.correlation_id, intent.causation_id, intent.tenant_id,
             intent.status, json.dumps(intent.metadata)),
        )
        conn.commit()

    def get_intent(self, intent_id: str) -> Optional[Intent]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM mcpl_intents WHERE intent_id = ?", (intent_id,)).fetchone()
        if row is None:
            return None
        return Intent(
            intent_id=row["intent_id"],
            description=row["description"] or "",
            created_at=row["created_at"] or "",
            correlation_id=row["correlation_id"] or "",
            causation_id=row["causation_id"] or "",
            tenant_id=row["tenant_id"] or "",
            status=row["status"] or "created",
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def list_intents(self, tenant_id: str = "", limit: int = 100) -> List[Intent]:
        conn = self._conn()
        if tenant_id:
            rows = conn.execute(
                "SELECT * FROM mcpl_intents WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM mcpl_intents ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            Intent(
                intent_id=r["intent_id"],
                description=r["description"] or "",
                created_at=r["created_at"] or "",
                correlation_id=r["correlation_id"] or "",
                causation_id=r["causation_id"] or "",
                tenant_id=r["tenant_id"] or "",
                status=r["status"] or "created",
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    def save_task(self, task: Task) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_tasks
               (task_id, intent_id, description, created_at, correlation_id, causation_id,
                tenant_id, status, agent_id, join_id, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.task_id, task.intent_id, task.description, task.created_at,
             task.correlation_id, task.causation_id, task.tenant_id,
             task.status, task.agent_id, task.join_id, json.dumps(task.metadata)),
        )
        conn.commit()

    def get_task(self, task_id: str) -> Optional[Task]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM mcpl_tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return Task(
            task_id=row["task_id"],
            intent_id=row["intent_id"] or "",
            description=row["description"] or "",
            created_at=row["created_at"] or "",
            correlation_id=row["correlation_id"] or "",
            causation_id=row["causation_id"] or "",
            tenant_id=row["tenant_id"] or "",
            status=row["status"] or "created",
            agent_id=row["agent_id"] or "",
            join_id=row["join_id"] or "",
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def list_tasks_by_intent(self, intent_id: str) -> List[Task]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM mcpl_tasks WHERE intent_id = ? ORDER BY created_at",
            (intent_id,),
        ).fetchall()
        return [
            Task(
                task_id=r["task_id"],
                intent_id=r["intent_id"] or "",
                description=r["description"] or "",
                created_at=r["created_at"] or "",
                correlation_id=r["correlation_id"] or "",
                causation_id=r["causation_id"] or "",
                tenant_id=r["tenant_id"] or "",
                status=r["status"] or "created",
                agent_id=r["agent_id"] or "",
                join_id=r["join_id"] or "",
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Execution CRUD
    # ------------------------------------------------------------------

    def save_execution(self, execution: Execution) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_executions
               (execution_id, task_id, tool_name, created_at, correlation_id, causation_id,
                tenant_id, status, authorization_id, decision_id, attempt_count,
                replay_of, replay_classification, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (execution.execution_id, execution.task_id, execution.tool_name,
             execution.created_at, execution.correlation_id, execution.causation_id,
             execution.tenant_id, execution.status, execution.authorization_id,
             execution.decision_id, execution.attempt_count,
             execution.replay_of, execution.replay_classification,
             json.dumps(execution.metadata)),
        )
        conn.commit()

    def get_execution(self, execution_id: str) -> Optional[Execution]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM mcpl_executions WHERE execution_id = ?", (execution_id,)
        ).fetchone()
        if row is None:
            return None
        return Execution(
            execution_id=row["execution_id"],
            task_id=row["task_id"] or "",
            tool_name=row["tool_name"] or "",
            created_at=row["created_at"] or "",
            correlation_id=row["correlation_id"] or "",
            causation_id=row["causation_id"] or "",
            tenant_id=row["tenant_id"] or "",
            status=row["status"] or "requested",
            authorization_id=row["authorization_id"] or "",
            decision_id=row["decision_id"] or "",
            attempt_count=row["attempt_count"] or 0,
            replay_of=row["replay_of"] or "",
            replay_classification=row["replay_classification"] or "",
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def list_executions_by_task(self, task_id: str) -> List[Execution]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM mcpl_executions WHERE task_id = ? ORDER BY created_at",
            (task_id,),
        ).fetchall()
        return [
            Execution(
                execution_id=r["execution_id"],
                task_id=r["task_id"] or "",
                tool_name=r["tool_name"] or "",
                created_at=r["created_at"] or "",
                correlation_id=r["correlation_id"] or "",
                causation_id=r["causation_id"] or "",
                tenant_id=r["tenant_id"] or "",
                status=r["status"] or "requested",
                authorization_id=r["authorization_id"] or "",
                decision_id=r["decision_id"] or "",
                attempt_count=r["attempt_count"] or 0,
                replay_of=r["replay_of"] or "",
                replay_classification=r["replay_classification"] or "",
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Attempt CRUD
    # ------------------------------------------------------------------

    def save_attempt(self, attempt: Attempt) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_attempts
               (attempt_id, execution_id, attempt_number, created_at, started_at,
                completed_at, status, error, error_type, duration_ms, result_hash,
                receipt_id, tenant_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (attempt.attempt_id, attempt.execution_id, attempt.attempt_number,
             attempt.created_at, attempt.started_at, attempt.completed_at,
             attempt.status, attempt.error, attempt.error_type,
             attempt.duration_ms, attempt.result_hash, attempt.receipt_id,
             attempt.tenant_id),
        )
        conn.commit()

    def get_attempt(self, attempt_id: str) -> Optional[Attempt]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM mcpl_attempts WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
        if row is None:
            return None
        return Attempt(
            attempt_id=row["attempt_id"],
            execution_id=row["execution_id"] or "",
            attempt_number=row["attempt_number"] or 1,
            created_at=row["created_at"] or "",
            started_at=row["started_at"] or "",
            completed_at=row["completed_at"] or "",
            status=row["status"] or "started",
            error=row["error"] or "",
            error_type=row["error_type"] or "",
            duration_ms=row["duration_ms"] or 0.0,
            result_hash=row["result_hash"] or "",
            receipt_id=row["receipt_id"] or "",
            tenant_id=row["tenant_id"] or "",
        )

    def list_attempts_by_execution(self, execution_id: str) -> List[Attempt]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM mcpl_attempts WHERE execution_id = ? ORDER BY attempt_number",
            (execution_id,),
        ).fetchall()
        return [
            Attempt(
                attempt_id=r["attempt_id"],
                execution_id=r["execution_id"] or "",
                attempt_number=r["attempt_number"] or 1,
                created_at=r["created_at"] or "",
                started_at=r["started_at"] or "",
                completed_at=r["completed_at"] or "",
                status=r["status"] or "started",
                error=r["error"] or "",
                error_type=r["error_type"] or "",
                duration_ms=r["duration_ms"] or 0.0,
                result_hash=r["result_hash"] or "",
                receipt_id=r["receipt_id"] or "",
                tenant_id=r["tenant_id"] or "",
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Decision CRUD
    # ------------------------------------------------------------------

    def save_decision(self, decision: Decision) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_decisions
               (decision_id, decision_type, task_id, agent_id, created_at,
                correlation_id, causation_id, tenant_id, status, reasoning,
                confidence, model_output_id, parent_decision_id,
                candidates, selected, selection_rationale,
                policy_id, policy_version, match_result,
                human_action, human_id, automated_decision_id, rationale)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (decision.decision_id, decision.decision_type, decision.task_id,
             decision.agent_id, decision.created_at,
             decision.correlation_id, decision.causation_id, decision.tenant_id,
             decision.status, decision.reasoning, decision.confidence,
             decision.model_output_id, decision.parent_decision_id,
             json.dumps(getattr(decision, "candidates", [])),
             getattr(decision, "selected", ""),
             getattr(decision, "selection_rationale", ""),
             getattr(decision, "policy_id", ""),
             getattr(decision, "policy_version", ""),
             getattr(decision, "match_result", ""),
             getattr(decision, "human_action", ""),
             getattr(decision, "human_id", ""),
             getattr(decision, "automated_decision_id", ""),
             getattr(decision, "rationale", "")),
        )
        conn.commit()

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM mcpl_decisions WHERE decision_id = ?", (decision_id,)
        ).fetchone()
        if row is None:
            return None
        base = Decision(
            decision_id=row["decision_id"],
            decision_type=row["decision_type"] or "agent_decision",
            task_id=row["task_id"] or "",
            agent_id=row["agent_id"] or "",
            created_at=row["created_at"] or "",
            correlation_id=row["correlation_id"] or "",
            causation_id=row["causation_id"] or "",
            tenant_id=row["tenant_id"] or "",
            status=row["status"] or "active",
            reasoning=row["reasoning"] or "",
            confidence=row["confidence"] or 0.0,
            model_output_id=row["model_output_id"] or "",
            parent_decision_id=row["parent_decision_id"] or "",
        )
        return base

    def list_decisions_by_task(self, task_id: str) -> List[Decision]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM mcpl_decisions WHERE task_id = ? ORDER BY created_at",
            (task_id,),
        ).fetchall()
        return [
            Decision(
                decision_id=r["decision_id"],
                decision_type=r["decision_type"] or "agent_decision",
                task_id=r["task_id"] or "",
                agent_id=r["agent_id"] or "",
                created_at=r["created_at"] or "",
                correlation_id=r["correlation_id"] or "",
                causation_id=r["causation_id"] or "",
                tenant_id=r["tenant_id"] or "",
                status=r["status"] or "active",
                reasoning=r["reasoning"] or "",
                confidence=r["confidence"] or 0.0,
                model_output_id=r["model_output_id"] or "",
                parent_decision_id=r["parent_decision_id"] or "",
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Verification CRUD
    # ------------------------------------------------------------------

    def save_verification(self, verification: Verification) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_verifications
               (verification_id, subject_id, subject_type, verifier_type, verifier_id,
                method, expected_condition, observed_result, status, confidence,
                evidence_ref, created_at, verified_at, correlation_id, causation_id,
                tenant_id, decision_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (verification.verification_id, verification.subject_id,
             verification.subject_type, verification.verifier_type,
             verification.verifier_id, verification.method,
             json.dumps(verification.expected_condition),
             json.dumps(verification.observed_result),
             verification.status, verification.confidence,
             verification.evidence_ref, verification.created_at,
             verification.verified_at, verification.correlation_id,
             verification.causation_id, verification.tenant_id,
             verification.decision_id),
        )
        conn.commit()

    def get_verification(self, verification_id: str) -> Optional[Verification]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM mcpl_verifications WHERE verification_id = ?", (verification_id,)
        ).fetchone()
        if row is None:
            return None
        return Verification(
            verification_id=row["verification_id"],
            subject_id=row["subject_id"] or "",
            subject_type=row["subject_type"] or "execution",
            verifier_type=row["verifier_type"] or "deterministic",
            verifier_id=row["verifier_id"] or "",
            method=row["method"] or "",
            expected_condition=json.loads(row["expected_condition"] or "{}"),
            observed_result=json.loads(row["observed_result"] or "{}"),
            status=row["status"] or "requested",
            confidence=row["confidence"] or 0.0,
            evidence_ref=row["evidence_ref"] or "",
            created_at=row["created_at"] or "",
            verified_at=row["verified_at"] or "",
            correlation_id=row["correlation_id"] or "",
            causation_id=row["causation_id"] or "",
            tenant_id=row["tenant_id"] or "",
            decision_id=row["decision_id"] or "",
        )

    def list_verifications_by_subject(self, subject_id: str) -> List[Verification]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM mcpl_verifications WHERE subject_id = ? ORDER BY created_at",
            (subject_id,),
        ).fetchall()
        return [
            Verification(
                verification_id=r["verification_id"],
                subject_id=r["subject_id"] or "",
                subject_type=r["subject_type"] or "execution",
                verifier_type=r["verifier_type"] or "deterministic",
                verifier_id=r["verifier_id"] or "",
                method=r["method"] or "",
                expected_condition=json.loads(r["expected_condition"] or "{}"),
                observed_result=json.loads(r["observed_result"] or "{}"),
                status=r["status"] or "requested",
                confidence=r["confidence"] or 0.0,
                evidence_ref=r["evidence_ref"] or "",
                created_at=r["created_at"] or "",
                verified_at=r["verified_at"] or "",
                correlation_id=r["correlation_id"] or "",
                causation_id=r["causation_id"] or "",
                tenant_id=r["tenant_id"] or "",
                decision_id=r["decision_id"] or "",
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Provenance Event CRUD
    # ------------------------------------------------------------------

    def save_provenance_event(self, record: ProvenanceRecord) -> None:
        conn = self._conn()
        conn.execute(
            """INSERT OR REPLACE INTO mcpl_provenance_events
               (event_id, schema_version, parent_id, causation_id, correlation_id,
                event_type, timestamp, tenant_id, actor, subject, causal_links,
                payload, integrity, retention)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.event_id, record.schema_version, record.parent_id,
             record.causation_id, record.correlation_id,
             record.event_type, record.timestamp, record.tenant_id,
             json.dumps(record.actor), json.dumps(record.subject),
             json.dumps(record.causal_links), json.dumps(record.payload),
             json.dumps(record.integrity), json.dumps(record.retention)),
        )
        conn.commit()

    def get_provenance_event(self, event_id: str) -> Optional[ProvenanceRecord]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM mcpl_provenance_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if row is None:
            return None
        return ProvenanceRecord(
            schema_version=row["schema_version"] or "1.0.0",
            event_id=row["event_id"],
            parent_id=row["parent_id"] or "",
            causation_id=row["causation_id"] or "",
            correlation_id=row["correlation_id"] or "",
            event_type=row["event_type"] or "",
            timestamp=row["timestamp"] or "",
            tenant_id=row["tenant_id"] or "",
            actor=json.loads(row["actor"] or "{}"),
            subject=json.loads(row["subject"] or "{}"),
            causal_links=json.loads(row["causal_links"] or "[]"),
            payload=json.loads(row["payload"] or "{}"),
            integrity=json.loads(row["integrity"] or "{}"),
            retention=json.loads(row["retention"] or "{}"),
        )

    def list_provenance_events(
        self,
        *,
        event_type: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        limit: int = 100,
    ) -> List[ProvenanceRecord]:
        conn = self._conn()
        conditions = []
        params: list = []
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if correlation_id:
            conditions.append("correlation_id = ?")
            params.append(correlation_id)
        if causation_id:
            conditions.append("causation_id = ?")
            params.append(causation_id)

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM mcpl_provenance_events WHERE {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [
            ProvenanceRecord(
                schema_version=r["schema_version"] or "1.0.0",
                event_id=r["event_id"],
                parent_id=r["parent_id"] or "",
                causation_id=r["causation_id"] or "",
                correlation_id=r["correlation_id"] or "",
                event_type=r["event_type"] or "",
                timestamp=r["timestamp"] or "",
                tenant_id=r["tenant_id"] or "",
                actor=json.loads(r["actor"] or "{}"),
                subject=json.loads(r["subject"] or "{}"),
                causal_links=json.loads(r["causal_links"] or "[]"),
                payload=json.loads(r["payload"] or "{}"),
                integrity=json.loads(r["integrity"] or "{}"),
                retention=json.loads(r["retention"] or "{}"),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Bulk event save (used by emitter listener)
    # ------------------------------------------------------------------

    def save_provenance_events_batch(self, records: List[ProvenanceRecord]) -> None:
        conn = self._conn()
        conn.executemany(
            """INSERT OR REPLACE INTO mcpl_provenance_events
               (event_id, schema_version, parent_id, causation_id, correlation_id,
                event_type, timestamp, tenant_id, actor, subject, causal_links,
                payload, integrity, retention)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (r.event_id, r.schema_version, r.parent_id,
                 r.causation_id, r.correlation_id,
                 r.event_type, r.timestamp, r.tenant_id,
                 json.dumps(r.actor), json.dumps(r.subject),
                 json.dumps(r.causal_links), json.dumps(r.payload),
                 json.dumps(r.integrity), json.dumps(r.retention))
                for r in records
            ],
        )
        conn.commit()
