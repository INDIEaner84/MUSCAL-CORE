from __future__ import annotations

import os
import re
import sys
from typing import Any

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, Finding, FindingSet, FindingStatus, Severity
from reconciliation.core.rule import Rule
from reconciliation.scanner import ScannerBase
from reconciliation.snapshot.file_node import FileNode
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot

IMPORT_RE = re.compile(r"^(?:from\s+(\S+)\s+import|\s*import\s+(\S+))", re.MULTILINE)
WILDCARD_RE = re.compile(r"from\s+\S+\s+import\s+\*")

CORE_MODULES = {
    "api_server", "boot_manager", "bridge", "chat_compiler", "cognitive_diff",
    "compiler_state", "compiler_updater", "compiler_validator", "compiler_version",
    "config", "dashboard", "debugger", "event_bus", "feedback", "graph", "kernel",
    "kernel_diff_engine", "loop_controller", "main", "main_boot", "mel", "memory",
    "mkc", "mkc_rules", "muscal_loop", "muscal_os", "os_config", "plugin_loader",
    "plugin_registry", "rag", "schema", "sphere", "system_runtime", "tools",
    "trace_engine",
}
CORE_PREFIXES = {
    "runtime.api", "runtime.kernel", "runtime.llm", "runtime.observation",
    "runtime.optimizer", "runtime.services", "guards", "spec",
}


def _sanitize(s: str, max_len: int = 30) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)[:max_len]


def _get_stdlib_modules() -> set[str]:
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)
    return set()


def _parse_requirements(req_file: FileNode | None) -> set[str]:
    if req_file is None:
        return set()
    try:
        with open(req_file.abs_path, "r") as f:
            lines = f.read().splitlines()
    except Exception:
        return set()
    pkgs: set[str] = set()
    for line in lines:
        line = line.split("#")[0].strip()
        if not line:
            continue
        m = re.match(r"^([a-zA-Z0-9_.-]+)", line)
        if m:
            pkgs.add(m.group(1).lower().replace("-", "_"))
    return pkgs


def _extract_imports(content: str) -> list[dict[str, Any]]:
    imports: list[dict[str, Any]] = []
    for match in IMPORT_RE.finditer(content):
        module_part = match.group(1) or match.group(2)
        imports.append({
            "statement": match.group(0).strip(),
            "module": module_part,
            "base_module": module_part.split(".")[0],
        })
    return imports


class ImportValidatorScanner(ScannerBase):
    def __init__(self) -> None:
        self._stdlib = _get_stdlib_modules()

    @property
    def name(self) -> str:
        return "import_validator_scanner"

    @property
    def rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="IMP-IR-001",
                description="Every import must resolve to an existing module",
                severity=Severity.HIGH,
                category=Category.B,
            ),
            Rule(
                rule_id="IMP-IR-002",
                description="Plugin code must not import core modules",
                severity=Severity.HIGH,
                category=Category.B,
            ),
            Rule(
                rule_id="IMP-IR-003",
                description="Third-party imports must be declared in requirements.txt",
                severity=Severity.MEDIUM,
                category=Category.B,
            ),
            Rule(
                rule_id="IMP-IR-005",
                description="Wildcard imports are prohibited",
                severity=Severity.LOW,
                category=Category.B,
            ),
        ]

    def scan(self, context: ScanContext) -> FindingSet:
        snapshot = context.snapshot
        if snapshot is None:
            return FindingSet(scanner=self.name, findings=[])

        req_file = snapshot.file_node_for("requirements.txt")
        third_party = _parse_requirements(req_file)

        py_files = snapshot.glob("**/*.py")
        findings: list[Finding] = []

        for py_file in py_files:
            if py_file.rel_path.startswith("__pycache__"):
                continue
            try:
                with open(py_file.abs_path, "r", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            imports = _extract_imports(content)
            for imp in imports:
                findings.extend(self._check_import(imp, py_file, snapshot, third_party))

            for wc_match in WILDCARD_RE.finditer(content):
                line_num = content[: wc_match.start()].count("\n") + 1
                findings.append(self._make_finding(
                    rule_id="IMP-IR-005",
                    file=py_file.rel_path,
                    description="Wildcard import detected",
                    severity=Severity.LOW,
                    category=Category.B,
                    current_value=wc_match.group(0),
                    expected_value="Explicit imports only",
                    line=line_num,
                ))

        return FindingSet(scanner=self.name, findings=findings)

    def _check_import(
        self,
        imp: dict[str, Any],
        py_file: FileNode,
        snapshot: RepositorySnapshot,
        third_party: set[str],
    ) -> list[Finding]:
        findings: list[Finding] = []
        base = imp["base_module"]
        module = imp["module"]

        if base in self._stdlib:
            return findings

        if base in third_party:
            return findings

        if self._is_project_module(module, snapshot):
            findings.extend(self._check_core_isolation(module, py_file))
            return findings

        if self._import_exists_in_snapshot(module, snapshot):
            return findings

        findings.append(self._make_finding(
            rule_id="IMP-IR-001",
            file=py_file.rel_path,
            description=f"Import '{imp['statement']}' does not resolve",
            severity=Severity.HIGH,
            category=Category.B,
            current_value=imp["statement"],
            expected_value="Existing module",
        ))

        if base not in self._stdlib | third_party | self._known_project_base_modules(snapshot):
            findings.append(self._make_finding(
                rule_id="IMP-IR-003",
                file=py_file.rel_path,
                description=f"Third-party import '{base}' not in requirements.txt",
                severity=Severity.MEDIUM,
                category=Category.B,
                current_value=f"Missing: {base}",
                expected_value="Declared in requirements.txt or stdlib",
            ))

        return findings

    def _check_core_isolation(
        self,
        module: str,
        py_file: FileNode,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if not py_file.rel_path.startswith("features/"):
            return findings
        base = module.split(".")[0]
        if base in CORE_MODULES:
            findings.append(self._make_finding(
                rule_id="IMP-IR-002",
                file=py_file.rel_path,
                description=f"Plugin imports core module: {module}",
                severity=Severity.HIGH,
                category=Category.B,
                current_value=f"Import: {module}",
                expected_value="Use hook API instead of direct core import",
            ))
        for prefix in CORE_PREFIXES:
            if module.startswith(prefix):
                findings.append(self._make_finding(
                    rule_id="IMP-IR-002",
                    file=py_file.rel_path,
                    description=f"Plugin imports core namespace: {module}",
                    severity=Severity.HIGH,
                    category=Category.B,
                    current_value=f"Import: {module}",
                    expected_value="Use hook API instead of direct core import",
                ))
        return findings

    @staticmethod
    def _is_project_module(module: str, snapshot: RepositorySnapshot) -> bool:
        base = module.split(".")[0]
        if base in {"features", "runtime"}:
            return True
        if snapshot.file_node_for(f"{base}.py"):
            return True
        return False

    @staticmethod
    def _import_exists_in_snapshot(module: str, snapshot: RepositorySnapshot) -> bool:
        parts = module.split(".")
        for i in range(len(parts), 0, -1):
            prefix = "/".join(parts[:i])
            for ext in (".py", ""):
                path = f"{prefix}{ext}"
                if snapshot.file_node_for(path):
                    return True
                init_path = f"{prefix}/__init__.py"
                if snapshot.file_node_for(init_path):
                    return True
        return False

    @staticmethod
    def _known_project_base_modules(snapshot: RepositorySnapshot) -> set[str]:
        modules: set[str] = set()
        for fn in snapshot.filter(extension=".py"):
            base = fn.filename.replace(".py", "")
            modules.add(base)
        return modules

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
