# MUSCAL Reconciliation Report

## Execution Metadata

| Field | Value |
|-------|-------|
| Timestamp | 2026-07-16T13:06:13.432725 |
| Repository | MUSCAL CORE |
| Root | `/home/hz/AlitaProject/Codebase/MUSCAL CORE` |
| Scanners | 5 |

## Summary

| Metric | Value |
|--------|-------|
| Total Findings | 53 |

### By Category

| Category | Count |
|----------|-------|
| A | 7 |
| B | 46 |
| C | 0 |
| D | 0 |

### By Severity

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 5 |
| Medium | 48 |
| Low | 0 |

## Findings

### broken_link_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| BL-001_docs_session_handovers_HANDOVE_path | `docs/session_handovers/HANDOVER_S-2026-07-14-003.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM___args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM___args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM_args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM___args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.0.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM_args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.0.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM___args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.0.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_ADR_014_IMPLEM_args | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.0.md` | Medium | B | Broken internal markdown link |
| BL-001_docs_governance_reconciliation_path | `docs/governance/reconciliation/validators/LINK_INTEGRITY_RULES.md` | Medium | B | Broken internal markdown link |

### adr_validator_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| ADR-CR-004_spec_ADR_001_kernel_md | `spec/ADR-001-kernel.md` | Medium | A | ADR-001 has invalid status: 'ACCEPTED — Phase 1 ✅' |
| ADR-CR-004_spec_ADR_002_memory_md | `spec/ADR-002-memory.md` | Medium | A | ADR-002 has invalid status: 'ACCEPTED — Phase 1 ✅, Phase 3 ✅, Phase 4 ✅' |
| ADR-CR-008_spec_ADR_013_pipeline_md | `spec/ADR-013-pipeline.md` | Medium | A | ADR-013 missing required section(s): ## Context, ## Consequences, ## Decision |
| ADR-CR-010_docs_PROJECT_STATE_md | `docs/PROJECT_STATE.md` | High | A | ADR-013 in ADR-INDEX.md but missing from PROJECT_STATE.md |

### import_validator_scanner

| ID | File | Severity | Category | Description |
|----|------|----------|----------|-------------|
| IMP-IR-002_features_runtime_confidence_re | `features/runtime/confidence_reset.py` | High | B | Plugin imports core module: mkc_rules |

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

*Report generated 2026-07-16T13:06:13.432725 by MUSCAL Reconciliation Engine.*