import time
import os
import subprocess
import shlex
import re
from features.identity.uuid7 import uuid7
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from features.provenance.context import ProvenanceContext


RESERVED = {
    "console.print", "filesystem.write", "math.add",
    "file.write",
    "browser.open", "browser.click", "browser.type",
    "browser.extract_text", "browser.screenshot", "browser.scroll",
    "desktop.screenshot", "desktop.type", "desktop.click",
    "desktop.open_app", "desktop.move", "desktop.keypress",
    "opencode.run",
}

_GLOBAL_EVENT_STORE = None
_GLOBAL_DEFAULT_TIMEOUT = 300


def set_global_event_store(es):
    global _GLOBAL_EVENT_STORE
    _GLOBAL_EVENT_STORE = es


def get_global_event_store():
    return _GLOBAL_EVENT_STORE


def set_global_default_timeout(timeout):
    global _GLOBAL_DEFAULT_TIMEOUT
    _GLOBAL_DEFAULT_TIMEOUT = timeout


def get_global_default_timeout():
    return _GLOBAL_DEFAULT_TIMEOUT


_UNSET_TIMEOUT = object()


class VerificationStatus:
    PENDING = "pending"
    EXECUTED = "executed"
    VERIFIED = "verified"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    NOT_SUPPORTED = "not_supported"
    TAMPERED = "tampered"

    _CANONICAL = {PENDING, EXECUTED, VERIFIED, FAILED, INCONCLUSIVE, NOT_SUPPORTED, TAMPERED}

    @classmethod
    def is_valid(cls, status):
        return status in cls._CANONICAL


class VerificationResult:
    __slots__ = (
        "verification_id", "execution_id", "receipt_id", "verifier_id",
        "status", "expected_state", "observed_state", "state_diff",
        "evidence", "verified_at",
        "decision_id",
    )

    def __init__(self, verification_id="", execution_id="", receipt_id="",
                 verifier_id="", status="pending", expected_state=None,
                 observed_state=None, state_diff=None, evidence=None, verified_at=0.0,
                 decision_id=""):
        self.verification_id = verification_id or uuid7()
        self.execution_id = execution_id
        self.receipt_id = receipt_id
        self.verifier_id = verifier_id
        self.status = status if VerificationStatus.is_valid(status) else VerificationStatus.PENDING
        self.expected_state = dict(expected_state or {})
        self.observed_state = dict(observed_state or {})
        self.state_diff = dict(state_diff or {})
        self.evidence = dict(evidence or {})
        self.verified_at = verified_at or time.time()
        self.decision_id = decision_id or ""

    def to_dict(self):
        return {
            "verification_id": self.verification_id,
            "execution_id": self.execution_id,
            "receipt_id": self.receipt_id,
            "verifier_id": self.verifier_id,
            "status": self.status,
            "expected_state": self.expected_state,
            "observed_state": self.observed_state,
            "state_diff": self.state_diff,
            "evidence": self.evidence,
            "verified_at": self.verified_at,
            "decision_id": self.decision_id,
        }

    @staticmethod
    def from_dict(d):
        return VerificationResult(
            verification_id=d.get("verification_id", ""),
            execution_id=d.get("execution_id", ""),
            receipt_id=d.get("receipt_id", ""),
            verifier_id=d.get("verifier_id", ""),
            status=d.get("status", "pending"),
            expected_state=d.get("expected_state", {}),
            observed_state=d.get("observed_state", {}),
            state_diff=d.get("state_diff", {}),
            evidence=d.get("evidence", {}),
            verified_at=d.get("verified_at", 0.0),
            decision_id=d.get("decision_id", ""),
        )


