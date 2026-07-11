#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PYTHONPATH=".:${PYTHONPATH:-}"

echo "=============================================="
echo "  MUSCAL CORE — ALL TESTS"
echo "=============================================="

total=0
passed=0
failed=0

PYTEST="python3 -m pytest"

run_test() {
    local name="$1"
    local cmd="$2"
    total=$((total + 1))
    printf "  %-30s ... " "$name"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ PASS"
        passed=$((passed + 1))
    else
        echo "❌ FAIL"
        failed=$((failed + 1))
    fi
}

echo ""
echo "--- Core Tests ---"
run_test "stress_test (100 iter)"    "$PYTEST tests/test_stress.py -v"
run_test "test_import_safety"        "$PYTEST tests/test_import_safety.py -v"
run_test "test_global_state"         "$PYTEST tests/test_global_state.py -v"
run_test "test_determinism"          "$PYTEST tests/test_determinism.py -v"

echo ""
echo "--- Plugin Tests ---"
run_test "test_plugin_loading"       "$PYTEST tests/test_plugin_loading.py -v"
run_test "test_plugin_audit"         "$PYTEST tests/test_plugin_audit.py -v"
run_test "test_plugin_confidence"    "$PYTEST tests/test_plugin_confidence.py -v"
run_test "test_plugin_health"        "$PYTEST tests/test_plugin_health.py -v"

echo ""
echo "--- Critical-Path Tests ---"
run_test "test_graph"                "$PYTEST tests/test_graph.py -v"
run_test "test_mkc"                  "$PYTEST tests/compiler/test_mkc.py -v"
run_test "test_bridge"               "$PYTEST tests/compiler/test_bridge.py -v"
run_test "test_mel"                  "$PYTEST tests/execution/test_mel.py -v"
run_test "test_memory"               "$PYTEST tests/test_memory.py -v"
run_test "test_kernel_boot"          "$PYTEST tests/kernel/test_boot.py -v"
run_test "test_state_transition"     "$PYTEST tests/kernel/test_state_transition.py -v"
run_test "test_pipeline_stability"   "$PYTEST tests/kernel/test_pipeline_stability.py -v"
run_test "test_events"               "$PYTEST tests/kernel/test_events.py -v"
run_test "test_eventbus_verification" "$PYTEST tests/test_eventbus_verification.py -v"
run_test "test_api_boot"             "$PYTEST tests/test_zzz_api_boot.py -v"

echo ""
echo "--- Reference Validation ---"
run_test "ref_full_pipeline"         "$PYTEST tests/test_full_pipeline.py -v"
run_test "ref_replay"                "$PYTEST tests/test_replay_determinism.py -v"
run_test "ref_memory"                "$PYTEST tests/test_memory_consistency.py -v"
run_test "ref_exec_trace"            "$PYTEST tests/test_execution_trace.py -v"

echo ""
echo "--- Security Regression ---"
run_test "path_policy"               "$PYTEST tests/security/test_path_policy.py -v"
run_test "input_limits"              "$PYTEST tests/security/test_input_limits.py -v"
run_test "db_validation"             "$PYTEST tests/security/test_database_validation.py -v"
run_test "tool_return_contract"      "$PYTEST tests/security/test_tool_return_contract.py -v"
run_test "api_security"              "$PYTEST tests/security/test_api_security.py -v"
run_test "plugin_timeout"            "$PYTEST tests/security/test_plugin_timeout.py -v"

echo ""
echo "--- Contract Tests ---"
run_test "supervisor_lifecycle"      "$PYTEST tests/contract/test_supervisor_lifecycle.py -v"

echo ""
echo "--- Container / Deployment ---"
run_test "deployment_contract"       "$PYTEST tests/container/test_deployment.py -v"

echo ""
echo "--- System Integration ---"
run_test "migration_script"          "$PYTEST tests/system/test_migration_script.py -v"
run_test "sqlite_consolidation"      "$PYTEST tests/system/test_sqlite_consolidation.py -v"
run_test "startup_lifecycle"         "$PYTEST tests/system/test_startup_lifecycle.py -v"

echo ""
echo "--- Coverage Analysis ---"
run_test "hook_coverage"             "$PYTEST tests/test_hook_coverage.py -v"

echo ""
echo "=============================================="
echo "  RESULTS: $passed/$total passed"
if [ "$failed" -gt 0 ]; then
    echo "  FAILED: $failed test(s)"
    exit 1
fi
echo "  ALL PASS"
echo "=============================================="
