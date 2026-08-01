from __future__ import annotations

from features.knowledge.models import (
    KnowledgeCandidate, KnowledgeEntry, KnowledgeMatch,
    EvidenceLevel, KnowledgeState, KNOWLEDGE_EVENTS,
)


class TestKnowledgeModels:

    def test_knowledge_candidate_defaults(self):
        kc = KnowledgeCandidate(
            id="kc-1", source_execution_id="e1", source_task_id="t1",
            project="test", category="general", problem="test problem",
            solution="test solution", evidence="test evidence",
            verification="passed", confidence=0.8,
        )
        assert kc.state == KnowledgeState.CANDIDATE
        assert kc.evidence_level == EvidenceLevel.UNKNOWN
        assert kc.created_at is not None

    def test_knowledge_candidate_to_dict(self):
        kc = KnowledgeCandidate(
            id="kc-1", source_execution_id="e1", source_task_id="t1",
            project="test", category="bug_fix", problem="fix bug",
            solution="patched", evidence="tests pass",
            verification="verified", confidence=0.9,
        )
        d = kc.to_dict()
        assert d["knowledge_candidate"]["id"] == "kc-1"
        assert d["knowledge_candidate"]["category"] == "bug_fix"
        assert d["knowledge_candidate"]["confidence"] == 0.9

    def test_knowledge_entry_defaults(self):
        entry = KnowledgeEntry(knowledge_id="ke-1", candidate_id="kc-1", entry={"key": "val"})
        assert entry.stored_at is not None

    def test_knowledge_entry_to_dict(self):
        entry = KnowledgeEntry(knowledge_id="ke-1", candidate_id="kc-1", entry={"data": "test"})
        d = entry.to_dict()
        assert d["knowledge_entry"]["knowledge_id"] == "ke-1"
        assert d["knowledge_entry"]["entry"]["data"] == "test"

    def test_knowledge_match(self):
        match = KnowledgeMatch(
            entry={"data": "test"}, relevance=0.85,
            confidence=0.9, evidence="tests passed",
            source_execution="e1",
        )
        assert match.relevance == 0.85
        assert match.confidence == 0.9

    def test_knowledge_match_to_dict(self):
        match = KnowledgeMatch(
            entry={"data": "test"}, relevance=0.75,
            confidence=0.8, evidence="verified",
            source_execution="e1",
        )
        d = match.to_dict()
        assert d["knowledge_match"]["relevance"] == 0.75
        assert d["knowledge_match"]["source_execution"] == "e1"

    def test_evidence_level_enum(self):
        assert EvidenceLevel.VERIFIED.value == "VERIFIED"
        assert EvidenceLevel.OBSERVED.value == "OBSERVED"
        assert EvidenceLevel.UNKNOWN.value == "UNKNOWN"

    def test_knowledge_state_enum(self):
        assert KnowledgeState.CANDIDATE.value == "CANDIDATE"
        assert KnowledgeState.VALIDATED.value == "VALIDATED"
        assert KnowledgeState.REJECTED.value == "REJECTED"

    def test_knowledge_events_set(self):
        expected = {
            "knowledge.candidate.created",
            "knowledge.candidate.validated",
            "knowledge.candidate.rejected",
            "knowledge.entry.updated",
            "knowledge.retrieval.requested",
        }
        assert KNOWLEDGE_EVENTS == expected

    def test_candidate_confidence_range(self):
        kc = KnowledgeCandidate(
            id="kc-2", source_execution_id="e1", source_task_id="t1",
            project="test", category="general", problem="p",
            solution="s", evidence="ev", verification="v",
            confidence=0.5,
        )
        assert 0.0 <= kc.confidence <= 1.0

    def test_candidate_str_evidence_level(self):
        kc = KnowledgeCandidate(
            id="kc-3", source_execution_id="e1", source_task_id="t1",
            project="test", category="general", problem="p",
            solution="s", evidence="ev", verification="v",
            confidence=0.5, evidence_level="VERIFIED",
        )
        assert kc.evidence_level == EvidenceLevel.VERIFIED
