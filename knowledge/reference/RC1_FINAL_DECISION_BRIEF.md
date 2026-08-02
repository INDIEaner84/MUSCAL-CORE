# RC-1 FINAL DECISION BRIEF — P0-1 / P0-2

- Datum: 02.08.2026
- Zweck: Finale Entscheidungsunterlage für RC-1 (Gate-Bedingung B5) — P0-1 Graph-Rebuild und P0-2 Watchdog-Persistence (read-only; **keine Empfehlung**, keine Entscheidung, keine Statusänderung)
- Basis: G7_01_RC1_DECISION_BRIEFS.md (Erweiterung von DECISION_CLOSURE_PACKAGE §RC-1 um Option D + Auswirkungs-Dimensionen), DECISION_CLOSURE_PACKAGE §RC-1, KF3_DECISION_QUEUE §RC-1, 16_BLOCKER_REGISTRY §5/§6
- Status: **created, not committed (external KF layer)**
- Entscheider: ARB / Human (Project Governance) — gleichrangig (G7-01); nicht dieser Agent.

---

# Teil 1: P0-1 — Graph-OS-State Rekonstruktion

## 1. Problem

GraphState/SphereState sind rein in-memory; nach Restart nicht rekonstruierbar. MC-TC-007 Phase H: ❌ FAIL. Graph-Events (NODE_CREATED, EDGE_CREATED …) WERDEN in `stored_events` persistiert, aber es existiert **kein Rücklese-/Rebuild-Code** (MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67). Widerspruch: GRAPH_OS_ARCHITECTURE_FREEZE v1.0 (24.07) behauptet „ALL P0 BLOCKERS RESOLVED" — das Reality-Zertifikat widerlegt das für den Rebuild-Teil (DECISION_CLOSURE_PACKAGE §RC-1; G7-01). Klassifikation in Blocker Registry: P0-1 = PA-08, Produktions-Restart-Risiko (G5 R1, HIGH).

## 2. Evidence

