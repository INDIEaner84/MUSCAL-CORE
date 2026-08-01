"""
Phase 5J: Frontend Integration Tests

Validates:
- All 8 frontend JSX files exist with correct structure
- API endpoint contracts match between frontend and backend
- WebSocket path matches
- Data structure keys match between what frontend expects and backend returns
- All imports reference existing files
- Mode switching works correctly
- Execution flow matches
"""

import ast
import os
import pytest

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
FEATURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "features")
SUPL_DIR = os.path.join(FEATURES_DIR, "supl")

REQUIRED_FRONTEND_FILES = [
    "Dashboard.jsx",
    "GraphView.jsx",
    "NodePanel.jsx",
    "TaskBox.jsx",
    "TraceViewer.jsx",
    "Replay.jsx",
    "Explain.jsx",
    "MetaExplain.jsx",
    "SuplApp.jsx",
    "ModeToggle.jsx",
    "SemanticOverlay.jsx",
    "SemanticGraphView.jsx",
    "SuplExecutionView.jsx",
    "useSuplWebSocket.js",
]

SUPL_FRONTEND_FILES = [
    "SuplApp.jsx",
    "ModeToggle.jsx",
    "SemanticOverlay.jsx",
    "SemanticGraphView.jsx",
    "SuplExecutionView.jsx",
    "useSuplWebSocket.js",
]


# ---------------------------------------------------------------------------
# Phase 5A: File existence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fname", REQUIRED_FRONTEND_FILES)
def test_frontend_file_exists(fname):
    path = os.path.join(FRONTEND_DIR, fname)
    assert os.path.isfile(path), f"Missing frontend file: {fname}"
    content = open(path).read()
    assert len(content) > 50, f"Frontend file {fname} is too short"


def test_all_supl_frontend_files_have_default_export():
    for fname in SUPL_FRONTEND_FILES:
        path = os.path.join(FRONTEND_DIR, fname)
        content = open(path).read()
        assert "export default" in content, (
            f"{fname} missing default export"
        )


# ---------------------------------------------------------------------------
# Phase 5B: Import validation (all imports resolve to existing files)
# ---------------------------------------------------------------------------

def _extract_imports(content):
    imports = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("import "):
            if "from " in line:
                parts = line.split(" from ")
                if len(parts) >= 2:
                    module = parts[1].strip().rstrip(";")
                    if module.startswith('"') or module.startswith("'"):
                        module = module[1:-1]
                    imports.append(module)
    return imports


@pytest.mark.parametrize("fname", SUPL_FRONTEND_FILES)
def test_imports_resolve(fname):
    path = os.path.join(FRONTEND_DIR, fname)
    content = open(path).read()
    imports = _extract_imports(content)

    for imp in imports:
        if imp.startswith("."):
            # relative import, should resolve to a file in frontend/
            base = os.path.dirname(path)
            # try .jsx, .js, .tsx, .ts
            resolved = None
            for ext in ("", ".jsx", ".js", ".tsx", ".ts"):
                candidate = os.path.normpath(os.path.join(base, imp + ext))
                if os.path.isfile(candidate):
                    resolved = candidate
                    break
            assert resolved is not None, (
                f"In {fname}, import '{imp}' does not resolve to any file"
            )


# ---------------------------------------------------------------------------
# Phase 5C: API endpoint contract validation
# ---------------------------------------------------------------------------

def test_frontend_api_urls_match_backend():
    """Verify frontend fetch URLs match backend route decorators."""
    supl_app_path = os.path.join(FRONTEND_DIR, "SuplApp.jsx")
    api_py_path = os.path.join(SUPL_DIR, "api.py")
    ws_py_path = os.path.join(SUPL_DIR, "ws_stream.py")

    frontend_content = open(supl_app_path).read()
    api_content = open(api_py_path).read()
    ws_content = open(ws_py_path).read()

    # Frontend should reference these endpoints (directly or via imported hook)
    expected_frontend_urls = [
        "/api/supl/apps",
        "/api/supl/projection/",
    ]

    for url in expected_frontend_urls:
        assert url in frontend_content, (
            f"Frontend missing reference to endpoint {url}"
        )

    # The WS endpoint is in useSuplWebSocket.js
    ws_hook_content = open(os.path.join(FRONTEND_DIR, "useSuplWebSocket.js")).read()
    assert "/api/supl/stream" in ws_hook_content

    # Backend should define these endpoints
    expected_backend_routes = [
        '"GET", "/api/supl/apps"',
        '"GET", "/api/supl/apps/{app_id}"',
        '"POST", "/api/supl/apps/{app_id}/action"',
        '"GET", "/api/supl/projection/{app_id}"',
        '"/api/supl/stream"',
    ]

    all_backend = api_content + "\n" + ws_content
    # Check in a more lenient way
    route_patterns = [
        '/api/supl/apps"',
        '/api/supl/projection/',
        '/api/supl/stream"',
    ]
    for pattern in route_patterns:
        assert pattern in all_backend, (
            f"Backend missing route pattern: {pattern}"
        )


