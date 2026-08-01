# G7_01_RC1_DECISION_BRIEFS — P0-1 / P0-2 Human Decision Package

**Gate:** G7-01 · **Date:** 2026-08-01 · **Modus:** READ/WRITE (docs/audit/)
**Erweiterung von:** DECISION_CLOSURE_PACKAGE.md §RC-1 (Optionen A/B/C → A/B/C/D)
**Regel:** Neutrale Entscheidungsgrundlage — **keine Empfehlung wird erzwungen**; jede Option ist für den Entscheider gleichberechtigt dargestellt.
**Entscheider:** ARB / Human (Project Governance) — nicht dieser Agent.

---

## P0-1 — Graph-OS-State Rekonstruktion (Human Decision Brief)

### Problemdefinition
GraphState/SphereState sind rein in-memory; nach Restart nicht rekonstruierbar.
MC-TC-007 Phase H: ❌ FAIL. Graph-Events WERDEN in `stored_events` persistiert,
aber es existiert **kein Rücklese-/Rebuild-Code**
(MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67). Widerspruch: GRAPH_OS_ARCHITECTURE_FREEZE
v1.0 (24.07) behauptet „ALL P0 BLOCKERS RESOLVED" — Reality-Zertifikat widerlegt das.

### Optionen

| Opt | Beschreibung | Klassifikation |
|-----|--------------|----------------|
| **A** | Rebuild-Service in `features/`: boot-seitige Graph-Rekonstruktion aus `stored_events` (Anbindung an Boot-Matrix Phase K) | ARCHITECTURE CHANGE (neues Feature) |
| **B** | Teilbereich: Watchdog-Fix (P0-2) sofort; Graph-OS-Rebuild formal **DEFERRED** mit Risiko-Dokumentation | Teil-Fix + Governance |
| **C** | Scope-Boundary akzeptieren: „Graph-OS ist Sitzungs-State"; ADR-Dokumentation + PROJECT_STATE-Update | Governance-Entscheidung |
| **D** | Freeze v1.0 als veraltet deklarieren; Rebuild als MUSCAL-2.0-Roadmap-Item (ADR-022-Abhängigkeit) integrieren; kein Code jetzt | Governance + Roadmap |

### Auswirkungen

| Dimension | A (Rebuild-Service) | B (DEFERRED) | C (Scope-Boundary) | D (Roadmap-Item) |
|-----------|---------------------|--------------|---------------------|------------------|
| **Architektur** | neue Persistenz-Rückkopplung; Graph-Zustand überlebensfähig; Integration in Replay-/Verifikationspfad | unverändert; L3 bleibt in-memory | Leitlinie „Sitzungsgebundenheit"; ADR-Niederschlag | in ADR-022-Design aufnehmen (kein heutiges System) |
| **Tests** | neue Rebuild-Tests; Baseline (470) erweitert; FL-01a-Fläche wächst (eigene Fixtures nötig) | keine neuen Tests; P0-Status-Test als Doku-Check möglich | kein Testbedarf; ggf. Dokumentations-Validierung | kein Testbedarf bis MUSCAL 2.0 |
| **Betrieb** | Restart = Zustands-Kontinuität; kürzere Cold-Boot-Zeit-Frage | Restart verliert Graph (Risiko bleibt R1) | Restart-Verlust ist definiertes Verhalten | Verlust bis MUSCAL 2.0 akzeptiert |
| **Governance** | ADR-/OVERRIDE-Pfad prüfen (`features/`-Pfad); Freeze-Status aktualisieren | Freeze-Widerspruch dokumentieren; DECISION_REGISTRY-Update | ADR-Ergänzung + PROJECT_STATE | Freeze v1.0 → DEPRECATED; ADR-022-Referenz |

### Offene Human Decision (P0-1)
„Welche Option (A/B/C/D) gilt für P0-1, und welche Frist gilt für die gewählte Option?"

---

## P0-2 — Watchdog-Events nicht persistent (Human Decision Brief)

### Problemdefinition
Watchdog-Erkennungen (Orphans) überleben Restart nicht. MC-TC-007 Phase F: ✅ PASS*.
`ExecutionWatchdog._force_fail_orphan()` ruft nur `event_bus.publish()` —
kein `EventStore.append()` (`features/monitoring/execution_watchdog.py:96-119`).
Folge-Finding C03: derselbe Orphan wird mehrfach erkannt (keine Dedup-Persistenz).

### Optionen

| Opt | Beschreibung | Klassifikation |
|-----|--------------|----------------|
| **A** | Persistenz: `_force_fail_orphan()` persistiert zusätzlich über `EventStore.append()` (Rückkanal) | ARCHITECTURE CHANGE (Feature, nicht CORE) |
| **B** | Dedup-Marker in EventStore + Persistenz in einem Schritt (behebt F-Stern **und** C03) | Feature (kombiniert) |
| **C** | DEFERRED dokumentieren (Watchdog bleibt Session-only) | Governance |
| **D** | Audit-only: Watchdog-Erkennungen in eigenes Audit-Log schreiben (kein EventStore-Topic, kein Replay-Impact) | Feature-lite |

### Auswirkungen

| Dimension | A (Persistenz) | B (Persistenz+Dedup) | C (DEFERRED) | D (Audit-only) |
|-----------|-----------------|----------------------|--------------|----------------|
| **Architektur** | Watchdog-Historie in EventStore; Replay-Relevanz (MC-TC-006-Matrix prüfen) | wie A + Dedup-Semantik | unverändert | Audit-Datei/Log außerhalb EventStore; keine Replay-Wirkung |
| **Tests** | neue Persistenz-Tests; Baseline-Erweiterung | wie A + Dedup-Test (C03) | keine | Audit-Format-Tests |
| **Betrieb** | Fehler-Historie überlebt Restart; Alarme reduziert | wie A + keine Doppelalarme | wiederholte Alarme (C03 bleibt) | Historie im Log, nicht im Event-Graph |
| **Governance** | ADR-Hinweis (Feature-Pfad); MC-TC-007 F→voll PASS dokumentieren | ADR-042-ähnliches Record | DEFERRED-Markierung | Governance-Doku für Audit-Kanal |

### Offene Human Decision (P0-2)
„Welche Option (A/B/C/D) gilt für P0-2, und welche Frist gilt?"

---

## Paket-Hinweis

- Beide Briefe ersetzen nichts — sie ERWEITERN DECISION_CLOSURE_PACKAGE RC-1 um
  die Optionen D und die Auswirkungs-Dimensionen.
- Entscheidungsergebnisse (je Option) sind in PROJECT_STATE + DECISION_REGISTRY
  zu protokollieren (durch den Entscheider/Governance).
- Keine Empfehlung erzwungen; Konsistenz-Warnung: Option B in P0-2 ist die einzige,
  die C03 adressiert (Faktenlage, keine Empfehlung).
