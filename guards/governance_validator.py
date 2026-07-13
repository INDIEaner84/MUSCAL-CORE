#!/usr/bin/env python3
"""
governance_validator.py — MUSCAL CORE Governance Enforcement Layer v1.1

Klassifiziert geänderte Dateien nach Lock Level (0-3),
validiert gegen Governance-Regeln und erzeugt Reports.

Nutzung:
    python guards/governance_validator.py --classify [files...]
    python guards/governance_validator.py --validate [files...]
    python guards/governance_validator.py --check-handover
    python guards/governance_validator.py --report [files...]
    python guards/governance_validator.py --pre-commit
"""

import argparse
import glob as glob_mod
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────
# Lock Level Definitionen
# ──────────────────────────────────────────────

LEVEL_0_DOCS = {"docs/", "spec/", ".opencode/"}
LEVEL_0_EXT = {".md"}

LEVEL_1_FEATURES = {"features/", "tests/"}

LEVEL_2_INFRA = {
    "guards/",
    ".github/",
    "runtime/monitoring/",
    "runtime/services/",
    ".pre-commit-config.yaml",
}

LEVEL_3_CORE_FILES = {
    "kernel.py", "config.py", "event_bus.py",
    "muscal_os.py", "plugin_loader.py", "plugin_registry.py",
}

LEVEL_3_CORE_DIRS = {
    "runtime/kernel/", "runtime/llm/",
    "runtime/optimizer/", "runtime/api/",
}

OVERRIDE_052_PATHS = {"guards/", ".github/", ".pre-commit-config.yaml"}


class ValidationReport:
    def __init__(self):
        self.violations = []
        self.warnings = []
        self.passed = []

    def has_violations(self) -> bool:
        return len(self.violations) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def all_pass(self) -> bool:
        return not self.has_violations() and not self.has_warnings()


def classify_file(path: str) -> tuple:
    """Gibt (lock_level, kategorie) zurueck."""
    p = path.replace("\\", "/")

    # Level 3 — Core (hoechste Prioritaet)
    if p in LEVEL_3_CORE_FILES:
        return (3, "Core")
    for d in LEVEL_3_CORE_DIRS:
        if p.startswith(d):
            return (3, "Core")

    # Level 2 — Infrastructure
    if p in LEVEL_2_INFRA:
        return (2, "Infrastructure")
    for d in LEVEL_2_INFRA:
        if p.startswith(d):
            return (2, "Infrastructure")

    # Level 1 — Feature
    for d in LEVEL_1_FEATURES:
        if p.startswith(d):
            return (1, "Feature")

    # Level 0 — Documentation
    ext = os.path.splitext(p)[1]
    if ext in LEVEL_0_EXT:
        return (0, "Documentation")
    for d in LEVEL_0_DOCS:
        if p.startswith(d):
            return (0, "Documentation")

    # Fallback — unbekannt (wird als Level 0 behandelt)
    return (0, "Unknown")


def is_core_file_level3(path: str) -> bool:
    """Prueft ob eine Datei ein Core File (Level 3) ist."""
    level, _ = classify_file(path)
    return level == 3


def is_override_052_path(path: str) -> bool:
    """Prueft ob path von OVERRIDE-052 abgedeckt wird."""
    p = path.replace("\\", "/")
    if p in OVERRIDE_052_PATHS:
        return True
    for d in OVERRIDE_052_PATHS:
        if p.startswith(d):
            return True
    return False


def override_052_is_active() -> bool:
    """Prueft ob OVERRIDE-052 aktiv ist (Status APPROVED oder APPLIED)."""
    override = ROOT / "spec" / "OVERRIDE.md"
    if not override.exists():
        return False
    text = override.read_text(encoding="utf-8")
    if "OVERRIDE-052" not in text:
        return False
    return "**Status:** APPROVED" in text or "**Status:** APPLIED" in text


