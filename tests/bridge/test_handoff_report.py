from __future__ import annotations

from pathlib import Path

from features.bridge.handoff_report import HandoffReport, BridgeReport
from features.bridge.project_scanner import ProjectScanner, GitStatus, ProjectContext
from features.bridge.result_normalizer import NormalizedResult, ExecutionInfo, VerifiedFact


class TestHandoffReport:

    def _make_report(self) -> BridgeReport:
        ctx = ProjectContext(
            root=Path("/test/repo"),
            repository="test",
            branch="main",
            commit="abc1234",
            git=GitStatus(dirty=False, modified_count=0, untracked_count=0),
            scan_timestamp="2026-07-28T12:00:00",
            scan_status="ok",
        )
        exec_info = ExecutionInfo(return_code=0, duration=2.5, session_reference="ses_001")
        normalized = NormalizedResult(status="completed", execution=exec_info)
        normalized.facts.append(VerifiedFact(
            statement="OpenCode process completed with exit code 0",
            evidence="return_code=0, duration=2.50s",
            source="opencode_adapter",
        ))
        return BridgeReport(
            project=ctx,
            task={"id": "task-001", "description": "test task"},
            execution=normalized,
            changes=[{"file": "test.py", "description": "added test"}],
            tests=[{"name": "test_foo", "status": "passed"}],
            risks=[{"priority": "P1", "description": "test risk"}],
            next_action="review results",
        )

    def test_report_to_markdown(self):
        report = self._make_report()
        md = report.to_markdown()
        assert "# Bridge Execution Report" in md
        assert "/test/repo" in md
        assert "main" in md
        assert "abc1234" in md
        assert "completed with exit code 0" in md
        assert "test risk" in md

    def test_report_to_yaml(self):
        report = self._make_report()
        yml = report.to_yaml()
        assert "project" in yml
        assert "branch: main" in yml
        assert "commit: abc1234" in yml

    def test_report_to_dict(self):
        report = self._make_report()
        d = report.to_dict()
        assert d["report"]["project"]["branch"] == "main"
        assert d["report"]["project"]["commit"] == "abc1234"
        assert d["report"]["task"]["id"] == "task-001"
        assert len(d["report"]["changes"]) == 1
        assert len(d["report"]["tests"]) == 1
        assert len(d["report"]["risks"]) == 1

    def test_empty_report_format(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        normalized = NormalizedResult(status="unknown")
        report = BridgeReport(
            project=ctx,
            task={"id": "", "description": ""},
            execution=normalized,
        )
        md = report.to_markdown()
        assert "# Bridge Execution Report" in md
        yml = report.to_yaml()
        assert "project" in yml

    def test_handoff_report_generates_files(self, tmp_path: Path):
        report = self._make_report()
        gen = HandoffReport(output_dir=tmp_path)
        md_path = tmp_path / "test_report.md"
        yml_path = tmp_path / "test_report.yaml"
        gen.generate(report, markdown_path=md_path, yaml_path=yml_path)
        assert md_path.exists()
        assert yml_path.exists()
        assert "# Bridge Execution Report" in md_path.read_text()
