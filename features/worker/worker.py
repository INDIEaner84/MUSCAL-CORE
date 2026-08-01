import time
import uuid

WORKER_STATUS = "ACTIVE"
WORKER_VERSION = "2.0.0"


FAIL_FAST = "fail_fast"
CONTINUE_INDEPENDENT = "continue_independent"
RETRYABLE = "retryable"
NON_RETRYABLE = "non_retryable"


class WorkerPlan:
    def __init__(self, plan_id, steps):
        self.plan_id = plan_id
        self.steps = steps
        self.status = "created"

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
        }


class WorkerStep:
    def __init__(self, step_id, action, tool, args, depends_on=None,
                 failure_policy=FAIL_FAST, max_retries=0):
        self.step_id = step_id
        self.action = action
        self.tool = tool
        self.args = dict(args) if args else {}
        self.depends_on = depends_on or []
        self.failure_policy = failure_policy
        self.max_retries = max_retries
        self.retry_count = 0
        self.status = "pending"
        self.result = None
        self.error = None

    def to_dict(self):
        return {
            "step_id": self.step_id,
            "action": self.action,
            "tool": self.tool,
            "args": dict(self.args),
            "depends_on": list(self.depends_on),
            "failure_policy": self.failure_policy,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "status": self.status,
            "error": self.error,
        }


class WorkerResult:
    def __init__(self, success, plan_id, step_results, errors=None,
                 receipts=None):
        self.success = success
        self.plan_id = plan_id
        self.step_results = step_results
        self.errors = errors or []
        self.receipts = receipts or []

    def to_dict(self):
        return {
            "success": self.success,
            "plan_id": self.plan_id,
            "step_results": self.step_results,
            "errors": list(self.errors),
            "receipts": [r.to_dict() if hasattr(r, "to_dict") else r
                         for r in self.receipts],
        }


