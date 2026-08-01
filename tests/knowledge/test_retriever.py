from __future__ import annotations

from features.knowledge.retriever import KnowledgeRetriever
from features.knowledge.knowledge_writer import KnowledgeWriter
from features.knowledge.models import KnowledgeCandidate


class TestKnowledgeRetriever:

    def _make_writer_with_entries(self, entries: list[dict]) -> KnowledgeWriter:
        writer = KnowledgeWriter()
        for e in entries:
            candidate = KnowledgeCandidate(
                id=e.get("id", "kc-x"),
                source_execution_id=e.get("execution", "e1"),
                source_task_id=e.get("task", "t1"),
                project=e.get("project", "test"),
                category=e.get("category", "general"),
                problem=e.get("problem", "test problem"),
                solution=e.get("solution", "test solution"),
                evidence=e.get("evidence", "verified"),
                verification=e.get("verification", "passed"),
                confidence=e.get("confidence", 0.8),
                evidence_level=e.get("evidence_level", "VERIFIED"),
                state=e.get("state", "VALIDATED"),
            )
            writer.write_validated(candidate)
        return writer

    def test_retrieve_relevant(self):
        writer = self._make_writer_with_entries([
            {"id": "kc-1", "problem": "fix login bug", "solution": "fixed validation"},
            {"id": "kc-2", "problem": "testing pipeline", "solution": "added tests"},
        ])
        retriever = KnowledgeRetriever(writer=writer)
        results = retriever.retrieve_relevant("login bug", top_k=3)
        assert len(results) >= 1

    def test_retrieve_empty_writer(self):
        writer = KnowledgeWriter()
        retriever = KnowledgeRetriever(writer=writer)
        results = retriever.retrieve_relevant("anything", top_k=3)
        assert len(results) == 0

    def test_retrieve_scored_by_relevance(self):
        writer = self._make_writer_with_entries([
            {"id": "kc-1", "problem": "fix login authentication bug", "solution": "fixed"},
            {"id": "kc-2", "problem": "add documentation for API", "solution": "wrote docs"},
        ])
        retriever = KnowledgeRetriever(writer=writer)
        results = retriever.retrieve_relevant("authentication login", top_k=3)
        assert len(results) > 0
        if len(results) >= 2:
            assert results[0].relevance >= results[1].relevance

    def test_retrieve_match_has_correct_fields(self):
        writer = self._make_writer_with_entries([
            {"id": "kc-1", "problem": "fix login bug", "solution": "fixed", "confidence": 0.9, "evidence": "tests pass", "execution": "e1"},
        ])
        retriever = KnowledgeRetriever(writer=writer)
        results = retriever.retrieve_relevant("login", top_k=3)
        if results:
            m = results[0]
            assert m.relevance > 0
            assert m.confidence > 0
            assert m.evidence is not None
            assert m.source_execution is not None

    def test_no_false_matches(self):
        writer = self._make_writer_with_entries([
            {"id": "kc-1", "problem": "database migration script", "solution": "ran migration"},
        ])
        retriever = KnowledgeRetriever(writer=writer)
        results = retriever.retrieve_relevant("frontend ui design", top_k=3)
        assert len(results) == 0
