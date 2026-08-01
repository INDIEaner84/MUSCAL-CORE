import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ──────────────────────────────────────────────
# TEST SUITE: E3.1-P5 Specialized CognitiveUnits
# ──────────────────────────────────────────────

# ── SCU-01: ValidationCU validates correctly ──

def test_validation_cu_valid():
    from features.cognitive_unit.specialized import ValidationCU
    cu = ValidationCU(unit_id="val-1", agent_type="validator")
    result = cu.execute({
        "task_type": "validation",
        "schema": {
            "name": {"required": True, "type": "str"},
            "age": {"required": True, "type": "int", "min": 0, "max": 150},
            "email": {"required": False, "type": "str", "pattern": r".+@.+"},
        },
        "data": {"name": "Alice", "age": 30, "email": "alice@test.com"},
    })
    assert result["status"] == "valid"
    assert result["valid"] is True
    assert len(result["errors"]) == 0

def test_validation_cu_invalid():
    from features.cognitive_unit.specialized import ValidationCU
    cu = ValidationCU(unit_id="val-1", agent_type="validator")
    result = cu.execute({
        "task_type": "validation",
        "schema": {
            "name": {"required": True, "type": "str"},
            "age": {"required": True, "type": "int", "min": 0},
        },
        "data": {"name": "Bob", "age": -5},
    })
    assert result["status"] == "invalid"
    assert result["valid"] is False
    assert len(result["errors"]) > 0

def test_validation_cu_missing_required():
    from features.cognitive_unit.specialized import ValidationCU
    cu = ValidationCU(unit_id="val-1", agent_type="validator")
    result = cu.execute({
        "task_type": "validation",
        "schema": {
            "name": {"required": True, "type": "str"},
        },
        "data": {},
    })
    assert result["status"] == "invalid"
    assert "Missing required" in result["errors"][0]


# ── SCU-02: AnalysisCU ──

def test_analysis_cu_stats():
    from features.cognitive_unit.specialized import AnalysisCU
    cu = AnalysisCU(unit_id="ana-1", agent_type="analyst")
    result = cu.execute({
        "task_type": "analysis",
        "mode": "stats",
        "data": {"a": 10, "b": 20, "c": 30, "d": "hello"},
    })
    assert result["status"] == "success"
    assert result["numeric_count"] == 3
    assert result["string_count"] == 1
    assert result["numeric_sum"] == 60
    assert result["numeric_avg"] == 20

def test_analysis_cu_classification():
    from features.cognitive_unit.specialized import AnalysisCU
    cu = AnalysisCU(unit_id="ana-1", agent_type="analyst")
    result = cu.execute({
        "task_type": "analysis",
        "mode": "classification",
        "data": {"a": 1, "b": "x", "c": 2.0, "d": True, "e": [1]},
    })
    assert result["status"] == "success"
    assert "int" in result["classification"]
    assert "str" in result["classification"]

def test_analysis_cu_unknown_mode():
    from features.cognitive_unit.specialized import AnalysisCU
    cu = AnalysisCU(unit_id="ana-1", agent_type="analyst")
    result = cu.execute({
        "task_type": "analysis",
        "mode": "unknown_mode",
        "data": {},
    })
    assert result["status"] == "error"


# ── SCU-03: TransformationCU ──

def test_transformation_cu_to_string():
    from features.cognitive_unit.specialized import TransformationCU
    cu = TransformationCU(unit_id="tr-1", agent_type="transformer")
    result = cu.execute({
        "task_type": "transformation",
        "format": "string",
        "data": {"name": "Alice", "age": 30},
    })
    assert result["status"] == "success"
    assert "name=Alice" in result["result"]
    assert "age=30" in result["result"]

def test_transformation_cu_columns():
    from features.cognitive_unit.specialized import TransformationCU
    cu = TransformationCU(unit_id="tr-1", agent_type="transformer")
    result = cu.execute({
        "task_type": "transformation",
        "format": "columns",
        "data": {"x": 10, "y": 20},
    })
    assert result["status"] == "success"
    assert result["result"]["keys"] == ["x", "y"]

def test_transformation_cu_filtered():
    from features.cognitive_unit.specialized import TransformationCU
    cu = TransformationCU(unit_id="tr-1", agent_type="transformer")
    result = cu.execute({
        "task_type": "transformation",
        "format": "filtered",
        "data": {"a": 1, "b": 2, "c": 3},
        "include_keys": ["a", "c"],
    })
    assert result["status"] == "success"
    assert result["result"] == {"a": 1, "c": 3}


