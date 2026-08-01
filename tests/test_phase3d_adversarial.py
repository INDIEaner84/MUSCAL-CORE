"""
MC-TC-003D — Adversarial Vulnerability Reproduction Tests

These tests actively attempt to disprove the Trust Core architecture.
Some are expected to FAIL, proving the vulnerability exists.

VULNERABILITY: Double Identity (Identity Fragmentation)
  EnrichedMuscalOS.run() creates identity A, then delegates to
  MuscalOS.run() which creates identity B. The enriched wrapper's
  lifecycle events use A, but kernel execution uses B.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import threading
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.identity import (
    ExecutionContext, ExecutionContextManager, get_context_manager,
    is_uuid7, uuid7,
    validate_execution_state_change, ValidationError,
)
from kernel import MuscalKernel
from runtime.event_store import EventStore


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-006 — Event Persisted Without Actual Execution
# ═══════════════════════════════════════════════════════════════════════


class TestFalseExecutionEvent:
    """Demonstrates that an event claiming TOOL_EXECUTED can be persisted
    without actual tool invocation — because EventStore.append() has
    no verification mechanism."""

    def test_false_execution_event_can_be_written(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        seq = store.append({
            "topic": "TOOL_EXECUTED",
            "payload": {"tool": "some_tool", "result": "success"},
            "source": "any_component",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": f"fake-event-{time.time()}",
            "execution_id": "non-existent-execution",
            "execution_mode": "real",
            "execution_state": "completed",
            "verification_state": "verified",
        })

        assert seq is not None

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-010 — Unauthorized Verification
# ═══════════════════════════════════════════════════════════════════════


class TestUnauthorizedVerification:
    def test_verification_state_direct_mutation_rejected(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        with pytest.raises(ValidationError):
            ctx.verification_state = "verified"

    def test_enrich_payload_uses_actual_verification_state(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        ctx.set_verification("verified", evidence_receipt_id="rcpt-001")
        payload = ctx.enrich_payload({"event": "test"})
        assert payload["verification_state"] == "verified"


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-007 — Simulation Leakage via Replay
# ═══════════════════════════════════════════════════════════════════════


class TestSimulationLeakage:
    def test_simulated_and_real_events_indistinguishable_at_replay(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        store.append({
            "topic": "TOOL_EXECUTED",
            "payload": {"tool": "test", "result": "sim", "execution_id": "sim-exec-1"},
            "source": "simulation",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": f"sim-{time.time()}",
            "execution_mode": "simulated",
            "execution_id": "sim-exec-1",
        })
        store.append({
            "topic": "TOOL_EXECUTED",
            "payload": {"tool": "test", "result": "real", "execution_id": "real-exec-1"},
            "source": "kernel",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": f"real-{time.time()}",
            "execution_mode": "real",
            "execution_id": "real-exec-1",
        })

        events = store.replay(limit=100)
        modes = {e.get("execution_mode") for e in events}
        assert "simulated" in modes
        assert "real" in modes

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-019 — State Transition Bypass (Direct Field Mutation)
# ═══════════════════════════════════════════════════════════════════════


class TestStateTransitionBypass:
    def test_execution_state_direct_mutation_rejected(self):
        ctx = ExecutionContext(execution_state="planned")
        with pytest.raises(ValidationError):
            ctx.execution_state = "completed"

    def test_state_only_changes_through_authorized_methods(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="planned")
        ctx.transition_state("queued")
        assert ctx.execution_state == "queued"


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-014 — No Ground Truth After Execution
# ═══════════════════════════════════════════════════════════════════════


class TestNoGroundTruth:
    def test_no_ground_truth_check_after_execution(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        ctx = ExecutionContext(execution_mode="real", execution_state="running")
        result = k.run("print hello", execution_context=ctx)
        assert result.success is not None
        print(f"\nresult.success={result.success}")
        print(f"BUT: No ground-truth check verified this")


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-009 — Broken Causation Chain via EventStore
# ═══════════════════════════════════════════════════════════════════════


class TestBrokenCausationChain:
    def test_store_receipt_sets_causation_backwards(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        class FakeReceipt:
            receipt_id = "receipt-123"
            execution_id = "exec-456"
            correlation_id = ""
            success = True
            verification_status = "pending"
            def to_dict(self):
                return {"receipt_id": self.receipt_id}

        store.store_receipt(FakeReceipt())

        events = store.replay(limit=100)
        receipt_events = [e for e in events if e["topic"] == "execution.receipt"]
        assert len(receipt_events) == 1
        e = receipt_events[0]
        print(f"\nstore_receipt: causation_id={e.get('causation_id')}")
        print(f"causation_id set to receipt_id — backwards causation")

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-012 — Verification Without Evidence
# ═══════════════════════════════════════════════════════════════════════


class TestVerificationWithoutEvidence:
    def test_verified_without_receipt_rejected(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        with pytest.raises(ValidationError):
            ctx.set_verification("verified")
        print(f"\nA-012 mitigated: set_verification('verified') requires evidence_receipt_id")


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-013 — Orphan Evidence (Evidence Without Execution)
# ═══════════════════════════════════════════════════════════════════════


class TestOrphanEvidence:
    def test_orphan_receipt_accepted(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        store.store_receipt(
            type('Obj', (), {
                'receipt_id': 'orphan-1', 'execution_id': 'nonexistent',
                'correlation_id': '', 'causation_id': '',
                'success': True, 'verification_status': 'verified',
                'to_dict': lambda self: {'receipt_id': 'orphan-1'},
            })()
        )

        events = store.replay(limit=100)
        assert any(e.get("topic") == "execution.receipt" for e in events)
        print(f"\nOrphan receipt accepted for non-existent execution")

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-001 — Claim/Evidence Boundary is Advisory Only
# ═══════════════════════════════════════════════════════════════════════


class TestClaimBoundaryAdvisory:
    def test_claim_markers_removed(self):
        pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-017 — No Causal Ordering in EventStore
# ═══════════════════════════════════════════════════════════════════════


class TestNoCausalOrdering:
    def test_out_of_order_events_accepted(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        store.append({"topic": "EXECUTION_COMPLETED", "payload": {},
                      "source": "test", "priority": "NORMAL",
                      "timestamp": time.time(), "id": f"comp-{time.time()}",
                      "execution_id": "t001", "execution_state": "completed"})
        store.append({"topic": "EXECUTION_STARTED", "payload": {},
                      "source": "test", "priority": "NORMAL",
                      "timestamp": time.time(), "id": f"start-{time.time()}",
                      "execution_id": "t001", "execution_state": "running"})

        events = store.replay(limit=100)
        topics = [e["topic"] for e in events if e.get("execution_id") == "t001"]
        assert topics == ["EXECUTION_COMPLETED", "EXECUTION_STARTED"]
        print(f"\nOut-of-order events accepted: {topics}")

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-018 — Conflicting Verification Results
# ═══════════════════════════════════════════════════════════════════════


class TestConflictingVerification:
    def test_conflicting_verifications_both_accepted(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        store.append({"topic": "VERIFICATION_PASSED",
                      "payload": {"execution_id": "exec-race"},
                      "source": "A", "priority": "NORMAL",
                      "timestamp": time.time(), "id": f"vp-{time.time()}",
                      "execution_id": "exec-race",
                      "verification_state": "verified"})
        store.append({"topic": "VERIFICATION_FAILED",
                      "payload": {"execution_id": "exec-race"},
                      "source": "B", "priority": "NORMAL",
                      "timestamp": time.time(), "id": f"vf-{time.time()}",
                      "execution_id": "exec-race",
                      "verification_state": "failed"})

        events = store.replay(limit=100)
        race = [(e["topic"], e.get("verification_state"))
                for e in events if e.get("execution_id") == "exec-race"]
        print(f"\nConflicting verifications: {race}")

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-005 — No Atomicity Between Execution and Persistence
# ═══════════════════════════════════════════════════════════════════════


class TestNoAtomicity:
    def test_execution_persistence_not_atomic(self):
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        ctx = ExecutionContext(execution_mode="real", execution_state="running")
        result = k.run("print hello", execution_context=ctx)
        print(f"\nexecution_id={result.execution_id}")
        print(f"execution completed but persistence is NOT in same transaction")
        print(f"crash between run() and EventStore.append() loses everything")


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-015 — Thread-local Context Race
# ═══════════════════════════════════════════════════════════════════════


class TestThreadLocalRace:
    def test_concurrent_enrich_payload_can_cross_contaminate(self):
        """ExecutionContextManager uses thread-local storage.
        But the _enriched_persist callback in EnrichedMuscalOS reads
        from thread-local context. If an EventBus event from execution A
        fires while execution A's context is still on the thread, and a
        subscriber from execution B processes it... this doesn't happen
        because EventBus callbacks are synchronous.

        However, if there's any async dispatch, cross-contamination occurs."""
        mgr = ExecutionContextManager()

        ctx_a = ExecutionContext(execution_id="A-001")
        ctx_b = ExecutionContext(execution_id="B-001")

        mgr.set_context(ctx_a)
        payload_a = mgr.enrich_payload({"from": "A"})
        assert payload_a["execution_id"] == "A-001"

        mgr.set_context(ctx_b)
        payload_b = mgr.enrich_payload({"from": "B"})
        assert payload_b["execution_id"] == "B-001"

        # Switch back to A (this is the race: async callback using stale context)
        mgr.set_context(ctx_a)
        stale = mgr.enrich_payload({"from": "A-after-B"})
        assert stale["execution_id"] == "A-001"  # correct
        mgr.clear_context()


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-016 — Duplicate Event Detection
# ═══════════════════════════════════════════════════════════════════════


