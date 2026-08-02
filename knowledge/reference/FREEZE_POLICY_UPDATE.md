# FREEZE_POLICY_UPDATE

- Datum: 02.08.2026
- Zweck: Zusammenstellung der Freeze-Zonen/-Objekte bis zum ARB (keine Entscheidung, keine Annahme — Vorlage für den Entscheider; read-only)
- Basis: ARCHITECTURE_RISK_REGISTER_UPDATE.md (Freeze-Zonen), SESSION_RULES v2.0 (CORE-Immutability), ADR-019 (Freeze v1.0), D-041 (Baseline 470), ADR-024 (Trust-Governance, Baseline 384), ADR-022…025 (DRAFT), ARB_IMPLEMENTATION_CONTRACTS.md, D-008/D-010…D-014 (Layer-Trennung, Chat-only-Architektur), D-020 (Core-Write-Regel), G6-04 (CHAT_ONLY)
- Status: **created, not committed (external KF layer)**

---

## 1. Grundsatz

- Bis zum ARB werden die nachfolgend gelisteten Objekte **nicht verändert** (keine Code-Änderung, keine Status-Änderung, keine Akzeptanz, keine Baseline-Anpassung) — als **Vorbereitungs-Vorschlag** formuliert; formale Geltung erhält dieser Freeze erst durch Entscheidung (ADR-019-Fortschreibung bzw. neue Freeze-Entscheidung).
- Ziel: eine stabile, eindeutige Referenz für die ARB-Entscheidungen (RC-1, RC-2, RC-4a, RC-5, MC-TC-005, Bridge-Governance) — keine Änderungen während der Simulation, keine versteckten Verschiebungen.
- Begriffsregel: „Freeze" hier = „keine Änderung bis zur expliziten Aufhebung"; CHAT_ONLY bleibt davon unberührt (bestehender Mechanismus, G6-04).

## 2. Freeze-Zonen und -Objekte (mit Quelle)

### 2.1 Core Runtime

| Objekt | Freeze-Grund |
|--------|--------------|
| `kernel.py` | zentrale Orchestrierung; jeder Eingriff berührt RC-1 (P0-1 Watchdog-Bypass) — Design-Entscheidung steht aus |
| `graph.py` (GraphState, CORE immutable; public API add_node/update_node/add_edge) | CORE-Immutability (SESSION_RULES v2.0); D-020; M4-K3-Rest hängt an P0-Entscheidung |
| `mel.py` | Core-Orchestrierung; D-020 |
| `event_bus.py` | zentrale Event-Infrastruktur; D-008 (Layer-Trennung) |
| `main_boot.py` | Boot-Phase; kein Phase-K-Rebuild-Code im Repo (KF5-C-4) |

### 2.2 Event-Modell (Persistenz-Säule)

| Objekt | Freeze-Grund |
|--------|--------------|
| `EventStore`/`Replay` (MC-TC-004/006-zertifiziert) | RC-1a/1b-Szenarien (Option A/B) würden diese Zone berühren (Impact-Graph §6: Risikokonzentration); zertifizierter Stand bleibt Referenz (Baseline, D-036) |
| Event-Format/D-008-Layer-Grenze | Änderungen präjudizieren RC-1-Optionen und MUSCAL-2.0-Hybridpfad (D-010) |

### 2.3 ADR-State

| Objekt | Freeze-Grund |
|--------|--------------|
| ADR-022, ADR-023, ADR-024, ADR-025 — **bleiben DRAFT** | RC-4a NOT READY (Review-Inputs fehlen, KF3-M-4); G4.5-B2 (keine Auto-Akzeptierung); Status-Änderung ist RC-4a-Entscheidung |
| ADR-INDEX/PROJECT_STATE-Spiegel | G6-01-Konsistenz-Anforderung; Referenz für M2/M4-Messpunkte |
| ADR-019 (Freeze v1.0) | Freeze-Kontinuität; Aufhebung nur durch Entscheider |

### 2.4 Baselines