class Worker:
    def __init__(self, worker_id, tool_runtime=None, safety_gate=None,
                 governance=None, agent_id="", cognitive_unit_id=""):
        self.id = worker_id
        self.tool_runtime = tool_runtime
        self.safety_gate = safety_gate
        self.governance = governance
        self.agent_id = agent_id
        self.cognitive_unit_id = cognitive_unit_id
        self._current_request_id = ""

    def plan(self, context, request_id=""):
        if not context:
            context = {}
        tool_name = context.get("tool", "")
        args = context.get("args", {})
        task_type = context.get("task_type", "general")
        if request_id:
            self._current_request_id = request_id

        if not tool_name:
            return WorkerPlan(plan_id=str(uuid.uuid4()), steps=[])

        steps = []
        step = WorkerStep(
            step_id=f"{tool_name}_{int(time.time())}_{uuid.uuid4().hex[:6]}",
            action=tool_name,
            tool=tool_name,
            args=args,
            depends_on=[],
            failure_policy=RETRYABLE if _is_retryable(tool_name) else FAIL_FAST,
            max_retries=1 if _is_retryable(tool_name) else 0,
        )
        steps.append(step)

        return WorkerPlan(plan_id=str(uuid.uuid4()), steps=steps)

    def execute_plan(self, plan):
        step_results = []
        errors = []
        receipts = []
        executed = set()
        last_execution_id = ""

        ready = [s for s in plan.steps if not s.depends_on]
        blocked = [s for s in plan.steps if s.depends_on]

        for step in ready:
            result = self._execute_step(step, plan.plan_id,
                                        causation_id=last_execution_id)
            step_results.append(result)
            executed.add(step.step_id)
            receipt = result.get("receipt")
            if receipt:
                receipts.append(receipt)
                if hasattr(receipt, "execution_id") and receipt.execution_id:
                    last_execution_id = receipt.execution_id
            step_status = result.get("status", "")
            if step_status in ("error", "no_runtime", "blocked_by_safety"):
                errors.append(result.get("error", step_status))
                if step.failure_policy == FAIL_FAST:
                    plan.status = "failed"
                    return WorkerResult(
                        success=False, plan_id=plan.plan_id,
                        step_results=step_results, errors=errors,
                        receipts=receipts,
                    )

        newly_ready = _find_ready(blocked, executed)
        for step in newly_ready:
            result = self._execute_step(step, plan.plan_id,
                                        causation_id=last_execution_id)
            step_results.append(result)
            executed.add(step.step_id)
            receipt = result.get("receipt")
            if receipt:
                receipts.append(receipt)
                if hasattr(receipt, "execution_id") and receipt.execution_id:
                    last_execution_id = receipt.execution_id
            step_status = result.get("status", "")
            if step_status in ("error", "no_runtime", "blocked_by_safety"):
                errors.append(result.get("error", step_status))

        plan.status = "completed" if not errors else "partial"
        return WorkerResult(
            success=len(errors) == 0,
            plan_id=plan.plan_id,
            step_results=step_results,
            errors=errors,
            receipts=receipts,
        )

    def execute(self, context, request_id=""):
        if not context:
            context = {}
        task_type = context.get("task_type", "general")
        if request_id:
            self._current_request_id = request_id
        plan = self.plan(context, request_id=self._current_request_id)
        if not plan.steps:
            return {
                "status": "noop",
                "worker_id": self.id,
                "task_type": task_type,
                "request_id": self._current_request_id,
            }
        result = self.execute_plan(plan)

        if not result.success and result.errors:
            step0 = result.step_results[0] if result.step_results else {}
            s0_status = step0.get("status", "")
            if s0_status == "blocked_by_safety":
                return {
                    "status": "blocked_by_safety",
                    "worker_id": self.id,
                    "reason": step0.get("error", ""),
                    "task_type": task_type,
                    "request_id": self._current_request_id,
                }
            if s0_status == "no_runtime":
                return {
                    "status": "no_runtime",
                    "worker_id": self.id,
                    "task_type": task_type,
                    "request_id": self._current_request_id,
                }
            return {
                "status": "error",
                "worker_id": self.id,
                "task_type": task_type,
                "plan_id": result.plan_id,
                "step_count": len(result.step_results),
                "errors": result.errors,
                "receipt_count": len(result.receipts),
                "request_id": self._current_request_id,
            }

        return {
            "status": "success",
            "worker_id": self.id,
            "task_type": task_type,
            "plan_id": result.plan_id,
            "step_count": len(result.step_results),
            "receipt_count": len(result.receipts),
            "request_id": self._current_request_id,
        }

    def _execute_step(self, step, plan_id="", causation_id=""):
        if self.safety_gate is not None:
            sg_result = self.safety_gate.check(step.tool, step.args)
            if not sg_result.allowed:
                step.status = "blocked_by_safety"
                return {
                    "step_id": step.step_id,
                    "status": "blocked_by_safety",
                    "error": sg_result.reason,
                }

        if self.tool_runtime is None:
            step.status = "no_runtime"
            return {"step_id": step.step_id, "status": "no_runtime"}

        attempt = 0
        while attempt <= step.max_retries:
            try:
                utr_result = self.tool_runtime.execute(
                    step.tool, step.args,
                    request_id=self._current_request_id,
                    plan_id=plan_id,
                    step_id=step.step_id,
                    agent_id=self.agent_id,
                    cognitive_unit_id=self.cognitive_unit_id,
                    causation_id=causation_id,
                    retry_count=step.retry_count,
                    attempt_number=attempt + 1,
                )
                if utr_result.success:
                    step.status = "success"
                    step.result = utr_result.output
                    r = {
                        "step_id": step.step_id,
                        "status": "success",
                        "output": utr_result.output,
                    }
                    if hasattr(utr_result, "receipt") and utr_result.receipt:
                        r["receipt"] = utr_result.receipt
                    return r
                else:
                    if attempt < step.max_retries:
                        attempt += 1
                        step.retry_count = attempt
                        continue
                    step.status = "error"
                    step.error = utr_result.error
                    r = {
                        "step_id": step.step_id,
                        "status": "error",
                        "error": utr_result.error,
                    }
                    if hasattr(utr_result, "receipt") and utr_result.receipt:
                        r["receipt"] = utr_result.receipt
                    return r
            except Exception as e:
                if attempt < step.max_retries:
                    attempt += 1
                    step.retry_count = attempt
                    continue
                step.status = "error"
                step.error = str(e)
                return {"step_id": step.step_id, "status": "error",
                        "error": str(e)}

        step.status = "error"
        return {"step_id": step.step_id, "status": "error",
                "error": "max_retries_exceeded"}

    def to_dict(self):
        return {"id": self.id, "version": WORKER_VERSION,
                "status": WORKER_STATUS}


def _is_retryable(tool_name):
    return tool_name in ("console.print", "math.add", "opencode.run")


def _find_ready(blocked, executed):
    return [s for s in blocked if all(d in executed for d in s.depends_on)]
