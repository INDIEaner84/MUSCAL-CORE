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
from features.memory_fabric.fabric import MemoryFabric


class TestMemoryType:
    def test_values(self):
        assert MemoryType.EPISODIC.value == "EPISODIC"
        assert MemoryType.SEMANTIC.value == "SEMANTIC"
        assert MemoryType.PROCEDURAL.value == "PROCEDURAL"
        assert MemoryType.DECISION.value == "DECISION"
        assert MemoryType.EXPERIENCE.value == "EXPERIENCE"
        assert MemoryType.CONTEXT.value == "CONTEXT"

    def test_is_enum(self):
        assert len(MemoryType) == 6

    def test_from_string(self):
        assert MemoryType("EPISODIC") == MemoryType.EPISODIC
        assert MemoryType("PROCEDURAL") == MemoryType.PROCEDURAL


class TestMemoryImportanceScore:
    def test_create_default(self):
        s = MemoryImportanceScore()
        assert s.frequency == 0.0
        assert s.total == 0.0

    def test_compute_total_default(self):
        s = MemoryImportanceScore()
        total = s.compute_total()
        assert total == 0.0

    def test_compute_total_mixed(self):
        s = MemoryImportanceScore(frequency=0.8, success_impact=0.9)
        total = s.compute_total()
        assert total > 0.0
        assert total < 1.0

    def test_compute_total_full(self):
        s = MemoryImportanceScore(
            frequency=1.0, success_impact=1.0, recency=1.0,
            confidence=1.0, future_usefulness=1.0, verification_level=1.0,
        )
        total = s.compute_total()
        assert total == 1.0

    def test_compute_total_capped(self):
        s = MemoryImportanceScore(frequency=2.0, success_impact=2.0)
        total = s.compute_total()
        assert total <= 1.0

    def test_to_dict(self):
        s = MemoryImportanceScore(frequency=0.5)
        d = s.to_dict()
        assert "memory_importance" in d
        assert d["memory_importance"]["frequency"] == 0.5

    def test_to_dict_sets_total(self):
        s = MemoryImportanceScore(frequency=1.0, success_impact=1.0)
        d = s.to_dict()
        assert d["memory_importance"]["total"] > 0.0


