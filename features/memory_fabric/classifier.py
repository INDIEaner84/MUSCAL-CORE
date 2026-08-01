from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .models import MemoryType, MemoryEntry


class MemoryClassifier:

    def classify(self, source: str, content: dict, *,
                 memory_type_hint: Optional[str] = None) -> list[MemoryEntry]:
        candidates: list[MemoryEntry] = []
        now = datetime.now(timezone.utc).isoformat()

        if memory_type_hint:
            mt = getattr(MemoryType, memory_type_hint.upper(), None)
            if mt:
                candidates.append(MemoryEntry(
                    id=str(uuid.uuid4()),
                    memory_type=mt,
                    content=content,
                    source=source,
                    timestamp=now,
                ))
                return candidates

        text = self._flatten(content)

        if self._is_execution(text):
            candidates.append(self._make_entry(source, content, MemoryType.EPISODIC, now))
            if self._has_procedural_aspects(text):
                candidates.append(self._make_entry(source, content, MemoryType.PROCEDURAL, now))

        if self._is_decision(text):
            candidates.append(self._make_entry(source, content, MemoryType.DECISION, now))

        if self._is_semantic(text):
            candidates.append(self._make_entry(source, content, MemoryType.SEMANTIC, now))

        if self._is_experience(text):
            candidates.append(self._make_entry(source, content, MemoryType.EXPERIENCE, now))

        if self._is_context(text):
            candidates.append(self._make_entry(source, content, MemoryType.CONTEXT, now))

        if not candidates:
            candidates.append(self._make_entry(source, content, MemoryType.EPISODIC, now))

        return candidates

    def classify_event(self, event: dict) -> list[MemoryEntry]:
        topic = event.get("topic", "")
        payload = event.get("payload", {})
        source = f"event:{topic}"

        if "optimization" in topic:
            return self.classify(source, payload, memory_type_hint="EXPERIENCE")
        if "knowledge" in topic:
            return self.classify(source, payload, memory_type_hint="SEMANTIC")
        if "tool" in topic:
            return self.classify(source, payload, memory_type_hint="PROCEDURAL")
        if "kernel" in topic:
            return self.classify(source, payload, memory_type_hint="DECISION")
        if "execution" in topic or "runtime" in topic:
            return self.classify(source, payload, memory_type_hint="EPISODIC")

        return self.classify(source, payload)

    def classify_knowledge_candidate(self, candidate: dict) -> list[MemoryEntry]:
        source = f"knowledge:candidate:{candidate.get('knowledge_candidate', {}).get('id', 'unknown')}"
        return self.classify(source, candidate, memory_type_hint="SEMANTIC")

    def explain_classification(self, source: str, content: dict) -> list[dict]:
        text = self._flatten(content)
        reasons = []
        if self._is_execution(text):
            reasons.append({"type": "EPISODIC", "rule": "content contains execution keywords"})
            if self._has_procedural_aspects(text):
                reasons.append({"type": "PROCEDURAL", "rule": "content contains step/plan/action keywords"})
        if self._is_decision(text):
            reasons.append({"type": "DECISION", "rule": "content contains decision/strategy/keywords"})
        if self._is_semantic(text):
            reasons.append({"type": "SEMANTIC", "rule": "content contains knowledge/fact/pattern keywords"})
        if self._is_experience(text):
            reasons.append({"type": "EXPERIENCE", "rule": "content contains experience/feedback/evaluation keywords"})
        if self._is_context(text):
            reasons.append({"type": "CONTEXT", "rule": "content contains context/session/environment keywords"})
        if not reasons:
            reasons.append({"type": "EPISODIC", "rule": "no matching keywords — default classification"})
        return reasons

    def _make_entry(self, source: str, content: dict,
                    memory_type: MemoryType, timestamp: str) -> MemoryEntry:
        return MemoryEntry(
            id=str(uuid.uuid4()),
            memory_type=memory_type,
            content=content,
            source=source,
            timestamp=timestamp,
        )

    def _flatten(self, content: dict) -> str:
        parts = []
        for k, v in content.items():
            if isinstance(v, (str, int, float)):
                parts.append(str(v))
            if isinstance(k, str):
                parts.append(k)
        return " ".join(parts)

    def _is_execution(self, text: str) -> bool:
        keywords = ("execution", "completed", "started", "failed", "result", "output")
        return any(k in text.lower() for k in keywords)

    def _has_procedural_aspects(self, text: str) -> bool:
        keywords = ("step", "plan", "action", "tool", "command", "procedure", "method")
        return any(k in text.lower() for k in keywords)

    def _is_decision(self, text: str) -> bool:
        keywords = ("decision", "selected", "chose", "recommended", "strategy",
                     "intent", "goal", "priority")
        return any(k in text.lower() for k in keywords)

    def _is_semantic(self, text: str) -> bool:
        keywords = ("knowledge", "learned", "fact", "pattern", "rule",
                     "principle", "concept", "definition")
        return any(k in text.lower() for k in keywords)

    def _is_experience(self, text: str) -> bool:
        keywords = ("experience", "feedback", "evaluation", "outcome",
                     "confidence", "score", "optimization")
        return any(k in text.lower() for k in keywords)

    def _is_context(self, text: str) -> bool:
        keywords = ("context", "session", "state", "environment", "profile",
                     "configuration", "setting")
        return any(k in text.lower() for k in keywords)
