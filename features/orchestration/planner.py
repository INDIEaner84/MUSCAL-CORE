from __future__ import annotations

import uuid
from typing import Any, Optional

from .models import TaskAnalysis, AgentDefinition, SelectionResult, ExecutionPlan, PlanStep
from .policy import OrchestrationPolicy


STEP_TEMPLATES: dict[str, list[dict]] = {
    "bug_fix": [
        {"action": "analyze", "description": "Analyze bug report and reproduce issue"},
        {"action": "retrieve_knowledge", "description": "Retrieve relevant knowledge from past executions"},
        {"action": "modify", "description": "Implement bug fix"},
        {"action": "test", "description": "Run tests to verify fix"},
        {"action": "verify", "description": "Verify fix meets acceptance criteria"},
        {"action": "document", "description": "Document fix and lessons learned"},
    ],
    "feature": [
        {"action": "analyze", "description": "Analyze feature requirements"},
        {"action": "retrieve_knowledge", "description": "Retrieve relevant patterns and knowledge"},
        {"action": "modify", "description": "Implement feature"},
        {"action": "test", "description": "Write and run tests"},
        {"action": "verify", "description": "Verify feature correctness"},
        {"action": "document", "description": "Document feature and usage"},
    ],
    "refactor": [
        {"action": "analyze", "description": "Analyze code to refactor"},
        {"action": "retrieve_knowledge", "description": "Retrieve refactoring patterns"},
        {"action": "modify", "description": "Apply refactoring"},
        {"action": "test", "description": "Run tests to verify no regression"},
        {"action": "verify", "description": "Verify refactoring goals met"},
    ],
    "documentation": [
        {"action": "analyze", "description": "Analyze documentation needs"},
        {"action": "modify", "description": "Write documentation"},
        {"action": "verify", "description": "Verify documentation accuracy"},
    ],
    "testing": [
        {"action": "analyze", "description": "Analyze test coverage gaps"},
        {"action": "modify", "description": "Write tests"},
        {"action": "test", "description": "Run test suite"},
        {"action": "verify", "description": "Verify coverage targets met"},
    ],
    "deployment": [
        {"action": "analyze", "description": "Analyze deployment requirements"},
        {"action": "retrieve_knowledge", "description": "Retrieve deployment procedures"},
        {"action": "modify", "description": "Prepare deployment artifacts"},
        {"action": "test", "description": "Run pre-deployment checks"},
        {"action": "verify", "description": "Verify deployment readiness"},
    ],
    "analysis": [
        {"action": "analyze", "description": "Perform code analysis"},
        {"action": "retrieve_knowledge", "description": "Retrieve relevant context"},
        {"action": "modify", "description": "Generate analysis report"},
        {"action": "verify", "description": "Verify analysis completeness"},
    ],
    "other": [
        {"action": "analyze", "description": "Analyze task requirements"},
        {"action": "retrieve_knowledge", "description": "Retrieve relevant knowledge"},
        {"action": "modify", "description": "Execute task"},
        {"action": "test", "description": "Run tests"},
        {"action": "verify", "description": "Verify results"},
    ],
}


class ExecutionPlanner:

    def __init__(self, policy: Optional[OrchestrationPolicy] = None):
        self._policy = policy or OrchestrationPolicy()

    def plan(self, task_analysis: TaskAnalysis, selection: SelectionResult) -> ExecutionPlan:
        category = task_analysis.category
        template = STEP_TEMPLATES.get(category, STEP_TEMPLATES["other"])

        steps: list[PlanStep] = []
        selected_id = selection.selected_agent.agent_id if selection.selected_agent else "default"

        for i, step_def in enumerate(template):
            controls = self._risk_controls_for_action(step_def["action"], task_analysis)
            steps.append(PlanStep(
                step_id=f"{task_analysis.task_id}-step-{i + 1}",
                action=step_def["action"],
                description=step_def["description"],
                agent=selected_id if step_def["action"] in ("modify", "test") else None,
                risk_controls=controls,
            ))

        agent_ids = [a.agent_id for a in [selection.selected_agent] + selection.alternatives if a]
        risk_controls = self._global_risk_controls(task_analysis)

        return ExecutionPlan(
            task_id=task_analysis.task_id,
            steps=steps,
            required_agents=list(set(agent_ids)),
            risk_controls=risk_controls,
            autonomy_level=task_analysis.recommended_autonomy,
            estimated_effort=task_analysis.estimated_effort,
        )

    def _risk_controls_for_action(self, action: str, analysis: TaskAnalysis) -> list[str]:
        controls: list[str] = []
        if action == "modify" and analysis.risk_level in ("MEDIUM", "HIGH"):
            controls.append("Create checkpoint before modification")
            controls.append("Rollback available on failure")
        if action == "test":
            controls.append("Run full test suite")
        if action == "deploy" or action == "push":
            controls.append("Requires human approval")
        return controls

    def _global_risk_controls(self, analysis: TaskAnalysis) -> list[str]:
        controls: list[str] = []
        if analysis.verification_required:
            controls.append("Verification required after execution")
        if analysis.risk_level == "HIGH":
            controls.append("Human approval required")
            controls.append("Sandboxed execution recommended")
        if analysis.risk_level == "MEDIUM":
            controls.append("Review required after execution")
        return controls
