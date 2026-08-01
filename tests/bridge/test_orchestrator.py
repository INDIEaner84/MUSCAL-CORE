from __future__ import annotations

from pathlib import Path

from features.bridge.orchestrator import (
    BridgeConfig, BridgeOutput, run_bridge,
)


class TestOrchestrator:

    def test_orchestrator_returns_bridge_output(self, tmp_path: Path):
        cfg = BridgeConfig(
            opencode_path="opencode",
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
            event_store_path=tmp_path / "bridge.db",
        )
        result = run_bridge("test message", config=cfg, task_id="test-orch-001")
        assert isinstance(result, BridgeOutput)
        assert result.task_id == "test-orch-001"
        assert result.status in ("completed", "failed")

    def test_orchestrator_with_help_message(self, tmp_path: Path):
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
        )
        result = run_bridge("--help", config=cfg)
        assert result.opencode_result is not None
        assert result.opencode_result.status == "completed"
        assert result.opencode_result.return_code == 0

    def test_orchestrator_produces_report_files(self, tmp_path: Path):
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
        )
        result = run_bridge("--help", config=cfg)
        if result.report_paths:
            md, yml = result.report_paths
            if md and md.exists():
                content = md.read_text()
                assert "# Bridge Execution Report" in content

    def test_orchestrator_scans_project(self):
        cfg = BridgeConfig(timeout=30, workdir=Path("."))
        result = run_bridge("--help", config=cfg)
        assert result.context is not None
        assert result.context.branch is not None
        assert len(result.context.commit) >= 7

    def test_orchestrator_captures_errors_on_bad_opencode(self, tmp_path: Path):
        cfg = BridgeConfig(
            opencode_path="/nonexistent/opencode",
            timeout=5,
            workdir=Path("."),
            output_dir=tmp_path,
        )
        result = run_bridge("test", config=cfg)
        assert len(result.errors) >= 1
