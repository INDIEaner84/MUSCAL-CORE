from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .project_scanner import ProjectScanner, ProjectContext, NotARepositoryError
from .opencode_adapter import OpenCodeAdapter, OpenCodeResult
from .result_normalizer import ResultNormalizer, NormalizedResult
from .bridge_event_writer import BridgeEventWriter
from .handoff_report import HandoffReport, BridgeReport
from .task_contract import TaskContract
from .session_continuity import SessionContinuityTracker
from .recovery import RecoveryHandler
from features.verification.bridge_verifier import BridgeVerifier
from features.execution_guard.guard import ExecutionGuard, GuardResult
from features.execution_guard.models import AutonomyLevel, GuardDecision


@dataclass
class BridgeConfig:
    opencode_path: str = "opencode"
    timeout: int = 120
    workdir: Optional[Path] = None
    output_dir: Optional[Path] = None
    event_store_path: Optional[Path] = None
    model: Optional[str] = None
    agent: Optional[str] = None
    session: Optional[str] = None
    max_retries: int = 3
    verification_required: bool = True
    autonomy_level: AutonomyLevel = AutonomyLevel.A3_MODIFY_AND_TEST

    def resolve(self) -> BridgeConfig:
        if self.workdir is None:
            self.workdir = Path.cwd()
        if self.output_dir is None:
            self.output_dir = Path("docs/bridge/handovers")
        return self


@dataclass
class BridgeOutput:
    context: Optional[ProjectContext]
    opencode_result: Optional[OpenCodeResult]
    normalized: Optional[NormalizedResult]
    event_seq: Optional[int]
    report_paths: tuple[Optional[Path], Optional[Path]]
    task_id: str
    status: str
    errors: list[str] = field(default_factory=list)
    task: Optional[TaskContract] = None
    verification_report: Optional[dict] = None
    recovery_events: list[dict] = field(default_factory=list)
    execution_record: Optional[dict] = None
    guard_result: Optional[dict] = None


