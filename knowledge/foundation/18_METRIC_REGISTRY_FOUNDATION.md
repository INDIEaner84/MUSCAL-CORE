# 18_METRIC_REGISTRY_FOUNDATION.md

**Doc:** KF-1/18 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** MASTER_INDEX.md §2 (Audit, 45.2) · G4_MEASUREMENT_REPORT.md (68.6) · G5_FINAL_READINESS_REPORT.md (74.8) · G6_READINESS_RECHECK.md (74.8, M4-Formel) · G4_5_EXECUTION_RESULT (Prognose 74.4) · KNOWLEDGE_FOUNDATION_CHARTER (KF-00) · 05_DECISION_REGISTRY_FOUNDATION (D-IDs)
**Modus:** reine Dokumentation — **keine Neuberechnung, keine Statusänderung, keine Entscheidung, keine Interpretation von CHAT_ONLY als implementiert**
**Regel:** Alle Werte wörtlich aus Gate-Reports übernommen; Formel-Basis unverändert: MASTER_INDEX §2 (M1–M5, unweighted average).

---

## 1. Purpose

Dieses Dokument macht die Messung der Knowledge Foundation **reproduzierbar und nachvollziehbar**:

1. **Reproduzierbare Messung** — jede Metrik ist mit Definition, Formel, Eingangsgrößen und Evidence-Quellen dokumentiert, sodass eine Re-Messung (RC-6) formel-konsistent zur Kette Audit → G2 → G4 → G4.5 → G5/G6 ausgeführt werden kann.
2. **Nachvollziehbarkeit von Gate-Entscheidungen** — Scores, Δ-Werte und Zielverfehlungen sind an Gate-Reports gebunden; jede Entscheidung (z.B. G4/G5: B — CONDITIONAL GO) ist mit der jeweiligen Messlage verknüpft.
3. **Keine Score-Optimierung durch Interpretation** — Messwerte werden nur geändert, wenn Repo-Evidence (C0/C1) vorliegt; CHAT_ONLY-Einträge (C2) bleiben unverändert und erhöhen keinen Score. „Formel-Ehrlichkeit" ist dokumentierte Praxis (G6 §2: kein erzwungenes GO durch ungewichtete Mittelung).

## 2. Metric Inventory

### M1 — Repository Health

| Feld | Inhalt |
|------|--------|
| Metric ID | M1 |
| Definition | Zustand des Repos: uncommitted Work, Duplikation, Wahrheits-Konsistenz (MASTER_INDEX §2 M1) |
| Zweck | Git-als-Wahrheit messen (D-022); Risiko durch nicht committete Arbeit/Gaps sichtbar machen |
| Formel | `100 − (uncommitted-work-Penalty + Duplikations-Penalty + Truth-Consistency-Penalty)`, gewichtet [C0] — Gewichtung nicht öffentlich spezifiziert (Teil-GAP, §4) |
| Eingangsgrößen | git status (uncommitted/untracked), Duplikations-Zählung (ADR ×4, Manuals ×3, `muscal-mvp/`), Test-Suite-Status (19/2.347/1), Baseline 470 (18/18) |
| Evidence Sources | MASTER_INDEX §2 M1; G4 §M1; G5 §1; G6 §1; REPOSITORY_CENSUS; MANUAL_RECONCILIATION_FINAL |
| Confidence Level | C0 (Audit/G4), C1 (G5-Messung) |
| Aktualisierungsregel | bei jeder Commit-/Git-Zustands-Änderung neu belegen; formale Messung nur bei Gate-Re-Messung |

### M2 — Governance Consistency

| Feld | Inhalt |
|------|--------|
| Metric ID | M2 |
| Definition | Anteil konsistenter Governance-Mechanismen (Overrides, Authority-Kette, Decision-Records) bei konfliktfreier Anwendung [C1] |
| Zweck | Governance-Durchsetzung messen (OVERRIDE-052, SESSION_RULES v2.0, ADR-INDEX-Konsistenz) |
| Formel | **nicht numerisch belegt** — qualitativ/Checklist-basiert (GAP, §4) |
| Eingangsgrößen | OVERRIDE-052-Status (`override_052_is_active()`), Authority-Kette (SESSION_RULES v2.0, 8 Ebenen), ADR-INDEX-Konsistenz (F-01/F-02 gelöst), HDR-001-Status, MC-TC-005-Autorisierung |
| Evidence Sources | MASTER_INDEX §2 M2; G4 §M2; G5 §1; G6 §1; PB-03 (6056f47), G4.5 (B1) |
| Confidence Level | C1 |
| Aktualisierungsregel | bei Governance-Artefakt-Änderungen (SESSION_RULES, ADR-INDEX, OVERRIDE); formale Messung bei Gate-Re-Messung |

### M3 — Session Continuity

