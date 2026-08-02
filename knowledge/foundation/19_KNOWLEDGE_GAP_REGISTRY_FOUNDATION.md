# 19 — Knowledge Gap Registry Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only, keine neuen Gaps, keine Statusänderungen)
- Quellen: MASTER_INDEX (KF), SOURCE_OF_TRUTH_MAP (KF), SESSION_CONTINUITY (KF + Doc 09), KF1_COMPLETION_AUDIT, DECISION_REGISTRY (KF), G5, G6 (G6-01…G6-05), G7 (G7-01…G7-04), TECHNICAL_MANUAL_CONFLICT_REPORT, FL01A_FLAKINESS_REGISTER, ADR_REVIEW_MATRIX, HDR-001_DECISION_RECORD

## 1 Purpose

Vollständige, quellenpflichtige Registrierung aller bereits bekannten Wissens-, Governance-, Dokumentations-, Technik- und Entscheidungs-Lücken des Projekts — als konsistenter Ausgangspunkt für KF-2 und die RC-Abarbeitung. Keine neuen Gaps, keine neuen Interpretationen, keine Statusänderungen.

## 2 Scope

- Aufgenommen: alle in den genannten Quellen explizit als offen/blockiert/UNKNOWN/ausstehend markierten Punkte.
- Nicht aufgenommen: behobene Punkte (z. B. ADR-013-Fehllabel — PA-06, d5f5ce7; M-1/M-2/M-3/M-5/M-6 — G2-Exekution; Backfill — PB-01); erfüllte Kriterien (G7-04 Kriterien 1–5+7).
- Grenzen: 19 Gaps, Stand 02.08.2026 (nach KF-1.1-Korrektur F-001/F-002).

## 3 Gap Classification Model

| Kategorie | Bedeutung | Status-Ausprägungen (unverändert aus Quelle) |
|---|---|---|
| Knowledge (K) | unbekanntes Wissen / fehlende Detailquelle | UNKNOWN, offen, teilweise (PARTIAL) |
| Governance (GOV) | fehlende Regel, Freigabe oder Autorität | offen, NOT AUTHORIZED, NICHT GESTARTET, PENDING HUMAN, HUMAN REQUIRED |
| Documentation (DOC) | fehlende/veraltete/ungelöste Dokumentation | offen, stale, blockiert |
| Technical (T) | technische Defizite (Fix/Freigabe ausstehend) | offen |
| Open Decision (OD) | ausstehende Entscheidung | PENDING HUMAN, HUMAN REQUIRED, offen |

Jeder Gap: ID KG-nn, Kategorie, Inhalt, Quelle, Status (wörtlich aus Quelle übernommen), Blocker.

## 4 Knowledge Gaps

| ID | Inhalt | Status | Quelle | Blocker |
|---|---|---|---|---|
| KG-01 | KIR-Repo-Status UNKNOWN (keine Detailquelle) | offen | MASTER_INDEX (S1), G7 §4 | RC-5 |
| KG-02 | S-2026-07-31-001 Detailinhalt UNKNOWN (registry-only) | offen | SESSION_CONTINUITY (G4-M3, G6-Recheck), Doc 09 G-2 | — |
| KG-03 | Manual-Konflikte TC-L1/L2 unaufgelöst (TC-L2 Teil C2) | offen | TECHNICAL_MANUAL_CONFLICT_REPORT, Doc 07 §6 | — |
| KG-04 | TC-H3 PARTIAL (v0.8-Manual-Erzeugung blockiert) | teilweise | TECHNICAL_MANUAL_CONFLICT_REPORT (B5/B6), G6 | RC-5 |
| KG-19 | M4-K3-Freshness: Re-Messung M1–M5 ausstehend | ausstehend | G6-05, Doc 18 §2 | RC-1/RC-2 (RC-6) |

## 5 Governance Gaps