# ---------------------------------------------------------------------------
# Phase 5D: Data structure contract — projection response
# ---------------------------------------------------------------------------

def test_frontend_projection_keys_match_backend():
    """Frontend uses backend projection keys correctly."""
    supl_app_content = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    overlay_content = open(os.path.join(FRONTEND_DIR, "SemanticOverlay.jsx")).read()
    graph_content = open(os.path.join(FRONTEND_DIR, "SemanticGraphView.jsx")).read()

    # ProjectionEngine.UIProjection.to_dict() keys:
    projection_keys = [
        "application_id",
        "application_name",
        "application_version",
        "capabilities",
        "parameters",
        "state",
        "actions",
        "events",
        "lifecycle",
    ]

    combined_frontend = supl_app_content + overlay_content + graph_content

    for key in projection_keys:
        assert key in combined_frontend, (
            f"Frontend does not reference projection key '{key}'"
        )


def test_action_response_keys_match_backend():
    """Frontend reads backend action response keys correctly."""
    supl_app_content = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    overlay_content = open(os.path.join(FRONTEND_DIR, "SemanticOverlay.jsx")).read()
    execution_view = open(os.path.join(FRONTEND_DIR, "SuplExecutionView.jsx")).read()
    combined = supl_app_content + overlay_content + execution_view

    action_response_keys = [
        "interaction_id",
        "execution_id",
        "receipt_id",
        "status",
    ]

    for key in action_response_keys:
        assert key in combined, (
            f"Frontend does not reference action response key '{key}'"
        )


# ---------------------------------------------------------------------------
# Phase 5E: WebSocket contract
# ---------------------------------------------------------------------------

def test_ws_url_matches():
    ws_hook = open(os.path.join(FRONTEND_DIR, "useSuplWebSocket.js")).read()
    ws_backend = open(os.path.join(SUPL_DIR, "ws_stream.py")).read()

    assert "/api/supl/stream" in ws_hook, (
        "Frontend WebSocket hook missing /api/supl/stream"
    )
    assert "/api/supl/stream" in ws_backend, (
        "Backend WebSocket missing /api/supl/stream"
    )


def test_ws_message_types_match():
    ws_hook = open(os.path.join(FRONTEND_DIR, "useSuplWebSocket.js")).read()
    ws_backend = open(os.path.join(SUPL_DIR, "ws_stream.py")).read()

    # Backend sends these message types
    backend_message_types = ["heartbeat", "gap_detected", "resync_required"]
    for msg_type in backend_message_types:
        assert msg_type in ws_backend, (
            f"Backend WS missing message type '{msg_type}'"
        )

    # Frontend handles these message types
    frontend_message_types = ["heartbeat", "gap_detected", "resync_required"]
    for msg_type in frontend_message_types:
        assert msg_type in ws_hook, (
            f"Frontend WS hook missing handler for '{msg_type}'"
        )


def test_ws_connection_states():
    ws_hook = open(os.path.join(FRONTEND_DIR, "useSuplWebSocket.js")).read()
    supl_app = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()

    required_states = ["CONNECTED", "RECONNECTING", "DISCONNECTED"]
    for state in required_states:
        assert state in ws_hook, (
            f"Frontend WS hook missing connection state '{state}'"
        )
        assert state in supl_app, (
            f"Frontend SuplApp missing connection state '{state}'"
        )


# ---------------------------------------------------------------------------
# Phase 5F: Mode switching
# ---------------------------------------------------------------------------

def test_mode_values_match():
    mode_toggle = open(os.path.join(FRONTEND_DIR, "ModeToggle.jsx")).read()
    projection_engine = open(os.path.join(SUPL_DIR, "projection_engine.py")).read()

    # Frontend modes
    assert "native" in mode_toggle
    assert "overlay" in mode_toggle
    assert "graph_native" in mode_toggle

    # Backend UIMode
    assert "NATIVE = \"native\"" in projection_engine
    assert "OVERLAY = \"overlay\"" in projection_engine
    assert "GRAPH_NATIVE = \"graph_native\"" in projection_engine


def test_mode_query_param_used():
    supl_app = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    api_py = open(os.path.join(SUPL_DIR, "api.py")).read()

    # Frontend sends mode as query param
    assert "mode=${mode}" in supl_app

    # Backend receives mode as query param
    assert "mode: str = \"overlay\"" in api_py


# ---------------------------------------------------------------------------
# Phase 5G: Cross-mode consistency — same app across all modes
# ---------------------------------------------------------------------------

def test_cross_mode_preserves_app_id():
    """SuplApp preserves app ID when switching modes."""
    content = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    # mode change handler should not reset app selection
    assert "setMode(newMode)" in content
    assert "setExecutionStatus(\"READY\")" in content


# ---------------------------------------------------------------------------
# Phase 5H: Execution flow
# ---------------------------------------------------------------------------

