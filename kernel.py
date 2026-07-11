"""
MUSCAL Kernel Fusion Layer v0.1

Single entry point for all system operations.
Orchestrates: MKC → RAG → Bridge → MEL → Feedback → Memory

Integration wiring:

  INPUT ──→ RAG.retrieve ──→ RAG.enrich ──→ MKC.compile ──→ MCXF ──→
              │                  │               │             │
              ▼                  ▼               ▼             ▼
         Graph: RAG_CONTEXT  Graph: INTENT   Graph: MKC_STEP Graph: MCXF_SECTION

  ──→ Bridge.map_tasks ──→ MEL.execute ──→ Feedback ──→ Memory.store ──→ KernelResult
          │                    │               │               │
          ▼                    ▼               ▼               ▼
     Graph: EXECUTION_PLAN Graph: TOOL_      Graph:        Graph:
                            EXECUTION      CONFLICT      MEMORY_ENTRY
                             + SYSTEM_ACTION
"""

import time

from bridge import map_tasks, validate_plan
from debugger import DebugEngine
from feedback import analyze_feedback
from graph import GraphState
from mel import execute
from memory import init as mem_init
from memory import log_jsonl, store_snapshot
from mkc import mkc
from mkc_rules import apply_feedback
from plugin_registry import HOOKS, run_hooks
from rag import enrich as rag_enrich
from rag import retrieve as rag_retrieve
from schema import (
    EDGE_TYPE_CONFLICTS_WITH,
    EDGE_TYPE_CONTROLS,
    EDGE_TYPE_DEPENDS_ON,
    EDGE_TYPE_DERIVES_FROM,
    EDGE_TYPE_EXECUTES,
    EDGE_TYPE_RETRIEVES_FROM,
    EVENT_EDGE_CREATED,
    EVENT_EXECUTION_FINISHED,
    EVENT_EXECUTION_STARTED,
    EVENT_NODE_CREATED,
    EVENT_NODE_UPDATED,
    EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
    EVENT_SYSTEM_ACTION_STARTED,
    NODE_TYPE_CONFLICT,
    NODE_TYPE_EXECUTION_PLAN,
    NODE_TYPE_INTENT,
    NODE_TYPE_MCXF_SECTION,
    NODE_TYPE_MEMORY_ENTRY,
    NODE_TYPE_MKC_STEP,
    NODE_TYPE_RAG_CONTEXT,
    NODE_TYPE_SYSTEM_ACTION,
    NODE_TYPE_TOOL_EXECUTION,
    ExecutionPlan,
    FeedbackReport,
    KernelResult,
    KnowledgeTriple,
    MCXFDocument,
    dict_to_mcxf_document,
    validate_mcxf,
)
from sphere import SphereState


class MKCModule:
    def compile(self, text: str, raw_input: str = None):
        mcxf = mkc(text, raw_input=raw_input)
        ok, errs = validate_mcxf(mcxf)
        if not ok:
            raise ValueError(f"MKC compile produced invalid MCXF: {errs}")
        return mcxf

    def apply_feedback(self, report: FeedbackReport):
        apply_feedback(report)


class MELModule:
    def execute(self, plan: ExecutionPlan):
        return execute(plan)


class BridgeModule:
    def map_tasks(self, triples, intent=""):
        return map_tasks(triples, intent=intent)

    def validate(self, plan):
        return validate_plan(plan)


class FeedbackModule:
    def analyze(self, tasks, exec_result, plan):
        return analyze_feedback(tasks, exec_result, plan)


class MemoryModule:
    def init(self):
        mem_init()

    def store_snapshot(self, input_text, mcxf, result, feedback=None):
        return store_snapshot(input_text, mcxf, result, feedback)

    def log(self, entry):
        log_jsonl(entry)


class RAGModule:
    def retrieve(self, query, top_k=3):
        return rag_retrieve(query, top_k=top_k)

    def enrich(self, input_text, context):
        return rag_enrich(input_text, context)