| Feld | Inhalt |
|------|--------|
| Metric ID | M3 |
| Definition | Rekonstruierbarkeit einer neuen Session anhand der Dokumente (Fresh-Session-Test) |
| Zweck | Session-Continuity sicherstellen; Lese-Reihenfolge (SESSION_RULES v2.0, 6 Checklist-Quellen) muss neueste Wahrheit erreichen |
| Formel | `SESSION_CONTINUITY_SCORE = Durchschnitt der §2-Rekonstruktions-Targets, unweighted` (SESSION_CONTINUITY_AUDIT §6) — Target-Scores nicht öffentlich (Teil-GAP, §4) |
| Eingangsgrößen | 6 Rekonstruktions-Targets (Zustand, Entscheidungen, Blocker, nächste Schritte, Autoritätsquellen, verbotene Annahmen); Handovers 17/17 (100%); S-07-31 UNKNOWN |
| Evidence Sources | SESSION_CONTINUITY_AUDIT §2/§6; G4 §M3; G5 §1; PB-01 (c29c8b8) |
| Confidence Level | C1 |
| Aktualisierungsregel | bei Handover-/Registry-/Checklist-Änderung; Rerun mit echter Fresh-Session empfohlen (G4 §M3, offen) |

### M4 — Decision Completeness

| Feld | Inhalt |
|------|--------|
| Metric ID | M4 |
| Definition | Vollständigkeit und Reife der Entscheidungs-Erfassung: Registry-Erfassung (K1), Entscheidungs-Reife (K2), Blocker-Status (K3) [G5 §1, G6 §2] |
| Zweck | Entscheidungslandschaft messen; offene Human-/ARB-Entscheidungen (P0-1/P0-2, HDR-001) als limitierenden Faktor sichtbar machen |
| Formel | `K1=100, K2=76, K3=25` → ungewichtet `(100+76+25)/3 = 67`; blocker-gewichtet `0.25·100 + 0.25·76 + 0.5·25 = 56.5`; **M4 = Mittelwert = 62** [C1] |
| Eingangsgrößen | Registry D-001…D-042 + ADR-INDEX kanonisch (K1); 13/17 aktive ADRs akzeptiert, 4 DRAFT 022…025 (K2); 1/4 Blocker prozessiert, P0-1/P0-2/HDR-001 offen (K3) |
| Evidence Sources | G5 §1; G6 §2 (transparente Formel); 05_DECISION_REGISTRY_FOUNDATION (D-036…D-042); G6_01 (ADR-022…025 formal 6/6) |
| Confidence Level | C1 |
| Aktualisierungsregel | **Metrik-Definition gewechselt**: Audit–G4.5 = „Documentation Redundancy" (35/45/50/60), G5+ = „Decision Completeness" (62) — Vergleichbarkeit dokumentiert (G5 §1 Hinweis, R6); neue Messung erst nach RC-1/RC-2 (K3-Hebel) |

### M5 — Knowledge Coverage

| Feld | Inhalt |
|------|--------|
| Metric ID | M5 |
| Definition | Anteil des Chat-abgeleiteten Wissens (S1+S2), das in Repo-Dokumenten (S3–S5) gespiegelt ist [C1] |
| Zweck | Chat-only-Wissen (S2) in Repo-Wissen überführen; Wissens-Lücken (D-033…035) sichtbar machen |
| Formel | Anteils-Formel (Kategorien-Zählung), keine öffentliche Gewichtung (Teil-GAP, §4) |
| Eingangsgrößen | Chat-Kategorien (28.–31.07: 4/5 gespiegelt), ADR-022…025 (DRAFT, im Repo), D-033…D-035 (CHAT_ONLY, kein Plan-Doc) |
| Evidence Sources | MASTER_INDEX §2 M5; G4 §M5; G5 §1; G6 §1; G6_04_REGISTRY_COMPLETION |
| Confidence Level | C1 |
| Aktualisierungsregel | bei Repo-Spiegelung von Chat-Wissen (z.B. Plan-Docs D-033…035 → dann Score-Wirkung messbar); CHAT_ONLY-Markierung bleibt bis Repo-Beleg |

## 3. Historical Measurements (ausschließlich belegte Werte, keine Neuberechnung)

| Gate | Overall | M1 | M2 | M3 | M4 | M5 | Quelle |
|------|---------|----|----|----|----|----|--------|
| Audit-Baseline | **45.2** | 55 | 45 | 41 | 35 (Redundanz) | 50 | MASTER_INDEX §2 [C0/C1] |
| G2 | **61.0** | 78 | 72 | 55 | 45 (Redundanz) | 55 | G2_EXECUTION_VALIDATION §4; G4-Tabelle Δ [C0] |
| G4 | **68.6** | 78 | 72 | 78 | 50 (Redundanz) | 65 | G4_MEASUREMENT_REPORT [C0] |
| G4.5 (Prognose) | **74.4** | 78 | 78 | 78 | 60 (Redundanz) | 78 | G4_5_EXECUTION_RESULT [C0] |
| G5 / G6 (Recheck) | **74.8** | 78 | 78 | 78 | 62 (Decision Completeness) | 78 | G5 §1; G6 §1 [C0] |

