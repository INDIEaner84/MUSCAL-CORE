# RC-2 FINAL DECISION BRIEF — HDR-001 (Architecture Council)

- Datum: 02.08.2026
- Zweck: Finale Entscheidungsunterlage für RC-2 (Gate-Bedingung B6) — HDR-001 (read-only; **keine Empfehlung**, keine Entscheidung, keine Statusänderung)
- Basis: `docs/governance/HDR-001_DECISION_RECORD.md` (G7-02), DECISION_CLOSURE_PACKAGE §RC-2, 05_DECISION_REGISTRY_FOUNDATION (D-023), 16_BLOCKER_REGISTRY §5/§7, KF3_DECISION_QUEUE §RC-2, PROJECT_STATE.md:116-119
- Status: **created, not committed (external KF layer)**

---

## 1. Entscheidungsfrage

**„Erklärt das Architecture Council HDR-001 mit welchen Auflagen als angenommen, und welche der blockierten HDR-002…004 werden anschließend entblockt?"**

- HDR-001: Architecture Council (Gesamt-Governance des MUSCAL-CORE-Programms)
- HDR-002: PMGA (Project Management & Governance Agent)
- HDR-003: Master Coding AI
- HDR-004: Requirements Engineering

Quelle: HDR-001_DECISION_RECORD §1.

## 2. Historie

| Datum | Ereignis | Quelle |
|-------|----------|--------|
| 2026-07-20 | HDR-001 eingereicht; READY FOR HUMAN DECISION; HDR-002…004 blockiert (9 Dependencies) | PROJECT_STATE.md:116-119; HDR-001_DECISION_RECORD; D-023 |
| 2026-07-20 | D-023 registriert: „documented; unresolved since 20.07" | 05_DECISION_REGISTRY_FOUNDATION §B (D-023) |
| 2026-07-30 | MC-TC-004 CERTIFIED WITH CONDITIONS | HDR-001_DECISION_RECORD §2 |
| 2026-07-27–31 | MC-TC-007 CONDITIONAL GO | HDR-001_DECISION_RECORD §2 |
| 2026-07-31 | G5: Readiness 74.8; RC-2 als Release-Blocker (G5 R2 HIGH) | G5_FINAL_READINESS_REPORT; 16_BLOCKER_REGISTRY §5 |
| 2026-08-01 | G7-02-Decision-Record (Optionen A–D); offen seit 20.07 (12 Tage per 01.08) | HDR-001_DECISION_RECORD (Statuszeile) |
| 2026-08-02 | KF-3: Status HUMAN REQUIRED unverändert; KF3_CORRECTION_REPORT (keine Änderung an RC-2) | KF3_DECISION_QUEUE §RC-2 |

## 3. Evidence

| Evidenz | Quelle | Level |
|---|---|---|
| Decision Record READY FOR HUMAN DECISION seit 20.07 | HDR-001_DECISION_RECORD (Statuszeile, G7-02) | C0 |
| Referenz D-023 (unresolved since 20.07) | 05_DECISION_REGISTRY_FOUNDATION §B; DECISION_REGISTRY | C1 |
| Blockade HDR-002/003/004 (vollständig, 9 Dependencies) | HDR-001_DECISION_RECORD §2; 16_BLOCKER_REGISTRY §7; DECISION_CLOSURE_PACKAGE §RC-2 | C1 |
| Reife-Indikatoren: MC-TC-004 CERTIFIED WITH CONDITIONS (30.07); MC-TC-007 CONDITIONAL GO (27.–31.07); Readiness 74.8 (G6) | HDR-001_DECISION_RECORD §2; 18_METRIC_REGISTRY §3 (G5/G6) | C1 |
| Status HUMAN REQUIRED (unverändert) | G4.5 B6; G5 RC-2; KF3_DECISION_QUEUE §RC-2 | C0 |
| G7-02-Brief nicht als Artefakt auffindbar; belegt via HDR-001_DECISION_RECORD + Doc 05 D-023 | KF3_INDEPENDENT_REVIEW_REPORT L-7; Doc 05 | C1 |

## 4. Optionen A–D

| Opt | Beschreibung | Konsequenz |
|-----|--------------|------------|
| A | Annehmen ohne Auflagen | HDR-002…004 entblockt; volle Governance-Kette aktiv. Hinweis: P0-1/P0-2 sind unabhängig davon weiter offen |
| B | Annehmen mit Auflagen (Standard-Vorschlag): (1) MC-TC-004-Zertifizierungs-Bedingungen eingehalten, (2) HDR-002…004 mit Evidence-Pflicht (Konfidenz C0/C1) starten, (3) P0-1/P0-2 bis zum nächsten Governance-Gate entschieden | Entblockt mit Kontrollpflichten; Risiko-arm |
| C | Ablehnen / zurückweisen (Annahme erst nach RC-1-P0-Entscheidung) | HDR-002…004 bleiben blockiert; Governance-Status quo; M2-Rest bleibt |
| D | Teilbereich: nur HDR-002 freigeben; HDR-003/004 blockiert lassen | Partieller Fortschritt; Dependencies von 003/004 offen |

