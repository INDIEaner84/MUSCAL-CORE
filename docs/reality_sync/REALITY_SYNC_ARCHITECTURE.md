# RSL — Reality Synchronization Layer (Architektur)

> Dokument: `docs/reality_sync/REALITY_SYNC_ARCHITECTURE.md`
> Planung/Status: Siehe `IMPLEMENTATION_ANALYSIS.md`, `IMPLEMENTATION_REPORT.md`,
> `VALIDATION_REPORT.md`, `RSL_COMPLETE.md`.

## 1. Ziel

Kontrollierte Verbindung zwischen **Runtime Events** (EventStore),
**State Reconstruction**, **Reality Evaluation** und **Canonical Update
Proposal** — ohne dass die Runtime-Reality ungeprüft die Canonical-Reality
überschreibt.

```text
Runtime Events (EventStore)
      │
      ▼
State Reconstruction            features/events/state_model.py
      │                         (ReconstructedState.to_dict)
      ▼
Reality Evaluation              features/reality_sync/DriftDetector
      │                         → DriftReport (diff + RiskLevel)
      ▼
Canonical Update Proposal       features/reality_sync/ProposalEngine
                                 → UpdateProposal (kein Auto-Write!)
```

## 2. Konstanten / Unverletzlich

- EventStore (= Single Source of Events, *stored_events*) bleibt IMMUTABLE.
- `features/reality_sync` schreibt niemals auf den EventStore.
- Proposal-Erstellung ist rein (pure); kein Seiteneffekt.
- RiskLevel-Klassifikation implementiert die angegebenen Regeln:

  | Risiko | Bedingung (Keypath-Muster) | Proposal-Behandlung |
  |--------|----------------------------|---------------------|
  | LOW    | Metriken, Statistik        | auto |
  | MEDIUM | Dokument-/Feature-Status   | review |
  | HIGH   | Architektur/Security/Datenmodell | approval erforderlich |

- Evidence-Objekt verlangt: Quelle, Timestamp, Event-Referenz, Hash und
  Vergleichsergebnis. `ChangeEvidence.is_complete()` prüft dies.

## 3. Komponenten

### 3.1 `features/reality_sync/models/`
- `drift.py`: `RiskLevel`, `DriftDifference` (keypfad, Runtime/Cannonical,
  change_type), `DriftReport`.
- `evidence.py`: `ChangeEvidence` inkl. `is_complete()`.
- `proposal.py`: `UpdateProposal` (Vorschlag; `approval_required`).

### 3.2 `features/reality_sync/validators/consistency.py`
- `ConsistencyValidator.validate()` erzwingt die für eine Realität nötigen
  Sektionen (`entities`, `graph_nodes`, `active_tasks`, `agents`).

### 3.3 `features/reality_sync/drift_detector.py`
- `DriftDetector.detect(runtime, canonical) → DriftReport`; reiner Vergleich
  der State-Dicts per Pfad.

### 3.4 `features/reality_sync/risk_classifier.py`
- `RiskClassifier.classify_keypath()` + Report-Aggregation (max).

### 3.5 `features/reality_sync/proposal_engine.py`
- `ProposalEngine.build(report, change_type, event_reference)` → `UpdateProposal`
  mit automatisch gesetztem `approval_required` bei HIGH.

### 3.6 `features/reality_sync/evaluator.py`
- `RealitySynchronizer`: Orchestrierung `DriftDetector` → `ProposalEngine`,
  plus optional `event_store` für die Rekonstruktion (bestehende State-API).

## 4. Integrationspunkte

- **EventStore v2** (`runtime/event_store.py`): nur lesend via `replay()`.
- **Knowledge / hypothesis** (`features/knowledge/`): Canonical-Daten.
- **EventHash** (`features/events/event_hash.py`): evtl. für Evidence stabil.
- **Replay** (`features/replay/replay_service.py`): optional wiederverwendbar,
  aktuell nicht Teil der Pipeline.

## 5. Risiken & Guardrails

| Risiko | Mitigation |
|--------|------------|
| Canonical-Write ohne Approvals | nur `UpdateProposal`-Erzeugung; kein auto-apply |
| Können Kern-schema-fehlen | `ConsistencyValidator` vor jedem Vergleich |
| Unkontrollierte Event-Replay | nur `replay()`-erlaubt, optional Limit |
| Idempotenz / Hash | Evidence beinhaltet Hash – Wiederwahrmöglichkeit |