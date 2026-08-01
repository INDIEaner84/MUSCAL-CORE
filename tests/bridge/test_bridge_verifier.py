from __future__ import annotations

from features.verification.bridge_verifier import (
    BridgeVerifier,
    BridgeVerificationReport,
    BridgeVerificationFinding,
    VERIFICATION_EVIDENCE_CATEGORIES,
)


class TestBridgeVerifier:

    def _success_result(self) -> dict:
        return {
            "execution": {
                "return_code": 0,
                "duration": 2.5,
                "session_reference": "ses_001",
            },
            "facts": {
                "verified": [
                    {"statement": "Execution completed", "evidence": "rc=0", "source": "test"},
                ],
            },
            "observations": {"extracted": []},
            "interpretations": {"inferred": []},
            "hypotheses": {"proposed": []},
            "unknowns": [],
        }

    def _failed_result(self) -> dict:
        return {
            "execution": {
                "return_code": 1,
                "duration": 5.0,
                "session_reference": "ses_002",
            },
            "facts": {"verified": []},
            "observations": {"extracted": []},
            "interpretations": {"inferred": []},
            "hypotheses": {"proposed": []},
            "unknowns": ["Something went wrong"],
        }

    def test_verification_passes_for_successful_execution(self):
        verifier = BridgeVerifier()
        report = verifier.verify_bridge_result(self._success_result())
        assert report.status == "passed"

    def test_verification_fails_for_failed_execution(self):
        verifier = BridgeVerifier()
        report = verifier.verify_bridge_result(self._failed_result())
        assert report.status == "failed"

    def test_verification_captures_return_code_fact(self):
        verifier = BridgeVerifier()
        report = verifier.verify_bridge_result(self._success_result())
        facts = [f for f in report.facts if "exit code 0" in f.statement]
        assert len(facts) >= 1

    def test_verification_captures_risks_for_long_duration(self):
        result = self._success_result()
        result["execution"]["duration"] = 400
        verifier = BridgeVerifier()
        report = verifier.verify_bridge_result(result)
        risks = [r for r in report.risks if "5 minutes" in r.statement]
        assert len(risks) >= 1

    def test_verification_reports_missing_evidence(self):
        result = {"execution": {}, "facts": {"verified": []}, "unknowns": []}
        verifier = BridgeVerifier()
        report = verifier.verify_bridge_result(result)
        assert len(report.evidence_missing) >= 1

    def test_verification_detects_missing_facts(self):
        result = self._success_result()
        result["facts"]["verified"] = []
        verifier = BridgeVerifier()
        report = verifier.verify_bridge_result(result)
        findings = [f for f in report.verification_findings if "No verified facts" in f.statement]
        assert len(findings) >= 1

    def test_verification_with_expected_state(self):
        verifier = BridgeVerifier()
        result = self._success_result()
        report = verifier.verify_bridge_result(
            result,
            expected={"execution.return_code": 0},
        )
        assert report.status == "passed"

    def test_verification_fails_on_expected_state_mismatch(self):
        verifier = BridgeVerifier()
        result = self._success_result()
        report = verifier.verify_bridge_result(
            result,
            expected={"execution.return_code": 99},
        )
        assert report.status == "failed"

    def test_verification_report_to_dict(self):
        report = BridgeVerificationReport(status="passed")
        report.add_finding(BridgeVerificationFinding(
            category="fact",
            statement="test fact",
            evidence="evidence",
            source="test",
        ))
        d = report.to_dict()
        assert d["verification"]["status"] == "passed"
        assert len(d["verification"]["facts"]) == 1

    def test_invalid_category_raises(self):
        import pytest
        finding = BridgeVerificationFinding(
            category="invalid_category",
            statement="test",
            evidence="test",
            source="test",
        )
        with pytest.raises(ValueError, match="Invalid category"):
            finding.validate()

    def test_evidence_categories(self):
        assert "fact" in VERIFICATION_EVIDENCE_CATEGORIES
        assert "observation" in VERIFICATION_EVIDENCE_CATEGORIES
        assert "verification_finding" in VERIFICATION_EVIDENCE_CATEGORIES
        assert "risk" in VERIFICATION_EVIDENCE_CATEGORIES
        assert "recommendation" in VERIFICATION_EVIDENCE_CATEGORIES
