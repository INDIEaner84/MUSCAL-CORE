from unittest.mock import MagicMock

from kernel import MuscalKernel


def test_lambda_closure_all_events_trigger():
    kernel = MuscalKernel(enable_graph=True, enable_sphere=True)
    sphere_sync = MagicMock()
    kernel.sphere.sync = sphere_sync

    system_action_events = ["SYSTEM_ACTION_STARTED", "SYSTEM_ACTION_COMPLETED", "SYSTEM_ACTION_FAILED"]
    non_system_events = ["NODE_CREATED", "NODE_UPDATED", "EDGE_CREATED",
                         "EXECUTION_STARTED", "EXECUTION_FINISHED"]

    for evt in non_system_events:
        kernel.graph.emit(evt, {})

    count_after_non_system = sphere_sync.call_count
    assert count_after_non_system == len(non_system_events), (
        f"Expected {len(non_system_events)} sync calls for non-system events, "
        f"got {count_after_non_system}"
    )

    for evt in system_action_events:
        kernel.graph.emit(evt, {"type": evt, "payload": {"tool": "browser.click"}})

    count_total = sphere_sync.call_count
    assert count_total > count_after_non_system, "System action events should also trigger sync"


def test_lambda_closure_system_action_routes_to_handler():
    kernel = MuscalKernel(enable_graph=True, enable_sphere=False)
    on_action = MagicMock()
    kernel.system.on_action_event = on_action

    kernel.graph.emit("SYSTEM_ACTION_STARTED", {"type": "SYSTEM_ACTION_STARTED", "payload": {}})
    assert on_action.call_count == 1, "SYSTEM_ACTION_STARTED must trigger on_action_event"

    kernel.graph.emit("EXECUTION_STARTED", {})
    assert on_action.call_count == 1, "EXECUTION_STARTED must NOT trigger on_action_event"
