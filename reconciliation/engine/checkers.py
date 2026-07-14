from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, Finding, FindingStatus, Severity
from reconciliation.core.rule import Rule
from reconciliation.snapshot.file_node import FileNode


def _make_finding_id(rule: Rule, target_name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", target_name)[:40]
    return f"{rule.rule_id}_{safe}"


class RuleChecker(ABC):
    @abstractmethod
    def handles(self) -> str:
        ...

    def supports(self, rule: Rule) -> bool:
        return rule.checker_type == self.handles()

    @abstractmethod
    def check(
        self,
        rule: Rule,
        target: object,
        context: ScanContext,
    ) -> Finding | None:
        ...


class FileExistsChecker(RuleChecker):
    def handles(self) -> str:
        return "file_exists"

    def check(
        self,
        rule: Rule,
        target: object,
        context: ScanContext,
    ) -> Finding | None:
        if context.snapshot is None:
            return None
        if not isinstance(target, str):
            return None
        node = context.snapshot.file_node_for(target)
        if node is not None:
            return None
        return Finding(
            finding_id=_make_finding_id(rule, target),
            scanner=rule.rule_id,
            file=target,
            severity=rule.severity,
            category=rule.category,
            status=FindingStatus.OPEN,
            description=rule.description,
            current_value=f"File not found: {target}",
            expected_value="File must exist",
        )


class ContentMatchChecker(RuleChecker):
    def handles(self) -> str:
        return "content_match"

    def check(
        self,
        rule: Rule,
        target: object,
        context: ScanContext,
    ) -> Finding | None:
        if not isinstance(target, FileNode):
            return None
        pattern: str = rule.params.get("pattern", "")
        if not pattern:
            return None
        invert: bool = rule.params.get("invert", False)
        try:
            with open(target.abs_path, "r", errors="replace") as f:
                content = f.read()
        except Exception:
            return Finding(
                finding_id=_make_finding_id(rule, target.rel_path),
                scanner=rule.rule_id,
                file=target.rel_path,
                severity=rule.severity,
                category=rule.category,
                status=FindingStatus.OPEN,
                description=rule.description,
                current_value="Could not read file",
                expected_value=f"Readable file with content matching /{pattern}/",
            )
        matched = re.search(pattern, content) is not None
        if invert:
            matched = not matched
        if matched:
            return None
        return Finding(
            finding_id=_make_finding_id(rule, target.rel_path),
            scanner=rule.rule_id,
            file=target.rel_path,
            severity=rule.severity,
            category=rule.category,
            status=FindingStatus.OPEN,
            description=rule.description,
            current_value=f"Pattern /{pattern}/ not{' ' if not invert else ' '}found",
            expected_value=f"Content matching /{pattern}/",
        )


class FileCountChecker(RuleChecker):
    def handles(self) -> str:
        return "file_count"

    def check(
        self,
        rule: Rule,
        target: object,
        context: ScanContext,
    ) -> Finding | None:
        if context.snapshot is None:
            return None
        if not isinstance(target, str):
            return None
        expected: int = rule.params.get("expected_count", 0)
        tolerance: int = rule.params.get("tolerance", 0)
        files = context.snapshot.filter(directory=target)
        actual = len(files)
        if abs(actual - expected) <= tolerance:
            return None
        return Finding(
            finding_id=_make_finding_id(rule, target.replace("/", "_")),
            scanner=rule.rule_id,
            file=target,
            severity=rule.severity,
            category=rule.category,
            status=FindingStatus.OPEN,
            description=rule.description,
            current_value=f"Found {actual} files",
            expected_value=f"{expected} files (tolerance {tolerance})",
        )
