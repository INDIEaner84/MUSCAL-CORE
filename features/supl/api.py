from __future__ import annotations
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from features.supl.semantic_model import (
    ActionInvocation, InteractionSource, InteractionStatus,
)
from features.supl.adapter_registry import AdapterRegistry
from features.supl.projection_engine import (
    ProjectionEngine, ProjectionContext, UIMode, UIProjection,
)
from features.supl.provenance import UIInteraction
from features.supl.event_integration import EventBusBridge
from features.supl.provenance_linker import ProvenanceLinker


_INVALID_MODE_MSG = "mode must be one of: native, overlay, graph_native"
_MISSING_ACTION_MSG = "action_id and parameters are required"


def _safe_execution_id(val: Any) -> str:
    return str(val) if val is not None else ""


def _validate_mode(mode: str) -> UIMode:
    try:
        return UIMode(mode)
    except ValueError:
        raise ValueError(_INVALID_MODE_MSG)


class SUPLAPI:
    def __init__(
        self,
        registry: AdapterRegistry,
        engine: ProjectionEngine,
        event_bridge: Optional[EventBusBridge] = None,
        linker: Optional[ProvenanceLinker] = None,
        utr: Any = None,
    ):
        self._registry = registry
        self._engine = engine
        self._bridge = event_bridge
        self._linker = linker
        self._utr = utr

    def register_routes(self, app: FastAPI) -> None:
        @app.get("/api/supl/apps")
        async def list_apps():
            apps = self._registry.list()
            return apps

        @app.get("/api/supl/apps/{app_id}")
        async def get_app(app_id: str):
            adapter = self._registry.get(app_id)
            if adapter is None:
                return JSONResponse({"error": f"application not found: {app_id}"}, status_code=404)
            app_model = adapter.discover()
            return app_model.to_dict()

        @app.post("/api/supl/apps/{app_id}/action")
        async def execute_action(app_id: str, request: Request):
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "invalid JSON body"}, status_code=400)

            action_id = body.get("action_id", "")
            parameters = body.get("parameters", {})
            if not action_id or not isinstance(action_id, str):
                return JSONResponse({"error": _MISSING_ACTION_MSG}, status_code=400)

            adapter = self._registry.get(app_id)
            if adapter is None:
                return JSONResponse({"error": f"application not found: {app_id}"}, status_code=404)

            ui_session_id = body.get("ui_session_id", "")
            projection_id = body.get("projection_id", "")
            source_mode_str = body.get("source_mode", "overlay")
            try:
                source_mode = InteractionSource(source_mode_str)
            except ValueError:
                source_mode = InteractionSource.OVERLAY

            interaction = UIInteraction.create(
                application_id=app_id,
                action_id=action_id,
                source_mode=source_mode,
                ui_session_id=ui_session_id,
                projection_id=projection_id,
            )

            if self._bridge:
                self._bridge.publish_action_requested(interaction)

            try:
                inv: ActionInvocation = adapter.map_action(action_id, parameters)
            except ValueError as e:
                interaction.mark_failed()
                if self._bridge:
                    self._bridge.publish_action_rejected(interaction, str(e))
                return JSONResponse({"error": str(e), "status": "REJECTED", "interaction_id": interaction.interaction_id}, status_code=400)
            except Exception as e:
                interaction.mark_failed()
                return JSONResponse({"error": f"action mapping failed: {e}", "status": "FAILED", "interaction_id": interaction.interaction_id}, status_code=500)

            interaction.mark_authorized()
            if self._bridge:
                self._bridge.publish_action_authorized(interaction)

            if self._utr is None:
                interaction.mark_failed()
                return JSONResponse({"error": "runtime not available", "status": "FAILED", "interaction_id": interaction.interaction_id}, status_code=503)

            interaction.mark_executing()
            if self._bridge:
                self._bridge.publish_interaction_updated(interaction)

            try:
                result = self._utr.execute(
                    inv.tool_name,
                    inv.args,
                    correlation_id=interaction.interaction_id,
                )
            except Exception as e:
                interaction.mark_failed()
                if self._bridge:
                    self._bridge.publish_execution_failed(interaction, str(e))
                return JSONResponse({"error": str(e), "status": "FAILED", "interaction_id": interaction.interaction_id}, status_code=500)

            if result.success:
                receipt = result.receipt
                if receipt is not None:
                    interaction.link_execution(receipt.execution_id)
                    interaction.link_receipt(receipt.receipt_id)
                    if self._linker:
                        self._linker.link(interaction, receipt)
                    if self._bridge:
                        self._bridge.publish_execution_completed(interaction, receipt)
                else:
                    if self._bridge:
                        self._bridge.publish_execution_completed(interaction, None)
                return {
                    "status": "EXECUTED",
                    "interaction_id": interaction.interaction_id,
                    "execution_id": _safe_execution_id(interaction.execution_id),
                    "receipt_id": _safe_execution_id(interaction.receipt_id),
                    "result": result.output if isinstance(result.output, dict) else {"output": str(result.output)},
                }
            else:
                interaction.mark_failed()
                if self._bridge:
                    self._bridge.publish_execution_failed(interaction, result.error or "unknown error")
                return JSONResponse({
                    "status": "FAILED",
                    "interaction_id": interaction.interaction_id,
                    "error": result.error or "execution failed",
                }, status_code=500)

        @app.get("/api/supl/projection/{app_id}")
        async def get_projection(app_id: str, mode: str = "overlay", user: str = "", role: str = "", task: str = ""):
            try:
                ui_mode = _validate_mode(mode)
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)

            ctx = ProjectionContext(user=user, role=role, task=task)
            projection = self._engine.project(app_id, ctx, ui_mode)
            if projection.projection_state.value == "error":
                return JSONResponse({"error": projection.filter_reason}, status_code=404)
            return projection.to_dict()


def create_supl_api(
    registry: AdapterRegistry,
    engine: Optional[ProjectionEngine] = None,
    event_bridge: Optional[EventBusBridge] = None,
    linker: Optional[ProvenanceLinker] = None,
    utr: Any = None,
) -> SUPLAPI:
    if engine is None:
        engine = ProjectionEngine(registry)
    return SUPLAPI(
        registry=registry,
        engine=engine,
        event_bridge=event_bridge,
        linker=linker,
        utr=utr,
    )