class TestMemoryEntry:
    def test_create_minimal(self):
        entry = MemoryEntry(id="m1", memory_type=MemoryType.EPISODIC,
                            content={"key": "val"}, source="test")
        assert entry.id == "m1"
        assert entry.memory_type == MemoryType.EPISODIC
        assert entry.timestamp != ""

    def test_create_with_string_type(self):
        entry = MemoryEntry(id="m1", memory_type="EPISODIC",
                            content={}, source="test")
        assert entry.memory_type == MemoryType.EPISODIC

    def test_to_dict(self):
        entry = MemoryEntry(id="m1", memory_type=MemoryType.DECISION,
                            content={"action": "deploy"}, source="kernel")
        d = entry.to_dict()
        assert d["memory_entry"]["id"] == "m1"
        assert d["memory_entry"]["memory_type"] == "DECISION"
        assert d["memory_entry"]["source"] == "kernel"

    def test_to_dict_with_importance(self):
        imp = MemoryImportanceScore(frequency=0.5)
        imp.compute_total()
        entry = MemoryEntry(id="m2", memory_type=MemoryType.SEMANTIC,
                            content={}, source="t", importance=imp)
        d = entry.to_dict()
        assert d["memory_entry"]["importance"] is not None
        assert d["memory_entry"]["importance"]["memory_importance"]["frequency"] == 0.5

    def test_references_default(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t")
        assert e.references == []

    def test_provenance_default(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t")
        assert "lifecycle_state" in e.provenance
        assert e.provenance["lifecycle_state"] == "NEW"

    def test_confidence_default(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t")
        assert e.confidence == 0.5

    def test_with_references(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t",
                        references=["r1", "r2"])
        assert len(e.references) == 2

    def test_with_provenance(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t",
                        provenance={"verified": True})
        assert e.provenance["verified"] is True


class TestUnifiedMemoryContext:
    def test_create_empty(self):
        ctx = UnifiedMemoryContext()
        assert ctx.experiences == []
        assert ctx.warnings == []

    def test_to_dict_empty(self):
        ctx = UnifiedMemoryContext()
        d = ctx.to_dict()
        assert d["unified_memory_context"]["experience_count"] == 0

    def test_to_dict_with_entries(self):
        e = MemoryEntry(id="e1", memory_type="EPISODIC", content={"r": "ok"}, source="t")
        ctx = UnifiedMemoryContext(experiences=[e])
        d = ctx.to_dict()
        assert d["unified_memory_context"]["experience_count"] == 1

    def test_to_dict_with_decisions(self):
        d_entry = MemoryEntry(id="d1", memory_type="DECISION", content={"c": "x"}, source="t")
        ctx = UnifiedMemoryContext(decisions=[d_entry])
        d = ctx.to_dict()
        assert d["unified_memory_context"]["decision_count"] == 1

    def test_to_dict_with_solutions(self):
        s = MemoryEntry(id="s1", memory_type="PROCEDURAL", content={}, source="t")
        ctx = UnifiedMemoryContext(previous_solutions=[s])
        d = ctx.to_dict()
        assert d["unified_memory_context"]["solution_count"] == 1

    def test_execution_id(self):
        ctx = UnifiedMemoryContext(execution_id="exec-1")
        assert ctx.execution_id == "exec-1"


class TestMemoryClassifier:
    def test_classify_execution(self):
        clf = MemoryClassifier()
        entries = clf.classify("runtime", {"status": "completed", "result": "ok"})
        assert len(entries) >= 1
        assert any(e.memory_type == MemoryType.EPISODIC for e in entries)

    def test_classify_decision(self):
        clf = MemoryClassifier()
        entries = clf.classify("kernel", {"decision": "selected strategy A"})
        assert any(e.memory_type == MemoryType.DECISION for e in entries)

    def test_classify_semantic(self):
        clf = MemoryClassifier()
        entries = clf.classify("knowledge", {"fact": "pattern found"})
        assert any(e.memory_type == MemoryType.SEMANTIC for e in entries)

    def test_classify_experience(self):
        clf = MemoryClassifier()
        entries = clf.classify("opt", {"experience": "good", "score": "0.9"})
        assert any(e.memory_type == MemoryType.EXPERIENCE for e in entries)

    def test_classify_context(self):
        clf = MemoryClassifier()
        entries = clf.classify("session", {"context": "production"})
        assert any(e.memory_type == MemoryType.CONTEXT for e in entries)

    def test_classify_with_hint(self):
        clf = MemoryClassifier()
        entries = clf.classify("test", {"data": "test"}, memory_type_hint="SEMANTIC")
        assert len(entries) == 1
        assert entries[0].memory_type == MemoryType.SEMANTIC

    def test_classify_with_invalid_hint(self):
        clf = MemoryClassifier()
        entries = clf.classify("test", {"data": "test"}, memory_type_hint="INVALID")
        assert len(entries) >= 1

    def test_classify_action_procedural(self):
        clf = MemoryClassifier()
        entries = clf.classify("tools", {"action": "step completed"})
        assert any(e.memory_type == MemoryType.PROCEDURAL for e in entries)

    def test_classify_event_execution(self):
        clf = MemoryClassifier()
        event = {"topic": "runtime.execution.completed", "payload": {"result": "ok"}}
        entries = clf.classify_event(event)
        assert any(e.memory_type == MemoryType.EPISODIC for e in entries)

    def test_classify_event_knowledge(self):
        clf = MemoryClassifier()
        event = {"topic": "knowledge.candidate.created", "payload": {"id": "k1"}}
        entries = clf.classify_event(event)
        assert any(e.memory_type == MemoryType.SEMANTIC for e in entries)

    def test_classify_event_tool(self):
        clf = MemoryClassifier()
        event = {"topic": "tool.executed", "payload": {"tool_id": "t1"}}
        entries = clf.classify_event(event)
        assert any(e.memory_type == MemoryType.PROCEDURAL for e in entries)

    def test_classify_event_kernel(self):
        clf = MemoryClassifier()
        event = {"topic": "kernel.intent.created", "payload": {"goal": "test"}}
        entries = clf.classify_event(event)
        assert any(e.memory_type == MemoryType.DECISION for e in entries)

    def test_classify_event_optimization(self):
        clf = MemoryClassifier()
        event = {"topic": "optimization.execution.evaluated", "payload": {"score": 0.8}}
        entries = clf.classify_event(event)
        assert any(e.memory_type == MemoryType.EXPERIENCE for e in entries)

    def test_classify_event_unknown(self):
        clf = MemoryClassifier()
        event = {"topic": "unknown.event", "payload": {}}
        entries = clf.classify_event(event)
        assert len(entries) >= 1

    def test_classify_knowledge_candidate(self):
        clf = MemoryClassifier()
        candidate = {"knowledge_candidate": {"id": "kc1", "problem": "bug", "solution": "fix"}}
        entries = clf.classify_knowledge_candidate(candidate)
        assert any(e.memory_type == MemoryType.SEMANTIC for e in entries)

    def test_each_entry_has_id(self):
        clf = MemoryClassifier()
        entries = clf.classify("test", {"execution": "completed", "step": "build"})
        for e in entries:
            assert e.id is not None

    def test_each_entry_has_timestamp(self):
        clf = MemoryClassifier()
        entries = clf.classify("test", {"execution": "completed"})
        for e in entries:
            assert e.timestamp != ""


class TestImportanceEngine:
    def test_score_default(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC", content={}, source="t")
        score = eng.score(entry)
        assert score.total >= 0.0

    def test_score_success_impact(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"status": "success"}, source="t")
        score = eng.score(entry)
        assert score.success_impact > 0.5

    def test_score_failure_impact(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"status": "failed"}, source="t")
        score = eng.score(entry)
        assert score.success_impact >= 0.4

    def test_score_procedural_future_usefulness(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={}, source="t")
        score = eng.score(entry)
        assert score.future_usefulness > 0.8

    def test_score_episodic_future_usefulness(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={}, source="t")
        score = eng.score(entry)
        assert score.future_usefulness == 0.5

    def test_score_context_future_usefulness(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="CONTEXT",
                            content={}, source="t")
        score = eng.score(entry)
        assert score.future_usefulness == 0.4

    def test_score_confidence(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={}, source="t", confidence=0.8)
        score = eng.score(entry)
        assert score.confidence == 0.8

    def test_score_verification_level_validated(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={}, source="t",
                            provenance={"verified": True})
        score = eng.score(entry)
        assert score.verification_level > 0.5

    def test_score_verification_level_unknown(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={}, source="t")
        score = eng.score(entry)
        assert score.verification_level == 0.2

    def test_score_frequency_with_entries(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={}, source="t", references=["r1"])
        others = [
            MemoryEntry(id="e2", memory_type="EPISODIC", content={}, source="t"),
            MemoryEntry(id="e3", memory_type="EPISODIC", content={}, source="t"),
        ]
        score = eng.score(entry, all_entries=others)
        assert score.frequency > 0.0

    def test_score_total_range(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={"status": "completed", "result": "passed"},
                            source="t", confidence=0.9,
                            provenance={"verified": True, "passed": True})
        score = eng.score(entry)
        assert score.total > 0.0


class TestMemoryRetriever:
    def test_retrieve_empty(self):
        retriever = MemoryRetriever()
        ctx = retriever.retrieve_context(execution_id="e1")
        assert ctx.execution_id == "e1"
        assert len(ctx.warnings) > 0

    def test_retrieve_with_warning(self):
        retriever = MemoryRetriever()
        ctx = retriever.retrieve_context()
        assert any("No prior memory" in w for w in ctx.warnings)

    def test_build_query_with_task(self):
        retriever = MemoryRetriever()
        q = retriever._build_query({"objective": "fix bug"}, None, None, None, None)
        assert "fix" in q
        assert "bug" in q

    def test_build_query_with_intent(self):
        retriever = MemoryRetriever()
        q = retriever._build_query(None, {"intent": {"goal": "implement feature"}}, None, None, None)
        assert "implement" in q

    def test_build_query_with_domain(self):
        retriever = MemoryRetriever()
        q = retriever._build_query(None, None, None, "testing", None)
        assert "testing" in q

    def test_build_query_with_constraints(self):
        retriever = MemoryRetriever()
        q = retriever._build_query(None, None, None, None, ["no side effects"])
        assert "no" in q

    def test_relevance_score_with_match(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"text": "bug fix completed"}, source="t")
        score = retriever._relevance_score(entry, "bug fix")
        assert score > 0.0

    def test_relevance_score_no_match(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"text": "deployment ok"}, source="t")
        score = retriever._relevance_score(entry, "bug fix")
        assert score == 0.0

    def test_relevance_score_empty_query(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"text": "test"}, source="t")
        score = retriever._relevance_score(entry, "")
        assert score == 0.1

    def test_fetch_all_entries_no_provider(self):
        retriever = MemoryRetriever()
        entries = retriever._fetch_all_entries()
        assert entries == []

    def test_register_store_provider(self):
        retriever = MemoryRetriever()
        provider = DummyStoreProvider()
        retriever.register_store_provider(provider)
        assert retriever._store_provider is not None

    def test_fetch_all_entries_with_provider(self):
        retriever = MemoryRetriever()
        provider = DummyStoreProvider()
        provider.entries = [
            MemoryEntry(id="s1", memory_type="EPISODIC", content={"r": "ok"}, source="t"),
        ]
        retriever.register_store_provider(provider)
        entries = retriever._fetch_all_entries()
        assert len(entries) == 1

    def test_classify_entry_adds_to_context(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"text": "completed"}, source="t")
        ctx = UnifiedMemoryContext()
        retriever._classify_entry(entry, ctx, "completed", 5)
        assert len(ctx.experiences) == 1

    def test_classify_entry_low_relevance(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={"text": "other"}, source="t")
        ctx = UnifiedMemoryContext()
        retriever._classify_entry(entry, ctx, "unrelated", 5)
        assert len(ctx.experiences) == 0


