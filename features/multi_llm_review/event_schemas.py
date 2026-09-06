"""
Event Schemas for Multi-LLM Review Events.

Defines payload structures for EventStore topics:
- review.task
- review.finding
- review.consensus
"""

REVIEW_TASK_PAYLOAD_FIELDS = (
    "task_id",
    "target_commit",
    "review_type",
    "target_files",
    "created_at",
)

REVIEW_FINDING_PAYLOAD_FIELDS = (
    "finding_id",
    "review_task_id",
    "finding_type",
    "severity",
    "confidence",
    "claim",
    "evidence",
    "file_refs",
    "created_at",
)

TECHNICAL_VERIFICATION_PAYLOAD_FIELDS = (
    "verification_id",
    "review_task_id",
    "tests_passed",
    "tests_total",
    "tests_failed",
    "tests_skipped",
    "coverage_pct",
    "static_analysis",
    "import_checks",
    "findings",
    "created_at",
)

REVIEW_CONSENSUS_PAYLOAD_FIELDS = (
    "consensus_id",
    "review_task_id",
    "status",
    "confidence",
    "dissent",
    "recommended_actions",
    "model_findings",
    "technical_verification",
    "created_at",
)

EVENT_TOPICS = {
    "review.task": REVIEW_TASK_PAYLOAD_FIELDS,
    "review.finding": REVIEW_FINDING_PAYLOAD_FIELDS,
    "verification.result": TECHNICAL_VERIFICATION_PAYLOAD_FIELDS,
    "review.consensus": REVIEW_CONSENSUS_PAYLOAD_FIELDS,
}

def validate_payload(topic: str, payload: dict) -> bool:
    """Validiert dass Payload alle erforderlichen Felder hat."""
    required = EVENT_TOPICS.get(topic, ())
    return all(field in payload for field in required)
