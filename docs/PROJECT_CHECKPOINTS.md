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
