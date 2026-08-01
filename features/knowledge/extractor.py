from __future__ import annotations

import uuid
from typing import Any, Optional

from .models import KnowledgeCandidate, EvidenceLevel
from .distiller import KnowledgeDistiller


class KnowledgeExtractor:

    def __init__(self, distiller: Optional[KnowledgeDistiller] = None):
        self._distiller = distiller or KnowledgeDistiller()

    def extract(
        self,
        bridge_output: Any,
        task: Any = None,
        verification_report: Optional[Any] = None,
    ) -> Optional[KnowledgeCandidate]:
        if bridge_output is None:
            return None

        output_status = bridge_output.status if hasattr(bridge_output, 'status') else "unknown"
        if output_status != "completed":
            return None

        execution_id = ""
        task_id = ""
        project = ""

        if hasattr(bridge_output, 'execution_record'):
            er = bridge_output.execution_record
            if er:
                er_dict = er if isinstance(er, dict) else (er.to_dict() if hasattr(er, 'to_dict') else {})
                rec = er_dict.get("execution_record", er_dict)
                execution_id = rec.get("bridge_execution_id", "")
                task_id = rec.get("task_identity", {}).get("id", "")
        if not execution_id and hasattr(bridge_output, 'task_id'):
            execution_id = bridge_output.task_id
        if not task_id:
            task_id = getattr(bridge_output, 'task_id', str(uuid.uuid4()))
        if not project:
            project = task.project if hasattr(task, 'project') else "muscal-core"

        normalized = getattr(bridge_output, 'normalized', None)

        distilled = self._distiller.distill(
            task=task or {"task": {"objective": "Unknown", "project": project}},
            normalized_result=normalized,
            verification_report=verification_report,
        )

        evidence_level = self._determine_evidence_level(bridge_output, verification_report)
        confidence = self._compute_confidence(bridge_output, verification_report)
        category = self._classify_category(distilled["problem"], distilled["solution"])

        return KnowledgeCandidate(
            id=str(uuid.uuid4()),
            source_execution_id=execution_id,
            source_task_id=task_id,
            project=project,
            category=category,
            problem=distilled["problem"],
            solution=distilled["solution"],
            evidence=distilled["evidence"],
            verification=self._extract_verification_summary(verification_report),
            confidence=confidence,
            evidence_level=evidence_level,
            reuse_conditions=distilled["context"],
            limitations=distilled["limitations"],
        )

    def _determine_evidence_level(
        self, bridge_output: Any, verification_report: Optional[Any]
    ) -> EvidenceLevel:
        if verification_report is None:
            return EvidenceLevel.UNKNOWN
        report = verification_report.to_dict() if hasattr(verification_report, 'to_dict') else {}
        status = report.get("status", "") or report.get("verification_report", {}).get("status", "")
        if status == "passed":
            return EvidenceLevel.VERIFIED
        if status == "failed":
            return EvidenceLevel.OBSERVED
        return EvidenceLevel.INFERRED

    def _compute_confidence(self, bridge_output: Any, verification_report: Optional[Any]) -> float:
        base = 0.5
        if bridge_output is None:
            return 0.0
        if hasattr(bridge_output, 'errors') and bridge_output.errors:
            base -= 0.2
        if verification_report is not None:
            report = verification_report.to_dict() if hasattr(verification_report, 'to_dict') else {}
            status = report.get("status", "") or report.get("verification_report", {}).get("status", "")
            if status == "passed":
                base += 0.3
            elif status == "failed":
                base -= 0.2
        return max(0.0, min(1.0, base))

    def _classify_category(self, problem: str, solution: str) -> str:
        combined = (problem + " " + solution).lower()
        if any(w in combined for w in ["bug", "fix", "error", "crash", "fail"]):
            return "bug_fix"
        if any(w in combined for w in ["test", "coverage", "assert"]):
            return "testing"
        if any(w in combined for w in ["refactor", "clean", "restructure"]):
            return "refactoring"
        if any(w in combined for w in ["doc", "readme", "comment"]):
            return "documentation"
        if any(w in combined for w in ["config", "setup", "install"]):
            return "configuration"
        if any(w in combined for w in ["feature", "add", "implement", "new"]):
            return "feature"
        return "general"

    def _extract_verification_summary(self, verification_report: Optional[Any]) -> str:
        if verification_report is None:
            return "Not verified"
        report = verification_report.to_dict() if hasattr(verification_report, 'to_dict') else {}
        report_data = report.get("verification_report", report)
        status = report_data.get("status", "unknown")
        findings = report_data.get("verification_findings", [])
        return f"Status: {status}, Findings: {len(findings)}"
