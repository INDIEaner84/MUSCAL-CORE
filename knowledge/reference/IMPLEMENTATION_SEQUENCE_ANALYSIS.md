# IMPLEMENTATION_SEQUENCE_ANALYSIS

- Datum: 02.08.2026
- Zweck: Vergleich der Implementierungs-Szenarien A/B/C über alle RCs hinweg — **keine Sieger-Auswahl**; Bewertungs-Dimensionen: Risk, Complexity, Reversibility, Test impact, Governance compatibility
- Basis: KF5_IMPLEMENTATION_READINESS_MAP §7 (Szenarien je RC), ARB_IMPLEMENTATION_CONTRACTS.md, ARCHITECTURE_DECISION_IMPACT_GRAPH.md, DECISION_CLOSURE_PACKAGE, SESSION_RULES v2.0
- Status: **created, not committed (external KF layer)**

---

## 1. Szenario-Definitionen (über alle RCs)

| Szenario | Leitprinzip | RC-Ausprägungen |
|----------|-------------|-----------------|
| **A — Minimal correction** | kleinstmögliche Änderung; Governance-/Doku-Pfad bevorzugt; kein neuer Feature-Code | RC-1a: Freeze-Korrektur + DEFERRED (Opt. B); RC-1b: DEFERRED (Opt. C) oder minimaler append (Opt. A); RC-2: Option A/B (Auflagen-frei bzw. minimal); RC-4a: Review auf Datei-Stand ohne Input-Nachführung; RC-5: F-03 + TC-H3 nur |
| **B — Architecture-aligned correction** | Lösung im bestehenden Architektur-Rahmen (features/-Plugins, zertifizierte Layer wiederverwenden) | RC-1a: Rebuild-Plugin (Opt. A) auf Replay/EventStore-Basis; RC-1b: Persistenz+Dedup (Opt. B); RC-2: Option B (Auflagen + Evidence-Pflicht); RC-4a: Review + Input-Vervollständigung (KF3-M-4); RC-5: v0.8 + D-033…035-Plan-Docs (vollständige DOC-Arbeit) |
| **C — MUSCAL-2.0 migration preparation** | heutige Entscheidungen so treffen, dass D-010-Hybrid-Pfad vorbereitet wird | RC-1a: Option D (Roadmap-Item, ADR-022-Integration, Freeze→DEPRECATED); RC-1b: Option A/B mit Blick auf MUSCAL-2.0-Event-Modell; RC-2: Option B mit MUSCAL-2.0-Governance-Vorbereitung (HDR-Rollen); RC-4a: ADR-022…025 als Phase-B-Design-Rahmen (keine Akzeptanz heute); RC-5: Manual-Konsolidierung im MUSCAL-2.0-Rahmen |

## 2. Bewertung je Dimension

### 2.1 Risk

| Szenario | Gesamt-Risiko-Profil | Höchste Risiko-Quelle |
|----------|----------------------|------------------------|
| A | **niedrig–mittel** | P0-Risiken bleiben operativ (R1 HIGH Restart; C03-Alarme); keine Code-Kollision; Governance-Verzögerung (RC-2-Option C-Variante) |
| B | **mittel** | Rebuild-/Persistenz-Code in zertifizierter Zone (EventStore/Replay, MC-TC-004/006); Feature-Interferenz RC-1a+1b; FL-01a-Fixture-Fläche wächst |
| C | **mittel–hoch** | Migrationspfad D-010↔ADR-001 unbestimmt (MEDIUM); heutige Entscheidungen präjudizieren MUSCAL-2.0-Design; Trust-Governance-NO-GO ungelöst bleibt |

### 2.2 Complexity

| Szenario | Komplexität | Aufwand (Quellen-Skala) |
|----------|-------------|--------------------------|
| A | **niedrig** | S (Doku/Governance; minimaler append S) |
| B | **mittel** | S–M (RC-1b) bis M–L (RC-1a Rebuild, DECISION_CLOSURE_PACKAGE §RC-1) |
| C | **mittel–hoch** | Design-/Migrations-Analyse (ADR-022-Migrationsbewertung fehlt — RC-4a NOT READY) |

### 2.3 Reversibility

| Szenario | Reversibilität | Detail |
|----------|----------------|--------|
| A | **hoch** | Doku-Commits reversibel; kein Feature-Code |
| B | **hoch (pro Komponente)** | features/-Plugins entfernen = Rollback (D-006); Core bleibt unberührt; zertifizierte Layer unverändert |
| C | **mittel** | ADR-022-Roadmap-Einträge reversibel; aber präjudizierte Design-Entscheidungen (DEPRECATED-Freeze) erfordern formale Rücknahme |

### 2.4 Test Impact

| Szenario | Test-Wirkung | Baseline-Bezug |
|----------|--------------|----------------|
| A | **minimal** | keine neuen Suiten; Bestands-Suiten unverändert; Baseline 470 stabil |
| B | **hoch** | neue Suiten (Rebuild, Persistenz, Dedup, Audit); FL-01a-Fixtures erforderlich (G7-01 P0-1-Test-Zeile); Baseline-Erweiterung nur mit dokumentierter Kalibrierung (D-041); MC-TC-006-Rerun nach EventStore-Berührung |
| C | **mittel** | keine neuen Code-Tests heute (Roadmap-Ansatz); aber Test-Governance-Vorbereitung (MPIR/MREIL, D-013/D-014-Bezug) |

