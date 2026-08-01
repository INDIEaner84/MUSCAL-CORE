class AgentDetectionResult:
    __slots__ = ("agent_type", "confidence", "reason", "task_type", "detector_version")

    def __init__(self, agent_type="general", confidence=0.5, reason="fallback",
                 task_type="general", detector_version="1.0"):
        self.agent_type = agent_type
        self.confidence = confidence
        self.reason = reason
        self.task_type = task_type
        self.detector_version = detector_version

    def to_dict(self):
        return {
            "agent_type": self.agent_type,
            "confidence": self.confidence,
            "reason": self.reason,
            "task_type": self.task_type,
            "detector_version": self.detector_version,
        }

    @staticmethod
    def from_dict(d):
        return AgentDetectionResult(
            agent_type=d.get("agent_type", "general"),
            confidence=d.get("confidence", 0.5),
            reason=d.get("reason", "fallback"),
            task_type=d.get("task_type", "general"),
            detector_version=d.get("detector_version", "1.0"),
        )