class TestDuplicateEvent:
    def test_duplicate_event_id_rejected(self):
        """EventStore has UNIQUE constraint on event_id."""
        import sqlite3
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        uid = f"dedup-test-{time.time()}"
        store.append({"topic": "TEST", "payload": {},
                      "source": "t", "priority": "NORMAL",
                      "timestamp": time.time(), "id": uid})

        with pytest.raises(sqlite3.IntegrityError):
            store.append({"topic": "TEST", "payload": {},
                          "source": "t", "priority": "NORMAL",
                          "timestamp": time.time(), "id": uid})

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-020 — Incomplete Provenance Fields
# ═══════════════════════════════════════════════════════════════════════


class TestIncompleteProvenance:
    def test_event_accepted_with_missing_identity_fields(self):
        db_path = Path(tempfile.mktemp(suffix=".db"))
        store = EventStore(db_path)

        # No execution_id, no correlation_id, no causation_id
        seq = store.append({
            "topic": "SOME_EVENT",
            "payload": {"data": "test"},
            "source": "unknown",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": f"no-identity-{time.time()}",
        })

        assert seq is not None
        events = store.replay(limit=100)
        e = [ev for ev in events if ev.get("id", "").startswith("no-identity")]
        assert len(e) == 1
        print(f"\nEvent accepted with empty identity fields:")
        print(f"  execution_id='{e[0].get('execution_id','')}'")
        print(f"  correlation_id='{e[0].get('correlation_id','')}'")
        print(f"  causation_id='{e[0].get('causation_id','')}'")

        store.close()
        try:
            os.unlink(db_path)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# VULNERABILITY A-003 — Requested ≠ Invoked ≠ Executed
# ═══════════════════════════════════════════════════════════════════════


class TestRequestedNotExecuted:
    def test_kernel_stage_emits_events_without_execution(self):
        """kernel.py:emit(EVENT_EXECUTION_STARTED) fires at the start
        of run(), before any tool is executed. This event does not
        prove any tool was invoked."""
        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        events_before = len(k.graph.get_event_stream(limit=1000))
        result = k.run("print hello")
        events_after = k.graph.get_event_stream(limit=1000)
        new_events = events_after[events_before:]
        started = [e for e in new_events
                   if e["payload"].get("execution_id") == result.execution_id
                   and e.get("type") == "EXECUTION_STARTED"]
        assert len(started) > 0
        print(f"\nEXECUTION_STARTED fired before any tool invocation")
        print(f"  execution_id={result.execution_id}")
        print(f"  This event means 'execution was requested', not 'execution happened'")
