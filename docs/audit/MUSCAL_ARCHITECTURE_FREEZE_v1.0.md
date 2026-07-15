# MUSCAL Architecture Freeze v1.0

**Version:** 1.0.0
**Date:** 2026-07-15
**Status:** Authoritative Architecture Reference

---

## 1. Repository Structure

```
reconciliation/
├── __init__.py              # Public API exports
├── scanner.py               # ScannerBase ABC
├── runner.py                # ReconciliationRunner
├── report.py                # ReportGenerator
├── core/
│   ├── __init__.py
│   ├── context.py           # ScanContext
│   ├── finding.py           # Finding, FindingSet, Category, Severity
│   ├── rule.py              # Rule, RuleSet
│   └── scope.py             # ScanScope
├── engine/
│   ├── __init__.py
│   ├── rule_engine.py       # RuleEngine
│   └── checkers.py          # FileExistsChecker, ContentMatchChecker, FileCountChecker
├── scan/
│   ├── __init__.py
│   ├── link_scanner.py      # BrokenLinkScanner
│   ├── adr_scanner.py       # AdrValidatorScanner
│   ├── import_scanner.py    # ImportValidatorScanner
│   ├── drift_scanner.py     # DriftDetectorScanner
│   └── rfc_scanner.py       # RfcValidatorScanner
├── snapshot/
│   ├── __init__.py
│   ├── repository_snapshot.py  # RepositorySnapshot
│   ├── file_node.py         # FileNode
│   ├── hash_cache.py        # HashCache
│   └── tree.py              # DirectoryTree, TreeNode
└── hooks/
    └── __init__.py          # HookBase (placeholder)

scripts/
├── reconcile.py             # CLI Entry Point
├── build_scanner_report.py  # Report Builder
├── checkpoint_summary.py    # Checkpoint Summarizer
├── config_snapshot.py       # Config Snapshot
└── registry.py              # Script Registry

guards/
├── install_hook.sh          # Pre-commit Hook Installer
└── pre-commit               # Pre-commit Script
```

---

## 2. Package Inventory

### 2.1 Core Package (`reconciliation.core`)

| Module | Size | Purpose |
|--------|------|---------|
| `context.py` | 408 bytes | ScanContext frozen dataclass |
| `finding.py` | 2,260 bytes | Finding, FindingSet, Category, Severity, FindingStatus |
| `rule.py` | 469 bytes | Rule, RuleSet dataclasses |
| `scope.py` | 1,800 bytes | ScanScope definition |

### 2.2 Engine Package (`reconciliation.engine`)

| Module | Size | Purpose |
|--------|------|---------|
| `rule_engine.py` | 1,571 bytes | Generic rule evaluation engine |
| `checkers.py` | 4,493 bytes | FileExistsChecker, ContentMatchChecker, FileCountChecker |

### 2.3 Scan Package (`reconciliation.scan`)

| Module | Size | Purpose |
|--------|------|---------|
| `link_scanner.py` | 4,910 bytes | Markdown link validation |
| `adr_scanner.py` | 17,005 bytes | ADR compliance validation |
| `import_scanner.py` | 9,879 bytes | Import integrity validation |
| `drift_scanner.py` | 11,509 bytes | Architecture drift detection |
| `rfc_scanner.py` | 9,486 bytes | RFC compliance validation |

### 2.4 Snapshot Package (`reconciliation.snapshot`)

| Module | Size | Purpose |
|--------|------|---------|
| `repository_snapshot.py` | 4,387 bytes | Immutable repository snapshot |
| `file_node.py` | 1,104 bytes | File metadata representation |
| `hash_cache.py` | 936 bytes | Lazy SHA-256 hashing |
| `tree.py` | 2,355 bytes | Directory tree with glob/filter |

### 2.5 Root Package (`reconciliation`)

| Module | Size | Purpose |
|--------|------|---------|
| `scanner.py` | 695 bytes | ScannerBase ABC |
| `runner.py` | 2,620 bytes | ReconciliationRunner |
| `report.py` | 6,549 bytes | ReportGenerator |

---

## 3. Public API Inventory

### 3.1 Exports from `reconciliation/__init__.py`

```python
# Core
Category
Finding
FindingSet
FindingStatus
Severity
Rule
RuleSet
ScanScope
ScannerBase
ScanContext

# Engine
RuleEngine
RuleChecker

# Runner
ReconciliationRunner
ReportGenerator

# Scanners
BrokenLinkScanner
AdrValidatorScanner
ImportValidatorScanner
DriftDetectorScanner
RfcValidatorScanner
```

