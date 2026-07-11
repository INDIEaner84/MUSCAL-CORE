# Changelog

## [0.7.0] — 2026-07-06

### Added
- **Graph Bounding**: `MAX_NODES=5000`, `MAX_EDGES=10000` in `graph.py` mit FIFO-Prune
- **Memory Bounding**: `MAX_MEMORY_ENTRIES=10000` in `memory.py` mit `_prune_memory()`-Hook
- **Event History Limit**: `_max_history=50000` in `event_bus.py` mit POP(0)-Eviction
- **Kernel Safety Guard**: Auto-Prune in `kernel.run()` bei >10000 Graph-Nodes
- **Reset State**: `reset_state()` + `DEFAULT_KEYWORDS` in `mkc_rules.py`
- **Safe Entrypoint**: `os.makedirs("storage")` + `if __name__ == "__main__"` in `main.py`
- **requirements.txt**: Vollständige Dependency-Liste (11 Pakete)
- **Stress Test Suite**: `tests/stress_test.py` (100 Iterationen, deterministische Verifikation)
- **Technische Dokumentation v0.7**: `TECHNICAL_MANUAL_v0.7.md`
- **Betriebsanleitung v0.2**: `MUSCALOS_v0.2.md`
- **Changelog**: `CHANGELOG_v0.7.md`

### Changed
- **memory.py**: `sqlite3.connect()` → lazy `_get_conn()` (kein module-level DB-Zugriff)
- **mel.py**: `SystemAgentRuntime()` → lazy `_get_runtime()` (kein module-level Runtime)
- **config.py**: `SESSION_ID` → lazy `get_session_id()` (kein module-level Timestamp)
- **Dockerfile**: `requirements_api.txt` → `requirements.txt`, `mkdir -p /app/storage`
- **graph.py**: `add_node()` und `add_edge()` rufen jetzt `prune_graph()` auf

### Fixed
- **Import Chain**: memory/mel/config brechen nicht mehr bei blossem `from`-Import
- **Storage Ordner**: Wird automatisch angelegt, kein manuelles `mkdir` nötig
- **Unbegrenztes Graph-Wachstum**: Hard-Limit verhindert OOM bei Dauerlauf
- **Unbegrenztes Speicher-Wachstum**: SQLite-Tabellen werden auf 10k Zeilen begrenzt
- **Event-History-Überlauf**: EventBus wächst nicht mehr unbegrenzt im Speicher

### Removed
- `requirements_api.txt` (ersetzt durch `requirements.txt`)

### Security
- **Letzter Stand v0.6 vor Stabilisierung**: System wies 6 kritische Import-Fehler auf (Score 43/100)
- **Nach v0.7**: Import Chain stabil, Speicher gebounded, Stresstest bestanden
- **Verbleibende Risiken**: SIGNAL_RULES Drift, FIFO-Prune ohne Semantik, keine Tests, ~45% Stubs

### Technical Debt (v0.7 bekannt, nicht adressiert)
- 0 echte Tests (nur 1 Stresstest-Skript)
- ~80 Stub-Dateien (<20 Zeilen) in Consensus, Distributed, Evolution
- Keine DB-Migrationen
- Keine CI/CD
- SIGNAL_RULES Confidence-Drift ohne Auto-Reset
- FIFO-Eviction ohne semantische Bewertung

---

**Vorherige Version:** v0.6 (nicht versioniert, Pre-Stabilisierung)
**Nächste geplant:** v0.8 (Feature-Arbeit)