class ExecutionReceipt:
    __slots__ = (
        "receipt_id", "tool_name", "args", "execution_time",
        "result_data", "success",
        "execution_id", "correlation_id", "causation_id",
        "trace_id", "span_id", "decision_id",
        "request_id", "plan_id", "step_id",
        "agent_id", "model_id", "cognitive_unit_id",
        "retry_count", "attempt_number", "attempt_id",
        "_verification_result", "_integrity_hash", "_finalized", "_receipt_version",
    )

    RECEIPT_VERSION = "2.0.0"

    def __init__(self, tool_name="", args=None, execution_time=0.0, result_data=None,
                 success=False, execution_id="", correlation_id="", causation_id="",
                 receipt_id="", trace_id=None, span_id=None, decision_id=None,
                 request_id="", plan_id="", step_id="",
                 agent_id="", model_id="", cognitive_unit_id="",
                 retry_count=0, attempt_number=0, attempt_id=""):
        self.receipt_id = receipt_id or uuid7()
        self.tool_name = tool_name
        self.args = dict(args or {})
        self.execution_time = execution_time
        self.result_data = result_data
        self.success = success
        self.execution_id = execution_id or uuid7()
        self.correlation_id = correlation_id or ""
        self.causation_id = causation_id or ""
        self.trace_id = trace_id or ""
        self.span_id = span_id or ""
        self.decision_id = decision_id or ""
        self.request_id = request_id or ""
        self.plan_id = plan_id or ""
        self.step_id = step_id or ""
        self.agent_id = agent_id or ""
        self.model_id = model_id or ""
        self.cognitive_unit_id = cognitive_unit_id or ""
        self.retry_count = retry_count
        self.attempt_number = attempt_number
        self.attempt_id = attempt_id or uuid7()
        self._verification_result = None
        self._integrity_hash = ""
        self._finalized = False
        self._receipt_version = 1

    def finalize(self):
        if self._finalized:
            return
        raw = (
            str(self.receipt_id) + "|" +
            str(self.tool_name) + "|" +
            json.dumps(self.args, sort_keys=True, default=str) + "|" +
            json.dumps(self.result_data, sort_keys=True, default=str) + "|" +
            str(self.success) + "|" +
            str(self.execution_time) + "|" +
            str(self.execution_id) + "|" +
            str(self.correlation_id) + "|" +
            str(self.causation_id) + "|" +
            str(self.trace_id) + "|" +
            str(self.span_id) + "|" +
            str(self.decision_id) + "|" +
            str(self.request_id) + "|" +
            str(self.plan_id) + "|" +
            str(self.step_id) + "|" +
            str(self.agent_id) + "|" +
            str(self.model_id) + "|" +
            str(self.cognitive_unit_id) + "|" +
            str(self.retry_count) + "|" +
            str(self.attempt_number) + "|" +
            str(self.attempt_id)
        )
        self._integrity_hash = hashlib.sha256(raw.encode()).hexdigest()
        self._finalized = True

    @property
    def finalized(self):
        return self._finalized

    @property
    def integrity_hash(self):
        return self._integrity_hash

    def verify_integrity(self):
        if not self._finalized:
            return False
        saved_hash = self._integrity_hash
        self._finalized = False
        self._integrity_hash = ""
        self.finalize()
        return self._integrity_hash == saved_hash

    def verification_result(self):
        return self._verification_result

    def set_verification(self, vr):
        self._verification_result = vr

    @property
    def verification_status(self):
        if self._verification_result is None:
            return VerificationStatus.PENDING
        return self._verification_result.status

    @property
    def verification_detail(self):
        if self._verification_result is None:
            return ""
        return json.dumps({
            "verifier_id": self._verification_result.verifier_id,
            "expected": self._verification_result.expected_state,
            "observed": self._verification_result.observed_state,
        })

    def to_dict(self):
        d = {
            "receipt_id": self.receipt_id,
            "tool": self.tool_name,
            "args": self.args,
            "execution_time": self.execution_time,
            "result_data": self.result_data,
            "success": self.success,
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "plan_id": self.plan_id,
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "cognitive_unit_id": self.cognitive_unit_id,
            "retry_count": self.retry_count,
            "attempt_number": self.attempt_number,
            "attempt_id": self.attempt_id,
            "integrity_hash": self._integrity_hash,
            "finalized": self._finalized,
            "_receipt_version": 2,
        }
        if self._verification_result is not None:
            d["verification"] = self._verification_result.to_dict()
        return d

    @staticmethod
    def from_dict(d):
        receipt = ExecutionReceipt(
            tool_name=d.get("tool", ""),
            args=d.get("args", {}),
            execution_time=d.get("execution_time", 0.0),
            result_data=d.get("result_data"),
            success=d.get("success", False),
            execution_id=d.get("execution_id", ""),
            correlation_id=d.get("correlation_id", ""),
            causation_id=d.get("causation_id", ""),
            receipt_id=d.get("receipt_id", ""),
            trace_id=d.get("trace_id"),
            span_id=d.get("span_id"),
            decision_id=d.get("decision_id"),
            request_id=d.get("request_id", ""),
            plan_id=d.get("plan_id", ""),
            step_id=d.get("step_id", ""),
            agent_id=d.get("agent_id", ""),
            model_id=d.get("model_id", ""),
            cognitive_unit_id=d.get("cognitive_unit_id", ""),
            retry_count=d.get("retry_count", 0),
            attempt_number=d.get("attempt_number", 0),
            attempt_id=d.get("attempt_id", ""),
        )
        receipt._integrity_hash = d.get("integrity_hash", "")
        receipt._finalized = d.get("finalized", False)
        receipt._receipt_version = d.get("_receipt_version", 1)
        v_raw = d.get("verification")
        if v_raw and isinstance(v_raw, dict):
            receipt.set_verification(VerificationResult.from_dict(v_raw))
        return receipt


