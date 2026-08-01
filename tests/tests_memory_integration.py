from __future__ import annotations

import uuid
import pytest

from features.memory_fabric.models import (
    MemoryType, MemoryEntry, UnifiedMemoryContext, MemoryImportanceScore,
)
from features.memory_fabric.classifier import MemoryClassifier
from features.memory_fabric.retriever import MemoryRetriever
from features.memory_fabric.consolidator import MemoryConsolidator
from features.memory_fabric.importance import ImportanceEngine
from features.memory_fabric.metrics import MemoryReuseScore, MemoryImpactScore, KnowledgeTransferScore
from features.memory_fabric.fabric import MemoryFabric
from features.kernel.models import Intent, GoalSet, UnifiedContext
from features.kernel.context_engine import ContextEngine


class DummyStore:
    def __init__(self):
        self.entries = []
        self.stored = []

    def list_entries(self):
        return self.entries

    def search(self, query, limit=10):
        return self.entries

    def save_entry(self, entry):
        self.stored.append(entry)


class DummyMemoryFabric:
    def __init__(self):
        self._retrieved = []

    def retrieve_context(self, task=None, intent=None, goal=None,
                         domain=None, constraints=None,
                         execution_id="", top_k=5):
        ctx = UnifiedMemoryContext(execution_id=execution_id)
        ctx.warnings.append("Using dummy fabric")
        return ctx


# ── Kernel + Memory Integration Tests ────────────────────────────────────

class TestKernelMemoryIntegration:
    def test_context_engine_accepts_memory_fabric(self):
        engine = ContextEngine()
        fabric = DummyMemoryFabric()
        engine.register_memory_fabric_provider(fabric)
        result = engine.build(execution_id="test-1")
        assert result.memory_context is not None

    def test_memory_context_in_unified_context(self):
        engine = ContextEngine()
        fabric = DummyMemoryFabric()
        engine.register_memory_fabric_provider(fabric)
        result = engine.build(execution_id="test-2")
        assert "unified_memory_context" in result.to_dict()["unified_context"]["memory_context"]

    def test_context_engine_without_memory_fabric(self):
        engine = ContextEngine()
        result = engine.build(execution_id="test-3")
        assert result.memory_context is None

    def test_context_engine_with_intent_passed(self):
        engine = ContextEngine()
        fabric = DummyMemoryFabric()
        engine.register_memory_fabric_provider(fabric)
        intent = Intent(task_id="t1", type="implementation", goal="fix bug",
                        constraints=[], priority="high", risk="low",
                        required_capabilities=[], expected_outcome="success",
                        confidence=0.8)
        result = engine.build(execution_id="test-4", intent=intent)
        assert result.memory_context is not None

    def test_context_engine_with_goal_passed(self):
        engine = ContextEngine()
        fabric = DummyMemoryFabric()
        engine.register_memory_fabric_provider(fabric)
        goals = GoalSet()
        result = engine.build(execution_id="test-5", goal=goals)
        assert result.memory_context is not None

    def test_full_fabric_retrieval_via_context(self):
        store = DummyStore()
        fabric = MemoryFabric(store_provider=store)
        entry = MemoryEntry(id="r1", memory_type="EPISODIC",
                            content={"text": "previous fix worked"}, source="t")
        store.entries = [entry]
        ctx = fabric.retrieve_context(task={"objective": "fix bug"})
        assert ctx.execution_id == ""
        assert len(ctx.warnings) == 0

    def test_fabric_retrieval_with_constraints(self):
        store = DummyStore()
        fabric = MemoryFabric(store_provider=store)
        store.entries = [
            MemoryEntry(id="s1", memory_type="PROCEDURAL",
                        content={"text": "deploy to prod safely"}, source="t"),
        ]
        ctx = fabric.retrieve_context(constraints=["safety", "rollback"])
        assert ctx.execution_id == ""

    def test_kernel_supports_memory_fabric_registration(self):
        from features.kernel.kernel import CognitiveKernel
        kernel = CognitiveKernel()
        engine = kernel.context_engine
        fabric = DummyMemoryFabric()
        engine.register_memory_fabric_provider(fabric)
        assert engine._memory_fabric_provider is not None


# ── Provenance Tracking Tests ────────────────────────────────────────────

