import re as _re

AGENT_TYPE_KEYWORDS = {
    "analytical": [
        r"\banaly\b", r"\bcompare\b", r"\bdifference\b", r"\bsimilar\b",
        r"\bevaluate\b", r"\bassess\b", r"\bmeasure\b", r"\bquantify\b",
        r"\bstatistics?\b", r"\bcorrelation\b", r"\btrend\b",
    ],
    "research": [
        r"\bresearch\b", r"\binvestigate\b", r"\bstudy\b", r"\bfind\b",
        r"\bsearch\b", r"\blookup\b", r"\bwhat is\b", r"\bwho is\b",
        r"\bexplain\b", r"\bdefinition\b",
    ],
    "creative": [
        r"\bwrite\b", r"\bcompose\b", r"\bcreate\b", r"\bdraft\b",
        r"\bgenerate\b", r"\bdesign\b", r"\bimagine\b", r"\bstory\b",
        r"\bpoem\b", r"\bcreative\b",
    ],
    "operational": [
        r"\bdeploy\b", r"\bmonitor\b", r"\bcheck\b", r"\brun\b",
        r"\bexecute\b", r"\bstart\b", r"\bstop\b", r"\brestart\b",
        r"\bschedule\b", r"\boperational\b",
    ],
    "coding": [
        r"\bcode\b", r"\bprogram\b", r"\bfunction\b", r"\bclass\b",
        r"\bimplement\b", r"\brefactor\b", r"\bfix\b", r"\bbug\b",
        r"\bdebug\b", r"\btest\b", r"\bcompile\b", r"\bscript\b",
        r"\bpython\b", r"\bjavascript\b",
    ],
}

DETECTOR_VERSION = "1.0"

_AGENT_TYPE_ORDER = [
    "analytical", "research", "creative", "operational", "coding",
]


def _count_matches(text, patterns):
    count = 0
    for pat in patterns:
        if _re.search(pat, text, _re.IGNORECASE):
            count += 1
    return count


class DeterministicAgentDetector:
    def __init__(self):
        self.version = DETECTOR_VERSION

    def detect(self, task_type="", mcxf_dict=None, routing_metadata=None):
        mcxf_dict = mcxf_dict or {}
        routing_metadata = routing_metadata or {}

        tasks_text = ""
        for task in mcxf_dict.get("tasks", []):
            if isinstance(task, dict):
                parts = [
                    str(task.get("tool", "")),
                    str(task.get("predicate", "")),
                    str(task.get("object", "")),
                    str(task.get("args", {})),
                ]
                tasks_text += " ".join(parts) + " "
            else:
                tasks_text += str(task) + " "

        combined = f"{task_type} {tasks_text} {str(routing_metadata)}".lower()

        if not combined.strip():
            return self._result("general", 0.5, "no input data", task_type)

        scores = {}
        for agent_type, patterns in AGENT_TYPE_KEYWORDS.items():
            matches = _count_matches(combined, patterns)
            if matches > 0:
                scores[agent_type] = matches

        if not scores:
            return self._result("general", 0.5, "no keyword matches", task_type)

        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]
        total = sum(scores.values())
        confidence = min(0.5 + (best_score / total) * 0.5, 0.99)

        return self._result(best_agent, confidence,
                            f"matched {best_score} keyword(s) for '{best_agent}'",
                            task_type)

    def _result(self, agent_type, confidence, reason, task_type):
        from features.cognitive_unit.contracts import AgentDetectionResult
        return AgentDetectionResult(
            agent_type=agent_type,
            confidence=confidence,
            reason=reason,
            task_type=task_type,
            detector_version=self.version,
        )


DEFAULT_DETECTOR = DeterministicAgentDetector()
