from __future__ import annotations

from pathlib import Path

from features.bridge.orchestrator import (
    BridgeConfig, BridgeOutput, run_bridge,
)
from features.bridge.task_contract import TaskContract


class TestOrchestratorV3:

    def test_orchestrator_with_task_contract(self, tmp_path: Path):
        task = TaskContract(
            id="tc-001",
            project="muscal-core",
            objective="Integration test with task contract",
            constraints=["no core changes"],
            expected_output="test result",
            verification_required=True,
        )
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
        )
        result = run_bridge("--help", config=cfg, task=task, task_id="tc-001")
        assert result.task is not None
        assert result.task.id == "tc-001"

    def test_orchestrator_with_verification(self, tmp_path: Path):
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
            verification_required=True,
        )
        result = run_bridge("--help", config=cfg)
        assert result.verification_report is not None
        assert "verification" in result.verification_report

    def test_orchestrator_with_execution_record(self, tmp_path: Path):
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
        )
        result = run_bridge("--help", config=cfg)
        assert result.execution_record is not None
        assert "execution_record" in result.execution_record

    def test_orchestrator_recovery_events(self, tmp_path: Path):
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
        )
        result = run_bridge("--help", config=cfg)
        assert result.recovery_events is not None

    def test_orchestrator_all_new_fields(self, tmp_path: Path):
        task = TaskContract(
            id="tc-all",
            project="muscal-core",
            objective="Test all new fields",
        )
        cfg = BridgeConfig(
            timeout=30,
            workdir=Path("."),
            output_dir=tmp_path,
            verification_required=True,
        )
        result = run_bridge("--help", config=cfg, task=task, task_id="tc-all")
        assert result.task is not None
        assert result.verification_report is not None
        assert result.execution_record is not None
        assert result.recovery_events is not None