### 3.2 Scanner API

```python
class ScannerBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def rules(self) -> list[Rule]: ...

    @abstractmethod
    def scan(self, context: ScanContext) -> FindingSet: ...

    def scan_legacy(self, scope: ScanScope) -> FindingSet: ...

    @property
    def auto_fixable(self) -> bool: ...
```

### 3.3 Runner API

```python
class ReconciliationRunner:
    def __init__(self, repo_root: str = "."): ...
    def register(self, scanner: ScannerBase) -> None: ...
    def register_defaults(self) -> None: ...
    def run_all(self, context: ScanContext | None = None) -> list[FindingSet]: ...
    def run_scanner(self, name: str, context: ScanContext | None = None) -> FindingSet | None: ...
    def save_report(self, results: list[FindingSet], path: str, checkpoint: str = "") -> str: ...
```

### 3.4 Report API

```python
class ReportGenerator:
    def finding_report(self, finding: Finding) -> str: ...
    def validation_report(self, findings: FindingSet) -> str: ...
    def reconciliation_report(self, results: list[FindingSet], checkpoint: str = "") -> str: ...
    def build_summary(self, results: list[FindingSet]) -> dict: ...
```

### 3.5 Snapshot API

```python
class RepositorySnapshot:
    def __init__(self, repo_root: str = ".", ignore_patterns: list[str] | None = None): ...
    def build(self) -> None: ...
    @property
    def files(self) -> list[FileNode]: ...
    @property
    def tree(self) -> DirectoryTree: ...
    def file_node_for(self, path: str) -> FileNode | None: ...
    def hash_for(self, path: str) -> str | None: ...
    def filter(self, extension: str | None = None, directory: str | None = None) -> list[FileNode]: ...
    def glob(self, pattern: str) -> list[FileNode]: ...
    def to_scan_scope(self) -> ScanScope: ...
    def invalidate_hash(self, path: str) -> None: ...
```

---

## 4. Dependency Graph

```
reconciliation
├── reconciliation.core
│   ├── context.py → snapshot.repository_snapshot, core.scope
│   ├── finding.py → (no dependencies)
│   ├── rule.py → core.finding
│   └── scope.py → (no dependencies)
├── reconciliation.engine
│   ├── rule_engine.py → core.finding, core.rule
│   └── checkers.py → core.finding
├── reconciliation.scan
│   ├── link_scanner.py → scanner, core.context, core.finding, core.rule, snapshot
│   ├── adr_scanner.py → scanner, core.context, core.finding, core.rule, snapshot
│   ├── import_scanner.py → scanner, core.context, core.finding, core.rule, snapshot
│   ├── drift_scanner.py → scanner, core.context, core.finding, core.rule, snapshot
│   └── rfc_scanner.py → scanner, core.context, core.finding, core.rule, snapshot
├── reconciliation.snapshot
│   ├── repository_snapshot.py → file_node, hash_cache, tree
│   ├── file_node.py → (no dependencies)
│   ├── hash_cache.py → (no dependencies)
│   └── tree.py → file_node
├── reconciliation.scanner → core.context, core.finding, core.rule
├── reconciliation.runner → core.context, core.finding, report, scanner, snapshot
└── reconciliation.report → core.finding
```

**No circular dependencies detected.**

---

## 5. Runtime Flow

```
1. CLI Entry (scripts/reconcile.py)
   │
   v
2. ReconciliationRunner(repo_root)
   │
   v
3. runner.register_defaults()
   │  └── Imports: reconciliation.scan
   │  └── Registers: 5 scanners
   │
   v
4. runner.run_all()
   │
   v
5. _build_context()
   │  ├── RepositorySnapshot(repo_root)
   │  ├── snapshot.build()
   │  └── ScanContext(snapshot=snapshot, scope=scope)
   │
   v
6. For each scanner:
   │  ├── scanner.scan(context)
   │  ├── discovery: snapshot.glob("**/*.md")
   │  ├── validation: rule-specific checks
   │  └── FindingSet(scanner=name, findings=[...])
   │
   v
7. Collect all FindingSet results
   │
   v
8. ReportGenerator.build_summary(results)
   │  └── Aggregate: scanners, findings, categories, severity
   │
   v
9. _build_report(repo_root, results, summary)
   │  └── Generate markdown report
   │
   v
10. Save to docs/audit/reconciliation_report.md
```

