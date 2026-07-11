from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class GraphMemoryProvider(Protocol):
    def add_node(self, node_id: str, content: Any) -> None: ...
    def add_edge(self, from_id: str, to_id: str, relation: str) -> None: ...
    def get_node(self, node_id: str) -> Optional[Any]: ...
    def get_related(self, node_id: str) -> List[Dict[str, str]]: ...
    def query(self, keyword: str) -> Dict[str, Any]: ...
    def query_related(self, node_id: str) -> List[Dict[str, str]]: ...
    def ingest(self, text: str) -> None: ...


class MemoryStoreProvider(Protocol):
    """Protocol for persistent key-value storage providers.

    Default implementation: SQLiteMemoryAdapter (features/memory/sqlite_adapter.py)
    wraps memory.py module-level functions into this interface.
    """
    def save(self, key: str, value: Any) -> None: ...
    def retrieve(self, key: str) -> Optional[Any]: ...
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]: ...


class MemoryProvider(Protocol):
    """Unified memory protocol combining graph + persistent store.

    The active implementation concatenates GraphMemory (graph_memory.py)
    with SQLiteMemoryAdapter (features/memory/sqlite_adapter.py).
    """
    graph: GraphMemoryProvider
    store: MemoryStoreProvider
    def store_snapshot(self, input_text: str, mcxf: Any, result: Any, feedback: Any = None) -> int: ...
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]: ...


class KernelProvider(Protocol):
    def run(self, input_text: str, **kwargs: Any) -> Any: ...


class EventBusProvider(Protocol):
    def publish(self, topic: str, payload: Optional[Dict[str, Any]] = None, source: str = "", priority: Any = None) -> Any: ...
    def subscribe(self, topic: str, callback: Any) -> None: ...
    def unsubscribe(self, topic: str, callback: Any) -> None: ...
    def get_history(self, topic: Optional[str] = None, limit: int = 10) -> List[Any]: ...
    def get_stats(self) -> Dict[str, Any]: ...


def get_memory_backend():
    """Lazily import and return the core memory module.

    This factory function bridges the immutability boundary:
    features/ -> interfaces.py (not immutable) -> memory (core).
    """
    import importlib
    return importlib.import_module("memory")


class PipelineStage(Protocol):
    """A composable pipeline stage for the MUSCAL execution pipeline.

    Each stage wraps a core module (MKC, Bridge, MEL, etc.) as a typed,
    ordered, composable unit. Plugins can insert new stages between
    existing ones using plugin_registry.register_stage().

    See ADR-007 for the full migration plan.
    """
    name: str
    order: int
    def process(self, context: dict) -> dict: ...
