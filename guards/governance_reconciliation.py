#!/usr/bin/env python3
"""
governance_reconciliation.py — MUSCAL CORE Governance Reconciliation v1.2

Prüft und berichtet über den Zustand der Governance-Struktur:

  1. Dokument-Code-Drift erkennen
  2. Commit-Session-Traceability validieren
  3. Vollständigen Reconciliation Report generieren

Nutzung:
    python guards/governance_reconciliation.py --check-drift
    python guards/governance_reconciliation.py --check-traceability
    python guards/governance_reconciliation.py --report
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────
# Drift Detection
# ──────────────────────────────────────────────

def check_drift_between_docs_and_code() -> list:
    """Prüft ob IMMUTABILITY_CONTRACT.md mit write_guard.py synchron ist."""
    findings = []

    contract = ROOT / "spec" / "IMMUTABILITY_CONTRACT.md"
    write_guard = ROOT / "guards" / "write_guard.py"

    if not contract.exists():
        findings.append({"type": "MISSING", "detail": "IMMUTABILITY_CONTRACT.md not found"})
        return findings
    if not write_guard.exists():
        findings.append({"type": "MISSING", "detail": "write_guard.py not found"})
        return findings

    contract_text = contract.read_text(encoding="utf-8")
    guard_text = write_guard.read_text(encoding="utf-8")

    # Extrahiere CORE_FILES aus write_guard.py
    guard_files = set()
    in_core_files = False
    for line in guard_text.split("\n"):
        if "CORE_FILES = frozenset({" in line:
            in_core_files = True
            continue
        if in_core_files:
            if "})" in line:
                break
            m = re.search(r'"(.+?)"', line)
            if m:
                guard_files.add(m.group(1))

    # Extrahiere CORE_DIRS aus write_guard.py
    guard_dirs = set()
    in_core_dirs = False
    for line in guard_text.split("\n"):
        if "CORE_DIRS = frozenset({" in line:
            in_core_dirs = True
            continue
        if in_core_dirs:
            if "})" in line:
                break
            m = re.search(r'"(.+?)"', line)
            if m:
                guard_dirs.add(m.group(1))

    # Prüfe ob CORE_FILES in Contract erwähnt werden
    for f in sorted(guard_files):
        if f not in contract_text:
            findings.append({
                "type": "DRIFT",
                "detail": f"CORE_FILE '{f}' in write_guard.py but not in IMMUTABILITY_CONTRACT.md",
            })

    # Prüfe ob CORE_DIRS in Contract erwähnt werden
    for d in sorted(guard_dirs):
        if d not in contract_text:
            findings.append({
                "type": "DRIFT",
                "detail": f"CORE_DIR '{d}' in write_guard.py but not in IMMUTABILITY_CONTRACT.md",
            })

    if not findings:
        findings.append({"type": "OK", "detail": "No drift detected between write_guard.py and IMMUTABILITY_CONTRACT.md"})

    return findings


def check_session_handover_coverage() -> list:
    """Prüft ob alle Sessions in SESSION_REGISTRY ein HANDOVER haben."""
    findings = []
    registry = ROOT / "docs" / "SESSION_REGISTRY.md"
    handover_dir = ROOT / "docs" / "session_handovers"

    if not registry.exists():
        findings.append({"type": "MISSING", "detail": "SESSION_REGISTRY.md not found"})
        return findings

    registry_text = registry.read_text(encoding="utf-8")

    # Extrahiere Session IDs aus Registry
    session_ids = set()
    for line in registry_text.split("\n"):
        m = re.search(r"\|\s*(S-\S+?)\s*\|", line)
        if m:
            session_ids.add(m.group(1))

    if not handover_dir.exists():
        findings.append({"type": "MISSING", "detail": "session_handovers/ directory not found"})
        return findings

    handover_files = list(handover_dir.glob("HANDOVER_*.md"))
    handover_ids = set()
    for h in handover_files:
        text = h.read_text(encoding="utf-8")
        m = re.search(r"Session ID:\s*(\S+)", text)
        if m:
            handover_ids.add(m.group(1))

    for sid in sorted(session_ids):
        if sid not in handover_ids:
            findings.append({
                "type": "MISSING_HANDOVER",
                "detail": f"Session {sid} in registry but has no HANDOVER file",
            })

    for hid in sorted(handover_ids):
        if hid not in session_ids:
            findings.append({
                "type": "ORPHAN_HANDOVER",
                "detail": f"Session {hid} in HANDOVER but not in SESSION_REGISTRY",
            })

    if not findings:
        findings.append({"type": "OK", "detail": "All sessions have matching HANDOVER files"})

    return findings


# ──────────────────────────────────────────────
# Traceability Check
# ──────────────────────────────────────────────

def check_commit_session_traceability() -> list:
    """Prüft ob alle Commits via SESSION_HANDOVER oder CHANGE_JOURNAL referenziert sind."""
    findings = []

    try:
        result = subprocess.run(
            ["git", "log", "--format=%H|%s"],
            capture_output=True, text=True, check=True,
            cwd=str(ROOT)
        )
        commits = [line.split("|", 1) for line in result.stdout.strip().split("\n") if line]
    except (subprocess.CalledProcessError, FileNotFoundError):
        findings.append({"type": "ERROR", "detail": "Git not available"})
        return findings

    handover_dir = ROOT / "docs" / "session_handovers"
    handover_texts = ""
    if handover_dir.exists():
        for h in sorted(handover_dir.glob("HANDOVER_*.md")):
            handover_texts += h.read_text(encoding="utf-8")

    journal = ROOT / "docs" / "CHANGE_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8") if journal.exists() else ""

    for h, subject in commits:
        short = h[:7]
        in_handover = short in handover_texts
        in_journal = short in journal_text

        if not in_handover and not in_journal:
            findings.append({
                "type": "UNTRACED_COMMIT",
                "detail": f"Commit {short} ('{subject[:50]}') not found in any HANDOVER or CHANGE_JOURNAL",
            })

    if not findings:
        findings.append({"type": "OK", "detail": "All commits are traceable"})

    return findings


# ──────────────────────────────────────────────
# Report Generator
# ──────────────────────────────────────────────

def generate_reconciliation_report() -> str:
    """Generiert vollständigen Governance Reconciliation Report."""
    lines = []
    lines.append("# GOVERNANCE RECONCILIATION REPORT")
    lines.append(f"**Generated:** 2026-07-13")
    lines.append(f"**Session:** S-2026-07-12-006")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Dokument-Code-Drift
    lines.append("## 1. Dokument-Code-Drift")
    lines.append("")
    drift = check_drift_between_docs_and_code()
    for d in drift:
        if d["type"] == "OK":
            lines.append(f"- ✅ {d['detail']}")
        else:
            lines.append(f"- ❌ **{d['type']}**: {d['detail']}")
    lines.append("")

    # 2. Session Handover Coverage
    lines.append("## 2. Session Handover Coverage")
    lines.append("")
    coverage = check_session_handover_coverage()
    for c in coverage:
        if c["type"] == "OK":
            lines.append(f"- ✅ {c['detail']}")
        elif c["type"] == "MISSING_HANDOVER":
            lines.append(f"- ⚠️ {c['detail']}")
        elif c["type"] == "ORPHAN_HANDOVER":
            lines.append(f"- ⚠️ {c['detail']}")
        else:
            lines.append(f"- ❌ **{c['type']}**: {c['detail']}")
    lines.append("")

    # 3. Commit Traceability
    lines.append("## 3. Commit → Session Traceability")
    lines.append("")
    trace = check_commit_session_traceability()
    for t in trace:
        if t["type"] == "OK":
            lines.append(f"- ✅ {t['detail']}")
        else:
            lines.append(f"- ⚠️ **{t['type']}**: {t['detail']}")
    lines.append("")

    # 4. Governance Dateien Status
    lines.append("## 4. Governance Files Status")
    lines.append("")
    governance_files = [
        "guards/governance_validator.py",
        "guards/governance_evidence.py",
        "guards/governance_reconciliation.py",
        "guards/pre_commit_hook.py",
        "guards/write_guard.py",
        "spec/OVERRIDE.md",
        "docs/LOCK_PROTOCOL.md",
        "docs/TASK_BOARD.md",
        "docs/CHANGE_JOURNAL.md",
        "docs/SESSION_REGISTRY.md",
        ".opencode/SESSION_RULES.md",
        ".github/workflows/governance-check.yml",
    ]
    lines.append("| File | Status |")
    lines.append("|------|--------|")
    for gf in governance_files:
        path = ROOT / gf
        if path.exists():
            lines.append(f"| {gf} | ✅ Present |")
        else:
            lines.append(f"| {gf} | ❌ Missing |")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    total_checks = (
        sum(1 for d in drift if d["type"] == "OK") +
        sum(1 for c in coverage if c["type"] == "OK") +
        sum(1 for t in trace if t["type"] == "OK")
    )
    total_issues = (
        sum(1 for d in drift if d["type"] != "OK") +
        sum(1 for c in coverage if c["type"] != "OK") +
        sum(1 for t in trace if t["type"] != "OK")
    )
    lines.append(f"- Checks passed: {total_checks}")
    lines.append(f"- Issues found: {total_issues}")
    present_files = sum(1 for gf in governance_files if (ROOT / gf).exists())
    lines.append(f"- Governance files: {present_files}/{len(governance_files)} present")
    lines.append(f"- Governance maturity: {present_files}/{len(governance_files)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MUSCAL Governance Reconciliation v1.2")
    parser.add_argument("--check-drift", action="store_true", help="Prüfe Dokument-Code-Drift")
    parser.add_argument("--check-traceability", action="store_true", help="Prüfe Commit Traceability")
    parser.add_argument("--check-coverage", action="store_true", help="Prüfe Session Handover Coverage")
    parser.add_argument("--report", action="store_true", help="Generiere Reconciliation Report")
    args = parser.parse_args()

    if args.check_drift:
        findings = check_drift_between_docs_and_code()
        for f in findings:
            if f["type"] == "OK":
                print(f"✅ {f['detail']}")
            else:
                print(f"⚠️  {f['type']}: {f['detail']}")
        sys.exit(0)

    if args.check_traceability:
        findings = check_commit_session_traceability()
        for f in findings:
            if f["type"] == "OK":
                print(f"✅ {f['detail']}")
            else:
                print(f"⚠️  {f['type']}: {f['detail']}")
        sys.exit(0)

    if args.check_coverage:
        findings = check_session_handover_coverage()
        for f in findings:
            if f["type"] == "OK":
                print(f"✅ {f['detail']}")
            else:
                print(f"⚠️  {f['type']}: {f['detail']}")
        sys.exit(0)

    if args.report:
        report_path = ROOT / "docs" / "governance" / "GOVERNANCE_RECONCILIATION_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = generate_reconciliation_report()
        report_path.write_text(markdown, encoding="utf-8")
        print(f"Report generated: {report_path}")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