**M4-Metrikwechsel (belegt, kein Rechenartefakt):** Spalte M4 vor G5 = „Documentation Redundancy"-Skala (G5 §1 Metrik-Hinweis, R6); ab G5 = „Decision Completeness" (62 = Mittelwert 67/56.5, G6 §2). Historische Werte werden **nicht** umgerechnet.

**Score-Entwicklung:** +29.6 Punkte seit Audit (G5 §2); Ziel: >75 auf allen 5 (nicht erreicht — Overall 74.8, M4 = 62 limitierend).

## 4. Formula Registry

### M1

| Feld | Inhalt |
|------|--------|
| Metric | M1 Repository Health |
| Inputs | uncommitted changes (git status), Duplikationen (ADR ×4, Manuals ×3, `muscal-mvp/`), Truth-Konsistenz (Baseline/Code-Abgleich) |
| Output | 0–100 |
| Beleg | Formel-Struktur [C0] MASTER_INDEX §2 M1; **GAP: Penalty-Gewichtung nicht öffentlich spezifiziert** |

### M2

| Feld | Inhalt |
|------|--------|
| Metric | M2 Governance Consistency |
| Inputs | OVERRIDE-Mechanismen, Authority-Kette, Decision-Records, Konfliktfreiheit |
| Output | 0–100 |
| Beleg | Definition [C1] MASTER_INDEX §2 M2, G4 §M2; **GAP: keine numerische Formel belegt** — Messung Checklist-/Muster-basiert |

### M3

| Feld | Inhalt |
|------|--------|
| Metric | M3 Session Continuity |
| Inputs | 6 Rekonstruktions-Targets (SESSION_CONTINUITY_AUDIT §2), Handover-Abdeckung, Stale-Docs |
| Output | 0–100 |
| Beleg | Formel (unweighted avg) [C1] SESSION_CONTINUITY_AUDIT §6, G4 §M3; **Teil-GAP: Target-Scores nicht veröffentlicht** |

### M4

| Feld | Inhalt |
|------|--------|
| Metric | M4 Decision Completeness |
| Inputs | Registry-Erfassung (K1), ADR-Zustand (K2: 13/17 akzeptiert, 4 DRAFT), Human-Decision-Status (K3: 1/4 prozessiert) |
| Output | 0–100 |
| Beleg | **vollständig** [C0] G6 §2: ungewichtet 67, blocker-gewichtet 56.5, Mittel 62 — keine GAP |

### M5

| Feld | Inhalt |
|------|--------|
| Metric | M5 Knowledge Coverage |
| Inputs | Chat-abgeleitetes Wissen (S1+S2) vs Repo-Spiegelung (S3–S5), Kategorien-Zählung |
| Output | 0–100 |
| Beleg | Definition [C1] MASTER_INDEX §2 M5, G4 §M5; **Teil-GAP: Kategorien-Gewichtung/Zählbasis nicht formalisiert** |

## 5. Evidence Binding

| Metric | Quelle | Evidence Level | Status |
|--------|--------|----------------|--------|
| M1 | MASTER_INDEX §2 M1; G4 §M1; G5 §1; G6 §1; REPOSITORY_CENSUS; MANUAL_RECONCILIATION_FINAL | C0/C1 | aktuell (G6, 01.08) |
| M2 | MASTER_INDEX §2 M2; G4 §M2; G5 §1; G6 §1; SESSION_RULES v2.0 (PB-03); ADR-INDEX kanonisch (G4.5 B1) | C1 | aktuell (G6) |
| M3 | SESSION_CONTINUITY_AUDIT §2/§6; G4 §M3; G5 §1; PB-01 (c29c8b8) | C1 | aktuell (G6) |
| M4 | G5 §1; G6 §2; G6_01 (ADR-022…025); 05_DECISION_REGISTRY_FOUNDATION (D-IDs); DECISION_REGISTRY (K1-Basis) | C1 | aktuell (G6); **Restblocker K3=25** |
| M5 | MASTER_INDEX §2 M5; G4 §M5; G5 §1; G6_04 (D-033…035 chat-only) | C1 | aktuell (G6) |
| Overall | MASTER_INDEX §2 (45.2); G4 (68.6); G5 §1/G6 §1 (74.8) | C0/C1 | aktuell |

## 6. Measurement Rules

