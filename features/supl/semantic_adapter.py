from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from features.supl.semantic_model import (
    SemanticApplication,
    Capability,
    ApplicationState,
    ActionInvocation,
)


@runtime_checkable
class SemanticAdapter(Protocol):
    @property
    def application_id(self) -> str: ...

    @property
    def application(self) -> SemanticApplication: ...

    def discover(self) -> SemanticApplication:
        ...

    def introspect_capability(self, capability_id: str) -> Optional[Capability]:
        ...

    def get_state(self, state_id: str) -> Optional[ApplicationState]:
        ...

    def synchronize_state(self) -> Dict[str, ApplicationState]:
        ...

    def map_action(self, action_id: str, parameters: Dict[str, Any]) -> ActionInvocation:
        ...

    def handle_event(self, event_id: str, payload: Dict[str, Any]) -> None:
        ...


class BaseSemanticAdapter(ABC):
    @property
    @abstractmethod
    def application_id(self) -> str:
        ...

    @property
    @abstractmethod
    def application(self) -> SemanticApplication:
        ...

    @abstractmethod
    def discover(self) -> SemanticApplication:
        ...

    @abstractmethod
    def introspect_capability(self, capability_id: str) -> Optional[Capability]:
        ...

    @abstractmethod
    def get_state(self, state_id: str) -> Optional[ApplicationState]:
        ...

    @abstractmethod
    def synchronize_state(self) -> Dict[str, ApplicationState]:
        ...

    @abstractmethod
    def map_action(self, action_id: str, parameters: Dict[str, Any]) -> ActionInvocation:
        ...

    def handle_event(self, event_id: str, payload: Dict[str, Any]) -> None:
        pass
