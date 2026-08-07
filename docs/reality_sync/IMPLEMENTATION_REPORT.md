# RSL — Implementierungsbericht

> Siehe auch: `REALITY_SYNC_ARCHITECTURE.md`, `VALIDATION_REPORT.md`,
> `RSL_COMPLETE.md`.

## 1. Umfang & Eckpunkte

- **Neues Feature**: `features/reality_sync/` (Plugin-konform, keine
  Core-Änderungen).
- **Vorgabe:** Reines Design; Proposal statt Auto-Write.
- **Test-HTML:** `tests/features/reality_sync/test_reality_sync`, 11 Tests.

## 2. Umgesetzte Komponenten

| Modul | Zweck |
|-------|-------|
| `models/drift.py` | `RiskLevel`, `DriftDifference`, `DriftReport` |
| `models/evidence.py` | `ChangeEvidence` (mit `is_complete()`) |
| `models/proposal.py` | `UpdateProposal` (Vorschlag) |
| `validators/consistency.py` | Pflicht-Sektionen-Prüfung |
| `drift_detector.py` | Struktur-Vergleich → `DriftReport` |
| `risk_classifier.py` | LOW/MEDIUM/HIGH-Klassifikation |
| `proposal_engine.py` | Proposal-Erstellung (pure) |
| `evaluator.py` | `RealitySynchronizer`-Orchestrierung |
| `__init__.py` | Public API |

## 3. Kernel-Konformität

- `guards.write_guard.validate_write()` für jede neue Datei **grün**.
- `AGENTS.md`-Regel „ALL EXTENSIONS GO TO /features/" eingehalten.
- Keine Änderungen an Core/`runtime/`-Dateien (git diff zeigt nur neue Dateien).

## 4. Implementierungsentscheidungen

- `DriftReport.has_drift` ist bool (statt nur differences-Länge);
  `recommended_action` bündelt `no_sync/auto_sync/review/require_approval`.
- RiskClassifier verwendet Keypath-Substrings (vorwärtskompatibel, keine
  festen Ontologie-Namen).
- `RealitySynchronizer` nimmt optional einen `event_store` und rekonstruiert
  den Runtime-State mit der bestehenden State-API — kein neuer Persistenz-Weg.

## 5. Absicherung höchster Vorgaben

- Kein Write auf EventStore (kein `append`/`write`-Aufruf im Package).
- `approval_required` wird nur vom RiskLevel abgeleitet (HIGH→True).
- `ChangeEvidence` erfüllt die geforderten Zusatzfelder (Quelle, Zeit,
  Event-Ref, Hash, Vergleichsergebnis).