Quelle: HDR-001_DECISION_RECORD §3 (Optionen A–D); DECISION_CLOSURE_PACKAGE §RC-2 (Optionen 1–4, identisch nummeriert).

## 5. Auswirkungen

| Opt | Governance | Readiness (M2) | Risiko |
|-----|-----------|----------------|--------|
| A | Kette voll aktiv | M2-Rest entfällt (HDR-001-Zeile) | niedrig (Auflagenlosigkeit ohne Review-Risiko?) |
| B | Kette aktiv mit Evidence-Pflicht | M2-Rest entfällt | niedrig — empfohlener Standard-Pfad (neutral formuliert) |
| C | Status quo | M2-Rest bleibt; HDR-Deadlock hält an | mittel (Governance-Verzögerung) |
| D | HDR-002 aktiv | Teil-Rest | niedrig-mittel |

Quelle: HDR-001_DECISION_RECORD §4. Hinweis: „M2-Rest" bezieht sich auf die M2-Eingangsgröße HDR-001-Status (18_METRIC_REGISTRY §2 M2; §RC-6-M2); es wird keine Score-Änderung berechnet (Messung nur bei formaler Gate-Re-Messung, 18_METRIC_REGISTRY §6-1).

## 6. Risiken (für den Entscheider)

| # | Risiko | Hinweis |
|---|--------|---------|
| 1 | HDR-002…004 starten ohne P0-Entscheidung → Arbeitsplanung auf unsicherer Basis | Option B-Auflage (3) adressiert das |
| 2 | HDR-003 (Master Coding AI) könnte Core-Änderungen fordern — Override-Pfad dokumentiert | SESSION_RULES v2.0 VIOLATION HANDLING; D-020 |
| 3 | Kein Entscheidungs-Deadline-Mechanismus definiert | Frist (z. B. 7 Tage) als Auflage erwägen (keine Empfehlung) |
| 4 | Evidence-Pflicht (C0/C1) erhöht Doku-Aufwand | Verhältnismäßigkeit in Auflagen prüfen |
| 5 | P0-1/P0-2 weiter offen bei Option A/C/D (kein P0-Bezug) | G7-01: P0 unabhängig von HDR-Entscheidung |

Quelle: HDR-001_DECISION_RECORD §6 (Risiken 1–4); KF3_DECISION_QUEUE §RC-2 (Risiko-Zeile).

## 7. Downstream-Abhängigkeiten

- **HDR-002/003/004**: vollständig blockiert seit 20.07; Entblockung nur durch Option A/B (voll) oder D (HDR-002) (HDR-001_DECISION_RECORD §1/§3; 16_BLOCKER_REGISTRY §7).
- **RC-6 (Mess-Gate)**: RC-2 ist Mess-Voraussetzung für die formale Re-Messung (§RC-6-M4; Doc 18 §2; KF3-H-1-Korrektur — notwendige, nicht hinreichende Bedingung).
- **M2-Eingangsgröße**: HDR-001-Status ist Eingangsgröße der Metrik M2 (18_METRIC_REGISTRY §2 M2; §RC-6-M2-Messpunkt).
- **Manual-Kanon**: v0.8-Manual-Autorität (TC-H3) — Abhängigkeit von HDR-001 (Manual-Autorität M-0.7) (KF3_DECISION_QUEUE §RC-2; Doc 07).
- **Protokollierung**: Entscheidung in PROJECT_STATE.md-HDR-Tabelle (Status → DECIDED) + DECISION_REGISTRY D-023-Update (HDR-001_DECISION_RECORD §7; G7-01 Paket-Hinweis).

## 8. Was passiert ohne Entscheidung

- HDR-Deadlock hält an (G5 R2 HIGH): HDR-002/003/004 bleiben blockiert.
- v0.8-Manual-Autorität bleibt ungeregelt (TC-H3 PARTIAL).
- M2-Eingangsgröße bleibt ungeklärt; formale Re-Messung (RC-6) bleibt aus.
- Kein Verfall der Entscheidungsunterlage (Status READY FOR HUMAN DECISION unverändert seit 20.07).

## Validation

- Read-only: keine Empfehlung („empfohlener Standard-Pfad" ist Zitat aus dem Decision Record, nicht Empfehlung dieses Pakets), keine Entscheidung, keine Statusänderung, keine Score-Berechnung.
- Optionen/Konsequenzen wörtlich aus HDR-001_DECISION_RECORD §3/§4 + DECISION_CLOSURE_PACKAGE §RC-2.
