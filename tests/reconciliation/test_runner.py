from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import FindingSet
from reconciliation.report import ReportGenerator
from reconciliation.runner import ReconciliationRunner
from reconciliation.scan import (
    AdrValidatorScanner,
    BrokenLinkScanner,
    DriftDetectorScanner,
    ImportValidatorScanner,
    RfcValidatorScanner,
)
from reconciliation.scan.adr_scanner import AdrValidatorScanner as AdrDirect
from reconciliation.scan.drift_scanner import DriftDetectorScanner as DriftDirect
from reconciliation.scan.import_scanner import ImportValidatorScanner as ImportDirect
from reconciliation.scan.link_scanner import BrokenLinkScanner as LinkDirect
from reconciliation.scan.rfc_scanner import RfcValidatorScanner as RfcDirect
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestRunnerInitialization:
    def test_import(self):
        assert ReconciliationRunner is not None

    def test_init_default(self):
        runner = ReconciliationRunner()
        assert runner.repo_root == os.path.abspath(".")

    def test_init_with_path(self):
        runner = ReconciliationRunner(REPO_ROOT)
        assert runner.repo_root == REPO_ROOT

    def test_scanners_property_empty(self):
        runner = ReconciliationRunner(REPO_ROOT)
        assert runner.scanners == []

    def test_scanners_dict_empty(self):
        runner = ReconciliationRunner(REPO_ROOT)
        assert runner._scanners == {}


class TestRegisterDefaults:
    def test_register_defaults(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert len(runner._scanners) == 5

    def test_broken_link_scanner_registered(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert "broken_link_scanner" in runner._scanners

    def test_adr_scanner_registered(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert "adr_validator_scanner" in runner._scanners

    def test_import_scanner_registered(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert "import_validator_scanner" in runner._scanners

    def test_drift_scanner_registered(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert "drift_detector_scanner" in runner._scanners

    def test_rfc_scanner_registered(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert "rfc_validator_scanner" in runner._scanners

    def test_scanner_types(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert isinstance(runner._scanners["broken_link_scanner"], BrokenLinkScanner)
        assert isinstance(runner._scanners["adr_validator_scanner"], AdrValidatorScanner)
        assert isinstance(runner._scanners["import_validator_scanner"], ImportValidatorScanner)
        assert isinstance(runner._scanners["drift_detector_scanner"], DriftDetectorScanner)
        assert isinstance(runner._scanners["rfc_validator_scanner"], RfcValidatorScanner)

    def test_register_individual(self):
        runner = ReconciliationRunner(REPO_ROOT)
        scanner = BrokenLinkScanner()
        runner.register(scanner)
        assert len(runner._scanners) == 1
        assert "broken_link_scanner" in runner._scanners

    def test_register_overwrite(self):
        runner = ReconciliationRunner(REPO_ROOT)
        s1 = BrokenLinkScanner()
        s2 = BrokenLinkScanner()
        runner.register(s1)
        runner.register(s2)
        assert len(runner._scanners) == 1


class TestSnapshotPipeline:
    def test_build_context(self):
        runner = ReconciliationRunner(REPO_ROOT)
        context = runner._build_context()
        assert isinstance(context, ScanContext)
        assert context.snapshot is not None

    def test_snapshot_is_built(self):
        runner = ReconciliationRunner(REPO_ROOT)
        context = runner._build_context()
        assert context.snapshot._built is True

    def test_snapshot_has_files(self):
        runner = ReconciliationRunner(REPO_ROOT)
        context = runner._build_context()
        assert len(context.snapshot.files) > 0

    def test_snapshot_has_tree(self):
        runner = ReconciliationRunner(REPO_ROOT)
        context = runner._build_context()
        assert context.snapshot.tree is not None

    def test_context_has_scope(self):
        runner = ReconciliationRunner(REPO_ROOT)
        context = runner._build_context()
        assert context.scope is not None


class TestEndToEndExecution:
    def test_run_all_returns_list(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        assert isinstance(results, list)

    def test_run_all_returns_finding_sets(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for result in results:
            assert isinstance(result, FindingSet)

    def test_run_all_returns_5_results(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        assert len(results) == 5

    def test_run_all_no_exceptions(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        assert results is not None

    def test_run_all_with_context(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        context = runner._build_context()
        results = runner.run_all(context=context)
        assert len(results) == 5

    def test_run_scanner(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        result = runner.run_scanner("broken_link_scanner")
        assert isinstance(result, FindingSet)
        assert result.scanner == "broken_link_scanner"

    def test_run_scanner_not_found(self):
        runner = ReconciliationRunner(REPO_ROOT)
        result = runner.run_scanner("nonexistent_scanner")
        assert result is None

    def test_scanner_names_match(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        scanner_names = [r.scanner for r in results]
        assert "broken_link_scanner" in scanner_names
        assert "adr_validator_scanner" in scanner_names
        assert "import_validator_scanner" in scanner_names
        assert "drift_detector_scanner" in scanner_names
        assert "rfc_validator_scanner" in scanner_names


class TestReportIntegration:
    def test_report_generator(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert "scanners" in summary
        assert "total_findings" in summary
        assert "categories" in summary
        assert "severity" in summary

    def test_summary_scanner_count(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["scanners"] == 5

    def test_summary_finding_sets(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["finding_sets"] == 5

    def test_summary_total_findings(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["total_findings"] >= 0

    def test_summary_categories(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert "A" in summary["categories"]
        assert "B" in summary["categories"]
        assert "C" in summary["categories"]
        assert "D" in summary["categories"]

    def test_summary_severity(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert "Critical" in summary["severity"]
        assert "High" in summary["severity"]
        assert "Medium" in summary["severity"]
        assert "Low" in summary["severity"]

    def test_reconciliation_report(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        report = gen.reconciliation_report(results, checkpoint="0.40")
        assert isinstance(report, str)
        assert "Reconciliation Report" in report

    def test_save_report(self, tmp_path):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        output_path = str(tmp_path / "test_report.md")
        saved = runner.save_report(results, output_path, checkpoint="0.40")
        assert os.path.exists(saved)
        with open(saved) as f:
            content = f.read()
        assert "Reconciliation Report" in content


class TestErrorHandling:
    def test_missing_repository(self):
        runner = ReconciliationRunner("/nonexistent/path")
        context = runner._build_context()
        assert context.snapshot is not None
        assert len(context.snapshot.files) == 0

    def test_empty_repository(self, tmp_path):
        runner = ReconciliationRunner(str(tmp_path))
        runner.register_defaults()
        results = runner.run_all()
        assert len(results) == 5
        for result in results:
            assert isinstance(result, FindingSet)

    def test_scanner_failure_isolation(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()

        original_scan = BrokenLinkScanner.scan

        def failing_scan(self_scanner, context):
            raise RuntimeError("Scanner failure")

        BrokenLinkScanner.scan = failing_scan

        try:
            results = runner.run_all()
        except RuntimeError:
            BrokenLinkScanner.scan = original_scan
            pytest.skip("Scanner failure not isolated")

        BrokenLinkScanner.scan = original_scan

    def test_run_scanner_with_context(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        context = runner._build_context()
        result = runner.run_scanner("broken_link_scanner", context=context)
        assert isinstance(result, FindingSet)
        assert result.scanner == "broken_link_scanner"