def run_bridge(
    message: str,
    config: Optional[BridgeConfig] = None,
    task_id: Optional[str] = None,
    task: Optional[TaskContract] = None,
) -> BridgeOutput:
    cfg = (config or BridgeConfig()).resolve()
    tid = task_id or str(uuid.uuid4())
    errors: list[str] = []

    task_obj = task or TaskContract(
        id=tid,
        project="muscal-core",
        objective=message[:500],
    )

    context: Optional[ProjectContext] = None
    try:
        scanner = ProjectScanner(cfg.workdir)
        context = scanner.scan()
    except NotARepositoryError as e:
        errors.append(str(e))

    guard = ExecutionGuard(autonomy_level=cfg.autonomy_level)
    pre = guard.pre_check(
        task_id=tid,
        project_id=str(context.root) if context else "unknown",
        path=cfg.workdir,
    )

    if pre.approval_status == GuardDecision.BLOCK:
        guard_result = GuardResult(
            pre=pre, post=None,
            rollback=guard.get_current_rollback() if hasattr(guard, '_rollback') and guard._rollback else __import__('features.execution_guard.rollback', fromlist=['RollbackInfo']).RollbackInfo.not_available(),
        )
        errors.append(f"Execution blocked by guard: {', '.join(pre.reasons)}")
        normalized = NormalizedResult(status="blocked")
        normalized.unknowns.append(f"Blocked by execution guard: {pre.reasons}")

        report = BridgeReport(
            project=context or _fallback_context(),
            task=task_obj.to_dict(),
            execution=normalized,
            risks=[{"priority": "P0", "description": e} for e in errors],
            next_action="Review guard findings and retry with appropriate autonomy level",
        )
        report_gen = HandoffReport(output_dir=cfg.output_dir)
        md_path, yml_path = report_gen.generate(report)

        return BridgeOutput(
            context=context, opencode_result=None, normalized=normalized,
            event_seq=None, report_paths=(md_path, yml_path),
            task_id=tid, status="blocked", errors=errors,
            task=task_obj, guard_result=guard_result.pre.to_dict() if hasattr(guard_result, 'pre') else pre.to_dict(),
        )

    adapter = OpenCodeAdapter(
        opencode_path=cfg.opencode_path,
        timeout=cfg.timeout,
    )
    raw = adapter.execute(
        message=message,
        workdir=cfg.workdir,
        session=cfg.session,
        model=cfg.model,
        agent=cfg.agent,
    )
    if raw.status == "not-found":
        errors.append("OpenCode executable not found")

    recovery_events: list[dict] = []
    if raw.status != "completed":
        recovery = RecoveryHandler(adapter=adapter, max_retries=cfg.max_retries)
        exec_id = str(uuid.uuid4())
        recovery_event = recovery.handle(raw, exec_id, message, cfg.session)
        recovery_events.append(recovery_event.to_dict())
        if recovery_event.recovered:
            raw = adapter.execute(
                message=message,
                workdir=cfg.workdir,
                session=recovery_event.recovery_action.retry_count > 0 and cfg.session or None,
            )

    normalizer = ResultNormalizer()
    normalized = normalizer.normalize(raw)

    verifier = BridgeVerifier()
    verification_report = None
    if cfg.verification_required and normalized:
        normalized_dict = normalized.to_dict().get("result", {})
        verification_report = verifier.verify_bridge_result(normalized_dict)
        if verification_report.status == "failed":
            errors.append(f"Verification failed: {len(verification_report.verification_findings)} findings")

    post = guard.post_check(pre, path=cfg.workdir)
    guard_result = GuardResult(
        pre=pre, post=post,
        rollback=guard.get_current_rollback() or __import__('features.execution_guard.rollback', fromlist=['RollbackInfo']).RollbackInfo.not_available(),
    )

    writer = BridgeEventWriter(db_path=cfg.event_store_path)
    event_seq = None
    if context and writer.is_connected:
        payload: dict[str, Any] = {
            "message": message,
            "return_code": raw.return_code,
            "duration": raw.duration,
            "guard_pre_decision": pre.approval_status.value,
            "guard_post_changes": len(post.changed_files),
        }
        if verification_report:
            payload["verification_status"] = verification_report.status
        event_seq = writer.write_execution_event(
            task_id=tid,
            project_id=str(context.root),
            execution_id=str(uuid.uuid4()),
            opencode_session=raw.session_reference,
            status=raw.status,
            causation_id=tid,
            payload=payload,
        )

    tracker = SessionContinuityTracker()
    exec_record = tracker.record_execution(
        project=context or _fallback_context(),
        task=task_obj,
        opencode_session=raw.session_reference,
        status=raw.status,
    )
    if raw.status == "completed":
        tracker.update_next_action(exec_record.bridge_execution_id, "Review execution output and verify results")
    else:
        tracker.update_next_action(exec_record.bridge_execution_id, "Diagnose execution failure and retry")
    last = tracker.get_last_execution()

    report = BridgeReport(
        project=context or _fallback_context(),
        task=task_obj.to_dict(),
        execution=normalized,
        risks=[{"priority": "P1", "description": e} for e in errors],
        next_action=last.next_action if last else "Unknown",
    )

    report_gen = HandoffReport(output_dir=cfg.output_dir)
    md_path, yml_path = report_gen.generate(report)

    overall_status = "completed" if raw.status == "completed" and not errors else "failed"

    return BridgeOutput(
        context=context,
        opencode_result=raw,
        normalized=normalized,
        event_seq=event_seq,
        report_paths=(md_path, yml_path),
        task_id=tid,
        status=overall_status,
        errors=errors,
        task=task_obj,
        verification_report=verification_report.to_dict() if verification_report else None,
        recovery_events=recovery_events,
        execution_record=exec_record.to_dict() if exec_record else None,
        guard_result=guard_result.pre.to_dict(),
    )


def _fallback_context() -> ProjectContext:
    from .project_scanner import GitStatus
    return ProjectContext(
        root=Path.cwd(),
        repository="unknown",
        branch="unknown",
        commit="unknown",
        git=GitStatus(dirty=False, modified_count=0, untracked_count=0),
        scan_timestamp=datetime.now(timezone.utc).isoformat(),
        scan_status="fallback",
    )