---

## 6. Scanner Inventory

| Scanner | File | Rules | Lines | Purpose |
|---------|------|-------|-------|---------|
| BrokenLinkScanner | `link_scanner.py` | BL-001, BL-002 | 141 | Markdown link validation |
| AdrValidatorScanner | `adr_scanner.py` | ADR-CR-001 to ADR-CR-010 | 418 | ADR compliance |
| ImportValidatorScanner | `import_scanner.py` | IMP-IR-001 to IMP-IR-004 | ~300 | Import integrity |
| DriftDetectorScanner | `drift_scanner.py` | SDR-IR-001 to SDR-IR-004 | ~350 | Architecture drift |
| RfcValidatorScanner | `rfc_scanner.py` | RFC-001 to RFC-003 | 244 | RFC compliance |

**Total:** 5 scanners, ~1,453 lines of scanner code

---

## 7. Rule Inventory

### 7.1 BrokenLinkScanner Rules

| Rule | Description | Severity | Category |
|------|-------------|----------|----------|
| BL-001 | Internal links must point to existing files | Medium | B |
| BL-002 | External links ignored | Low | D |

### 7.2 AdrValidatorScanner Rules

| Rule | Description | Severity | Category |
|------|-------------|----------|----------|
| ADR-CR-001 | Unique ADR numbers | High | A |
| ADR-CR-002 | ADR-INDEX.md completeness | High | A |
| ADR-CR-003 | Index accuracy | High | A |
| ADR-CR-004 | Valid status values | Medium | A |
| ADR-CR-005 | APPLIED ADRs must have date | Medium | A |
| ADR-CR-007 | Sequential numbering | Low | B |
| ADR-CR-008 | Required sections | Medium | A |
| ADR-CR-009 | Filename format | Low | A |
| ADR-CR-010 | PROJECT_STATE alignment | High | A |

### 7.3 ImportValidatorScanner Rules

| Rule | Description | Severity | Category |
|------|-------------|----------|----------|
| IMP-IR-001 | Unresolvable imports | High | B |
| IMP-IR-002 | Core module imports from features | High | B |
| IMP-IR-003 | Missing requirements.txt | Medium | B |
| IMP-IR-004 | Unused imports | Medium | B |

### 7.4 DriftDetectorScanner Rules

| Rule | Description | Severity | Category |
|------|-------------|----------|----------|
| SDR-IR-001 | Pipeline order drift | High | A |
| SDR-IR-002 | Layer count mismatch | Medium | B |
| SDR-IR-003 | Table count mismatch | Medium | B |
| SDR-IR-004 | Module count drift | Medium | B |

### 7.5 RfcValidatorScanner Rules

| Rule | Description | Severity | Category |
|------|-------------|----------|----------|
| RFC-001 | Frontmatter validation | Medium | B |
| RFC-002 | Required sections | Medium | B |
| RFC-003 | Numbering consistency | High | A |

**Total:** 22 rules across 5 scanners

---

## 8. Report Pipeline

### 8.1 Report Types

| Type | Method | Output |
|------|--------|--------|
| Individual Finding | `finding_report()` | Single finding markdown |
| Validation Report | `validation_report()` | Single scanner markdown |
| Reconciliation Report | `reconciliation_report()` | Full pipeline markdown |
| Summary | `build_summary()` | dict with metrics |

### 8.2 Summary Structure

```python
{
    "scanners": int,
    "finding_sets": int,
    "total_findings": int,
    "categories": {"A": int, "B": int, "C": int, "D": int},
    "severity": {"Critical": int, "High": int, "Medium": int, "Low": int}
}
```

### 8.3 Report Sections

1. Execution Metadata (timestamp, repo, scanners)
2. Summary (total, categories, severity)
3. Scanner Results (per-scanner table)
4. Findings (grouped by scanner, detailed per finding)

---

## 9. CLI Components

### 9.1 Entry Point

**File:** `scripts/reconcile.py`
**Size:** 3,348 bytes
**Executable:** Yes

### 9.2 Functions

| Function | Purpose |
|----------|---------|
| `main()` | CLI entry, orchestration |
| `_find_repo_root()` | Auto-detect repository root |
| `_build_report()` | Generate markdown report |

### 9.3 Usage

```bash
python3 scripts/reconcile.py
```

### 9.4 Output

- **Path:** `docs/audit/reconciliation_report.md`
- **Format:** Markdown
- **Size:** ~26KB (174 findings)

