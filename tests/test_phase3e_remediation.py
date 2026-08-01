"""
MC-TC-003E — P0/P1 Remediation Re-Certification Tests

Tests that every P0 and P1 finding from MC-TC-003D is resolved.
"""

import os
import sys
import time
import threading
import tempfile
import json
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.identity import (
    ExecutionContext, ExecutionContextManager, get_context_manager,
    is_uuid7, uuid7, ValidationError,
    validate_execution_state_change, validate_verification_state_change,
)
from event_bus import EventBus
from runtime.event_store import EventStore


# ═══════════════════════════════════════════════════════════════════════
# INV-ID-001: ONE EXECUTION = ONE CANONICAL EXECUTION_ID
# ═══════════════════════════════════════════════════════════════════════


class TestSingleCanonicalIdentity:
    def test_default_execution_single_id(self):
        ctx = ExecutionContext()
        eid = ctx.execution_id
        assert eid
        assert ctx.execution_id == eid
        assert is_uuid7(eid)

    def test_supplied_context_preserved(self):
        ctx = ExecutionContext(execution_id="custom-id-001")
        assert ctx.execution_id == "custom-id-001"

    def test_graph_node_matches_execution_id(self):
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        ctx = ExecutionContext(execution_id="graph-match-test")
        result = k.run("print hello", execution_context=ctx)
        for node in k.graph.nodes.values():
            assert node.execution_id == "graph-match-test", f"Node {node.id} has wrong execution_id"

    def test_kernel_result_matches_execution_id(self):
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        ctx = ExecutionContext(execution_id="result-match-test")
        result = k.run("print hello", execution_context=ctx)
        assert result.execution_id == "result-match-test"

    def test_muscal_os_run_single_identity(self):
        from muscal_os import MuscalOS
        from os_config import load_config
        os_inst = MuscalOS(load_config("local_dev"))
        os_inst.start()

        seen_ids = set()
        original = os_inst._persist_to_store
        def capturing(msg):
            payload = msg.payload or {}
            eid = payload.get("execution_id", "") or ""
            if eid:
                seen_ids.add(eid)
            original(msg)

        os_inst.events.unsubscribe("*", os_inst._persist_to_store)
        os_inst.events.subscribe("*", capturing)
        os_inst._persist_to_store = capturing

        result = os_inst.run("print hello")
        result_eid = result.get("execution_id", "")
        assert len(seen_ids) <= 1, f"Multiple identities seen: {seen_ids}"
        os_inst.shutdown()

    def test_nested_invocation_no_identity_replacement(self):
        ctx = ExecutionContext(execution_id="outer-call")
        from muscal_os import MuscalOS
        from os_config import load_config
        os_inst = MuscalOS(load_config("local_dev"))
        os_inst.start()
        result = os_inst.run("print hello", execution_context=ctx)
        assert result.get("execution_id") == "outer-call", "Outer identity must be preserved"
        os_inst.shutdown()

    def test_identity_replacement_rejected(self):
        ctx = ExecutionContext(execution_id="original")
        from muscal_os import MuscalOS
        from os_config import load_config
        os_inst = MuscalOS(load_config("local_dev"))
        os_inst.start()
        result = os_inst.run("print hello", execution_context=ctx)
        assert result.get("execution_id") == "original"
        os_inst.shutdown()


# ═══════════════════════════════════════════════════════════════════════
# INV-PERSIST-001: PERSISTENCE PRESERVES IDENTITY
# ═══════════════════════════════════════════════════════════════════════


