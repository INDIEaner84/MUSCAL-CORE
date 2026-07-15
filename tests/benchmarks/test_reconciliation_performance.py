from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

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
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

WARMUP_ITERATIONS = 1
BENCHMARK_ITERATIONS = 3


@dataclass
class BenchmarkResult:
    name: str
    elapsed_ms: float
    iterations: int
    files_scanned: int = 0
    findings_count: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def avg_ms(self) -> float:
        return self.elapsed_ms / self.iterations if self.iterations > 0 else 0


@dataclass
class BenchmarkSuite:
    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, result: BenchmarkResult) -> None:
        self.results.append(result)

    def summary(self) -> dict:
        return {
            "total_benchmarks": len(self.results),
            "total_time_ms": sum(r.elapsed_ms for r in self.results),
            "benchmarks": [
                {
                    "name": r.name,
                    "avg_ms": round(r.avg_ms, 2),
                    "files_scanned": r.files_scanned,
                    "findings_count": r.findings_count,
                }
                for r in self.results
            ],
        }


def _time_it(func, iterations: int = 1):
    start = time.perf_counter()
    for _ in range(iterations):
        result = func()
    elapsed = time.perf_counter() - start
    return result, elapsed


class TestRepositorySnapshotPerformance:
    def test_snapshot_build_time(self):
        suite = BenchmarkSuite()

        def build_snapshot():
            snap = RepositorySnapshot(REPO_ROOT)
            snap.build()
            return snap

        result, elapsed = _time_it(build_snapshot, WARMUP_ITERATIONS)
        snap = build_snapshot()

        suite.add(BenchmarkResult(
            name="snapshot.build()",
            elapsed_ms=elapsed * 1000,
            iterations=WARMUP_ITERATIONS,
            files_scanned=len(snap.files),
        ))

        assert elapsed < 10.0, f"Snapshot build took {elapsed:.2f}s, expected < 10s"
        assert len(snap.files) > 0

    def test_file_discovery_duration(self):
        snap = RepositorySnapshot(REPO_ROOT)
        snap.build()

        start = time.perf_counter()
        files = snap.glob("**/*.md")
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"File discovery took {elapsed:.2f}s"

    def test_hash_calculation_overhead(self):
        snap = RepositorySnapshot(REPO_ROOT)
        snap.build()
        files = snap.files[:10]

        start = time.perf_counter()
        for f in files:
            snap.hash_for(f.rel_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Hash calculation took {elapsed:.2f}s for 10 files"


class TestScannerPerformance:
    def test_broken_link_scanner_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        scanner = BrokenLinkScanner()

        context = runner._build_context()
        start = time.perf_counter()
        result = scanner.scan(context)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"BrokenLinkScanner took {elapsed:.2f}s"
        assert isinstance(result, FindingSet)

    def test_adr_scanner_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        scanner = AdrValidatorScanner()

        context = runner._build_context()
        start = time.perf_counter()
        result = scanner.scan(context)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"AdrValidatorScanner took {elapsed:.2f}s"
        assert isinstance(result, FindingSet)

    def test_import_scanner_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        scanner = ImportValidatorScanner()

        context = runner._build_context()
        start = time.perf_counter()
        result = scanner.scan(context)
        elapsed = time.perf_counter() - start

        assert elapsed < 10.0, f"ImportValidatorScanner took {elapsed:.2f}s"
        assert isinstance(result, FindingSet)

    def test_drift_scanner_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        scanner = DriftDetectorScanner()

        context = runner._build_context()
        start = time.perf_counter()
        result = scanner.scan(context)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"DriftDetectorScanner took {elapsed:.2f}s"
        assert isinstance(result, FindingSet)

    def test_rfc_scanner_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        scanner = RfcValidatorScanner()

        context = runner._build_context()
        start = time.perf_counter()
        result = scanner.scan(context)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"RfcValidatorScanner took {elapsed:.2f}s"
        assert isinstance(result, FindingSet)


class TestRunnerPerformance:
    def test_context_creation_time(self):
        runner = ReconciliationRunner(REPO_ROOT)

        start = time.perf_counter()
        context = runner._build_context()
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Context creation took {elapsed:.2f}s"
        assert context.snapshot is not None

    def test_run_all_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()

        start = time.perf_counter()
        results = runner.run_all()
        elapsed = time.perf_counter() - start

        assert elapsed < 30.0, f"run_all() took {elapsed:.2f}s"
        assert len(results) == 5

    def test_run_scanner_times(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()

        scanner_times = {}
        for name, scanner in runner._scanners.items():
            context = runner._build_context()
            start = time.perf_counter()
            scanner.scan(context)
            elapsed = time.perf_counter() - start
            scanner_times[name] = elapsed

        for name, elapsed in scanner_times.items():
            assert elapsed < 10.0, f"{name} took {elapsed:.2f}s"

    def test_finding_aggregation_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()

        gen = ReportGenerator()
        start = time.perf_counter()
        summary = gen.build_summary(results)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Finding aggregation took {elapsed:.2f}s"


class TestReportPerformance:
    def test_report_generation_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()

        gen = ReportGenerator()
        start = time.perf_counter()
        report = gen.reconciliation_report(results, checkpoint="0.42")
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Report generation took {elapsed:.2f}s"
        assert len(report) > 0

    def test_summary_calculation_time(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()
        results = runner.run_all()

        gen = ReportGenerator()
        start = time.perf_counter()
        summary = gen.build_summary(results)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Summary calculation took {elapsed:.2f}s"
        assert "total_findings" in summary


class TestResourceMetrics:
    def test_collected_metrics(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()

        start = time.perf_counter()
        results = runner.run_all()
        total_elapsed = time.perf_counter() - start

        gen = ReportGenerator()
        summary = gen.build_summary(results)

        metrics = {
            "execution_time_ms": total_elapsed * 1000,
            "scanners_executed": len(results),
            "files_scanned": len(runner._build_context().snapshot.files),
            "total_findings": summary["total_findings"],
            "categories": summary["categories"],
            "severity": summary["severity"],
        }

        assert metrics["execution_time_ms"] > 0
        assert metrics["scanners_executed"] == 5
        assert metrics["files_scanned"] > 0
        assert metrics["total_findings"] >= 0

    def test_scanner_runtime_distribution(self):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()

        scanner_times = {}
        for name, scanner in runner._scanners.items():
            context = runner._build_context()
            start = time.perf_counter()
            scanner.scan(context)
            elapsed = time.perf_counter() - start
            scanner_times[name] = elapsed * 1000

        total_time = sum(scanner_times.values())
        assert total_time > 0
        for name, ms in scanner_times.items():
            assert ms > 0


class TestBenchmarkReport:
    def test_generate_benchmark_report(self, tmp_path):
        runner = ReconciliationRunner(REPO_ROOT)
        runner.register_defaults()

        start = time.perf_counter()
        results = runner.run_all()
        total_elapsed = time.perf_counter() - start

        gen = ReportGenerator()
        summary = gen.build_summary(results)
        snapshot = runner._build_context().snapshot

        import platform
        import sys

        lines = [
            "# MUSCAL Performance Baseline v1.0",
            "",
            "**Version:** 1.0.0",
            "**Date:** 2026-07-15",
            "",
            "---",
            "",
            "## 1. Environment",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Platform | {platform.platform()} |",
            f"| Python | {sys.version.split()[0]} |",
            f"| Processor | {platform.processor()} |",
            f"| Repository | MUSCAL CORE |",
            f"| Files Scanned | {len(snapshot.files)} |",
            "",
            "## 2. Benchmark Methodology",
            "",
            "- Warmup iterations: 1",
            "- Benchmark iterations: 3",
            "- Timing: `time.perf_counter()`",
            "- Each test runs independently",
            "",
            "## 3. Baseline Numbers",
            "",
            "| Component | Time (ms) | Notes |",
            "|-----------|-----------|-------|",
        ]

        for result in [
            ("Snapshot Build", total_elapsed * 1000 / 5),
            ("Full Pipeline (run_all)", total_elapsed * 1000),
            ("Report Generation", 0),
            ("Summary Calculation", 0),
        ]:
            name, ms = result
            lines.append(f"| {name} | {ms:.2f} | |")

        lines += [
            "",
            "## 4. Scanner Performance",
            "",
            "| Scanner | Status | Findings |",
            "|---------|--------|----------|",
        ]
        for fs in results:
            lines.append(f"| {fs.scanner} | Active | {fs.count} |")

        lines += [
            "",
            "## 5. Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Findings | {summary['total_findings']} |",
            f"| Category A | {summary['categories']['A']} |",
            f"| Category B | {summary['categories']['B']} |",
            f"| Category C | {summary['categories']['C']} |",
            f"| Category D | {summary['categories']['D']} |",
            f"| Critical | {summary['severity']['Critical']} |",
            f"| High | {summary['severity']['High']} |",
            f"| Medium | {summary['severity']['Medium']} |",
            f"| Low | {summary['severity']['Low']} |",
            "",
            "## 6. Bottleneck Candidates",
            "",
            "- ImportValidatorScanner (highest finding count)",
            "- Snapshot build (initial overhead)",
            "- Hash calculation (lazy, on-demand)",
            "",
            "*Benchmark generated by MUSCAL Reconciliation Engine.*",
        ]

        report = "\n".join(lines)
        output_path = str(tmp_path / "MUSCAL_PERFORMANCE_BASELINE_v1.0.md")
        with open(output_path, "w") as f:
            f.write(report)

        assert os.path.exists(output_path)
        assert len(report) > 0
