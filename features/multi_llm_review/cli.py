"""
CLI Entry Point for Multi-LLM Review.

Usage:
    python -m features.multi_llm_review.cli run --commit <sha>
    python -m features.multi_llm_review.cli run --pr <number>
"""

import argparse
import sys
from typing import Optional

from features.multi_llm_review.orchestrator.orchestrator import (
    OrchestratorConfig,
    ReviewOrchestrator,
)
from features.multi_llm_review.review_schemas import ReviewTask
from runtime.database import get_connection
from runtime.event_store import EventStore


def create_event_store() -> EventStore:
    """Create EventStore instance."""
    conn = get_connection()
    return EventStore(conn)


def run_review(
    commit: str,
    review_type: str = "full",
    files: Optional[list[str]] = None,
) -> int:
    """Run review for a commit."""
    orchestrator = ReviewOrchestrator(
        event_store=create_event_store(),
        config=OrchestratorConfig(),
    )

    task = ReviewTask(
        target_commit=commit,
        review_type=review_type,
        target_files=files or [],
    )

    result = orchestrator.run_review(task)

    print(f"Review completed: {result.run_id}")
    print(f"Status: {result.consensus.status}")
    print(f"Confidence: {result.consensus.confidence:.2f}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Findings: {sum(len(f) for f in result.agent_findings.values())}")
    tv = result.technical_verification
    print(f"Technical Verification: {'PASS' if tv.tests_passed else 'FAIL'}")

    if result.errors:
        print(f"Errors: {result.errors}")

    return 0 if result.consensus.status in ("VERIFIED", "PARTIALLY") else 1


def main():
    parser = argparse.ArgumentParser(description="MUSCAL Multi-LLM Review CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run review for a commit")
    run_parser.add_argument("--commit", required=True, help="Target commit SHA")
    run_parser.add_argument(
        "--type",
        default="full",
        choices=["full", "security", "architecture", "quality", "pr"],
    )
    run_parser.add_argument("--files", nargs="*", help="Specific files to review")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(run_review(args.commit, args.type, args.files))


if __name__ == "__main__":
    main()
