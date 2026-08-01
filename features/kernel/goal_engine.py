from __future__ import annotations

import uuid
from typing import Any, Optional

from .models import Intent, Goal, GoalSet, GoalPriority


class GoalEngine:

    def create(self, intent: Intent) -> GoalSet:
        goals: list[Goal] = []

        goals.append(Goal(
            id=str(uuid.uuid4()),
            description=f"Complete {intent.type} task: {intent.goal[:80]}",
            priority=GoalPriority.PRIMARY,
        ))

        if intent.risk in ("high", "critical"):
            goals.append(Goal(
                id=str(uuid.uuid4()),
                description="Ensure no breaking changes or regressions",
                priority=GoalPriority.SAFETY,
                dependencies=[goals[0].id],
            ))

        goals.append(Goal(
            id=str(uuid.uuid4()),
            description="Verify results meet acceptance criteria",
            priority=GoalPriority.VERIFICATION,
            dependencies=[goals[0].id],
        ))

        goals.append(Goal(
            id=str(uuid.uuid4()),
            description="Extract knowledge from execution for future reuse",
            priority=GoalPriority.KNOWLEDGE,
            dependencies=[goals[0].id],
        ))

        if intent.priority in ("high", "critical"):
            goals.append(Goal(
                id=str(uuid.uuid4()),
                description="Optimize execution for efficiency",
                priority=GoalPriority.OPTIMIZATION,
                dependencies=[goals[0].id],
            ))

        if intent.constraints:
            for i, c in enumerate(intent.constraints):
                goals.append(Goal(
                    id=str(uuid.uuid4()),
                    description=f"Respect constraint: {c}",
                    priority=GoalPriority.SECONDARY,
                    dependencies=[goals[0].id],
                ))

        return GoalSet(goals=goals)
