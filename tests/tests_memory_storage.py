from __future__ import annotations

import json
import os
import tempfile
import pytest

from features.memory_fabric.models import (
    MemoryType, MemoryEntry, MemoryImportanceScore,
    LifecycleState, LIFECYCLE_STATES, LIFECYCLE_TRANSITIONS,
)
from features.memory_fabric.storage.sqlite_provider import SQLiteMemoryProvider
from features.memory_fabric.event_listener import EventListener
from features.memory_fabric.fabric import MemoryFabric


# ── Lifecycle Tests ──────────────────────────────────────────────────────

class TestLifecycleState:
    def test_values(self):
        assert LifecycleState.NEW.value == "NEW"
        assert LifecycleState.CLASSIFIED.value == "CLASSIFIED"
        assert LifecycleState.VALIDATED.value == "VALIDATED"
        assert LifecycleState.PROMOTED.value == "PROMOTED"
        assert LifecycleState.ARCHIVED.value == "ARCHIVED"

    def test_lifecycle_states_frozenset(self):
        assert "NEW" in LIFECYCLE_STATES
        assert "ARCHIVED" in LIFECYCLE_STATES

    def test_transitions_new_to_classified(self):
        assert "CLASSIFIED" in LIFECYCLE_TRANSITIONS["NEW"]

    def test_transitions_classified_to_validated(self):
        assert "VALIDATED" in LIFECYCLE_TRANSITIONS["CLASSIFIED"]

    def test_transitions_validated_to_promoted(self):
        assert "PROMOTED" in LIFECYCLE_TRANSITIONS["VALIDATED"]

    def test_transitions_validated_to_archived(self):
        assert "ARCHIVED" in LIFECYCLE_TRANSITIONS["VALIDATED"]

    def test_transitions_promoted_to_archived(self):
        assert "ARCHIVED" in LIFECYCLE_TRANSITIONS["PROMOTED"]

    def test_transitions_archived_no_targets(self):
        assert LIFECYCLE_TRANSITIONS["ARCHIVED"] == set()

    def test_invalid_transition(self):
        entry = MemoryEntry(id="l1", memory_type="EPISODIC", content={}, source="t")
        ok, _ = entry.transition_lifecycle("PROMOTED")
        assert ok is False

    def test_valid_transition_new_to_classified(self):
        entry = MemoryEntry(id="l2", memory_type="EPISODIC", content={}, source="t")
        ok, reason = entry.transition_lifecycle("CLASSIFIED")
        assert ok is True
        assert "CLASSIFIED" in reason

    def test_full_lifecycle(self):
        entry = MemoryEntry(id="l3", memory_type="EPISODIC", content={"r": "ok"}, source="t")
        assert entry.lifecycle_state == "NEW"
        entry.transition_lifecycle("CLASSIFIED")
        assert entry.lifecycle_state == "CLASSIFIED"
        entry.transition_lifecycle("VALIDATED")
        assert entry.lifecycle_state == "VALIDATED"
        entry.transition_lifecycle("PROMOTED")
        assert entry.lifecycle_state == "PROMOTED"
        entry.transition_lifecycle("ARCHIVED")
        assert entry.lifecycle_state == "ARCHIVED"

    def test_lifecycle_state_in_to_dict(self):
        entry = MemoryEntry(id="l4", memory_type="EPISODIC", content={}, source="t")
        d = entry.to_dict()
        assert d["memory_entry"]["lifecycle_state"] == "NEW"

    def test_lifecycle_updated_at_set(self):
        entry = MemoryEntry(id="l5", memory_type="EPISODIC", content={}, source="t")
        assert "lifecycle_updated_at" in entry.provenance

    def test_multiple_transitions_chain(self):
        entry = MemoryEntry(id="l6", memory_type="EPISODIC", content={}, source="t")
        for state in ["CLASSIFIED", "VALIDATED", "PROMOTED", "ARCHIVED"]:
            ok, _ = entry.transition_lifecycle(state)
            assert ok is True


# ── SQLite Provider Tests ────────────────────────────────────────────────

