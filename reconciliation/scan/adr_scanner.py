from __future__ import annotations

import os
import re
from typing import Any

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, Finding, FindingSet, FindingStatus, Severity
from reconciliation.core.rule import Rule
from reconciliation.scanner import ScannerBase
from reconciliation.snapshot.file_node import FileNode
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot

VALID_STATUSES = {"PROPOSED", "ACCEPTED", "APPLIED", "DEPRECATED", "SUPERSEDED"}
REQUIRED_SECTIONS = {"## Context", "## Decision", "## Consequences"}
ADR_FILENAME_RE = re.compile(r"^ADR-(\d{3})-(.+)\.md$")
H1_ADR_RE = re.compile(r"^#\s*ADR-(\d{3}):")
STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(.+)")
DATE_RE = re.compile(r"\*\*Date:\*\*\s*(.+)")
INDEX_ENTRY_RE = re.compile(r"\| ADR-(\d{3}) \| \[([^\]]+)\]\(([^)]+)\) \| (.+?) \|.+?")


def _sanitize(s: str, max_len: int = 30) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)[:max_len]


class AdrValidatorScanner(ScannerBase):
    @property
    def name(self) -> str:
        return "adr_validator_scanner"

    @property
    def rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="ADR-CR-001",
                description="Every ADR must have a unique number",
                severity=Severity.HIGH,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-002",
                description="Every ADR in spec/ must be listed in ADR-INDEX.md",
                severity=Severity.HIGH,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-003",
                description="ADR-INDEX.md must not reference non-existent files",
                severity=Severity.HIGH,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-004",
                description="ADR status must be one of: PROPOSED, ACCEPTED, APPLIED, DEPRECATED, SUPERSEDED",
                severity=Severity.MEDIUM,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-005",
                description="APPLIED ADRs must have a date",
                severity=Severity.MEDIUM,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-007",
                description="ADR numbers must be sequential without gaps",
                severity=Severity.LOW,
                category=Category.B,
            ),
            Rule(
                rule_id="ADR-CR-008",
                description="Every ADR must have Context, Decision, and Consequences sections",
                severity=Severity.MEDIUM,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-009",
                description="ADR filenames must follow ADR-NNN-description.md",
                severity=Severity.LOW,
                category=Category.A,
            ),
            Rule(
                rule_id="ADR-CR-010",
                description="PROJECT_STATE.md ADR table must match ADR-INDEX.md",
                severity=Severity.HIGH,
                category=Category.A,
            ),
        ]

    def scan(self, context: ScanContext) -> FindingSet:
        snapshot = context.snapshot
        if snapshot is None:
            return FindingSet(scanner=self.name, findings=[])

        adr_files = [f for f in snapshot.glob("spec/ADR-*.md") if f.rel_path != "spec/ADR-INDEX.md"]
        index_file = snapshot.file_node_for("spec/ADR-INDEX.md")
        project_state = snapshot.file_node_for("docs/PROJECT_STATE.md")

        findings: list[Finding] = []

        index_entries = self._parse_index(index_file, snapshot) if index_file else []
        project_adrs = self._parse_project_state_adrs(project_state) if project_state else []

        findings.extend(self._check_unique_numbers(adr_files))
        findings.extend(self._check_index_completeness(adr_files, index_entries))
        findings.extend(self._check_index_accuracy(index_entries, snapshot))
        findings.extend(self._check_statuses(adr_files))
        findings.extend(self._check_dates(adr_files))
        findings.extend(self._check_sequential_numbers(adr_files))
        findings.extend(self._check_required_sections(adr_files))
        findings.extend(self._check_filenames(adr_files))
        findings.extend(self._check_project_state_alignment(index_entries, project_adrs))

        return FindingSet(scanner=self.name, findings=findings)

    @staticmethod
    def _parse_index(index_file: FileNode, snapshot: RepositorySnapshot) -> list[dict[str, Any]]:
        try:
            with open(index_file.abs_path, "r") as f:
                content = f.read()
        except Exception:
            return []
        index_dir = index_file.directory
        entries: list[dict[str, Any]] = []
        for line in content.split("\n"):
            m = INDEX_ENTRY_RE.search(line)
            if m:
                link_file = m.group(3).lstrip("./")
                resolved = os.path.normpath(os.path.join(index_dir, link_file))
                file_node = snapshot.file_node_for(resolved) if resolved else None
                entries.append({
                    "number": int(m.group(1)),
                    "title": m.group(2),
                    "link": resolved,
                    "file_node": file_node,
                    "status_raw": m.group(4).strip(),
                })
        return entries

    @staticmethod
    def _parse_project_state_adrs(project_state: FileNode) -> list[dict[str, str]]:
        try:
            with open(project_state.abs_path, "r") as f:
                content = f.read()
        except Exception:
            return []
        entries: list[dict[str, str]] = []
        in_table = False
        for line in content.split("\n"):
            if line.startswith("| ADR-"):
                in_table = True
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 3:
                    entries.append({"id": parts[0], "title": parts[1], "status": parts[2]})
            elif in_table and not line.startswith("|"):
                break
        return entries

    def _make_finding(
        self,
        rule_id: str,
        file: str,
        description: str,
        severity: Severity,
        category: Category,
        current_value: str = "",
        expected_value: str = "",
        line: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Finding:
        safe_file = _sanitize(file.replace("/", "_"))
        return Finding(
            finding_id=f"{rule_id}_{safe_file}",
            scanner=self.name,
            file=file,
            severity=severity,
            category=category,
            status=FindingStatus.OPEN,
            line=line,
            description=description,
            current_value=current_value,
            expected_value=expected_value,
            extra=extra or {},
        )

    def _check_unique_numbers(self, adr_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        seen: dict[int, list[FileNode]] = {}
        for f in adr_files:
            m = ADR_FILENAME_RE.match(f.filename)
            if m:
                num = int(m.group(1))
                seen.setdefault(num, []).append(f)

        for num, files in seen.items():
            if len(files) > 1:
                paths = ", ".join(f.rel_path for f in files)
                f0 = files[0]
                findings.append(self._make_finding(
                    rule_id="ADR-CR-001",
                    file=f0.rel_path,
                    description=f"Duplicate ADR number {num:03d}",
                    severity=Severity.HIGH,
                    category=Category.A,
                    current_value=f"Files: {paths}",
                    expected_value=f"Single file for ADR-{num:03d}",
                ))
        return findings

    def _check_index_completeness(
        self,
        adr_files: list[FileNode],
        index_entries: list[dict[str, Any]],
    ) -> list[Finding]:
        findings: list[Finding] = []
        indexed_numbers = {e["number"] for e in index_entries}
        for f in adr_files:
            m = ADR_FILENAME_RE.match(f.filename)
            if m:
                num = int(m.group(1))
                if num not in indexed_numbers:
                    findings.append(self._make_finding(
                        rule_id="ADR-CR-002",
                        file=f.rel_path,
                        description=f"ADR-{num:03d} not listed in ADR-INDEX.md",
                        severity=Severity.HIGH,
                        category=Category.A,
                        current_value=f"File exists at {f.rel_path} but no index entry",
                        expected_value=f"Entry in ADR-INDEX.md for ADR-{num:03d}",
                    ))
        return findings

    def _check_index_accuracy(
        self,
        index_entries: list[dict[str, Any]],
        snapshot: RepositorySnapshot,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for entry in index_entries:
            target = entry["link"]
            if target and not snapshot.file_node_for(target):
                findings.append(self._make_finding(
                    rule_id="ADR-CR-003",
                    file="spec/ADR-INDEX.md",
                    description=f"Index entry ADR-{entry['number']:03d} references non-existent file",
                    severity=Severity.HIGH,
                    category=Category.A,
                    current_value=f"Referenced file: {target}",
                    expected_value="Existing file",
                    extra={"link_target": target, "adr_number": entry["number"]},
                ))
        return findings

    def _check_statuses(self, adr_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        for f in adr_files:
            status_raw = self._extract_field(f, STATUS_RE)
            if status_raw is None:
                continue
            status_clean = status_raw.rstrip("*").strip()
            m = ADR_FILENAME_RE.match(f.filename)
            num = m.group(1) if m else "???"
            if status_clean not in VALID_STATUSES:
                findings.append(self._make_finding(
                    rule_id="ADR-CR-004",
                    file=f.rel_path,
                    description=f"ADR-{num} has invalid status: '{status_clean}'",
                    severity=Severity.MEDIUM,
                    category=Category.A,
                    current_value=f"Status: {status_raw}",
                    expected_value=f"One of: {', '.join(sorted(VALID_STATUSES))}",
                ))
        return findings

    def _check_dates(self, adr_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        for f in adr_files:
            status_raw = self._extract_field(f, STATUS_RE)
            if status_raw is None:
                continue
            is_applied = "APPLIED" in status_raw and "NOT_" not in status_raw
            if not is_applied:
                continue
            date_raw = self._extract_field(f, DATE_RE)
            if not date_raw or not date_raw.strip():
                m = ADR_FILENAME_RE.match(f.filename)
                num = m.group(1) if m else "???"
                findings.append(self._make_finding(
                    rule_id="ADR-CR-005",
                    file=f.rel_path,
                    description=f"ADR-{num} is APPLIED but missing date",
                    severity=Severity.MEDIUM,
                    category=Category.A,
                    current_value="No **Date:** field found",
                    expected_value="**Date:** YYYY-MM-DD",
                ))
        return findings

    def _check_sequential_numbers(self, adr_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        numbers: list[int] = []
        for f in adr_files:
            m = ADR_FILENAME_RE.match(f.filename)
            if m:
                numbers.append(int(m.group(1)))
        if not numbers:
            return findings
        numbers.sort()
        gaps: list[str] = []
        for i in range(numbers[0], numbers[-1] + 1):
            if i not in numbers:
                gaps.append(f"ADR-{i:03d}")

        for f in adr_files:
            m = ADR_FILENAME_RE.match(f.filename)
            if m and int(m.group(1)) == numbers[-1]:
                if gaps:
                    findings.append(self._make_finding(
                        rule_id="ADR-CR-007",
                        file="spec/ADR-INDEX.md",
                        description=f"Gaps in ADR numbering: {', '.join(gaps)}",
                        severity=Severity.LOW,
                        category=Category.B,
                        current_value=f"Numbers present: {', '.join(f'ADR-{n:03d}' for n in numbers)}",
                        expected_value=f"Sequential from ADR-{numbers[0]:03d} to ADR-{numbers[-1]:03d}",
                    ))
                break
        return findings

    def _check_required_sections(self, adr_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        for f in adr_files:
            try:
                with open(f.abs_path, "r") as fh:
                    content = fh.read()
            except Exception:
                continue
            m = ADR_FILENAME_RE.match(f.filename)
            num = m.group(1) if m else "???"
            missing = [s for s in REQUIRED_SECTIONS if s not in content]
            if missing:
                findings.append(self._make_finding(
                    rule_id="ADR-CR-008",
                    file=f.rel_path,
                    description=f"ADR-{num} missing required section(s): {', '.join(missing)}",
                    severity=Severity.MEDIUM,
                    category=Category.A,
                    current_value=f"Missing: {', '.join(missing)}",
                    expected_value=f"All required sections: {', '.join(REQUIRED_SECTIONS)}",
                ))
        return findings

    def _check_filenames(self, adr_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        for f in adr_files:
            if not ADR_FILENAME_RE.match(f.filename):
                findings.append(self._make_finding(
                    rule_id="ADR-CR-009",
                    file=f.rel_path,
                    description=f"Filename does not follow ADR-NNN-description.md pattern",
                    severity=Severity.LOW,
                    category=Category.A,
                    current_value=f"Filename: {f.filename}",
                    expected_value="ADR-NNN-description.md",
                ))
        return findings

    def _check_project_state_alignment(
        self,
        index_entries: list[dict[str, Any]],
        project_adrs: list[dict[str, str]],
    ) -> list[Finding]:
        findings: list[Finding] = []
        index_map = {e["number"]: e for e in index_entries}
        project_map = {e["id"]: e for e in project_adrs}

        for entry in index_entries:
            adr_id = f"ADR-{entry['number']:03d}"
            if adr_id not in project_map:
                findings.append(self._make_finding(
                    rule_id="ADR-CR-010",
                    file="docs/PROJECT_STATE.md",
                    description=f"{adr_id} in ADR-INDEX.md but missing from PROJECT_STATE.md",
                    severity=Severity.HIGH,
                    category=Category.A,
                    current_value=f"Missing: {adr_id} — {entry['title']}",
                    expected_value="Entry in PROJECT_STATE.md ADR table",
                ))

        for adr_id, entry in project_map.items():
            num_match = re.match(r"ADR-(\d{3})", adr_id)
            if num_match:
                num = int(num_match.group(1))
                if num not in index_map:
                    findings.append(self._make_finding(
                        rule_id="ADR-CR-010",
                        file="docs/PROJECT_STATE.md",
                        description=f"{adr_id} in PROJECT_STATE.md but missing from ADR-INDEX.md",
                        severity=Severity.HIGH,
                        category=Category.A,
                        current_value=f"Extra: {adr_id} — {entry.get('title', '')}",
                        expected_value="Consistent between both documents",
                    ))

        return findings

    @staticmethod
    def _extract_field(file_node: FileNode, pattern: re.Pattern[str]) -> str | None:
        try:
            with open(file_node.abs_path, "r") as f:
                for line in f:
                    m = pattern.search(line)
                    if m:
                        return m.group(1).strip()
        except Exception:
            return None
        return None