class ToolResult:
    __slots__ = ("tool_name", "success", "output", "error", "metadata", "execution_time", "receipt")

    def __init__(self, tool_name="", success=False, output=None, error="", metadata=None, execution_time=0.0, receipt=None):
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        self.execution_time = execution_time
        self.receipt = receipt

    def to_dict(self):
        d = {
            "tool": self.tool_name,
            "status": "success" if self.success else "error",
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
        }
        if self.receipt is not None:
            d["receipt"] = self.receipt.to_dict() if hasattr(self.receipt, "to_dict") else self.receipt
        return d

    @staticmethod
    def from_dict(d):
        receipt_raw = d.get("receipt")
        receipt = None
        if receipt_raw and isinstance(receipt_raw, dict):
            receipt = ExecutionReceipt.from_dict(receipt_raw)
        return ToolResult(
            tool_name=d.get("tool", ""),
            success=d.get("status") == "success",
            output=d.get("output"),
            error=d.get("error", ""),
            metadata=d.get("metadata", {}),
            execution_time=d.get("execution_time", 0.0),
            receipt=receipt,
        )


class UnifiedToolRuntime:
    def __init__(self, safety_gate=None, receipt_store=None):
        self._executors = {}
        self._schemas = {}
        self._safety_gate = safety_gate
        self._verifiers = {}
        self._receipt_store = receipt_store if receipt_store is not None else {}
        self._execution_store = {}
        self._verification_store = {}
        self._expected_state_store = {}
        self._executor_pool = ThreadPoolExecutor(max_workers=4)
        self._on_receipt_callback = None
        self._on_verification_callback = None
        self._default_timeout = get_global_default_timeout()
        self._pending_futures = {}

    def set_default_timeout(self, timeout):
        self._default_timeout = timeout

    def shutdown(self, wait=True):
        for fid, future in list(self._pending_futures.items()):
            future.cancel()
        self._pending_futures.clear()
        self._executor_pool.shutdown(wait=wait)

    def set_receipt_callback(self, callback):
        self._on_receipt_callback = callback

    def set_verification_callback(self, callback):
        self._on_verification_callback = callback

    def register_tool(self, name, executor, schema=None, verifier=None):
        if name not in RESERVED and schema is None:
            raise ValueError(f"Tool '{name}' requires a schema if not in RESERVED set")
        self._executors[name] = executor
        self._schemas[name] = schema
        if verifier is not None:
            self._verifiers[name] = verifier

    def register_executor(self, name, executor):
        self._executors[name] = executor

    def register_verifier(self, name, verifier_fn):
        self._verifiers[name] = verifier_fn

    def resolve(self, name):
        fn = self._executors.get(name)
        if fn is None:
            return None
        return fn

    def capabilities(self):
        return list(self._executors.keys())

    def health(self):
        return {name: callable(fn) for name, fn in self._executors.items()}

    def schema(self, name):
        return self._schemas.get(name)

    def receipts(self):
        return self._receipts_all()

    def receipt(self, receipt_id):
        return self._get_receipt(receipt_id)

    def _put_receipt(self, receipt):
        if isinstance(self._receipt_store, dict):
            self._receipt_store[receipt.receipt_id] = receipt
        else:
            self._receipt_store.put(receipt.receipt_id, receipt)

    def _get_receipt(self, receipt_id):
        if isinstance(self._receipt_store, dict):
            return self._receipt_store.get(receipt_id)
        return self._receipt_store.get(receipt_id)

    def _receipts_all(self):
        if isinstance(self._receipt_store, dict):
            return list(self._receipt_store.values())
        return self._receipt_store.all()

    def _build_receipt(self, name, args, elapsed, result_data=None, success=False,
                       execution_id="", correlation_id="", causation_id="",
                       trace_id=None, span_id=None, decision_id=None,
                       request_id="", plan_id="", step_id="",
                       agent_id="", model_id="", cognitive_unit_id="",
                       retry_count=0, attempt_number=0):
        receipt = ExecutionReceipt(
            tool_name=name, args=args, execution_time=elapsed,
            result_data=result_data, success=success,
            execution_id=execution_id, correlation_id=correlation_id,
            causation_id=causation_id,
            trace_id=trace_id, span_id=span_id, decision_id=decision_id,
            request_id=request_id, plan_id=plan_id, step_id=step_id,
            agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
            retry_count=retry_count, attempt_number=attempt_number,
        )
        receipt.finalize()
        self._put_receipt(receipt)
        if self._on_receipt_callback:
            self._on_receipt_callback(receipt)
        if execution_id:
            self._execution_store[execution_id] = receipt
        return receipt

    def execute(self, name, args=None, execution_id="", correlation_id="",
                causation_id="", request_id="", plan_id="", step_id="",
                agent_id="", model_id="", cognitive_unit_id="",
                retry_count=0, attempt_number=0, timeout=_UNSET_TIMEOUT):
        args = args or {}
        start = time.time()

        trace_id = ProvenanceContext.get_trace_id()
        span_id = ProvenanceContext.generate_span_id()
        decision_id = ProvenanceContext.get_decision_id()

        if not execution_id:
            execution_id = uuid7()

        if execution_id in self._execution_store:
            elapsed = time.time() - start
            return ToolResult(
                tool_name=name, success=False, output=None,
                error=f"DUPLICATE_EXECUTION_ID: '{execution_id}' already processed",
                execution_time=elapsed,
                metadata={"execution_id": execution_id, "dedup": True},
            )

        fn = self._executors.get(name)
        if fn is None:
            elapsed = time.time() - start
            receipt = self._build_receipt(name, args, elapsed, success=False,
                                           execution_id=execution_id, correlation_id=correlation_id,
                                           causation_id=causation_id,
                                           trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                           request_id=request_id, plan_id=plan_id, step_id=step_id,
                                           agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                           retry_count=retry_count, attempt_number=attempt_number)
            return ToolResult(
                tool_name=name, success=False, output=None,
                error=f"Unknown tool: '{name}'",
                execution_time=elapsed, receipt=receipt,
            )

        if self._safety_gate is not None:
            gate_result = self._safety_gate.check(name, args)
            if not gate_result.allowed:
                elapsed = time.time() - start
                receipt = self._build_receipt(name, args, elapsed, success=False,
                                               execution_id=execution_id, correlation_id=correlation_id,
                                               causation_id=causation_id,
                                               trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                               request_id=request_id, plan_id=plan_id, step_id=step_id,
                                               agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                               retry_count=retry_count, attempt_number=attempt_number)
                blocked_vr = VerificationResult(
                    execution_id=execution_id, receipt_id=receipt.receipt_id,
                    verifier_id="safety_gate", status=VerificationStatus.FAILED,
                    expected_state={"allowed": True},
                    observed_state={"allowed": False, "reason": gate_result.reason},
                    evidence={"gate": gate_result.to_dict()},
                )
                receipt.set_verification(blocked_vr)
                return ToolResult(
                    tool_name=name, success=False, output=None,
                    error=gate_result.reason or "BLOCKED_BY_SAFETY_GATE",
                    metadata={"gate": gate_result.to_dict()},
                    execution_time=elapsed, receipt=receipt,
                )

        if timeout is _UNSET_TIMEOUT:
            effective_timeout = self._default_timeout
        else:
            effective_timeout = timeout
        submitted_future = None
        try:
            if effective_timeout is not None:
                future = self._executor_pool.submit(fn, args)
                submitted_future = future
                self._pending_futures[id(future)] = future
                result = future.result(timeout=effective_timeout)
            else:
                result = fn(args)
        except FutureTimeoutError:
            if submitted_future is not None:
                submitted_future.cancel()
                self._pending_futures.pop(id(submitted_future), None)
            elapsed = time.time() - start
            receipt = self._build_receipt(name, args, elapsed, success=False,
                                           execution_id=execution_id, correlation_id=correlation_id,
                                           causation_id=causation_id,
                                           trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                           request_id=request_id, plan_id=plan_id, step_id=step_id,
                                           agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                           retry_count=retry_count, attempt_number=attempt_number)
            timeout_val = effective_timeout if effective_timeout is not None else "infinite"
            return ToolResult(
                tool_name=name, success=False, output=None,
                error=f"TIMEOUT: tool '{name}' exceeded {timeout_val}s",
                execution_time=elapsed, receipt=receipt,
            )
        except Exception as e:
            elapsed = time.time() - start
            receipt = self._build_receipt(name, args, elapsed, success=False,
                                           execution_id=execution_id, correlation_id=correlation_id,
                                           causation_id=causation_id,
                                           trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                           request_id=request_id, plan_id=plan_id, step_id=step_id,
                                           agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                           retry_count=retry_count, attempt_number=attempt_number)
            failed_vr = VerificationResult(
                execution_id=execution_id, receipt_id=receipt.receipt_id,
                verifier_id="executor", status=VerificationStatus.FAILED,
                expected_state={"success": True},
                observed_state={"success": False, "error": str(e)},
                evidence={"exception": str(e)},
            )
            receipt.set_verification(failed_vr)
            return ToolResult(
                tool_name=name, success=False, output=None,
                error=str(e), execution_time=elapsed, receipt=receipt,
            )

        elapsed = time.time() - start
        if isinstance(result, dict):
            success = result.get("status") in ("success", "written", "saved", "ok", "opened", "clicked", "typed", "output")
            success = success or "error" not in result
            receipt = self._build_receipt(name, args, elapsed, result_data=result, success=success,
                                           execution_id=execution_id, correlation_id=correlation_id,
                                           causation_id=causation_id,
                                           trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                           request_id=request_id, plan_id=plan_id, step_id=step_id,
                                           agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                           retry_count=retry_count, attempt_number=attempt_number)
            return ToolResult(
                tool_name=name, success=success,
                output=result, error=result.get("error", ""),
                execution_time=elapsed, receipt=receipt,
            )
        if isinstance(result, ToolResult):
            receipt = self._build_receipt(name, args, elapsed, result_data=result.to_dict(), success=result.success,
                                           execution_id=execution_id, correlation_id=correlation_id,
                                           causation_id=causation_id,
                                           trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                           request_id=request_id, plan_id=plan_id, step_id=step_id,
                                           agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                           retry_count=retry_count, attempt_number=attempt_number)
            result.execution_time = elapsed
            result.receipt = receipt
            return result
        receipt = self._build_receipt(name, args, elapsed, result_data=str(result), success=True,
                                       execution_id=execution_id, correlation_id=correlation_id,
                                       causation_id=causation_id,
                                       trace_id=trace_id, span_id=span_id, decision_id=decision_id,
                                       request_id=request_id, plan_id=plan_id, step_id=step_id,
                                       agent_id=agent_id, model_id=model_id, cognitive_unit_id=cognitive_unit_id,
                                       retry_count=retry_count, attempt_number=attempt_number)
        return ToolResult(
            tool_name=name, success=True, output=result,
            execution_time=elapsed, receipt=receipt,
        )

    def verify(self, receipt_id=None, name=None):
        if receipt_id is not None:
            receipt = self._get_receipt(receipt_id)
            if receipt is None:
                return None
            return self._verify_one(receipt)
        if name is not None:
            results = []
            for r in self._receipts_all():
                if r.tool_name == name:
                    results.append(self._verify_one(r))
            return results
        results = {}
        for r in self._receipts_all():
            results[r.receipt_id] = self._verify_one(r)
        return results

    def _verify_one(self, receipt):
        if not receipt.finalized:
            vr = VerificationResult(
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id="integrity_check",
                status=VerificationStatus.TAMPERED,
                expected_state={"finalized": True},
                observed_state={"finalized": False},
            )
            receipt.set_verification(vr)
            self._verification_store[vr.verification_id] = vr
            if self._on_verification_callback:
                self._on_verification_callback(vr)
            return vr

        if not receipt.verify_integrity():
            vr = VerificationResult(
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id="integrity_check",
                status=VerificationStatus.TAMPERED,
                expected_state={"integrity_hash": receipt.integrity_hash},
                observed_state={"integrity_hash": receipt.integrity_hash, "tampered": True},
                evidence={"note": "Receipt content hash does not match"},
            )
            receipt.set_verification(vr)
            self._verification_store[vr.verification_id] = vr
            if self._on_verification_callback:
                self._on_verification_callback(vr)
            return vr

        verifier = self._verifiers.get(receipt.tool_name)
        if verifier is None:
            vr = VerificationResult(
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id="none",
                status=VerificationStatus.NOT_SUPPORTED,
                expected_state={},
                observed_state={},
                evidence={"note": "No verifier registered for " + receipt.tool_name},
            )
            receipt.set_verification(vr)
            self._verification_store[vr.verification_id] = vr
            if self._on_verification_callback:
                self._on_verification_callback(vr)
            return vr

        try:
            expected_state = self.get_expected_state(receipt.execution_id)
            result = verifier(receipt, expected_state=expected_state)
            if result is True:
                vr = VerificationResult(
                    execution_id=receipt.execution_id,
                    receipt_id=receipt.receipt_id,
                    verifier_id=receipt.tool_name,
                    status=VerificationStatus.VERIFIED,
                    expected_state={"verifiable": True},
                    observed_state={"verifiable": True},
                    evidence={"verified_by": receipt.tool_name},
                )
            elif result is False:
                vr = VerificationResult(
                    execution_id=receipt.execution_id,
                    receipt_id=receipt.receipt_id,
                    verifier_id=receipt.tool_name,
                    status=VerificationStatus.FAILED,
                    expected_state={"verifiable": True},
                    observed_state={"verifiable": False},
                    evidence={"verifier": receipt.tool_name, "reason": "Verifier returned False"},
                )
            else:
                vr = VerificationResult(
                    execution_id=receipt.execution_id,
                    receipt_id=receipt.receipt_id,
                    verifier_id=receipt.tool_name,
                    status=VerificationStatus.INCONCLUSIVE,
                    expected_state={},
                    observed_state={},
                    evidence={"verifier": receipt.tool_name, "detail": str(result)},
                )
        except Exception as e:
            vr = VerificationResult(
                execution_id=receipt.execution_id,
                receipt_id=receipt.receipt_id,
                verifier_id=receipt.tool_name,
                status=VerificationStatus.INCONCLUSIVE,
                expected_state={},
                observed_state={},
                evidence={"verifier": receipt.tool_name, "error": str(e)},
            )

        receipt.set_verification(vr)
        self._verification_store[vr.verification_id] = vr
        if self._on_verification_callback:
            self._on_verification_callback(vr)
        return vr

    def verification_results(self):
        return list(self._verification_store.values())

    def set_expected_state(self, execution_id, expected: dict):
        if execution_id in self._execution_store:
            raise RuntimeError(
                f"Cannot set expected state for '{execution_id}': execution already processed"
            )
        self._expected_state_store[execution_id] = dict(expected)

    def get_expected_state(self, execution_id):
        return self._expected_state_store.get(execution_id, {})

    def has_expected_state(self, execution_id):
        return execution_id in self._expected_state_store

    def execution_exists(self, execution_id):
        return execution_id in self._execution_store


