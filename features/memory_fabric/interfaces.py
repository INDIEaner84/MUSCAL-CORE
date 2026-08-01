from __future__ import annotations

from typing import Any, Optional, Protocol


class MemoryStoreProvider(Protocol):
    def list_entries(self) -> list[Any]: ...
    def search(self, query: str, limit: int = 10) -> list[Any]: ...
    def save_entry(self, entry: Any) -> None: ...


class KnowledgeProvider(Protocol):
    def retrieve_relevant(self, context: str, top_k: int = 3) -> list[Any]: ...


class EventEmitter(Protocol):
    def emit(self, topic: str, payload: dict, **kwargs: Any) -> Optional[int]: ...


class RuntimeStateProvider(Protocol):
    def get_state(self) -> dict: ...
    def compute(self) -> dict: ...


class SessionProvider(Protocol):
    def get_session(self, execution_id: str) -> Optional[Any]: ...


class ProfileProvider(Protocol):
    def get_all_profiles(self) -> list[Any]: ...
