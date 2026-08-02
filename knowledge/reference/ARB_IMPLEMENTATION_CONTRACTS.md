# ARB_IMPLEMENTATION_CONTRACTS

- Datum: 02.08.2026
- Zweck: Implementierungs-Kontrakte je offener Entscheidung (RC-1a, RC-1b, RC-2, RC-4a, RC-5) — definiert Entscheidungs-Grenze (Mensch), Agenten-Grenze, Validierungs-Grenze und Verbotene Aktionen (read-only; keine Implementierung, keine Entscheidung, keine Statusänderung, keine Score-Berechnung)
- Basis: KF5_IMPLEMENTATION_READINESS_MAP.md, ARCHITECTURE_DECISION_IMPACT_GRAPH.md, POST_ARB_EXECUTION_PLAN.md, ARCHITECTURE_RISK_REGISTER_UPDATE.md, DECISION_CLOSURE_PACKAGE.md, HUMAN_DECISION_INDEX.md, PROJECT_STATE.md, RC1/RC2-Briefe, ADR_REVIEW_PACKET.md, SESSION_RULES v2.0
- Status: **created, not committed (external KF layer)**

---

## Kontrakt-Modell

| Grenze | Bedeutung | Allgemeine Regel (Quelle) |
|--------|-----------|---------------------------|
| **Decision Boundary** | Was nur Menschen/ARB entscheiden dürfen | Keine Optionen-Wahl durch Agenten (G7-01: „Entscheider: ARB / Human — nicht dieser Agent"); keine ADR-Akzeptanz (G4.5-B2) |
| **Agent Boundary** | Was Agenten nach Entscheidung implementieren dürfen | Erweiterungen nur in `features/` (D-006); kein Core-Write ohne ARCHITECTURE CHANGE + OVERRIDE (D-020; SESSION_RULES v2.0) |
| **Validation Boundary** | Was Fertigstellung beweist | Test-basiert; Baseline 470 (D-041); MC-TC-006-Determinismus; Evidence C0/C1 (18_METRIC_REGISTRY §6-2) |
| **Forbidden Actions** | Was unter keinen Umständen passieren darf | Kein stillschweigendes Auflösen von Konflikten (SESSION_RULES Conflict rule); keine Score-Manipulation (G6-04); keine Löschung (F-03) |

---

## KONTRAKT RC-1a — Graph-OS Reconstruction (P0-1)

### Decision Boundary (menschlich/ARB)
- Wahl der Option A/B/C/D je P0-1 (G7-01: „Welche Option (A/B/C/D) gilt für P0-1, und welche Frist gilt?") — Entscheidung + Frist.
- Bei Option A: Freigabe ARCHITECTURE CHANGE (neues Feature) + Boot-Phase-K-Integrationsfreigabe.
- Bei Option D: Deklaration Freeze v1.0 → DEPRECATED + ADR-022-Roadmap-Aufnahme.
- Bei Option C: Freigabe der Scope-Boundary-Leitlinie („Graph-OS ist Sitzungs-State").
- Auflösung des Freeze-Widerspruchs (GRAPH_OS_ARCHITECTURE_FREEZE v1.0 „ALL P0 BLOCKERS RESOLVED" vs. MC-TC-007) — nur durch Entscheider (Teil jeder Option).

### Agent Boundary (nach Entscheidung)
- Option A: Rebuild-Service-Plugin unter `features/graph_rebuild/` (Vorschlag) auf Basis ReplayService + EventStoreAdapter; ausschließlich public GraphState-API (add_node/update_node/add_edge) — kein graph.py-Schreibzugriff; Boot-Wiring in `features/boot/` (utr_wiring.py oder neues Modul).
- Option B/C/D: reine Doku-/Governance-Änderungen (PROJECT_STATE, DECISION_REGISTRY, Freeze-Doku, ADR-022) — keine Code-Änderung am Graph-Pfad.

### Validation Boundary
- Option A: Rebuild-Tests grün (Rekonstruktion ≡ Event-Log; Knoten-/Kanten-Anzahl; Reihenfolge); MC-TC-007-Phase-H-Befund überprüfbar (Rebuild existiert); Regression: Baseline 470 + MC-TC-006-Suite ±0; FL-01a-Fixtures für neue Tests; Doku-Update MC-TC-007-Phase-H-Status.
- Option B: DEFERRED-Doku mit Risiko-Notiz vorhanden (R1 bleibt dokumentiert).
- Option C: ADR-/PROJECT_STATE-Niederschlag der Scope-Boundary vorhanden.
- Option D: Freeze-DEPRECATED-Markierung + ADR-022-Item im Repo.

### Forbidden Actions
- ❌ graph.py/sphere.py/kernel.py/mel.py ändern (CORE-Immutability, SESSION_RULES v2.0).
- ❌ `--allow-core-write` ohne dokumentierten ARCHITECTURE-CHANGE-Beschluss + OVERRIDE-Eintrag (D-020).
- ❌ Rebuild als „erledigt" deklarieren ohne Rebuild-Tests (C0/C1-Evidence-Pflicht, 18_METRIC_REGISTRY §6-2).
- ❌ Freeze-Widerspruch stillschweigend auflösen (Conflict rule: dokumentieren, nicht auflösen).
- ❌ Optionen-Kombinationen erfinden (nur A/B/C/D je P0; G7-01-Struktur).

## KONTRAKT RC-1b — Watchdog EventStore Persistence (P0-2)

### Decision Boundary (menschlich/ARB)
- Wahl der Option A/B/C/D je P0-2 (G7-01: „Welche Option (A/B/C/D) gilt für P0-2, und welche Frist gilt?").
- Bei Option A/B: Freigabe EventStore-Schreibpfad im Watchdog + MC-TC-006-Replay-Matrix-Prüfung als Voraussetzung.
- Bei Option C: Freigabe DEFERRED-Markierung (Watchdog Session-only).
- Faktenlage-Hinweis (keine Empfehlung): Option B adressiert als einzige C03 (G7-01 Paket-Hinweis) — Entscheider-Kenntnis, keine Agenten-Auswahl.

### Agent Boundary (nach Entscheidung)
- Option A: `features/monitoring/execution_watchdog.py` (Zeile 96-119-Bereich) um EventStore-append erweitern — via vorhandenem `EventStoreAdapter` (features/events/event_adapter.py:75-85); kein neues Core-Import.
- Option B: zusätzlich Dedup-Semantik (Marker) im Watchdog-/EventStore-Pfad.
- Option D: eigener Audit-Kanal in features/monitoring/ (außerhalb EventStore, kein Replay-Impact).
- Option C: keine Code-Änderung; DEFERRED-Doku.

### Validation Boundary
- Option A/B: Persistenz-Tests (EXECUTION_FAILED-Events im stored_events nach Orphan-Fail); Option B: Dedup-Test (C03 — gleicher Orphan nur 1×); MC-TC-006-Suite deterministisch ±0 (kein Replay-Drift); Baseline 470.
- Option D: Audit-Format-Tests.
- Option A/B: MC-TC-007 Phase F → voll PASS dokumentierbar.

### Forbidden Actions
- ❌ EventBus/EventStore/AuditLog verschmelzen (D-008).
- ❌ EventStore.append ohne Signatur-Verifikation (D-009: Bridge-Callback-Mismatch-Historie).
- ❌ Replay-Determinismus-Änderung ohne MC-TC-006-Rerun (zertifizierter Layer, D-036).
- ❌ Doppel-Persistenz stillschweigend einführen (Replay-Matrix-Prüfung ist Voraussetzung, G7-01).
- ❌ Watchdog-Fix als P0-1-Erledigung verbuchen (getrennte Entscheidungen, G7-01).

## KONTRAKT RC-2 — HDR-001 Governance

### Decision Boundary (menschlich/ARB)
- Beantwortung der Entscheidungsfrage (HDR-001_DECISION_RECORD §1): Annahme-Erklärung + Auflagen (Option A/B) oder Ablehnung (C) oder Teilfreigabe (D).
- Festlegung, welche HDR-002…004 entblockt werden (Teil der Frage).
- Protokollierung in PROJECT_STATE-HDR-Tabelle (→ DECIDED) + DECISION_REGISTRY D-023 (durch Human/Governance).
- G7-02-Artefaktstatus klären (KF3-L-7: Datei nicht auffindbar; Beleg via HDR-001_DECISION_RECORD + Doc 05 D-023).

### Agent Boundary (nach Entscheidung)
- Dokumentations-Arbeiten nur nach Protokollierung: PROJECT_STATE-Update, D-023-Registry-Update, HDR-002…004-Startrampen (Rollen-Beschreibungen, Evidence-Pflicht C0/C1 bei Option B-Auflagen).
- Keine Governance-Befugnis: Agent dokumentiert Mandate, übt sie nicht aus (HDR-001_DECISION_RECORD §5: „Dieser Agent: KEINE Entscheidungsbefugnis").

### Validation Boundary
- PROJECT_STATE-HDR-Tabelle: Status DECIDED + gewählte Option + Datum (sichtbar, C0).
- DECISION_REGISTRY D-023: resolved-Eintrag mit Quelle.
- Bei Option B: Auflagen als Arbeitsregeln an HDR-002…004 übergeben (Doku-Nachweis).

### Forbidden Actions
- ❌ HDR-Entscheidung durch Agenten (Mandat verboten).
- ❌ Statusänderung ohne Protokollierung durch den Entscheider.
- ❌ P0-1/P0-2 als Teil der HDR-Entscheidung behandeln (unabhängig offen, Record-Hinweis).

## KONTRAKT RC-4a — ADR-022…025 Review

### Decision Boundary (menschlich/ARB)
- Review-Runde ansetzen (ARB); je ADR Datei-OQs (3) beantworten; G6-01-Kategorien als Template-Anforderungen annehmen (ADR_REVIEW_MATRIX Protokoll 1).
- Konflikt-Urteile je Zeile (bestätigen/verwerfen/ergänzen) (Protokoll 2).
- Status-Empfehlung je ADR: PROPOSED-final / DEPRECATED / ACCEPTED — Entscheidung durch ARB/Human, nicht durch Agenten (Protokoll 3).
- Input-Beschaffung: Turnier-Primärquelle beschaffbar? (KF3-L-9); Migrationsbewertung; Security-Model-Spezifikation; RFC-Process-Definition; Trust-Governance-Interaktion (KF3-M-4).

### Agent Boundary (nach Review)
- Dokumentarische Umsetzung des ARB-Urteils: ADR-INDEX + ADR-Dateien + PROJECT_STATE-ADR-Spiegel aktualisieren (nur durch Review-Instanz, Protokoll 4).
- REFERENCE_GRAPH-DRAFT-Knoten (Doc 04/14) bei ACCEPTED aktualisieren.
- Registry-Spiegel D-010…D-014: CHAT_ONLY-Markierung nur bei Repo-Beleg entfernen (G6-04).
- Keine Design-/Code-Arbeit aus ADR-Inhalten (MUSCAL-2.0-Umsetzung ist Folge-Phase).

### Validation Boundary
- Review-Protokoll je ADR liegt vor (OQs beantwortet, Konflikt-Urteil, Status-Empfehlung).
- ADR-Dateien/INDEX zeigen konsistenten Status (Repository-Sicht, C0).
- Kein Code aus ADR-Inhalten entstanden (Compliance-Check je ADR: „Kein Code-Anteil").

### Forbidden Actions
- ❌ Auto-Akzeptierung (G4.5-B2; KF-03: keine Akzeptanzannahmen).
- ❌ CHAT_ONLY als implementiert interpretieren (C2 ≠ C0/C1; G6-04).
- ❌ ADR-Inhalte in Code umsetzen vor ARB-Urteil (Design-Fragen offen, §RC-4).
- ❌ OQs erfinden/umformulieren; Konflikt-Severity ändern (nur ARB).

## KONTRAKT RC-5 — Documentation Consolidation

### Decision Boundary (menschlich/ARB)
- DOC-Auftrag (G4.5 §7 B1–B4): Freigabe F-03-Inhaltsprüfung, v0.8-Manual-Generierung, D-033…D-035-Plan-Docs, TC-H3-Header-Hinweise (Inhaltsänderung an 3 Manuals — außerhalb KF-Mandat).
- Kein Human-Entscheidungsbedarf für die Items selbst (KF3-M-2: kein RC-1-Bezug).
- Klärung B5/B6 (v0.8/TC-H3) als Voraussetzung für v0.8-Generierung (KF3-Queue §RC-5).

### Agent Boundary
- F-03: Inhalt prüfen → referenzieren oder Referenz-Markierung (KEINE Löschung).
- v0.8-Manual: Generierung aus REPOSITORY_CENSUS/Reconciliation-Daten (verbindliche Zahlen; Implementiert/Geplant-Abgrenzung, TECHNICAL_MANUAL_v0.8_SCOPE).
- D-033…035: je Plan-Dokument in docs/governance/ (Phase C, DOC; CHAT_ONLY-Markierung bleibt bis Repo-Beleg).
- TC-H3: Header-Hinweise nur mit Inhalts-Mandat (Manuals = Inhaltsänderung).

### Validation Boundary
- F-03: Referenz-/Markierungsstatus dokumentiert; keine Löschung erfolgt.
- v0.8: Zahlen deckungsgleich mit Census (TF-06-Kontradiktion aufgelöst); Manual im Repo committet.
- D-033…035: 3 Plan-Docs im Repo (docs/governance/), Status-Update erst dann (G6-04: Repo-Beleg).
- TC-H3: Header-Hinweise in 3 Manuals (bei Inhalts-Mandat).

### Forbidden Actions
- ❌ Löschung specs/adrs/IMPLEMENTATION_STATUS.md (F-03-Regel, §RC-5).
- ❌ v0.8-Zahlen ohne verifizierte Quelle (TF-02/TF-06-Kontradiktion).
- ❌ CHAT_ONLY→Repo-Status ohne Artefakt (G6-04).
- ❌ Score-/Registry-Änderung durch Doku-Arbeit (18_METRIC_REGISTRY §6-1: Doku erhöht keinen Score).

---

## Cross-Contract Regeln

| Regel | Quelle |
|-------|--------|
| Pre-Write-Check `guards.write_guard.validate_write(path)` vor jedem Schreibzugriff | AGENTS.md |
| Core-Write nur mit ARCHITECTURE CHANGE + OVERRIDE + `--allow-core-write` | SESSION_RULES v2.0; D-020 |
| Handover-Pflicht je Session mit Änderungen | D-021 |
| Evidence C0/C1 für jede Fertigstellungs-Erklärung; C2 allein genügt nicht | 18_METRIC_REGISTRY §6-2 |
| Konflikte dokumentieren, nicht stillschweigend auflösen | SESSION_RULES Conflict rule |
| Keine Empfehlung in Entscheidungsunterlagen (G7-01-Regel) | G7-01 |

## Validation

- Read-only: keine Entscheidung, keine Implementierung, keine Statusänderung, keine Score-Berechnung; Grenzen aus KF5-Map/Kontrakten mit Quelle; Szenarien A/B/C (KF5 §7) ungewählt.
- Konsistent mit HUMAN_DECISION_INDEX (Entscheider/Status) und DECISION_CLOSURE_PACKAGE (Optionen/Verantwortliche).
