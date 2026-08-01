# ADR_CANONICAL_MAP — MUSCAL CORE

**Phase:** Phase B · **Block:** PB-04 (ADR-Konsolidierung) · **Datum:** 2026-08-01
**Modus:** READ-MOSTLY — **nur Mapping, keine Löschung, keine Umbenennung, keine Verschiebung**
**Inventar-Standorte:** `spec/` (kanonisch) · `spec/ADRs/` · `specs/adrs/` · `archive/history/adrs/` · `docs/engineering/` (ADR-020/021)

> Grundsatz: Jede hier gelistete Aktion ist EIN VORSCHLAG für die Umsetzung
> nach Phase B (Gate G4). Phase B selbst verändert keine ADR-Dateien.

---

## 1. Kanonische ADRs (`spec/ADR-*.md`)

| ADR-ID | Quelle | Status | Autorität | Superseded durch | Duplikate | Aktion (Vorschlag) |
|--------|--------|--------|-----------|------------------|-----------|--------------------|
| ADR-001 | spec/ADR-001-kernel.md | APPLIED | kanonisch | — | — | keine |
| ADR-002 | spec/ADR-002-memory.md | ACCEPTED (Ph1-4 ✅) | kanonisch | — | — | keine |
| ADR-003 | spec/ADR-003-events.md | APPLIED | kanonisch | — | — | keine |
| ADR-004 | spec/ADR-004-plugins.md | ACCEPTED | kanonisch | — | — | keine |
| ADR-005 | spec/ADR-005-pipeline.md | ACCEPTED | kanonisch | — | — | keine |
| ADR-006 | spec/ADR-006-graph.md | ACCEPTED | kanonisch | — | — | keine |
| ADR-007 | spec/ADR-007-immutability.md | ACCEPTED | kanonisch (Write Guard Policy) | — | ADR-013 (historisch, falsch benannt) | keine (ADR-013-Hinweis existiert) |
| ADR-008 | spec/ADR-008-deployment.md | ACCEPTED | kanonisch | — | — | keine |
| ADR-009 | spec/ADR-009-observability.md | ACCEPTED | kanonisch | — | — | keine |
| ADR-010 | spec/ADR-010-sqlite.md | APPLIED | kanonisch | — | — | keine |
| ADR-011 | spec/ADR-011-verification.md | ACCEPTED | kanonisch | — | — | keine |
| ADR-012 | spec/ADR-012-event-persistence.md | APPLIED | kanonisch | — | — | keine |
| ADR-013 | spec/ADR-013-pipeline.md | **SUPERSEDED** | historisch (fehlbenannt; Inhalt = Plugin Migration Path) | ADR-007 | — | INDEX korrekt; Datei behalten |
| ADR-014 | spec/ADR-014-tool-runtime.md | **ACCEPTED** (Datei, 01.08) | kanonisch | — | — | ⚠️ **INDEX stale**: zeigt PROPOSED (15.07) → INDEX-Zeile nach G4 aktualisieren |

## 2. Erweiterungs-ADRs (`spec/ADRs/`)

