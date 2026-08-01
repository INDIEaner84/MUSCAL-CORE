import time
import re

from .cognitive_unit import CognitiveUnit


class ValidationCU(CognitiveUnit):
    def execute(self, context):
        if not context:
            context = {}
        task_type = context.get("task_type", "validation")
        schema = context.get("schema", {})
        data = context.get("data", {})

        if self.governance is not None:
            gov_result = self.governance.check(context)
            if not getattr(gov_result, "allowed", True):
                return {"status": "blocked_by_governance", "unit_id": self.id, "task_type": task_type}

        errors = []
        for field, constraints in schema.items():
            value = data.get(field)
            if constraints.get("required", False) and value is None:
                errors.append(f"Missing required field: {field}")
                continue
            if value is not None:
                vtype = constraints.get("type")
                if vtype == "int" and not isinstance(value, int):
                    errors.append(f"Field '{field}' should be int, got {type(value).__name__}")
                elif vtype == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be numeric, got {type(value).__name__}")
                elif vtype == "str" and not isinstance(value, str):
                    errors.append(f"Field '{field}' should be str, got {type(value).__name__}")
                if "min" in constraints and isinstance(value, (int, float)) and value < constraints["min"]:
                    errors.append(f"Field '{field}' below minimum {constraints['min']}")
                if "max" in constraints and isinstance(value, (int, float)) and value > constraints["max"]:
                    errors.append(f"Field '{field}' above maximum {constraints['max']}")
                if "pattern" in constraints and isinstance(value, str):
                    if not re.match(constraints["pattern"], value):
                        errors.append(f"Field '{field}' does not match pattern")

        return {
            "status": "valid" if not errors else "invalid",
            "unit_id": self.id,
            "agent_type": self.agent_type,
            "task_type": task_type,
            "valid": len(errors) == 0,
            "errors": errors,
            "field_count": len(data),
        }


class AnalysisCU(CognitiveUnit):
    def execute(self, context):
        if not context:
            context = {}
        task_type = context.get("task_type", "analysis")
        data = context.get("data", {})
        mode = context.get("mode", "stats")

        if self.governance is not None:
            gov_result = self.governance.check(context)
            if not getattr(gov_result, "allowed", True):
                return {"status": "blocked_by_governance", "unit_id": self.id, "task_type": task_type}

        if mode == "stats":
            numeric_values = [v for v in data.values() if isinstance(v, (int, float))]
            string_values = [v for v in data.values() if isinstance(v, str)]
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "mode": mode,
                "total_fields": len(data),
                "numeric_count": len(numeric_values),
                "string_count": len(string_values),
                "numeric_sum": sum(numeric_values) if numeric_values else 0,
                "numeric_avg": sum(numeric_values) / len(numeric_values) if numeric_values else 0,
            }

        if mode == "classification":
            types = {}
            for k, v in data.items():
                tname = type(v).__name__
                types[tname] = types.get(tname, 0) + 1
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "mode": mode,
                "classification": types,
            }

        return {
            "status": "error",
            "unit_id": self.id,
            "agent_type": self.agent_type,
            "task_type": task_type,
            "error": f"Unknown mode: {mode}",
        }


class TransformationCU(CognitiveUnit):
    def execute(self, context):
        if not context:
            context = {}
        task_type = context.get("task_type", "transformation")
        data = context.get("data", {})
        target_format = context.get("format", "string")

        if self.governance is not None:
            gov_result = self.governance.check(context)
            if not getattr(gov_result, "allowed", True):
                return {"status": "blocked_by_governance", "unit_id": self.id, "task_type": task_type}

        if target_format == "string":
            parts = [f"{k}={v}" for k, v in sorted(data.items())]
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "format": target_format,
                "result": ", ".join(parts),
                "length": len(", ".join(parts)),
            }

        if target_format == "columns":
            keys = sorted(data.keys())
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "format": target_format,
                "result": {"keys": keys, "values": [data[k] for k in keys]},
                "length": len(keys),
            }

        if target_format == "filtered":
            include_keys = context.get("include_keys", [])
            filtered = {k: v for k, v in data.items() if k in include_keys}
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "format": target_format,
                "result": filtered,
                "length": len(filtered),
            }

        return {
            "status": "error",
            "unit_id": self.id,
            "agent_type": self.agent_type,
            "task_type": task_type,
            "error": f"Unknown format: {target_format}",
        }


class VerificationCU(CognitiveUnit):
    def execute(self, context):
        if not context:
            context = {}
        task_type = context.get("task_type", "verification")
        receipt_id = context.get("receipt_id", "")
        tool_name = context.get("tool", "")

        if self.governance is not None:
            gov_result = self.governance.check(context)
            if not getattr(gov_result, "allowed", True):
                return {"status": "blocked_by_governance", "unit_id": self.id, "task_type": task_type}

        if self.tool_runtime is None:
            return {
                "status": "error",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "error": "No tool runtime available for verification",
            }

        if receipt_id:
            result = self.tool_runtime.verify(receipt_id=receipt_id)
            if result is None:
                return {
                    "status": "not_found",
                    "unit_id": self.id,
                    "task_type": task_type,
                    "error": f"Receipt not found: {receipt_id}",
                }
            return {
                "status": "verified" if result.status == "verified" else result.status,
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "receipt_id": receipt_id,
                "verification": result.status,
                "detail": result.status,
            }

        if tool_name:
            results = self.tool_runtime.verify(name=tool_name)
            verified = sum(1 for r in results if r.status == "verified")
            failed = sum(1 for r in results if r.status == "failed")
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "tool": tool_name,
                "total_receipts": len(results),
                "verified": verified,
                "failed": failed,
            }

        all_results = self.tool_runtime.verify()
        verified = sum(1 for r in all_results.values() if r.status == "verified")
        failed = sum(1 for r in all_results.values() if r.status == "failed")
        not_supported = sum(1 for r in all_results.values() if r.status == "not_supported")
        inconclusive = sum(1 for r in all_results.values() if r.status == "inconclusive")

        return {
            "status": "success",
            "unit_id": self.id,
            "agent_type": self.agent_type,
            "task_type": task_type,
            "total_receipts": len(all_results),
            "verified": verified,
            "failed": failed,
            "not_supported": not_supported,
            "inconclusive": inconclusive,
        }


class PolicyCU(CognitiveUnit):
    def execute(self, context):
        if not context:
            context = {}
        task_type = context.get("task_type", "policy")
        action = context.get("action", "check")
        tool_name = context.get("tool", "")
        args = context.get("args", {})

        if self.governance is not None:
            gov_result = self.governance.check(context)
            if not getattr(gov_result, "allowed", True):
                return {"status": "blocked_by_governance", "unit_id": self.id, "task_type": task_type}

        if action == "check" and self.safety_gate is not None:
            sresult = self.safety_gate.check(tool_name, args)
            return {
                "status": "allowed" if sresult.allowed else "denied",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "action": action,
                "tool": tool_name,
                "allowed": sresult.allowed,
                "reason": sresult.reason,
                "risk": sresult.risk,
            }

        if action == "permit":
            if self.safety_gate is not None:
                self.safety_gate.permit(tool_name)
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "action": action,
                "tool": tool_name,
            }

        if action == "risk_of" and self.safety_gate is not None:
            risk = self.safety_gate.risk_of(tool_name)
            return {
                "status": "success",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "task_type": task_type,
                "action": action,
                "tool": tool_name,
                "risk": risk,
            }

        return {
            "status": "noop",
            "unit_id": self.id,
            "task_type": task_type,
            "error": f"Unknown action or no safety gate: {action}",
        }
