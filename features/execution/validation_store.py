from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

from runtime.database import get_connection

log = logging.getLogger("muscal.execution.validation_store")


class ValidationArtifactStore:

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path

    def set_db_path(self, db_path: Path) -> None:
        self._db_path = db_path

    def store(self, artifact: dict) -> bool:
        if self._db_path is None:
            return False
        try:
            conn = get_connection(self._db_path)
            conn.execute("""INSERT OR FAIL INTO validation_artifacts (
                validation_id, evaluation_id, execution_id,
                trace_id, span_id, decision_id,
                agent_id, model_id, outcome_id,
                validation_result, evidence_status, rationale,
                integrity_hash, created_at, finalized
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
                artifact.get("validation_id", ""),
                artifact.get("evaluation_id", ""),
                artifact.get("execution_id", ""),
                artifact.get("trace_id", ""),
                artifact.get("span_id", ""),
                artifact.get("decision_id", ""),
                artifact.get("agent_id", ""),
                artifact.get("model_id", ""),
                artifact.get("outcome_id", ""),
                artifact.get("validation_result", "INCONCLUSIVE"),
                artifact.get("evidence_status", "MISSING"),
                artifact.get("rationale", ""),
                artifact.get("integrity_hash", ""),
                artifact.get("created_at", 0.0),
                1 if artifact.get("finalized", False) else 0,
            ])
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log.warning("Failed to store validation %s: %s",
                        artifact.get("validation_id", ""), e)
            return False

    def load(self, validation_id: str) -> Optional[dict]:
        if self._db_path is None:
            return None
        try:
            conn = get_connection(self._db_path)
            row = conn.execute(
                "SELECT * FROM validation_artifacts WHERE validation_id = ?",
                [validation_id]
            ).fetchone()
            conn.close()
            if row is None:
                return None
            d = dict(row)
            d["finalized"] = bool(d.get("finalized", 0))
            return d
        except Exception as e:
            log.warning("Failed to load validation %s: %s", validation_id, e)
            return None

    def load_by_evaluation(self, evaluation_id: str) -> list[dict]:
        if self._db_path is None:
            return []
        try:
            conn = get_connection(self._db_path)
            rows = conn.execute(
                "SELECT * FROM validation_artifacts WHERE evaluation_id = ? ORDER BY created_at",
                [evaluation_id]
            ).fetchall()
            conn.close()
            result = []
            for row in rows:
                d = dict(row)
                d["finalized"] = bool(d.get("finalized", 0))
                result.append(d)
            return result
        except Exception as e:
            log.warning("Failed to load validations for evaluation %s: %s",
                        evaluation_id, e)
            return []

    def load_by_execution(self, execution_id: str) -> list[dict]:
        if self._db_path is None:
            return []
        try:
            conn = get_connection(self._db_path)
            rows = conn.execute(
                "SELECT * FROM validation_artifacts WHERE execution_id = ? ORDER BY created_at",
                [execution_id]
            ).fetchall()
            conn.close()
            result = []
            for row in rows:
                d = dict(row)
                d["finalized"] = bool(d.get("finalized", 0))
                result.append(d)
            return result
        except Exception as e:
            log.warning("Failed to load validations for execution %s: %s",
                        execution_id, e)
            return []

    def exists(self, validation_id: str) -> bool:
        return self.load(validation_id) is not None

    def verify_integrity(self, artifact: dict) -> bool:
        from features.execution.evaluation_validation import EvaluationValidation
        v = EvaluationValidation.from_dict(artifact)
        return v.verify_integrity()
