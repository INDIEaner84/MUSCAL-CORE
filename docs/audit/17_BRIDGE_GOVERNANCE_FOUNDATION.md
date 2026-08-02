# 17 — Bridge Governance Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only; keine Bridge-Entscheidung, keine Governance-Änderung)
- Quellen: git status (docs/bridge/), G7 §4, G4-M1, Doc 09 G-4, Doc 19 KG-12, DECISION_REGISTRY, HDR-001_DECISION_RECORD, G7-01/G7-02, PROJECT_STATE

## 1 Purpose

Bestandsdokumentation der Bridge-Artefakte und ihres Governance-Zustands. Es werden **keine** Governance-Regeln eingeführt und **keine** Entscheidungen getroffen; KG-12 bleibt offene Entscheidung. Ziel: belegter Ausgangspunkt für den späteren Bridge-Beschluss (Human/ARB).

## 2 Scope

- Aufgenommen: alle Bridge-Artefakte unter `docs/bridge/` (Stand: untracked, committeter Zustand unverändert), bestehende Governance-Bezüge (Lesepfad-Regel, Autoritätskette), bekannte Gaps (KG-12, G4-M1), verknüpfte offene Entscheidungen (RC-1, RC-2).
- Nicht aufgenommen: Artefakt-Inhalte (nicht geprüft, kein Governance-Status), neue Regeln, neue Entscheidungen, Bewertung der Handover-Inhalte.

## 3 Bridge Artefact Inventory

| Merkmal | Wert | Beleg |
|---|---|---|
| Speicherort | `docs/bridge/handovers/` (einziger Bridge-Unterordner) | git status --porcelain |
| Anzahl | 104 Artefakte (untracked) | git status (gezählt 104) |
| Namensmuster | `handover_<UTC-Timestamp>.md` + `.yaml` (Paare) | git status |
| Frühester Beleg | handover_20260801T202638.md/.yaml | git status |
| Git-Status | alle `??` (untracked) — keine Commit-Evidence | git status |
| Registrierung | kein Registry-/Governance-Eintrag belegt | — (kein Eintrag gefunden) |

Hinweis: Die Artefakte sind nicht Teil der 55 committeten Audit-Artefakte (392734e) und werden hier nicht bewertet (Scope §2).

## 4 Current Governance State

