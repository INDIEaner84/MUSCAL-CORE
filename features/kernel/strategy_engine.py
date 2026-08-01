from __future__ import annotations

from typing import Any, Optional

from .models import Intent, GoalSet, UnifiedContext, Strategy, StrategyType


STRATEGY_MAP: dict[str, tuple[StrategyType, str]] = {
    "architecture": (StrategyType.ARCHITECTURE,
                     "Design or modify system architecture"),
    "implementation": (StrategyType.IMPLEMENTATION,
                       "Implement new features or code changes"),
    "investigation": (StrategyType.INVESTIGATION,
                      "Investigate, analyze, or audit code"),
    "repair": (StrategyType.REPAIR,
               "Fix bugs, errors, or crashes"),
    "validation": (StrategyType.VALIDATION,
                   "Test, verify, or validate code"),
    "documentation": (StrategyType.DOCUMENTATION,
                      "Write or update documentation"),
}


class StrategyEngine:

    def select(self, intent: Intent, goals: GoalSet,
               context: Optional[UnifiedContext] = None) -> Strategy:
        stype, desc = STRATEGY_MAP.get(intent.type,
                                        (StrategyType.IMPLEMENTATION, "General implementation"))

        reasoning_parts = [
            f"Intent type '{intent.type}' maps to {stype.value} strategy",
            f"Priority: {intent.priority}, Risk: {intent.risk}",
        ]

        if intent.risk in ("high", "critical"):
            stype = StrategyType.INVESTIGATION
            reasoning_parts.append("Risk override: switching to investigation strategy")
            desc = "High-risk task requires thorough investigation before action"
        elif intent.type == "repair" and intent.risk == "low":
            reasoning_parts.append("Low-risk repair — direct fix strategy")

        if context and context.knowledge:
            reasoning_parts.append(f"Context includes {len(context.knowledge)} knowledge entries")

        return Strategy(
            type=stype,
            description=desc,
            reasoning="; ".join(reasoning_parts),
            recommended_autonomy="A2" if intent.risk in ("high", "critical") else "A3",
        )
