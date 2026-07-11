"""
Pipeline Builder — composable pipeline stages (ADR-007).

Provides PipelineStage registration and pipeline composition outside
the immutable plugin_registry. Stages wrap core modules as typed,
ordered, composable units. Plugins register stages here instead of
modifying kernel.py.

Usage:
    from features.runtime.pipeline_builder import PipelineBuilder

    builder = PipelineBuilder()
    builder.register(MKCStage(), after="rag")
    builder.register(CustomStage(), before="mel")
    pipeline = builder.build()

    context = {"input_text": "hello"}
    for stage in pipeline:
        context = stage.process(context)
"""

from typing import List, Optional, Protocol


class PipelineStage(Protocol):
    name: str
    order: int
    def process(self, context: dict) -> dict: ...


class PipelineBuilder:
    """Registry + composer for PipelineStage instances.

    Stages are ordered by their `order` field. Plugins can insert
    new stages relative to existing ones via `before`/`after`.
    """

    def __init__(self):
        self._stages: dict[str, PipelineStage] = {}

    def register(self, stage: PipelineStage, before: Optional[str] = None, after: Optional[str] = None) -> None:
        if before and after:
            raise ValueError("Use either 'before' or 'after', not both")
        if before and before in self._stages:
            existing = self._stages[before]
            stage.order = existing.order - 1
        elif after and after in self._stages:
            existing = self._stages[after]
            stage.order = existing.order + 1
        self._stages[stage.name] = stage

    def build(self) -> List[PipelineStage]:
        return sorted(self._stages.values(), key=lambda s: s.order)

    def get(self, name: str) -> Optional[PipelineStage]:
        return self._stages.get(name)
