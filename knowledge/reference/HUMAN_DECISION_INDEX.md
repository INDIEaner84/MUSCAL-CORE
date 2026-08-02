# HUMAN_DECISION_INDEX — Einstiegsseite für Entscheider

- Datum: 02.08.2026
- Zweck: Eine Einstiegsseite für Entscheider — offene Entscheidungen, benötigter Entscheider, Entscheidungsreife, relevante Quellen, Abhängigkeiten, Nichtentscheidungs-Risiko (read-only; keine Empfehlung, keine Entscheidung, keine Statusänderung)
- Basis: KF3_DECISION_QUEUE.md, KF3_DECISION_DEPENDENCY_GRAPH.md, KF3_READINESS_REPORT.md, DECISION_CLOSURE_PACKAGE.md, G7-01/G7-02, ADR_REVIEW_MATRIX.md, 16_BLOCKER_REGISTRY_FOUNDATION.md
- Status: **created, not committed (external KF layer)**

---

## Übersicht

| ID | Entscheidung | Status (unverändert) | Entscheider | Reife | Nichtentscheidungs-Risiko |
|----|--------------|----------------------|-------------|-------|---------------------------|
| RC-1 | P0-1 Graph-OS-Rekonstruktion + P0-2 Watchdog-Persistenz (Optionen A–D je P0) | **PENDING HUMAN** | ARB / Human (gleichrangig) | entscheidungsfähig (Entscheidungsbereitschaft) | Produktions-Restart-Risiko (G5 R1 HIGH); M4-Freshness/RC-6 bleibt aus; Gate-Status bleibt CONDITIONAL |
| RC-2 | HDR-001 Architecture Council annehmen (Optionen A–D) | **HUMAN REQUIRED** | Human (Projektleitung) | entscheidungsfähig (seit 20.07 offen) | HDR-Deadlock (G5 R2 HIGH); HDR-002…004 blockiert; v0.8-Manual-Autorität ungeregelt (TC-H3) |
| RC-3 | FL-01a-Fix / Global-State-ADR D-042 (Optionen A–C) | Deferred; Fix-Freigabe offen; D-042 kein ACCEPTED | ARB (G5 RC-3 ARB/DOC) | Entscheidungsentwurf vorliegend | CI-Wiederholbarkeit ungesichert; Baseline-Drift (G5 R3 MEDIUM) |
| RC-4a | ADR-022…025-Review (Status-Klärung, keine Auto-Akzeptierung) | **NICHT GESTARTET** (NOT READY) | ARB | Review-Struktur fertig (G7-03-Matrix); Input unvollständig | MUSCAL-2.0-Richtung unverbindlich (chat-only); ADR-Akzeptanz blockiert Folge-Architektur-Dokumente |
| RC-5 | M4-Restpunkte: F-03, v0.8-Manual (TC-H3) + D-033…D-035-Cluster | offen (PLANNED + CHAT_ONLY) | DOC (Governance-Konsolidierung) | arbeitsfähig ohne Human-Entscheidung | M4-Restlücke bleibt; Manual-Autorität veraltet (TC-H3 PARTIAL); Leiche specs/adrs/ bleibt referenzierbar (F-03) |
| RC-6 | Formale Re-Messung M1…M5 (vollständiges Mess-Gate) | ausstehend (blockiert durch RC-1/RC-2/RC-4a/RC-5) | je Messpunkt: M1 Governance-Team, M2 ARB/Human, M3 Doku-Team, M4 ARB/Human+Doku | Mess-Protokoll dokumentiert (§RC-6, G6-Frame) | Keine formal aktualisierte Score-Lage; Gate-Status bleibt CONDITIONAL (G4.5/G7-04) |

## Detail je Entscheidung

### RC-1 — P0-1 / P0-2 (Graph-OS / Watchdog)

