from __future__ import annotations

from typing import Any, Optional


class KnowledgeDistiller:

    def distill(
        self,
        task: Any,
        normalized_result: Any,
        verification_report: Optional[Any] = None,
    ) -> dict:
        task_dict = task.to_dict() if hasattr(task, 'to_dict') else (task if isinstance(task, dict) else {})
        task_data = task_dict.get("task", task_dict)
        result_data = normalized_result.to_dict() if hasattr(normalized_result, 'to_dict') else {}

        problem = task_data.get("objective", "Unknown objective")
        constraints = task_data.get("constraints", [])
        expected = task_data.get("expected_output", "")

        solution = self._extract_solution(result_data)
        evidence = self._extract_evidence(verification_report)
        context = self._build_context(task_data, constraints, expected)
        limitations = self._extract_limitations(verification_report)

        return {
            "problem": problem,
            "solution": solution,
            "evidence": evidence,
            "context": context,
            "limitations": limitations,
        }

    def _extract_solution(self, result: dict) -> str:
        norm = result.get("result", result)
        stdout = norm.get("stdout", "")
        if stdout and len(stdout) > 10:
            return stdout[:2000]
        output = norm.get("output", "")
        if output:
            return str(output)[:2000]
        summary = norm.get("summary", "")
        if summary:
            return summary[:2000]
        changes = norm.get("summary_changes", "")
        if changes:
            return changes[:2000]
        return "Execution completed — no detailed solution extracted"

    def _extract_evidence(self, verification_report: Optional[Any]) -> str:
        if verification_report is None:
            return "No verification report available"
        report = verification_report.to_dict() if hasattr(verification_report, 'to_dict') else {}
        facts = report.get("facts", []) or report.get("verification_report", {}).get("facts", [])
        if facts:
            statements = [f.get("statement", "") for f in facts]
            return "; ".join(statements)
        status = report.get("status", "") or report.get("verification_report", {}).get("status", "")
        return f"Verification status: {status}"

    def _build_context(self, task_data: dict, constraints: list, expected: str) -> str:
        parts = []
        parts.append(f"Project: {task_data.get('project', 'unknown')}")
        if constraints:
            parts.append(f"Constraints: {'; '.join(constraints)}")
        if expected:
            parts.append(f"Expected output: {expected}")
        return " | ".join(parts)

    def _extract_limitations(self, verification_report: Optional[Any]) -> str:
        if verification_report is None:
            return "Not verified"
        report = verification_report.to_dict() if hasattr(verification_report, 'to_dict') else {}
        risks = report.get("risks", []) or report.get("verification_report", {}).get("risks", [])
        if risks:
            statements = [r.get("statement", "") for r in risks]
            return "; ".join(statements)
        return "No limitations identified"
