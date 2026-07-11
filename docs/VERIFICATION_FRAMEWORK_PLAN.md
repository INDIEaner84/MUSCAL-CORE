# MUSCAL Verification Framework — Implementation Plan

Vier-Phasen-Plan zur plugin-basierten Einführung des Verification Frameworks.
Core-Dateien bleiben IMMUTABLE. Alle Erweiterungen in `features/event_sourcing/`.

---

## Übersicht

```
Phase 0: Konsolidierung           (kernel.py + muscal_loop.py)
Phase 1: Event Sourcing Layer     (Plugin: Persistenz & Immutability)
Phase 2: Hash Chains & Verify     (Plugin: Integrität)
Phase 3: Replay Engine            (Plugin: State-Rekonstruktion)
Phase 4: Verification & Proof     (Plugin: Beweis)
```

---

## Phase 0: Konsolidierung (Dauer: ~2-3 Tage)

**Ziel:** Eine einzige Pipeline-Autorität, bevor Event-Sourcing beginnt.

**Problem:** `kernel.py` und `muscal_loop.py` duplizieren große Teile der Pipeline.

**Vorgehen:**
1. Differenzanalyse kernel.py vs. muscal_loop.py
2. Gemeinsame Teile identifizieren (RAG, MKC, MCXF, Bridge, MEL, Feedback, Memory)
3. Unterschiede extrahieren (Loop hat StateStore, ReplayEngine, CognitiveDiffEngine)
4. `features/consolidation/kernel_loop_bridge.py` — Wrapper für beide Pipelines
5. Vergleichstest: Gleicher Input → gleicher Output in beiden Pipelines

**Risiko:** MITTEL
**Core-Änderungen:** Keine
**Tests:** Neu (Vergleichstest)

---

## Phase 1: Event Sourcing Layer (Dauer: ~3-4 Tage)

**Ziel:** Kernel-Pipeline-Events werden persistent, immutable, append-only gespeichert.

**Architektur:**
```
kernel.py → Hook → Event Persistence Plugin → SQLite Event Store → Immutable Log
```

**Schritte:**
1. `features/event_sourcing/__init__.py`
2. `features/event_sourcing/event_store.py`
   - Eigene SQLite-Tabelle: `kernel_events`
   - Felder: id, seq, type, payload, previous_hash, hash, timestamp, version
   - Nur INSERT (append-only), kein UPDATE/DELETE
   - SHA-256 über payload + previous_hash
3. `features/event_sourcing/event_persistence_plugin.py`
   - Plugin an 14 Hook-Punkten (kernel_before/after, mkc_before/after, ...)
   - Jeder Pipeline-Step → Event erzeugen → hashen → speichern
4. `features/event_sourcing/schemas.py`
   - KernelEvent, EventChain Dataclasses

**Risiko:** NIEDRIG (Plugin, kein Core-Zugriff)
**Core-Änderungen:** Keine
**Tests:** Event-Speicherung, Hash-Ketten-Konsistenz, Append-Only

---

## Phase 2: Hash Chains & Verification (Dauer: ~2-3 Tage)

**Ziel:** Jede Pipeline-Ausführung hat kryptografischen Integritätsnachweis.

**Schritte:**
1. `features/event_sourcing/hash_chain.py`
   - HashChain Klasse, compute_event_hash(), verify_chain()
2. `features/event_sourcing/verification.py`
   - verify_pipeline_run(run_id) → VerificationResult
   - Gespeicherter Hash vs. Neuberechnung
   - Chain-Integrität (Lücken, Verkettung)
3. `features/event_sourcing/core_hash_store.py`
   - SHA-256 von Core-Dateien speichern (ADR-007 Phase 2)
   - verify_core_integrity() → IntegrityReport

**Risiko:** NIEDRIG
**Core-Änderungen:** Keine
**Tests:** Deterministische Hash-Berechnung, Manipulationserkennung

---

## Phase 3: Replay Engine (Dauer: ~3-4 Tage)

**Ziel:** State kann aus Event-Historie rekonstruiert werden.

**Architektur:**
```
Event Store → Replay Engine → State Reconstruction → Hash Comparison
```

**Schritte:**
1. `features/event_sourcing/replay_engine.py`
   - ReplayEngine Klasse
   - replay(run_id) → rekonstruierter GraphState
2. `features/event_sourcing/state_reconstructor.py`
   - Mapping: Event-Typ → State-Transformation
   - MKC_STEP → graph.add_node(), etc.
3. `features/event_sourcing/replay_verifier.py`
   - verify_replay(run_id) → ReplayResult
   - Rekonstruierter Hash vs. Original-Hash

**Risiko:** MITTEL (State-Rekonstruktion ist fragil)
**Core-Änderungen:** Keine (rein Hook-basiert)
**Tests:** Identischer State, unabhängige Runs, fehlende Events

---

## Phase 4: Verification & Proof Generation (Dauer: ~2-3 Tage)

**Ziel:** Jede Pipeline-Ausführung kann formal verifiziert werden.

**Schritte:**
1. `features/event_sourcing/proof_generator.py`
   - ProofGenerator → generate_proof(run_id) → Proof
   - Input-Hash, Event-Chain-Hash, State-Hash, Runtime-Version, Kernel-Version
2. `features/event_sourcing/verification_pipeline.py`
   - VerificationPipeline → verify(run_id) → VerificationResult
   - Event-Chain → State-Rekonstruktion → Hash-Vergleich → Proof
3. `features/event_sourcing/__main__.py`
   - CLI-Tool: `python -m features.event_sourcing verify <run_id>`
4. `features/event_sourcing/mreil_bridge.py`
   - Verification-Kosten an MREIL melden

**Risiko:** NIEDRIG
**Core-Änderungen:** Keine
**Tests:** Proof für erfolgreiche/fehlgeschlagene Runs

---

## Dateistruktur nach Implementierung

```
features/event_sourcing/
├── __init__.py
├── __main__.py              ← CLI
├── schemas.py               ← Dataclasses
├── event_store.py           ← SQLite Event Store
├── event_persistence_plugin.py ← Hook-Integration
├── hash_chain.py            ← Hash-Berechnung & Kette
├── core_hash_store.py       ← Core-Dateien-Integrität
├── verification.py          ← Einzelne Verifikation
├── replay_engine.py         ← State-Rekonstruktion
├── state_reconstructor.py   ← Event → State Mapping
├── replay_verifier.py       ← Replay-Verifikation
├── proof_generator.py       ← Proof-Erzeugung
├── verification_pipeline.py ← Gesamtverifikation
└── mreil_bridge.py          ← MREIL-Integration
```

---

## Risikobewertung

| Phase | Risiko | Core-Änderung | Rollback |
|---|---|---|---|
| 0 Konsolidierung | MITTEL | Nein | Einfach |
| 1 Event Sourcing | NIEDRIG | Nein | Einfach |
| 2 Hash Chains | NIEDRIG | Nein | Einfach |
| 3 Replay Engine | MITTEL | Nein | Mittel |
| 4 Verification | NIEDRIG | Nein | Einfach |

---

## Architekturentscheidung

Siehe: `spec/ADR-011-verification.md`

---

*Plan: 2026-07-11*
*Status: ARCHITECTURE DECISION — no implementation until Phase 0-4 ready*
