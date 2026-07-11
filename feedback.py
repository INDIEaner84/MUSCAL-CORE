from mkc_rules import SIGNAL_RULES
from schema import FailurePattern, FeedbackReport, KnowledgeTriple, SemanticGap


def analyze_feedback(tasks, execution_result, execution_plan):
    report = FeedbackReport()
    errors = execution_result.get("errors", [])
    outputs = execution_result.get("tool_outputs", [])
    success = execution_result.get("success", False)

    unmapped_count = 0
    wrong_type_count = 0
    partial_count = 0

    for i, step in enumerate(execution_plan.steps):
        tool = step.get("tool", "")
        task_text = step.get("original_task", "")

        if tool == "UNMAPPED":
            unmapped_count += 1
            report.failure_patterns.append(FailurePattern(
                pattern_type="UNMAPPED_TOOL",
                tool=tool,
                task_text=task_text,
                count=1,
                description=f"Bridge could not map task: '{task_text}'"
            ))
            if i < len(tasks):
                triple = tasks[i]
                triple_text = f"{triple.predicate} {triple.object}"
                report.semantic_gaps.append(SemanticGap(
                    gap_type="AMBIGUOUS_TASK",
                    section="06_TASKS",
                    content=triple_text,
                    suggestion="Task text does not match any tool extraction pattern. Consider adding a new pattern or keyword."
                ))

        if tool != "UNMAPPED" and i < len(outputs):
            out = outputs[i]
            if isinstance(out, dict) and out.get("tool") == "UNMAPPED":
                wrong_type_count += 1
                report.failure_patterns.append(FailurePattern(
                    pattern_type="WRONG_ARG_TYPE",
                    tool=tool,
                    task_text=task_text,
                    count=1,
                    description=f"MEL rejected args for '{tool}'"
                ))

    if 0 < unmapped_count < len(execution_plan.steps):
        partial_count = unmapped_count
        report.failure_patterns.append(FailurePattern(
            pattern_type="PARTIAL_EXECUTION",
            tool="MULTIPLE",
            task_text="",
            count=partial_count,
            description=f"{partial_count}/{len(execution_plan.steps)} steps were UNMAPPED"
        ))

    if unmapped_count > 0:
        report.confidence_adjustments["TASKS"] = -0.05

    if wrong_type_count > 0:
        report.confidence_adjustments["TASKS"] = \
            report.confidence_adjustments.get("TASKS", 0) - 0.03

    if not success and unmapped_count == len(execution_plan.steps):
        for section in SIGNAL_RULES:
            report.confidence_adjustments[section] = \
                report.confidence_adjustments.get(section, 0) - 0.02

    updates = []
    if unmapped_count > 0:
        updates.append("Review TASK extraction patterns in bridge.py matchers")
    if wrong_type_count > 0:
        updates.append("Tighten arg type validation for failing tool")
    if partial_count > 0:
        updates.append("Consider splitting complex tasks into simpler steps")

    report.recommended_mkc_updates = updates

    parts = []
    if unmapped_count:
        parts.append(f"{unmapped_count} unmapped tool(s)")
    if wrong_type_count:
        parts.append(f"{wrong_type_count} arg type error(s)")
    if partial_count:
        parts.append(f"partial execution ({partial_count} skipped)")
    if not parts:
        parts.append("no issues detected")

    report.summary = "; ".join(parts)

    return report
