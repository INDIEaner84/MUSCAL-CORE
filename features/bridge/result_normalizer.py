from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .opencode_adapter import OpenCodeResult


@dataclass
class VerifiedFact:
    statement: str
    evidence: str
    source: str


@dataclass
class ExtractedObservation:
    statement: str
    source: str


@dataclass
class InferredInterpretation:
    statement: str
    confidence: str


@dataclass
class ProposedHypothesis:
    statement: str
    confidence: str


@dataclass
class ExecutionInfo:
    return_code: Optional[int]
    duration: float
    session_reference: Optional[str]


@dataclass
class NormalizedResult:
    status: str
    facts: list[VerifiedFact] = field(default_factory=list)
    observations: list[ExtractedObservation] = field(default_factory=list)
    interpretations: list[InferredInterpretation] = field(default_factory=list)
    hypotheses: list[ProposedHypothesis] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    execution: Optional[ExecutionInfo] = None
    raw_stdout_ref: Optional[str] = None
    raw_stderr_ref: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "result": {
                "status": self.status,
                "facts": {
                    "verified": [
                        {"statement": f.statement, "evidence": f.evidence, "source": f.source}
                        for f in self.facts
                    ],
                },
                "observations": {
                    "extracted": [
                        {"statement": o.statement, "source": o.source}
                        for o in self.observations
                    ],
                },
                "interpretations": {
                    "inferred": [
                        {"statement": i.statement, "confidence": i.confidence}
                        for i in self.interpretations
                    ],
                },
                "hypotheses": {
                    "proposed": [
                        {"statement": h.statement, "confidence": h.confidence}
                        for h in self.hypotheses
                    ],
                },
                "unknowns": self.unknowns,
                "execution": {
                    "return_code": self.execution.return_code if self.execution else None,
                    "duration": self.execution.duration if self.execution else None,
                    "session_reference": self.execution.session_reference if self.execution else None,
                },
                "raw_artifacts": {
                    "stdout_reference": self.raw_stdout_ref,
                    "stderr_reference": self.raw_stderr_ref,
                },
            }
        }


class ResultNormalizer:

    def normalize(self, raw: OpenCodeResult) -> NormalizedResult:
        result = NormalizedResult(
            status=raw.status,
            execution=ExecutionInfo(
                return_code=raw.return_code,
                duration=raw.duration,
                session_reference=raw.session_reference,
            ),
            raw_stdout_ref=f"stdout:{len(raw.stdout)}b" if raw.stdout else None,
            raw_stderr_ref=f"stderr:{len(raw.stderr)}b" if raw.stderr else None,
        )

        if raw.status == "not-found":
            result.unknowns.append("OpenCode executable not found on system PATH")
            return result

        if raw.status == "timeout":
            result.unknowns.append(f"Execution timed out; partial output may exist")
            return result

        if raw.status == "failed":
            result.unknowns.append(f"Process failed with return code {raw.return_code}")
            if raw.stderr:
                result.observations.append(ExtractedObservation(
                    statement=f"stderr: {raw.stderr[:500]}",
                    source="opencode_adapter",
                ))
            return result

        if raw.status == "completed":
            self._extract_facts(raw, result)

        return result

    def _extract_facts(self, raw: OpenCodeResult, result: NormalizedResult) -> None:
        artifacts = raw.raw_artifacts
        if not artifacts:
            return

        if isinstance(artifacts, dict) and "raw_stdout" in artifacts:
            result.observations.append(ExtractedObservation(
                statement="Output was not valid JSON; captured as raw text",
                source="result_normalizer",
            ))
            return

        if isinstance(artifacts, dict):
            for key in ("result", "data", "output"):
                if key in artifacts:
                    result.observations.append(ExtractedObservation(
                        statement=f"Execution produced structured output under '{key}'",
                        source="result_normalizer",
                    ))

        result.facts.append(VerifiedFact(
            statement=f"OpenCode process completed with exit code 0",
            evidence=f"return_code={raw.return_code}, duration={raw.duration:.2f}s",
            source="opencode_adapter",
        ))
