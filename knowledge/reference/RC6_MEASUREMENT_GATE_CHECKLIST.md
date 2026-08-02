# RC-6 MEASUREMENT GATE CHECKLIST

- Datum: 02.08.2026
- Zweck: Dokumentation der Voraussetzungen für die formale Re-Messung (RC-6) mit Trennung der Reife-Ebenen (read-only; **keine GO/NO-GO-Empfehlung**, keine Score-Prognose, keine Messung)
- Basis: DECISION_CLOSURE_PACKAGE §RC-6 (Messpunkte M1–M5), G6_READINESS_RECHECK.md (G6-05), 18_METRIC_REGISTRY_FOUNDATION.md, Doc 18 §2 (Aktualisierungsregel), KF3_READINESS_REPORT.md (H-1-Korrektur), KF3_DECISION_QUEUE §RC-6
- Status: **created, not committed (external KF layer)**

---

## 1. Reife-Ebenen (Definition, aus vorhandener Evidenz)

| Ebene | Bedeutung | Beleg |
|-------|-----------|-------|
| **Decision Ready** | Entscheidungsunterlage vollständig; Entscheider kann Optionen wählen; keine Informations-Lücke für die Entscheidung | KF3_READINESS_REPORT (RC-1/RC-2 = Entscheidungsbereitschaft); G7-01/G7-02 |
| **Measurement Ready** | Alle Mess-Voraussetzungen erfüllt, damit eine formale Re-Messung nach G6-Protokoll valide ausgeführt werden kann | DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt; G6_READINESS_RECHECK §1-M4 („ADR-Review (RC-4a) → K2"); KF3-H-1-Korrektur |
| **Phase Gate Ready** | Ergebnis der Re-Messung erfüllt die Gate-Bedingungen; GO-Entscheidung der Phase (formell, durch das Gate-Gremium) | DECISION_CLOSURE_PACKAGE §RC-6 (GO-Trigger-Reihenfolge 1–5); G4.5/G7-04; 18_METRIC_REGISTRY §6 (Messungs-Regeln) |

Trennregel (KF3-H-1-Korrektur): **Decision Ready ≠ Measurement Ready ≠ Phase Gate Ready**. RC-1/RC-2 sind Decision Ready; RC-6 ist erst nach Erfüllung aller Mess-Voraussetzungen Measurement Ready; Phase Gate Ready ist ausschließlich durch das formale Re-Messungsergebnis (alle 5 Metriken > 75 nach §RC-6-Zielwerte) feststellbar — dies wird hier nicht bewertet.

## 2. Voraussetzungen für die Re-Messung (Stand 02.08.2026)

### RC-1 — P0-1 / P0-2 Entscheidung

| Feld | Inhalt |
|------|--------|
| **Status (unverändert)** | **PENDING HUMAN** (PROJECT_STATE 01.08; G4.5 B5; G5 RC-1) |
| **Mess-Voraussetzung** | RC-1 abgeschlossen = P0-1/P0-2-Entscheidung getroffen und protokolliert (PROJECT_STATE + DECISION_REGISTRY, G7-01) |
| **Quelle** | DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt („RC-1 (P0-Entscheidung)"); G6_READINESS_RECHECK §1-M4 („P0-Entscheidung (RC-1) → K3"); G7-01 |
| **Reife** | **Decision Ready** (Unterlage vollständig); Mess-Wirkung erst nach Entscheidung (K3-Hebel) |
| **Offen** | Optionen A–D je P0 nicht gewählt; Frist nicht definiert (G7-01) |

### RC-2 — HDR-001 Entscheidung

| Feld | Inhalt |
|------|--------|
| **Status (unverändert)** | **HUMAN REQUIRED** (seit 20.07; G4.5 B6; G5 RC-2) |
| **Mess-Voraussetzung** | RC-2 abgeschlossen = HDR-001-Entscheidung getroffen und protokolliert (PROJECT_STATE-HDR-Tabelle + DECISION_REGISTRY D-023-Update) |
| **Quelle** | DECISION_CLOSURE_PACKAGE §RC-6 („RC-2: HDR-001-Entscheidung (Human) — M2/M4-Rest"); §RC-6-M2; HDR-001_DECISION_RECORD §7 |
| **Reife** | **Decision Ready** (Unterlage vollständig, Optionen A–D); Mess-Wirkung erst nach Entscheidung |
| **Offen** | HDR-002…004 blockiert; G7-02-Artefaktstatus ungeklärt (KF3-L-7) |

### RC-4a — ADR-Review (ADR-022…025)

| Feld | Inhalt |
|------|--------|
| **Status (unverändert)** | **NICHT GESTARTET** — NOT READY (DECISION_CLOSURE_PACKAGE §RC-4) |
| **Mess-Voraussetzung** | RC-4a abgeschlossen = ADR-Review abgeschlossen (Status-Klärung je ADR; KEINE Auto-Akzeptierung) |
| **Quelle** | DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt („RC-4 (ADR-022…025-Status)"); G6_READINESS_RECHECK §1-M4 („ADR-Review (RC-4a) → K2"); KF3-H-1-Korrektur |
| **Reife** | **Weder Decision Ready noch Measurement Ready**: Review-Struktur fertig (G7-03-Matrix), aber Input unvollständig (Turnier-Primärquelle fehlt; Migrationsbewertung fehlt; Security Model; Trust-Governance-Interaktion; RFC-Prozess) |
| **Offen** | 4 individuelle Review-Abhängigkeiten (KF3-M-4); ARB-Review-Runde anzusetzen |

### RC-5 — Dokumentationsreste (M4-Restpunkte)

| Feld | Inhalt |
|------|--------|
| **Status (unverändert)** | offen; D-033…D-035 = PLANNED + CHAT_ONLY (C2); F-03 offen; v0.8-Manual fehlt (TC-H3 PARTIAL); KIR = KG-01 (kein RC-5-Punkt, KF3-M-3) |
| **Mess-Voraussetzung** | RC-5 abgeschlossen = Dokumentationsreste bewertet (D-033…035-Plan-Docs, v0.8, F-03, TC-H3) |
| **Quelle** | DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt („RC-5 (D-033…035, v0.8, F-03, TC-H3)"); §RC-5-Statusliste; G6_04_REGISTRY_COMPLETION |
| **Reife** | **Decision Ready** (arbeitsfähig ohne Human-Entscheidung, DOC-Klasse); Mess-Wirkung erst nach Erledigung |
| **Offen** | F-03-Inhaltsprüfung; v0.8-Erzeugung (nach B5/B6-Klärung); Plan-Docs Phase C |

## 3. Messpunkte und Eingangsgrößen (RC-6-Matrix, Stand unverändert)

| Metrik | Ziel | Messpunkt | Verantwortlich | Status (unverändert) |
|--------|------|-----------|----------------|----------------------|
| M1 Repository Health | >75 | Git-State, untracked (Bridge-Governance), Suite-Stabilität | Governance-Team | 78 (G6-05) |
| M2 Governance Consistency | >75 | ADR-INDEX konsistent, HDR-001 entschieden, MC-TC-005-Klärung | ARB/Human | 78 (HDR-001-Rest: nach RC-2) |
| M3 Session Continuity | >75 | Handover 17/17, Checklist v2.0, Stale-Docs | Doku-Team | 78 (Stale-Update optional) |
| M4 Decision Completeness | >75 | RC-1 (P0-Entscheidung), RC-4 (ADR-022…025-Status), RC-5 (D-033…035, v0.8, F-03, TC-H3) | ARB/Human + Doku | 62 — Kern der Restarbeit |
| M5 Knowledge Coverage | >75 | ADR-022…025 gespiegelt, D-033…035-Docs (RC-5) | Doku-Team | 78 (Rest nach RC-5) |

Quelle: DECISION_CLOSURE_PACKAGE §RC-6-Tabelle; G6_READINESS_RECHECK §1 (Werte ±0 bestätigt).

## 4. Re-Messungs-Regeln (keine neue Regel — übernommen)

| # | Regel | Quelle |
|---|-------|--------|
| 1 | Messung nur bei formaler Gate-Re-Messung (RC-6) oder explizitem Auftrag; reine Doku erhöht keinen Score | 18_METRIC_REGISTRY §6-1; G6 §1 (±0) |
| 2 | Jede Score-Änderung erfordert Repo-Evidence C0/C1; CHAT_ONLY (C2) allein begründet keine Erhöhung | 18_METRIC_REGISTRY §6-2; G6-04-Prinzip |
| 3 | Formel-Konsistenz zu MASTER_INDEX §2 / G2 / G4 / G5 / G6 (unweighted avg); Abweichung nur mit dokumentierter Formel-Änderung | 18_METRIC_REGISTRY §6-3 |
| 4 | Messwerte versionieren mit Audit-ID + Datum; Reihenfolge-Kette Audit → G2 → G4 → G4.5 → G5 → G6 ist Referenz | 18_METRIC_REGISTRY §6-4 |
| 5 | Keine rückwirkende Anpassung historischer Messungen | 18_METRIC_REGISTRY §6-5 |
| 6 | Keine Score-Optimierung durch Interpretation | 18_METRIC_REGISTRY §6-6; G6 §2 (Formel-Ehrlichkeit) |

## 5. GO-Trigger-Reihenfolge (übernommen, keine Empfehlung)

1. RC-1a/1b: P0-1/P0-2-Entscheidung (ARB/Human) — M4-K3-Hebel
2. RC-2: HDR-001-Entscheidung (Human) — M2/M4-Rest
3. RC-4a: ADR-022…025-ARB-Review (Status-Klärung, keine Auto-Akzeptierung) — M4-K2
4. RC-5: D-033…035-Docs + v0.8 + F-03 + TC-H3 (DOC) — M4/M5
5. **Re-Messung** (formel-konsistent zu Audit/G2/G4/G5) → alle 5 >75 → GO-Bewertung der Phase (Entscheidung durch Gate-Gremium)

Quelle: DECISION_CLOSURE_PACKAGE §RC-6 (GO-Trigger 1–5). Hinweis: Die dort genannten Szenario-/Prognose-Werte (§RC-6-Prognose; G6 §4) werden hier bewusst **nicht** übernommen oder fortgeschrieben (keine Score-Prognose).

## 6. Status-Tabelle je Ebene (heutiger Stand, unverändert)

| Voraussetzung | Decision Ready | Measurement Ready | Phase Gate Ready |
|---------------|----------------|-------------------|------------------|
| RC-1 (P0-Entscheidung) | ✅ (Unterlage vollständig) | ❌ (Entscheidung ausstehend) | — |
| RC-2 (HDR-001) | ✅ (Unterlage vollständig) | ❌ (Entscheidung ausstehend) | — |
| RC-4a (ADR-Review) | ❌ (Input unvollständig) | ❌ (Review ausstehend) | — |
| RC-5 (Doku-Reste) | ✅ (arbeitsfähig, DOC) | ❌ (Erledigung ausstehend) | — |
| Re-Messung (RC-6) | — | ❌ (Voraussetzungen RC-1/2/4a/5 offen) | ❌ (keine formale Re-Messung erfolgt) |

Bewertungs-Basis: KF3_READINESS_REPORT (H-1-Korrektur); Status wörtlich aus Quellen (§2). **Kein GO/NO-GO** — die Phase-Gate-Bewertung ist allein Sache der formalen Re-Messung und des Gate-Gremiums.

## Validation

- Read-only: keine Messung, keine Berechnung, keine Score-Prognose, keine GO/NO-GO-Empfehlung, keine Statusänderung.
- Messwerte (78/78/78/62/78, Overall 74.8) wörtlich aus G6-05/DECISION_CLOSURE_PACKAGE §RC-6 übernommen, nicht neu berechnet; Szenario-Werte der Quellen nicht fortgeschrieben.