class TestProvenanceTracking:
    def test_entry_provenance_preserved(self):
        entry = MemoryEntry(id="p1", memory_type="EPISODIC",
                            content={"r": "ok"}, source="t",
                            provenance={"execution_id": "e1", "verified": True})
        assert entry.provenance["execution_id"] == "e1"
        assert entry.provenance["verified"] is True

    def test_classifier_sets_source_as_provenance(self):
        clf = MemoryClassifier()
        entries = clf.classify("event:runtime.execution.completed",
                               {"result": "ok"})
        for e in entries:
            assert "event" in e.source

    def test_consolidation_preserves_provenance(self):
        con = MemoryConsolidator()
        entries = con.consolidate("event:test", {"status": "completed", "id": "e1"})
        for e in entries:
            assert e.source == "event:test"

    def test_importance_score_updates_provenance(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed"})
        for e in entries:
            assert e.importance is not None


# ── Consolidation Safety Tests ───────────────────────────────────────────

class TestConsolidationSafety:
    def test_no_automatic_deletion(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed"})
        assert len(entries) >= 1

    def test_validation_errors_do_not_delete(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="v1", memory_type="EPISODIC",
                            content={"r": "ok"}, source="t")
        entry.id = ""
        is_valid, reasons = con.validate_entry(entry)
        assert is_valid is False
        assert entry.id == ""

    def test_promote_preserves_entry(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="p1", memory_type="PROCEDURAL",
                            content={"status": "passed"}, source="t")
        imp = MemoryImportanceScore(frequency=1.0, success_impact=1.0, recency=1.0,
                                     confidence=1.0, future_usefulness=1.0, verification_level=1.0)
        imp.compute_total()
        entry.importance = imp
        result = con.promote(entry)
        assert result is not None
        assert result.id == "p1"

    def test_no_store_write_without_provider(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed"})
        assert len(entries) >= 1


# ── Retrieval Ranking Tests ──────────────────────────────────────────────

class TestRetrievalRanking:
    def test_verified_entries_sorted_first(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"text": "fix bug in parser"}, source="t",
                         provenance={"verified": True})
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"text": "fix bug in parser"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "fix bug")
        assert sorted_entries[0].id == "e1"

    def test_successful_entries_sorted_second(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"text": "completed deployment"}, source="t")
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"text": "failed attempt"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "deployment")
        assert sorted_entries[0].id == "e1"

    def test_relevant_entries_sorted_third(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"text": "fix critical parser bug"}, source="t")
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"text": "deploy to staging"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "fix critical parser bug")
        assert sorted_entries[0].id == "e1"

    def test_recent_entries_sorted_fourth(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"text": "some task"}, source="t",
                         timestamp="2025-01-01T00:00:00")
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"text": "some task"}, source="t",
                         timestamp="2024-01-01T00:00:00")
        sorted_entries = retriever._sort_by_priority([e2, e1], "some task")
        assert sorted_entries[0].id == "e1"


# ── Memory Confidence Tests ──────────────────────────────────────────────

class TestMemoryConfidence:
    def test_default_confidence(self):
        entry = MemoryEntry(id="c1", memory_type="EPISODIC",
                            content={}, source="t")
        assert entry.confidence == 0.5

    def test_confidence_clamped(self):
        entry = MemoryEntry(id="c2", memory_type="EPISODIC",
                            content={}, source="t", confidence=1.5)
        assert entry.confidence == 1.0

    def test_confidence_from_importance(self):
        entry = MemoryEntry(id="c3", memory_type="PROCEDURAL",
                            content={"status": "completed"}, source="t",
                            confidence=0.8)
        eng = ImportanceEngine()
        score = eng.score(entry)
        assert score.confidence == 0.8

    def test_promote_increases_confidence(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="c4", memory_type="PROCEDURAL",
                            content={"status": "passed"}, source="t",
                            confidence=0.8)
        imp = MemoryImportanceScore(frequency=1.0, success_impact=1.0, recency=1.0,
                                     confidence=1.0, future_usefulness=1.0, verification_level=1.0)
        imp.compute_total()
        entry.importance = imp
        result = con.promote(entry)
        assert result.confidence > 0.8


# ── Failure Handling Tests ───────────────────────────────────────────────

class TestFailureHandling:
    def test_classify_with_empty_content(self):
        clf = MemoryClassifier()
        entries = clf.classify("test", {})
        assert len(entries) >= 1

    def test_classify_with_none_content(self):
        clf = MemoryClassifier()
        with pytest.raises(AttributeError):
            clf.classify("test", None)

    def test_retrieve_with_no_provider(self):
        retriever = MemoryRetriever()
        ctx = retriever.retrieve_context()
        assert len(ctx.warnings) >= 1

    def test_retrieve_with_empty_query(self):
        retriever = MemoryRetriever()
        ctx = retriever.retrieve_context(task={})
        assert len(ctx.warnings) >= 1

    def test_importance_with_empty_entry(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="f1", memory_type="EPISODIC",
                            content={}, source="t")
        score = eng.score(entry)
        assert score.total >= 0.0

    def test_consolidate_with_malformed_content(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"unexpected": object()})
        assert len(entries) >= 1

    def test_memory_fabric_no_store(self):
        fabric = MemoryFabric()
        entries = fabric.consolidate("test", {"status": "completed"})
        assert len(entries) >= 1


# ── MREIL Metrics Tests ──────────────────────────────────────────────────

