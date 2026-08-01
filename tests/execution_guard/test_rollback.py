from __future__ import annotations

import pytest

from features.execution_guard.rollback import RollbackInfo, ROLLBACK_METHODS


class TestRollbackInfo:

    def test_not_available(self):
        rb = RollbackInfo.not_available()
        assert rb.available is False
        assert rb.method is None

    def test_from_commit(self):
        rb = RollbackInfo.from_commit("abc1234")
        assert rb.available is True
        assert rb.method == "git_commit_reference"
        assert rb.reference == "abc1234"

    def test_from_diff(self):
        rb = RollbackInfo.from_diff("diff-ref-001")
        assert rb.available is True
        assert rb.method == "git_diff_patch"
        assert rb.reference == "diff-ref-001"

    def test_from_checkpoint(self):
        rb = RollbackInfo.from_checkpoint("cp-001")
        assert rb.available is True
        assert rb.method == "checkpoint_reference"
        assert rb.reference == "cp-001"

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Invalid rollback method"):
            RollbackInfo(available=True, method="invalid_method", reference="ref", created_at="now")

    def test_to_dict(self):
        rb = RollbackInfo.from_commit("def5678")
        d = rb.to_dict()
        assert d["rollback"]["available"] is True
        assert d["rollback"]["method"] == "git_commit_reference"
        assert d["rollback"]["reference"] == "def5678"

    def test_rollback_methods_set(self):
        assert "git_commit_reference" in ROLLBACK_METHODS
        assert "git_diff_patch" in ROLLBACK_METHODS
        assert "checkpoint_reference" in ROLLBACK_METHODS
