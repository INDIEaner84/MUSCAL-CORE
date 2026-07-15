from __future__ import annotations

import re
from typing import Any

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, Finding, FindingSet, FindingStatus, Severity
from reconciliation.core.rule import Rule
from reconciliation.scanner import ScannerBase
from reconciliation.snapshot.file_node import FileNode

REQUIRED_SECTIONS = {"## Motivation", "## Specification", "## Decision", "## Consequences"}
FRONTMATTER_FIELDS = {"id", "title", "status", "date"}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
RFC_FILENAME_RE = re.compile(r"^RFC[-_](\d{3})[-_]?(.*)\.md$", re.IGNORECASE)
RFC_H1_RE = re.compile(r"^#\s*RFC[-_](\d{3})", re.IGNORECASE)
H2_RE = re.compile(r"^##\s+(.+)")


def _sanitize(s: str, max_len: int = 30) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)[:max_len]


class RfcValidatorScanner(ScannerBase):
    @property
    def name(self) -> str:
        return "rfc_validator_scanner"

    @property
    def rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="RFC-001",
                description="RFC files must have valid frontmatter with id, title, status, date",
                severity=Severity.MEDIUM,
                category=Category.B,
            ),
            Rule(
                rule_id="RFC-002",
                description="RFC files must contain required sections: Motivation, Specification, Decision, Consequences",
                severity=Severity.MEDIUM,
                category=Category.B,
            ),
            Rule(
                rule_id="RFC-003",
                description="RFC numbering must be consistent (no duplicates, valid format)",
                severity=Severity.HIGH,
                category=Category.A,
            ),
        ]

    def scan(self, context: ScanContext) -> FindingSet:
        snapshot = context.snapshot
        if snapshot is None:
            return FindingSet(scanner=self.name, findings=[])

        md_files = snapshot.glob("**/*.md")
        rfc_files = [f for f in md_files if self._is_rfc(f)]

        findings: list[Finding] = []
        findings.extend(self._check_frontmatter(rfc_files))
        findings.extend(self._check_required_sections(rfc_files))
        findings.extend(self._check_numbering(rfc_files))

        return FindingSet(scanner=self.name, findings=findings)

    def _is_rfc(self, file_node: FileNode) -> bool:
        if RFC_FILENAME_RE.match(file_node.filename):
            return True
        try:
            with open(file_node.abs_path, "r", errors="replace") as f:
                content = f.read(2000)
        except Exception:
            return False
        if RFC_H1_RE.search(content):
            return True
        fm_match = FRONTMATTER_RE.match(content)
        if fm_match:
            fm_text = fm_match.group(1)
            if re.search(r"^type:\s*rfc", fm_text, re.IGNORECASE | re.MULTILINE):
                return True
            if re.search(r"^rfc:", fm_text, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def _check_frontmatter(self, rfc_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        for f in rfc_files:
            try:
                with open(f.abs_path, "r", errors="replace") as fh:
                    content = fh.read()
            except Exception:
                continue

            fm_match = FRONTMATTER_RE.match(content)
            if not fm_match:
                findings.append(self._make_finding(
                    rule_id="RFC-001",
                    file=f.rel_path,
                    description="RFC file missing frontmatter (--- delimiters)",
                    severity=Severity.MEDIUM,
                    category=Category.B,
                    current_value="No frontmatter found",
                    expected_value="Frontmatter with id, title, status, date",
                ))
                continue

            fm_text = fm_match.group(1)
            present = set()
            for line in fm_text.split("\n"):
                for field in FRONTMATTER_FIELDS:
                    if re.match(rf"^{field}:", line, re.IGNORECASE):
                        present.add(field)

            missing = FRONTMATTER_FIELDS - present
            if missing:
                findings.append(self._make_finding(
                    rule_id="RFC-001",
                    file=f.rel_path,
                    description=f"RFC frontmatter missing field(s): {', '.join(sorted(missing))}",
                    severity=Severity.MEDIUM,
                    category=Category.B,
                    current_value=f"Present: {', '.join(sorted(present)) if present else 'none'}",
                    expected_value=f"Required: {', '.join(sorted(FRONTMATTER_FIELDS))}",
                ))
        return findings

    def _check_required_sections(self, rfc_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        for f in rfc_files:
            try:
                with open(f.abs_path, "r", errors="replace") as fh:
                    content = fh.read()
            except Exception:
                continue

            found_sections: set[str] = set()
            for line in content.split("\n"):
                m = H2_RE.match(line)
                if m:
                    heading = m.group(1).strip()
                    for req in REQUIRED_SECTIONS:
                        req_name = req.lstrip("# ").strip()
                        if req_name.lower() == heading.lower():
                            found_sections.add(req)

            missing = REQUIRED_SECTIONS - found_sections
            if missing:
                findings.append(self._make_finding(
                    rule_id="RFC-002",
                    file=f.rel_path,
                    description=f"RFC missing required section(s): {', '.join(sorted(missing))}",
                    severity=Severity.MEDIUM,
                    category=Category.B,
                    current_value=f"Missing: {', '.join(sorted(missing))}",
                    expected_value=f"All sections: {', '.join(sorted(REQUIRED_SECTIONS))}",
                ))
        return findings

    def _check_numbering(self, rfc_files: list[FileNode]) -> list[Finding]:
        findings: list[Finding] = []
        seen: dict[str, list[FileNode]] = {}

        for f in rfc_files:
            m = RFC_FILENAME_RE.match(f.filename)
            if m:
                rfc_id = f"RFC-{m.group(1)}"
                seen.setdefault(rfc_id, []).append(f)
                continue
            try:
                with open(f.abs_path, "r", errors="replace") as fh:
                    content = fh.read(2000)
            except Exception:
                continue
            h1_match = RFC_H1_RE.search(content)
            if h1_match:
                rfc_id = f"RFC-{h1_match.group(1)}"
                seen.setdefault(rfc_id, []).append(f)

        for rfc_id, files in seen.items():
            if len(files) > 1:
                paths = ", ".join(f.rel_path for f in files)
                findings.append(self._make_finding(
                    rule_id="RFC-003",
                    file=files[0].rel_path,
                    description=f"Duplicate RFC ID: {rfc_id}",
                    severity=Severity.HIGH,
                    category=Category.A,
                    current_value=f"Files: {paths}",
                    expected_value=f"Single file for {rfc_id}",
                ))

        numbers: list[int] = []
        for rfc_id in seen:
            m = re.match(r"RFC-(\d+)", rfc_id)
            if m:
                numbers.append(int(m.group(1)))

        if numbers:
            numbers.sort()
            gaps: list[str] = []
            for i in range(numbers[0], numbers[-1] + 1):
                if i not in numbers:
                    gaps.append(f"RFC-{i:03d}")
            if gaps:
                last_file = [f for f in rfc_files if RFC_FILENAME_RE.match(f.filename)]
                target_file = last_file[-1].rel_path if last_file else rfc_files[0].rel_path if rfc_files else "unknown"
                findings.append(self._make_finding(
                    rule_id="RFC-003",
                    file=target_file,
                    description=f"Gaps in RFC numbering: {', '.join(gaps)}",
                    severity=Severity.LOW,
                    category=Category.B,
                    current_value=f"Numbers present: {', '.join(f'RFC-{n:03d}' for n in numbers)}",
                    expected_value=f"Sequential from RFC-{numbers[0]:03d} to RFC-{numbers[-1]:03d}",
                ))

        return findings

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