- **Keine Artefakt-Governance:** 104 Bridge-Artefakte ohne Governance-/Lesepfad-Regel (G7 §4; Doc 19 KG-12; G4-M1).
- **Lesepfad-Lücke:** SESSION_RULES v2.0 definiert einen Lesepfad (PROJECT_STATE zuerst, Autoritätskette Prio 1–8); `docs/bridge/` ist darin nicht adressiert (G4-M1: „Bridge-Artefakte (104 untracked) ohne Lesepfad-Regel").
- **Kein Autoritätsstatus:** Die Artefakte sind keiner Prio-Ebene der Quelle-Kette (SOURCE_OF_TRUTH_MAP, Doc 03 §3) zugeordnet; damit keine belegte Autoritätswirkung.
- **Keine Status-Klassifikation:** kein IMPLEMENTED/DOCUMENTED/PLANNED/CHAT_ONLY-Status belegt (kein D-ID-Eintrag gefunden).
- Stand unverändert: Die Lücke ist als offene Entscheidung registriert (KG-12, Doc 19; Doc 09 G-4), nicht aufgelöst.

## 5 Authority Model

- **Bestandteile (unverändert, belegt):** SESSION_RULES v2.0 (Lesepfad, .opencode/, 20.07) · Projekt-Autoritätskette Prio 1–8 (PROJECT_STATE → MC-TC → ADR-INDEX → DECISIONS → CHANGE_JOURNAL → archive → ROADMAP → CHANGELOG; Doc 02/03, SESSION_RULES) · Manual-Kanon (M-0.6 > M-0.7 > M-ROOT; Doc 07).
- **Einordnung Bridge-Artefakte:** nicht in der Kette enthalten → keine belegte Autorität; Inhalt könnte dennoch Wissenswert enthalten (keine Bewertung, G4-M1).
- **Relevanz der offenen Entscheidungen:** HDR-001 (Manual-Authority, RC-2) und P0-1/P0-2 (RC-1) sind unabhängig vom Bridge-Beschluss offen; ein Bridge-Beschluss müsste in den bestehenden Entscheidungs-/Freigabepfad (Human/ARB, G7-01/G7-02-Muster) eingeordnet werden — **keine** Festlegung hier.

## 6 Known Gaps

| ID | Gap | Status (unverändert) | Quelle |
|---|---|---|---|
| KG-12 | Bridge-Artefakte (104 untracked) ohne Artefakt-Governance/Lesepfad-Regel | offen (Dokumentation in diesem Doc; keine Entscheidung) | Doc 19 KG-12, G7 §4, Doc 09 G-4 |
| G4-M1 | SESSION_RULES-Lesepfad: Bridge-Artefakte ohne Lesepfad-Regel | offen | G4-M1, Doc 09 G-4 |
| — | Kein Git-Commit der Bridge-Artefakte (untracked) | offen (unverändert) | git status |
| — | Kein Registry-/Autoritäts-Status der Bridge-Artefakte | offen (unverändert) | — (kein Eintrag belegt) |

## 7 Open Decisions

| Entscheidung | Status (wörtlich) | Quelle | Verknüpfung |
|---|---|---|---|
| Bridge-Governance-Beschluss (Artefakt-Governance + Lesepfad für docs/bridge/) | offen — KG-12; kein Beschluss getroffen | Doc 19 KG-12, G7 §4 | RC-5 (Doku-Pfad); Doc 16 B4-Muster |
| P0-1/P0-2 (Graph-OS/Watchdog) | **PENDING HUMAN** | PROJECT_STATE 01.08, G7-01, Doc 16 RC-1 | betroffen: Bridge-Handover-Inhalte nicht bewertet |
| HDR-001 (Manual-Authority) | **HUMAN REQUIRED** | HDR-001, G7-02, Doc 16 RC-2 | Autoritätsmodell §5 |

## 8 Risk Assessment

- **Wissensverlust-Risiko:** Bridge-Artefakte sind untracked → nicht versioniert, kein Revisionspfad, kein Backup über Git; ohne Governance kein belegter Zustand (G4-M1, G7 §4). Risiko-Einstufung: nur beschreibend, keine neue Messung.
- **Autoritäts-Risiko:** Artefakte ohne Kette-Zuordnung könnten bei Nutzung als Quelle irreführen (keine Prio-Ebene); bis zum Bridge-Beschluss keine Verwendung als Quelle belegt (KG-12).
- **Fresh-Session-Risiko:** Lesepfad-Lücke bedeutet, dass neue Sessions Bridge-Inhalte weder als verpflichtend noch als autoritativ erkennen (G4-M1; Doc 09 G-3/G-4).
- Keine neuen Risiken definiert; ausschließlich belegte Zustände beschrieben.

## 9 Evidence Binding

| Aussage | Beleg | Confidence |
|---|---|---|
| 104 Artefakte unter docs/bridge/handovers/, untracked | git status --porcelain (104 × `??`) | C0 |
| Namensmuster handover_<TS>.{md,yaml} | git status | C0 |
| Keine Lesepfad-/Governance-Regel | G4-M1, G7 §4, Doc 09 G-4 | C0 |
| KG-12 offen | Doc 19 KG-12 (19_KNOWLEDGE_GAP_REGISTRY_FOUNDATION.md) | C0 |
| RC-1/RC-2-Status | PROJECT_STATE (01.08), HDR-001, G7-01/G7-02 | C0 |
| Autoritätskette ohne docs/bridge/ | Doc 02 §1.1, Doc 03 §3.1 | C0 |

## 10 Validation

- Read-only: keine Datei verändert, keine Bridge-Entscheidung, keine Governance-Änderung, keine Statusänderung, keine ADR-Akzeptierung, kein Code; Artefakte unverändert untracked.
- Quellenprüfung: Inventory per `git status` verifiziert (104 Artefakte, docs/bridge/handovers/, handover_*.*-Muster); alle Gaps/Entscheidungen mit Quelle.
- Statusprüfung: KG-12 „offen" unverändert; PENDING HUMAN / HUMAN REQUIRED wörtlich übernommen; kein neuer Status eingeführt.
- Confidence-Prüfung: nur C0-Belege (git status, committete KF-Docs); keine Aufwertung; Artefakt-Inhalte ungeprüft (bewusst kein C-Wert).
- Widerspruchsprüfung: konsistent mit Doc 19 (KG-12), Doc 09 (G-4), Doc 12 §8, Doc 16; kein Widerspruch zu G7 §4.
