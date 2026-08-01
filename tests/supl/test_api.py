from __future__ import annotations
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from features.supl.semantic_model import ActionInvocation


def _make_test_client(api):
    app = FastAPI()
    api.register_routes(app)
    return TestClient(app)


class TestSUPLAPIRoutes:
    def test_list_apps(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/apps")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        app_ids = [a.get("application_id", a.get("id", "")) for a in data]
        assert "test_calc" in app_ids
        assert "failing_app" in app_ids

    def test_get_app_success(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/apps/test_calc")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("id") == "test_calc" or data.get("application_id") == "test_calc"

    def test_get_app_not_found(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/apps/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json().get("error", "")

    def test_execute_action_success(self, registry, projection_engine, utr, bridge, linker):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine, utr=utr, event_bridge=bridge, linker=linker)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/test_calc/action",
            json={"action_id": "add", "parameters": {"a": 3, "b": 4}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "EXECUTED"
        assert data["interaction_id"] is not None
        result = data.get("result", {})
        assert result.get("result") == 7 or result.get("output") == "7" or 7 in str(result)

    def test_execute_action_missing_action_id(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/test_calc/action",
            json={"parameters": {"a": 1}},
        )
        assert resp.status_code == 400
        assert "action_id" in resp.json().get("error", "").lower() or "required" in resp.json().get("error", "")

    def test_execute_action_app_not_found(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/nonexistent/action",
            json={"action_id": "add", "parameters": {"a": 1, "b": 2}},
        )
        assert resp.status_code == 404

    def test_execute_action_fails_mapping(self, registry, projection_engine, utr):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine, utr=utr)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/failing_app/action",
            json={"action_id": "crash", "parameters": {}},
        )
        assert resp.status_code == 400 or resp.status_code == 500
        data = resp.json()
        assert "REJECTED" in data.get("status", "") or "FAILED" in data.get("status", "")

    def test_execute_action_no_utr(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine, utr=None)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/test_calc/action",
            json={"action_id": "add", "parameters": {"a": 1, "b": 2}},
        )
        assert resp.status_code == 503

    def test_get_projection_default_mode(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/projection/test_calc")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert data.get("projection_state") in ("fresh", "synced")

    def test_get_projection_native_mode(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/projection/test_calc?mode=native")
        assert resp.status_code == 200
        assert resp.json()["mode"] == "native"

    def test_get_projection_invalid_mode(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/projection/test_calc?mode=invalid")
        assert resp.status_code == 400
        assert "mode" in resp.json().get("error", "").lower()

    def test_get_projection_not_found(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.get("/api/supl/projection/nonexistent")
        assert resp.status_code == 404

    def test_create_supl_api_helper(self, registry, projection_engine):
        from features.supl.api import create_supl_api
        api = create_supl_api(registry=registry, engine=projection_engine)
        assert isinstance(api, object)

    def test_execute_action_invalid_json(self, registry, projection_engine):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/test_calc/action",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400


class TestSUPLAPIProvenance:
    def test_action_produces_full_provenance(self, registry, projection_engine, utr, bridge, linker):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine, utr=utr, event_bridge=bridge, linker=linker)
        client = _make_test_client(api)
        resp = client.post(
            "/api/supl/apps/test_calc/action",
            json={"action_id": "add", "parameters": {"a": 3, "b": 4}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["interaction_id"] is not None
        assert data["execution_id"] is not None and data["execution_id"] != ""
        assert data["receipt_id"] is not None and data["receipt_id"] != ""

    def test_multiple_actions_unique_ids(self, registry, projection_engine, utr):
        from features.supl.api import SUPLAPI
        api = SUPLAPI(registry=registry, engine=projection_engine, utr=utr)
        client = _make_test_client(api)
        ids = []
        for _ in range(3):
            resp = client.post(
                "/api/supl/apps/test_calc/action",
                json={"action_id": "add", "parameters": {"a": 1, "b": 2}},
            )
            assert resp.status_code == 200
            ids.append(resp.json().get("interaction_id"))
        assert len(set(ids)) == 3


class TestProvenanceLinker:
    def test_link_and_get_chain(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        mock_receipt = MagicMock()
        mock_receipt.receipt_id = "receipt-1"
        mock_receipt.execution_id = "exec-1"
        linker.link(interaction, mock_receipt)
        chain = linker.get_chain(interaction.interaction_id)
        assert chain is not None
        assert chain["execution_id"] == "exec-1"
        assert chain["receipt_id"] == "receipt-1"

    def test_link_without_objects(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        linker.link(interaction)
        chain = linker.get_chain(interaction.interaction_id)
        assert chain is not None

    def test_link_with_verification(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        mock_v = MagicMock()
        mock_v.verification_id = "verif-1"
        linker.link(interaction, verification=mock_v)
        chain = linker.get_chain(interaction.interaction_id)
        assert chain["verification_id"] == "verif-1"

    def test_validate_consistency_ok(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        mock_r = MagicMock()
        mock_r.receipt_id = "r1"
        mock_r.execution_id = "e1"
        linker.link(interaction, mock_r)
        assert linker.validate_consistency(interaction.interaction_id, "e1", "r1") is True

    def test_validate_consistency_fail(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        mock_r = MagicMock()
        mock_r.receipt_id = "r1"
        mock_r.execution_id = "e1"
        linker.link(interaction, mock_r)
        assert linker.validate_consistency(interaction.interaction_id, "wrong", "r1") is False

    def test_get_chain_missing(self, linker):
        assert linker.get_chain("no-such-interaction") is None


class TestEventBusBridge:
    def test_bridge_events_flow_through_bus(self, bridge, event_bus):
        received = []
        event_bus.subscribe("supl.application.registered", lambda m: received.append(m))
        bridge.publish_application_registered("test1", "Test One", "1.0")
        assert len(received) == 1
        assert received[0].payload["application_id"] == "test1"

    def test_bridge_interaction_updated(self, bridge, event_bus):
        from features.supl.provenance import UIInteraction
        received = []
        event_bus.subscribe("supl.interaction.updated", lambda m: received.append(m))
        interaction = UIInteraction.create(application_id="a", action_id="b")
        interaction.mark_authorized()
        interaction.mark_executing()
        bridge.publish_interaction_updated(interaction)
        assert len(received) == 1
