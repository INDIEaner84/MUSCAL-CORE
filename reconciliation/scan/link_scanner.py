from __future__ import annotations

import os
import re

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, Finding, FindingSet, FindingStatus, Severity
from reconciliation.core.rule import Rule
from reconciliation.scanner import ScannerBase
from reconciliation.snapshot.file_node import FileNode
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


class BrokenLinkScanner(ScannerBase):
    @property
    def name(self) -> str:
        return "broken_link_scanner"

    @property
    def rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="BL-001",
                description="Markdown internal links must point to existing files",
                severity=Severity.MEDIUM,
                category=Category.B,
                checker_type="file_exists",
            ),
            Rule(
                rule_id="BL-002",
                description="External links are ignored by this scanner",
                severity=Severity.LOW,
                category=Category.D,
                checker_type="content_match",
                params={"pattern": r"https?://"},
            ),
        ]

    def scan(self, context: ScanContext) -> FindingSet:
        snapshot = context.snapshot
        findings: list[Finding] = []

        if snapshot is None:
            return FindingSet(scanner=self.name, findings=[])

        md_files = snapshot.glob("**/*.md")
        for md_file in md_files:
            try:
                with open(md_file.abs_path, "r", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue
            findings.extend(self._scan_file(md_file, content, snapshot))

        return FindingSet(scanner=self.name, findings=findings)

    def _scan_file(
        self,
        md_file: FileNode,
        content: str,
        snapshot: RepositorySnapshot,
    ) -> list[Finding]:
        findings: list[Finding] = []
        source_dir = os.path.dirname(md_file.rel_path)

        for match in LINK_PATTERN.finditer(content):
            link_text = match.group(1)
            raw_target = match.group(2).strip()

            if re.match(r"^(https?://|mailto:|ftp://)", raw_target):
                continue
            if raw_target.startswith("#"):
                continue

            line_num = content[: match.start()].count("\n") + 1
            targets = self._resolve_targets(raw_target, source_dir)
            exists = any(self._target_exists(t, snapshot) for t in targets)

            if not exists:
                findings.append(
                    self._make_finding(md_file, raw_target, line_num, link_text)
                )

        return findings

    @staticmethod
    def _resolve_targets(raw_target: str, source_dir: str) -> list[str]:
        target = raw_target.split("#")[0]
        if not target:
            return []
        candidates: list[str] = []
        if target.startswith("/"):
            candidates.append(target.lstrip("/"))
        elif target.startswith("./") or target.startswith("../"):
            resolved = os.path.normpath(os.path.join(source_dir, target))
            candidates.append(resolved)
        else:
            resolved = os.path.normpath(os.path.join(source_dir, target))
            if resolved != target:
                candidates.append(resolved)
            candidates.append(target)
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _target_exists(target: str, snapshot: RepositorySnapshot) -> bool:
        if snapshot.file_node_for(target):
            return True
        if not target.endswith(".md") and snapshot.file_node_for(target + ".md"):
            return True
        if snapshot.filter(directory=target):
            return True
        if snapshot.glob(target):
            return True
        return False

    @staticmethod
    def _make_finding(
        md_file: FileNode,
        target: str,
        line_num: int,
        link_text: str,
    ) -> Finding:
        safe_source = re.sub(r"[^a-zA-Z0-9_]", "_", md_file.rel_path)[:30]
        safe_target = re.sub(r"[^a-zA-Z0-9_]", "_", target)[:20]
        is_archive = md_file.rel_path.startswith("archive")

        return Finding(
            finding_id=f"BL-001_{safe_source}_{safe_target}",
            scanner="broken_link_scanner",
            file=md_file.rel_path,
            severity=Severity.MEDIUM,
            category=Category.D if is_archive else Category.B,
            status=FindingStatus.OPEN,
            line=line_num,
            description="Broken internal markdown link",
            current_value=f"Referenced file does not exist: {target}",
            expected_value="Target file must exist",
            extra={"link_target": target, "link_text": link_text},
        )