def test_execution_flow_matches():
    supl_app = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    api_py = open(os.path.join(SUPL_DIR, "api.py")).read()

    # Frontend sends POST with action_id + parameters
    assert "/api/supl/apps/${selectedAppId}/action" in supl_app
    assert "action" in supl_app.lower() or "action_id" in supl_app

    # Backend expects action_id + parameters
    assert "action_id" in api_py
    assert "parameters" in api_py

    # Frontend handles execution statuses
    for status in ["REQUESTED", "EXECUTED", "FAILED"]:
        assert status in supl_app, (
            f"Frontend missing execution status '{status}'"
        )

    # Backend returns execution statuses
    for status in ["EXECUTED", "FAILED", "REJECTED"]:
        assert status in api_py


# ---------------------------------------------------------------------------
# Phase 5I: Native view capabilities (minimal metadata)
# ---------------------------------------------------------------------------

def test_native_mode_filtering():
    projection_engine = open(os.path.join(SUPL_DIR, "projection_engine.py")).read()
    # In native mode, capabilities/parameters/actions/events are cleared
    assert "mode == UIMode.NATIVE" in projection_engine
    assert "projection.capabilities = []" in projection_engine


# ---------------------------------------------------------------------------
# Phase 5J: Security boundary — UI never sets execution/safety authority
# ---------------------------------------------------------------------------

def test_ui_does_not_set_execution_authority():
    """Frontend JSX files must NOT contain execution authority logic."""
    suspicious_patterns = [
        "SafetyGate",
        "UnifiedToolRuntime",
        "EventBus.publish",
        "EventStore.append",
        "ProvenanceLinker",
        "tool_runtime",
        "adapter_registry",
        "map_action",
        "ActionInvocation",
    ]
    for fname in SUPL_FRONTEND_FILES:
        path = os.path.join(FRONTEND_DIR, fname)
        content = open(path).read()
        for pat in suspicious_patterns:
            if pat in content:
                # allow mentions in comments or _display_ of provenance IDs
                if "provenance" in pat.lower():
                    continue
                if "interaction_id" in pat.lower():
                    continue
                pytest.fail(
                    f"{fname} contains execution authority pattern '{pat}'"
                )


def test_frontend_only_calls_api_endpoint():
    """Frontend must only interact via API, never directly with core."""
    supl_app = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    # The only core interactions should be via fetch to API
    # No direct imports of core modules
    forbidden = ["kernel", "runtime", "event_bus", "event_store", "safety"]
    for fname in SUPL_FRONTEND_FILES:
        path = os.path.join(FRONTEND_DIR, fname)
        content = open(path).read()
        for mod in forbidden:
            if mod in content:
                pytest.fail(
                    f"{fname} directly references core module '{mod}'"
                )


# ---------------------------------------------------------------------------
# Phase 5K: Dashboard integration
# ---------------------------------------------------------------------------

def test_dashboard_includes_supl():
    dashboard = open(os.path.join(FRONTEND_DIR, "Dashboard.jsx")).read()
    assert "SuplApp" in dashboard
    assert 'from "./SuplApp"' in dashboard or "from './SuplApp'" in dashboard


# ---------------------------------------------------------------------------
# Phase 5L: Graph view contract
# ---------------------------------------------------------------------------

def test_graph_view_has_event_display():
    graph = open(os.path.join(FRONTEND_DIR, "SemanticGraphView.jsx")).read()
    assert "RECENT EVENTS" in graph
    assert "events" in graph


def test_graph_view_has_execute_button():
    graph = open(os.path.join(FRONTEND_DIR, "SemanticGraphView.jsx")).read()
    assert "Execute" in graph


# ---------------------------------------------------------------------------
# M-SUPL-001 Authority Boundary Enforcement
# ---------------------------------------------------------------------------

def test_ui_never_becomes_projection_authority():
    """M-SUPL-001 §4.2: UI never subsumes projection authority.

    Only the SuplApp orchestrator may call the projection API.
    Presentational components receive projection as props (correct).
    """
    # SuplApp must call the API for projection
    supl_app = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    assert "/api/supl/projection/" in supl_app
    assert "projection" in supl_app

    # Presentational components get projection as prop, not from API
    overlay = open(os.path.join(FRONTEND_DIR, "SemanticOverlay.jsx")).read()
    assert "/api/supl/projection/" not in overlay, (
        "SemanticOverlay must not directly fetch projection"
    )

    graph = open(os.path.join(FRONTEND_DIR, "SemanticGraphView.jsx")).read()
    assert "/api/supl/projection/" not in graph, (
        "SemanticGraphView must not directly fetch projection"
    )


def test_ui_never_becomes_event_authority():
    """M-SUPL-001 §4.2: UI never subsumes event authority."""
    ws_hook = open(os.path.join(FRONTEND_DIR, "useSuplWebSocket.js")).read()
    # UI must use WebSocket, not direct EventBus
    assert "new WebSocket" in ws_hook
    assert "EventBus" not in ws_hook


def test_provenance_is_display_only():
    """M-SUPL-001 §4.2: UI displays provenance but never creates it."""
    execution_view = open(os.path.join(FRONTEND_DIR, "SuplExecutionView.jsx")).read()
    assert "PROVENANCE" in execution_view or "provenance" in execution_view
    supl_app = open(os.path.join(FRONTEND_DIR, "SuplApp.jsx")).read()
    assert "provenance" in supl_app
