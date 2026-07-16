#!/usr/bin/env python3
"""MUSCAL CI Baseline Comparison Script.

Compares current reconciliation findings against the approved baseline.
Exit 0 = PASS, Exit 1 = FAIL
"""

from __future__ import annotations

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

BASELINE_PATH = os.path.join(REPO_ROOT, "docs", "audit", "MUSCAL_FINDINGS_BASELINE_v1.0.md")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "audit", "reconciliation_report.md")

KNOWN_FALSE_POSITIVES = {"IMP-IR-001", "IMP-IR-003"}
KNOWN_HISTORICAL_ARCHIVE = {"RFC-001", "RFC-002"}
KNOWN_ACCEPTED_DEBT = {"ADR-CR-004", "IMP-IR-002"}
KNOWN_TRUE_POSITIVES = {"BL-001", "ADR-CR-008", "ADR-CR-010", "SDR-IR-001", "SDR-IR-002", "SDR-IR-003"}
KNOWN_FINDINGS = KNOWN_FALSE_POSITIVES | KNOWN_HISTORICAL_ARCHIVE | KNOWN_ACCEPTED_DEBT | KNOWN_TRUE_POSITIVES

FALSE_POSITIVE_PATH_PATTERNS = [
    re.compile(r"BL-001_.*ADR.?014.?IMPLEM"),
]


def parse_baseline_findings() -> set[str]:
    findings = set()
    if not os.path.exists(BASELINE_PATH):
        print(f"ERROR: Baseline file not found: {BASELINE_PATH}")
        sys.exit(1)
    try:
        with open(BASELINE_PATH, "r") as f:
            content = f.read()
        pattern = re.compile(r"\| (RFC-\d+|IMP-IR-\d+|ADR-CR-\d+|BL-\d+|SDR-IR-\d+)_")
        for match in pattern.finditer(content):
            findings.add(match.group(1))
    except Exception as e:
        print(f"ERROR: Cannot parse baseline: {e}")
        sys.exit(1)
    return findings


def parse_report_findings() -> dict[str, list[str]]:
    scanner_findings: dict[str, list[str]] = {}
    if not os.path.exists(REPORT_PATH):
        print(f"ERROR: Report file not found: {REPORT_PATH}")
        sys.exit(1)
    try:
        with open(REPORT_PATH, "r") as f:
            content = f.read()

        current_scanner = None
        for line in content.split("\n"):
            scanner_match = re.match(r"### (\w+)", line)
            if scanner_match:
                current_scanner = scanner_match.group(1)
                scanner_findings.setdefault(current_scanner, [])

            if current_scanner and "| " in line and "---" not in line:
                finding_match = re.search(r"\| ((?:BL|ADR-CR|IMP-IR|SDR-IR|RFC)-\d+_\S+?) \|", line)
                if finding_match:
                    scanner_findings[current_scanner].append(finding_match.group(1))
    except Exception as e:
        print(f"ERROR: Cannot parse report: {e}")
        sys.exit(1)
    return scanner_findings


def classify_finding(finding_id: str) -> str:
    for pattern in FALSE_POSITIVE_PATH_PATTERNS:
        if pattern.search(finding_id):
            return "FALSE_POSITIVE"

    prefix = finding_id.split("_")[0] if "_" in finding_id else finding_id

    if prefix in KNOWN_FALSE_POSITIVES:
        return "FALSE_POSITIVE"
    if prefix in KNOWN_HISTORICAL_ARCHIVE:
        return "HISTORICAL_ARCHIVE"
    if prefix in KNOWN_ACCEPTED_DEBT:
        return "ACCEPTED_TECHNICAL_DEBT"
    if prefix in KNOWN_TRUE_POSITIVES:
        return "TRUE_POSITIVE"
    return "UNKNOWN"


def run_reconciliation() -> bool:
    try:
        from reconciliation.runner import ReconciliationRunner

        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()

        expected_scanners = {
            "broken_link_scanner",
            "adr_validator_scanner",
            "import_validator_scanner",
            "drift_detector_scanner",
            "rfc_validator_scanner",
        }
        actual_scanners = {r.scanner for r in results}

        if expected_scanners != actual_scanners:
            missing = expected_scanners - actual_scanners
            print(f"ERROR: Missing scanners: {missing}")
            return False

        total = sum(r.count for r in results)
        print(f"Reconciliation complete: {total} findings")
        return True
    except Exception as e:
        print(f"ERROR: Scanner execution failed: {e}")
        return False


def main() -> int:
    print("=== MUSCAL CI Baseline Comparison ===\n")

    if not os.path.exists(BASELINE_PATH):
        print(f"FAIL: Baseline file missing: {BASELINE_PATH}")
        return 1

    print("Step 1: Run reconciliation...")
    if not run_reconciliation():
        print("FAIL: Reconciliation execution failed")
        return 1

    print("\nStep 2: Parse baseline...")
    baseline_findings = parse_baseline_findings()
    print(f"  Baseline has {len(baseline_findings)} rule references")

    print("\nStep 3: Parse current report...")
    current_findings = parse_report_findings()
    total_current = sum(len(f) for f in current_findings.values())
    print(f"  Current report has {total_current} findings")

    print("\nStep 4: Classify findings...")
    new_true_positives = []
    known_count = 0

    for scanner, findings in current_findings.items():
        for finding_id in findings:
            classification = classify_finding(finding_id)

            if classification == "UNKNOWN":
                new_true_positives.append(f"{scanner}: {finding_id} (NEW)")
            else:
                known_count += 1

    print(f"  Known (pass): {known_count}")
    print(f"  New unknown (fail): {len(new_true_positives)}")

    print("\nStep 5: Evaluate...")
    if new_true_positives:
        print("\nFAIL: Unknown findings detected:")
        for tp in new_true_positives:
            print(f"  - {tp}")
        return 1

    print("\nPASS: All findings are known (FP/HA/TD/TP)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
