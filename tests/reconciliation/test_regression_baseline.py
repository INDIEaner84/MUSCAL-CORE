from __future__ import annotations

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reconciliation.runner import ReconciliationRunner
from reconciliation.report import ReportGenerator


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_TOTAL = 53
EXPECTED_SCANNERS = [
    "broken_link_scanner",
    "adr_validator_scanner",
    "import_validator_scanner",
    "drift_detector_scanner",
    "rfc_validator_scanner",
]
EXPECTED_BY_SCANNER = {
    "broken_link_scanner": 9,
    "adr_validator_scanner": 3,
    "import_validator_scanner": 2,
    "drift_detector_scanner": 3,
    "rfc_validator_scanner": 36,
}


class TestFullPipeline:
    def test_runner_initializes(self):
        runner = ReconciliationRunner(REPO_ROOT)
        assert runner.repo_root == REPO_ROOT

    def test_five_scanners_registered(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        assert len(runner._scanners) == 5

    def test_all_scanners_present(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        for name in EXPECTED_SCANNERS:
            assert name in runner._scanners, f"Scanner {name} not registered"

    def test_pipeline_executes(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        assert len(results) == 5

    def test_report_generation(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        report = gen.reconciliation_report(results, checkpoint="0.46")
        assert isinstance(report, str)
        assert "Reconciliation Report" in report

    def test_compare_baseline_exits_zero(self):
        result = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "scripts", "compare_baseline.py")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"compare_baseline.py failed: {result.stderr}"


class TestFindingStability:
    def test_total_findings(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        total = sum(r.count for r in results)
        assert total == EXPECTED_TOTAL, f"Expected {EXPECTED_TOTAL} findings, got {total}"

    def test_broken_link_scanner_count(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for r in results:
            if r.scanner == "broken_link_scanner":
                assert r.count == EXPECTED_BY_SCANNER["broken_link_scanner"], \
                    f"Expected {EXPECTED_BY_SCANNER['broken_link_scanner']} findings, got {r.count}"
                return
        pytest.fail("broken_link_scanner not found in results")

    def test_adr_scanner_count(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for r in results:
            if r.scanner == "adr_validator_scanner":
                assert r.count == EXPECTED_BY_SCANNER["adr_validator_scanner"], \
                    f"Expected {EXPECTED_BY_SCANNER['adr_validator_scanner']} findings, got {r.count}"
                return
        pytest.fail("adr_validator_scanner not found in results")

    def test_import_scanner_count(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for r in results:
            if r.scanner == "import_validator_scanner":
                assert r.count == EXPECTED_BY_SCANNER["import_validator_scanner"], \
                    f"Expected {EXPECTED_BY_SCANNER['import_validator_scanner']} findings, got {r.count}"
                return
        pytest.fail("import_validator_scanner not found in results")

    def test_drift_scanner_count(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for r in results:
            if r.scanner == "drift_detector_scanner":
                assert r.count == EXPECTED_BY_SCANNER["drift_detector_scanner"], \
                    f"Expected {EXPECTED_BY_SCANNER['drift_detector_scanner']} findings, got {r.count}"
                return
        pytest.fail("drift_detector_scanner not found in results")

    def test_rfc_scanner_count(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        for r in results:
            if r.scanner == "rfc_validator_scanner":
                assert r.count == EXPECTED_BY_SCANNER["rfc_validator_scanner"], \
                    f"Expected {EXPECTED_BY_SCANNER['rfc_validator_scanner']} findings, got {r.count}"
                return
        pytest.fail("rfc_validator_scanner not found in results")

    def test_no_unknown_classifications(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()
        gen = ReportGenerator()
        summary = gen.build_summary(results)
        assert summary["total_findings"] == EXPECTED_TOTAL


class TestDeterminism:
    def test_same_scanner_order(self):
        runner1 = ReconciliationRunner(REPO_ROOT)
        runner1.register_defaults()
        results1 = runner1.run_all()

        runner2 = ReconciliationRunner(REPO_ROOT)
        runner2.register_defaults()
        results2 = runner2.run_all()

        names1 = [r.scanner for r in results1]
        names2 = [r.scanner for r in results2]
        assert names1 == names2, "Scanner order differs between runs"

    def test_same_finding_ids(self):
        runner1 = ReconciliationRunner(REPO_ROOT)
        runner1.register_defaults()
        results1 = runner1.run_all()

        runner2 = ReconciliationRunner(REPO_ROOT)
        runner2.register_defaults()
        results2 = runner2.run_all()

        for r1, r2 in zip(results1, results2):
            ids1 = sorted([f.finding_id for f in r1.findings])
            ids2 = sorted([f.finding_id for f in r2.findings])
            assert ids1 == ids2, f"Finding IDs differ for {r1.scanner}"

    def test_same_classifications(self):
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

        assert summary1 == summary2, "Classifications differ between runs"


class TestCICompatibility:
    def test_compare_baseline_exit_code(self):
        result = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "scripts", "compare_baseline.py")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"compare_baseline.py failed: {result.stderr}"

    def test_compare_baseline_output(self):
        result = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "scripts", "compare_baseline.py")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert "PASS" in result.stdout, f"compare_baseline.py did not pass: {result.stdout}"
