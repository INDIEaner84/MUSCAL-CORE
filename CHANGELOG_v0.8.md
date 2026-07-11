# Changelog

## [0.8.0] — 2026-07-11

### Added
- **253 Tests, 0 Failures**: Vollständige Test-Suite mit pytest (Unit, Integration, Security, System, Stress, Benchmark)
- **Script-to-Pytest Migration**: Alle 28 Legacy-Skripte in pytest-konforme Tests migriert
- **CI/CD auf volle Suite**: `.github/workflows/test.yml` läuft jetzt `pytest -m "not slow"` (statt 7 Dateien)
- **Graph Manager Plugin**: `features/runtime/graph_manager.py` — semantischer Graph-Prune (Connectivity + Recency) mit SOFT_LIMIT=500, HARD_LIMIT=3000
- **Confidence Reset Plugin**: `features/runtime/confidence_reset.py` — automatischer SIGNAL_RULES-Reset alle 10 Runs bei Über-Drift
- **Versionierte DB-Migrationen**: `scripts/migrate_sqlite.py` mit `@_migration`-Decorator und `schema_version`-Tracking
- **Benchmark-Tests**: `tests/test_benchmark.py` — Kernel-Laufzeit + Plugin-Load-Performance
- **Makefile**: `make test`, `make lint`, `make coverage`, `make install`, `make clean`
- **CONTRIBUTING.md**: Beitragsrichtlinie mit Quick-Start, Code-Style und Plugin-Contract
- **Release-Workflow**: `.github/workflows/release.yml` — automatisierte Release-Erstellung mit Artefakten
- **pyproject.toml**: `[tool.setuptools.packages.find]` für reproduzierbare Installation

### Changed
- **Containerfile**: Python 3.11 → 3.12 (Version angleichen an restliches Projekt)
- **pyproject.toml Dependencies**: `flasgger`, `slowapi`, `flask-limiter` zu core deps hinzugefügt
- **api_server.py**: Broken Imports (`graph_store`, `meta_reasoning_kernel`) durch try/except-guards ersetzt
- **tests/helpers.py**: `reset_plugins()` baut `HOOKS` jetzt aus Basis-Dict neu auf (statt `clear()`)
- **tests/system/**: Autouse-Fixtures rebuilden `HOOKS` mit allen 14 Hook-Keys
- **Audit Plugin**: `audit_plugin.py` skippt nicht-list `HOOKS`-Einträge (verhindert Plugin-Load-Crash)

### Fixed
- **C1 — Graph Growth Drift**: Semantischer Prune via Plugin (vorher nur FIFO bei 5000 Nodes)
- **C6 — Memory/Confidence Drift**: Auto-Reset alle 10 Runs via Plugin (vorher nie zurückgesetzt)
- **C7 — DB Migration**: Versionierte Migrations-Engine (vorher nur `CREATE TABLE IF NOT EXISTS`)
- **C8 — FIFO Prune**: Importance-Scoring statt reiner Timestamp-Sortierung
- **C3 — Dead Stubs**: `event_node.py`, `vector_memory.py` archiviert (keine aktiven Imports)
- **HOOKS-Wiederverwendung**: Alle `setup_function`/Fixtures rebuilden `HOOKS` aus konstantem Dict (behob 30 Test-Failures)
- **Zirkuläre Test-Imports**: Entfernt durch Migration auf pytest-Framework

### Security
- **10 registrierte Plugins** (vorher 8) — graph_manager + confidence_reset laufen innerhalb der Plugin-Sandbox
- **CI Security-Job**: `pip-audit` bleibt aktiv, Governance-Checks laufen unverändert
- **Keine neuen Forbidden-Patterns**: Neue Plugins verwenden nur erlaubte Imports

### Removed
- Leere Test-Subdirs: `tests/api/`, `tests/memory/`, `tests/reference/` (nur `__init__.py`)
- Dead Stubs: `compiler_updater.py`, `compiler_validator.py`, `compiler_state.py` (bereits in 23.27 gelöscht)
- `RestrictedPython` aus `requirements.txt` (ersetzt durch `validate_plugin()`-Static-Scan)

### Technical Debt (v0.8 bekannt, nicht adressiert)
- ~41 Placeholder-Stubs (<20 Zeilen) in Performance, Consensus, Coordination, Vision
- Graph wächst pro Run +9 Nodes (gedrosselt durch Plugin-Prune)
- Keine LLM-basierten Integrationstests (alle Tests mock-frei auf regex/rule-Basis)
- Coverage bei 41% (viele Module ungetestet: supervisor.py, scheduler.py, runtime-APIs)
- `api_server.py` teilweise guarded (graph_store, meta_reasoning_kernel existieren nicht aktiv)
- Keine DB-Migrationsgeschichte (Schema-Brüche möglich bei Format-Änderungen)
- Kein automatisiertes Performance-Regression-Tracking
- `kernel_core.py` FROZEN, Removal geplant 2026-08-08

---

**Vorherige Version:** [0.7.0] — 2026-07-06
**Nächste geplant:** v0.9 (Feature-Arbeit: Stubs auffüllen, Coverage erhöhen)
