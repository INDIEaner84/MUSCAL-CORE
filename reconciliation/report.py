from __future__ import annotations

import datetime

from reconciliation.core.finding import Category, Finding, FindingSet, Severity


class ReportGenerator:
    def finding_report(self, finding: Finding) -> str:
        fields = [
            ("Finding ID", finding.finding_id),
            ("Scanner", finding.scanner),
            ("File", finding.file),
        ]
        if finding.line is not None:
            fields.append(("Line(s)", str(finding.line)))
        fields += [
            ("Severity", finding.severity.value),
            ("Category", finding.category.value),
            ("Status", finding.status.value),
        ]

        lines = ["# Finding Report", "", "## Individual Finding", "", "| Field | Value |"]
        lines.append("|-------|-------|")
        for k, v in fields:
            lines.append(f"| **{k}** | {v} |")

        if finding.description:
            lines += ["", "### Description", "", finding.description]
        if finding.current_value:
            lines += ["", "### Current Value", "", f"```\n{finding.current_value}\n```"]
        if finding.expected_value:
            lines += ["", "### Expected Value", "", f"```\n{finding.expected_value}\n```"]
        if finding.suggested_fix:
            lines += ["", "### Suggested Fix", "", finding.suggested_fix]
        if finding.validation:
            lines += ["", "### Validation", "", finding.validation]

        return "\n".join(lines)

    def validation_report(self, findings: FindingSet) -> str:
        lines = [
            f"# Validation Report",
            "",
            f"**Scanner:** {findings.scanner}",
            f"**Date:** {datetime.date.today().isoformat()}",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Findings | {findings.count} |",
        ]
        for cat in Category:
            count = len(findings.by_category.get(cat, []))
            lines.append(f"| Category {cat.value} | {count} |")
        for sev in Severity:
            count = len(findings.by_severity.get(sev, []))
            lines.append(f"| {sev.value} | {count} |")

        if findings.findings:
            lines += ["", "## Findings"]
            for f in findings.findings:
                lines += [
                    "",
                    f"### {f.finding_id}",
                    "",
                    f"**File:** {f.file}",
                    f"**Severity:** {f.severity.value}",
                    f"**Category:** {f.category.value}",
                ]
                if f.description:
                    lines.append(f"**Description:** {f.description}")
                if f.suggested_fix:
                    lines.append(f"**Suggested Fix:** {f.suggested_fix}")

        return "\n".join(lines)

    def reconciliation_report(self, results: list[FindingSet], checkpoint: str = "") -> str:
        today = datetime.date.today().isoformat()
        lines = [
            "# Reconciliation Report",
            "",
        ]
        if checkpoint:
            lines.append(f"**Checkpoint:** {checkpoint}")
        lines += [
            f"**Date:** {today}",
            "",
            "## 1. Executive Summary",
            "",
            "## 2. Scanner Results",
            "",
            "| Scanner | Findings | Cat A | Cat B | Cat C | Cat D |",
            "|---------|----------|-------|-------|-------|-------|",
        ]

        total_findings = 0
        total_a = total_b = total_c = total_d = 0
        for fs in results:
            ca = len(fs.by_category.get(Category.A, []))
            cb = len(fs.by_category.get(Category.B, []))
            cc = len(fs.by_category.get(Category.C, []))
            cd = len(fs.by_category.get(Category.D, []))
            total_findings += fs.count
            total_a += ca
            total_b += cb
            total_c += cc
            total_d += cd
            lines.append(f"| {fs.scanner} | {fs.count} | {ca} | {cb} | {cc} | {cd} |")

        lines.append(f"| **Total** | **{total_findings}** | **{total_a}** | **{total_b}** | **{total_c}** | **{total_d}** |")

        for fs in results:
            if not fs.findings:
                continue
            lines += ["", f"## 3. Scanner: {fs.scanner}"]
            for f in fs.findings:
                lines += [
                    "",
                    f"### {f.finding_id}",
                    f"**File:** {f.file}",
                    f"**Category:** {f.category.value}",
                    f"**Severity:** {f.severity.value}",
                ]
                if f.description:
                    lines.append(f"**Description:** {f.description}")
                if f.suggested_fix:
                    lines.append(f"**Suggested Fix:** {f.suggested_fix}")

        lines += [
            "",
            f"*Report generated {today} by Reconciliation Engine.*",
        ]
        return "\n".join(lines)