_UNAVAILABLE = object()


class BrowserAgent:
    def __init__(self, headless=False):
        self._playwright = None
        self._browser = None
        self._page = None
        self.headless = headless
        self._available = False

    def start(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright()
            self._playwright = self._pw.__enter__()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self):
        return self._available

    def open(self, url):
        if not self._available:
            return {"status": "stub", "title": "stub", "url": url}
        self._page.goto(url, timeout=15000)
        return {"status": "opened", "title": self._page.title(), "url": url}

    def click(self, selector):
        if not self._available:
            return {"status": "stub", "selector": selector}
        self._page.click(selector)
        return {"status": "clicked", "selector": selector}

    def type_text(self, selector, text):
        if not self._available:
            return {"status": "stub", "selector": selector, "text": text}
        self._page.fill(selector, text)
        return {"status": "typed", "selector": selector, "text": text}

    def extract_text(self, selector="body"):
        if not self._available:
            return {"status": "stub", "text": ""}
        element = self._page.query_selector(selector)
        text = element.inner_text() if element else ""
        return {"status": "extracted", "text": text[:10000]}

    def screenshot(self, path="screenshot.png"):
        if not self._available:
            return {"status": "stub", "path": path}
        self._page.screenshot(path=path)
        return {"status": "saved", "path": path}

    def scroll(self, direction="down"):
        if not self._available:
            return {"status": "stub", "direction": direction}
        delta = 500 if direction == "down" else -500
        self._page.evaluate(f"window.scrollBy(0, {delta})")
        return {"status": "scrolled", "direction": direction}

    def close(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.__exit__(None, None, None)


DEFAULT_ALLOWED_WRITE_PATHS = [
    "/tmp",
]

DEFAULT_MAX_WRITE_SIZE = 1_048_576

DEFAULT_ALLOWED_OPENCODE_COMMANDS = ["ls", "cat", "echo", "python3 -c", "pwd", "wc", "head", "tail"]


def _register_all_browser(browser_agent, rt, safety_gate):
    def make_exec(name, agent_fn):
        def exec_fn(args):
            if not browser_agent.available:
                browser_agent.start()
            return agent_fn(**args)
        return exec_fn

    rt.register_tool("browser.open", make_exec("browser.open", browser_agent.open))
    rt.register_tool("browser.click", make_exec("browser.click", browser_agent.click))
    rt.register_tool("browser.type", make_exec("browser.type", browser_agent.type_text))
    rt.register_tool("browser.extract_text", make_exec("browser.extract_text", browser_agent.extract_text))
    rt.register_tool("browser.screenshot", make_exec("browser.screenshot", browser_agent.screenshot))
    rt.register_verifier("browser.screenshot", lambda r, expected_state=None: (
        r.result_data
        and r.result_data.get("status") == "saved"
        and os.path.exists(r.args.get("path", "screenshot.png"))
    ))
    rt.register_tool("browser.scroll", make_exec("browser.scroll", browser_agent.scroll))


def _register_all_desktop(rt):
    for name in ("desktop.screenshot", "desktop.type", "desktop.click",
                 "desktop.open_app", "desktop.move", "desktop.keypress"):
        rt.register_tool(name, lambda args, _n=name: {
            "status": "unavailable", "tool": _n,
            "error": f"Desktop runtime not available (no pyautogui)"
        })


def _register_console_print(rt):
    rt.register_tool("console.print", lambda args: {
        "status": "success", "printed": print(args["message"]) or args["message"],
    })


def _register_file_write(rt, allowed_paths=None, max_size=None):
    allowed_paths = allowed_paths or DEFAULT_ALLOWED_WRITE_PATHS
    max_size = max_size or DEFAULT_MAX_WRITE_SIZE
    basedir = os.path.dirname(os.path.abspath(__file__))
    storage_path = os.path.join(os.path.dirname(basedir), "storage")
    abs_allowed = [os.path.abspath(p) for p in allowed_paths] + [os.path.abspath(storage_path)]

    def exec_fn(args):
        path = args.get("path", "")
        content = args.get("content", "")
        abspath = os.path.abspath(path)
        allowed = any(abspath.startswith(base) for base in abs_allowed)
        if not allowed:
            return {"status": "blocked", "path": path, "error": f"path not allowed"}
        if len(content) > max_size:
            return {"status": "blocked", "path": path, "error": "content exceeds max size"}
        os.makedirs(os.path.dirname(abspath), exist_ok=True)
        with open(abspath, "w") as f:
            f.write(content)
        return {"status": "written", "path": path}

    rt.register_tool("filesystem.write", exec_fn)
    rt.register_tool("file.write", exec_fn)
    file_verifier = _make_file_write_verifier(allowed_paths)
    rt.register_verifier("filesystem.write", file_verifier)
    rt.register_verifier("file.write", file_verifier)

def _make_file_write_verifier(allowed_paths=None):
    allowed_paths = allowed_paths or DEFAULT_ALLOWED_WRITE_PATHS
    basedir = os.path.dirname(os.path.abspath(__file__))
    storage_path = os.path.join(os.path.dirname(basedir), "storage")
    abs_allowed = [os.path.abspath(p) for p in allowed_paths] + [os.path.abspath(storage_path)]

    def verify(receipt, expected_state=None):
        path = receipt.args.get("path", "")
        abspath = os.path.abspath(path)
        allowed = any(abspath.startswith(base) for base in abs_allowed)
        if not allowed:
            return receipt.result_data and receipt.result_data.get("status") == "blocked"
        if expected_state and "content" in expected_state:
            expected_content = expected_state["content"]
            if not os.path.exists(abspath):
                return "UNVERIFIED: file not found"
            with open(abspath) as f:
                actual_content = f.read()
                return actual_content == expected_content
        if receipt.result_data and receipt.result_data.get("status") == "ok":
            written = os.path.exists(abspath)
            if written:
                return True
            return "UNVERIFIED: file not found after write"
        return receipt.result_data and receipt.result_data.get("status") == "blocked"
    return verify


def _register_math_add(rt):
    rt.register_tool("math.add", lambda args: {
        "result": args.get("a", 0) + args.get("b", 0),
    })
    rt.register_verifier("math.add", lambda r, expected_state=None: (
        r.result_data
        and r.result_data.get("result") == r.args.get("a", 0) + r.args.get("b", 0)
    ))


def _register_opencode_run(rt, allowed_commands=None):
    allowed_commands = allowed_commands or DEFAULT_ALLOWED_OPENCODE_COMMANDS

    def exec_fn(args):
        command = args.get("command", "")
        stripped = command.strip()
        allowed = any(stripped.startswith(c) or stripped == c for c in allowed_commands)
        if not allowed:
            return {
                "status": "blocked", "command": command,
                "error": f"command not in allowlist: {allowed_commands}",
            }
        try:
            parts = shlex.split(stripped)
            result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
            output = (result.stdout or result.stderr).strip()
            return {"status": "ok", "command": command, "output": output[:2000]}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "command": command}
        except Exception as e:
            return {"status": "error", "command": command, "error": str(e)}

    rt.register_tool("opencode.run", exec_fn)

    def _verify_opencode_run(receipt, expected_state=None):
        command = receipt.args.get("command", "")
        stripped = command.strip()
        allowed = any(stripped.startswith(c) or stripped == c for c in allowed_commands)
        if not allowed:
            return receipt.result_data and receipt.result_data.get("status") == "blocked"
        if not receipt.result_data:
            return False
        return receipt.result_data.get("status") in ("ok",)

    rt.register_verifier("opencode.run", _verify_opencode_run)


def create_default_utr(safety_gate=None, browser_agent=None, event_store=None):
    if event_store is None:
        event_store = get_global_event_store()
    rt = UnifiedToolRuntime(safety_gate=safety_gate)
    if event_store is not None:
        rt.set_receipt_callback(lambda receipt: event_store.store_receipt(receipt))
        rt.set_verification_callback(lambda vr: event_store.store_verification(vr))
    _register_console_print(rt)
    _register_file_write(rt)
    _register_math_add(rt)
    _register_opencode_run(rt)
    if browser_agent is None:
        browser_agent = BrowserAgent(headless=True)
    _register_all_browser(browser_agent, rt, safety_gate)
    _register_all_desktop(rt)
    if safety_gate is not None:
        for name in rt.capabilities():
            safety_gate.permit(name)
    return rt, browser_agent
