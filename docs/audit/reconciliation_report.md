# MUSCAL Reconciliation Report

## Execution Metadata

| Field | Value |
|-------|-------|
| Timestamp | 2026-07-15T04:57:58.890296 |
| Repository | MUSCAL CORE |
| Root | `/home/hz/AlitaProject/Codebase/MUSCAL CORE` |
| Scanners | 5 |

## Summary

| Metric | Value |
|--------|-------|
| Total Findings | 174 |

### By Category

| Category | Count |
|----------|-------|
| A | 7 |
| B | 167 |
| C | 0 |
| D | 0 |

### By Severity

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 71 |
| Medium | 103 |
| Low | 0 |

## Findings

### broken_link_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| BL-001_docs_session_handovers_HANDOVE_path | `docs/session_handovers/HANDOVER_S-2026-07-14-003.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_reconciliation_path | `docs/governance/reconciliation/validators/LINK_INTEGRITY_RULES.md` | Medium | B | Broken internal markdown link |

### adr_validator_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| ADR-CR-004_spec_ADR_001_kernel_md | `spec/ADR-001-kernel.md` | Medium | A | ADR-001 has invalid status: 'ACCEPTED — Phase 1 ✅' |
| ADR-CR-004_spec_ADR_002_memory_md | `spec/ADR-002-memory.md` | Medium | A | ADR-002 has invalid status: 'ACCEPTED — Phase 1 ✅, Phase 3 ✅, Phase 4 ✅' |
| ADR-CR-008_spec_ADR_013_pipeline_md | `spec/ADR-013-pipeline.md` | Medium | A | ADR-013 missing required section(s): ## Consequences, ## Decision, ## Context |
| ADR-CR-010_docs_PROJECT_STATE_md | `docs/PROJECT_STATE.md` | High | A | ADR-013 in ADR-INDEX.md but missing from PROJECT_STATE.md |

