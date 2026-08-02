# 13_ADR_INDEX_FOUNDATION.md

**Doc:** KF-1B/13 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** ADR_CANONICAL_MAP.md (PB-04, F-01…F-05) · spec/ADR-INDEX.md (kanonisch, G4.5 B1) · ADR_REVIEW_MATRIX.md (G7-03) · DECISION_REGISTRY (D-010…D-025) · SOURCE_OF_TRUTH_MAP (§2.1/§2.6)
**Modus:** Read-only Konsolidierung — **keine neuen ADRs, keine Statusänderung, keine Akzeptierung, keine Umbenennung**
**Grundregel:** ADR-022…025 bleiben DRAFT/PROPOSED; Review-Ergebnis (RC-4a) nicht vorweggenommen.

---

## 1. Purpose

Dieses Dokument macht den ADR-Bestand des MUSCAL-CORE navigierbar: kanonische ID-Liste, Standorte (5+), Status-Registry, Supersession-Beziehungen und bekannte Lücken. Es ist der operative Nachfolger von ADR_CANONICAL_MAP + ADR-INDEX und Eingangsquelle für M4 (K2: Entscheidungs-Reife, 13/17 akzeptiert, 4 DRAFT).

## 2. ADR Authority Model

| Regel | Beleg | Quelle |
|-------|-------|--------|
| Kanonischer Bestand = `spec/ADR-*.md` (14) | SESSION_RULES Prio 4 + B1 | SESSION_RULES v2.0 [C0], ADR-INDEX [C0] |
| Status-Vokabular: DRAFT / PROPOSED / ACCEPTED / APPLIED / DEPRECATED / SUPERSEDED | INDEX „Status Definitions" | ADR-INDEX [C0] |
| Supersession-Regel: historische ADRs ohne Autorität (D-025) | SESSION_RULES §HISTORICAL | SESSION_RULES [C0] |
| Erweiterungs-ADRs (`spec/ADRs/`, `docs/engineering/`) = nicht kanonisch, via B1 in INDEX aufgenommen (F-02 behoben) | B1-Notiz, INDEX-Zeilen | ADR-INDEX [C0] |
| Review-Kompetenz: Status-Empfehlung nur durch ARB/Human (RC-4a) | ADR_REVIEW_MATRIX §3 | Matrix [C0] |

## 3. ADR Inventory (24 registrierte ADRs + 6 historische — keine neuen)

| Gruppe | IDs | Anzahl |
|--------|-----|-------:|
| Kanonisch `spec/ADR-*.md` | ADR-001…ADR-014 | 14 |
| Erweiterung `spec/ADRs/` | ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001 | 3 |
| Außerhalb Kanon `docs/engineering/` | ADR-020, ADR-021 | 2 |
| Entwürfe `spec/ADR-*.md` | ADR-022…ADR-025 (DRAFT/PROPOSED) | 4 |
| Historisch `archive/history/adrs/` | ADR-001…006 (Vorversionen) | 6 |
| Plan-Dokumente (keine ADRs) | ADR-014-IMPLEMENTATION_PLAN v1.0/v1.1 | 2 |

## 4. ADR Locations

| Standort | Inhalt | Autorität | Befund | Quelle |
|----------|--------|-----------|--------|--------|
| `spec/` | 14 kanonische + 4 Entwürfe | **kanonisch** | 4-Standorte-Splitting belegt (F-04: keine inhaltlichen Duplikate) | Canonical-Map §1, F-04 |
| `spec/ADRs/` | 3 Erweiterungs-ADRs (committet 1c4a1e7) | nicht kanonisch, INDEX-gelistet | F-02 aufgenommen | Map §2, B1 |
| `specs/adrs/` | IMPLEMENTATION_STATUS.md | **keine** (konventionslos) | F-03 offen — Migration nach G4 vorgeschlagen (keine Löschung) | Map §3 |
| `archive/history/adrs/` | ADR-001…006 Vorversionen | keine (Referenz) | F-05: Supersession-Regel D-025 anwendbar | Map §4, B1 |
| `docs/engineering/` + `docs/governance/` | ADR-020/021; IMPLEMENTATION_PLAN v1.0/v1.1 | nicht kanonisch, INDEX-gelistet; Plan ≠ ADR | — | Map §5 |