def check_override_scope(files: list) -> str:
    """
    Prueft ob Aenderungen durch OVERRIDE-052 abgedeckt sind.

    Rueckgabe:
        "ALLOW_INFRA" — guards/, .github/, .pre-commit-config.yaml + beliebige Level 0
        "BLOCK"       — Core Files im Changeset
        "NONE"        — OVERRIDE-052 nicht aktiv oder nicht betroffen
    """
    if not override_052_is_active():
        return "NONE"

    has_override_path = any(is_override_052_path(f) for f in files)
    if not has_override_path:
        return "NONE"

    # Core files sind IMMER blockiert (OVERRIDE-052 deckt sie nicht)
    for f in files:
        if is_core_file_level3(f):
            return "BLOCK"

    # Nicht-OVERRIDE Dateien muessen Level 0 sein (dokumentation)
    for f in files:
        if not is_override_052_path(f):
            level, _ = classify_file(f)
            if level > 0:
                return "BLOCK"

    return "ALLOW_INFRA"


def check_task_board_entry(filename: str) -> str:
    """Prueft ob ein TASK_BOARD Eintrag fuer die Datei existiert."""
    task_board = ROOT / "docs" / "TASK_BOARD.md"
    if not task_board.exists():
        return "TASK_BOARD not found"
    text = task_board.read_text(encoding="utf-8")
    if filename in text:
        return None
    return f"No TASK_BOARD entry for {filename}"


def check_session_handover(files: list) -> str:
    """Prueft ob SESSION_HANDOVER fuer Level 2+ Aenderungen vorhanden ist."""
    max_level = 0
    for f in files:
        level, _ = classify_file(f)
        if level > max_level:
            max_level = level

    if max_level < 2:
        return None

    handovers = list(ROOT.glob("docs/session_handovers/HANDOVER_*.md"))
    if not handovers:
        return "WARNING: Level 2+ changes without SESSION_HANDOVER"
    return None


def validate_staged_files(files: list) -> ValidationReport:
    """Validiert alle Dateien gegen Lock Level Anforderungen."""
    report = ValidationReport()

    for f in files:
        level, category = classify_file(f)
        entry = {"file": f, "level": level, "category": category}

        if level == 0:
            entry["approval"] = "None"
            entry["status"] = "PASS"
            report.passed.append(entry)

        elif level == 1:
            warning = check_task_board_entry(f)
            entry["approval"] = "Review"
            if warning:
                entry["status"] = "WARN"
                entry["message"] = warning
                report.warnings.append(entry)
            else:
                entry["status"] = "PASS"
                report.passed.append(entry)

        elif level == 2:
            entry["approval"] = "Architecture Review"
            warning = check_task_board_entry(f)
            if warning:
                entry["status"] = "WARN"
                entry["message"] = warning
                report.warnings.append(entry)
            else:
                handover = check_session_handover(files)
                if handover:
                    entry["status"] = "WARN"
                    entry["message"] = handover
                    report.warnings.append(entry)
                else:
                    entry["status"] = "PASS"
                    report.passed.append(entry)

        elif level == 3:
            entry["approval"] = "ADR Required"
            entry["status"] = "BLOCKED"
            entry["message"] = f"Core file {f}: requires ADR + OVERRIDE + --allow-core-write"
            report.violations.append(entry)

    return report