### import_validator_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| IMP-IR-002_features_runtime_confidence_re | `features/runtime/confidence_reset.py` | High | B | Plugin imports core module: mkc_rules |
| IMP-IR-001_tests_test_full_pipeline_py | `tests/test_full_pipeline.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_full_pipeline_py | `tests/test_full_pipeline.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_benchmark_py | `tests/test_benchmark.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_benchmark_py | `tests/test_benchmark.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_state_transition_py | `tests/test_state_transition.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_state_transition_py | `tests/test_state_transition.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_multi_hop_reasoner_ | `tests/test_multi_hop_reasoner.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_multi_hop_reasoner_ | `tests/test_multi_hop_reasoner.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_memory_py | `tests/test_memory.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_memory_py | `tests/test_memory.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_plugin_confidence_p | `tests/test_plugin_confidence.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_plugin_confidence_p | `tests/test_plugin_confidence.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_runtime_api_py | `tests/test_runtime_api.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_runtime_api_py | `tests/test_runtime_api.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_replay_determinism_ | `tests/test_replay_determinism.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_replay_determinism_ | `tests/test_replay_determinism.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_boot_contract_py | `tests/test_boot_contract.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_boot_contract_py | `tests/test_boot_contract.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_self_reasoning_kern | `tests/test_self_reasoning_kernel.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_self_reasoning_kern | `tests/test_self_reasoning_kernel.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_stress_py | `tests/test_stress.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_stress_py | `tests/test_stress.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_memory_consistency_ | `tests/test_memory_consistency.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_memory_consistency_ | `tests/test_memory_consistency.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_plugin_audit_py | `tests/test_plugin_audit.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_plugin_audit_py | `tests/test_plugin_audit.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_global_state_py | `tests/test_global_state.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_global_state_py | `tests/test_global_state.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_plugin_health_py | `tests/test_plugin_health.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_plugin_health_py | `tests/test_plugin_health.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_graph_builder_py | `tests/test_graph_builder.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_graph_builder_py | `tests/test_graph_builder.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_task_queue_py | `tests/test_task_queue.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_task_queue_py | `tests/test_task_queue.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_plugin_loading_py | `tests/test_plugin_loading.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_plugin_loading_py | `tests/test_plugin_loading.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_execution_trace_py | `tests/test_execution_trace.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_execution_trace_py | `tests/test_execution_trace.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_conftest_py | `tests/conftest.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_conftest_py | `tests/conftest.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_test_core_pipeline_py | `tests/test_core_pipeline.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_test_core_pipeline_py | `tests/test_core_pipeline.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_container_test_deploymen | `tests/container/test_deployment.py` | High | B | Import 'import yaml' does not resolve |
| IMP-IR-003_tests_container_test_deploymen | `tests/container/test_deployment.py` | Medium | B | Third-party import 'yaml' not in requirements.txt |
| IMP-IR-001_tests_system_test_migration_sc | `tests/system/test_migration_script.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_system_test_migration_sc | `tests/system/test_migration_script.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_system_test_event_persis | `tests/system/test_event_persistence.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_system_test_event_persis | `tests/system/test_event_persistence.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_system_test_sqlite_conso | `tests/system/test_sqlite_consolidation.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_system_test_sqlite_conso | `tests/system/test_sqlite_consolidation.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_system_test_optimizer_pi | `tests/system/test_optimizer_pipeline.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_system_test_optimizer_pi | `tests/system/test_optimizer_pipeline.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_system_test_startup_life | `tests/system/test_startup_lifecycle.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_system_test_startup_life | `tests/system/test_startup_lifecycle.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_contract_test_supervisor | `tests/contract/test_supervisor_lifecycle.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_contract_test_supervisor | `tests/contract/test_supervisor_lifecycle.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_integration_container_te | `tests/integration/container/test_build.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_integration_container_te | `tests/integration/container/test_build.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_integration_container_te | `tests/integration/container/test_run.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_integration_container_te | `tests/integration/container/test_run.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_integration_container_co | `tests/integration/container/conftest.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_integration_container_co | `tests/integration/container/conftest.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_security_test_plugin_san | `tests/security/test_plugin_sandbox_integration.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_security_test_plugin_san | `tests/security/test_plugin_sandbox_integration.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_security_test_api_securi | `tests/security/test_api_security.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_security_test_api_securi | `tests/security/test_api_security.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_security_test_plugin_san | `tests/security/test_plugin_sandbox.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_security_test_plugin_san | `tests/security/test_plugin_sandbox.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_tests_security_test_input_limi | `tests/security/test_input_limits.py` | High | B | Import 'import pytest' does not resolve |
| IMP-IR-003_tests_security_test_input_limi | `tests/security/test_input_limits.py` | Medium | B | Third-party import 'pytest' not in requirements.txt |
| IMP-IR-001_archive_trace_to_graph_py | `archive/trace_to_graph.py` | High | B | Import 'from graph_node import' does not resolve |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from compiler_state import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'compiler_state' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from compiler_updater import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'compiler_updater' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from compiler_validator import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'compiler_validator' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from evolution_evaluator import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'evolution_evaluator' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from evolution_loop import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'evolution_loop' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from evolution_mkc import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'evolution_mkc' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from meta_compiler import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'meta_compiler' not in requirements.txt |
| IMP-IR-001_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | High | B | Import 'from meta_evolution_kernel import' does not resolve |
| IMP-IR-003_archive_meta_evolution_loop_py | `archive/meta_evolution_loop.py` | Medium | B | Third-party import 'meta_evolution_kernel' not in requirements.txt |
| IMP-IR-001_archive_muscal_boot_py | `archive/muscal_boot.py` | High | B | Import 'from kernel_core import' does not resolve |
| IMP-IR-003_archive_muscal_boot_py | `archive/muscal_boot.py` | Medium | B | Third-party import 'kernel_core' not in requirements.txt |
| IMP-IR-001_archive_rag_vector_py | `archive/rag_vector.py` | High | B | Import 'from vector_memory import' does not resolve |
| IMP-IR-001_archive_distributed_muscal_py | `archive/distributed_muscal.py` | High | B | Import 'from global_memory import' does not resolve |
| IMP-IR-003_archive_distributed_muscal_py | `archive/distributed_muscal.py` | Medium | B | Third-party import 'global_memory' not in requirements.txt |
| IMP-IR-001_archive_vector_memory_py | `archive/vector_memory.py` | High | B | Import 'import faiss' does not resolve |
| IMP-IR-003_archive_vector_memory_py | `archive/vector_memory.py` | Medium | B | Third-party import 'faiss' not in requirements.txt |
| IMP-IR-001_archive_graph_system_loop_py | `archive/graph_system_loop.py` | High | B | Import 'from graph_context_builder import' does not resolve |
| IMP-IR-001_archive_graph_system_loop_py | `archive/graph_system_loop.py` | High | B | Import 'from minimal_core import' does not resolve |
| IMP-IR-003_archive_graph_system_loop_py | `archive/graph_system_loop.py` | Medium | B | Third-party import 'minimal_core' not in requirements.txt |
| IMP-IR-001_archive_graph_system_loop_py | `archive/graph_system_loop.py` | High | B | Import 'from minimal_mkc import' does not resolve |
| IMP-IR-003_archive_graph_system_loop_py | `archive/graph_system_loop.py` | Medium | B | Third-party import 'minimal_mkc' not in requirements.txt |
| IMP-IR-001_archive_graph_system_loop_py | `archive/graph_system_loop.py` | High | B | Import 'from minimal_router import' does not resolve |
| IMP-IR-003_archive_graph_system_loop_py | `archive/graph_system_loop.py` | Medium | B | Third-party import 'minimal_router' not in requirements.txt |
| IMP-IR-001_archive_distributed_boot_py | `archive/distributed_boot.py` | High | B | Import 'from distributed_kernel import' does not resolve |
| IMP-IR-003_archive_distributed_boot_py | `archive/distributed_boot.py` | Medium | B | Third-party import 'distributed_kernel' not in requirements.txt |
| IMP-IR-001_archive_distributed_boot_py | `archive/distributed_boot.py` | High | B | Import 'from kernel_core import' does not resolve |
| IMP-IR-003_archive_distributed_boot_py | `archive/distributed_boot.py` | Medium | B | Third-party import 'kernel_core' not in requirements.txt |
| IMP-IR-001_archive_distributed_boot_py | `archive/distributed_boot.py` | High | B | Import 'from muscal_node import' does not resolve |
| IMP-IR-003_archive_distributed_boot_py | `archive/distributed_boot.py` | Medium | B | Third-party import 'muscal_node' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_core import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_core' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_evaluator import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_evaluator' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_feedback import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_feedback' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_fusion import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_fusion' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_mcxf_memory import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_mcxf_memory' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_memory import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_memory' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_mkc import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_mkc' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_rag import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_rag' not in requirements.txt |
| IMP-IR-001_archive_minimal_loop_py | `archive/minimal_loop.py` | High | B | Import 'from minimal_router import' does not resolve |
| IMP-IR-003_archive_minimal_loop_py | `archive/minimal_loop.py` | Medium | B | Third-party import 'minimal_router' not in requirements.txt |
| IMP-IR-001_archive_swarm_system_py | `archive/swarm_system.py` | High | B | Import 'from webrtc_mesh import' does not resolve |
| IMP-IR-001_archive_swarm_system_py | `archive/swarm_system.py` | High | B | Import 'from event_bus_swarm import' does not resolve |
| IMP-IR-003_archive_swarm_system_py | `archive/swarm_system.py` | Medium | B | Third-party import 'event_bus_swarm' not in requirements.txt |