class TestMemoryEntryValidation:
    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="id is required"):
            MemoryEntry(id="", memory_type="EPISODIC", content={"a": 1}, source="t")

    def test_empty_source_raises(self):
        with pytest.raises(ValueError, match="source is required"):
            MemoryEntry(id="m1", memory_type="EPISODIC", content={"a": 1}, source="")

    def test_none_content_raises(self):
        with pytest.raises(ValueError, match="content is required"):
            MemoryEntry(id="m1", memory_type="EPISODIC", content=None, source="t")

    def test_empty_dict_content_valid(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t")
        assert e.content == {}

    def test_confidence_clamped_negative(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t", confidence=-0.5)
        assert e.confidence == 0.0

    def test_confidence_clamped_over_one(self):
        e = MemoryEntry(id="m1", memory_type="EPISODIC", content={}, source="t", confidence=1.5)
        assert e.confidence == 1.0


class TestClassifierExplain:
    def test_explain_execution(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("runtime", {"status": "completed"})
        assert any(r["type"] == "EPISODIC" for r in reasons)

    def test_explain_decision(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("kernel", {"decision": "selected A"})
        assert any(r["type"] == "DECISION" for r in reasons)

    def test_explain_semantic(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("knowledge", {"fact": "rule found"})
        assert any(r["type"] == "SEMANTIC" for r in reasons)

    def test_explain_experience(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("opt", {"score": "0.9", "outcome": "good"})
        assert any(r["type"] == "EXPERIENCE" for r in reasons)

    def test_explain_context(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("session", {"context": "production"})
        assert any(r["type"] == "CONTEXT" for r in reasons)

    def test_explain_default(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("test", {"unrelated": "data"})
        assert any(r["type"] == "EPISODIC" for r in reasons)
        assert any("default" in r["rule"] for r in reasons)

    def test_explain_each_has_type_and_rule(self):
        clf = MemoryClassifier()
        reasons = clf.explain_classification("test", {"execution": "completed", "step": "build"})
        for r in reasons:
            assert "type" in r
            assert "rule" in r


class TestImportanceExplain:
    def test_explain_returns_dict_with_total(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC", content={}, source="t")
        explanation = eng.explain(entry)
        assert "total" in explanation
        assert "factors" in explanation

    def test_explain_has_six_factors(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC", content={}, source="t")
        explanation = eng.explain(entry)
        assert len(explanation["factors"]) == 6

    def test_explain_each_factor_has_fields(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={"status": "passed"}, source="t", confidence=0.9,
                            provenance={"verified": True})
        explanation = eng.explain(entry)
        for f in explanation["factors"]:
            assert "factor" in f
            assert "value" in f
            assert "weight" in f
            assert "contribution" in f
            assert "reason" in f

    def test_explain_total_matches_score(self):
        eng = ImportanceEngine()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={"status": "completed"}, source="t", confidence=0.9)
        score = eng.score(entry)
        explanation = eng.explain(entry)
        assert explanation["total"] == score.total


class TestConsolidatorValidation:
    def test_validate_entry_valid(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="v1", memory_type="EPISODIC", content={"r": "ok"}, source="t")
        is_valid, reasons = con.validate_entry(entry)
        assert is_valid is True
        assert reasons == []

    def test_validate_entry_empty_id(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="v1", memory_type="EPISODIC", content={"r": "ok"}, source="t")
        entry.id = ""
        is_valid, reasons = con.validate_entry(entry)
        assert is_valid is False
        assert any("id" in r.lower() for r in reasons)

    def test_validate_entry_empty_source(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="v1", memory_type="EPISODIC", content={"r": "ok"}, source="t")
        entry.source = ""
        is_valid, reasons = con.validate_entry(entry)
        assert is_valid is False
        assert any("source" in r.lower() for r in reasons)

    def test_validate_entry_none_content(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="v1", memory_type="EPISODIC", content={"r": "ok"}, source="t")
        entry.content = None
        is_valid, reasons = con.validate_entry(entry)
        assert is_valid is False
        assert any("content" in r.lower() for r in reasons)


class TestRetrieverPriority:
    def test_sort_by_priority_verified_first(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"task": "fix bug"}, source="t",
                         provenance={"verified": True})
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"task": "fix bug"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "fix bug")
        assert sorted_entries[0].id == "e1"

    def test_sort_by_priority_success_before_neutral(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"status": "success"}, source="t")
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"status": "unknown"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "status")
        assert sorted_entries[0].id == "e1"

    def test_sort_by_priority_relevant_before_irrelevant(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"text": "fix bug in parser"}, source="t")
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"text": "deploy to prod"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "fix bug")
        assert sorted_entries[0].id == "e1"

    def test_priority_verified_and_success(self):
        retriever = MemoryRetriever()
        e1 = MemoryEntry(id="e1", memory_type="EPISODIC",
                         content={"text": "failed attempt"}, source="t",
                         provenance={"verified": True})
        e2 = MemoryEntry(id="e2", memory_type="EPISODIC",
                         content={"text": "great success"}, source="t")
        sorted_entries = retriever._sort_by_priority([e2, e1], "text")
        assert sorted_entries[0].id == "e1"


class DummyStoreProvider:
    def __init__(self):
        self.entries = []
        self.stored = []

    def list_entries(self):
        return self.entries

    def search(self, query, limit=10):
        return self.entries

    def save_entry(self, entry):
        self.stored.append(entry)


class TestMemoryConsolidator:
    def test_consolidate_basic(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed", "result": "ok"})
        assert len(entries) >= 1

    def test_consolidate_with_store(self):
        con = MemoryConsolidator()
        provider = DummyStoreProvider()
        entries = con.consolidate("test", {"status": "completed", "result": "ok"},
                                   store_provider=provider)
        assert len(entries) >= 1
        assert len(provider.stored) >= 1

    def test_consolidate_each_has_importance(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed", "result": "ok"})
        for e in entries:
            assert e.importance is not None

    def test_promote_high_importance(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={"status": "passed"}, source="t",
                            confidence=0.8)
        imp = MemoryImportanceScore(
            frequency=1.0, success_impact=1.0, recency=1.0,
            confidence=1.0, future_usefulness=1.0, verification_level=1.0,
        )
        imp.compute_total()
        entry.importance = imp
        result = con.promote(entry)
        assert result is not None
        assert result.confidence > 0.8

    def test_promote_low_importance(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="e2", memory_type="CONTEXT",
                            content={}, source="t", confidence=0.3)
        imp = MemoryImportanceScore()
        imp.compute_total()
        entry.importance = imp
        result = con.promote(entry)
        assert result is None

    def test_promote_with_store(self):
        con = MemoryConsolidator()
        provider = DummyStoreProvider()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={"status": "passed"}, source="t")
        imp = MemoryImportanceScore(
            frequency=1.0, success_impact=1.0, recency=1.0,
            confidence=1.0, future_usefulness=1.0, verification_level=1.0,
        )
        imp.compute_total()
        entry.importance = imp
        result = con.promote(entry, store_provider=provider)
        assert result is not None
        assert len(provider.stored) == 1

    def test_promote_provenance_preserved(self):
        con = MemoryConsolidator()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC",
                            content={}, source="t", provenance={"source": "test"})
        imp = MemoryImportanceScore(frequency=1.0, success_impact=1.0, recency=1.0,
                                     confidence=1.0, future_usefulness=1.0, verification_level=1.0)
        imp.compute_total()
        entry.importance = imp
        result = con.promote(entry)
        assert result.provenance["source"] == "test"

    def test_consolidate_preserves_provenance(self):
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed"})
        for e in entries:
            assert e.source == "test"


class TestMemoryFabric:
    def test_create(self):
        fabric = MemoryFabric()
        assert fabric is not None

    def test_classify(self):
        fabric = MemoryFabric()
        entries = fabric.classify("test", {"execution": "completed"})
        assert len(entries) >= 1

    def test_classify_event(self):
        fabric = MemoryFabric()
        event = {"topic": "runtime.execution.completed", "payload": {"r": "ok"}}
        entries = fabric.classify_event(event)
        assert len(entries) >= 1

    def test_retrieve_context(self):
        fabric = MemoryFabric()
        ctx = fabric.retrieve_context(execution_id="e1")
        assert ctx.execution_id == "e1"

    def test_consolidate(self):
        fabric = MemoryFabric()
        entries = fabric.consolidate("test", {"status": "completed"})
        assert len(entries) >= 1

    def test_promote_high(self):
        fabric = MemoryFabric()
        entry = MemoryEntry(id="e1", memory_type="PROCEDURAL",
                            content={"status": "passed"}, source="t")
        imp = MemoryImportanceScore(frequency=1.0, success_impact=1.0, recency=1.0,
                                     confidence=1.0, future_usefulness=1.0, verification_level=1.0)
        imp.compute_total()
        entry.importance = imp
        result = fabric.promote(entry)
        assert result is not None

    def test_promote_low(self):
        fabric = MemoryFabric()
        entry = MemoryEntry(id="e2", memory_type="CONTEXT",
                            content={}, source="t")
        imp = MemoryImportanceScore()
        imp.compute_total()
        entry.importance = imp
        result = fabric.promote(entry)
        assert result is None

    def test_score_importance(self):
        fabric = MemoryFabric()
        entry = MemoryEntry(id="e1", memory_type="EPISODIC", content={}, source="t")
        score = fabric.score_importance(entry)
        assert score.total >= 0.0

    def test_retriever_property(self):
        fabric = MemoryFabric()
        assert fabric.retriever is not None

    def test_classifier_property(self):
        fabric = MemoryFabric()
        assert fabric.classifier is not None

    def test_consolidate_with_store(self):
        provider = DummyStoreProvider()
        fabric = MemoryFabric(store_provider=provider)
        entries = fabric.consolidate("test", {"status": "completed"})
        assert len(entries) >= 1

    def test_fabric_classify_each_has_id(self):
        fabric = MemoryFabric()
        entries = fabric.classify("test", {"execution": "completed"})
        for e in entries:
            assert e.id is not None

    def test_fabric_retrieve_context_with_warning(self):
        fabric = MemoryFabric()
        ctx = fabric.retrieve_context()
        assert len(ctx.warnings) >= 1

    def test_fabric_consolidated_entries_have_importance(self):
        fabric = MemoryFabric()
        entries = fabric.consolidate("test", {"execution": "completed"})
        for e in entries:
            assert e.importance is not None

    def test_fabric_with_store_persists(self):
        provider = DummyStoreProvider()
        fabric = MemoryFabric(store_provider=provider)
        fabric.consolidate("test", {"status": "completed", "result": "passed"})
        assert len(provider.stored) >= 1

    def test_fabric_retriever_has_store(self):
        provider = DummyStoreProvider()
        provider.entries = [
            MemoryEntry(id="r1", memory_type="EPISODIC",
                        content={"text": "ok result from test run"}, source="t"),
        ]
        fabric = MemoryFabric(store_provider=provider)
        ctx = fabric.retrieve_context(task={"objective": "test"})
        assert len(ctx.warnings) == 0
