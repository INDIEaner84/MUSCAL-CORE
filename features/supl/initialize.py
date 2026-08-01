from __future__ import annotations
import logging
from typing import Any, Dict, Optional, Set

from fastapi import FastAPI

from event_bus import EventBus
from runtime.event_store import EventStore

from features.supl.adapter_registry import AdapterRegistry
from features.supl.event_integration import EventBusBridge
from features.supl.graph_projection import GraphProjectionEngine
from features.supl.graph_projection_events import create_graph_projection_event_bridge
from features.supl.projection_engine import ProjectionEngine
from features.supl.provenance_linker import ProvenanceLinker
from features.supl.api import create_supl_api, SUPLAPI
from features.supl.ws_stream import register_supl_ws, SUPLWebSocketManager

logger = logging.getLogger(__name__)


class SuplGraphStore:
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: list = []


class SuplRuntime:
    def __init__(
        self,
        registry: AdapterRegistry,
        bus_bridge: EventBusBridge,
        projection_engine: ProjectionEngine,
        graph_projection_engine: GraphProjectionEngine,
        graph_projection_bridge: Optional[Any],
        linker: ProvenanceLinker,
        supl_api: SUPLAPI,
        ws_manager: Optional[SUPLWebSocketManager],
        graph_store: SuplGraphStore,
    ):
        self.registry = registry
        self.bus_bridge = bus_bridge
        self.projection_engine = projection_engine
        self.graph_projection_engine = graph_projection_engine
        self.graph_projection_bridge = graph_projection_bridge
        self.linker = linker
        self.supl_api = supl_api
        self.ws_manager = ws_manager
        self.graph_store = graph_store

    def shutdown(self) -> None:
        logger.info("Shutting down SUPL runtime")
        if self.graph_projection_bridge is not None:
            try:
                self.graph_projection_bridge.stop()
            except Exception:
                pass
        if self.bus_bridge is not None:
            try:
                self.bus_bridge.unsubscribe_all()
            except Exception:
                pass


def initialize_supl_runtime(
    event_bus: EventBus,
    event_store: Optional[EventStore] = None,
    fastapi_app: Optional[FastAPI] = None,
    utr: Any = None,
) -> SuplRuntime:
    bus_bridge = EventBusBridge(event_bus)

    registry = AdapterRegistry(event_bridge=bus_bridge)

    graph_store = SuplGraphStore()
    projection_engine = ProjectionEngine(registry)

    graph_projection_engine = GraphProjectionEngine(registry, graph_store)

    graph_projection_bridge = create_graph_projection_event_bridge(
        event_bus=event_bus,
        projection_engine=graph_projection_engine,
    )

    linker = ProvenanceLinker(bus_bridge)

    supl_api = create_supl_api(
        registry=registry,
        engine=projection_engine,
        event_bridge=bus_bridge,
        linker=linker,
        utr=utr,
    )

    ws_manager: Optional[SUPLWebSocketManager] = None
    if fastapi_app is not None:
        supl_api.register_routes(fastapi_app)

        ws_manager = register_supl_ws(
            app=fastapi_app,
            event_bus=event_bus,
            event_store=event_store,
        )

    logger.info(
        "SUPL runtime initialized: registry=%s graph_projection=%s api=%s ws=%s",
        bool(registry),
        bool(graph_projection_engine),
        bool(supl_api),
        bool(ws_manager),
    )

    return SuplRuntime(
        registry=registry,
        bus_bridge=bus_bridge,
        projection_engine=projection_engine,
        graph_projection_engine=graph_projection_engine,
        graph_projection_bridge=graph_projection_bridge,
        linker=linker,
        supl_api=supl_api,
        ws_manager=ws_manager,
        graph_store=graph_store,
    )