### drift_detector_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| SDR-IR-001_kernel_py | `kernel.py` | High | A | Pipeline order in kernel.py docstring differs from TECHNICAL_BASELINE.md |
| SDR-IR-002_docs_ARCHITECTURE_md | `docs/ARCHITECTURE.md` | High | A | Layer count mismatch between architecture docs |
| SDR-IR-003_docs_ARCHITECTURE_md | `docs/ARCHITECTURE.md` | High | A | ARCHITECTURE.md claims 12 tables but TECHNICAL_BASELINE.md claims 5 |

### rfc_validator_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| RFC-001_archive_history_rfcs_MAS_0001_ | `archive/history/rfcs/MAS-0001.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0400_ | `archive/history/rfcs/MAS-0400.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0012_ | `archive/history/rfcs/MAS-0012.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0005_ | `archive/history/rfcs/MAS-0005.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0500_ | `archive/history/rfcs/MAS-0500.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0000_ | `archive/history/rfcs/MAS-0000.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0009_ | `archive/history/rfcs/MAS-0009.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0010_ | `archive/history/rfcs/MAS-0010.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0301_ | `archive/history/rfcs/MAS-0301.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0008_ | `archive/history/rfcs/MAS-0008.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0004_ | `archive/history/rfcs/MAS-0004.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0007_ | `archive/history/rfcs/MAS-0007.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0100_ | `archive/history/rfcs/MAS-0100.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0002_ | `archive/history/rfcs/MAS-0002.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0006_ | `archive/history/rfcs/MAS-0006.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0011_ | `archive/history/rfcs/MAS-0011.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0003_ | `archive/history/rfcs/MAS-0003.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-001_archive_history_rfcs_MAS_0300_ | `archive/history/rfcs/MAS-0300.md` | Medium | B | RFC frontmatter missing field(s): id |
| RFC-002_archive_history_rfcs_MAS_0001_ | `archive/history/rfcs/MAS-0001.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0400_ | `archive/history/rfcs/MAS-0400.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0012_ | `archive/history/rfcs/MAS-0012.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0005_ | `archive/history/rfcs/MAS-0005.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0500_ | `archive/history/rfcs/MAS-0500.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0000_ | `archive/history/rfcs/MAS-0000.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0009_ | `archive/history/rfcs/MAS-0009.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0010_ | `archive/history/rfcs/MAS-0010.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0301_ | `archive/history/rfcs/MAS-0301.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0008_ | `archive/history/rfcs/MAS-0008.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0004_ | `archive/history/rfcs/MAS-0004.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0007_ | `archive/history/rfcs/MAS-0007.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0100_ | `archive/history/rfcs/MAS-0100.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0002_ | `archive/history/rfcs/MAS-0002.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0006_ | `archive/history/rfcs/MAS-0006.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0011_ | `archive/history/rfcs/MAS-0011.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0003_ | `archive/history/rfcs/MAS-0003.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |
| RFC-002_archive_history_rfcs_MAS_0300_ | `archive/history/rfcs/MAS-0300.md` | Medium | B | RFC missing required section(s): ## Consequences, ## Decision, ## Motivation, ## |

*Report generated 2026-07-15T04:57:58.890296 by MUSCAL Reconciliation Engine.*