## 5. ADR Status Registry (unverändert, wörtlich aus INDEX)

| Status | ADRs | Anzahl |
|--------|------|-------:|
| **APPLIED** | ADR-001, 003, 010, 012 | 4 |
| **ACCEPTED** | ADR-002, 004, 005, 006, 007, 008, 009, 011, 014 (Datei-Stand 01.08, F-01 behoben) | 9 |
| **SUPERSEDED** | ADR-013 (fehlbezeichnet; Inhalt = Feature-Plugin-Migration, superseded by ADR-007) | 1 |
| **DRAFT/PROPOSED** | ADR-022, 023, 024, 025 | 4 |
| **aktiv (nicht kanonisch)** | ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001, ADR-020, ADR-021 | 5 |
| **historisch** | ADR-001…006 (archive) | 6 |

**M4-K2-Beleg (G5):** 13/17 aktive ADRs akzeptiert (ADR-001…012, 014); 4 DRAFT (022…025) — unverändert [C1].

## 6. Supersession Registry (nur belegte Beziehungen)

| ADR | Superseded durch | Beleg |
|-----|------------------|-------|
| ADR-013 (fehlbenannt) | ADR-007 (Write Guard Policy) | Canonical-Map §1, INDEX-Zeile [C0] |
| ADR-001…006 (historisch) | kanonische ADR-001…006 | Map §4 F-05, D-025-Regel [C0] |
| ADR-014-IMPLEMENTATION_PLAN v1.0 | v1.1 | Map §5 [C0] |
| D-018-Statuskonflikt (ADR-014 PROPOSED vs Datei) | D-038 (ACCEPTED, G2-Resolution) | DECISION_REGISTRY D-038 [C1] |
| (keine Supersession der DRAFT-Entwürfe) | — | ADR-022…025 ohne Supersession-Eintrag [C0] |

## 7. Known ADR Gaps (unverändert)

| # | Gap | Status | Quelle |
|---|-----|--------|--------|
| G-1 | `specs/adrs/`-Ordner konventionslos (F-03) | offen — Migration vorgeschlagen, keine Löschung | Canonical-Map F-03 |
| G-2 | ADR-022…025-Review (RC-4a) NICHT GESTARTET; OQ 3+6 je ADR | offen — Entscheidung durch ARB/Human | ADR_REVIEW_MATRIX |
| G-3 | Kein ADR für v0.8 (CHANGELOG_v0.8.md, kein ADR-015+) | offen — dokumentiert | DECISION_REGISTRY §E |
| G-4 | MC-015→ADR-Konvertierung nur als DRAFT (D-010) | offen — Akzeptanz ausstehend | Registry §E, ADR-022 |
| G-5 | MKSD fehlt (Spec-Gap) | offen — bestätigt | Reconciliation-Claim 17 [C1] |
| G-6 | ADR-EVENT-001-Standort (Registry-§E-Gap) | adressiert via B1-INDEX (Aufnahme); physischer Standort unverändert | B1-Notiz |
| G-7 | ADR-014-INDEX-Stale (F-01) | behoben (INDEX zeigt ACCEPTED, 01.08) | INDEX-Notiz, B1 |

## 8. Validation

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Keine neuen ADRs erzeugt | ✅ 24 IDs + 6 historische ausschließlich aus Map/INDEX; keine neue ID |
| Keine Statusänderung | ✅ Status-Zeilen wörtlich aus INDEX (01.08); ADR-022…025 bleiben DRAFT/PROPOSED; Review-Ergebnis nicht vorweggenommen |
| Keine Akzeptierung | ✅ keine ACCEPTED-Empfehlung; ARB-Kompetenz zitiert (Matrix §3) |
| Jede Aussage mit Provenance | ✅ Tabellen mit Quelle/Confidence (Map F-01…F-05, INDEX, Matrix, Registry) |
| Unbekanntes als GAP | ✅ G-1…G-7; Review-Status „NICHT GESTARTET" |
| Markdown only | ✅ docs/audit/13_ADR_INDEX_FOUNDATION.md |

---

*Erstellt als konsolidierte ADR-Referenz — keine neuen ADRs, keine Statusänderung. Stand: 02.08.2026.*
