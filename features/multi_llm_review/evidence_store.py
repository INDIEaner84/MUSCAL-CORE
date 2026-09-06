"""
Review Evidence Store - Wrapper um bestehenden EventStore.

Kein neuer SQLite-Store. Routet Review-Events durch
runtime.event_store.EventStore (append-only, hash-chained).
"""

from features.multi_llm_review.event_schemas import validate_payload
from features.multi_llm_review.review_schemas import (
    Consensus,
    ReviewFinding,
    ReviewTask,
    TechnicalVerification,
)
from runtime.event_store import EventStore


class ReviewEvidenceStore:
    """Routet Review-Events durch bestehenden EventStore."""

    def __init__(self, event_store: EventStore):
        self._store = event_store

    def record_review_task(self, task: ReviewTask) -> int:
        """Speichert ReviewTask als Event."""
        payload = task.to_dict()
        if not validate_payload("review.task", payload):
            raise ValueError("Invalid review.task payload")
        return self._store.append(
            topic="review.task",
            payload=payload,
            source="multi_llm_review",
        )

    def record_review_finding(self, finding: ReviewFinding) -> int:
        """Speichert ReviewFinding als Event."""
        payload = finding.to_dict()
        if not validate_payload("review.finding", payload):
            raise ValueError("Invalid review.finding payload")
        return self._store.append(
            topic="review.finding",
            payload=payload,
            source="multi_llm_review",
        )

    def record_technical_verification(self, verification: TechnicalVerification) -> int:
        """Speichert TechnicalVerification als Event."""
        payload = verification.to_dict()
        if not validate_payload("verification.result", payload):
            raise ValueError("Invalid verification.result payload")
        return self._store.append(
            topic="verification.result",
            payload=payload,
            source="multi_llm_review",
        )

    def record_consensus(self, consensus: Consensus) -> int:
        """Speichert Consensus als Event."""
        payload = consensus.to_dict()
        if not validate_payload("review.consensus", payload):
            raise ValueError("Invalid review.consensus payload")
        return self._store.append(
            topic="review.consensus",
            payload=payload,
            source="multi_llm_review",
        )

    def get_review_findings(self, review_task_id: str) -> list[ReviewFinding]:
        """Liest alle Findings für einen ReviewTask."""
        events = self._store.replay(topic="review.finding")
        findings = []
        for event in events:
            if event.payload.get("review_task_id") == review_task_id:
                finding = ReviewFinding(**event.payload)
                findings.append(finding)
        return findings

    def get_technical_verification(self, review_task_id: str) -> TechnicalVerification | None:
        """Liest TechnicalVerification für einen ReviewTask."""
        events = self._store.replay(topic="verification.result")
        for event in events:
            if event.payload.get("review_task_id") == review_task_id:
                return TechnicalVerification(**event.payload)
        return None

    def get_consensus(self, review_task_id: str) -> Consensus | None:
        """Liest Consensus für einen ReviewTask."""
        events = self._store.replay(topic="review.consensus")
        for event in events:
            if event.payload.get("review_task_id") == review_task_id:
                return Consensus(**event.payload)
        return None