class SystemModule:
    """Tracks system-level actions emitted by SystemAgentRuntime."""

    def __init__(self, graph=None):
        self.graph = graph

    def on_action_event(self, event):
        if self.graph is None:
            return
        etype = event.get("type", "")
        payload = event.get("payload", {})
        tool = payload.get("tool", "")
        if etype == EVENT_SYSTEM_ACTION_STARTED:
            action_id = self.graph.add_node(NODE_TYPE_SYSTEM_ACTION, {
                "tool": tool,
                "status": "running",
                "args": payload.get("args", "")
            })
            # Find the latest EXECUTION_PLAN and link via CONTROLS
            plans = [
                nid for nid, n in self.graph.nodes.items()
                if n.type == "EXECUTION_PLAN"
            ]
            if plans:
                latest_plan = sorted(plans)[-1]
                self.graph.add_edge(latest_plan, action_id, EDGE_TYPE_CONTROLS)
        elif etype in (EVENT_SYSTEM_ACTION_COMPLETED, EVENT_SYSTEM_ACTION_FAILED):
            # Find the most recent SYSTEM_ACTION node for this tool and mark it
            for nid in sorted(self.graph.nodes.keys(), reverse=True):
                n = self.graph.nodes.get(nid)
                if n and n.type == NODE_TYPE_SYSTEM_ACTION and n.payload.get("tool") == tool:
                    self.graph.update_node(
                        nid,
                        status="completed" if etype == EVENT_SYSTEM_ACTION_COMPLETED else "failed",
                        payload={"result": payload.get("result", payload.get("error", ""))}
                    )
                    break


