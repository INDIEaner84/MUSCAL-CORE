"""
Multi-LLM Review Package

Provides evidence-based multi-LLM review capabilities for MUSCAL CORE.
"""

from features.multi_llm_review.consensus_builder import ConsensusBuilder
from features.multi_llm_review.evidence_store import ReviewEvidenceStore
from features.multi_llm_review.review_schemas import (
    Consensus,
    ReviewFinding,
    ReviewTask,
    TechnicalVerification,
)
from features.multi_llm_review.technical_verifier import TechnicalVerifier

__version__ = "0.1.0"
__all__ = [
    "ReviewTask",
    "ReviewFinding",
    "TechnicalVerification",
    "Consensus",
    "ReviewEvidenceStore",
    "TechnicalVerifier",
    "ConsensusBuilder",
]
