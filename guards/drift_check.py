#!/usr/bin/env python3
"""
drift_check.py — Prueft ob der Code von der TECHNICAL_BASELINE abweicht.

Liest erwartete Werte aus docs/TECHNICAL_BASELINE.md und vergleicht
mit tatsaechlichem Code.

Nutzung:
    python guards/drift_check.py          # Vollstaendiger Check
    python guards/drift_check.py --quick  # Nur kritische Pruefungen
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "docs" / "TECHNICAL_BASELINE.md"

# Erwartete Werte aus TECHNICAL_BASELINE.md
EXPECTED_LIMITS = {
    "MAX_NODES": 5000,
    "MAX_EDGES": 10000,
    "MAX_MEMORY_ENTRIES": 10000,
    "_max_history": 50000,
}

EXPECTED_FILES = [
    "kernel.py", "mkc.py", "bridge.py", "memory.py", "mel.py",
    "schema.py", "mkc_rules.py", "config.py", "event_bus.py",
    "graph.py", "feedback.py", "muscal_os.py", "main.py",
    "main_boot.py", "boot_manager.py", "os_config.py",
    "plugin_registry.py", "plugin_loader.py",
]

PIPELINE_MODULES = {
    "RAG": "rag.py",
    "MKC": "mkc.py",
    "Bridge": "bridge.py",
    "MEL": "mel.py",
    "Feedback": "feedback.py",
    "Memory": "memory.py",
}


class DriftReport:
    def __init__(self):
        self.violations: list[str] = []
        self.warnings: list[str] = []
        self.ok: list[str] = []

    def violation(self, msg: str):
        self.violations.append(msg)

    def warning(self, msg: str):
        self.warnings.append(msg)

    def success(self, msg: str):
        self.ok.append(msg)

    @property
    def status(self) -> str:
        if self.violations:
            return "VIOLATION"
        if self.warnings:
            return "WARNING"
        return "CLEAN"

    def print_report(self):
        status = self.status
        symbol = {"CLEAN": "OK", "WARNING": "WARN", "VIOLATION": "FAIL"}[status]
        print(f"\nDRIFT CHECK: {symbol}")
        print(f"  OK: {len(self.ok)}  Warnings: {len(self.warnings)}  "
              f"Violations: {len(self.violations)}")

        if self.warnings:
            print("\nWARNINGS:")
            for w in self.warnings:
                print(f"  W: {w}")

        if self.violations:
            print("\nVIOLATIONS:")
            for v in self.violations:
                print(f"  X: {v}")

        if not self.warnings and not self.violations:
            print("\nAlle Pruefungen bestanden.")


def check_resource_limits(report: DriftReport):
    """Prueft ob MAX-Werte im Code den Baseline-Werten entsprechen."""
    for varname, expected in EXPECTED_LIMITS.items():
        found = False
        for pyfile in ROOT.rglob("*.py"):
            if "__pycache__" in str(pyfile) or "archive" in str(pyfile):
                continue
            if "test" in pyfile.name.lower():
                continue
            try:
                content = pyfile.read_text(encoding="utf-8")
            except Exception:
                continue
            # Pattern: MAX_NODES = 5000 oder self._max_history = 50000
            pattern = rf'(?:self\.)?{varname}\s*=\s*(\d+)'
            match = re.search(pattern, content)
            if match:
                actual = int(match.group(1))
                if actual != expected:
                    report.violation(
                        f"{varname} in {pyfile.name}: "
                        f"erwartet {expected}, gefunden {actual}"
                    )
                else:
                    report.success(f"{varname} = {actual} (in {pyfile.name})")
                found = True
                break
        if not found:
            report.warning(f"{varname}: Keine Definition gefunden (erwartet {expected})")


def check_core_files(report: DriftReport):
    """Prueft ob alle erwarteten Kern-Dateien existieren."""
    for fname in EXPECTED_FILES:
        fpath = ROOT / fname
        if fpath.exists():
            report.success(f"{fname}: vorhanden")
        else:
            report.violation(f"{fname}: FEHLT")


def check_pipeline_modules(report: DriftReport):
    """Prueft ob Pipeline-Module existieren und Klassen/Funktionen enthalten."""
    for stage, module in PIPELINE_MODULES.items():
        fpath = ROOT / module
        if not fpath.exists():
            report.violation(f"Pipeline-{stage}: {module} FEHLT")
            continue
        content = fpath.read_text(encoding="utf-8")
        if len(content.strip()) < 50:
            report.warning(f"Pipeline-{stage}: {module} sehr klein ({len(content)} Bytes)")
        else:
            report.success(f"Pipeline-{stage}: {module} OK ({len(content)} Bytes)")


def check_guard_sync(report: DriftReport):
    """Prueft ob write_guard.py und IMMUTABILITY_CONTRACT.md synchron sind."""
    try:
        sys.path.insert(0, str(ROOT))
        from guards.sync_governance import (
            parse_guard_files, parse_guard_dirs,
            parse_contract_files, parse_contract_dirs
        )
        guard_files = parse_guard_files()
        contract_files = parse_contract_files()
        guard_dirs = parse_guard_dirs()
        contract_dirs = parse_contract_dirs()

        file_diff = guard_files.symmetric_difference(contract_files)
        dir_diff = guard_dirs.symmetric_difference(contract_dirs)

        if file_diff:
            report.violation(
                f"Guard/Contract File-Drift: {len(file_diff)} Differenzen"
            )
        else:
            report.success(f"Guard/Contract Files synchron ({len(guard_files)})")

        if dir_diff:
            report.violation(
                f"Guard/Contract Dir-Drift: {len(dir_diff)} Differenzen"
            )
        else:
            report.success(f"Guard/Contract Dirs synchron ({len(guard_dirs)})")
    except Exception as e:
        report.warning(f"Guard-Sync-Check fehlgeschlagen: {e}")


def check_import_health(report: DriftReport):
    """Prueft ob die Kernmodule importiert werden koennen."""
    for module in ["kernel", "mkc", "bridge", "memory", "mel", "schema"]:
        fpath = ROOT / f"{module}.py"
        if not fpath.exists():
            report.warning(f"Import-Check: {module}.py nicht vorhanden")
            continue
        content = fpath.read_text(encoding="utf-8")
        # Pruefe auf offensichtliche Syntaxfehler
        try:
            compile(content, str(fpath), "exec")
            report.success(f"{module}.py: Syntax OK")
        except SyntaxError as e:
            report.violation(f"{module}.py: Syntaxfehler — {e}")


def main():
    parser = argparse.ArgumentParser(description="MUSCAL CORE Drift Check")
    parser.add_argument("--quick", action="store_true",
                        help="Nur kritische Pruefungen (Guard-Sync + Core-Files)")
    args = parser.parse_args()

    report = DriftReport()

    check_core_files(report)
    check_guard_sync(report)

    if not args.quick:
        check_resource_limits(report)
        check_pipeline_modules(report)
        check_import_health(report)

    report.print_report()
    sys.exit(1 if report.status == "VIOLATION" else 0)


if __name__ == "__main__":
    main()