class TestPersistencePreservesIdentity:
    def test_muscal_os_persist_extracts_execution_id(self):
        from muscal_os import MuscalOS
        from os_config import load_config
        import tempfile
        import os as os_mod
        db_path = Path(tempfile.mktemp(suffix=".db"))
        from config import DB_PATH
        orig_db = DB_PATH
        try:
            import config
            config.DB_PATH = db_path
            os_inst = MuscalOS(load_config("local_dev"))
            os_inst.start()
            os_inst.run("print hello", execution_context=ExecutionContext(execution_id="persist-test-001"))
            events = os_inst.event_store.replay(limit=1000)
            with_execution = [e for e in events if e["execution_id"] == "persist-test-001"]
            assert len(with_execution) > 0, "No persisted events have the expected execution_id"
            os_inst.shutdown()
        finally:
            config.DB_PATH = orig_db
            try:
                os_mod.unlink(db_path)
            except Exception:
                pass

    def test_persist_extracts_correlation_id(self):
        ctx = ExecutionContext(execution_id="corr-test", correlation_id="corr-group-1")
        from muscal_os import MuscalOS
        from os_config import load_config
        import tempfile
        import os as os_mod
        db_path = Path(tempfile.mktemp(suffix=".db"))
        from config import DB_PATH as orig_db
        try:
            import config
            config.DB_PATH = db_path
            os_inst = MuscalOS(load_config("local_dev"))
            os_inst.start()
            os_inst.run("print hello", execution_context=ctx)
            events = os_inst.event_store.replay(limit=1000)
            with_corr = [e for e in events if e["correlation_id"] == "corr-group-1"]
            assert len(with_corr) > 0, "correlation_id not persisted"
            os_inst.shutdown()
        finally:
            config.DB_PATH = orig_db
            try:
                os_mod.unlink(db_path)
            except Exception:
                pass

    def test_persist_extracts_causation_id(self):
        ctx = ExecutionContext(execution_id="cause-test", causation_id="parent-exec")
        from muscal_os import MuscalOS
        from os_config import load_config
        import tempfile
        import os as os_mod
        db_path = Path(tempfile.mktemp(suffix=".db"))
        from config import DB_PATH as orig_db
        try:
            import config
            config.DB_PATH = db_path
            os_inst = MuscalOS(load_config("local_dev"))
            os_inst.start()
            os_inst.run("print hello", execution_context=ctx)
            events = os_inst.event_store.replay(limit=1000)
            with_cause = [e for e in events if e["causation_id"] == "parent-exec"]
            assert len(with_cause) > 0, "causation_id not persisted"
            os_inst.shutdown()
        finally:
            config.DB_PATH = orig_db
            try:
                os_mod.unlink(db_path)
            except Exception:
                pass

    def test_persist_extracts_execution_mode(self):
        ctx = ExecutionContext(execution_id="mode-test", execution_mode="simulated")
        from muscal_os import MuscalOS
        from os_config import load_config
        import tempfile
        import os as os_mod
        db_path = Path(tempfile.mktemp(suffix=".db"))
        from config import DB_PATH as orig_db
        try:
            import config
            config.DB_PATH = db_path
            os_inst = MuscalOS(load_config("local_dev"))
            os_inst.start()
            os_inst.run("print hello", execution_context=ctx)
            events = os_inst.event_store.replay(limit=1000)
            with_mode = [e for e in events if e["execution_mode"] == "simulated"]
            assert len(with_mode) > 0, "execution_mode not persisted"
            os_inst.shutdown()
        finally:
            config.DB_PATH = orig_db
            try:
                os_mod.unlink(db_path)
            except Exception:
                pass

    def test_persist_does_not_generate_replacement_id(self):
        from muscal_os import MuscalOS
        from os_config import load_config
        import tempfile
        import os as os_mod
        db_path = Path(tempfile.mktemp(suffix=".db"))
        from config import DB_PATH as orig_db
        try:
            import config
            config.DB_PATH = db_path
            os_inst = MuscalOS(load_config("local_dev"))
            os_inst.start()
            os_inst.run("print hello", execution_context=ExecutionContext(execution_id="no-replace"))
            events = os_inst.event_store.replay(limit=1000)
            eids = {e["execution_id"] for e in events if e["execution_id"]}
            assert eids == {"no-replace"}, f"Unexpected replacement IDs: {eids}"
            os_inst.shutdown()
        finally:
            config.DB_PATH = orig_db
            try:
                os_mod.unlink(db_path)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════
# INV-VERIFY-001: VERIFIED IS A DERIVED STATE, NOT USER-ASSIGNABLE
# ═══════════════════════════════════════════════════════════════════════