class TestSQLiteProvider:
    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmp.name
        self._tmp.close()
        self.provider = SQLiteMemoryProvider(self._db_path)

    def teardown_method(self):
        self.provider.close()
        if os.path.exists(self._db_path):
            os.unlink(self._db_path)

    def make_entry(self, mid="e1", mtype="EPISODIC", source="test",
                   confidence=0.5, content=None):
        return MemoryEntry(
            id=mid, memory_type=mtype,
            content=content or {"text": "test entry"},
            source=source, confidence=confidence,
        )

    def test_save_and_get(self):
        entry = self.make_entry()
        saved_id = self.provider.save(entry)
        assert saved_id == "e1"
        retrieved = self.provider.get("e1")
        assert retrieved is not None
        assert retrieved.id == "e1"
        assert retrieved.memory_type == MemoryType.EPISODIC

    def test_get_nonexistent(self):
        result = self.provider.get("nonexistent")
        assert result is None

    def test_search_by_content(self):
        self.provider.save(self.make_entry("e1", content={"text": "fix bug in parser"}))
        self.provider.save(self.make_entry("e2", content={"text": "deploy to prod"}))
        results = self.provider.search("bug")
        assert len(results) >= 1
        assert any(r.id == "e1" for r in results)

    def test_search_empty(self):
        self.provider.save(self.make_entry("e1"))
        results = self.provider.search("zzzzzzzz")
        assert len(results) == 0

    def test_list_by_type(self):
        self.provider.save(self.make_entry("e1", mtype="EPISODIC"))
        self.provider.save(self.make_entry("e2", mtype="SEMANTIC"))
        episodics = self.provider.list_by_type("EPISODIC")
        assert len(episodics) == 1
        assert episodics[0].id == "e1"

    def test_list_by_type_empty(self):
        results = self.provider.list_by_type("DECISION")
        assert results == []

    def test_list_entries(self):
        self.provider.save(self.make_entry("e1"))
        self.provider.save(self.make_entry("e2"))
        entries = self.provider.list_entries()
        assert len(entries) == 2

    def test_list_entries_empty(self):
        entries = self.provider.list_entries()
        assert entries == []

    def test_update_lifecycle(self):
        self.provider.save(self.make_entry("e1"))
        ok = self.provider.update("e1", {"lifecycle_state": "CLASSIFIED",
                                          "lifecycle_updated_at": "2026-01-01T00:00:00"})
        assert ok is True
        retrieved = self.provider.get("e1")
        assert retrieved.provenance["lifecycle_state"] == "CLASSIFIED"

    def test_update_nonexistent(self):
        ok = self.provider.update("no_such_id", {"lifecycle_state": "ARCHIVED"})
        assert ok is False

    def test_update_confidence(self):
        self.provider.save(self.make_entry("e1", confidence=0.5))
        ok = self.provider.update("e1", {"confidence": 0.9})
        assert ok is True
        retrieved = self.provider.get("e1")
        assert retrieved.confidence == 0.9

    def test_persistence_across_reopen(self):
        entry = self.make_entry("persist1")
        self.provider.save(entry)
        self.provider.close()
        provider2 = SQLiteMemoryProvider(self._db_path)
        retrieved = provider2.get("persist1")
        assert retrieved is not None
        assert retrieved.id == "persist1"
        provider2.close()

    def test_save_with_importance(self):
        entry = self.make_entry("imp1")
        imp = MemoryImportanceScore(frequency=0.5, success_impact=0.8)
        imp.compute_total()
        entry.importance = imp
        saved_id = self.provider.save(entry)
        assert saved_id == "imp1"
        retrieved = self.provider.get("imp1")
        assert retrieved.importance is not None
        assert retrieved.importance.frequency == 0.5

    def test_save_with_references(self):
        entry = self.make_entry("ref1")
        entry.references = ["r1", "r2"]
        self.provider.save(entry)
        retrieved = self.provider.get("ref1")
        assert len(retrieved.references) == 2

    def test_save_with_provenance(self):
        entry = self.make_entry("prov1")
        entry.provenance["verified"] = True
        self.provider.save(entry)
        retrieved = self.provider.get("prov1")
        assert retrieved.provenance["verified"] is True

    def test_count(self):
        assert self.provider.count() == 0
        self.provider.save(self.make_entry("c1"))
        self.provider.save(self.make_entry("c2"))
        assert self.provider.count() == 2

    def test_save_entry_alias(self):
        entry = self.make_entry("alias1")
        self.provider.save_entry(entry)
        assert self.provider.get("alias1") is not None

    def test_replaces_existing(self):
        self.provider.save(self.make_entry("dup", content={"text": "first"}))
        self.provider.save(self.make_entry("dup", content={"text": "second"}))
        retrieved = self.provider.get("dup")
        assert retrieved.content["text"] == "second"


# ── Lifecycle + Store Integration Tests ─────────────────────────────────

