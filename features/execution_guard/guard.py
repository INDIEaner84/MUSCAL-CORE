from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    GitSnapshot, PreExecutionGuard, PostExecutionGuard,
    AutonomyLevel, GuardDecision, GuardFinding,
)
from .git_snapshot import GitSnapshotter, NotGitRepositoryError
from .policy import AutonomyPolicy
from .rollback import RollbackInfo


@dataclass
class GuardResult:
    pre: PreExecutionGuard
    post: Optional[PostExecutionGuard]
    rollback: RollbackInfo
    findings: list[GuardFinding] = field(default_factory=list)


class ExecutionGuard:

    def __init__(
        self,
        policy: Optional[AutonomyPolicy] = None,
        git_snapshotter: Optional[GitSnapshotter] = None,
        autonomy_level: AutonomyLevel = AutonomyLevel.A3_MODIFY_AND_TEST,
    ):
        self._policy = policy or AutonomyPolicy(level=autonomy_level)
        self._snapshotter = git_snapshotter or GitSnapshotter()
        self._rollback: Optional[RollbackInfo] = None

    def pre_check(
        self,
        task_id: str,
        project_id: str,
        path: Optional[Path] = None,
    ) -> PreExecutionGuard:
        target = path or Path.cwd()
        findings: list[GuardFinding] = []
        reasons: list[str] = []

        try:
            snapshot = self._snapshotter.snapshot(target)
        except NotGitRepositoryError as e:
            snapshot = GitSnapshot(
                repository_root=Path.cwd(),
                branch="unknown",
                commit="unknown",
                dirty=False,
                modified_files=[],
                untracked_files=[],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if not self._policy.can("modify_code"):
            findings.append(GuardFinding(
                category="autonomy",
                message=f"Autonomy level {self._policy.level.value} does not permit code modification",
                severity="high",
            ))
            reasons.append(f"Current autonomy level {self._policy.level.value} is read-only")
            decision = GuardDecision.BLOCK
            allowed = False
        elif snapshot.dirty:
            findings.append(GuardFinding(
                category="git",
                message=f"Repository has {len(snapshot.modified_files)} modified and {len(snapshot.untracked_files)} untracked files",
                severity="warning",
            ))
            reasons.append(f"Dirty repository: {len(snapshot.modified_files)} modified, {len(snapshot.untracked_files)} untracked")
            decision = GuardDecision.ALLOW_WITH_WARNING
            allowed = True
        else:
            findings.append(GuardFinding(
                category="git",
                message="Repository is clean",
                severity="info",
            ))
            reasons.append("Clean repository — safe to proceed")
            decision = GuardDecision.ALLOW
            allowed = True

        return PreExecutionGuard(
            task_id=task_id,
            project_id=project_id,
            snapshot=snapshot,
            autonomy_level=self._policy.level,
            approval_status=decision,
            allowed=allowed,
            findings=findings,
            reasons=reasons,
        )

    def post_check(
        self,
        pre: PreExecutionGuard,
        path: Optional[Path] = None,
    ) -> PostExecutionGuard:
        target = path or Path.cwd()
        findings: list[GuardFinding] = []

        post_snapshot = self._snapshotter.snapshot(target)
        pre_snap = pre.snapshot

        changed = self._snapshotter.detect_changes(pre_snap, post_snapshot)

        commit_changed = pre_snap.commit != post_snapshot.commit
        tests_changed = any("test" in f.lower() for f in changed)

        self._create_rollback(post_snapshot)

        if changed:
            findings.append(GuardFinding(
                category="changes",
                message=f"Detected {len(changed)} changes after execution",
                severity="info",
            ))
        if commit_changed:
            findings.append(GuardFinding(
                category="git",
                message=f"Commit changed: {pre_snap.commit[:8]} -> {post_snapshot.commit[:8]}",
                severity="info",
            ))

        return PostExecutionGuard(
            pre_snapshot=pre_snap,
            post_snapshot=post_snapshot,
            changed_files=changed,
            commit_changed=commit_changed,
            tests_changed=tests_changed,
            rollback_available=self._rollback is not None and self._rollback.available,
            findings=findings,
        )

    def _create_rollback(self, snapshot: GitSnapshot) -> None:
        self._rollback = RollbackInfo.from_commit(snapshot.commit)

    def get_current_rollback(self) -> Optional[RollbackInfo]:
        return self._rollback
