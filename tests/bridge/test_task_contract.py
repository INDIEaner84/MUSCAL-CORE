from __future__ import annotations

import pytest

from features.bridge.task_contract import TaskContract


class TestTaskContract:

    def test_valid_task(self):
        task = TaskContract(
            id="task-001",
            project="muscal-core",
            objective="Implement bridge MVP",
            constraints=["no core changes"],
            expected_output="working bridge",
            verification_required=True,
        )
        errors = task.validate()
        assert len(errors) == 0

    def test_missing_id_fails_validation(self):
        task = TaskContract(id="", project="muscal-core", objective="test")
        errors = task.validate()
        assert "task.id is required" in errors

    def test_missing_project_fails_validation(self):
        task = TaskContract(id="t1", project="", objective="test")
        errors = task.validate()
        assert "task.project is required" in errors

    def test_missing_objective_fails_validation(self):
        task = TaskContract(id="t1", project="p1", objective="")
        errors = task.validate()
        assert "task.objective is required" in errors

    def test_to_dict(self):
        task = TaskContract(id="t1", project="p1", objective="obj",
                            constraints=["c1"], expected_output="out")
        d = task.to_dict()
        assert d["task"]["id"] == "t1"
        assert d["task"]["constraints"] == ["c1"]
        assert d["task"]["verification_required"] is True

    def test_from_dict(self):
        data = {"task": {"id": "t2", "project": "p2", "objective": "obj2",
                         "constraints": ["c2"]}}
        task = TaskContract.from_dict(data)
        assert task.id == "t2"
        assert task.project == "p2"
        assert task.constraints == ["c2"]

    def test_from_dict_top_level(self):
        data = {"id": "t3", "project": "p3", "objective": "obj3"}
        task = TaskContract.from_dict(data)
        assert task.id == "t3"