class TestLifecycleStore:
    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmp.name
        self._tmp.close()
        self.provider = SQLiteMemoryProvider(self._db_path)

    def teardown_method(self):
        self.provider.close()
        if os.path.exists(self._db_path):
            os.unlink(self._db_path)

    def make_entry(self, mid="s1"):
        return MemoryEntry(
            id=mid, memory_type="EPISODIC",
            content={"text": "test"}, source="t",
        )

    def test_save_and_retrieve_lifecycle(self):
        entry = self.make_entry()
        self.provider.save(entry)
        retrieved = self.provider.get("s1")
        assert retrieved.lifecycle_state == "NEW"

    def test_transition_and_persist(self):
        entry = self.make_entry("s2")
        entry.transition_lifecycle("CLASSIFIED")
        self.provider.save(entry)
        retrieved = self.provider.get("s2")
        assert retrieved.lifecycle_state == "CLASSIFIED"

    def test_full_lifecycle_persisted(self):
        entry = self.make_entry("s3")
        entry.transition_lifecycle("CLASSIFIED")
        self.provider.save(entry)
        entry.transition_lifecycle("VALIDATED")
        self.provider.save(entry)
        entry.transition_lifecycle("PROMOTED")
        self.provider.save(entry)
        retrieved = self.provider.get("s3")
        assert retrieved.lifecycle_state == "PROMOTED"

    def test_archived_state_persisted(self):
        entry = self.make_entry("s4")
        entry.transition_lifecycle("CLASSIFIED")
        entry.transition_lifecycle("VALIDATED")
        entry.transition_lifecycle("ARCHIVED")
        self.provider.save(entry)
        retrieved = self.provider.get("s4")
        assert retrieved.lifecycle_state == "ARCHIVED"


# ── Event Listener Tests ─────────────────────────────────────────────────

class TestEventListener:
    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmp.name
        self._tmp.close()
        self.store = SQLiteMemoryProvider(self._db_path)
        self.fabric = MemoryFabric(store_provider=self.store)
        self.listener = EventListener(self.fabric)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self._db_path):
            os.unlink(self._db_path)

    def test_listen_topics(self):
        assert "runtime.execution.completed" in EventListener.LISTEN_TOPICS
        assert "runtime.execution.failed" in EventListener.LISTEN_TOPICS
        assert "knowledge.candidate.created" in EventListener.LISTEN_TOPICS

    def test_process_execution_completed_event(self):
        event = {"topic": "runtime.execution.completed",
                 "payload": {"result": "ok", "status": "completed"}}
        stored = self.listener.process_event(event)
        assert len(stored) >= 1

    def test_process_ignored_topic(self):
        event = {"topic": "some.unknown.event", "payload": {}}
        stored = self.listener.process_event(event)
        assert stored == []

    def test_process_knowledge_created_event(self):
        event = {"topic": "knowledge.candidate.created",
                 "payload": {"id": "k1", "problem": "bug", "solution": "fix"}}
        stored = self.listener.process_event(event)
        assert len(stored) >= 1

    def test_process_kernel_intent_event(self):
        event = {"topic": "kernel.intent.created",
                 "payload": {"goal": "implement feature"}}
        stored = self.listener.process_event(event)
        assert len(stored) >= 1

    def test_process_batch(self):
        events = [
            {"topic": "runtime.execution.completed", "payload": {"r": "ok"}},
            {"topic": "ignored", "payload": {}},
            {"topic": "runtime.execution.failed", "payload": {"error": "timeout"}},
        ]
        stored = self.listener.process_event_batch(events)
        assert len(stored) >= 2

    def test_event_results_persisted(self):
        event = {"topic": "runtime.execution.completed",
                 "payload": {"result": "persist_me"}}
        self.listener.process_event(event)
        entries = self.store.list_entries()
        assert len(entries) >= 1

    def test_event_results_have_classified_lifecycle(self):
        event = {"topic": "runtime.execution.completed",
                 "payload": {"result": "ok"}}
        stored = self.listener.process_event(event)
        for entry in stored:
            assert entry.lifecycle_state in ("NEW", "CLASSIFIED")


# ── Consolidator Integration Tests ───────────────────────────────────────

