from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from features.tool_runtime.tool_runtime import (
    ExecutionReceipt,
    VerificationResult,
    VerificationStatus,
)
from features.identity.uuid7 import uuid7


class Verifier(ABC):
    name: str = "base"

    @abstractmethod
    def verify(
        self,
        receipt: ExecutionReceipt,
        expected_state: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        ...

    def verify_id(self) -> str:
        return uuid7()


class IntegrityVerifier(Verifier):
    name = "integrity_check"

    def verify(
        self,
        receipt: ExecutionReceipt,
        expected_state: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        if not receipt.finalized:
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.TAMPERED,
                expected_state={"finalized": True},
                observed_state={"finalized": False},
                evidence={"note": "Receipt was never finalized"},
                verified_at=time.time(),
            )

        if not receipt.verify_integrity():
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.TAMPERED,
                expected_state={"integrity": "valid"},
                observed_state={"integrity": "invalid"},
                evidence={"note": "Receipt integrity hash mismatch — content may have been tampered"},
                verified_at=time.time(),
            )

        return VerificationResult(
            verification_id=self.verify_id(),
            execution_id=receipt.execution_id,
            receipt_id=receipt.receipt_id,
            verifier_id=self.name,
            status=VerificationStatus.EXECUTED,
            expected_state={},
            observed_state={},
            evidence={"note": "Receipt integrity hash valid"},
            verified_at=time.time(),
        )


class MathVerifier(Verifier):
    name = "math.add"

    def verify(
        self,
        receipt: ExecutionReceipt,
        expected_state: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        a = receipt.args.get("a", 0)
        b = receipt.args.get("b", 0)
        expected = a + b
        observed = None
        if receipt.result_data and isinstance(receipt.result_data, dict):
            observed = receipt.result_data.get("result")

        if observed is not None and observed == expected:
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.VERIFIED,
                expected_state={"result": expected},
                observed_state={"result": observed},
                evidence={"recomputed": True},
                verified_at=time.time(),
            )

        return VerificationResult(
            verification_id=self.verify_id(),
            execution_id=receipt.execution_id,
            receipt_id=receipt.receipt_id,
            verifier_id=self.name,
            status=VerificationStatus.FAILED,
            expected_state={"result": expected},
            observed_state={"result": observed},
            state_diff={"expected": expected, "observed": observed},
            evidence={"recomputed": True},
            verified_at=time.time(),
        )


class FilesystemVerifier(Verifier):
    name = "filesystem.write"

    def __init__(self, allowed_paths: Optional[list] = None):
        self._allowed_paths = allowed_paths or ["/tmp"]

    def verify(
        self,
        receipt: ExecutionReceipt,
        expected_state: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        path = receipt.args.get("path", "")
        abspath = os.path.abspath(path)
        allowed = any(abspath.startswith(os.path.abspath(p)) for p in self._allowed_paths)

        if not allowed:
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.NOT_SUPPORTED,
                expected_state={},
                observed_state={},
                evidence={"note": f"Path {path} not in allowed paths"},
                verified_at=time.time(),
            )

        if not os.path.exists(abspath):
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.FAILED,
                expected_state={"exists": True},
                observed_state={"exists": False},
                state_diff={"file_status": "missing"},
                evidence={"path": path},
                verified_at=time.time(),
            )

        if expected_state and "content" in expected_state:
            with open(abspath) as f:
                actual = f.read()
            if actual == expected_state["content"]:
                return VerificationResult(
                    verification_id=self.verify_id(),
                    execution_id=receipt.execution_id,
                    receipt_id=receipt.receipt_id,
                    verifier_id=self.name,
                    status=VerificationStatus.VERIFIED,
                    expected_state={"content": expected_state["content"]},
                    observed_state={"content": actual},
                    evidence={"path": path, "match": True},
                    verified_at=time.time(),
                )
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.FAILED,
                expected_state={"content": expected_state["content"]},
                observed_state={"content": actual},
                state_diff={"content_mismatch": True},
                evidence={"path": path},
                verified_at=time.time(),
            )

        return VerificationResult(
            verification_id=self.verify_id(),
            execution_id=receipt.execution_id,
            receipt_id=receipt.receipt_id,
            verifier_id=self.name,
            status=VerificationStatus.VERIFIED,
            expected_state={"exists": True},
            observed_state={"exists": True},
            evidence={"path": path},
            verified_at=time.time(),
        )


class OpenCodeRunVerifier(Verifier):
    name = "opencode.run"

    def verify(
        self,
        receipt: ExecutionReceipt,
        expected_state: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        if not receipt.result_data:
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.INCONCLUSIVE,
                expected_state={},
                observed_state={},
                evidence={"note": "No result data available"},
                verified_at=time.time(),
            )

        status = receipt.result_data.get("status", "")
        if status == "ok":
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.VERIFIED,
                expected_state={"status": "ok"},
                observed_state={"status": status},
                evidence={"command": receipt.args.get("command", "")},
                verified_at=time.time(),
            )

        if status in ("blocked", "timeout", "error"):
            return VerificationResult(
                verification_id=self.verify_id(),
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=self.name,
                status=VerificationStatus.FAILED,
                expected_state={"status": "ok"},
                observed_state={"status": status},
                state_diff={"command_status": status},
                evidence={"command": receipt.args.get("command", ""),
                          "error": receipt.result_data.get("error", "")},
                verified_at=time.time(),
            )

        return VerificationResult(
            verification_id=self.verify_id(),
            execution_id=receipt.execution_id,
            receipt_id=receipt.receipt_id,
            verifier_id=self.name,
            status=VerificationStatus.INCONCLUSIVE,
            expected_state={},
            observed_state={"status": status},
            evidence={"note": f"Unknown status: {status}"},
            verified_at=time.time(),
        )


BUILTIN_VERIFIERS: Dict[str, Verifier] = {
    "math.add": MathVerifier(),
    "filesystem.write": FilesystemVerifier(),
    "file.write": FilesystemVerifier(),
    "opencode.run": OpenCodeRunVerifier(),
    "integrity_check": IntegrityVerifier(),
}
