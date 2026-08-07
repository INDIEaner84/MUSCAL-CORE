import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.reality_sync import (  # noqa: E402
    ChangeEvidence,
    DriftDetector,
    DriftReport,
    InvalidStateError,
    ProposalEngine,
    RealitySynchronizer,
    RiskClassifier,
    RiskLevel,
    UpdateProposal,
)


def make_state(**over):
    state = {
        "entities": {
            "e:1": {"type": "doc", "status": "active", "object_id": "e:1"},
        },
        "graph_nodes": {"n:1": {"id": "n:1", "object_id": "n:1"}},
        "active_tasks": {},
        "agents": {},
        "timestamp": 1.0,
    }
    state.update(over)
    return state


HONEST_CANONICAL = make_state()


class TestNoDrift:
    def test_identical_state_produces_no_drift(self):
        detector = DriftDetector()
        report = detector.detect(make_state(), make_state())
        assert report.has_drift is False
        assert report.differences == []
        assert report.risk_level == RiskLevel.LOW


class TestDriftDetection:
    def test_changed_state_produces_drift(self):
        runtime = make_state()
        runtime["entities"]["e:1"] = {
            "type": "doc",
            "status": "archived",
            "object_id": "e:1",
        }
        report = DriftDetector().detect(runtime, make_state())
        assert report.has_drift is True
        assert len(report.differences) >= 1
        assert report.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH)

    def test_removed_object_produces_removed_difference(self):
        runtime = make_state()
        canonical = make_state()
        canonical["entities"]["e:2"] = {"type": "doc", "object_id": "e:2"}
        report = DriftDetector().detect(runtime, canonical)
        assert report.has_drift is True
        change_types = {d.change_type for d in report.differences}
        assert "removed" in change_types


class TestRiskClassification:
    def test_low_risk_auto_classified(self):
        runtime = make_state()
        runtime["entities"]["metrics:lat"] = {"p95": 120, "stats": "ok"}
        report = DriftDetector().detect(runtime, make_state())
        assert report.risk_level == RiskLevel.LOW
        assert report.recommended_action == "auto_sync"

    def test_high_risk_approval_required(self):
        runtime = make_state()
        runtime["entities"]["security:api-gateway"] = {"auth": "broken"}
        report = DriftDetector().detect(runtime, make_state())
        assert report.risk_level == RiskLevel.HIGH
        proposal = ProposalEngine().build(report)
        assert proposal.approval_required is True

    def test_medium_risk_classified(self):
        runtime = make_state()
        runtime["entities"]["feature:x"] = {"feature_status": "beta"}
        report = DriftDetector().detect(runtime, make_state())
        assert report.risk_level == RiskLevel.MEDIUM


class TestEvidence:
    def test_evidence_complete(self):
        runtime = make_state()
        runtime["entities"]["security:keyring"] = {"threat": True}
        report = DriftDetector().detect(runtime, make_state())
        evidence = ChangeEvidence(
            source=report.source,
            timestamp=report.timestamp,
            event_reference="evt-0001",
            event_hash=DriftDetector.hash_difference(report.differences[0]),
            comparison_result={"risk_level": report.risk_level.value},
        )
        assert evidence.is_complete() is True
        d = evidence.to_dict()["change_evidence"]
        assert d["source"] == "runtime"
        assert d["event_reference"] != ""
        assert d["event_hash"] != ""
        assert "comparison_result" in d


class TestProposal:
    def test_proposal_created(self):
        runtime = make_state()
        runtime["entities"]["feature:x"] = {"feature_status": "beta"}
        sync = RealitySynchronizer()
        result = sync.evaluate(canonical_state=make_state(), runtime_state=runtime)
        proposal = result["proposal"]["update_proposal"]
        assert proposal["proposal_id"] != ""
        assert proposal["change_type"] == "state.sync"
        assert len(proposal["affected_objects"]) >= 1


class TestInvalidState:
    def test_invalid_state_rejected(self):
        sync = RealitySynchronizer()
        with pytest.raises(InvalidStateError):
            sync.evaluate(canonical_state={"no", "required", "keys"}, runtime_state=make_state())

    def test_missing_section_rejected(self):
        detector = DriftDetector()
        with pytest.raises(InvalidStateError):
            detector.detect(make_state(), {"entities": {}})  # fehlt graph_nodes etc.


class TestProposalEngineNoWrites:
    def test_proposal_engine_returns_object_only(self):
        runtime = make_state()
        runtime["entities"]["security:x"] = {"auth": False}
        report = DriftDetector().detect(runtime, make_state())
        proposal = ProposalEngine().build(report, change_type="state.sync")
        assert isinstance(proposal, UpdateProposal)
        assert proposal.affected_objects == ["security:x"]