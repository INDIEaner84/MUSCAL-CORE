import logging
import os
import threading

from features.provenance.context import ProvenanceContext
from features.provenance.decision_writer import write_decision
from runtime.kernel.governance import GovernanceSync, GovernanceLimits
from schema import FeedbackReport, KernelResult

log = logging.getLogger("muscal.stage.governance")


class GovernanceStage:
    name = "governance"
    order = 5

    def __init__(self, kernel):
        self.k = kernel
        self._governance = None
        self._lock = threading.Lock()

    def _get_governance(self):
        if self._governance is None:
            limits = GovernanceLimits(
                max_iterations=int(os.environ.get("MUSCAL_MAX_ITERATIONS", "25")),
                max_tokens_per_session=int(os.environ.get("MUSCAL_MAX_TOKENS", "100000")),
                max_cost_usd=float(os.environ.get("MUSCAL_MAX_COST", "2.0")),
            )
            self._governance = GovernanceSync(limits=limits)
        return self._governance

    def _record_decision(self, ctx, decision_id, action, status, reason):
        try:
            from pathlib import Path
            db_path = Path(os.environ.get(
                "MUSCAL_DB_PATH",
                str(Path(__file__).parent.parent.parent / "storage" / "muscal.db")
            ))
            write_decision(
                db_path=db_path,
                decision_id=decision_id,
                trace_id=ctx.get("trace_id"),
                span_id=ProvenanceContext.get_span_id(),
                governance_action=action,
                decision_status=status,
                reasoning=reason,
                decision_type="governance",
            )
        except Exception as e:
            log.warning("Failed to record governance decision: %s", e)

    def process(self, ctx):
        if "trace_id" not in ctx:
            ctx["trace_id"] = ProvenanceContext.generate_trace_id()
        else:
            ProvenanceContext.set_trace_id(ctx["trace_id"])

        g = self._get_governance()
        decision_id = ProvenanceContext.generate_decision_id()
        ctx["decision_id"] = decision_id

        allowed = g.consume_iteration("pipeline")
        if not allowed:
            violations = g.get_violations("pipeline")
            reason = violations[-1]["message"] if violations else "iteration_limit_exceeded"
            ctx["governance_decision"] = "blocked"
            ctx["governance_status"] = "violation"
            ctx["governance_reason"] = reason
            ctx["_early_exit"] = True
            ctx["_early_result"] = KernelResult(
                mcxf=None, execution=[], memory_id=None,
                feedback=FeedbackReport(), success=False,
                errors=[reason], execution_plan=None,
            )
            self._record_decision(ctx, decision_id, "block", "violation", reason)
            return ctx

        ctx["governance_decision"] = "allowed"
        ctx["governance_status"] = "ok"
        ctx["governance_reason"] = None
        self._record_decision(ctx, decision_id, "allow", "active", None)
        return ctx
