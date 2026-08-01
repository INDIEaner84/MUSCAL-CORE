"""
MC-TC-003B — Trust Core Identity + Execution State Implementation Tests

Tests the approved Trust Core contracts:
  - Canonical execution identity
  - Event identity
  - Execution state machine (3D: mode x state x verification)
  - Claim vs execution semantics
  - Legacy simulation_mode mapping
"""

import os
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.identity import (
    ExecutionContext, ExecutionContextManager, get_context_manager,
    ContextLifecycle,
    ExecutionMode, ExecutionState, VerificationState,
    validate_state_transition, validate_execution_state_change,
    validate_verification_state_change,
    verify_execution_state_change, verify_verification_state_change,
    ValidationError,
    uuid7, is_uuid7,
    map_simulation_mode, map_execution_mode_to_simulation,
)
from event_bus import EventBus, EventMessage, EventPriority


# ═══════════════════════════════════════════════════════════════════════
# A. Canonical Identity Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCanonicalIdentity:
    def test_execution_id_generated_once(self):
        ctx = ExecutionContext()
        eid = ctx.execution_id
        assert is_uuid7(eid)
        assert ctx.execution_id == eid

    def test_execution_id_immutable(self):
        ctx = ExecutionContext(execution_id="fixed-id")
        assert ctx.execution_id == "fixed-id"

    def test_uuid7_uniqueness(self):
        ids = set()
        for _ in range(1000):
            eid = uuid7()
            assert eid not in ids
            ids.add(eid)

    def test_correlation_id_groups_executions(self):
        group_id = uuid7()
        ctx1 = ExecutionContext(correlation_id=group_id)
        ctx2 = ExecutionContext(correlation_id=group_id)
        assert ctx1.correlation_id == ctx2.correlation_id
        assert ctx1.execution_id != ctx2.execution_id

    def test_causation_id_links_parent_child(self):
        parent = ExecutionContext()
        child = ExecutionContext(causation_id=parent.execution_id)
        assert child.causation_id == parent.execution_id


# ═══════════════════════════════════════════════════════════════════════
# B. Execution Context Lifecycle Tests
# ═══════════════════════════════════════════════════════════════════════


class TestExecutionContextLifecycle:
    def test_lifecycle_created_to_active(self):
        ctx = ExecutionContext()
        assert ctx.lifecycle == "created"
        ctx.transition_lifecycle(ContextLifecycle.ACTIVE)
        assert ctx.lifecycle == "active"

    def test_lifecycle_active_to_completed(self):
        ctx = ExecutionContext()
        ctx.transition_lifecycle(ContextLifecycle.ACTIVE)
        ctx.transition_lifecycle(ContextLifecycle.COMPLETED)
        assert ctx.lifecycle == "completed"

    def test_lifecycle_active_to_failed(self):
        ctx = ExecutionContext()
        ctx.transition_lifecycle(ContextLifecycle.ACTIVE)
        ctx.transition_lifecycle(ContextLifecycle.FAILED)
        assert ctx.lifecycle == "failed"

    def test_lifecycle_created_to_cancelled(self):
        ctx = ExecutionContext()
        ctx.transition_lifecycle(ContextLifecycle.CANCELLED)
        assert ctx.lifecycle == "cancelled"

    def test_lifecycle_invalid_transition_raises(self):
        ctx = ExecutionContext()
        with pytest.raises(ValidationError):
            ctx.transition_lifecycle(ContextLifecycle.COMPLETED)

    def test_lifecycle_terminal_cannot_transition(self):
        ctx = ExecutionContext()
        ctx.transition_lifecycle(ContextLifecycle.ACTIVE)
        ctx.transition_lifecycle(ContextLifecycle.COMPLETED)
        with pytest.raises(ValidationError):
            ctx.transition_lifecycle(ContextLifecycle.ACTIVE)


# ═══════════════════════════════════════════════════════════════════════
# C. Execution State Transition Tests
# ═══════════════════════════════════════════════════════════════════════


