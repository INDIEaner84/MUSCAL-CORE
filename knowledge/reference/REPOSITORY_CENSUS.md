# REPOSITORY_CENSUS — MUSCAL CORE

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** RAW FACT / EXTRACTED METADATA
**Source:** `MUSCAL CORE/` (S3) · **Date:** 2026-08-01 · **Method:** file system walk + git inspection (read-only)

---

## 1. Overview Numbers

| Metric | Value | Confidence |
|--------|-------|------------|
| Total files (excluding node_modules/.git/__pycache__/build) | **1,209** | C0 (walk) |
| Python files | **611** | C0 |
| Python LOC | **77,376** | C0 (line count) |
| Markdown files | **422** | C0 |
| YAML files | 108 | C0 |
| Test files (`tests/`) | **204** | C0 |
| Test functions (`def test_`) | **2,869** | C0 (grep) |
| JSX/TS frontend files | 21 | C0 |
| JSON / JSONL | 18 | C0 |
| Git last commit | **2026-07-20 20:59** | C0 (`git log -1`) |
| Uncommitted changes | **197** (29 modified, 168 untracked) | C0 (`git status`) |

> **CRITICAL GAP [C0]:** The last git commit is `2026-07-20 20:59`. All repository activity after that date — including the entire MC-TC-003D/004/005/006/007 audit trail, E3.2/E3.3 reports, `spec/OVERRIDE.md` updates and `spec/ADR-014-tool-runtime.md` (all dated 2026-07-23 → 2026-07-30) — is **NOT in git history**. 29 modified files include core files declared IMMUTABLE (`kernel.py`, `graph.py`, `mel.py`, `muscal_os.py`, `schema.py`, `event_bus.py`, `plugin_registry.py`).

## 2. Top-Level Directory Census

| Directory | Files | Classification | Notes |
|-----------|------:|----------------|-------|
| `docs/` | 402 | Documentation + audits + handovers | 55 audit docs, 14 handovers, 21 governance |
| `tests/` | 204 | Tests | 18 subdirectories |
| `features/` | 187 | Plugin/Feature implementations | 42 plugin dirs (AGENTS.md: "ALL EXTENSIONS GO TO /features/") |
| `runtime/` | 62 | Core runtime (immutable per SESSION_RULES) | — |
| `.opencode/` | 59 | Session infrastructure | SESSION_RULES.md, 6 subdirs (EVENTBUS, MAOP, MONITORING, OC AGENT BUILD TEAM, REGISTRY, TESTING) |
| `archive/` | 49 | Historical | `history/adrs/` (6), `history/rfcs/` (18), `stubs/` (1 remaining `.py`) |
| `spec/` | 26 | Governance/ADRs/Contracts | 14 canonical ADRs + `ADRs/` (3) + contracts |
| `reconciliation/` | 25 | Governance enforcement code | scanner, runner, report, snapshot |
| `frontend/` | 14 | Dashboard UI | JSX |
| `guards/` | 12 | Pre-commit/CI guards | — |
| `muscal-mvp/` | 11 | **Second implementation** | `core/engine/mcir/ve` — separate MVP |
| `storage/` | 10 | Runtime storage | — |
| `baseline/` | 6 | Test baseline | — |
| `.github/` | 5 | CI workflows | — |
| `scripts/` | 3 | Utilities | — |
| `specs/` (plural) | 3 | **Duplication candidate** | `ORDER.md`, `adrs/IMPLEMENTATION_STATUS.md`, `schemas/`, `templates/` |
| `api/`, `reports/`, `white-paper/`, `build/` | small | API server, reports, whitepaper, build artifact | — |
| Root-level `*.py` | 99 | Core modules | 7,803 LOC — see §4 |

## 3. Documentation Classification (422 md files)

| Category | Location | Count | Newest |
|----------|----------|------:|--------|
| Audit / certification | `docs/audit/` | 55 | 2026-07-30 (MC-TC-004 ARB_DECISION, CERTIFICATION_REPORT) |
| Governance | `docs/governance/` | 21 | 2026-07-20 (CHECKPOINT_INDEX, WORK_QUEUE, ACTIVE_TASKS) |
| Session handovers | `docs/session_handovers/` | 14 | 2026-07-27 (HANDOVER_S-2026-07-27-001) |
| History | `docs/history/` | 11 | incl. `technical_manual_v0.6.md` |
| Specs & contracts | `spec/` | 22 | 2026-07-28 (OVERRIDE.md, ADR-014) |
| Historical ADRs | `archive/history/adrs/` | 6 | — |
| Historical RFCs (MAS) | `archive/history/rfcs/` | 18 | — |
| Root docs | root + `docs/*.md` | ~30 | PROJECT_STATE 07-20, SESSION_REGISTRY 07-28 |
| Whitepaper | `white-paper/` | 1 | — |

## 4. Core Module Inventory (root `*.py`, 99 files, 7,803 LOC)

IMMUTABLE per SESSION_RULES (`kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py, mkc_rules.py, config.py, event_bus.py, graph.py, feedback.py, muscal_os.py, main.py, main_boot.py, boot_manager.py, os_config.py, sphere.py, debugger.py, tools.py, rag.py, trace_engine.py, plugin_registry.py, plugin_loader.py`) — verified actual line counts:

