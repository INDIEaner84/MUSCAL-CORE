# MUSCAL MASTER TRANSFER PACKAGE v1.0

**Version:** 1.0.0
**Erstellt:** 2026-07-14
**Status:** Authoritative Transfer Document

---

## 1. PROJECT IDENTITY

| Feld | Wert |
|------|------|
| Name | MUSCAL CORE (Multi-Step Cognitive Architecture Language) |
| Version | 0.8.0 |
| Python | >=3.12 |
| Repo | `/home/hz/AlitaProject/Codebase/MUSCAL CORE/` |
| Branch | `prototype-stable` |
| Phase | Prototype Stable |
| Status | READY WITH RISKS |

---

## 2. SYSTEM PURPOSE

MUSCAL CORE ist ein kognitives Betriebssystem — keine Bibliothek, kein Framework. Es orchestriert AI-Agents, fuehrt Tasks aus, kompiliert natuerliche Sprache in ausfuehrbare Plaene und ueberwacht sich selbst durch einen Observability-Stack.

**Kernfunktionen:**
- NL->Plan Compilation (MKC Compiler)
- Tool-Matching (Bridge, 9 Regex-Matcher)
- Deterministische Ausfuehrung (MEL)
- Plugin-System (Hook-basiert, `features/`)
- Observability (EventBus, Replay, DebugEngine)

---

## 3. ARCHITECTURE

### 3.1 7-Schichten-Architektur

```
L7 FRONTEND      React JSX (Dashboard, GraphView)
L6 API LAYER     Flask API (:5050), FastAPI (:8080)
L5 OS LAYER      BootManager, EventBus, Deployment-Modi
L4 COMPILER      MKC (MCXF), Bridge (Tool-Match), Optimizer, Feedback
L3 EXECUTION     MEL (Tool-Dispatch), Browser Engine, Desktop Tools
L2 KERNEL        WriterThread (CQRS), Scheduler, Gate, Governance, RAG
L1 STORAGE       SQLite (WAL, 5 Tabellen), JSONL, ChromaDB
```

### 3.2 Pipeline Data Flow

```
Input -> RAG -> MKC -> Bridge -> Optimizer -> MEL -> Feedback -> Memory -> Output
```

### 3.3 5 Kernel Perspectives

| Kernel | Layers | Responsibility |
|--------|--------|---------------|
| Observability | L7+L6+L5 | Monitoring, metrics, UI, replay |
| Control | L5+L2 | Decisions, limits, consensus, strategy |
| Cognitive | L4 | NL->Plan compilation, optimization |
| Runtime | L3+L2 | Execution, process isolation, safety |
| Storage | L1 | Persistence, indices, state recovery |

### 3.4 Immutability Contract

**Core is IMMUTABLE.** Dateien die NICHT veraendert werden duerfen:

- `kernel.py`, `mkc.py`, `bridge.py`, `memory.py`, `mel.py`, `schema.py`, `mkc_rules.py`
- `config.py`, `event_bus.py`, `graph.py`, `feedback.py`, `muscal_os.py`
- `main.py`, `main_boot.py`, `boot_manager.py`, `os_config.py`, `sphere.py`
- `debugger.py`, `tools.py`, `rag.py`, `trace_engine.py`, `plugin_registry.py`, `plugin_loader.py`
- `runtime/kernel/*`, `runtime/llm/*`, `runtime/optimizer/*`, `runtime/api/*`, `runtime/services/*`

**Regel:** Alle neuen Features gehen in `features/` als Plugin.

### 3.5 Kernel Principles

| Prinzip | Beschreibung |
|---------|-------------|
| Determinismus | L1-Routing ist regelbasiert, kein LLM, <1us |
| Single Writer | Nur ein Thread schreibt in die DB (CQRS) |
| Safety First | Jeder LLM-Input wird auf Injection geprueft |
| Layer-Trennung | Jede Schicht hat genau eine Verantwortung |
| Replayability | Jeder Task ist deterministisch wiederholbar |
| Bounded Growth | Graph (5000 Nodes), Memory (10000), Events (50000) |

---

## 4. MODULE INVENTORY

### 4.1 Kernel Modules (IMMUTABLE)

| Datei | Klasse/Funktion | Verantwortung |
|-------|-----------------|---------------|
| `kernel.py` | `MuscalKernel` | Hauptorchestrator |
| `mkc.py` | `mkc()` | NL->MCXF Compiler |
| `mkc_rules.py` | `SIGNAL_RULES` | Regelbasierte Klassifikation |
| `bridge.py` | Tool-Matching | 9 Regex-Matcher |
| `mel.py` | `SystemAgentRuntime` | Tool-Dispatch |
| `memory.py` | SQLite + JSONL | Persistenz (MAX 10000) |
| `graph.py` | GraphState | Event-Driven Graph (MAX 5000 Nodes) |
| `feedback.py` | Feedback | Confidence Adjustments |
| `event_bus.py` | EventBus | Event-System (MAX 50000) |
| `schema.py` | Schema | Datenformat-Definitionen |
| `config.py` | Config | Lazy Session-Config |
| `sphere.py` | SphereState | Radiale UI-Projektion |

