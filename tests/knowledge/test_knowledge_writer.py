from __future__ import annotations

from features.knowledge.knowledge_writer import KnowledgeWriter
from features.knowledge.models import KnowledgeCandidate, KnowledgeState


class TestKnowledgeWriter:

    def _make_candidate(self, **overrides):
        params = dict(
            id="kc-1", source_execution_id="e1", source_task_id="t1",
            project="test", category="general",
            problem="test problem", solution="test solution",
            evidence="verified", verification="passed",
            confidence=0.8,
        )
        params.update(overrides)
        return KnowledgeCandidate(**params)

    def test_write_candidate(self):
        writer = KnowledgeWriter()
        candidate = self._make_candidate()
        result = writer.write_candidate(candidate)
        assert result == candidate.id
        assert len(writer.list_candidates()) == 1

    def test_write_validated(self):
        writer = KnowledgeWriter()
        candidate = self._make_candidate()
        kid = writer.write_validated(candidate)
        assert kid is not None
        assert len(writer.list_entries()) == 1
        assert candidate.state == KnowledgeState.VALIDATED

    def test_write_rejected(self):
        writer = KnowledgeWriter()
        candidate = self._make_candidate()
        writer.write_rejected(candidate)
        assert candidate.state == KnowledgeState.REJECTED

    def test_get_entry(self):
        writer = KnowledgeWriter()
        candidate = self._make_candidate()
        kid = writer.write_validated(candidate)
        entry = writer.get_entry(kid)
        assert entry is not None
        assert entry["knowledge_entry"]["candidate_id"] == "kc-1"

    def test_get_entry_not_found(self):
        writer = KnowledgeWriter()
        entry = writer.get_entry("nonexistent")
        assert entry is None

    def test_write_candidate_emits_event(self):
        events = []
        class MockEmitter:
            def emit(self, topic, payload, **kwargs):
                events.append((topic, payload))
        writer = KnowledgeWriter(event_emitter=MockEmitter())
        candidate = self._make_candidate()
        writer.write_candidate(candidate)
        assert len(events) == 1
        assert events[0][0] == "knowledge.candidate.created"

    def test_write_validated_emits_event(self):
        events = []
        class MockEmitter:
            def emit(self, topic, payload, **kwargs):
                events.append((topic, payload))
        writer = KnowledgeWriter(event_emitter=MockEmitter())
        candidate = self._make_candidate()
        writer.write_validated(candidate)
        assert len(events) == 1
        assert events[0][0] == "knowledge.candidate.validated"

    def test_list_candidates_empty(self):
        writer = KnowledgeWriter()
        assert writer.list_candidates() == []

    def test_list_entries_empty(self):
        writer = KnowledgeWriter()
        assert writer.list_entries() == []

    def test_multiple_candidates(self):
        writer = KnowledgeWriter()
        c1 = self._make_candidate(id="kc-1")
        c2 = self._make_candidate(id="kc-2")
        writer.write_candidate(c1)
        writer.write_candidate(c2)
        assert len(writer.list_candidates()) == 2
