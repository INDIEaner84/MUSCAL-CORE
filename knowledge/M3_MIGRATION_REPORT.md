# M3 Migration Report — ADR Canonical Migration

**Migration:** MUSCAL-KNOWLEDGE-MIGRATION-001 · **Phase:** M3 — ADR-Konsolidierung
**Datum:** 2026-08-02 · **Status:** M3_COMPLETE
**Referenz:** KNOWLEDGE_CONSOLIDATION_PLAN.md V1.0 (§2.3), ADR-INDEX (spec/), ADR_CANONICAL_MAP (F-01…F-05), MIGRATION_MANIFEST.yaml
**Regeln:** Keine Inhaltsänderung · Keine Nummern-Neuvergabe · Keine fachliche Neuinterpretation · Nur Struktur/Referenzierung/Kanonisierung

## ADR Mapping Summary

| Quelle | Kategorie | Ziel | Anzahl | Status(quer) |
|---|---|---|---|---|
| `spec/ADR-*.md` (001–014, 022–025) | CANONICAL | `knowledge/adr/ADR-NNN-name.md` | 18 | APPLIED/ACCEPTED/SUPERSEDED/DRAFT |
| `spec/ADRs/*.md` (API/EVENT/RUNTIME-001) | CANONICAL | `knowledge/adr/` | 3 | aktiv (Approved, Gate-1) |
| `docs/engineering/ADR-020, ADR-021` | CANONICAL | `knowledge/adr/` | 2 | DRAFT/aktiv |
| `docs/audit/MC-TC-003A_ADR_PACKAGE.md` (ADR-011…016) | **AUDIT_REFERENCE** | bleibt `Codebase/docs/audit/` | — | keine Übernahme (M3-D1) |
| `docs/audit/ADR_CANONICAL_MAP, ADR_REVIEW_MATRIX, 13_ADR_INDEX_FOUNDATION, G6_01_*` | AUDIT_REFERENCE | bleiben `docs/audit/` | — | Governance-Artefakte |
| `archive/history/adrs/ADR-001…006` | ARCHIVED | bleiben `archive/history/adrs/` | 6 | Referenz (D-025) |
| `specs/adrs/IMPLEMENTATION_STATUS.md` | **DEPRECATED** | bleibt, Header-Marker (M3-D3) | 1 | ersetzt durch ADR-INDEX v2.0 |
| `specs/templates/RFC_TEMPLATE.md` | DEPRECATED (Plan §3) | bleibt | 1 | ersetzt durch ADR_TEMPLATE.md |

**Migriert: 23 kanonische ADRs** → `knowledge/adr/` (Konvention `ADR-NNN-name.md`, Namen 1:1, keine Umbenennung nötig). Neu: `ADR_TEMPLATE.md`, `ADR-INDEX.md` (v2.0).

## Nummernkollision (M3-D1)

MC-TC-003A ADR-011…016 (Trust-Core-Serie im Root-Lager `docs/audit/MC-TC-003A_ADR_PACKAGE.md`) werden **NICHT** in die kanonische Serie übernommen:
- Kanonische Nummern 011/012/013/014 (Verification, Event-Persistence, Pipeline, Tool-Runtime) bleiben unangetastet.
- Audit-Serie bleibt kontextualisiert (`MC-TC-003A`), kein Nummern-Reuse.
- Dokumentiert im ADR-INDEX v2.0 (§ Audit-Kontext-ADRs) und Manifest (decisions: M3-D1).

## Redirect Status

- **24 Altort-Redirects** (Header `> **REDIRECT:** … knowledge/adr/<datei>`, Original-Inhalt unverändert darunter): 18 × `spec/`, 3 × `spec/ADRs/`, 2 × `docs/engineering/`, 1 × `spec/ADR-INDEX.md`.
- `specs/adrs/IMPLEMENTATION_STATUS.md`: DEPRECATED-Header (kein Redirect nötig, kein kanonischer Inhalt).
- Keine Löschung; Historie bleibt über Git + Header erhalten.

## Validation

| Prüfung | Ergebnis |
|---|---|
| Keine ADR verloren (Quell-Menge ⊆ Ziel) | OK — 23/23 ✓ |
| Inhalt Hash Quelle = Ziel (je Datei) | ALL_IDENTICAL 23/23 ✓ |
| Aggregat-Inhalts-Hash (23 ADRs, vor = nach) | `a505bcf06df82c5f6b388934b6bd3f0b0b6da2ba694ba6a7bcf07d8ef7d8ec33` ✓ |
| Keine ID doppelt (Ziel) | 23 eindeutige IDs (001–025 + API/EVENT/RUNTIME) ✓ |
| Keine Nummernkollision mit Audit-Serie | MC-TC-003A unberührt, kein Reuse ✓ |
| Redirects korrekt (Stub = Header + Original) | 24/24 + INDEX ✓ |
| ADR_CANONICAL_MAP konsistent | F-01…F-05 vorhanden; F-Closure-Marking (RESOLVED) als Governance-Schritt offen (ARB) — siehe Blocker |
| Manifest | VALID (phase M3, decisions M3-D1…D3, migrated_objects 3) ✓ |
| Working Tree | nur knowledge/, spec/, specs/, docs/engineering/-Änderungen (staged) ✓ |

## Blocker

1. **Keine Blocker.**
2. Offen (nicht M3): F-01…F-05-Final-Markierung in `ADR_CANONICAL_MAP.md` (RESOLVED-Einträge) — erfolgt als Governance-Review (ARB), da Audit-Artefakt; inhaltlich sind alle Findings durch M3 erfüllt (F-01: INDEX-Generierung ab M4, F-02: Standorte konsolidiert, F-03: specs/adrs deprecated, F-04: keine Duplikate, F-05: Kollision entschieden).
3. Offen: ADR-022…025-Akzeptanz (RC-4a, Human/ARB) — betrifft Status, nicht Struktur.

## Next Step

**GO für M4** (Metadata-Schema v1.0 + Frontmatter-Backfill + INDEX-Generierung).