### 4.2 Runtime Modules

| Pfad | Verantwortung |
|------|---------------|
| `runtime/kernel/` | Kernel Runtime Layer |
| `runtime/llm/` | LLM Integration |
| `runtime/optimizer/` | DCE -> Fusion -> Parallel |
| `runtime/api/` | API Runtime |
| `runtime/services/` | Service Layer |

### 4.3 Reconciliation Engine

| Datei | Klasse | Verantwortung |
|-------|--------|---------------|
| `reconciliation/core/finding.py` | `Finding`, `FindingSet`, `Category`, `Severity` | Datenmodell |
| `reconciliation/core/context.py` | `ScanContext` | Scan-Kontext (frozen dataclass) |
| `reconciliation/core/rule.py` | `Rule`, `RuleSet` | Regeldefinition |
| `reconciliation/core/scope.py` | `ScanScope` | Scan-Bereich |
| `reconciliation/scanner.py` | `ScannerBase` (ABC) | Abstract Scanner Interface |
| `reconciliation/runner.py` | `ReconciliationRunner` | Orchestrierung |
| `reconciliation/report.py` | `ReportGenerator` | MD-Report-Formatierung |
| `reconciliation/engine/rule_engine.py` | `RuleEngine` | Generic Rule Checker |
| `reconciliation/engine/checkers.py` | `FileExistsChecker`, `ContentMatchChecker`, `FileCountChecker` | Checker-Implementierungen |
| `reconciliation/snapshot/repository_snapshot.py` | `RepositorySnapshot` | Immutable Snapshot Builder |
| `reconciliation/snapshot/file_node.py` | `FileNode` | Datei-Metadaten |
| `reconciliation/snapshot/hash_cache.py` | `HashCache` | Lazy SHA-256 mit mtime-Invalidation |
| `reconciliation/snapshot/tree.py` | `DirectoryTree`, `TreeNode` | Verzeichnisbaum mit glob/filter/traverse |

### 4.4 Scanners

| Datei | Klasse | Rules | Status |
|-------|--------|-------|--------|
| `reconciliation/scan/link_scanner.py` | `BrokenLinkScanner` | LINK-001 | Fertig |
| `reconciliation/scan/adr_scanner.py` | `AdrValidatorScanner` | ADR-CR01-09 | Fertig |
| `reconciliation/scan/import_scanner.py` | `ImportValidatorScanner` | IMP-IR01-04 | Fertig |
| `reconciliation/scan/drift_scanner.py` | `DriftDetectorScanner` | SDR-IR01-04 | Fertig |
| `reconciliation/scan/rfc_scanner.py` | `RfcValidatorScanner` | RFC-001-03 | FEHLT |

### 4.5 Feature Plugins

| Pfad | Zweck |
|------|-------|
| `features/event_sourcing/` | Event Persistence + Replay |
| `features/` (sonstige) | Plugin-Sandbox |

### 4.6 Guards

| Datei | Zweck |
|-------|-------|
| `guards/install_hook.sh` | Pre-commit Hook Installation |
| `guards/pre-commit` | Pre-commit Skript |

### 4.7 Scripts

| Datei | Zweck |
|-------|-------|
| `scripts/build_scanner_report.py` | Scanner-Report Builder |
| `scripts/checkpoint_summary.py` | Checkpoint Status Summarizer |
| `scripts/config_snapshot.py` | Config Snapshot |
| `scripts/registry.py` | Script Registry |

---

## 5. RESOURCE LIMITS

| Ressource | Max | Datei | Eviction |
|-----------|-----|-------|----------|
| Graph Nodes | 5000 | `graph.py` | FIFO (Timestamp) |
| Graph Edges | 10000 | `graph.py` | FIFO |
| Memory DB | 10000 Zeilen | `memory.py` | ORDER BY id DESC |
| Event History | 50000 | `event_bus.py` | POP(0) |
| Graph Safety | 10000 Nodes | `kernel.py` | Auto-Prune |

---

## 6. CHECKPOINT HISTORY

