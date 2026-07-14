"""Pipeline stage wrappers — delegate to kernel.stage_* methods.

Each stage wraps a kernel stage method as a PipelineStage-compatible object,
allowing plugins to insert custom stages between core stages via
plugin_registry.register_stage() / build_pipeline().

Usage (in kernel._register_pipeline_stages):
    register_stage(RAGStage(self))
    register_stage(MKCStage(self))
    ...
    pipeline = build_pipeline()
    for stage in pipeline:
        ctx = stage.process(ctx)
"""


class RAGStage:
    name = "rag"
    order = 10

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["context"], ctx["enriched_input"], ctx["intent_id"] = self.k.stage_rag(ctx["input_text"], ctx)
        return ctx


class MKCStage:
    name = "mkc"
    order = 20

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["mcxf_dict"], ctx["mcxf"] = self.k.stage_mkc(ctx["input_text"], ctx["enriched_input"], ctx["intent_id"], ctx)
        return ctx


class MCXFStage:
    name = "mcxf"
    order = 30

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["section_id"] = self.k.stage_mcxf_section(ctx["mcxf"], ctx["intent_id"], ctx)
        return ctx


class BridgeStage:
    name = "bridge"
    order = 40

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        execution_plan, plan_id, bridge_mem, bridge_errs = self.k.stage_bridge(
            ctx["mcxf"], ctx["input_text"], ctx["section_id"], ctx.get("mcxf_dict", {}), ctx)
        ctx["execution_plan"] = execution_plan
        ctx["plan_id"] = plan_id
        if bridge_mem is not None:
            ctx["_bridge_mem"] = bridge_mem
            ctx["_bridge_errs"] = bridge_errs
            ctx["_early_exit"] = True
        return ctx


class OptimizerStage:
    name = "optimizer"
    order = 50

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["optimized_plan"] = self.k.stage_optimizer(ctx["execution_plan"], ctx)
        return ctx


class MELStage:
    name = "mel"
    order = 60

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["mel_result"] = self.k.stage_mel(ctx.get("optimized_plan", ctx["execution_plan"]), ctx["execution_plan"], ctx.get("plan_id", ""), ctx)
        return ctx


class FeedbackStage:
    name = "feedback"
    order = 70

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["feedback"] = self.k.stage_feedback(ctx["mcxf"], ctx.get("mel_result", []), ctx["execution_plan"], ctx.get("plan_id", ""), ctx)
        return ctx


class MemoryStage:
    name = "memory"
    order = 80

    def __init__(self, kernel):
        self.k = kernel

    def process(self, ctx):
        ctx["mem_id"] = self.k.stage_memory(ctx["input_text"], ctx["mcxf"], ctx.get("mcxf_dict", {}), ctx.get("mel_result", []), ctx.get("feedback"), ctx["execution_plan"], ctx.get("plan_id", ""), ctx)
        return ctx