| # | Regel |
|---|-------|
| 1 | **Messung wann:** nur bei formaler Gate-Re-Messung (RC-6) oder explizitem Auftrag — nicht bei jeder Doc-Änderung; reine Doku erhöht keinen Score (G6 §1: ±0 durch G6-Vorbereitung) |
| 2 | **Evidence-Pflicht:** jede Score-Änderung erfordert Repo-Evidence C0/C1; CHAT_ONLY (C2) allein begründet keine Erhöhung; Score-Änderung ohne Evidence = Erfindung (verboten, G6-04-Prinzip) |
| 3 | **Formel-Konsistenz:** Messungen erfolgen formel-konsistent zu MASTER_INDEX §2 / G2 / G4 / G5 / G6 (unweighted avg); Abweichung nur mit dokumentierter Formel-Änderung (M4-Metrikwechsel: G5-R6 dokumentiert) |
| 4 | **Versionierung:** Messwerte werden in Gate-Reports mit Audit-ID + Datum versioniert (G4/G5 in KNOWLEDGE_FOUNDATION/, G6-Recheck im Repo `docs/audit/G6_READINESS_RECHECK.md`); Reihenfolge-Kette Audit → G2 → G4 → G4.5 → G5 → G6 ist Referenz |
| 5 | **Keine rückwirkende Anpassung:** historische Messungen bleiben unverändert (45.2/61.0/68.6/74.4/74.8); keine Retrospektiv-Korrektur, keine Neuberechnung (dieses Dokument übernimmt Werte, verändert sie nicht) |
| 6 | **Keine Score-Optimierung durch Interpretation:** M4 = 62 (Mittelwert) wird beibehalten; kein „Zufalls-GO" über ungewichtete 67/75.8 (G6 §2) |

## 7. Known Gaps (Status unverändert — Übernahme aus G5 §3/§4, G6 §3)

| Gap | Status | Betroffene Metrik | Quelle |
|-----|--------|-------------------|--------|
| M4-Restblocker: K3 = 25 (1/4 prozessiert) | offen — P0-1/P0-2 + HDR-001 unentschieden | M4 | G6 §2/§3 |
| P0-1 Graph-OS Reconstruction / P0-2 Watchdog-Persistenz | **PENDING HUMAN** (RC-1, PA-08/PA-09; kein DECIDED, kein DEFERRED) | M4 (K3), Readiness-Gate | G5 §3 B5; PROJECT_STATE:45-49 |
| HDR-001 Architecture Council | **HUMAN REQUIRED** (RC-2; blockiert HDR-002…004, 9 Dependencies; D-023) | M4 (K3), M2 | G5 §3 B6; PROJECT_STATE:116 |
| FL-01a (19 flaky Tests, globale Singletons `_UTR`, `set_global_utr`, `set_global_event_store`) | dokumentiert (D-040), Fix deferred, ARB-Freigabe nötig (D-042-Global-State-ADR, RC-3) | M1 (Testlage) | G5 §3 B7; FL01A_FLAKINESS_REGISTER |
| ADR-Review ADR-022…025 (formal 6/6, NOT READY, DRAFT) | offen (RC-4a, ARB; Matrix G7-03) | M4 (K2) | G6_01; ADR_REVIEW_MATRIX |
| TC-H3 (3 RESOLVED / 2 PARTIAL / 3 OPEN) | offen (RC-5; v0.8, F-03, Manual-Triple) | M4-Redundanz-Rest (R4), M1 | TC_H3_CLOSURE (G6-03) |
| M3-Fresh-Session-Rerun | empfohlen, nicht durchgeführt | M3 (Bestätigung) | G4 §M3 |

## 8. Validation Section

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Alle Zahlen besitzen Quelle | ✅ 45.2/61.0/68.6/74.4/74.8 + Metrik-Werte mit Gate-Report-Referenz (Abschnitt 3) |
| Keine neue Interpretation | ✅ Werte/Formeln wörtlich aus MASTER_INDEX/G4/G5/G6; keine Neuberechnung |
| Keine Entscheidungen erzeugt | ✅ kein ID/Status/Datum neu gesetzt; Blocker §7 unverändert |
| CHAT_ONLY bleibt CHAT_ONLY | ✅ D-033…D-035, D-010…D-014 unverändert C2/markiert; kein Score-Effekt |
| Markdown only | ✅ docs/audit/18_METRIC_REGISTRY_FOUNDATION.md |
| Formel-GAPs ehrlich markiert | ✅ M1 (Gewichtung), M2 (keine Formel), M3 (Target-Scores), M5 (Gewichtung) als GAP/Teil-GAP; M4 vollständig belegt |

---

*Erstellt als reine Metrik-Dokumentation aus belegten Gate-Reports. Registry-Werte: Stand G6 (01.08.2026) — keine Änderung durch dieses Dokument.*