---

## 10. Snapshot Layer

### 10.1 Components

| Component | Purpose |
|-----------|---------|
| `RepositorySnapshot` | Immutable repository state |
| `FileNode` | File metadata (path, size, hash, mtime) |
| `HashCache` | Lazy SHA-256 with mtime invalidation |
| `DirectoryTree` | Tree structure with glob/filter |

### 10.2 Discovery Method

```python
snapshot.glob("**/*.md")  # Primary discovery
snapshot.filter(extension=".py")  # Extension filter
snapshot.filter(directory="src")  # Directory filter
```

### 10.3 Immutability

- Snapshot built once via `snapshot.build()`
- All scanners consume same snapshot instance
- Hash computed lazily on first access
- mtime-based invalidation for rebuilds

### 10.4 Ignore Patterns

Default ignores:
- `.git/**`, `__pycache__/**`, `*.pyc`
- `.venv/**`, `venv/**`
- `*.db`, `*.sqlite`
- `.env`, `.env.*`
- `*.egg-info/**`, `build/**`, `dist/**`
- `.pytest_cache/**`, `.mypy_cache/**`, `.ruff_cache/**`

---

## 11. Governance Layer

### 11.1 Enforcement Cycle

```
Baseline → Run → Report → Compare → Action
    ↑                                    │
    └────────────────────────────────────┘
```

### 11.2 Current Baseline

- **Document:** `docs/audit/MUSCAL_RECONCILIATION_BASELINE_v1.0.md`
- **Findings:** 174
- **Date:** 2026-07-15

### 11.3 Enforcement Rules

1. No ADR changes during enforcement
2. No RFC changes during enforcement
3. No architecture document modifications
4. Only documentation and tooling may be created
5. Findings are documented, not auto-fixed

### 11.4 Governance Reports

- `docs/audit/reconciliation_report.md` — Current run
- `docs/audit/MUSCAL_RECONCILIATION_BASELINE_v1.0.md` — Reference baseline
- `docs/audit/MUSCAL_MASTER_TRANSFER_PACKAGE_v1.0.md` — Project transfer document

---

## 12. Current Technical Debt

| # | Item | Severity | File |
|---|------|----------|------|
| 1 | ImportValidatorScanner high volume (129 findings) | Medium | import_scanner.py |
| 2 | Runner integration tests missing | Medium | runner.py |
| 3 | Integration test coverage missing | Medium | tests/ |
| 4 | Config-driven scanner loading | Low | runner.py |
| 5 | HTML reporting | Low | report.py |
| 6 | Auto-fix capabilities | Low | scanner.py |
| 7 | CI/CD integration | Low | .github/ |

---

## 13. Extension Points

### 13.1 Adding New Scanners

1. Create `reconciliation/scan/new_scanner.py`
2. Implement `ScannerBase` ABC
3. Add to `reconciliation/scan/__init__.py`
4. Register in `runner.register_defaults()`

### 13.2 Adding New Rules

1. Add `Rule` to scanner's `rules` property
2. Implement validation logic in `scan()` method
3. Return `Finding` objects for violations

### 13.3 Adding New Checkers

1. Create checker class in `reconciliation/engine/checkers.py`
2. Add to `reconciliation/engine/__init__.py`
3. Use in `RuleEngine` for generic validation

### 13.4 Custom Report Formats

1. Extend `ReportGenerator` class
2. Add new report method
3. Integrate in `runner.save_report()`

---

## 14. Future Compatibility Notes

### 14.1 Backward Compatibility

- `scan_legacy()` method provided for backward compatibility
- `ScanScope` still supported via `ScanContext.scope`
- All scanner names remain unchanged

### 14.2 Forward Compatibility

- `ScanContext.config` dict allows future extensions
- `Finding.extra` dict allows additional metadata
- `Rule.params` dict allows rule-specific configuration

### 14.3 Migration Path

- Existing scanners remain functional
- New scanners must implement `ScannerBase`
- Reports maintain markdown format
- CLI entry point unchanged

### 14.4 Versioning

- Package version: 0.8.0 (from pyproject.toml)
- Architecture freeze: v1.0.0
- Baseline version: v1.0.0

---

**FREEZE STATUS:** This architecture is frozen as of 2026-07-15. No structural changes permitted without explicit unfreeze decision.

**NEXT PHASE:** Hardening (integration tests, CI/CD, performance optimization)

---

*Architecture documented by MUSCAL Reconciliation Engine.*