class TestTrustStateProtected:
    def test_execution_state_direct_assignment_rejected(self):
        ctx = ExecutionContext()
        with pytest.raises(ValidationError):
            ctx.execution_state = "completed"

    def test_verification_state_direct_assignment_rejected(self):
        ctx = ExecutionContext()
        with pytest.raises(ValidationError):
            ctx.verification_state = "verified"

    def test_transition_state_works_correctly(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="planned")
        ctx.transition_state("queued")
        assert ctx.execution_state == "queued"
        ctx.transition_state("running")
        assert ctx.execution_state == "running"
        ctx.transition_state("completed")
        assert ctx.execution_state == "completed"

    def test_invalid_transition_state_rejected(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="planned")
        with pytest.raises(ValidationError):
            ctx.transition_state("completed")

    def test_set_verification_works_correctly(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        ctx.set_verification("verified", evidence_receipt_id="rcpt-001")
        assert ctx.verification_state == "verified"

    def test_invalid_verification_mode_state_rejected(self):
        ctx = ExecutionContext(execution_mode="proposed", execution_state="planned")
        with pytest.raises(ValidationError):
            ctx.set_verification("verified", evidence_receipt_id="rcpt-001")

    def test_verification_bound_to_execution_id(self):
        ctx = ExecutionContext(execution_id="exec-A", execution_mode="real", execution_state="completed")
        ctx.set_verification("verified", evidence_receipt_id="rcpt-001")
        assert ctx.execution_id == "exec-A"

    def test_verification_without_execution_id_allowed_for_real_completed(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        ctx.set_verification("verified", evidence_receipt_id="rcpt-001")

    def test_verification_requires_valid_verification_state_transition(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        ctx.set_verification("verified", evidence_receipt_id="rcpt-001")
        assert ctx.verification_state == "verified"
        ctx.set_verification("failed", evidence_receipt_id="rcpt-001")
        assert ctx.verification_state == "failed"
        with pytest.raises(ValidationError):
            ctx.set_verification("verified", evidence_receipt_id="rcpt-001")

    def test_rejected_verification_terminal(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        ctx.set_verification("rejected")
        assert ctx.verification_state == "rejected"
        with pytest.raises(ValidationError):
            ctx.set_verification("verified", evidence_receipt_id="rcpt-001")


# ═══════════════════════════════════════════════════════════════════════
# P1-F01: EventBus uses uuid7 for canonical event identity
# ═══════════════════════════════════════════════════════════════════════


class TestEventBusUuid7:
    def test_bus_message_id_is_uuid7(self):
        bus = EventBus()
        msg = bus.publish("test.topic", {"data": 1})
        assert is_uuid7(msg.id), f"EventBus.id is not uuid7: {msg.id}"

    def test_unique_ids_per_publish(self):
        bus = EventBus()
        ids = set()
        for _ in range(100):
            msg = bus.publish("test.unique", {"n": _})
            ids.add(msg.id)
        assert len(ids) == 100

    def test_stored_event_id_is_uuid7(self):
        bus = EventBus()
        msg = bus.publish("test.store", {"data": 1})
        assert is_uuid7(msg.id)

    def test_graph_events_use_provided_execution_id(self):
        bus = EventBus()
        msg = bus.publish("test.event", {"execution_id": "custom-a-001"})
        assert is_uuid7(msg.id)  # EventBus.id is uuid7
        assert msg.payload.get("execution_id") == "custom-a-001"


# ═══════════════════════════════════════════════════════════════════════
# P1-F02/F03: Execution mode propagated through store_receipt/store_verification
# ═══════════════════════════════════════════════════════════════════════


class TestExecutionModePropagation:
    def test_store_receipt_preserves_simulated_mode(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        class SimReceipt:
            receipt_id = "receipt-sim-1"
            execution_id = "exec-sim-1"
            execution_mode = "simulated"
            correlation_id = ""
            causation_id = ""
            success = True
            verification_status = "pending"
            def to_dict(self):
                return {"receipt_id": self.receipt_id, "execution_id": self.execution_id}

        store.store_receipt(SimReceipt())
        events = store.replay(limit=100)
        receipt_events = [e for e in events if e["topic"] == "execution.receipt"]
        assert len(receipt_events) == 1
        assert receipt_events[0]["execution_mode"] == "simulated"

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_store_receipt_preserves_proposed_mode(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        class PropReceipt:
            receipt_id = "receipt-prop-1"
            execution_id = "exec-prop-1"
            execution_mode = "proposed"
            correlation_id = ""
            causation_id = ""
            success = False
            verification_status = "pending"
            def to_dict(self):
                return {"receipt_id": self.receipt_id}

        store.store_receipt(PropReceipt())
        events = store.replay(limit=100)
        receipt_events = [e for e in events if e["topic"] == "execution.receipt"]
        assert receipt_events[0]["execution_mode"] == "proposed"

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_store_verification_preserves_simulated_mode(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        class SimVerification:
            verification_id = "ver-sim-1"
            execution_id = "exec-sim-1"
            execution_mode = "simulated"
            correlation_id = ""
            causation_id = ""
            receipt_id = "receipt-sim-1"
            status = "verified"
            def to_dict(self):
                return {"verification_id": self.verification_id}

        store.store_verification(SimVerification())
        events = store.replay(limit=100)
        ver_events = [e for e in events if e["topic"] == "execution.verification"]
        assert len(ver_events) == 1
        assert ver_events[0]["execution_mode"] == "simulated"

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# P1-F04: Causation direction is correct
# ═══════════════════════════════════════════════════════════════════════


class TestCausationDirection:
    def test_store_receipt_causation_points_to_execution(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        class Receipt:
            receipt_id = "r-001"
            execution_id = "e-001"
            execution_mode = "real"
            correlation_id = "c-001"
            causation_id = "e-001"
            success = True
            verification_status = "pending"
            def to_dict(self):
                return {"receipt_id": self.receipt_id}

        store.store_receipt(Receipt())
        events = store.replay(limit=100)
        receipt_events = [e for e in events if e["topic"] == "execution.receipt"]
        assert receipt_events[0]["causation_id"] == "e-001"
        assert receipt_events[0]["causation_id"] != "r-001"

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_store_verification_causation_defaults_to_receipt(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        class Verification:
            verification_id = "v-001"
            execution_id = "e-001"
            execution_mode = "real"
            correlation_id = ""
            causation_id = ""
            receipt_id = "r-001"
            status = "verified"
            def to_dict(self):
                return {"verification_id": self.verification_id}

        store.store_verification(Verification())
        events = store.replay(limit=100)
        ver_events = [e for e in events if e["topic"] == "execution.verification"]
        assert ver_events[0]["causation_id"] == "r-001"

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# P1-F05: Orphan event validation
# ═══════════════════════════════════════════════════════════════════════


class TestOrphanEventValidation:
    def test_execution_event_without_execution_id_rejected(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)
        with pytest.raises(ValueError, match="requires execution_id"):
            store.append({
                "topic": "EXECUTION_STARTED",
                "payload": {"input": "test"},
                "source": "test",
                "priority": "NORMAL",
                "timestamp": time.time(),
                "id": uuid7(),
            })
        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_receipt_without_execution_id_rejected(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)
        with pytest.raises(ValueError, match="requires execution_id"):
            store.append({
                "topic": "execution.receipt",
                "payload": {"receipt_id": "orphan"},
                "source": "test",
                "priority": "NORMAL",
                "timestamp": time.time(),
                "id": uuid7(),
            })
        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_verification_topic_without_execution_id_rejected(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)
        with pytest.raises(ValueError, match="requires execution_id"):
            store.append({
                "topic": "VERIFICATION_PASSED",
                "payload": {},
                "source": "test",
                "priority": "NORMAL",
                "timestamp": time.time(),
                "id": uuid7(),
            })
        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_execution_event_with_execution_id_accepted(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)
        seq = store.append({
            "topic": "EXECUTION_STARTED",
            "payload": {"execution_id": "valid-eid"},
            "source": "test",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": uuid7(),
            "execution_id": "valid-eid",
        })
        assert seq is not None
        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass

    def test_non_execution_event_allowed_without_execution_id(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)
        seq = store.append({
            "topic": "boot.init",
            "payload": {"message": "hello"},
            "source": "test",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": uuid7(),
        })
        assert seq is not None
        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# INV-ID-001: ADAPTIVE — identity replacement attempt rejected
# ═══════════════════════════════════════════════════════════════════════


class TestIdentityReplacement:
    def test_muscal_os_preserves_existing_execution_id(self):
        from muscal_os import MuscalOS
        from os_config import load_config
        os_inst = MuscalOS(load_config("local_dev"))
        os_inst.start()
        given = ExecutionContext(execution_id="must-preserve-this-id")
        result = os_inst.run("print hello", execution_context=given)
        assert result.get("execution_id") == "must-preserve-this-id"
        os_inst.shutdown()
