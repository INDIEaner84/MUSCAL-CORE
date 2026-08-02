# KF-3 Decision Queue

- Datum: 02.08.2026
- Zweck: Vorbereitung der offenen Entscheidungsphase (read-only; keine Empfehlungen erzwungen, keine Entscheidungen getroffen, keine Scores berechnet)
- Basis: ausschließlich bestehende Evidence (G4.5/G5/G6/G7, DECISION_CLOSURE_PACKAGE, ADR_REVIEW_MATRIX, FL01A_FLAKINESS_REGISTER, HDR-001, PROJECT_STATE, Doc 12/16/19)

---

## RC-1 — P0-1 / P0-2

| Feld | Inhalt |
|---|---|
| **ID** | RC-1 (Gate-Bedingung B5) |
| **Problem** | P0-1: GraphState/SphereState rein in-memory, kein Rebuild-Mechanismus (Graph-OS-Rekonstruktion). P0-2: Watchdog erkennt Orphans, persistiert aber keine Events in den EventStore. |
| **Evidence** | MC-TC-007 Phase H ❌ FAIL + Phase F ⚠️ PASS* (384/384 Tests sonst); DECISION_CLOSURE_PACKAGE §RC-1 (Optionen A–D je P0; A: Rebuild-Service aus stored_events / `_force_fail_orphan()` via EventStore.append(), jeweils features/-Pfad, D-006-konform); PA-08/PA-09; features/monitoring/execution_watchdog.py:96-119; G4.5 B5; G5 R1 (HIGH); P0-2-Option B adressiert als einzige das Folge-Finding C03 (Doppelalarme — Faktenlage, G7-01, keine Empfehlung) |
| **Aktueller Status** | **PENDING HUMAN** (PROJECT_STATE-Update 01.08) |
| **Entscheider** | ARB / Human (Project Governance) — gleichrangig (G7-01: „Entscheider: ARB / Human (Project Governance) — nicht dieser Agent"); G4.5 §7 B5/B7 → ARB |
| **Abhängigkeiten** | RC-6 (Mess-Gate: siehe RC-6); keine Dokument-Blocker mehr (20/20); D-033…D-035 = separater Doku-/Roadmap-Cluster, keine automatische Abhängigkeit (M-2-Korrektur) |
| **Mögliche nächste Aktion** | Option A–D wählen oder als ARCHITECTURE CHANGE deklarieren (G7-01) |
| **Frist** | je Option: nicht definiert (offene Frage im G7-01-Brief: „Welche Option (A/B/C/D) gilt … und welche Frist gilt für die gewählte Option?") |
| **Risiko bei Nichtentscheidung** | Produktions-Restart-Risiko (G5 R1 HIGH); M4-Freshness/RC-6 bleibt aus; Gate-Status bleibt CONDITIONAL |

## RC-2 — HDR-001 (Manual Authority)

| Feld | Inhalt |
|---|---|
| **ID** | RC-2 (Gate-Bedingung B6) |
| **Problem** | Manual-Autorität (M-0.7) ohne formale Entscheidung; Deadlock der Folge-HDRs |
| **Evidence** | docs/governance/HDR-001_DECISION_RECORD.md (20.07); D-023 (DECISION_REGISTRY); G4.5 B6 (READY FOR HUMAN DECISION); G5 R2 (HIGH); G7-02 (Optionen A–D) |
| **Aktueller Status** | **HUMAN REQUIRED** |
| **Entscheider** | Human (Projektleitung) — G4.5 §7 B6; G5 RC-2 |
| **Abhängigkeiten** | HDR-002…004 (3 HDRs seit 20.07 blockiert); RC-6; Manual-Kanon (Doc 07 TC-Konflikte) |
| **Mögliche nächste Aktion** | Optionen A–D aus G7-02 entscheiden; Registry-/PROJECT_STATE-Update |
| **Risiko bei Nichtentscheidung** | HDR-Deadlock (G5 R2 HIGH); v0.8-Manual-Autorität bleibt ungeregelt (TC-H3) |

## RC-3 — FL-01a / D-042

| Feld | Inhalt |
|---|---|
| **ID** | RC-3 (Gate-Bedingung B7) |
| **Problem** | 19 order-dependent Pytest-Failures (Flakiness) durch globale Singletons; Global-State-ADR-Entwurf (D-042) ohne Akzeptanz |
| **Evidence** | FL01A_FLAKINESS_REGISTER; G2 §FL-01a (2× reproduziert: 23 failed / 2.343 passed / 1 skipped; Einzelsuite 177/177; Root-Cause C1: features/tools/tools.py:9-24, features/tool_runtime/tool_runtime.py:37-42 und :28-42); GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT (Optionen A–C; A = Test-Fixtures test-only, empfohlen im Entwurf); D-040/D-042; G5 RC-3 (ARB/DOC) |
| **Aktueller Status** | Deferred; Fix-Freigabe offen; D-042 kein ACCEPTED |
| **Entscheider** | ARB (G5 RC-3 ARB/DOC) |
| **Abhängigkeiten** | Test-Governance (Doc 10 §5: 19 flaky / 2.347 passed / 1 skipped); Baseline-Stabilität (EXPECTED_TOTAL 470) |
| **Mögliche nächste Aktion** | Freigabe Fixture-Fix (test-only) oder dauerhafte Dokumentations-Entscheidung (D-042) |
| **Risiko bei Nichtentscheidung** | CI-Wiederholbarkeit ungesichert, Baseline-Drift (G5 R3 MEDIUM) |

## RC-4a — ADR-022…025

| Feld | Inhalt |
|---|---|
| **ID** | RC-4a (ADR-Readiness-Review) |
| **Problem** | 4 ADR-Entwürfe (MUSCAL 2.0, Agent, Compiler, Tool-Integration) ohne Review/Akzeptanz |
| **Evidence** | ADR_REVIEW_MATRIX (G7-03: NICHT GESTARTET; Datei ADR_REVIEW_MATRIX.md im Repo vorhanden, lesbar leer — Referenzstatus nur über Doc 04/16-Kette, kein Inhalt angenommen); DECISION_CLOSURE_PACKAGE §RC-4 (NOT READY: Turnier-Primärquelle nicht im Repo, Migrationsbewertung fehlt); ADR-022…025 DRAFT im Repo (a977091); Basis D-010…D-014 (CHAT_ONLY, C2) |
| **Aktueller Status** | **NICHT GESTARTET** (DRAFT bleibt DRAFT; KF-03: keine Akzeptanzannahmen) |
| **Entscheider** | ARB |
| **Abhängigkeiten** | Turnier-Primärquelle (MC-015-Chat 25.07, S2) — Klärung offen, ob beschaffbar (versteckte Annahme entfernt, L-9-Korrektur); Migrationsbewertung (ADR-001-Bezug); Architektur-Dokumente Doc 04/14 (DRAFT-Knoten); Review-Abhängigkeiten je ADR (nur Feststellung, keine Bewertung/Annahme): ADR-022 — MUSCAL-2.0-Architecture-Scope (Turnier-Primärquelle nicht im Repo; Migrationsbewertung/ADR-001-Bezug fehlt); ADR-023 — Security Model (unzureichend spezifiziert); ADR-024 — P5 / MC-TC-007-Trust-Governance-Interaktion (NO-GO-Befund offen); ADR-025 — RFC-Process (nicht definiert) |
| **Mögliche nächste Aktion** | Review mit vorliegender Matrix; je ADR festgestellte Abhängigkeit klären (Primärquelle, Security Model, Trust-Governance-Interaktion, RFC-Process); Primärquelle einbringen oder Migrationsbewertung ergänzen |
| **Risiko bei Nichtentscheidung** | MUSCAL-2.0-Richtung unverbindlich (G5 M5-Rest: chat-only); DRAFT-Status verlängert sich; ADR-Akzeptanz blockiert Folge-Architektur-Dokumente |

## RC-5 — Offene Foundation Gaps

| Feld | Inhalt |
|---|---|
| **ID** | RC-5 (M4-Restpunkte) |
| **Problem** | F-03 (specs/adrs/-Leiche), D-033…D-035-Plan-Docs (separater Doku-/Roadmap-Cluster, Status PLANNED + CHAT_ONLY), v0.8-Manual-Erzeugung (TC-H3); KIR-Repo-Status = Knowledge-Gap KG-01 (Doc 19; G7 §4) — kein M4-Restpunkt, keine Decision-Queue-Aufnahme (M-3-Korrektur); weitere Einzelgaps in Doc 19 (KG-01…KG-19) |
| **Evidence** | DECISION_CLOSURE_PACKAGE §RC-5 (Statusliste: D-033/034/035, v0.8, F-03, TC-H3); G6-01 (F-03); G6_04_REGISTRY_COMPLETION (D-033…D-035 PLANNED, chat-only, C2, ohne Repo-Artefakt); TECHNICAL_MANUAL_CONFLICT_REPORT (B5/B6, TC-H3); Doc 19 KG-01/KG-05/KG-10/KG-11 |
| **Aktueller Status** | offen (je Gap unverändert, Doc 19) |
| **Entscheider** | DOC (Governance-Konsolidierung; G4.5 §7 B1–B4 DOC-only); keine ARB-Entscheidung erforderlich (keine Kopplung an RC-1) |
| **Abhängigkeiten** | B5/B6 (v0.8/TC-H3); D-033…D-035: keine automatische Abhängigkeit von RC-1 (M-2-Korrektur, G6_04_REGISTRY_COMPLETION — kein Repo-Artefakt, kein RC-1-Bezug); keine Review-Blocker für F-03 (reine Doku-Prüfung) |
| **Mögliche nächste Aktion** | F-03-Inhaltsprüfung; v0.8-Erzeugung nach B5/B6-Klärung; D-033…D-035-Plan-Dokumente in docs/governance/ (Phase C, DOC, §RC-5) |
| **Risiko bei Nichtentscheidung** | M4-Restlücke bleibt; Manual-Autorität veraltet (TC-H3 PARTIAL); Leiche specs/adrs/ bleibt referenzierbar (F-03) |

## D-033…D-035 — Doku-/Roadmap-Cluster (M-2-Korrektur: entkoppelt von RC-1)

| Feld | Inhalt |
|---|---|
| **ID** | D-033, D-034, D-035 (B3-Anteil; ursprünglich als Teil von RC-5 geführt) |
| **Kategorie** | Documentation/Roadmap Cluster (Status PLANNED + CHAT_ONLY, C2; kein Repo-Artefakt) |
| **Problem** | Plan-Dokumente zu den D-033…D-035-Themen stehen aus; keine RC-1-Kopplung (G7-01 verweist nicht auf D-033…D-035) |
| **Evidence** | DECISION_CLOSURE_PACKAGE §RC-5 (Statusliste); G6_04_REGISTRY_COMPLETION (D-033…D-035 PLANNED, chat-only, C2, ohne Repo-Artefakt); Doc 16 B3/RC-1 ohne D-033…D-035-Bezug |
| **Aktueller Status** | PLANNED + CHAT_ONLY |
| **Entscheider** | DOC (Phase C, §RC-5) |
| **Abhängigkeiten** | keine automatische Abhängigkeit von RC-1 (M-2-Korrektur); kein Human-Entscheidungsbedarf |
| **Mögliche nächste Aktion** | Plan-Dokumente in docs/governance/ (Phase C) |
| **Risiko bei Nichtentscheidung** | M4-Restlücke bleibt (kein Score-Einfluss, chat-only) |

## RC-6 — Re-Messung

| Feld | Inhalt |
|---|---|
| **ID** | RC-6 (finale Gate-Checkliste) |
| **Problem** | M1…M5-Re-Messung ausstehend; formeller Score-Fortschritt (>75) nicht festgestellt |
| **Evidence** | G6-05 (Recheck ±0); Doc 18 §2 (Aktualisierungsregel: neue Messung erst nach RC-1/RC-2); DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt (RC-1 + RC-4 + RC-5); G6_READINESS_RECHECK §1-M4 („ADR-Review (RC-4a) → K2"); G4/G4.5-Prognose-Mechanik (nicht neu berechnet) |
| **Aktueller Status** | ausstehend; RC-6 = **vollständiges Mess-Gate** — Kennzeichnung (H-1-Korrektur): RC-1/RC-2 = Entscheidungsbereitschaft, RC-6 = formale Re-Messung nach RC-1 + RC-2 + RC-4a (ADR-Review abgeschlossen) + RC-5 (Dokumentationsreste bewertet) |
| **Entscheider** | je Messpunkt (Verantwortlich laut §RC-6): M1 Governance-Team, M2 ARB/Human, M3 Doku-Team, M4 ARB/Human+Doku; Mess-Protokoll ARB (G6-Frame) — L-2-Korrektur (wörtlicher Beleg) |
| **Abhängigkeiten** | RC-1, RC-2 (Mess-Voraussetzung, Doc 18 §2 — notwendige, nicht hinreichende Bedingung), RC-4a (ADR-Review abgeschlossen), RC-5 (Dokumentationsreste bewertet) |
| **Mögliche nächste Aktion** | Nach RC-1/RC-2/RC-4a/RC-5: formale Re-Messung M1–M5 nach G6-Recheck-Protokoll (§RC-6-M4) |
| **Risiko bei Nichtentscheidung** | Keine formal aktualisierte Score-Lage; Gate-Status bleibt CONDITIONAL (G4.5/G7-04) |

---

## MC-TC-005 — Authorization Decision (M-1-Korrektur: ergänzt aus KF2_COMPLETION_REPORT)

| Feld | Inhalt |
|---|---|
| **ID** | MC-TC-005 (Authorization) |
| **Kategorie** | Authorization Decision |
| **Problem** | Scope-Erweiterung (MC-TC-005) ohne ARB-Mandat; Autorisierung ausstehend |
| **Evidence** | MC-TC-005.1-CLOSURE-TRUTH-AUDIT.md; MC-TC-005.3-SINGLE-EVENT-AUTHORITY-CONSOLIDATION.md (COMPLETE, 51 Tests); REFERENCE_GRAPH N-AUD; Doc 15 §7; Doc 18 M2-Eingangsgröße („MC-TC-005-Autorisierung"); DECISION_CLOSURE_PACKAGE §RC-6-M2 („MC-TC-005-Klärung", ARB/Human); KF2_COMPLETION_REPORT §4 — nur vorhandene Artefakte, kein Implementierungsclaim (C0/C1) |
| **Aktueller Status** | NOT AUTHORIZED |
| **Entscheider** | ARB (Klären/Autorisieren, §RC-6-M2) |
| **Abhängigkeiten** | M2-Eingangsgröße (Doc 18 M2); KF2_COMPLETION_REPORT §4 |
| **Mögliche nächste Aktion** | Autorisierungs-/Klärungsentscheidung ARB |
| **Risiko bei Nichtentscheidung** | M2-Eingangsgröße bleibt ungeklärt; Autorisierungsstatus bleibt offen |

## Bridge Governance / KG-12 — Governance Decision (M-1-Korrektur: ergänzt aus Doc 17/Doc 19)

| Feld | Inhalt |
|---|---|
| **ID** | Bridge Governance (KG-12) |
| **Kategorie** | Governance Decision |
| **Problem** | 104 untracked Artefakte (docs/bridge/handovers/handover_*.{md,yaml}) ohne Governance-Beschluss und ohne Lesepfad |
| **Evidence** | Doc 17 (Artefakt-Inventory 104, git status, read-only); Doc 19 KG-12; G7 §4; G4-M1; DECISION_CLOSURE_PACKAGE §RC-6-M1-Messpunkt („untracked (Bridge-Governance)"); Doc 18 M1-Eingangsgröße; KF2_COMPLETION_REPORT §4 — kein Beschluss (OPEN) |
| **Aktueller Status** | OPEN (kein Beschluss) |
| **Entscheider** | Human/ARB (Muster G7-01/G7-02, Doc 17 §7 — keine Festlegung durch KF) |
| **Abhängigkeiten** | M1-Messpunkt (nicht blockierend, M1 = 78) |
| **Mögliche nächste Aktion** | Beschluss Artefakt-Governance (Tracking/Lesepfad) |
| **Risiko bei Nichtentscheidung** | Wissensverlust / keine Autorität für Bridge-Artefakte (Doc 17 §8) |

---

*Keine Scores berechnet; alle Angaben mit Quelle; Entscheider, Status und Abhängigkeiten wörtlich aus den genannten Artefakten übernommen (Detail: KF3_DECISION_DEPENDENCY_GRAPH.md, KF3_READINESS_REPORT.md).*