| Objekt | Freeze-Grund |
|--------|--------------|
| Baseline 470 (D-041) | Mess-Referenz; Kalibrierung nur mit dokumentierter Erweiterung nach ARB-Entscheidung (Szenario B) |
| Baseline 384 (ADR-024, Trust-Governance) | Referenz für K2-Komponente; ADR-024-Status offen (RC-4a) |
| MC-TC-006-Suite (deterministisch, ReplayService) | deterministische Referenz; Rerun-Nachweis erwartet bei Suite-Berührung (Evidence E-3) |

### 2.5 Architektur-Steuerung

| Objekt | Freeze-Grund |
|--------|--------------|
| Chat-only-Architektur (D-010…D-014) | CHAT_ONLY bleibt bis Repo-Beleg (G6-04); Doku-Arbeiten (RC-5) füllen die Lücke, ohne die Architektur zu wechseln |
| Pre-Write-Check `guards.write_guard.validate_write(path)` | wirkt als technischer Freeze-Mechanismus (D-020-Flanke); unverändert lassen |

## 3. Ausnahmen und Regelungen

| Regel | Inhalt |
|-------|--------|
| R-1 | **Keine Ausnahme ohne ARB-Entscheidung**; jede gewünschte Änderung an gefrorenen Objekten wird als offener Punkt protokolliert (Freeze-Review-Liste) |
| R-2 | **Lesende Arbeit bleibt erlaubt** (Reviews, Kontrakte, Matrizen, Checklisten — wie bisher) |
| R-3 | **Neue Feature-Code-Arbeit (features/) wird NICHT begonnen**, solange RC-1/RC-2-Entscheidungen ausstehen (Szenario-Auswahl präjudiziert die Plugin-Struktur) |
| R-4 | **Doku-Arbeiten mit RC-5-Mandat (D-033…035, v0.8, F-03, TC-H3) bleiben möglich** — sie ändern keine gefrorenen Objekte, sondern vervollständigen die Referenzen (CHAT_ONLY-Rahmen) |
| R-5 | **Aufhebe-Bedingungen**: Freeze endet je Zone mit der jeweiligen ARB-Entscheidung + Phase-1/2-POST_ARB_Aktionszulassung; formale Aufhebung durch neue Freeze-Entscheidung oder ADR-019-Fortschreibung |
| R-6 | **Konfliktregel**: Widerspricht eine ARB-Entscheidung diesem Freeze, hat die ARB-Entscheidung Vorrang; Freeze wird danach angepasst (Protokoll) |

## 4. Verhältnis zu bestehenden Mechanismen

| Mechanismus | Verhältnis |
|-------------|------------|
| SESSION_RULES v2.0 (CORE-Immutability-Liste) | bleibt die operative Grundlage; dieser Freeze ergänzt sie um Zonen mit ARB-Bezug |
| D-020 (Core-Write) | unverändert gültig; Pre-Write-Check bleibt aktiv |
| ADR-019 (Freeze v1.0) | dieser Freeze ist eine **Vorbereitungs-Zusammenstellung**, keine Änderung von ADR-019 |
| G6-04 (CHAT_ONLY) | unberührt; gültig bis Repo-Beleg |
| Handover (D-021) | Freeze-Objekte und offene Punkte werden im Handover gespiegelt |

## 5. Offene Punkte dieser Vorlage (für den Entscheider)

1. Annahme/Ablehnung des Freeze-Vorschlags als Ganzes oder je Zone (R-1…R-6).
2. Zusätzliche Objekte: z. B. `docs/specs/adrs/`-Review-Arbeit, `SESSION_RULES`-Ergänzungen (kann der Agent hinzufügen? — aktuell keine Regeländerung erlaubt).
3. Umgang mit ADR_REVIEW_MATRIX-Diskrepanz (KF4-Fund #6) vor RC-4a-Start.

## 6. Validation

- Read-only: keine Entscheidung, keine Annahme, keine Änderung an SESSION_RULES oder ADR-Dateien; Empfehlungs-Charakter klar markiert („Vorbereitungs-Vorschlag").
- Jede Freeze-Zone mit Quelle belegt (Session-Regeln, ADRs, D-IDs, Code-Zeugen); keine Score-Berechnung; konsistent mit ARB_IMPLEMENTATION_CONTRACTS (Forbidden Actions) und POST_ARB_EXECUTION_PLAN (Phasen 1–2).
