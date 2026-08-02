# ADR-011: Verification Layer Architecture

**Status:** ACCEPTED  
**Date:** 2026-07-11  
**Author:** ARCHITECTURE RECONCILIATION

---

## Context

MUSCAL Band III (Verifikationsframework) definiert eine Architektur aus:

- Event Sourcing (immutable, append-only Events)
- Hash Chains (kryptografische Verkettung)
- Replay Engine (State-Rekonstruktion aus Events)
- Verification Layer (Proof-Generierung)

Die Analyse des Frameworks gegenüber der aktuellen Implementierung
(11.07.2026) hat gezeigt:

| Konflikt | Status |
|---|---|
| Core Immutability | 39 Dateien geschützt, keine direkten Änderungen |
| Event Sourcing | Kernel-Events flüchtig (In-Memory) |
| State Reconstruction | Nur Print-Only-Replay |
| Hash Verification | Nur im Optimizer (DAG), nicht im Kernel |
| Proof Generation | Existiert nicht |

Eine direkte Integration würde mindestens kernel.py, memory.py, graph.py
fundamental umbauen — und damit die Core-Immutability-Policy verletzen.

---

## Decision

**Das Verification Framework wird NICHT in Core-Dateien implementiert.**

Stattdessen wächst der Verification Layer als Plugin-Schicht über dem Core:

```
features/event_sourcing/   ← alle Verification-Komponenten
```

### Implementierungsprinzipien

| Prinzip | Regel |
|---|---|
| **Plugin-Only** | Keine Änderung an kernel.py, memory.py, graph.py etc. |
| **Hook-basiert** | Anbindung über 14 bestehende Hook-Punkte |
| **Inkrementell** | Vier Phasen: 0 Konsolidierung → 1 Events → 2 Hash → 3 Replay → 4 Proof |
| **Read-Only Start** | Phase 1-2: nur beobachten und protokollieren |
| **Replay später** | Phase 3-4: erst wenn Event-Log stabil ist |

---

## Phases

### Phase 0: Konsolidierung
- kernel.py + muscal_loop.py auf eine Pipeline-Autorität bringen
- In `features/consolidation/` als Bridge

### Phase 1: Event Sourcing Layer
- Eigene SQLite-Tabelle `kernel_events` (append-only)
- Plugin logged jeden Pipeline-Step als Event mit Hash
- Keine Verhaltensänderung

### Phase 2: Hash Chains & Verification
- SHA-256 basierte Hash-Kette
- Pipeline-Run-Verifikation gegen gespeicherte Hashes
- Core-File-Hash-Store (ADR-007 Phase 2)

### Phase 3: Replay Engine
- State-Rekonstruktion aus Event-Log
- Hash-Vergleich: Original vs. Rekonstruiert

### Phase 4: Verification & Proof
- Proof-Generierung pro Pipeline-Run
- CLI-Tool zur Verifikation
- MREIL-Integration (Verification-Kosten)

---

## Migration Plan

| Schritt | Abhängigkeit | Dauer |
|---|---|---|
| Phase 0: Konsolidierung | — | ~2-3 Tage |
| Phase 1: Event Sourcing | Phase 0 | ~3-4 Tage |
| Phase 2: Hash Chains | Phase 1 | ~2-3 Tage |
| Phase 3: Replay Engine | Phase 2 | ~3-4 Tage |
| Phase 4: Proof | Phase 3 | ~2-3 Tage |

---

## Consequences

### Positive
- Core bleibt stabil und immutable
- Plugin-Rollback jederzeit möglich
- Inkrementelle Einführung reduziert Risiko
- Bestehende Tests bleiben unverändert

### Negative
- Phase 1 Event Sourcing kann Kernel-Events NICCHT nachträglich erfassen
- Replay Engine muss auf Hook-basierter Rekonstruktion aufbauen
- Keine native Event-Persistenz im Kernel (nur Plugin-Ebene)
- Phase 0 Konsolidierung ist Voraussetzung — ohne sie keine saubere Event-Kette

### Neutral
- Eventuell später Core-Integration nach Stabilisierung möglich (neues ADR nötig)

---

## Compliance Check

- [ ] Phase 0: kernel.py + muscal_loop.py konsolidiert
- [ ] Phase 1: Event Store appended-only, keine Core-Änderungen
- [ ] Phase 2: Hash-Ketten verifizierbar, Manipulation erkennbar
- [ ] Phase 3: Replay erzeugt identischen State
- [ ] Phase 4: Proof-Generierung pro Run
- [ ] Alle 32+ Tests passieren nach jeder Phase
- [ ] Write Guard schützt weiterhin 39 Core-Dateien
