# Reality Synchronization Layer (RSL) — Implementierungsanalyse

**Datum:** 2026-08-07
**Scope:** Read-only Analyse vor der Umsetzung. Kein Core-Code geändert.

---

## 1. Gefundene Komponenten

| Komponente | Pfad | Kern-API |
|-----------|------|----------|
| EventStore v2 | `runtime/event_store.py` | `EventStore` (SQLite `stored_events`, 23 Spalten), `append()`, `replay(cursor, topic, limit)`, `event_count()` |
| Event Producer + Observer | `features/events/` | `GraphObserverAdapter`, `default_producer_factory`, `observer_event_contract` (E1–E10), `event_hash` |
| Replay / Reconstruction | `features/replay/replay_service.py`, `features/events/state_model.py` | `ReplayService`, `ReconstructedState`, `reconstruct_state()`, `reconstruct_from_store()`, `validate_chain()` |
| Canonical Runtime | `features/runtime_canonical.py`, `features/identity/reality.py` | `init_canonical_runtime()`, `ExecutionMode/State/Verification` |
| Knowledge Layer | `features/knowledge/` | `KnowledgeCandidate`, `KnowledgeEntry`, `KnowledgeValidator`, `KnowledgeWriter`, `EvidenceLevel` |
| Decision Registry | `features/provenance/` | `write_decision()`, `MCPLStore` |
| ADRs | `spec/ADR-*.md` (migriert nach `knowledge/adr/`), insbesondere `ADR-EVENT-001` (`event_store.py` = Single Canonical Event Authority) |

**Grundregel der Codebase:** EventStore Schema ist CANONICAL und IMMUTABLE. Core-`kernel`, `mkc`, etc. sind read-only. Alle neuen Features landen in `features/`.

---

## 2. Integrationspunkte der RSL

```
Runtime Events (EventStore.replay)
        ↓
State Reconstruction (ReconstructedState / replay_service)
        ↓
Reality Evaluation (DriftDetector vs. Canonical State)
        ↓
Canonical Update Proposal (ProposalEngine — NICHT schreibend)
```

- **Quelle Runtime:** `EventStore.replay()` (passiv, kein Write).
- **Runtime-State:** `features/events/state_model.reconstruct_state()` liefert `ReconstructedState.to_dict()` / `summary()`.
- **Canonical-State:** wird als Vergleichsobjekt bereitgestellt (instanziierbar por Dic/Adapters; Canonical = Knowledge/Etablierter-Sicht). RSL vergleicht Schema-agnostisch.
- **Evidence:** nutzt `calculate_event_hash` (sha256, H2) für reproduzierbare `event_hash`-Felder.
- **Keine neuen Speicher:** Proposals sind flüchtige Datenobjekte; kein `EventStore.append()`, keine neuen Tabellen. (Optional: bestehende Decision-Registry via `features/provenance.write_decision()` — nur zum Loggen, nicht automatisch.)

---

## 3. Bestehende Canonical / Decision Struktur

- `featuregood/knowledge/models.py`: `KnowledgeCandidate`, `KnowledgeEntry` → Canonical-Dezined-Zustand (VALIDADED/REJECTED/SUPERSEDED).
- `features/identity/reality.py`: `ExecutionMode/ExecutionState/VerificationState` sind die Runtime-Reality-Bezugsziele.
- `feature/provenance/decision_writer.py`: `decisions`-Tabelle — Referenzpunkt für Proposal-Registrierung (optional, nicht berührt).

---

## 4. Risiken

| Risiko | Maßnahme |
|--------|----------|
| EventStore-Schema oder -Event unverändert | RSL nutzt NUR `replay()`; kein `append`; IMMUTABLE Check vor Tests |
| Drag-On von neuen Persistenzschichten | Keine neuen Tabellen; Proposals nur in-memory |
| Drift-Fehlklassifikation (Reality vs. Knowledge) | Klare Policy: Data-Mapping, RAID, geregelte Signaturen in `risk_classifier` |
| Laufzeitbeschleunigung/Kompat der bestehenden Test | Neue Tests eigenständig, `features/reality_sync/` isoliert; Bestandstests unangetastet |
| Schreibenkreislauf (MCP) | `proposal_engine` hat KEINEN Write-Pfad; `approval_required` steuert Sichtbarkeit |

---

## 5. Geplante Dateien

```
features/reality_sync/            (neues Plugin-Feature, kein Core-Change)
├── __init__.py
├── evaluator.py                  # RealitySynchronizer (BSes Orchestrierung)
├── drift_detector.py
├── risk_classifier.py
├── proposal_engine.py
├── models/
│   ├── __init__.py
│   ├── drift.py                  # DriftReport, DriftDifference (source, target)
│   ├── proposal.py               # UpdateProposal (nur Vorschlag)
│   └── evidence.py               # ChangeEvidence (source, timestamp, event, hash, ergebnis)
└── validators/
    ├── __init__.py
    └── consistency.py            # Invalid-State-Ablehnung
```

Tests: `features/reality_sync/tests/` (gemäß bestehender Verzeichnisstruktur `features/events/tests/`) — zusätzlich extrahierbar via `tests/features/reality_sync/`.

Doku:
```
members/  → features/reality_sync/docs/  ODER  docs/reality_sync/
   ├── IMPLEMENTATION_ANALYSIS.md   (diese Datei)
   ├── REALITY_SYNC_ARCHITECTURE.md
   ├── IMPLEMENTATION_REPORT.md
   ├── VALIDATION_REPORT.md
   └── RSL_COMPLETE.md
```

---

*Read-only. Keine Zuständigkeit geändert.*