| # | Checkpoint | Beschreibung | Status |
|---|-----------|--------------|--------|
| 0.1 | Kernel Design | MKC -> Bridge -> MEL Pipeline | Done |
| 0.2 | MKC Integrated | Regelbasierte Klassifikation | Done |
| 0.3 | Graph + Sphere | Event-Driven Runtime | Done |
| 0.4 | Plugin System | features/ + Plugin API | Done |
| 0.5 | Import Stability | Lazy Connections | Done |
| 0.6 | Graph + Memory Pruning | Bounded Growth | Done |
| 0.7 | Prototype READY | Stress Test 100 Iterations | Done |
| 0.8 | Architecture Evolution | Verification Layer Boundary | Done |
| 0.25 | Category A Fixes | 10/10 Auto-Fixes | Done |
| 0.26 | Reconciliation Foundation | Scanner Specs + Rules | Done |
| 0.27 | Category B Reconciliation | Import Guards | Done |
| 0.28 | Repository Cleanup | RestrictedPython + Deprecations | Done |
| 0.29.1 | Reconciliation Runtime Kernel | Core Data Model + ABCs | Done |
| 0.29.2 | Repository Snapshot Layer | Snapshot + FileNode + HashCache | Done |
| 0.30 | ScanContext Migration | v2 Context + Snapshot Integration | Done |
| 0.31 | Rule Engine | Generic Checkers | Done |
| 0.32 | BrokenLinkScanner | Markdown Link Validation | Done |
| 0.33 | AdrValidatorScanner | 9 ADR-CR Rules | Done |
| 0.34 | ImportValidatorScanner | 4 IMP-IR Rules, 129 Findings | Done |
| 0.35 | DriftDetectorScanner | 4 SDR-IR Rules, 3 Findings | Done |
| 0.36 | RfcValidatorScanner | RFC-001-03 Rules | MISSING |

---

## 7. ADR SUMMARY

| ADR | Titel | Status |
|-----|-------|--------|
| ADR-001 | Kernel Runtime — Single Pipeline Authority | APPLIED |
| ADR-002 | Memory — GraphMemory als Standard-Interface | ACCEPTED |
| ADR-003 | Event System — EventBus als Standard | APPLIED |
| ADR-004 | Plugin System — Hook-Based Extensions | ACCEPTED |
| ADR-005 | Pipeline Architecture — Monolithic Data Flow | ACCEPTED |
| ADR-006 | Graph/Sphere — Event-Driven Execution Graph | ACCEPTED |
| ADR-007 | Core Immutability — Write Guard Policy | ACCEPTED |
| ADR-008 | Deployment Runtime — Supervisor Container Model | ACCEPTED |
| ADR-009 | Observability Foundation | ACCEPTED |
| ADR-010 | SQLite Consolidation — Unified Single Database | APPLIED |
| ADR-011 | Verification Layer Architecture | ACCEPTED |
| ADR-012 | Event Persistence — Audit Log + Replay | APPLIED |

---

## 8. RECONCILIATION ENGINE STATUS

### 8.1 Implemented Components

| Component | Status | Tests | Findings |
|-----------|--------|-------|----------|
| Snapshot Layer | Done | 3/3 | — |
| ScanContext v2 | Done | Yes | — |
| BaseScanner ABC | Done | Yes | — |
| RuleEngine | Done | Yes | — |
| Findings/Report | Done | Yes | — |
| Runner | Done | No dedicated test | — |
| BrokenLinkScanner | Done | Yes | 1 |
| AdrValidatorScanner | Done | Yes | 4 |
| ImportValidatorScanner | Done | Yes | 129 |
| DriftDetectorScanner | Done | Yes | 3 |
| RfcValidatorScanner | **MISSING** | — | — |

### 8.2 Scan Findings Summary

| Scanner | Findings | Kategorie |
|---------|----------|-----------|
| BrokenLinkScanner | 1 | Broken Markdown Link |
| AdrValidatorScanner | 4 | Missing ADR/RFC Files |
| ImportValidatorScanner | 129 | 128 Unused Imports + 1 Formatting |
| DriftDetectorScanner | 3 | Pipeline Order + Layer/Table Count |
| **Total** | **137** | |

### 8.3 Test Coverage

| Metrik | Wert |
|--------|------|
| Test-Dateien (gesamt) | 56 |
| Test-Dateien (reconciliation) | 0 |
| Test-Dateien (tests/) | 56 |
| Pytest | Ja |

---

## 9. TECHNICAL DEBT

| # | Item | Severity | ADR |
|---|------|----------|-----|
| 1 | RfcValidatorScanner fehlt | High | — |
| 2 | 128 unused-import findings (import_scanner) | Medium | — |
| 3 | Runner.py untested | Medium | — |
| 4 | Plugin-System nur Hook-basiert | Medium | ADR-004 |
| 5 | SIGNAL_RULES Confidence-Drift ohne Auto-Reset | Medium | — |
| 6 | FIFO-Eviction ohne semantische Bewertung | Low | — |
| 7 | DB-Migration via scripts/migrate_sqlite.py | Low | ADR-010 |
| 8 | CI/CD via .github/workflows/test.yml | Low | ADR-008 |

---

## 10. DEVELOPMENT CONVENTIONS