def generate_markdown_report(files: list) -> str:
    """Generiert einen Markdown Report der Klassifikation und Validierung."""
    report = validate_staged_files(files)

    lines = []
    lines.append("# CHANGE CLASSIFICATION REPORT")
    lines.append(f"**Generated:** 2026-07-12")
    lines.append(f"**Session:** S-2026-07-12-005")
    lines.append("")
    lines.append("| Datei | Lock Level | Kategorie | Approval | Status |")
    lines.append("|-------|------------|-----------|----------|--------|")

    for entry in report.violations:
        status = f"❌ {entry['status']}"
        msg = f" ({entry.get('message', '')})" if entry.get('message') else ""
        lines.append(f"| {entry['file']} | {entry['level']} | {entry['category']} | {entry['approval']} | {status}{msg} |")

    for entry in report.warnings:
        status = f"⚠️ {entry['status']}"
        msg = f" ({entry.get('message', '')})" if entry.get('message') else ""
        lines.append(f"| {entry['file']} | {entry['level']} | {entry['category']} | {entry['approval']} | {status}{msg} |")

    for entry in report.passed:
        lines.append(f"| {entry['file']} | {entry['level']} | {entry['category']} | {entry['approval']} | ✅ {entry['status']} |")

    lines.append("")
    lines.append("## Summary")
    lines.append(f"")
    lines.append(f"- Total files: {len(files)}")
    lines.append(f"- Passed: {len(report.passed)}")
    lines.append(f"- Warnings: {len(report.warnings)}")
    lines.append(f"- Violations: {len(report.violations)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MUSCAL Governance Validator")
    parser.add_argument("--classify", nargs="*", default=None, help="Klassifiziere Dateien nach Lock Level")
    parser.add_argument("--validate", nargs="*", default=None, help="Validiere Dateien gegen Lock Regeln")
    parser.add_argument("--check-handover", action="store_true", help="Pruefe SESSION_HANDOVER Existenz")
    parser.add_argument("--report", nargs="*", default=None, help="Generiere CHANGE_CLASSIFICATION_REPORT.md")
    parser.add_argument("--pre-commit", action="store_true", help="Pre-Commit Hook (liest staged files aus git)")
    parser.add_argument("--evidence", nargs="*", default=None, help="Evidence Check via governance_evidence.py")
    parser.add_argument("--reconcile", action="store_true", help="Reconciliation Check via governance_reconciliation.py")
    args = parser.parse_args()

    files = []

    if args.pre_commit:
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=False,
            cwd=str(ROOT)
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    elif args.classify is not None:
        files = args.classify
    elif args.validate is not None:
        files = args.validate
    elif args.report is not None:
        files = args.report
    elif args.evidence is not None:
        files = args.evidence
    elif args.check_handover:
        pass
    else:
        parser.print_help()
        sys.exit(0)

    if args.classify is not None:
        print(f"{'File':<50} {'Level':<6} {'Category'}")
        print("-" * 70)
        for f in files:
            level, cat = classify_file(f)
            print(f"{f:<50} {level:<6} {cat}")
        sys.exit(0)

    if args.validate is not None or args.pre_commit:
        report = validate_staged_files(files)
        if report.has_violations():
            print("GOVERNANCE VALIDATION FAILED")
            print("=" * 50)
            for v in report.violations:
                print(f"❌ BLOCKED: {v['file']} ({v['category']} Level {v['level']})")
                print(f"   {v.get('message', '')}")
            sys.exit(1)
        if report.has_warnings():
            print("GOVERNANCE VALIDATION PASSED WITH WARNINGS")
            print("=" * 50)
            for w in report.warnings:
                print(f"⚠️  {w['file']}: {w.get('message', '')}")
        else:
            print("GOVERNANCE VALIDATION PASSED")
        sys.exit(0)

    if args.check_handover:
        result = check_session_handover(files if files else [])
        if result:
            print(result)
            sys.exit(1)
        else:
            print("SESSION_HANDOVER check passed")
            sys.exit(0)

    if args.report is not None:
        report_path = ROOT / "docs" / "governance" / "CHANGE_CLASSIFICATION_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = generate_markdown_report(files)
        report_path.write_text(markdown, encoding="utf-8")
        print(f"Report generated: {report_path}")
        sys.exit(0)

    if args.evidence is not None:
        from guards.governance_evidence import generate_evidence_report
        files = args.evidence
        report_path = ROOT / "docs" / "governance" / "GOVERNANCE_EVIDENCE_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = generate_evidence_report(files)
        report_path.write_text(markdown, encoding="utf-8")
        print(f"Evidence report generated: {report_path}")
        sys.exit(0)

    if args.reconcile:
        from guards.governance_reconciliation import generate_reconciliation_report
        report_path = ROOT / "docs" / "governance" / "GOVERNANCE_RECONCILIATION_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = generate_reconciliation_report()
        report_path.write_text(markdown, encoding="utf-8")
        print(f"Reconciliation report generated: {report_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