| ADR-ID | Quelle | Status | Autorität | Superseded durch | Duplikate | Aktion (Vorschlag) |
|--------|--------|--------|-----------|------------------|-----------|--------------------|
| ADR-API-001 | spec/ADRs/ADR-API-001-dual-runtime.md | aktiv (Phase-1A-Wave, committet 1c4a1e7) | nicht kanonisch (außerhalb `spec/ADR-*.md`-Namensschema) | — | — | in ADR-INDEX aufnehmen („Dual Runtime") oder Umbenennung → ADR-015 |
| ADR-EVENT-001 | spec/ADRs/ADR-EVENT-001-eventstore-boundary.md | aktiv (committet 1c4a1e7) | nicht kanonisch | — | Registry §E-Gap: „nicht in kanonischem spec/-Set" | INDEX-Aufnahme oder → ADR-016 |
| ADR-RUNTIME-001 | spec/ADRs/ADR-RUNTIME-001-supl-ownership.md | aktiv (committet 1c4a1e7) | nicht kanonisch | — | — | INDEX-Aufnahme oder → ADR-017 |

## 3. Verwaister Ordner (`specs/adrs/`)

| ADR-ID | Quelle | Status | Autorität | Superseded durch | Duplikate | Aktion (Vorschlag) |
|--------|--------|--------|-----------|------------------|-----------|--------------------|
| (kein ADR) | specs/adrs/IMPLEMENTATION_STATUS.md | aktiv (Inhalt prüfen) | keine (Ordner außerhalb aller Konventionen) | — | — | Inhalt in `docs/engineering/`-Schema migrieren; Ordner nach G4 als Referenz markieren — **keine Löschung** |

## 4. Historische ADRs (`archive/history/adrs/`)

| ADR-ID | Quelle | Status | Autorität | Superseded durch | Duplikate | Aktion (Vorschlag) |
|--------|--------|--------|-----------|------------------|-----------|--------------------|
| ADR-001 | archive/history/adrs/ADR-001.md | historisch | keine (Referenz) | ADR-001 (kanonisch) | historische Fassung des kanonischen ADR-001 | keine |
| ADR-002 | archive/history/adrs/ADR-002.md | historisch | keine | ADR-002 (kanonisch) | dito | keine |
| ADR-003 | archive/history/adrs/ADR-003.md | historisch | keine | ADR-003 (kanonisch) | dito | keine |
| ADR-004 | archive/history/adrs/ADR-004.md | historisch | keine | ADR-004 (kanonisch) | dito | keine |
| ADR-005 | archive/history/adrs/ADR-005.md | historisch | keine | ADR-005 (kanonisch) | dito | keine |
| ADR-006 | archive/history/adrs/ADR-006.md | historisch | keine | ADR-006 (kanonisch) | dito | keine |

## 5. ADRs außerhalb des Kanons (`docs/engineering/`, `docs/governance/`)

| ADR-ID | Quelle | Status | Autorität | Superseded durch | Duplikate | Aktion (Vorschlag) |
|--------|--------|--------|-----------|------------------|-----------|--------------------|
| ADR-020 | docs/engineering/ADR-020-PIPELINE-STAGES-ADOPTION.md | aktiv | nicht kanonisch | — | — | in ADR-INDEX aufnehmen („Pipeline Stages Adoption") |
| ADR-021 | docs/engineering/ADR-021-AGENT-DETECTION-FORMALIZATION.md | aktiv | nicht kanonisch | — | — | in ADR-INDEX aufnehmen („Agent Detection Formalization") |
| ADR-014-IMPLEMENTATION_PLAN_v1.0 | docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.0.md | superseded (durch v1.1) | Plan-Dokument (kein ADR) | ADR-014-IMPLEMENTATION_PLAN_v1.1 | v1.1 | als „superseded by v1.1" markieren |
| ADR-014-IMPLEMENTATION_PLAN_v1.1 | docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md | aktiv | Plan-Dokument (kein ADR) | — | v1.0 | keine |

---

## Findings (PB-04)

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| F-01 | **ADR-INDEX stale:** ADR-014 in INDEX als PROPOSED (15.07) geführt, Datei seit 01.08 ACCEPTED (a39f545) | MEDIUM | offen (INDEX-Update nach G4) |
| F-02 | **5 ADRs außerhalb des Kanons:** ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001, ADR-020, ADR-021 nicht in `spec/ADR-INDEX.md` | MEDIUM | offen (INDEX-Aufnahme nach G4) |
| F-03 | **Verwaister Ordner `specs/adrs/`:** IMPLEMENTATION_STATUS.md ohne Konvention | LOW | offen (Migration nach G4) |
| F-04 | **Kein Duplikat im engeren Sinn:** alle Standorte enthalten originäre Inhalte; keine inhaltlich identischen ADR-Paare | — | verifiziert |
| F-05 | **Historische ADR-001…006** = Vorversionen der kanonischen ADR-001…006; Supersession-Regel (D-025) anwendbar | — | verifiziert |

---

*Methode: Dateisystem-Inventar aller 5 Standorte + ADR-INDEX-Abgleich (2026-08-01). Keine Datei wurde verändert, gelöscht oder verschoben.*