### 10.1 Code Style

- Python 3.12+
- Ruff: `line-length = 100`, `target-version = "py312"`
- Lint Rules: `["E", "F", "W", "I"]`
- MyPy: `ignore_missing_imports = true`
- Type Hints: Meistens vorhanden, nicht 100%

### 10.2 File Conventions

- Scanners erben von `ScannerBase` (ABC)
- Scanners implementieren `scan(context: ScanContext) -> FindingSet`
- Scanners expoertieren `name` und `rules` Properties
- Findings verwenden `Finding` dataclass mit `finding_id`, `scanner`, `file`, `severity`, `category`

### 10.3 Git Conventions

- Commits: `"MUSCAL: <Description>"`
- Branch: `prototype-stable`
- Pre-commit Hook: `guards/pre-commit`

### 10.4 Testing

- Framework: pytest
- Mocking: `unittest.mock`
- Fixtures: `conftest.py`
- Temp-Dirs: `tmp_path`

---

## 11. DOCUMENTATION MAP

| Dokument | Pfad | Zweck |
|----------|------|-------|
| TECHNICAL BASELINE | `docs/TECHNICAL_BASELINE.md` | Verbindliche Architektur |
| ARCHITECTURE.md | `docs/ARCHITECTURE.md` | Uebersicht + Layering |
| PROJECT_STATE.md | `docs/PROJECT_STATE.md` | Aktueller Projektzustand |
| PROJECT_CHECKPOINTS.md | `docs/PROJECT_CHECKPOINTS.md` | Milestone-Protokoll |
| ADRs | `spec/ADR-*.md` | Architecture Decision Records |
| IMMUTABILITY CONTRACT | `spec/IMMUTABILITY_CONTRACT.md` | Core/Feature-Grenzen |
| PLUGIN_API.md | `spec/PLUGIN_API.md` | Plugin SDK |
| MASTER TRANSFER PACKAGE | `docs/MUSCAL_MASTER_TRANSFER_PACKAGE_v1.0.md` | Dieses Dokument |

---

## 12. RFC INVENTORY

RFC-Dateien in `archive/history/rfcs/`:

| RFC | Datei |
|-----|-------|
| MAS-0000 | `archive/history/rfcs/MAS-0000.md` |
| MAS-0001 | `archive/history/rfcs/MAS-0001.md` |
| MAS-0002 | `archive/history/rfcs/MAS-0002.md` |
| MAS-0003 | `archive/history/rfcs/MAS-0003.md` |
| MAS-0004 | `archive/history/rfcs/MAS-0004.md` |
| MAS-0005 | `archive/history/rfcs/MAS-0005.md` |
| MAS-0006 | `archive/history/rfcs/MAS-0006.md` |
| MAS-0007 | `archive/history/rfcs/MAS-0007.md` |
| MAS-0008 | `archive/history/rfcs/MAS-0008.md` |
| MAS-0009 | `archive/history/rfcs/MAS-0009.md` |
| MAS-0010 | `archive/history/rfcs/MAS-0010.md` |
| MAS-0011 | `archive/history/rfcs/MAS-0011.md` |
| MAS-0012 | `archive/history/rfcs/MAS-0012.md` |
| MAS-0100 | `archive/history/rfcs/MAS-0100.md` |
| MAS-0300 | `archive/history/rfcs/MAS-0300.md` |
| MAS-0301 | `archive/history/rfcs/MAS-0301.md` |
| MAS-0400 | `archive/history/rfcs/MAS-0400.md` |
| MAS-0500 | `archive/history/rfcs/MAS-0500.md` |

---

## 13. QUICK REFERENCE

### Scanners ausfuehren

```python
from reconciliation.scan import BrokenLinkScanner, AdrValidatorScanner, ImportValidatorScanner, DriftDetectorScanner
from reconciliation.snapshot import RepositorySnapshot
from reconciliation.core.context import ScanContext

snapshot = RepositorySnapshot(".")
snapshot.build()

scanner = BrokenLinkScanner()
result = scanner.scan(ScanContext(snapshot=snapshot))
print(result.count)
```

### RuleEngine ausfuehren

```python
from reconciliation.engine import RuleEngine

engine = RuleEngine(rules=[...])
engine.evaluate(snapshot)
```

### Reports generieren

```bash
python scripts/build_scanner_report.py
```

---

## 14. NEXT STEPS

| Priority | Item | Effort |
|----------|------|--------|
| P0 | RfcValidatorScanner implementieren (Checkpoint 0.36) | 1 day |
| P1 | test_runner.py schreiben | 0.5 day |
| P2 | 129 import_findings triagieren | 1 day |
| P3 | GitHub Actions CI + pytest config | 0.5 day |
| P4 | Integration Test (End-to-End) | 1 day |

---

**END OF TRANSFER PACKAGE**
