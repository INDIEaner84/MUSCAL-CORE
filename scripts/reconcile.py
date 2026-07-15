#!/usr/bin/env python3
"""MUSCAL Governance Reconciliation CLI Entry Point."""

from __future__ import annotations

import datetime
import json
import os
import sys


def main() -> None:
    repo_root = _find_repo_root()
    sys.path.insert(0, repo_root)

    output_path = os.path.join(repo_root, "docs", "audit", "reconciliation_report.md")

    from reconciliation.runner import ReconciliationRunner
    from reconciliation.report import ReportGenerator

    runner = ReconciliationRunner(repo_root)
    runner.register_defaults()

    print(f"Repository: {repo_root}")
    print(f"Scanners: {len(runner.scanners)}")
    print(f"Running reconciliation...")

    results = runner.run_all()

    total_findings = sum(fs.count for fs in results)
    print(f"Findings: {total_findings}")

    gen = ReportGenerator()
    summary = gen.build_summary(results)

    report_md = _build_report(repo_root, results, summary)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report_md)

    print(f"Report: {output_path}")
    print("DONE")


def _find_repo_root() -> str:
    candidate = os.path.abspath(".")
    for _ in range(10):
        if os.path.isfile(os.path.join(candidate, "pyproject.toml")):
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    return os.path.abspath(".")


def _build_report(repo_root: str, results: list, summary: dict) -> str:
    today = datetime.datetime.now().isoformat()
    repo_name = os.path.basename(repo_root)

    lines = [
        "# MUSCAL Reconciliation Report",
        "",
        "## Execution Metadata",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Timestamp | {today} |",
        f"| Repository | {repo_name} |",
        f"| Root | `{repo_root}` |",
        f"| Scanners | {summary['scanners']} |",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Findings | {summary['total_findings']} |",
        "",
        "### By Category",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    for cat in ["A", "B", "C", "D"]:
        lines.append(f"| {cat} | {summary['categories'][cat]} |")

    lines += [
        "",
        "### By Severity",
        "",
        "| Severity | Count |",
        "|----------|-------|",
    ]
    for sev in ["Critical", "High", "Medium", "Low"]:
        lines.append(f"| {sev} | {summary['severity'][sev]} |")

    lines += [
        "",
        "## Findings",
        "",
    ]

    for fs in results:
        if not fs.findings:
            continue
        lines.append(f"### {fs.scanner}")
        lines.append("")
        lines.append("| ID | File | Severity | Category | Description |")
        lines.append("|----|------|----------|----------|-------------|")
        for f in fs.findings:
            desc = f.description.replace("|", "\\|")[:80] if f.description else ""
            lines.append(f"| {f.finding_id} | `{f.file}` | {f.severity.value} | {f.category.value} | {desc} |")
        lines.append("")

    lines.append(f"*Report generated {today} by MUSCAL Reconciliation Engine.*")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
