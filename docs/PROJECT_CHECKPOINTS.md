# MUSCAL CORE — Project Checkpoints

Milestone protocol.

---

## Checkpoint 0.1 — Kernel Design

- First kernel design
- MKC → Bridge → MEL pipeline defined
- MCXF data format defined

## Checkpoint 0.2 — MKC Integrated

- MKC compiler operational
- mkc_rules.py with SIGNAL_RULES
- Regex-based tool matching in bridge.py
- Deterministic classification (no LLM in L1)

## Checkpoint 0.3 — Graph + Sphere

- GraphState event-driven runtime layer
- SphereState radial UI projection
- DebugEngine with comprehensive tracing

## Checkpoint 0.4 — Plugin System

- `features/` directory created
- Plugin interface defined (register/execute)
- `plugin_registry.py` + `plugin_loader.py`
- `spec/IMMUTABILITY_CONTRACT.md` (v1.0)
- `spec/PLUGIN_API.md` (SDK v1.0)

## Checkpoint 0.5 — Import Stability

- `memory.py`: lazy `_get_conn()` instead of module-level `sqlite3.connect()`
- `mel.py`: lazy `_get_runtime()` instead of module-level `SystemAgentRuntime()`
- `config.py`: lazy `get_session_id()` instead of module-level `datetime.now()`
- `mkc_rules.py`: `reset_state()` + `DEFAULT_KEYWORDS`
- `requirements.txt` complete

## Checkpoint 0.6 — Graph + Memory Pruning

- `graph.py`: MAX_NODES=5000, MAX_EDGES=10000, FIFO eviction
- `memory.py`: MAX_MEMORY_ENTRIES=10000, `_prune_memory()`
- `event_bus.py`: `_max_history=50000`, POP(0) eviction
- `kernel.py`: Safety guard at 10000 nodes

## Checkpoint 0.7 — Prototype READY WITH RISKS

- Stress test: 100 iterations, 0 crashes, deterministic
- Import chain: 3/3 PASS (memory, mel, config)
- Documentation: TECHNICAL_MANUAL_v0.7.md
- Core is declared IMMUTABLE
- Plugin architecture in place

**Technical Debt (known, not addressed):**
- ~80 stub files (<20 lines)
- SIGNAL_RULES drift without auto-reset
- FIFO pruning without semantic selection
- No DB migrations
- No CI/CD

## Checkpoint 0.8 — Architecture Evolution Boundary

- Verifikationsframework analysiert (Framework vs. Ist-Zustand)
- Konflikte identifiziert: Event Sourcing, State Reconstruction, Hash Chains
- Entscheidung: Verification Layer wächst als Plugin-Schicht über dem Core
- Core bleibt IMMUTABLE
- Plugin-basierte Implementierung in `features/event_sourcing/`
- ADR-011 erstellt: Verification Layer Architecture (ACCEPTED)
- Vier Phasen: Konsolidierung → Event Sourcing → Hash Chains → Replay → Verification

**Risikobewertung:**
- Phase 0 (Konsolidierung): MITTEL
- Phase 1-2 (Event Sourcing + Hash): NIEDRIG
- Phase 3 (Replay): MITTEL
- Phase 4 (Verification): NIEDRIG

**Nächster Schritt:** Dokumentationsbaseline abschließen, dann Implementierung starten.

---

## Checkpoint 0.25 — Category A Auto-Fixes (10/10)

- Broken links, kernel.py docstring, missing handover, ADR-007→013
- TASK_BOARD items, test.txt deletion, table count 12→5, perspective count 4→5
- DEVELOPER_PREVIEW deprecation, GOVERNANCE_CHECKPOINT scope fix
- All 10 Category A findings resolved and validated

## Checkpoint 0.26 — Reconciliation Engine Foundation

- `reconciliation/` directory structure created
- 5 scanner specs: ADR_VALIDATOR, DRIFT_DETECTOR, BROKEN_LINK_SCANNER, IMPORT_VALIDATOR, RFC_VALIDATOR
- 4 validator rule sets: ADR_CONSISTENCY_RULES, LINK_INTEGRITY_RULES, SEMANTIC_DRIFT_RULES, IMPORT_INTEGRITY_RULES
- 3 report templates: VALIDATION_REPORT, RECONCILIATION_REPORT, FINDING_TEMPLATE
- Concept hook registry

## Checkpoint 0.27 — Category B Reconciliation

- simple_rag import guards in mcxf_fusion.py, dashboard.py
- meta_reasoning_kernel guard validated
- 8 specs/ link fixes in ANLAGE_PLAN.md, Docs.md, PROJECT_STATE.md
- RestrictedPython sandbox analysis, archive stub analysis

## Checkpoint 0.28 — Repository Cleanup

- RestrictedPython imports removed from plugin_sandbox.py
- DEPRECATED markers added to specs/ORDER.md, specs/adrs/IMPLEMENTATION_STATUS.md, specs/templates/RFC_TEMPLATE.md
- Retention banner added to archive/stubs/emergent_consensus.py

## Checkpoint 0.29.1 — Reconciliation Runtime Kernel

- Core data model: Finding, FindingSet, Category, Severity, FindingStatus, Rule, RuleSet, ScanScope
- Abstract ScannerBase, ReportGenerator (MD format), ReconciliationRunner, HookBase
- 399 lines, 10 files

## Checkpoint 0.29.2 — Repository Snapshot Layer

- `reconciliation/snapshot/` package with RepositorySnapshot, FileNode, HashCache, DirectoryTree
- Immutable snapshot built once, consumed by all scanners
- Lazy SHA-256 hashing with mtime-based invalidation
- DirectoryTree with glob, filter, lookup, traverse
- 463 lines, 5 files

## Checkpoint 0.30 — ScanContext Migration & Snapshot Integration

- `ScanContext` frozen dataclass (snapshot + scope + config placeholder)
- `ScannerBase.scan()` upgraded: `ScanScope` → `ScanContext`; `scan_legacy()` for backward compat
- `RepositorySnapshot.to_scan_scope()` and `ScanScope.from_snapshot()` bidirectional bridge
- `ReconciliationRunner` builds snapshot once, creates context, passes to scanners
- 0 circular imports, 0 breaking changes, 63 net new/changed lines
