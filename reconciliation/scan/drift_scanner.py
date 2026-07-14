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


def _sanitize(s: str, max_len: int = 30) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)[:max_len]


def _read_file(file_node: FileNode | None) -> str:
    if file_node is None:
        return ""
    try:
        with open(file_node.abs_path, "r", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _find_line(content: str, pattern: str) -> int | None:
    for i, line in enumerate(content.split("\n"), 1):
        if pattern in line:
            return i
    return None


class DriftDetectorScanner(ScannerBase):
    @property
    def name(self) -> str:
        return "drift_detector_scanner"

    @property
    def rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="SDR-IR-001",
                description="Pipeline order must be consistent across all docs and code",
                severity=Severity.HIGH,
                category=Category.A,
            ),
            Rule(
                rule_id="SDR-IR-002",
                description="Layer count must be consistent across architecture docs",
                severity=Severity.HIGH,
                category=Category.A,
            ),
            Rule(
                rule_id="SDR-IR-003",
                description="Numeric claims must match actual measurements",
                severity=Severity.HIGH,
                category=Category.A,
            ),
            Rule(
                rule_id="SDR-IR-007",
                description="Test coverage claims must match actual test files",
                severity=Severity.MEDIUM,
                category=Category.B,
            ),
        ]

    def scan(self, context: ScanContext) -> FindingSet:
        snapshot = context.snapshot
        if snapshot is None:
            return FindingSet(scanner=self.name, findings=[])

        findings: list[Finding] = []

        findings.extend(self._check_pipeline_order(snapshot))
        findings.extend(self._check_layer_consistency(snapshot))
        findings.extend(self._check_numeric_claims(snapshot))
        findings.extend(self._check_test_counts(snapshot))

        return FindingSet(scanner=self.name, findings=findings)

    def _check_pipeline_order(
        self, snapshot: RepositorySnapshot
    ) -> list[Finding]:
        findings: list[Finding] = []

        kernel_py = snapshot.file_node_for("kernel.py")
        baseline = snapshot.file_node_for("docs/TECHNICAL_BASELINE.md")
        arch = snapshot.file_node_for("docs/ARCHITECTURE.md")

        baseline_content = _read_file(baseline)
        arch_content = _read_file(arch)

        pipeline_baseline = self._extract_pipeline(
            baseline_content, "Orchestriert:"
        )
        pipeline_arch = self._extract_pipeline(arch_content, "Input")

        if kernel_py:
            kernel_content = _read_file(kernel_py)
            pipeline_kernel = self._extract_pipeline(
                kernel_content, "Orchestrates:"
            )
            pipeline_kernel_detail = self._extract_pipeline(
                kernel_content, "INPUT"
            )

            if pipeline_baseline and pipeline_kernel:
                if pipeline_kernel != pipeline_baseline:
                    line_no = _find_line(kernel_content, "Orchestrates:")
                    findings.append(self._make_finding(
                        rule_id="SDR-IR-001",
                        file="kernel.py",
                        description="Pipeline order in kernel.py docstring differs from TECHNICAL_BASELINE.md",
                        severity=Severity.HIGH,
                        category=Category.A,
                        current_value=f"kernel.py: {pipeline_kernel}",
                        expected_value=f"TECHNICAL_BASELINE.md: {pipeline_baseline}",
                        line=line_no,
                        extra={"source": "kernel.py", "target": "docs/TECHNICAL_BASELINE.md"},
                    ))

            if pipeline_baseline and pipeline_arch:
                if pipeline_baseline != pipeline_arch:
                    findings.append(self._make_finding(
                        rule_id="SDR-IR-001",
                        file="docs/ARCHITECTURE.md",
                        description="Pipeline order in ARCHITECTURE.md differs from TECHNICAL_BASELINE.md",
                        severity=Severity.HIGH,
                        category=Category.A,
                        current_value=f"ARCHITECTURE.md: {pipeline_arch}",
                        expected_value=f"TECHNICAL_BASELINE.md: {pipeline_baseline}",
                        extra={"source": "docs/ARCHITECTURE.md", "target": "docs/TECHNICAL_BASELINE.md"},
                    ))

        return findings

    def _check_layer_consistency(
        self, snapshot: RepositorySnapshot
    ) -> list[Finding]:
        findings: list[Finding] = []

        baseline = snapshot.file_node_for("docs/TECHNICAL_BASELINE.md")
        arch = snapshot.file_node_for("docs/ARCHITECTURE.md")

        baseline_layers = self._count_layer_sections(
            _read_file(baseline), patterns=["L1 ", "L2 ", "L3 ", "L4 ", "L5 ", "L6 ", "L7 "]
        )
        arch_layers = self._count_layer_sections(
            _read_file(arch), patterns=["L1 ", "L2 ", "L3 ", "L4 ", "L5 ", "L6 ", "L7 "]
        )

        arch_content = _read_file(arch)
        arch_perspectives = 0
        m = re.search(r"(\d+)\s*Kernel Perspectives", arch_content)
        if m:
            arch_perspectives = int(m.group(1))

        actual_perspectives = len(re.findall(r"^\| \w+ \|", arch_content, re.MULTILINE)) - 1

        if baseline_layers and arch_layers and baseline_layers != arch_layers:
            findings.append(self._make_finding(
                rule_id="SDR-IR-002",
                file="docs/ARCHITECTURE.md",
                description="Layer count mismatch between architecture docs",
                severity=Severity.HIGH,
                category=Category.A,
                current_value=f"ARCHITECTURE.md: {arch_layers} layers",
                expected_value=f"TECHNICAL_BASELINE.md: {baseline_layers} layers",
            ))

        if arch_perspectives and actual_perspectives and arch_perspectives != actual_perspectives:
            findings.append(self._make_finding(
                rule_id="SDR-IR-002",
                file="docs/ARCHITECTURE.md",
                description=f"Claimed {arch_perspectives} Kernel Perspectives but table shows {actual_perspectives}",
                severity=Severity.HIGH,
                category=Category.A,
                current_value=f"Claimed: {arch_perspectives}",
                expected_value=f"Actual: {actual_perspectives}",
            ))

        return findings

    def _check_numeric_claims(
        self, snapshot: RepositorySnapshot
    ) -> list[Finding]:
        findings: list[Finding] = []

        arch_content = _read_file(snapshot.file_node_for("docs/ARCHITECTURE.md"))
        baseline_content = _read_file(snapshot.file_node_for("docs/TECHNICAL_BASELINE.md"))

        arch_tables = re.search(r"(\d+)\s+Tabellen", arch_content)
        baseline_tables = re.search(r"(\d+)\s+Tabellen", baseline_content)

        if arch_tables and baseline_tables:
            arch_n = int(arch_tables.group(1))
            baseline_n = int(baseline_tables.group(1))
            if arch_n != baseline_n:
                findings.append(self._make_finding(
                    rule_id="SDR-IR-003",
                    file="docs/ARCHITECTURE.md",
                    description=f"ARCHITECTURE.md claims {arch_n} tables but TECHNICAL_BASELINE.md claims {baseline_n}",
                    severity=Severity.HIGH,
                    category=Category.A,
                    current_value=f"ARCHITECTURE.md: {arch_n} Tabellen",
                    expected_value=f"TECHNICAL_BASELINE.md: {baseline_n} Tabellen",
                ))

        kp_baseline = re.search(r"(\d+)\s*Kernel\s*Perspectives", baseline_content, re.IGNORECASE)
        kp_arch = re.search(r"(\d+)\s*Kernel\s*Perspectives", arch_content, re.IGNORECASE)

        return findings

    def _check_test_counts(
        self, snapshot: RepositorySnapshot
    ) -> list[Finding]:
        findings: list[Finding] = []

        test_files = snapshot.glob("**/test_*.py") + snapshot.glob("**/*test*.py")
        test_file_count = len({f.rel_path for f in test_files})

        conftest_files = snapshot.glob("**/conftest.py")
        conftest_count = len(conftest_files)
        total = test_file_count + conftest_count

        project_state = snapshot.file_node_for("docs/PROJECT_STATE.md")
        if project_state:
            ps_content = _read_file(project_state)
            for line in ps_content.split("\n"):
                nums = re.findall(r"(\d+)\s*(?:Test|test|pytest)", line)
                for num_str in nums:
                    claimed = int(num_str)
                    if abs(claimed - total) > 5:
                        findings.append(self._make_finding(
                            rule_id="SDR-IR-007",
                            file="docs/PROJECT_STATE.md",
                            description=f"Project claims {claimed} tests but {total} test files found",
                            severity=Severity.MEDIUM,
                            category=Category.B,
                            current_value=f"Claimed: {claimed} tests",
                            expected_value=f"Actual: {total} test files",
                        ))
                        break

        return findings

    @staticmethod
    def _extract_pipeline(content: str, marker: str) -> str:
        for line in content.split("\n"):
            if marker in line:
                parts = re.split(r"[→➡,]", line.split(marker, 1)[1])
                clean = [p.strip().replace("Input", "").replace("Output", "").strip() for p in parts]
                clean = [c for c in clean if c]
                return " → ".join(clean)
        return ""

    @staticmethod
    def _count_layer_sections(
        content: str, patterns: list[str]
    ) -> int:
        count = 0
        for line in content.split("\n"):
            for pat in patterns:
                if pat in line:
                    count += 1
                    break
        return count

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
        safe = _sanitize(file.replace("/", "_"))
        return Finding(
            finding_id=f"{rule_id}_{safe}",
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
