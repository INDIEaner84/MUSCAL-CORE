from features.cognitive_unit.registry import resolve, register, default as default_cu
from features.cognitive_unit.cognitive_unit import CognitiveUnit


class CognitiveUnitStage:
    name = "cognitive_unit"
    order = 27

    def __init__(self, kernel):
        self.k = kernel
        self._initialized = False

    def _ensure_registry(self):
        if self._initialized:
            return
        from features.safety.safety_gate import SafetyGate
        from features.tool_runtime.tool_runtime import create_default_utr
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        general_cu = CognitiveUnit(
            unit_id="cu_general",
            agent_type="general",
            tool_runtime=utr,
            safety_gate=sg,
        )
        register(general_cu)
        for agent_type in ("analytical", "research", "creative", "operational", "coding"):
            cu = CognitiveUnit(
                unit_id=f"cu_{agent_type}",
                agent_type=agent_type,
                tool_runtime=utr,
                safety_gate=sg,
            )
            register(cu)
        self._initialized = True

    def process(self, ctx):
        self._ensure_registry()
        agent_type = ctx.get("agent_type", "general")
        task_type = ctx.get("routing_task_type", "general")
        cu = resolve(agent_type)
        ctx["cognitive_unit"] = cu
        ctx["cognitive_unit_id"] = cu.id
        ctx["agent_type"] = cu.agent_type
        return ctx