| ID | Inhalt | Status | Quelle | Blocker |
|---|---|---|---|---|
| KG-12 | Bridge-Artefakte (104 untracked) ohne Artefakt-Governance/Lesepfad-Regel | offen | G7, Doc 09 G-4, G4-M1 | Doc 17 fehlt (P3) |
| KG-13 | HDR-002…004 durch RC-2 blockiert | offen | HDR-001, G7-02 | RC-2 |
| KG-14 | ADR-022…025-Review | NICHT GESTARTET | ADR_REVIEW_MATRIX, G7-03 | RC-4a |
| KG-15 | MC-TC-005 NOT AUTHORIZED (Scope-Grenze unbekannt) | offen | G6/G7, Doc 09 M-2, SESSION_CONTINUITY | — |

## 6 Documentation Gaps

| ID | Inhalt | Status | Quelle | Blocker |
|---|---|---|---|---|
| KG-05 | F-03: specs/adrs/-Leiche (4. ADR-Standort physisch, kein Inhalt) | offen | SOURCE_OF_TRUTH_MAP, ADR_CANONICAL_MAP, G6-01, Doc 03 SO-4 | RC-5 |
| KG-07 | TECHNICAL_BASELINE + ARCHITECTURE stale (12.07) | offen | SOURCE_OF_TRUTH_MAP §2.1, Doc 09 G-1 | — |
| KG-08 | CHANGE_JOURNAL endet 13.07 (kein Fortschritt seit Audit) | offen | REPOSITORY_CENSUS §7, Doc 09 G-5 | — |
| KG-10 | v0.8-Changelog ohne ROADMAP-/DECISIONS-Update | offen | SESSION_CONTINUITY_AUDIT M-7, Doc 09 M-7 | RC-5 |
| KG-11 | Fehlende 20-Doc-Dokumente: 04 (Knowledge Graph, P2), 14 (Architektur-Landkarte, P2), 15 (Zertifizierungs-Register, P2), 16 (Blocker-Register, P2), 17 (Bridge-Governance, P3) | fehlen | KF-01-Dokumentenplan, KF-03 | 15/16: RC-1/RC-2; 04/14: RC-4a; 17: Bridge-Beschluss |

## 7 Technical Gaps

| ID | Inhalt | Status | Quelle | Blocker |
|---|---|---|---|---|
| KG-06 | FL-01a-Root-Cause: globale Singletons (tools.py 9–24, tool_runtime.py 28–42); 19 flaky, D-040 | Fix offen | FL01A_FLAKINESS_REGISTER, G6, Doc 10 §7 | RC-3 (ARB-Freigabe) |
| KG-09 | D-042: Global-State-Architecture-ADR (Entwurf vorhanden, Freigabe ausstehend) | offen | GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT, DECISION_REGISTRY | RC-3 |

## 8 Open Decision Gaps

| ID | Inhalt | Status | Quelle | Blocker |
|---|---|---|---|---|
| KG-16 | P0-1/P0-2 (D-033…D-035-Plan-Docs, MUSCAL-2.0-Nachfolger) | PENDING HUMAN | PROJECT_STATE (Update 01.08), G7-01 (Optionen A–D) | RC-1 |
| KG-17 | HDR-001 (Manual-Authority, M-0.7) | HUMAN REQUIRED | PROJECT_STATE, G7-02 (Optionen A–D) | RC-2 |
| KG-18 | Entscheidungslücken D-019, D-026…D-029 | offen | DECISION_REGISTRY (Lücken), Doc 05 §G | — |

## 9 Validation

- Read-only eingehalten: keine Dokumentänderung, keine neue Entscheidung, keine Statusänderung, keine ADR-Akzeptierung, keine Re-Messung, kein Code.
- Alle 19 Gaps mit Quelle (KF-Artefakt/Gate/Dokument); Status wörtlich aus Quelle übernommen; keine neuen Gaps erfunden.
- Konsistenz: KG-IDs KG-12…KG-18 deckungsgleich mit Doc 12 §8; ADR-013-Fehllabel als GAP ausgeschlossen (behoben, PA-06/d5f5ce7 — KF-1.1-Korrektur); F-03 (KG-05) separat von ADR-013 geführt (KF1_COMPLETION_AUDIT F-001/F-002).
- Gesamt: 19 dokumentierte Gaps (5 Knowledge, 4 Governance, 5 Documentation, 2 Technical, 3 Open Decision).
