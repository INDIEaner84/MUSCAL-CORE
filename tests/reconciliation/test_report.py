from reconciliation.core.finding import Category, Finding, FindingSet, Severity
from reconciliation.report import ReportGenerator


class TestFindingReport:
    def test_finding_report_renders_fields(self):
        f = Finding("F-001", "test-scanner", "file.py", Severity.HIGH, Category.A)
        gen = ReportGenerator()
        report = gen.finding_report(f)
        assert f.finding_id in report
        assert "test-scanner" in report
        assert "file.py" in report

    def test_finding_report_with_line(self):
        f = Finding("F-002", "test", "x.py", Severity.LOW, Category.B, line=15)
        gen = ReportGenerator()
        report = gen.finding_report(f)
        assert "15" in report

    def test_finding_report_with_description(self):
        f = Finding("F-003", "test", "x.py", Severity.CRITICAL, Category.A,
                     description="Critical issue found")
        gen = ReportGenerator()
        report = gen.finding_report(f)
        assert "Critical issue found" in report

    def test_finding_report_with_current_and_expected(self):
        f = Finding("F-004", "test", "x.py", Severity.MEDIUM, Category.C,
                     current_value="old value", expected_value="new value")
        gen = ReportGenerator()
        report = gen.finding_report(f)
        assert "old value" in report
        assert "new value" in report

    def test_finding_report_with_suggested_fix(self):
        f = Finding("F-005", "test", "x.py", Severity.HIGH, Category.B,
                     suggested_fix="Remove bad code")
        gen = ReportGenerator()
        report = gen.finding_report(f)
        assert "Remove bad code" in report


class TestValidationReport:
    def test_empty_findings(self):
        fs = FindingSet(scanner="test")
        gen = ReportGenerator()
        report = gen.validation_report(fs)
        assert "test" in report
        assert "0" in report

    def test_with_findings(self):
        f1 = Finding("F1", "test", "a.py", Severity.HIGH, Category.A)
        f2 = Finding("F2", "test", "b.py", Severity.LOW, Category.B)
        fs = FindingSet(scanner="test", findings=[f1, f2])
        gen = ReportGenerator()
        report = gen.validation_report(fs)
        assert "F1" in report
        assert "F2" in report
        assert "Category A" in report or "A" in report

    def test_summary_counts(self):
        findings = [
            Finding("F1", "test", "a.py", Severity.CRITICAL, Category.A),
            Finding("F2", "test", "b.py", Severity.HIGH, Category.A),
            Finding("F3", "test", "c.py", Severity.LOW, Category.B),
        ]
        fs = FindingSet(scanner="test", findings=findings)
        gen = ReportGenerator()
        report = gen.validation_report(fs)
        assert "| 3 |" in report or "Total Findings" in report


class TestReconciliationReport:
    def test_empty_results(self):
        gen = ReportGenerator()
        report = gen.reconciliation_report([])
        assert "Reconciliation Report" in report
        assert "0" in report

    def test_with_results(self):
        f1 = Finding("F1", "s1", "a.py", Severity.HIGH, Category.A)
        f2 = Finding("F2", "s2", "b.py", Severity.LOW, Category.B)
        results = [
            FindingSet(scanner="s1", findings=[f1]),
            FindingSet(scanner="s2", findings=[f2]),
        ]
        gen = ReportGenerator()
        report = gen.reconciliation_report(results)
        assert "s1" in report
        assert "s2" in report
        assert "F1" in report
        assert "F2" in report

    def test_checkpoint_included(self):
        gen = ReportGenerator()
        report = gen.reconciliation_report([], checkpoint="v1.0")
        assert "v1.0" in report

    def test_executive_summary_section(self):
        gen = ReportGenerator()
        report = gen.reconciliation_report([])
        assert "Executive Summary" in report


class TestBuildSummary:
    def test_empty(self):
        gen = ReportGenerator()
        summary = gen.build_summary([])
        assert summary["scanners"] == 0
        assert summary["total_findings"] == 0
        assert summary["categories"]["A"] == 0
        assert summary["severity"]["Critical"] == 0

    def test_with_findings(self):
        results = [
            FindingSet(scanner="s1", findings=[
                Finding("F1", "s1", "a.py", Severity.CRITICAL, Category.A),
                Finding("F2", "s1", "b.py", Severity.HIGH, Category.B),
            ]),
            FindingSet(scanner="s2", findings=[
                Finding("F3", "s2", "c.py", Severity.MEDIUM, Category.A),
            ]),
        ]
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["scanners"] == 2
        assert summary["total_findings"] == 3
        assert summary["categories"]["A"] == 2
        assert summary["categories"]["B"] == 1
        assert summary["severity"]["Critical"] == 1
        assert summary["severity"]["High"] == 1
        assert summary["severity"]["Medium"] == 1

    def test_all_categories_severities_present(self):
        categories = ["A", "B", "C", "D"]
        severities = ["Critical", "High", "Medium", "Low"]
        gen = ReportGenerator()
        summary = gen.build_summary([])
        for cat in categories:
            assert cat in summary["categories"]
        for sev in severities:
            assert sev in summary["severity"]