| Evidenz | Quelle | Level |
|---|---|---|
| MC-TC-007 Phase H ❌ FAIL (12/14-Kriterien-Gate, 28.07) | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md; DECISION_CLOSURE_PACKAGE §RC-1 | C0 (Artefakt) |
| Graph-Events persistiert, kein Rebuild-Code | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67 | C0 |
| Freeze-Widerspruch („ALL P0 BLOCKERS RESOLVED" vs. Reality) | GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md (24.07); MC-TC-007-Artefakte (27.–31.07) | C0 |
| Status PENDING HUMAN | PROJECT_STATE-Update 01.08; G7-01; KF3_DECISION_QUEUE §RC-1 | C0 |
| Restart-Risiko R1 HIGH | G5 R1 (G5_FINAL_READINESS_REPORT); 16_BLOCKER_REGISTRY §6 | C1 |
| 384/384 Tests sonst grün (außer P0-Befunden) | KF3_DECISION_QUEUE §RC-1 (aus MC-TC-007-Artefakten) | C1 |

## 3. Aktueller Status

**PENDING HUMAN** (PROJECT_STATE-Update 01.08; G4.5 B5; G5 RC-1). Keine Entscheidung getroffen; keine Option gewählt; kein DEFERRED-Beschluss (Blocker Registry §6: „kein DECIDED, kein DEFERRED").

## 4. Optionen A–D (P0-1)

| Opt | Beschreibung | Klassifikation |
|-----|--------------|----------------|
| A | Rebuild-Service in `features/`: boot-seitige Graph-Rekonstruktion aus `stored_events` (Anbindung an Boot-Matrix Phase K) | ARCHITECTURE CHANGE (neues Feature; vermutlich `features/`-Pfad, D-006-konform) |
| B | Teilbereich: Watchdog-Fix (P0-2) sofort; Graph-OS-Rebuild formal **DEFERRED** mit Risiko-Dokumentation | Teil-Fix + Governance |
| C | Scope-Boundary akzeptieren: „Graph-OS ist Sitzungs-State"; ADR-Dokumentation + PROJECT_STATE-Update | Governance-Entscheidung |
| D | Freeze v1.0 als veraltet deklarieren; Rebuild als MUSCAL-2.0-Roadmap-Item (ADR-022-Abhängigkeit) integrieren; kein Code jetzt | Governance + Roadmap |

Quelle: G7-01 (Optionen-Tabelle P0-1); DECISION_CLOSURE_PACKAGE §RC-1 (Optionen A–C, Aufwand S–M / M–L ohne Zeitplan-Bindung).

## 5. Auswirkungen (P0-1)

### Architektur

| Opt | Auswirkung |
|-----|-----------|
| A | neue Persistenz-Rückkopplung; Graph-Zustand überlebensfähig; Integration in Replay-/Verifikationspfad (MC-TC-004/006-Replay-Pfad, Integrationstest nötig); Risiko Core-Immutabilität → features/-Plugin-Pfad erforderlich (D-006) |
| B | unverändert; L3 bleibt in-memory; Rebuild-Risiko dokumentiert |
| C | Leitlinie „Sitzungsgebundenheit"; ADR-Niederschlag |
| D | in ADR-022-Design aufnehmen (kein heutiges System) |

### Tests

| Opt | Auswirkung |
|-----|-----------|
| A | neue Rebuild-Tests; Baseline (470) erweitert; FL-01a-Fläche wächst (eigene Fixtures nötig) |
| B | keine neuen Tests; P0-Status-Test als Doku-Check möglich |
| C | kein Testbedarf; ggf. Dokumentations-Validierung |
| D | kein Testbedarf bis MUSCAL 2.0 |

### Betrieb

| Opt | Auswirkung |
|-----|-----------|
| A | Restart = Zustands-Kontinuität; kürzere Cold-Boot-Zeit-Frage |
| B | Restart verliert Graph (Risiko bleibt R1) |
| C | Restart-Verlust ist definiertes Verhalten |
| D | Verlust bis MUSCAL 2.0 akzeptiert |

### Governance

| Opt | Auswirkung |
|-----|-----------|
| A | ADR-/OVERRIDE-Pfad prüfen (`features/`-Pfad); Freeze-Status aktualisieren |
| B | Freeze-Widerspruch dokumentieren; DECISION_REGISTRY-Update |
| C | ADR-Ergänzung + PROJECT_STATE |
| D | Freeze v1.0 → DEPRECATED; ADR-022-Referenz |

## 6. Abhängigkeiten (P0-1)

- RC-6 (Mess-Gate): formale Re-Messung erst nach RC-1 (Doc 18 §2; §RC-6-M4) — RC-1 ist notwendige, nicht hinreichende Bedingung (KF3-H-1-Korrektur).
- D-006 (features/-Plugin-Pfad) bei Option A (Core-Immutabilität).
- Keine Dokument-Blocker (20/20); D-033…D-035 = separater Cluster, keine automatische Abhängigkeit (KF3-M-2-Korrektur).
- ADR-022-Bezug bei Option D (MUSCAL-2.0-Roadmap).

## 7. Was passiert ohne Entscheidung (P0-1)

- Produktions-Restart-Risiko bleibt (G5 R1 HIGH): Anwendungsfälle mit persistenter Session unwirksam; Verifikations-Graph geht bei Restart verloren (A-001-artige Risiken, s. MC-TC-003F; DECISION_CLOSURE_PACKAGE §RC-1-Risiken C).
- M4-Freshness (K3 = 25, 1/4 prozessiert) und damit RC-6-Re-Messung bleiben aus (G6 §2/§3; 18_METRIC_REGISTRY §7).
- Gate-Status bleibt CONDITIONAL (G4.5/G7-04).
- Freeze-Widerspruch („ALL P0 BLOCKERS RESOLVED" vs. Reality) bleibt unaufgelöst.

---

# Teil 2: P0-2 — Watchdog-Events nicht persistent

## 1. Problem

Watchdog-Erkennungen (Orphans) überleben Restart nicht. MC-TC-007 Phase F: ✅ PASS*. `ExecutionWatchdog._force_fail_orphan()` ruft nur `event_bus.publish()` — kein `EventStore.append()` (features/monitoring/execution_watchdog.py:96-119). Folge-Finding C03: derselbe Orphan wird mehrfach erkannt (keine Dedup-Persistenz). Klassifikation in Blocker Registry: P0-2 = PA-09, Lücke dokumentiert.

## 2. Evidence

| Evidenz | Quelle | Level |
|---|---|---|
| Phase F ⚠️ PASS* (Stern = Persistenzlücke) | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:71-76 | C0 |
| `_force_fail_orphan()` ohne `EventStore.append()` | features/monitoring/execution_watchdog.py:96-119 | C0 (Code) |
| Folge-Finding C03 (Doppelalarme, keine Dedup-Persistenz) | G7-01; DECISION_CLOSURE_PACKAGE §RC-1; PA-09 | C1 |
| Status PENDING HUMAN | PROJECT_STATE 01.08; KF3_DECISION_QUEUE §RC-1 | C0 |
| P0-2-Option B adressiert als einzige C03 (Faktenlage, keine Empfehlung) | G7-01 Paket-Hinweis Z.79-80 | C0 |

## 3. Aktueller Status

**PENDING HUMAN** (PROJECT_STATE-Update 01.08; G4.5 B5; G5 RC-1). Keine Entscheidung getroffen.

## 4. Optionen A–D (P0-2)

| Opt | Beschreibung | Klassifikation |
|-----|--------------|----------------|
| A | Persistenz: `_force_fail_orphan()` persistiert zusätzlich über `EventStore.append()` (Rückkanal) | ARCHITECTURE CHANGE (Feature, nicht CORE — features/monitoring/ ist NICHT CORE) |
| B | Dedup-Marker in EventStore + Persistenz in einem Schritt (behebt F-Stern **und** C03) | Feature (kombiniert) |
| C | DEFERRED dokumentieren (Watchdog bleibt Session-only) | Governance |
| D | Audit-only: Watchdog-Erkennungen in eigenes Audit-Log schreiben (kein EventStore-Topic, kein Replay-Impact) | Feature-lite |

Quelle: G7-01 (Optionen-Tabelle P0-2); DECISION_CLOSURE_PACKAGE §RC-1 (Optionen A–C, Aufwand S–M).

## 5. Auswirkungen (P0-2)

### Architektur

| Opt | Auswirkung |
|-----|-----------|
| A | Watchdog-Historie in EventStore; Replay-Relevanz (MC-TC-006-Matrix prüfen); Risiko Event-Doppelpersistenz (Bridge/Replay-Matrizen prüfen, MC-TC-006) |
| B | wie A + Dedup-Semantik |
| C | unverändert |
| D | Audit-Datei/Log außerhalb EventStore; keine Replay-Wirkung |

### Tests

| Opt | Auswirkung |
|-----|-----------|
| A | neue Persistenz-Tests; Baseline-Erweiterung |
| B | wie A + Dedup-Test (C03) |
| C | keine |
| D | Audit-Format-Tests |

### Betrieb

| Opt | Auswirkung |
|-----|-----------|
| A | Fehler-Historie überlebt Restart; Alarme reduziert |
| B | wie A + keine Doppelalarme |
| C | wiederholte Alarme (C03 bleibt) |
| D | Historie im Log, nicht im Event-Graph |

### Governance

| Opt | Auswirkung |
|-----|-----------|
| A | ADR-Hinweis (Feature-Pfad); MC-TC-007 F→voll PASS dokumentieren |
| B | ADR-042-ähnliches Record |
| C | DEFERRED-Markierung |
| D | Governance-Doku für Audit-Kanal |

## 6. Abhängigkeiten (P0-2)

- RC-6 (Mess-Gate) — wie P0-1 (notwendige, nicht hinreichende Bedingung).
- MC-TC-006-Replay-Matrix bei Option A/B (Event-Doppelpersistenz-Prüfung).
- D-006 (features/-Pfad; features/monitoring/ ist nicht CORE).
- Option B: Dedup-Semantik adressiert C03 (Faktenlage, keine Empfehlung — G7-01).

## 7. Was passiert ohne Entscheidung (P0-2)

- Fehlende Fehler-Historie: Watchdog-Erkennungen überleben Restart nicht.
- Wiederholte Alarme (C03 bleibt): Doppelalarme ohne Dedup.
- M4-Freshness (K3 = 25) und RC-6-Re-Messung bleiben aus; Gate-Status bleibt CONDITIONAL.

---

## Gemeinsame Abschluss-Hinweise (P0-1 + P0-2)

- Beide Briefe ersetzen nichts — sie ERWEITERN DECISION_CLOSURE_PACKAGE §RC-1 (G7-01).
- Entscheidungsergebnisse (je Option) sind in PROJECT_STATE + DECISION_REGISTRY zu protokollieren (durch den Entscheider/Governance, G7-01).
- Frist je Option: nicht definiert (offene Frage im G7-01-Brief: „welche Frist gilt?").
- Keine Empfehlung erzwungen (G7-01-Regel).

## Validation

- Read-only: keine Entscheidung, keine Empfehlung, keine Statusänderung, keine Score-Berechnung; Optionen/Auswirkungen wörtlich aus G7-01 + DECISION_CLOSURE_PACKAGE §RC-1; Status PENDING HUMAN unverändert.
