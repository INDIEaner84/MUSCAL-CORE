from __future__ import annotations

from features.bridge.result_normalizer import ResultNormalizer, NormalizedResult, VerifiedFact
from features.bridge.opencode_adapter import OpenCodeResult


class TestResultNormalizer:

    def test_normalizer_handles_not_found(self):
        normalizer = ResultNormalizer()
        raw = OpenCodeResult(
            status="not-found", return_code=None,
            duration=0.1, stdout="", stderr="not found",
            session_reference=None,
        )
        result = normalizer.normalize(raw)
        assert result.status == "not-found"
        assert "OpenCode executable not found" in str(result.unknowns)

    def test_normalizer_handles_timeout(self):
        normalizer = ResultNormalizer()
        raw = OpenCodeResult(
            status="timeout", return_code=None,
            duration=30.0, stdout="", stderr="timeout",
            session_reference=None,
        )
        result = normalizer.normalize(raw)
        assert result.status == "timeout"
        assert "timed out" in str(result.unknowns)

    def test_normalizer_handles_failure(self):
        normalizer = ResultNormalizer()
        raw = OpenCodeResult(
            status="failed", return_code=1,
            duration=2.0, stdout="", stderr="error occurred",
            session_reference=None,
        )
        result = normalizer.normalize(raw)
        assert result.status == "failed"
        assert result.execution is not None
        assert result.execution.return_code == 1

    def test_normalizer_handles_completed_with_json(self):
        normalizer = ResultNormalizer()
        raw = OpenCodeResult(
            status="completed", return_code=0,
            duration=5.0, stdout='{"result": "ok"}', stderr="",
            session_reference="ses_123",
            raw_artifacts={"result": "ok"},
        )
        result = normalizer.normalize(raw)
        assert result.status == "completed"
        assert len(result.facts) >= 1
        assert "completed with exit code 0" in str(result.facts[0].statement)

    def test_normalizer_preserves_execution_info(self):
        normalizer = ResultNormalizer()
        raw = OpenCodeResult(
            status="completed", return_code=0,
            duration=3.5, stdout="ok", stderr="",
            session_reference="ses_456",
        )
        result = normalizer.normalize(raw)
        assert result.execution is not None
        assert result.execution.return_code == 0
        assert result.execution.duration == 3.5
        assert result.execution.session_reference == "ses_456"

    def test_normalized_result_to_dict(self):
        result = NormalizedResult(status="completed")
        result.facts.append(VerifiedFact(
            statement="test fact", evidence="evidence", source="test",
        ))
        d = result.to_dict()
        assert d["result"]["status"] == "completed"
        assert len(d["result"]["facts"]["verified"]) == 1
        assert d["result"]["facts"]["verified"][0]["statement"] == "test fact"