### 2.5 Governance Compatibility

| Szenario | Kompatibilität | Konflikt-Risiko |
|----------|----------------|-----------------|
| A | **hoch** | volle Konformität mit D-006/D-020 (kein Core); G6-04 unberührt; Handover-Pflicht erfüllt |
| B | **hoch** | D-006-konform (features/); D-009 (append-Signatur) und D-008 (Layer-Trennung) müssen eingehalten werden; ARCHITECTURE-CHANGE-Deklaration nötig (neue Features) |
| C | **mittel** | ADR-022-Akzeptanz-Frage (G4.5-B2: keine Auto-Akzeptierung) berührt; CHAT_ONLY-Status (D-010…D-014) bleibt bis Repo-Beleg (G6-04); Freeze-DEPRECATED nur durch Entscheider |

## 3. Sequenz-Vergleich (Reihenfolge-Effekte)

| Aspekt | Szenario A | Szenario B | Szenario C |
|--------|-----------|-----------|-----------|
| Erster Schritt | RC-2 (Governance) → RC-1b minimal | RC-2 → RC-1b (S) → RC-1a (M–L) → RC-4a | RC-2 → RC-4a (Design-Rahmen) → RC-1-Roadmap-Entscheidungen |
| Abhängigkeits-Entflechtung | kein neuer Code → keine neuen Kanten | RC-1a/1b teilen EventStore/Replay-Zone → Sequenz-Planung nötig (Impact-Graph §6 Risikokonzentration) | D-010↔ADR-001-Migrationspfad wird erstes Bearbeitungs-Objekt |
| RC-6-Wirkung | langsamste (P0-Risiken bleiben; M4-K3 nur partiell) | schnellste vollständige M4-K3/K2-Bearbeitung (Ableitung aus G6 §3-Hebel, keine Score-Prognose) | M4-K2 über Review; P0-Code-Lösung verzögert |
| Rollback-Fenster | durchgehend klein | pro Phase klein | größer (Design-Präjudiz) |

## 4. Beobachtungen (keine Auswahl)

1. **Szenario A** minimiert Risiko und Governance-Konflikt, lässt aber die P0-Last (R1, C03) und damit den Kern der M4-K3-Restarbeit liegen — die RC-6-Voraussetzungen (RC-1 abgeschlossen) bleiben im engsten Sinne unerfüllt, sofern DEFERRED nicht als „abgeschlossen" gezählt wird (Status-Semantik liegt beim Entscheider; kein GO/NO-GO hier).
2. **Szenario B** adressiert die P0-Probleme im zertifizierten Rahmen und nutzt vorhandene Infrastruktur (ReplayService, EventStoreAdapter) — mit der höchsten Test- und Sequenz-Komplexität (EventStore/Replay-Zone wird von RC-1a und RC-1b berührt; Impact-Graph §6).
3. **Szenario C** bereitet MUSCAL 2.0 vor, verschärft aber die Abhängigkeit vom ungelösten Migrationspfad (D-010 vs D-001, MEDIUM) und vom Trust-Governance-NO-GO — beides Review-Inputs von RC-4a.
4. Die Dimensionen korrelieren teilweise (A = niedriges Risiko/Komplexität, aber geringe P0-Auflösung; B = mittlere Komplexität mit voller P0-Auflösung; C = höchste strategische Reichweite mit höchster Design-Abhängigkeit). Eine Bewertung (welche Dimension Priorität hat) ist Entscheider-Sache.
5. Alle drei Szenarien sind mit D-006/D-020 kompatibel, sofern keine Core-Berührung erfolgt; Szenario B erfordert ARCHITECTURE-CHANGE-Deklarationen (neue Features), Szenario C zusätzlich die Freeze-DEPRECATED-Entscheidung.

## 5. Governance-Kompatibilitäts-Matrix (je Szenario, je Regel)

| Regel | A | B | C |
|-------|---|---|---|
| D-006 (features/-Pflicht) | ✅ (kein Code) | ✅ (Plugins) | ✅ (kein Code heute) |
| D-020/Core-Immutability | ✅ | ✅ | ✅ |
| D-008 (EventBus/EventStore/AuditLog getrennt) | ✅ | ⚠️ Prüfpflicht (Doppelpersistenz) | ✅ |
| D-009 (append-Signatur verifiziert) | ✅ | ✅ (Voraussetzung) | ✅ |
| G4.5-B2 (keine Auto-Akzeptierung) | ✅ | ✅ | ⚠️ ADR-022-Rolle klären |
| G6-04 (CHAT_ONLY bleibt) | ✅ | ✅ | ✅ |
| D-041 (Baseline 470) | ✅ | ⚠️ Kalibrierung bei Erweiterung | ✅ |
| Handover-Pflicht (D-021) | ✅ | ✅ | ✅ |

## 6. Validation

- Read-only: keine Sieger-Auswahl, keine Empfehlung, keine Entscheidung, keine Score-Berechnung; Aufwandsskalen wörtlich aus DECISION_CLOSURE_PACKAGE; Beobachtungen als Modell-Ableitung gekennzeichnet (nicht als GO/NO-GO).
- Konsistent mit ARB_IMPLEMENTATION_CONTRACTS (Grenzen) und ARCHITECTURE_DECISION_IMPACT_GRAPH (Risikokonzentration EventStore/Replay-Zone).
