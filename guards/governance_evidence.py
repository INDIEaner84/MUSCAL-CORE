#!/usr/bin/env python3
"""
governance_evidence.py — MUSCAL CORE Governance Evidence Layer v1.2

Erfasst, verknüpft und validiert Evidence für Änderungen:

  1. CHANGE Evidence Mapping
  2. Commit → Session Traceability
  3. ADR → Change Validation
  4. Test Evidence Tracking

Nutzung:
    python guards/governance_evidence.py --map [files...]
    python guards/governance_evidence.py --trace <commit_hash>
    python guards/governance_evidence.py --adr-check [files...]
    python guards/governance_evidence.py --test-evidence [files...]
    python guards/governance_evidence.py --report [files...]
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────
# CHANGE Evidence Mapping
# ──────────────────────────────────────────────

def find_adrs_for_file(file: str) -> list:
    """Findet ADRs die zu einer Datei passen."""
    adrs = sorted(ROOT.glob("spec/ADR-*.md"))
    results = []
    file_lower = file.lower()
    for adr in adrs:
        text = adr.read_text(encoding="utf-8", errors="ignore")
        if file_lower in text.lower():
            # Extrahiere ADR-Nummer aus Dateinamen
            m = re.search(r"ADR-(\d+)", adr.name)
            if m:
                results.append({
                    "adr": f"ADR-{m.group(1)}",
                    "file": adr.name,
                    "path": str(adr.relative_to(ROOT)),
                })
    return results


def find_session_handover_for_file(file: str) -> list:
    """Findet SESSION_HANDOVER die eine Datei referenzieren."""
    handovers = sorted(ROOT.glob("docs/session_handovers/HANDOVER_*.md"))
    results = []
    for h in handovers:
        text = h.read_text(encoding="utf-8", errors="ignore")
        if file in text:
            m = re.search(r"Session ID:\s*(\S+)", text)
            session_id = m.group(1) if m else "unknown"
            results.append({
                "session_id": session_id,
                "file": h.name,
                "path": str(h.relative_to(ROOT)),
            })
    return results


def find_tests_for_file(file: str) -> list:
    """Findet Tests die zu einer Datei passen (test_<name>.py)."""
    basename = os.path.splitext(os.path.basename(file))[0]
    test_patterns = [
        f"tests/test_{basename}.py",
        f"tests/test_{basename}_*.py",
        f"tests/*/test_{basename}.py",
    ]
    results = []
    for pattern in test_patterns:
        matches = sorted(ROOT.glob(pattern))
        for m in matches:
            results.append(str(m.relative_to(ROOT)))
    return results


def map_change_to_evidence(file: str) -> dict:
    """Vollständiges Evidence Mapping für eine Datei."""
    return {
        "file": file,
        "adrs": find_adrs_for_file(file),
        "handovers": find_session_handover_for_file(file),
        "tests": find_tests_for_file(file),
    }


# ──────────────────────────────────────────────
# Commit → Session Traceability
# ──────────────────────────────────────────────

def get_commits(limit: int = 20) -> list:
    """Holt die letzten Commits aus Git."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}",
             "--format=%H|%h|%ci|%s"],
            capture_output=True, text=True, check=True,
            cwd=str(ROOT)
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "short": parts[1],
                    "date": parts[2],
                    "subject": parts[3],
                })
        return commits
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def get_commit_files(commit_hash: str) -> list:
    """Holt die Dateien eines Commits."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "-r", "--name-only",
             "-r", commit_hash],
            capture_output=True, text=True, check=True,
            cwd=str(ROOT)
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def trace_commit_to_session(commit_hash: str) -> str | None:
    """Findet Session ID für einen Commit via git log + HANDOVER Suche."""
    files = get_commit_files(commit_hash)
    session_ids = set()
    for f in files:
        handovers = find_session_handover_for_file(f)
        for h in handovers:
            session_ids.add(h["session_id"])

    if session_ids:
        return ", ".join(sorted(session_ids))
    return None


def get_session_for_commit_from_message(commit_hash: str) -> str | None:
    """Extrahiert Session ID aus Commit Message (via CHANGE_JOURNAL)."""
    journal = ROOT / "docs" / "CHANGE_JOURNAL.md"
    if not journal.exists():
        return None
    text = journal.read_text(encoding="utf-8")
    if commit_hash[:7] in text:
        m = re.search(r"\|.*?\| (S-\S+) \|", text)
        if m:
            return m.group(1)
    return None


# ──────────────────────────────────────────────
# ADR → Change Validation
# ──────────────────────────────────────────────

def load_adr_index() -> list:
    """Lädt ADR-INDEX.md und parst die Tabelle."""
    index = ROOT / "spec" / "ADR-INDEX.md"
    if not index.exists():
        return []
    text = index.read_text(encoding="utf-8")
    adrs = []
    in_table = False
    for line in text.split("\n"):
        if "| ---" in line:
            in_table = True
            continue
        if in_table and line.startswith("| ADR-"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                adrs.append({
                    "id": parts[0],
                    "title": parts[1].split("](")[0].replace("[", ""),
                    "status": parts[2] if len(parts) > 2 else "UNKNOWN",
                })
    return adrs


def find_adr_for_change(file: str) -> list:
    """Findet ADRs die für eine Änderung relevant sind."""
    return find_adrs_for_file(file)


def validate_adr_compliance(files: list) -> list:
    """Validiert dass Änderungen durch ADRs abgedeckt sind."""
    results = []
    for f in files:
        adrs = find_adr_for_change(f)
        results.append({
            "file": f,
            "adrs": adrs,
            "compliant": len(adrs) > 0 or f.endswith(".md"),
        })
    return results


# ──────────────────────────────────────────────
# Test Evidence Tracking
# ──────────────────────────────────────────────

def track_test_evidence(files: list) -> list:
    """Findet Test-Evidence für eine Liste von Dateien."""
    results = []
    for f in files:
        tests = find_tests_for_file(f)
        results.append({
            "file": f,
            "tests": tests,
            "has_tests": len(tests) > 0,
        })
    return results


# ──────────────────────────────────────────────
# Report Generator
# ──────────────────────────────────────────────

def generate_evidence_report(files: list, commit_hash: str = None) -> str:
    """Generiert vollständigen Evidence Report als Markdown."""
    lines = []
    lines.append("# GOVERNANCE EVIDENCE REPORT")
    lines.append(f"**Generated:** 2026-07-13")
    lines.append(f"**Session:** S-2026-07-12-006")
    if commit_hash:
        lines.append(f"**Commit:** {commit_hash}")
    lines.append("")

    # Commit → Session Traceability
    lines.append("## 1. Commit → Session Traceability")
    lines.append("")
    commits = get_commits(3)
    if commits:
        lines.append("| Commit | Short | Date | Session | Subject |")
        lines.append("|--------|-------|------|---------|---------|")
        for c in commits:
            session = trace_commit_to_session(c["hash"]) or get_session_for_commit_from_message(c["hash"]) or "—"
            lines.append(f"| {c['hash']} | {c['short']} | {c['date']} | {session} | {c['subject']} |")
    else:
        lines.append("*No commits found*")
    lines.append("")

    # CHANGE Evidence Mapping
    lines.append("## 2. CHANGE Evidence Mapping")
    lines.append("")
    lines.append("| File | ADRs | Handovers | Tests |")
    lines.append("|------|------|-----------|-------|")
    for f in files:
        ev = map_change_to_evidence(f)
        adr_str = ", ".join(a["adr"] for a in ev["adrs"]) if ev["adrs"] else "—"
        hand_str = ", ".join(h["session_id"] for h in ev["handovers"]) if ev["handovers"] else "—"
        test_str = ", ".join(ev["tests"]) if ev["tests"] else "—"
        lines.append(f"| {f} | {adr_str} | {hand_str} | {test_str} |")
    lines.append("")

    # ADR → Change Validation
    lines.append("## 3. ADR → Change Validation")
    lines.append("")
    adr_results = validate_adr_compliance(files)
    for r in adr_results:
        if r["compliant"]:
            lines.append(f"- ✅ {r['file']}: {', '.join(a['adr'] for a in r['adrs']) if r['adrs'] else 'Doc-only'}")
        else:
            lines.append(f"- ⚠️ {r['file']}: No ADR found")
    lines.append("")

    # Test Evidence Tracking
    lines.append("## 4. Test Evidence Tracking")
    lines.append("")
    test_results = track_test_evidence(files)
    for r in test_results:
        if r["has_tests"]:
            lines.append(f"- ✅ {r['file']}: {', '.join(r['tests'])}")
        else:
            lines.append(f"- ⚠️ {r['file']}: No tests found")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total files: {len(files)}")
    adr_compliant = sum(1 for r in adr_results if r["compliant"])
    lines.append(f"- ADR compliant: {adr_compliant}/{len(adr_results)}")
    test_covered = sum(1 for r in test_results if r["has_tests"])
    lines.append(f"- Test coverage: {test_covered}/{len(test_results)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MUSCAL Governance Evidence Layer v1.2")
    parser.add_argument("--map", nargs="*", default=None, help="Evidence Mapping für Dateien")
    parser.add_argument("--trace", type=str, default=None, help="Trace Commit zu Session")
    parser.add_argument("--adr-check", nargs="*", default=None, help="ADR Compliance Check")
    parser.add_argument("--test-evidence", nargs="*", default=None, help="Test Evidence Tracking")
    parser.add_argument("--report", nargs="*", default=None, help="Generiere Evidence Report")
    parser.add_argument("--commit-hash", type=str, default=None, help="Commit Hash für Report")
    args = parser.parse_args()

    if args.map is not None:
        print(f"{'File':<50} {'ADRs':<30} {'Handovers':<20} {'Tests'}")
        print("-" * 120)
        for f in args.map:
            ev = map_change_to_evidence(f)
            adr_str = ", ".join(a["adr"] for a in ev["adrs"])[:28]
            hand_str = ", ".join(h["session_id"] for h in ev["handovers"])[:18]
            test_str = ", ".join(ev["tests"])[:30]
            print(f"{f:<50} {adr_str:<30} {hand_str:<20} {test_str}")
        sys.exit(0)

    if args.trace:
        session = trace_commit_to_session(args.trace) or get_session_for_commit_from_message(args.trace) or "No session found"
        print(f"Commit {args.trace[:7]} → Session: {session}")
        sys.exit(0)

    if args.adr_check is not None:
        results = validate_adr_compliance(args.adr_check)
        for r in results:
            status = "✅" if r["compliant"] else "⚠️"
            adrs = ", ".join(a["adr"] for a in r["adrs"]) if r["adrs"] else "No ADR"
            print(f"{status} {r['file']}: {adrs}")
        sys.exit(0)

    if args.test_evidence is not None:
        results = track_test_evidence(args.test_evidence)
        for r in results:
            status = "✅" if r["has_tests"] else "⚠️"
            tests = ", ".join(r["tests"]) if r["tests"] else "No tests"
            print(f"{status} {r['file']}: {tests}")
        sys.exit(0)

    if args.report is not None:
        files = args.report
        report_path = ROOT / "docs" / "governance" / "GOVERNANCE_EVIDENCE_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = generate_evidence_report(files, commit_hash=args.commit_hash)
        report_path.write_text(markdown, encoding="utf-8")
        print(f"Report generated: {report_path}")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