class TestConsolidatorIntegration:
    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmp.name
        self._tmp.close()
        self.store = SQLiteMemoryProvider(self._db_path)
        self.fabric = MemoryFabric(store_provider=self.store)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self._db_path):
            os.unlink(self._db_path)

    def make_entry(self, mid="c1", mtype="EPISODIC", confidence=0.8):
        return MemoryEntry(
            id=mid, memory_type=mtype,
            content={"status": "passed", "result": "success"},
            source="test", confidence=confidence,
        )

    def test_persist_entry(self):
        entry = self.make_entry()
        saved_id = self.fabric.persist(entry)
        assert saved_id == "c1"
        assert self.store.count() == 1

    def test_validate_memory_valid(self):
        entry = self.make_entry()
        entry.transition_lifecycle("CLASSIFIED")
        self.fabric.persist(entry)
        result, reasons = self.fabric.validate_memory(entry)
        assert result is not None
        assert len(reasons) == 0

    def test_validate_memory_invalid(self):
        entry = MemoryEntry(id="bad", memory_type="EPISODIC",
                            content={"r": "ok"}, source="t")
        entry.id = ""
        is_valid, reasons = self.fabric._consolidator.validate_entry(entry)
        assert is_valid is False

    def test_archive_memory(self):
        entry = self.make_entry()
        entry.transition_lifecycle("CLASSIFIED")
        entry.transition_lifecycle("VALIDATED")
        result = self.fabric.archive_memory(entry)
        assert result is not None
        assert result.lifecycle_state == "ARCHIVED"

    def test_archive_memory_invalid_transition(self):
        entry = self.make_entry()
        result = self.fabric.archive_memory(entry)
        assert result is None

    def test_promote_memory(self):
        entry = self.make_entry()
        entry.transition_lifecycle("CLASSIFIED")
        entry.transition_lifecycle("VALIDATED")
        imp = MemoryImportanceScore(frequency=1.0, success_impact=1.0, recency=1.0,
                                     confidence=1.0, future_usefulness=1.0, verification_level=1.0)
        imp.compute_total()
        entry.importance = imp
        result = self.fabric.promote(entry)
        assert result is not None
        assert result.lifecycle_state == "PROMOTED"

    def test_promoted_persisted(self):
        entry = self.make_entry()
        entry.transition_lifecycle("CLASSIFIED")
        entry.transition_lifecycle("VALIDATED")
        imp = MemoryImportanceScore(frequency=1.0, success_impact=1.0, recency=1.0,
                                     confidence=1.0, future_usefulness=1.0, verification_level=1.0)
        imp.compute_total()
        entry.importance = imp
        self.fabric.promote(entry)
        self.fabric.persist(entry)
        retrieved = self.store.get(entry.id)
        assert retrieved.lifecycle_state == "PROMOTED"

    def test_validate_memory_updates_provenance(self):
        entry = self.make_entry()
        entry.transition_lifecycle("CLASSIFIED")
        result, _ = self.fabric.validate_memory(entry)
        assert result is not None
        assert "validation_timestamp" in result.provenance

    def test_validate_memory_without_classified(self):
        entry = self.make_entry()
        result, _ = self.fabric.validate_memory(entry)
        assert result is not None

    def test_consolidate_persists_entries(self):
        from features.memory_fabric.consolidator import MemoryConsolidator
        con = MemoryConsolidator()
        entries = con.consolidate("test", {"status": "completed"},
                                  store_provider=self.store)
        assert len(entries) >= 1
        assert self.store.count() >= 1


# ── Fabric Persistence Integration ───────────────────────────────────────

class TestFabricPersistence:
    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmp.name
        self._tmp.close()
        self.store = SQLiteMemoryProvider(self._db_path)
        self.fabric = MemoryFabric(store_provider=self.store)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self._db_path):
            os.unlink(self._db_path)

    def make_entry(self, mid="f1"):
        return MemoryEntry(
            id=mid, memory_type="EPISODIC",
            content={"text": "integration test"}, source="test",
        )

    def test_classify_and_persist(self):
        entries = self.fabric.classify("test", {"execution": "completed"})
        for e in entries:
            self.fabric.persist(e)
        assert self.store.count() >= 1

    def test_consolidate_and_persist(self):
        entries = self.fabric.consolidate("test", {"status": "completed"})
        for e in entries:
            self.fabric.persist(e)
        assert self.store.count() >= 1

    def test_retrieve_from_persisted(self):
        e = self.make_entry()
        self.fabric.persist(e)
        ctx = self.fabric.retrieve_context(task={"objective": "integration"})
        assert ctx.execution_id == ""

    def test_event_listener_with_real_db(self):
        listener = EventListener(self.fabric)
        event = {"topic": "runtime.execution.completed",
                 "payload": {"result": "db_test"}}
        stored = listener.process_event(event)
        assert len(stored) >= 1
        assert self.store.count() >= 1