- **Benötigter Entscheider:** ARB / Human (Project Governance) — gleichrangig (G7-01: „Entscheider: ARB / Human (Project Governance) — nicht dieser Agent"); G4.5 §7 B5/B7 → ARB.
- **Entscheidungsreife:** **Entscheidungsbereitschaft** — Entscheidungsbrief G7-01 mit Optionen A–D je P0 liegt vor; Projektzustand auf 01.08 aktualisiert (PROJECT_STATE); technischer Befund zertifizierungsgestützt (MC-TC-007 Phase H ❌ FAIL, Phase F ⚠️ PASS*; 384/384 Tests sonst).
- **Relevante Quellen:** `docs/audit/G7_01_RC1_DECISION_BRIEFS.md`; DECISION_CLOSURE_PACKAGE §RC-1; KF3_DECISION_QUEUE §RC-1; 16_BLOCKER_REGISTRY §5/§6 (PA-08, PA-09); MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67,71-76; GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md; features/monitoring/execution_watchdog.py:96-119.
- **Abhängigkeiten:** RC-6 (Mess-Gate, siehe dort); keine Dokument-Blocker (20/20); D-033…D-035 = separater Cluster, keine automatische Abhängigkeit (KF3-M-2-Korrektur).
- **Nichtentscheidungs-Risiko:** Produktions-Restart-Risiko (G5 R1 HIGH); M4-Freshness/RC-6 bleibt aus; Gate-Status bleibt CONDITIONAL (G4.5/G7-04).
- **Frist:** je Option nicht definiert (offene Frage im G7-01-Brief).

### RC-2 — HDR-001 (Manual Authority)

- **Benötigter Entscheider:** Human (Projektleitung/Programm-Owner) — verbindliche Entscheidung (HDR-001_DECISION_RECORD §5); G4.5 §7 B6; G5 RC-2. ARB nur fachliche Vorprüfung der Auflagen, falls gewünscht.
- **Entscheidungsreife:** Entscheidungsunterlage vollständig — Decision Record READY FOR HUMAN DECISION seit 20.07 (12 Tage offen per 01.08); Optionen A–D (G7-02); D-023 „documented; unresolved since 20.07".
- **Relevante Quellen:** `docs/governance/HDR-001_DECISION_RECORD.md`; DECISION_CLOSURE_PACKAGE §RC-2; 05_DECISION_REGISTRY_FOUNDATION (D-023); 16_BLOCKER_REGISTRY §5/§7; KF3_DECISION_QUEUE §RC-2; PROJECT_STATE.md:116-119.
- **Abhängigkeiten:** HDR-002…004 (3 HDRs seit 20.07 blockiert, 9 Dependencies); RC-6 (Mess-Gate); Manual-Kanon (Doc 07 TC-Konflikte); M2-Eingangsgröße (Doc 18 M2).
- **Nichtentscheidungs-Risiko:** HDR-Deadlock (G5 R2 HIGH); v0.8-Manual-Autorität bleibt ungeregelt (TC-H3).

### RC-3 — FL-01a / D-042 (Global-State)

- **Benötigter Entscheider:** ARB (G5 RC-3: ARB/DOC).
- **Entscheidungsreife:** Entscheidungsentwurf GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT (Optionen A–C) liegt vor; nicht akzeptiert; Flakiness-Root-Cause C1-dokumentiert (globale Singletons).
- **Relevante Quellen:** FL01A_FLAKINESS_REGISTER.md; G2 §FL-01a; GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT.md; DECISION_CLOSURE_PACKAGE §RC-3; 05_DECISION_REGISTRY_FOUNDATION (D-040, D-042); 16_BLOCKER_REGISTRY §8; KF3_DECISION_QUEUE §RC-3.
- **Abhängigkeiten:** Test-Governance (Doc 10 §5: 19 flaky / 2.347 passed / 1 skipped); Baseline-Stabilität (EXPECTED_TOTAL 470, D-041).
- **Nichtentscheidungs-Risiko:** CI-Wiederholbarkeit ungesichert; Baseline-Drift (G5 R3 MEDIUM).

### RC-4a — ADR-022…025 Review

- **Benötigter Entscheider:** ARB (Review-Runde; G4.5 §7 B4; Eingangsdaten-Klärung D-012/D-013 über B5; ADR-Folgeprozess über B3).
- **Entscheidungsreife:** NICHT GESTARTET (NOT READY, §RC-4): Turnier-Primärquelle nicht im Repo; Migrationsbewertung fehlt; Security Model unzureichend; Trust-Governance-NO-GO offen; RFC-Prozess nicht definiert. Review-Struktur: ADR_REVIEW_MATRIX (G7-03) mit Prüfmatrix + Review-Protokoll.
- **Relevante Quellen:** `docs/audit/ADR_REVIEW_MATRIX.md`; DECISION_CLOSURE_PACKAGE §RC-4; G6_01_ADR_CLOSURE_PREPARATION.md; spec/ADR-022…025; 05_DECISION_REGISTRY_FOUNDATION (D-010…D-014); KF3_DECISION_QUEUE §RC-4a.
- **Abhängigkeiten:** Turnier-Primärquelle (MC-015-Chat 25.07, S2) — Klärung offen, ob beschaffbar; Migrationsbewertung (ADR-001-Bezug); Architektur-Dokumente Doc 04/14 (DRAFT-Knoten); Review-Abhängigkeiten je ADR (siehe ADR_REVIEW_PACKET.md).
- **Nichtentscheidungs-Risiko:** MUSCAL-2.0-Richtung unverbindlich (G5 M5-Rest: chat-only); DRAFT-Status verlängert sich; ADR-Akzeptanz blockiert Folge-Architektur-Dokumente.

### RC-5 — M4-Restpunkte (inkl. D-033…D-035-Cluster)

- **Benötigter Entscheider:** DOC (Governance-Konsolidierung; G4.5 §7 B1–B4 DOC-only); keine ARB-Entscheidung erforderlich (KF3-M-2-Korrektur: keine Kopplung an RC-1).
- **Entscheidungsreife:** arbeitsfähig ohne Human-Entscheidung; Items unverändert (F-03, v0.8/TC-H3, D-033…D-035 PLANNED + CHAT_ONLY, C2; KIR = KG-01, kein RC-5-Punkt).
- **Relevante Quellen:** DECISION_CLOSURE_PACKAGE §RC-5 (Statusliste); G6_04_REGISTRY_COMPLETION.md; TECHNICAL_MANUAL_CONFLICT_REPORT.md (TC-H3); Doc 19 KG-01/KG-05/KG-10/KG-11; KF3_DECISION_QUEUE §RC-5 + D-033…D-035-Cluster.
- **Abhängigkeiten:** B5/B6 (v0.8/TC-H3); keine automatische Abhängigkeit von RC-1 (M-2-Korrektur).
- **Nichtentscheidungs-Risiko:** M4-Restlücke bleibt; Manual-Autorität veraltet (TC-H3 PARTIAL); Leiche specs/adrs/ bleibt referenzierbar (F-03).

### RC-6 — Formale Re-Messung (Mess-Gate)

- **Benötigter Entscheider:** je Messpunkt (Verantwortlich laut §RC-6): M1 Governance-Team, M2 ARB/Human, M3 Doku-Team, M4 ARB/Human+Doku; Mess-Protokoll ARB (G6-Frame).
- **Entscheidungsreife:** Mess-Protokoll und Mess-Voraussetzungen dokumentiert (Doc 18 §2, G6-05, G6_READINESS_RECHECK, 18_METRIC_REGISTRY_FOUNDATION); Kennzeichnung: RC-6 = **vollständiges Mess-Gate** (nicht Entscheidungsbereitschaft).
- **Relevante Quellen:** DECISION_CLOSURE_PACKAGE §RC-6 (Messpunkte M1–M5); G6_READINESS_RECHECK.md; 18_METRIC_REGISTRY_FOUNDATION.md; G6-05; KF3_DECISION_QUEUE §RC-6; KF3_READINESS_REPORT §2.2.
- **Abhängigkeiten:** RC-1 abgeschlossen + RC-2 abgeschlossen + RC-4a (ADR-Review abgeschlossen) + RC-5 (Dokumentationsreste bewertet) — formale Re-Messung erst danach (§RC-6-M4-Messpunkt, G6-Recheck-M4; H-1-Korrektur).
- **Nichtentscheidungs-Risiko:** Keine formal aktualisierte Score-Lage; Gate-Status bleibt CONDITIONAL (G4.5/G7-04).

## Weitere offene Punkte (aus KF3-Queue, kein Gate-Blocker)

| ID | Entscheidung | Status | Entscheider | Nichtentscheidungs-Risiko |
|----|--------------|--------|-------------|---------------------------|
| MC-TC-005 | Autorisierung der Scope-Erweiterung | NOT AUTHORIZED | ARB (Klären/Autorisieren, §RC-6-M2) | M2-Eingangsgröße bleibt ungeklärt |
| Bridge Governance / KG-12 | Governance-Beschluss für 104 untracked Artefakte | OPEN (kein Beschluss) | Human/ARB (keine Festlegung durch KF) | Wissensverlust / keine Autorität für Bridge-Artefakte (Doc 17 §8) |
| G7-02-Artefaktstatus | „G7-02" ohne auffindbare Datei (belegt via HDR-001_DECISION_RECORD + Doc 05 D-023) | Klärung offen (KF3-L-7: KEIN_ZUGRIFF) | Human/ARB | Referenzierungsgenauigkeit |

## Lesereihenfolge für Entscheider

1. Dieser Index → 2. KF3_DECISION_QUEUE.md (Detail-Status je RC) → 3. je Entscheidung: RC1_FINAL_DECISION_BRIEF.md bzw. RC2_HDR001_FINAL_DECISION_BRIEF.md → 4. ADR_REVIEW_PACKET.md (RC-4a) → 5. RC6_MEASUREMENT_GATE_CHECKLIST.md (RC-6) → 6. KF3_DECISION_DEPENDENCY_GRAPH.md (Kanten) → 7. KF3_CORRECTION_REPORT.md (H-1/M-1…M-4-Stand)

## Validation

- Read-only: keine Entscheidung getroffen, keine Empfehlung, keine Statusänderung, keine Score-Berechnung; alle Aussagen mit Quelle (G4.5/G5/G6/G7, DECISION_CLOSURE_PACKAGE, HDR-001, ADR_REVIEW_MATRIX, Registries).
- Status wörtlich übernommen: PENDING HUMAN, HUMAN REQUIRED, Deferred, NICHT GESTARTET (NOT READY), offen, ausstehend, NOT AUTHORIZED, OPEN, PLANNED + CHAT_ONLY.