class TestExecutionStateTransitions:
    def test_valid_planned_to_queued(self):
        assert validate_execution_state_change("planned", "queued")

    def test_valid_queued_to_running(self):
        assert validate_execution_state_change("queued", "running")

    def test_valid_running_to_completed(self):
        assert validate_execution_state_change("running", "completed")

    def test_valid_running_to_failed(self):
        assert validate_execution_state_change("running", "failed")

    def test_valid_failed_to_queued_retry(self):
        assert validate_execution_state_change("failed", "queued")

    def test_invalid_planned_to_completed(self):
        assert not validate_execution_state_change("planned", "completed")

    def test_invalid_completed_to_running(self):
        assert not validate_execution_state_change("completed", "running")

    def test_invalid_cancelled_to_queued(self):
        assert not validate_execution_state_change("cancelled", "queued")

    def test_verify_valid_transition_passes(self):
        verify_execution_state_change("running", "completed")

    def test_verify_invalid_transition_raises(self):
        with pytest.raises(ValidationError):
            verify_execution_state_change("completed", "running")


# ═══════════════════════════════════════════════════════════════════════
# D. Verification State Transition Tests
# ═══════════════════════════════════════════════════════════════════════


class TestVerificationStateTransitions:
    def test_unverified_to_verified(self):
        assert validate_verification_state_change("unverified", "verified")

    def test_unverified_to_failed(self):
        assert validate_verification_state_change("unverified", "failed")

    def test_verified_to_failed_external_contradiction(self):
        assert validate_verification_state_change("verified", "failed")

    def test_failed_to_unverified_reverify(self):
        assert validate_verification_state_change("failed", "unverified")

    def test_rejected_is_terminal(self):
        assert not validate_verification_state_change("rejected", "unverified")

    def test_verified_to_unverified_invalid(self):
        assert not validate_verification_state_change("verified", "unverified")


# ═══════════════════════════════════════════════════════════════════════
# E. 3D State Machine (Mode x State x Verification) Tests
# ═══════════════════════════════════════════════════════════════════════


class Test3DStateMachine:
    def test_real_running_unverified_valid(self):
        assert validate_state_transition("real", "running", "unverified")

    def test_real_completed_verified_valid(self):
        assert validate_state_transition("real", "completed", "verified")

    def test_proposed_running_invalid(self):
        assert not validate_state_transition("proposed", "running", "unverified")

    def test_proposed_verified_invalid(self):
        assert not validate_state_transition("proposed", "planned", "verified")

    def test_simulated_completed_verified_valid(self):
        assert validate_state_transition("simulated", "completed", "verified")

    def test_replay_completed_verified_valid(self):
        assert validate_state_transition("replay", "completed", "verified")

    def test_shadow_completed_verified_valid(self):
        assert validate_state_transition("shadow", "completed", "verified")


# ═══════════════════════════════════════════════════════════════════════
# F. Simulation Mode Mapping Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSimulationModeMapping:
    def test_simulation_mode_true_maps_to_simulated(self):
        assert map_simulation_mode(True) == "simulated"

    def test_simulation_mode_false_maps_to_real(self):
        assert map_simulation_mode(False) == "real"

    def test_simulated_maps_back_to_true(self):
        assert map_execution_mode_to_simulation("simulated") is True

    def test_real_maps_back_to_false(self):
        assert map_execution_mode_to_simulation("real") is False

    def test_proposed_maps_to_false(self):
        assert map_execution_mode_to_simulation("proposed") is False

    def test_shadow_maps_to_false(self):
        assert map_execution_mode_to_simulation("shadow") is False

    def test_replay_maps_to_false(self):
        assert map_execution_mode_to_simulation("replay") is False


# ═══════════════════════════════════════════════════════════════════════
# H. ExecutionContext Enrichment Tests
# ═══════════════════════════════════════════════════════════════════════


