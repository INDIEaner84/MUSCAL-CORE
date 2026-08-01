from __future__ import annotations

from typing import Any, Optional

from .models import ExecutionMetrics, QualityMetrics


class MetricsCollector:

    def collect(self, bridge_output: Any, verification_report: Optional[Any] = None) -> ExecutionMetrics:
        output_dict = bridge_output.to_dict() if hasattr(bridge_output, "to_dict") else {}
        exec_record = output_dict.get("execution_record") or {}
        normalized = output_dict.get("normalized") or {}

        execution_id = exec_record.get("bridge_execution_id", "unknown")
        task_id = bridge_output.task_id if hasattr(bridge_output, "task_id") else "unknown"
        status = getattr(bridge_output, "status", "unknown")
        success = status == "completed"

        meta = normalized.get("meta", {}) if isinstance(normalized, dict) else {}
        duration = meta.get("duration", 0.0) if isinstance(meta, dict) else 0.0
        token_count = meta.get("tokens", 0) if isinstance(meta, dict) else 0

        cpu_time = 0.0
        memory_usage = 0
        if hasattr(bridge_output, "normalized") and bridge_output.normalized:
            nm = bridge_output.normalized
            nmd = nm.to_dict() if hasattr(nm, "to_dict") else {}
            meta2 = nmd.get("result", {}).get("meta", {})
            cpu_time = meta2.get("cpu_time", meta2.get("latency", duration))
            memory_usage = meta2.get("memory_usage", meta2.get("ram_peak", 0))

        latency = meta.get("latency", duration) if isinstance(meta, dict) else duration

        verification_score = self._compute_verification_score(verification_report)

        return ExecutionMetrics(
            execution_id=execution_id,
            task_id=task_id,
            agent_id=getattr(bridge_output, "agent_id", "default"),
            model_id=getattr(bridge_output, "model_id", "default"),
            duration=duration,
            tokens=token_count,
            cpu_time=cpu_time,
            memory_usage=memory_usage,
            latency=latency,
            success=success,
            verification_score=verification_score,
        )

    def collect_quality(self, verification_report: Optional[Any] = None,
                         knowledge_value: float = 0.0) -> QualityMetrics:
        score = self._compute_verification_score(verification_report)
        return QualityMetrics(
            correctness=score,
            completeness=score * 0.9,
            verification_confidence=score,
            knowledge_value=knowledge_value,
        )

    def _compute_verification_score(self, report: Optional[Any]) -> float:
        if report is None:
            return 0.0
        report_dict = report.to_dict() if hasattr(report, "to_dict") else {}
        r = report_dict.get("verification_report", report_dict)
        status = r.get("status", "") if isinstance(r, dict) else ""
        if status == "passed":
            return 1.0
        if status == "failed":
            return 0.0
        if status == "partial":
            facts = r.get("facts", []) if isinstance(r, dict) else []
            passed = sum(1 for f in facts if isinstance(f, dict) and f.get("status") == "passed")
            total = max(len(facts), 1)
            return passed / total
        return 0.5
