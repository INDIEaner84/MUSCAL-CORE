from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .opencode_adapter import OpenCodeAdapter, OpenCodeResult


RECOVERY_STRATEGIES = frozenset({
    "retry",
    "resume_session",
    "fallback_execution",
    "report_failure",
})


@dataclass
class RecoveryAction:
    strategy: str
    description: str
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RecoveryEvent:
    execution_id: str
    original_status: str
    recovery_action: RecoveryAction
    result: Optional[dict] = None
    recovered: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "recovery_event": {
                "execution_id": self.execution_id,
                "original_status": self.original_status,
                "recovery_action": {
                    "strategy": self.recovery_action.strategy,
                    "description": self.recovery_action.description,
                    "retry_count": self.recovery_action.retry_count,
                },
                "recovered": self.recovered,
                "result": self.result,
                "timestamp": self.timestamp,
            }
        }


class RecoveryHandler:

    def __init__(self, adapter: OpenCodeAdapter, max_retries: int = 3):
        self._adapter = adapter
        self._max_retries = max_retries
        self._recovery_history: list[RecoveryEvent] = []

    def handle(self, result: OpenCodeResult, execution_id: str,
               message: str, session: Optional[str] = None) -> RecoveryEvent:
        if result.status == "completed":
            return self._no_recovery_needed(execution_id, result)

        strategy = self._determine_strategy(result)
        action = RecoveryAction(
            strategy=strategy,
            description=f"Recovering from {result.status}",
            max_retries=self._max_retries,
        )

        recovered = False
        recovery_result = None

        if strategy == "retry":
            recovered, recovery_result = self._retry(message, session, action)
        elif strategy == "resume_session" and session:
            recovered, recovery_result = self._resume_session(message, session, action)
        elif strategy == "report_failure":
            recovered = False
            recovery_result = {"note": "No recovery strategy available"}

        event = RecoveryEvent(
            execution_id=execution_id,
            original_status=result.status,
            recovery_action=action,
            result=recovery_result,
            recovered=recovered,
        )
        self._recovery_history.append(event)
        return event

    def get_recovery_history(self) -> list[RecoveryEvent]:
        return list(self._recovery_history)

    def _determine_strategy(self, result: OpenCodeResult) -> str:
        if result.status == "timeout":
            return "retry"
        elif result.status == "failed":
            return "resume_session" if result.session_reference else "retry"
        elif result.status == "not-found":
            return "report_failure"
        return "report_failure"

    def _retry(self, message: str, session: Optional[str],
               action: RecoveryAction) -> tuple[bool, dict]:
        for attempt in range(1, action.max_retries + 1):
            action.retry_count = attempt
            retry_result = self._adapter.execute(
                message=message,
                session=session,
            )
            if retry_result.status == "completed":
                return True, {
                    "attempts": attempt,
                    "status": retry_result.status,
                    "return_code": retry_result.return_code,
                }
        return False, {
            "attempts": action.max_retries,
            "final_status": retry_result.status if 'retry_result' in dir() else "unknown",
        }

    def _resume_session(self, message: str, session: str,
                        action: RecoveryAction) -> tuple[bool, dict]:
        for attempt in range(1, action.max_retries + 1):
            action.retry_count = attempt
            resume_result = self._adapter.execute(
                message=message,
                session=session,
            )
            if resume_result.status == "completed":
                return True, {
                    "attempts": attempt,
                    "strategy": "resume_session",
                    "session": session,
                }
        return False, {
            "attempts": action.max_retries,
            "strategy": "resume_session",
            "session": session,
            "final_status": resume_result.status if 'resume_result' in dir() else "unknown",
        }

    def _no_recovery_needed(self, execution_id: str,
                            result: OpenCodeResult) -> RecoveryEvent:
        action = RecoveryAction(
            strategy="report_failure",
            description="Execution completed successfully — no recovery needed",
        )
        event = RecoveryEvent(
            execution_id=execution_id,
            original_status=result.status,
            recovery_action=action,
            result={"status": result.status, "return_code": result.return_code},
            recovered=True,
        )
        self._recovery_history.append(event)
        return event
