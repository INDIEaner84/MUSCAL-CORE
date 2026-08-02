# KF-3 Correction Report

- Datum: 02.08.2026
- Anlass: KF3_INDEPENDENT_REVIEW_REPORT.md (0 CRITICAL · 1 HIGH · 4 MEDIUM · 10 LOW)
- Umfang: H-1 + M-1…M-4 vollständig; L-2/L-3/L-4/L-6/L-8/L-9 umgesetzt; L-1/L-5/L-7/L-10 als NICHT BEHEBBAR / KEIN_AKTION dokumentiert (jeweils mit Begründung)
- Status: **created, not committed (external KF layer)** — Commit-Message der nächsten KF-Batch: `KF3 correction wave: resolve review findings H-1 M-1..M-4` (KNOWLEDGE_FOUNDATION ist bewusst außerhalb des MUSCAL CORE Git-Repos; kein Spiegeln, kein neues Repo)

---

## 1. Umgesetzte Korrekturen

| Finding | Datei | Änderung (vorher → nachher) | Quelle |
|---|---|---|---|
| H-1 | KF3_READINESS_REPORT.md §2.2, §3 | RC-6 „ausführbar unmittelbar nach RC-1/RC-2" → **vollständiges Mess-Gate**: formale Re-Messung erst nach RC-1 + RC-2 + RC-4a (ADR-Review abgeschlossen) + RC-5 (Dokumentationsreste bewertet); Kennzeichnung Entscheidungsbereitschaft (RC-1/RC-2) vs. Mess-Gate (RC-6); keine Prognose als Fakt | DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt (RC-1 + RC-4 + RC-5), G6_READINESS_RECHECK §1-M4 („ADR-Review (RC-4a) → K2"), Doc 18 §2 (notwendige, nicht hinreichende Bedingung) |
| H-1 | KF3_DECISION_QUEUE.md §RC-6 | Status/Abhängigkeiten/Aktion auf Mess-Gate-Semantik umgestellt; Readiness §2.3-Konsequenz korrigiert (RC-4a Bestandteil des Mess-Gates; RC-1/RC-2/RC-3 davon unabhängig) | s. o. |
| M-1 | KF3_DECISION_QUEUE.md | Neue Einträge **„MC-TC-005 — Authorization Decision"** (Kategorie Authorization Decision, Status NOT AUTHORIZED, Evidence MC-TC-005.1/.3, REFERENCE_GRAPH N-AUD, Doc 15 §7, Doc 18 M2, §RC-6-M2, KF2_COMPLETION_REPORT §4; kein Implementierungsclaim C0/C1) und **„Bridge Governance / KG-12"** (Kategorie Governance Decision, Status OPEN, Evidence Doc 17, Doc 19 KG-12, G7 §4, G4-M1, §RC-6-M1, Doc 18 M1; kein Beschluss) | KF2_COMPLETION_REPORT §4, DECISION_CLOSURE_PACKAGE §RC-6-M1/M2, Doc 15 §7, Doc 17 §7/§8 |
| M-2 | KF3_DECISION_QUEUE.md §RC-1/§RC-5 | Kopplung „RC-1 → D-033…D-035" entfernt; neuer separater Cluster **„D-033…D-035 — Doku-/Roadmap-Cluster"** (Status PLANNED + CHAT_ONLY, C2, ohne Repo-Artefakt; keine automatische Abhängigkeit von RC-1) | G6_04_REGISTRY_COMPLETION (PLANNED, chat-only, C2, ohne Repo-Artefakt); G7-01 ohne D-033…35-Bezug; Doc 16 B3 ohne Beleg |
| M-2 | KF3_DECISION_DEPENDENCY_GRAPH.md | Graph-Zeile + Kante „RC-5 → RC-1 (Teil)" ersetzt durch „D-033…D-035 → docs/governance/" (keine RC-1-Kante); Eigenschaften-Absatz angepasst | s. o. |
| M-2 | KF3_READINESS_REPORT.md §3 | RC-5-Zeile: D-033…D-035 als separater Cluster (keine RC-1-Kopplung) | s. o. |
| M-3 | KF3_DECISION_QUEUE.md §RC-5, KF3_DECISION_DEPENDENCY_GRAPH.md | KIR-Repo-Status aus RC-5 entfernt; KIR bleibt Knowledge-Gap **KG-01** (Doc 19; G7 §4), keine Decision-Queue-Aufnahme | G7 §4, Doc 19 KG-01, §RC-5-Statusliste (ohne KIR) |
| M-4 | KF3_DECISION_QUEUE.md §RC-4a, KF3_READINESS_REPORT.md §3 | Review-Abhängigkeiten je ADR ergänzt (nur Feststellung, keine Bewertung/Annahme): ADR-022 — MUSCAL-2.0-Architecture-Scope (Turnier-Primärquelle nicht im Repo; Migrationsbewertung/ADR-001-Bezug fehlt); ADR-023 — Security Model (unzureichend spezifiziert); ADR-024 — P5 / MC-TC-007-Trust-Governance-Interaktion (NO-GO-Befund offen); ADR-025 — RFC-Process (nicht definiert) | DECISION_CLOSURE_PACKAGE §RC-4 (NOT READY, je ADR individuelle Gründe); Review M-4 |
| L-2 | KF3_DECISION_QUEUE.md §RC-6 | Entscheider wörtlich belegt: M1 Governance-Team, M2 ARB/Human, M3 Doku-Team, M4 ARB/Human+Doku (§RC-6-Verantwortlich); Mess-Protokoll ARB (G6-Frame) | DECISION_CLOSURE_PACKAGE §RC-6 |
| L-3 | KF3_DECISION_DEPENDENCY_GRAPH.md | Kante RC-4a → Architektur-Dokumente präzisiert: KF-03 blockiert Akzeptanz-Bezug, nicht die Dokumente | Doc 04/14 (DRAFT-Knoten existieren), KF-03 |
| L-4 | KF3_DECISION_QUEUE.md §RC-1 | Entscheider: „ARB / Human (Project Governance) — gleichrangig (G7-01-Zitat); G4.5 §7 B5/B7 → ARB" | G7-01 Z.6, PROJECT_STATE |
| L-6 | KF3_DECISION_QUEUE.md §RC-1 | Frist-Zeile ergänzt: „je Option: nicht definiert (offene Frage im G7-01-Brief: „welche Frist gilt?")" | G7-01 Z.38/69 |
| L-8 | KF3_DECISION_QUEUE.md §RC-4a | ADR_REVIEW_MATRIX-Referenz präzisiert: Datei im Repo vorhanden, lesbar leer; „NICHT GESTARTET" nur über Doc-04/16-Kette belegt; kein Inhalt angenommen | read/head (leer), Doc 16 |
| L-9 | KF3_DECISION_QUEUE.md §RC-4a | Versteckte Annahme entfernt: „Turnier-Primärquelle … beschaffbar?" → „Klärung offen, ob beschaffbar" | Review L-9 (C2) |

## 2. LOWs: NICHT BEHEBBAR / KEIN_AKTION (bewusst, je mit Begründung)

| Finding | Befund | Behandlung |
|---|---|---|
| L-1 | D-019, D-026…D-029 (Registry-Entscheidungslücken) nicht in Queue | KEIN_AKTION: Review belegt selbst „keine Messwirkung" (C0); Aufnahme würde Queue ohne Entscheidungswirkung verbreitern — bewusst nicht aufgenommen; Registrierung bleibt DECISION_REGISTRY/Doc 05 §G |
| L-5 | Reihenfolgeunbestimmtheit RC-3 vs. RC-6 (M1-Eingangsgröße Test-Suite ändert sich durch FL-01a-Fix) | KEIN_AKTION: keine Quelle legt Reihenfolge fest; KF3_DECISION_DEPENDENCY_GRAPH §3 regelt bereits „keine Reihenfolge-Empfehlung impliziert" — Reihenfolge-Wahl bliebe Empfehlung (Neutralitätsprinzip) |
| L-7 | „G7-02" ohne auffindbare Datei (belegt via HDR-001_DECISION_RECORD.md + Doc 05 D-023) | NICHT BEHEBBAR (KEIN_ZUGRIFF): G7-02 liegt außerhalb des KF-Lesezugriffs; Human/ARB muss Datei-Existenz bestätigen (Brief-Referenz D-023); KF-3-Zeilen bleiben referenziert |
| L-10 | Keine Dringlichkeits-/Risiko-Reihung trotz G5 R1/R2 (HIGH) | KEIN_AKTION: Reihung wäre Wertung/Nichtentscheidungskosten-Abschätzung — nicht Aufgabe der Queue (neutrale Entscheidungsunterlage); Verweis auf G5 §3 bleibt |

## 3. Validierungs-Checkliste

| Check | Ergebnis |
|---|---|
| Keine neue Entscheidung getroffen | ✅ erfüllt |
| Keine ADR akzeptiert / Status geändert | ✅ erfüllt (ADR-022…025 bleiben DRAFT; NICHT GESTARTET) |
| Keine CHAT_ONLY-/PLANNED-Einträge hochgestuft | ✅ erfüllt (D-033…D-035 bleiben PLANNED + CHAT_ONLY) |
| Keine Score-/Messwert-Änderung | ✅ erfüllt (keine Berechnung; G6-05-Stand ±0 unverändert referenziert) |
| Alle Änderungen Markdown only | ✅ erfüllt |
| Widerspruchsfreiheit zwischen den drei Artefakten | ✅ erfüllt (H-1/M-2/M-3/M-4 konsistent in Queue, Graph, Readiness) |
| Provenance aktualisiert | ✅ erfüllt (SHA-256 in KF3_READINESS_REPORT.md §5; Queue 2ac10e9d…, Graph aa6d2304…, Readiness a27e0e24… exkl. self-line) |

## 4. Ergebnis

- H-1, M-1…M-4: vollständig umgesetzt; L-2, L-3, L-4, L-6, L-8, L-9: umgesetzt; L-1, L-5, L-10: KEIN_AKTION (bewusst, begründet); L-7: NICHT BEHEBBAR (KEIN_ZUGRIFF).
- READY_FOR_HUMAN_DECISION gilt unverändert für RC-1/RC-2 (Review §8.2); RC-6-Bewertung folgt jetzt der korrigierten Mess-Matrix (H-1).
- Keine offenen Folge-Befunde aus der Independent Review; neue Befunde durch die Korrektur nicht eingeführt (Selbstprüfung §3).
- Commit-Message der nächsten KF-Batch (externer Layer, kein Git-Commit hier): `KF3 correction wave: resolve review findings H-1 M-1..M-4`