| File | Declared v0.7 manual | Actual (2026-08-01) | Delta | Confidence |
|------|---------------------|--------------------:|-------|------------|
| `kernel.py` | 417 lines | **708** | +291 | C0 |
| `memory.py` | 139 lines | **162** | +23 | C0 |
| `graph.py` | 219 lines | **279** | +60 | C0 |
| `event_bus.py` | 74 lines | **111** | +37 | C0 |

> **CONFLICT [C0]:** TECHNICAL_MANUAL_v0.7 §4 documents per-module line counts that are **all below** current file sizes. The manual reflects an earlier snapshot (≈2026-07-12), while the code has grown since (v0.8 additions). See TECHNICAL_MANUAL_CONFLICT_REPORT.md.

## 5. Duplication Map

| Duplication | Evidence | Impact | Confidence |
|-------------|----------|--------|------------|
| **ADR locations ×4** | `spec/ADR-*.md` (14) · `spec/ADRs/` (3) · `specs/adrs/` (1 status file) · `archive/history/adrs/` (6) | Authority ambiguity — which ADR set is canonical? | C0 (file walk) |
| **`spec/` vs `specs/`** | Two sibling directories with different ADR structures | Confusion risk | C0 |
| **`muscal-mvp/` vs core** | Second implementation of core/engine/mcir/ve | Two codebases claim the same domain | C0 |
| **Mislabelled ADR file** | `spec/ADR-013-pipeline.md` contains content titled "# ADR-007: Feature Plugin Migration Path" | Filename ≠ content — breaks ADR lookup | C0 (content read) |
| **Manual versions ×3** | `Codebase/TECHNICAL_MANUAL.md` (v0.5) · `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md` (v0.7) · `docs/history/technical_manual_v0.6.md` (v0.6) | Conflicting version authority | C0 |
| **Checkpoint reports** | `docs/governance/checkpoints/` vs `docs/governance/*.md` vs `docs/audit/*.md` | Multiple overlapping checkpoint sources | C1 |
| **Test counts ×4** | PROJECT_STATE: 547 · E3.2 chat: 812 · MC-TC-004: 431 · MC-TC-007: 384 (actual test functions: 2,869) | No single test-count authority | C1 |

## 6. Stale / Obsolete Artifacts

| Artifact | Status | Notes | Confidence |
|----------|--------|-------|------------|
| `build/`, `__pycache__`, `*.egg-info`, `.pytest_cache` | Build/cache debris | Not source of truth | C0 |
| `archive/stubs/emergent_consensus.py` | 1 file remains | PROJECT_STATE claims "alle 28 Stubs gelöscht" [C1] — 1 file + `__pycache__` remain | C0 (walk) |
| `CHANGELOG_v0.7.md`, `CHANGELOG_v0.8.md` | Version changelogs | v0.8 changelog exists but no v0.8 manual | C1 |
| `TECHNICAL_MANUAL.md` (root, v0.5) | Outdated version | Claims "~237 files across two coexisting codebases" | C0 |
| `docs/history/Session Muscal Core.md`, `mcxf_demo.md` | Historical session notes | reference only (SESSION_RULES: history has no authority) | C1 |
| `.env.example`, `requirements*.txt` | Config | `spec.yaml` + `requirements.lock` suggest 2 dependency sources | C1 |

## 7. Git / Version Control State

| Item | Value | Confidence |
|------|-------|------------|
| Last commit | 2026-07-20 20:59:32 (cdaa1c2) | C0 |
| Uncommitted modified | **29** files — incl. core `kernel.py`, `graph.py`, `mel.py`, `muscal_os.py`, `schema.py`, `event_bus.py`, `plugin_registry.py` | C0 |
| Uncommitted untracked | **168** files — mostly `docs/audit/MC-TC-*`, `E3.*` reports, `GRAPH_OS_*` | C0 |
| CHANGE_JOURNAL coverage | ends **2026-07-13** (C-004) | C0 |
| SESSION_REGISTRY coverage | ends **2026-07-27** (S-2026-07-27-001) | C0 |

> **CONSEQUENCE [C1]:** Per CHANGE_JOURNAL the authority hierarchy is "Git History → CHANGE_JOURNAL → SESSION_REGISTRY". The **entire audit wave 2026-07-23 → 2026-07-30 (MC-TC-003D/004/005/006/007, E3.2, OVERRIDE-067..073)** exists only as untracked files — technically not part of Git History and therefore **not visible to the declared authority chain**.

## 8. Repository Health Indicators

| Indicator | Reading | Trend |
|-----------|---------|-------|
| Code size | 611 py / 77,376 LOC | Large for a "Stable Prototype" |
| Test surface | 2,869 test functions / 204 files | Healthy size |
| Version claims | v0.7 manual / v0.8 changelog / "Baseline 1.0.0" | Divergent version labels |
| Governance enforcement | `reconciliation/` + `guards/` + `.github/` | Present |
| Documentation currency | Newest authoritative doc: 07-20 (PROJECT_STATE); audit docs to 07-30 | State docs stale by 11–12 days vs audits |
| Git hygiene | 197 uncommitted changes | **Critical — longest uncommitted window is 11 days** |
| Duplication | 4× ADR locations, 3× manuals, 2× codebases | High |

---

*Provenance: all counts computed read-only on 2026-08-01 from `MUSCAL CORE/` file system, git, and document contents.*
