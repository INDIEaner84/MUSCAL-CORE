from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, FindingSet, Severity
from reconciliation.report import ReportGenerator
from reconciliation.runner import ReconciliationRunner
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_SCANNERS = [
    "broken_link_scanner",
    "adr_validator_scanner",
    "import_validator_scanner",
    "drift_detector_scanner",
    "rfc_validator_scanner",
]


class TestPipelineInitialization:
    def test_snapshot_builds(self):
        snapshot = RepositorySnapshot(REPO_ROOT)
        snapshot.build()
        assert snapshot._built is True

    def test_snapshot_has_files(self):
        snapshot = RepositorySnapshot(REPO_ROOT)
        snapshot.build()
        assert len(snapshot.files) > 0

    def test_scan_context_creation(self):
        snapshot = RepositorySnapshot(REPO_ROOT)
        snapshot.build()
        context = ScanContext(snapshot=snapshot)
        assert context.snapshot is snapshot

    def test_runner_initializes(self):
        runner = ReconciliationRunner(REPO_ROOT)
        assert runner.repo_root == REPO_ROOT
        assert runner._scanners == {}

    def test_runner_with_defaults(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert len(runner._scanners) == 5


class TestScannerExecution:
    def test_all_scanners_execute(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        assert len(results) == 5

    def test_scanner_names(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        names = [r.scanner for r in results]
        for expected in EXPECTED_SCANNERS:
            assert expected in names

    def test_each_scanner_returns_finding_set(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for result in results:
            assert isinstance(result, FindingSet)
            assert result.scanner != ""
            assert isinstance(result.findings, list)

    def test_no_scanner_raises_exception(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        assert len(results) == 5

    def test_scanner_execution_order(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        names = [r.scanner for r in results]
        assert names == EXPECTED_SCANNERS


class TestFindingAggregation:
    def test_finding_sets_are_lists(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for fs in results:
            assert isinstance(fs, FindingSet)
            assert isinstance(fs.findings, list)

    def test_findings_have_required_fields(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for fs in results:
            for f in fs.findings:
                assert f.finding_id != ""
                assert f.scanner != ""
                assert f.file != ""
                assert f.severity in Severity
                assert f.category in Category

    def test_findings_aggregated_by_category(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        total_by_cat = sum(summary["categories"].values())
        assert total_by_cat == summary["total_findings"]

    def test_findings_aggregated_by_severity(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        total_by_sev = sum(summary["severity"].values())
        assert total_by_sev == summary["total_findings"]

    def test_category_counts_non_negative(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        for cat, count in summary["categories"].items():
            assert count >= 0, f"Category {cat} has negative count: {count}"

    def test_severity_counts_non_negative(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        for sev, count in summary["severity"].items():
            assert count >= 0, f"Severity {sev} has negative count: {count}"


class TestReportGeneration:
    def test_report_generation(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        report = gen.reconciliation_report(results, checkpoint="0.41")
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_summary(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        report = gen.reconciliation_report(results, checkpoint="0.41")
        assert "Summary" in report

    def test_report_contains_scanner_results(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        report = gen.reconciliation_report(results, checkpoint="0.41")
        assert "Scanner Results" in report

    def test_summary_metrics_exist(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert "scanners" in summary
        assert "finding_sets" in summary
        assert "total_findings" in summary
        assert "categories" in summary
        assert "severity" in summary

    def test_summary_scanner_count_matches(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["scanners"] == 5

    def test_summary_finding_sets_count_matches(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["finding_sets"] == 5


class TestDeterminism:
    def test_same_scanner_inventory(self):
        runner1 = ReconciliationRunner(REPO_ROOT)
        runner1.register_defaults()
        results1 = runner1.run_all()

        runner2 = ReconciliationRunner(REPO_ROOT)
        runner2.register_defaults()
        results2 = runner2.run_all()

        names1 = [r.scanner for r in results1]
        names2 = [r.scanner for r in results2]
        assert names1 == names2

    def test_same_result_structure(self):
        runner1 = ReconciliationRunner(REPO_ROOT)
        runner1.register_defaults()
        results1 = runner1.run_all()

        runner2 = ReconciliationRunner(REPO_ROOT)
        runner2.register_defaults()
        results2 = runner2.run_all()

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.scanner == r2.scanner
            assert len(r1.findings) == len(r2.findings)

    def test_no_repository_mutation(self):
        snapshot1 = RepositorySnapshot(REPO_ROOT)
        snapshot1.build()
        files1 = [f.rel_path for f in snapshot1.files]

        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        runner.run_all()

        snapshot2 = RepositorySnapshot(REPO_ROOT)
        snapshot2.build()
        files2 = [f.rel_path for f in snapshot2.files]

        assert files1 == files2

    def test_deterministic_findings(self):
        runner1 = ReconciliationRunner(REPO_ROOT)
        runner1.register_defaults()
        results1 = runner1.run_all()
        gen1 = ReportGenerator()
        summary1 = gen1.build_summary(results1)

        runner2 = ReconciliationRunner(REPO_ROOT)
        runner2.register_defaults()
        results2 = runner2.run_all()
        gen2 = ReportGenerator()
        summary2 = gen2.build_summary(results2)

        assert summary1["total_findings"] == summary2["total_findings"]
        assert summary1["categories"] == summary2["categories"]
        assert summary1["severity"] == summary2["severity"]
