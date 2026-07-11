from dataclasses import dataclass, field
from typing import Any, Dict, List

from schema import MCXF_REQUIRED_KEYS, validate_mcxf


@dataclass
class CognitiveDiffEntry:
    diff_type: str
    section: str
    field: str
    old_value: object
    new_value: object
    impact: str
    description: str


@dataclass
class RiskEntry:
    risk_type: str
    severity: str
    signal: str
    mitigation: str


@dataclass
class PerformanceDelta:
    accuracy: str
    stability: str
    conflict_rate: str
    confidence: str


@dataclass
class CognitiveDiffReport:
    mcxf_a_version: str = ""
    mcxf_b_version: str = ""
    logical_diff: List[CognitiveDiffEntry] = field(default_factory=list)
    behavioral_diff: List[CognitiveDiffEntry] = field(default_factory=list)
    architectural_diff: List[CognitiveDiffEntry] = field(default_factory=list)
    risk_analysis: List[RiskEntry] = field(default_factory=list)
    performance_delta: PerformanceDelta = field(default_factory=lambda: PerformanceDelta("UNKNOWN", "UNKNOWN", "UNKNOWN", "LOW"))
    recommendation: str = "REVIEW"


class CognitiveDiffEngine:

    def diff(self, a: Dict[str, Any], b: Dict[str, Any]) -> CognitiveDiffReport:
        for name, d in [("A", a), ("B", b)]:
            ok, errs = validate_mcxf(d)
            if not ok:
                raise ValueError(f"MCXF {name} is invalid: {errs}")

        diff = CognitiveDiffReport(
            mcxf_a_version=a.get("_version", "unknown"),
            mcxf_b_version=b.get("_version", "unknown"),
        )
        diff.logical_diff = self._logical_diff(a, b)
        diff.behavioral_diff = self._behavioral_diff(a, b)
        diff.architectural_diff = self._architectural_diff(a, b)
        diff.risk_analysis = self._risk_analysis(diff.logical_diff, diff.behavioral_diff)
        diff.performance_delta = self._performance_delta(diff)
        diff.recommendation = self._recommend(diff)
        return diff

    def _triple_key(self, t: dict) -> str:
        return f"{t.get('predicate','')}|{t.get('object','')}"

    def _triple_text(self, t: dict) -> str:
        return f"{t.get('predicate','')} {t.get('object','')}"

    def _logical_diff(self, a, b):
        entries = []
        a_dec = {self._triple_key(t): t for t in a.get("decisions", [])}
        b_dec = {self._triple_key(t): t for t in b.get("decisions", [])}

        for key in sorted(set(b_dec) - set(a_dec)):
            t = b_dec[key]
            entries.append(CognitiveDiffEntry(
                "DECISION_ADDED", "decisions", key,
                None, self._triple_text(t), "MEDIUM",
                f"New decision: {self._triple_text(t)}"
            ))
        for key in sorted(set(a_dec) - set(b_dec)):
            t = a_dec[key]
            entries.append(CognitiveDiffEntry(
                "DECISION_REMOVED", "decisions", key,
                self._triple_text(t), None, "HIGH",
                f"Decision removed: {self._triple_text(t)}"
            ))
        for key in sorted(set(a_dec) & set(b_dec)):
            ta, tb = a_dec[key], b_dec[key]
            if ta.get("confidence") != tb.get("confidence"):
                entries.append(CognitiveDiffEntry(
                    "DECISION_CONFIDENCE_CHANGED", "decisions", key,
                    ta.get("confidence"), tb.get("confidence"), "LOW",
                    f"Decision '{key}' confidence: {ta.get('confidence')} → {tb.get('confidence')}"
                ))

        a_oq = set(a.get("open_questions", []))
        b_oq = set(b.get("open_questions", []))
        for q in sorted(b_oq - a_oq):
            entries.append(CognitiveDiffEntry(
                "OPEN_QUESTION_ADDED", "open_questions", q,
                None, q, "LOW", f"New open question: '{q}'"
            ))
        for q in sorted(a_oq - b_oq):
            entries.append(CognitiveDiffEntry(
                "OPEN_QUESTION_RESOLVED", "open_questions", q,
                q, None, "MEDIUM", f"Open question resolved: '{q}'"
            ))

        return entries

    def _behavioral_diff(self, a, b):
        entries = []
        a_tasks = {self._triple_key(t): t for t in a.get("tasks", [])}
        b_tasks = {self._triple_key(t): t for t in b.get("tasks", [])}

        for key in sorted(set(b_tasks) - set(a_tasks)):
            t = b_tasks[key]
            entries.append(CognitiveDiffEntry(
                "TASK_ADDED", "tasks", key,
                None, self._triple_text(t), "HIGH",
                f"New task: {self._triple_text(t)}"
            ))
        for key in sorted(set(a_tasks) - set(b_tasks)):
            t = a_tasks[key]
            entries.append(CognitiveDiffEntry(
                "TASK_REMOVED", "tasks", key,
                self._triple_text(t), None, "CRITICAL",
                f"Task removed: {self._triple_text(t)}"
            ))
        for key in sorted(set(a_tasks) & set(b_tasks)):
            ta, tb = a_tasks[key], b_tasks[key]
            if ta.get("confidence") != tb.get("confidence"):
                entries.append(CognitiveDiffEntry(
                    "TASK_CONFIDENCE_CHANGED", "tasks", key,
                    ta.get("confidence"), tb.get("confidence"), "LOW",
                    f"Task '{key}' confidence: {ta.get('confidence')} → {tb.get('confidence')}"
                ))

        a_predicates = {t.get("predicate") for t in a.get("tasks", [])}
        b_predicates = {t.get("predicate") for t in b.get("tasks", [])}
        for p in sorted(b_predicates - a_predicates):
            entries.append(CognitiveDiffEntry(
                "TOOL_ADDED", "tasks", p,
                None, p, "HIGH",
                f"New tool '{p}' appears in tasks"
            ))
        for p in sorted(a_predicates - b_predicates):
            entries.append(CognitiveDiffEntry(
                "TOOL_REMOVED", "tasks", p,
                p, None, "HIGH",
                f"Tool '{p}' no longer appears in tasks"
            ))

        return entries

    def _architectural_diff(self, a, b):
        entries = []
        a_arch = {self._triple_key(t): t for t in a.get("architecture", [])}
        b_arch = {self._triple_key(t): t for t in b.get("architecture", [])}

        for key in sorted(set(b_arch) - set(a_arch)):
            t = b_arch[key]
            entries.append(CognitiveDiffEntry(
                "ARCH_ADDED", "architecture", key,
                None, self._triple_text(t), "HIGH",
                f"New architecture rule: {self._triple_text(t)}"
            ))
        for key in sorted(set(a_arch) - set(b_arch)):
            t = a_arch[key]
            entries.append(CognitiveDiffEntry(
                "ARCH_REMOVED", "architecture", key,
                self._triple_text(t), None, "CRITICAL",
                f"Architecture rule removed: {self._triple_text(t)}"
            ))

        a_cons = {self._triple_key(t): t for t in a.get("constraints", [])}
        b_cons = {self._triple_key(t): t for t in b.get("constraints", [])}
        for key in sorted(set(b_cons) - set(a_cons)):
            t = b_cons[key]
            entries.append(CognitiveDiffEntry(
                "CONSTRAINT_ADDED", "constraints", key,
                None, self._triple_text(t), "HIGH",
                f"New constraint: {self._triple_text(t)}"
            ))
        for key in sorted(set(a_cons) - set(b_cons)):
            t = a_cons[key]
            entries.append(CognitiveDiffEntry(
                "CONSTRAINT_REMOVED", "constraints", key,
                self._triple_text(t), None, "MEDIUM",
                f"Constraint removed: {self._triple_text(t)}"
            ))

        return entries

    def _risk_analysis(self, logical, behavioral):
        risks = []

        for entry in behavioral:
            if entry.diff_type == "TOOL_ADDED":
                tool = entry.field
                if "browser" in tool or "desktop" in tool:
                    risks.append(RiskEntry(
                        "DETERMINISM", "HIGH",
                        f"New external tool '{tool}' in tasks — "
                        "system behavior may vary based on external state.",
                        "Ensure tool is sandboxed. Pin library versions."
                    ))
                else:
                    risks.append(RiskEntry(
                        "AMBIGUITY", "MEDIUM",
                        f"New tool '{tool}' added to task set — "
                        "execution surface expands.",
                        "Verify tool is properly registered and tested."
                    ))

        task_additions = sum(1 for e in behavioral if e.diff_type == "TASK_ADDED")
        if task_additions > 3:
            risks.append(RiskEntry(
                "INSTABILITY", "MEDIUM",
                f"{task_additions} new tasks added — execution plan is expanding.",
                "Review task necessity and consolidation."
            ))

        task_removals = sum(1 for e in behavioral if e.diff_type == "TASK_REMOVED")
        if task_removals > 0:
            risks.append(RiskEntry(
                "OVERSIGHT", "LOW",
                f"{task_removals} task(s) removed — verify no required work was lost.",
                "Confirm removals are intentional and no dependencies break."
            ))

        arch_removals = sum(1 for e in logical + behavioral
                            if e.diff_type in ("DECISION_REMOVED", "ARCH_REMOVED"))
        if arch_removals > 2:
            risks.append(RiskEntry(
                "HALLUCINATION", "CRITICAL",
                f"{arch_removals} decision(s)/architecture rule(s) removed — "
                "system may be losing core knowledge.",
                "Investigate each removal. Consider reverting if critical."
            ))

        if not risks:
            risks.append(RiskEntry(
                "NONE_DETECTED", "LOW",
                "No risks identified from the diff.",
                "Continue monitoring."
            ))

        return risks

    def _performance_delta(self, diff):
        logical = diff.logical_diff
        behavioral = diff.behavioral_diff

        accuracy = "UNKNOWN"
        conf_changes = []
        for e in logical:
            if "CONFIDENCE" in e.diff_type:
                ov = e.old_value if isinstance(e.old_value, (int, float)) else 0
                nv = e.new_value if isinstance(e.new_value, (int, float)) else 0
                conf_changes.append(nv - ov)
        if conf_changes:
            avg = sum(conf_changes) / len(conf_changes)
            if avg > 0.05:
                accuracy = "+5%"
            elif avg > 0.01:
                accuracy = "+2%"
            elif avg < -0.05:
                accuracy = "-5%"
            elif avg < -0.01:
                accuracy = "-2%"
            else:
                accuracy = "~0%"

        stability = "UNKNOWN"
        task_delta = 0
        for e in behavioral:
            if e.diff_type == "TASK_ADDED":
                task_delta += 1
            elif e.diff_type == "TASK_REMOVED":
                task_delta -= 1
        if task_delta > 2:
            stability = "-5%"
        elif task_delta > 0:
            stability = "-2%"
        elif task_delta == 0:
            stability = "~0%"
        elif task_delta < -2:
            stability = "+5%"
        else:
            stability = "+2%"

        conflict_rate = "UNKNOWN"
        total_added = sum(1 for e in logical + behavioral
                          if "ADDED" in e.diff_type)
        if total_added > 5:
            conflict_rate = "+3%"
        elif total_added > 2:
            conflict_rate = "+1%"
        else:
            conflict_rate = "~0%"

        total_changes = len(logical) + len(behavioral)
        if total_changes == 0:
            confidence = "HIGH"
        elif total_changes < 5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return PerformanceDelta(accuracy, stability, conflict_rate, confidence)

    def _recommend(self, diff):
        risks = diff.risk_analysis
        perf = diff.performance_delta

        critical_risks = [r for r in risks if r.severity == "CRITICAL"]
        high_risks = [r for r in risks if r.severity == "HIGH"]

        if critical_risks:
            return "REJECT"

        if high_risks:
            return "REVIEW"

        if perf.accuracy and "-" in perf.accuracy and "+" not in perf.accuracy:
            if perf.stability and "-" in perf.stability:
                return "ROLLBACK"

        if perf.confidence == "HIGH":
            return "MERGE"

        return "REVIEW"