class MuscalKernel:
    """Single entry point for all MUSCAL operations."""

    def __init__(self, enable_graph=True, enable_sphere=True, debugger=None):
        self.mkc = MKCModule()
        self.mel = MELModule()
        self.bridge = BridgeModule()
        self.feedback = FeedbackModule()
        self.memory = MemoryModule()
        self.rag = RAGModule()
        self.graph = GraphState() if enable_graph else None
        self.sphere = None
        self.system = SystemModule(graph=self.graph)
        self.debugger = debugger

        if self.graph:
            self.graph.reset_event_listeners()

        if self.graph and enable_sphere:
            self.sphere = SphereState(self.graph)
            all_events = [
                EVENT_NODE_CREATED, EVENT_NODE_UPDATED, EVENT_EDGE_CREATED,
                EVENT_EXECUTION_STARTED, EVENT_EXECUTION_FINISHED,
                EVENT_SYSTEM_ACTION_STARTED, EVENT_SYSTEM_ACTION_COMPLETED,
                EVENT_SYSTEM_ACTION_FAILED
            ]
            for evt in all_events:
                self.graph.on(evt, lambda _e: self.sphere.sync())

        # Wire system action events from the runtime
        if enable_graph:
            for evt in [EVENT_SYSTEM_ACTION_STARTED, EVENT_SYSTEM_ACTION_COMPLETED, EVENT_SYSTEM_ACTION_FAILED]:
                self.graph.on(evt, lambda e: self.system.on_action_event(e))

        self.memory.init()

    def _mcxf_dict_to_document(self, mcxf_dict: dict, input_text: str) -> MCXFDocument:
        return dict_to_mcxf_document(mcxf_dict, input_text=input_text)

    def _build_exec_result(self, mel_results):
        errors = [
            r for r in mel_results
            if isinstance(r, dict) and r.get("tool") == "UNMAPPED"
        ]
        success = all(
            isinstance(r, dict) and r.get("tool") != "UNMAPPED" and "error" not in r
            and not (isinstance(r, dict) and r.get("status") == "failed")
            for r in mel_results
        )
        return {
            "success": success,
            "tool_outputs": mel_results,
            "errors": errors,
            "runtime_logs": []
        }

    def _is_success(self, mel_results):
        return all(
            isinstance(r, dict) and r.get("tool") != "UNMAPPED" and "error" not in r
            and not (isinstance(r, dict) and r.get("status") == "failed")
            for r in mel_results
        )

    def run(self, input_text: str):
        g = self.graph
        d = self.debugger

        if g and len(g.nodes) > 10000:
            g.prune_graph()

        if d:
            d.start_execution(input_text)

        if g:
            g.emit(EVENT_EXECUTION_STARTED, {"input": input_text, "timestamp": time.time()})

        _ctx = {"input_text": input_text, "kernel": self}
        run_hooks("kernel_before", _ctx)
        _errors = []
        _stage_metrics = {}

        # 1. RAG context retrieval + enrichment
        _stage_start = time.time()
        try:
            if d:
                d.stage_enter("rag_inject", {"input": input_text})
            context = self.rag.retrieve(input_text)
            enriched_input = self.rag.enrich(input_text, context)
            if d:
                d.stage_exit("rag_inject", {
                    "context_count": len(context),
                    "enriched_length": len(enriched_input),
                }, extra_input={"context": [c.get("input_text", "") for c in context]})
                d.wait_for_step()
            intent_id = ""
            if g:
                intent_id = g.add_node(NODE_TYPE_INTENT, {"text": input_text})
                for ctx in context:
                    rag_id = g.add_node(NODE_TYPE_RAG_CONTEXT, {
                        "memory_id": ctx.get("id"),
                        "input_text": ctx.get("input_text", "")
                    })
                    g.add_edge(rag_id, intent_id, EDGE_TYPE_RETRIEVES_FROM)
        except Exception as exc:
            _errors.append(f"[RAG] {exc}")
            context = []
            enriched_input = input_text
            intent_id = ""
        _stage_metrics["rag"] = round((time.time() - _stage_start) * 1000, 2)

        # 2. MKC compile → MCXF dict (single source of truth)
        _stage_start = time.time()
        try:
            if d:
                d.stage_enter("mkc_classify", {"input": enriched_input, "raw": input_text})
            _ctx["enriched_input"] = enriched_input
            run_hooks("mkc_before", _ctx)
            mcxf_dict = self.mkc.compile(enriched_input, raw_input=input_text)
            mcxf = self._mcxf_dict_to_document(mcxf_dict, input_text)
            _ctx["mcxf_dict"] = mcxf_dict
            _ctx["mcxf"] = mcxf
            run_hooks("mkc_after", _ctx)
            if d:
                d.stage_exit("mkc_classify", {
                    "decisions": len(mcxf_dict.get("decisions", [])),
                    "tasks": len(mcxf_dict.get("tasks", [])),
                })
                d.wait_for_step()
            if g:
                for task in mcxf_dict.get("tasks", []):
                    step_id = g.add_node(NODE_TYPE_MKC_STEP, {
                        "predicate": task.get("predicate", ""),
                        "object": task.get("object", ""),
                    })
                    g.add_edge(intent_id, step_id, EDGE_TYPE_DERIVES_FROM)
        except Exception as exc:
            _errors.append(f"[MKC] {exc}")
            run_hooks("kernel_after", _ctx)
            run_hooks("memory_after", _ctx)
            if d:
                d.finish_execution()
            r = KernelResult(
                mcxf=None, execution=[], memory_id=None,
                feedback=FeedbackReport(summary=f"MKC compile failed: {exc}"),
                success=False, errors=_errors + [str(exc)],
                execution_plan=ExecutionPlan(intent="", steps=[]),
            )
            r.stage_metrics = _stage_metrics
            return r
        _stage_metrics["mkc"] = round((time.time() - _stage_start) * 1000, 2)

        # 3. MCXF document section node
        _stage_start = time.time()
        try:
            if d:
                d.stage_enter("mcxf_build", {"task_count": len(mcxf.tasks)})
                d.stage_exit("mcxf_build", {"task_count": len(mcxf.tasks)})
                d.wait_for_step()
            section_id = ""
            if g:
                section_id = g.add_node(NODE_TYPE_MCXF_SECTION, {
                    "section_count": len(mcxf.tasks),
                    "tasks": [f"{t.predicate} {t.object}" for t in mcxf.tasks]
                })
                g.add_edge(intent_id, section_id, EDGE_TYPE_DERIVES_FROM)
        except Exception as exc:
            _errors.append(f"[MCXF] {exc}")
            section_id = ""
        _stage_metrics["mcxf"] = round((time.time() - _stage_start) * 1000, 2)

        # 4. Bridge: MCXF → ExecutionPlan
        _stage_start = time.time()
        validation = None
        execution_plan = None
        plan_id = ""
        try:
            if d:
                d.stage_enter("bridge_exec", {"task_count": len(mcxf.tasks)})
            _ctx["mcxf"] = mcxf
            run_hooks("bridge_before", _ctx)
            execution_plan = self.bridge.map_tasks(mcxf.tasks, intent=input_text)
            validation = self.bridge.validate(execution_plan)
            _ctx["execution_plan"] = execution_plan
            _ctx["validation"] = validation
            run_hooks("bridge_after", _ctx)
            if d:
                d.stage_exit("bridge_exec", {
                    "intent": execution_plan.intent,
                    "step_count": len(execution_plan.steps),
                    "valid": validation.valid,
                })
                d.wait_for_step()
            if g:
                plan_id = g.add_node(NODE_TYPE_EXECUTION_PLAN, {
                    "intent": execution_plan.intent,
                    "step_count": len(execution_plan.steps),
                    "valid": validation.valid
                })
                g.add_edge(section_id, plan_id, EDGE_TYPE_DERIVES_FROM)
            if not validation.valid:
                mem_id = self.memory.store_snapshot(input_text, mcxf, {"error": validation.errors})
                self.memory.log({
                    "input": input_text,
                    "mcxf_dict": mcxf_dict,
                    "bridge_errors": validation.errors,
                    "memory_id": mem_id
                })
                if d:
                    d.emit_memory_write(mem_id)
                if g:
                    g.set_focus(plan_id)
                    mem_node = g.add_node(NODE_TYPE_MEMORY_ENTRY, {
                        "memory_id": mem_id,
                        "status": "error"
                    })
                    g.add_edge(plan_id, mem_node, EDGE_TYPE_DERIVES_FROM)
                    g.emit(EVENT_EXECUTION_FINISHED, {"success": False, "memory_id": mem_id})
                if d:
                    d.finish_execution()
                run_hooks("kernel_after", _ctx)
                r = KernelResult(
                    mcxf=mcxf, execution=[], memory_id=mem_id,
                    feedback=FeedbackReport(), success=False,
                    errors=_errors + list(validation.errors),
                    execution_plan=execution_plan,
                )
                r.stage_metrics = _stage_metrics
                return r
        except Exception as exc:
            _errors.append(f"[Bridge] {exc}")
            execution_plan = ExecutionPlan(intent=input_text, steps=[])
            _ctx["execution_plan"] = execution_plan
        _stage_metrics["bridge"] = round((time.time() - _stage_start) * 1000, 2)

        # 5. Optimizer: ExecutionPlan → OptimizedPlan
        _stage_start = time.time()
        try:
            if d:
                d.stage_enter("graph_optimizer", {"step_count": len(execution_plan.steps)})
            from runtime.optimizer.pipeline import OptimizerPipeline
            _optimizer = OptimizerPipeline()
            run_hooks("optimizer_before", _ctx)
            optimized_plan, opt_report = _optimizer.optimize(execution_plan)
            _ctx["optimized_plan"] = optimized_plan
            _ctx["opt_report"] = opt_report
            run_hooks("optimizer_after", _ctx)
            if d:
                d.stage_exit("graph_optimizer", {
                    "nodes_before": opt_report.node_count_before,
                    "nodes_after": opt_report.node_count_after,
                    "layers": opt_report.parallel_layers,
                    "verification": "PASS" if opt_report.verification.get("passed") else "FAIL",
                })
        except Exception as exc:
            _errors.append(f"[Optimizer] {exc}")
            optimized_plan = execution_plan
            _ctx["optimized_plan"] = optimized_plan
        _stage_metrics["optimizer"] = round((time.time() - _stage_start) * 1000, 2)

        # 6. MEL execute mit optimiertem Plan
        _stage_start = time.time()
        try:
            if d:
                d.stage_enter("mel_tool_call", {"step_count": len(optimized_plan.layers)})
            run_hooks("mel_before", _ctx)
            mel_result = self.mel.execute(optimized_plan)
            _ctx["mel_result"] = mel_result
            run_hooks("mel_after", _ctx)
            if d:
                for i, step_result in enumerate(mel_result):
                    tool_name = execution_plan.steps[i].get("tool", "unknown") if i < len(execution_plan.steps) else "unknown"
                    d.emit_tool_call(
                        tool_name,
                        execution_plan.steps[i].get("args", {}),
                        step_result,
                        duration_ms=0.0,
                    )
                d.stage_exit("mel_tool_call", {"result_count": len(mel_result)})
                d.wait_for_step()
            if g:
                for i, step_result in enumerate(mel_result):
                    tool_name = execution_plan.steps[i].get("tool", "unknown") if i < len(execution_plan.steps) else "unknown"
                    is_system = tool_name.startswith("browser.") or tool_name.startswith("desktop.")
                    ntype = NODE_TYPE_SYSTEM_ACTION if is_system else NODE_TYPE_TOOL_EXECUTION
                    exec_id = g.add_node(ntype, {
                        "tool": tool_name,
                        "result": str(step_result)
                    })
                    g.add_edge(plan_id, exec_id, EDGE_TYPE_EXECUTES if not is_system else EDGE_TYPE_CONTROLS)
        except Exception as exc:
            _errors.append(f"[MEL] {exc}")
            mel_result = []
            _ctx["mel_result"] = mel_result
        _stage_metrics["mel"] = round((time.time() - _stage_start) * 1000, 2)

        # 7. Feedback analysis
        _stage_start = time.time()
        try:
            exec_result = self._build_exec_result(mel_result)
            _ctx["exec_result"] = exec_result
            run_hooks("feedback_before", _ctx)
            feedback = self.feedback.analyze(mcxf.tasks, exec_result, execution_plan)
            self.mkc.apply_feedback(feedback)
            _ctx["feedback"] = feedback
            run_hooks("feedback_after", _ctx)
            if g and feedback.confidence_adjustments:
                for section, delta in feedback.confidence_adjustments.items():
                    conf_id = g.add_node(NODE_TYPE_CONFLICT, {
                        "section": section,
                        "delta": delta,
                        "patterns": [f.description for f in feedback.failure_patterns]
                    })
                    g.add_edge(conf_id, plan_id, EDGE_TYPE_CONFLICTS_WITH)
            if d and feedback.confidence_adjustments:
                for section, delta in feedback.confidence_adjustments.items():
                    d.emit_conflict(
                        section, delta,
                        [f.description for f in feedback.failure_patterns],
                        severity=min(1.0, abs(delta) * 2),
                    )
        except Exception as exc:
            _errors.append(f"[Feedback] {exc}")
            feedback = FeedbackReport()
            _ctx["feedback"] = feedback
        _stage_metrics["feedback"] = round((time.time() - _stage_start) * 1000, 2)

        # 8. Memory persist
        _stage_start = time.time()
        try:
            run_hooks("memory_before", _ctx)
            mem_id = self.memory.store_snapshot(input_text, mcxf, mel_result, feedback)
            self.memory.log({
                "input": input_text,
                "mcxf_dict": mcxf_dict,
                "execution_plan": execution_plan.intent,
                "result": mel_result,
                "feedback": {"summary": feedback.summary, "adjustments": feedback.confidence_adjustments},
                "memory_id": mem_id
            })
            _ctx["mem_id"] = mem_id
            if d:
                d.emit_memory_write(mem_id)
            if g:
                mem_node = g.add_node(NODE_TYPE_MEMORY_ENTRY, {
                    "memory_id": mem_id,
                    "status": "stored",
                    "success": self._is_success(mel_result)
                })
                g.add_edge(mem_node, plan_id, EDGE_TYPE_DERIVES_FROM)
                g.set_focus(mem_node)
                g.emit(EVENT_EXECUTION_FINISHED, {
                    "success": self._is_success(mel_result),
                    "memory_id": mem_id
                })
        except Exception as exc:
            _errors.append(f"[Memory] {exc}")
            mem_id = None
        _stage_metrics["memory"] = round((time.time() - _stage_start) * 1000, 2)

        if d:
            d.finish_execution()

        run_hooks("kernel_after", _ctx)
        run_hooks("memory_after", _ctx)

        r = KernelResult(
            mcxf=mcxf, execution=mel_result, memory_id=mem_id,
            feedback=feedback, success=self._is_success(mel_result),
            errors=_errors, execution_plan=execution_plan,
        )
        r.stage_metrics = _stage_metrics
        return r