# ── SCU-04: VerificationCU ──

def test_verification_cu_no_runtime():
    from features.cognitive_unit.specialized import VerificationCU
    cu = VerificationCU(unit_id="ver-1", agent_type="verifier")
    result = cu.execute({"task_type": "verification"})
    assert result["status"] == "error"
    assert "No tool runtime" in result["error"]

def test_verification_cu_with_runtime():
    from features.cognitive_unit.specialized import VerificationCU
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    utr.execute("math.add", {"a": 1, "b": 2})
    cu = VerificationCU(unit_id="ver-1", agent_type="verifier", tool_runtime=utr)
    result = cu.execute({"task_type": "verification"})
    assert result["status"] == "success"
    assert result["total_receipts"] == 1

def test_verification_cu_single_receipt():
    from features.cognitive_unit.specialized import VerificationCU
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    r = utr.execute("math.add", {"a": 3, "b": 4})
    rid = r.receipt.receipt_id
    cu = VerificationCU(unit_id="ver-1", agent_type="verifier", tool_runtime=utr)
    result = cu.execute({"task_type": "verification", "receipt_id": rid})
    assert result["status"] == "verified"

def test_verification_cu_tool_name():
    from features.cognitive_unit.specialized import VerificationCU
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    utr.execute("math.add", {"a": 1, "b": 1})
    utr.execute("math.add", {"a": 2, "b": 2})
    cu = VerificationCU(unit_id="ver-1", agent_type="verifier", tool_runtime=utr)
    result = cu.execute({"task_type": "verification", "tool": "math.add"})
    assert result["status"] == "success"
    assert result["total_receipts"] == 2


# ── SCU-05: PolicyCU ──

def test_policy_cu_check():
    from features.cognitive_unit.specialized import PolicyCU
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    cu = PolicyCU(unit_id="pol-1", agent_type="policy", safety_gate=sg)
    result = cu.execute({
        "task_type": "policy",
        "action": "check",
        "tool": "opencode.run",
        "args": {"command": "ls"},
    })
    assert result["status"] == "denied"

def test_policy_cu_permit():
    from features.cognitive_unit.specialized import PolicyCU
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    cu = PolicyCU(unit_id="pol-1", agent_type="policy", safety_gate=sg)
    result = cu.execute({
        "task_type": "policy",
        "action": "permit",
        "tool": "opencode.run",
    })
    assert result["status"] == "success"
    assert sg.is_allowed("opencode.run")

def test_policy_cu_risk_of():
    from features.cognitive_unit.specialized import PolicyCU
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    cu = PolicyCU(unit_id="pol-1", agent_type="policy", safety_gate=sg)
    result = cu.execute({
        "task_type": "policy",
        "action": "risk_of",
        "tool": "browser.open",
    })
    assert result["status"] == "success"
    assert result["risk"] == "high"


# ── SCU-06: All Specialized CUs register in CognitiveUnitRegistry ──

def test_specialized_cus_in_registry():
    from features.cognitive_unit import registry as cu_registry
    from features.cognitive_unit.specialized import (
        ValidationCU, AnalysisCU, TransformationCU,
        VerificationCU, PolicyCU,
    )
    cu_registry.clear()
    units = [ValidationCU, AnalysisCU, TransformationCU, VerificationCU, PolicyCU]
    for cls in units:
        agent_type = cls.__name__.replace("CU", "").lower()
        inst = cls(unit_id=f"{agent_type}-1", agent_type=agent_type)
        cu_registry.register(inst)
    all_units = cu_registry.all_units()
    assert len(all_units) == 5
    types = {u.agent_type for u in all_units.values()}
    assert "validation" in types
    assert "analysis" in types
    assert "transformation" in types
    assert "verification" in types
    assert "policy" in types
    cu_registry.clear()


# ── helpers ──

def _make_sg_permit_all():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    for name in [
        "console.print", "math.add", "filesystem.write", "file.write",
        "opencode.run", "browser.open", "browser.click", "browser.type",
        "browser.extract_text", "browser.screenshot", "browser.scroll",
        "desktop.screenshot", "desktop.type", "desktop.click",
        "desktop.open_app", "desktop.move", "desktop.keypress",
    ]:
        sg.permit(name)
    return sg