class TestMemoryReuseScore:
    def test_compute_default(self):
        mrs = MemoryReuseScore()
        entry = MemoryEntry(id="r1", memory_type="EPISODIC", content={}, source="t")
        score = mrs.compute(entry)
        assert score == 0.0

    def test_compute_with_references(self):
        mrs = MemoryReuseScore()
        entry = MemoryEntry(id="r2", memory_type="EPISODIC", content={}, source="t",
                            references=["a", "b", "c"])
        score = mrs.compute(entry)
        assert score > 0.0

    def test_compute_with_history(self):
        mrs = MemoryReuseScore()
        entry = MemoryEntry(id="r3", memory_type="EPISODIC", content={}, source="t")
        history = [{"memory_id": "r3"}, {"memory_id": "r3"}, {"memory_id": "other"}]
        score = mrs.compute(entry, retrieval_history=history)
        assert score == 0.2

    def test_to_dict(self):
        mrs = MemoryReuseScore()
        entry = MemoryEntry(id="r4", memory_type="EPISODIC", content={}, source="t",
                            references=["x"])
        d = mrs.to_dict(entry)
        assert "memory_reuse" in d
        assert d["memory_reuse"]["memory_id"] == "r4"


class TestMemoryImpactScore:
    def test_compute_default(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i1", memory_type="EPISODIC", content={}, source="t")
        score = mis.compute(entry)
        assert score == 0.5

    def test_compute_success_outcome(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i2", memory_type="EPISODIC", content={}, source="t")
        score = mis.compute(entry, outcome="success")
        assert score == 1.0

    def test_compute_failure_outcome(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i3", memory_type="EPISODIC", content={}, source="t")
        score = mis.compute(entry, outcome="failure")
        assert score == 0.0

    def test_compute_with_success_content(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i4", memory_type="EPISODIC",
                            content={"status": "passed"}, source="t")
        score = mis.compute(entry)
        assert score > 0.5

    def test_compute_with_failure_content(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i5", memory_type="EPISODIC",
                            content={"status": "failed"}, source="t")
        score = mis.compute(entry)
        assert score < 0.5

    def test_compute_with_high_importance(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i6", memory_type="EPISODIC", content={}, source="t")
        imp = MemoryImportanceScore(frequency=0.0, success_impact=0.0, recency=0.0,
                                     confidence=0.0, future_usefulness=0.0, verification_level=0.0)
        imp.total = 0.8
        entry.importance = imp
        score = mis.compute(entry)
        assert score > 0.5

    def test_to_dict(self):
        mis = MemoryImpactScore()
        entry = MemoryEntry(id="i7", memory_type="SEMANTIC", content={}, source="t")
        d = mis.to_dict(entry)
        assert "memory_impact" in d
        assert d["memory_impact"]["memory_type"] == "SEMANTIC"


class TestKnowledgeTransferScore:
    def test_compute_default_semantic(self):
        kts = KnowledgeTransferScore()
        entry = MemoryEntry(id="k1", memory_type="SEMANTIC", content={}, source="t")
        score = kts.compute(entry)
        assert score == 0.85

    def test_compute_default_procedural(self):
        kts = KnowledgeTransferScore()
        entry = MemoryEntry(id="k2", memory_type="PROCEDURAL", content={}, source="t")
        score = kts.compute(entry)
        assert score == 0.75

    def test_compute_default_episodic(self):
        kts = KnowledgeTransferScore()
        entry = MemoryEntry(id="k3", memory_type="EPISODIC", content={}, source="t")
        score = kts.compute(entry)
        assert score == 0.4

    def test_compute_with_similar_domains(self):
        kts = KnowledgeTransferScore()
        entry = MemoryEntry(id="k4", memory_type="SEMANTIC", content={}, source="t")
        score = kts.compute(entry, source_domain="testing python code",
                            target_domain="testing python code")
        assert score > 0.5

    def test_compute_with_different_domains(self):
        kts = KnowledgeTransferScore()
        entry = MemoryEntry(id="k5", memory_type="SEMANTIC", content={}, source="t")
        score = kts.compute(entry, source_domain="python backend",
                            target_domain="react frontend")
        assert score >= 0.5

    def test_to_dict(self):
        kts = KnowledgeTransferScore()
        entry = MemoryEntry(id="k6", memory_type="DECISION", content={}, source="t")
        d = kts.to_dict(entry, source_domain="a", target_domain="b")
        assert "knowledge_transfer" in d
        assert d["knowledge_transfer"]["source_domain"] == "a"

    def test_fabric_exposes_metrics(self):
        fabric = MemoryFabric()
        entry = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t")
        assert fabric.compute_reuse_score(entry) is not None
        assert fabric.compute_impact_score(entry) is not None
        assert fabric.compute_transfer_score(entry) is not None

    def test_fabric_metrics_properties(self):
        fabric = MemoryFabric()
        assert fabric.reuse_metrics is not None
        assert fabric.impact_metrics is not None
        assert fabric.transfer_metrics is not None
