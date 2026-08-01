from __future__ import annotations

from typing import Any, Optional

from .models import MemoryEntry
from .classifier import MemoryClassifier
from .consolidator import MemoryConsolidator


class EventListener:

    def __init__(self, fabric: Any,
                 classifier: Optional[MemoryClassifier] = None,
                 consolidator: Optional[MemoryConsolidator] = None):
        self._fabric = fabric
        self._classifier = classifier or MemoryClassifier()
        self._consolidator = consolidator or MemoryConsolidator()

    LISTEN_TOPICS = frozenset({
        "runtime.execution.completed",
        "runtime.execution.failed",
        "knowledge.candidate.created",
        "knowledge.candidate.validated",
        "kernel.intent.created",
        "kernel.strategy.selected",
    })

    def process_event(self, event: dict) -> list[MemoryEntry]:
        topic = event.get("topic", "")
        if topic not in self.LISTEN_TOPICS:
            return []

        payload = event.get("payload", {})
        source = f"event:{topic}"

        entries = self._fabric.classify(source, payload)

        stored = []
        for entry in entries:
            transitioned, _ = entry.transition_lifecycle("CLASSIFIED")
            consolidated = self._fabric.consolidate(entry.source, entry.content)
            stored.extend(consolidated)

        return stored

    def process_event_batch(self, events: list[dict]) -> list[MemoryEntry]:
        all_stored = []
        for event in events:
            stored = self.process_event(event)
            all_stored.extend(stored)
        return all_stored