class TestContextEnrichment:
    def test_enrich_with_execution_id(self):
        ctx = ExecutionContext(execution_id="enrich-1")
        payload = ctx.enrich_payload({"task": "test"})
        assert payload["execution_id"] == "enrich-1"

    def test_enrich_with_all_fields(self):
        ctx = ExecutionContext(
            execution_id="e1",
            correlation_id="c1",
            causation_id="cause-1",
            execution_mode="simulated",
            execution_state="running",
            verification_state="unverified",
            agent_id="agent-1",
            model_id="model-1",
            request_id="req-1",
        )
        payload = ctx.enrich_payload({"task": "test"})
        assert payload["execution_id"] == "e1"
        assert payload["correlation_id"] == "c1"
        assert payload["causation_id"] == "cause-1"
        assert payload["execution_mode"] == "simulated"
        assert payload["agent_id"] == "agent-1"

    def test_context_to_dict_roundtrip(self):
        ctx = ExecutionContext(
            execution_id="roundtrip-1",
            execution_state="running",
            verification_state="unverified",
        )
        d = ctx.to_dict()
        restored = ExecutionContext.extract_from_payload(d)
        assert restored.execution_id == "roundtrip-1"
        assert restored.execution_state == "running"

    def test_context_manager_thread_safe(self):
        mgr = ExecutionContextManager()
        results = {}

        def worker(name):
            ctx = ExecutionContext(execution_id=f"thread-{name}")
            mgr.set_context(ctx)
            time.sleep(0.01)
            results[name] = mgr.get_context().execution_id
            mgr.clear_context()

        threads = [threading.Thread(target=worker, args=("A",)), threading.Thread(target=worker, args=("B",))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert results["A"] == "thread-A"
        assert results["B"] == "thread-B"


# ═══════════════════════════════════════════════════════════════════════
# I. Kernel Identity Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestKernelIdentityIntegration:
    def test_kernel_accepts_execution_context(self):
        from kernel import MuscalKernel
        from features.identity import ExecutionContext

        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        ctx = ExecutionContext(execution_id="kernel-test-1", execution_mode="real")
        result = k.run("print hello", execution_context=ctx)
        assert result.execution_id == "kernel-test-1"

    def test_kernel_generates_default_context(self):
        from kernel import MuscalKernel

        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        result = k.run("print hello")
        assert result.execution_id != ""

    def test_graph_nodes_have_execution_id(self):
        from kernel import MuscalKernel
        from features.identity import ExecutionContext

        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        ctx = ExecutionContext(execution_id="graph-eid-test")
        k.run("print hello", execution_context=ctx)

        for node in k.graph.nodes.values():
            assert node.execution_id == "graph-eid-test", f"Node {node.id} missing execution_id"

    def test_execution_id_in_graph_events(self):
        from kernel import MuscalKernel
        from features.identity import ExecutionContext

        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        ctx = ExecutionContext(execution_id="event-eid-test")
        k.run("print hello", execution_context=ctx)

        event_stream = k.graph.get_event_stream(limit=100)
        execution_events = [e for e in event_stream if e.get("payload", {}).get("execution_id") == "event-eid-test"]
        assert len(execution_events) > 0

    def test_kernel_result_has_execution_id(self):
        from kernel import MuscalKernel

        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        result = k.run("print hello")
        assert result.execution_id != ""
        assert is_uuid7(result.execution_id)


# ═══════════════════════════════════════════════════════════════════════
# J. Execution Context Transition in Context Tests
# ═══════════════════════════════════════════════════════════════════════


class TestContextStateTransitions:
    def test_context_transition_state_valid(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="planned")
        ctx.transition_state("queued")
        assert ctx.execution_state == "queued"

    def test_context_transition_state_invalid(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        with pytest.raises(ValidationError):
            ctx.transition_state("running")

    def test_context_set_verification_valid(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="completed")
        ctx.set_verification("verified", evidence_receipt_id="rcpt-001")
        assert ctx.verification_state == "verified"

    def test_context_set_verification_invalid_for_proposed(self):
        ctx = ExecutionContext(execution_mode="proposed", execution_state="planned")
        with pytest.raises(ValidationError):
            ctx.set_verification("verified", evidence_receipt_id="rcpt-001")

    def test_context_validate_passes(self):
        ctx = ExecutionContext(execution_mode="real", execution_state="running", verification_state="unverified")
        ctx.validate()

    def test_context_validate_raises(self):
        ctx = ExecutionContext(execution_mode="proposed", execution_state="running", verification_state="unverified")
        with pytest.raises(ValidationError):
            ctx.validate()
