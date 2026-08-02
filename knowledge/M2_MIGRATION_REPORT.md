# M2 Migration Report

**Migration:** MUSCAL-KNOWLEDGE-MIGRATION-001 · **Phase:** M2 — Foundation Docs
**Datum:** 2026-08-02 · **Status:** M2_COMPLETE
**Referenz:** KNOWLEDGE_CONSOLIDATION_PLAN.md V1.0 (§2.2/§3), FOUNDATION_SOURCE_BINDING (KF-02), M1_MIGRATION_REPORT.md, MIGRATION_MANIFEST.yaml

## Migration Summary

| Feld | Wert |
|---|---|
| Quelle | `docs/audit/` (in-Repo) |
| Ziel | `knowledge/foundation/` |
| Methode | `copy → validate → git add` (Dateinamen 1:1, `cp -p`) |
| Migrierte Docs | **18** (Doc 00, 03–19) |
| Größe | 148.080 Bytes |
| Inhaltsänderung | **keine** (Hash-Identität vor Stub-Erstellung verifiziert) |
| Redirect-Stubs | 18 an Altorten (`docs/audit/`), Header + Original-Inhalt (Historie erhalten) |

**Abweichung Doc 01/02:** Laut KNOWLEDGE_FOUNDATION_MAPPING (PB-05) und FOUNDATION_SOURCE_BINDING sind Doc 01 (AUDIT_SCOPE) und Doc 02 (REPOSITORY_CENSUS) durch die **Audit-Originale** abgedeckt — es existieren keine separaten Foundation-Dateien für 01/02. Sie liegen seit M1 unter `knowledge/reference/`. Damit ist der 20-Doc-Plan im Zielpfad vollständig: Doc 00 + 03–19 in `foundation/`, Doc 01/02 in `reference/`.

## Doc 00–19 Mapping

| Doc | Datei (Ziel: `knowledge/foundation/`) | Quelle (`docs/audit/`) | Redirect |
|---|---|---|---|
| 00 | 00_KNOWLEDGE_FOUNDATION_CHARTER_IMPLEMENTATION.md | 00_KNOWLEDGE_FOUNDATION_CHARTER_IMPLEMENTATION.md | ✓ |
| 01 | (in `knowledge/reference/AUDIT_SCOPE.md`) | — | — |
| 02 | (in `knowledge/reference/REPOSITORY_CENSUS.md`) | — | — |
| 03 | 03_SOURCE_OF_TRUTH_MAP_FOUNDATION.md | 03_SOURCE_OF_TRUTH_MAP_FOUNDATION.md | ✓ |
| 04 | 04_KNOWLEDGE_GRAPH_FOUNDATION.md | 04_KNOWLEDGE_GRAPH_FOUNDATION.md | ✓ |
| 05 | 05_DECISION_REGISTRY_FOUNDATION.md | 05_DECISION_REGISTRY_FOUNDATION.md | ✓ |
| 06 | 06_CHAT_CODE_DOC_RECONCILIATION_FOUNDATION.md | 06_CHAT_CODE_DOC_RECONCILIATION_FOUNDATION.md | ✓ |
| 07 | 07_TECHNICAL_MANUAL_CONFLICT_FOUNDATION.md | 07_TECHNICAL_MANUAL_CONFLICT_FOUNDATION.md | ✓ |
| 08 | 08_REMEDIATION_GATE_HISTORY_FOUNDATION.md | 08_REMEDIATION_GATE_HISTORY_FOUNDATION.md | ✓ |
| 09 | 09_SESSION_CONTINUITY_FOUNDATION.md | 09_SESSION_CONTINUITY_FOUNDATION.md | ✓ |
| 10 | 10_TEST_GOVERNANCE_FOUNDATION.md | 10_TEST_GOVERNANCE_FOUNDATION.md | ✓ |
| 11 | 11_TEMPORAL_ANALYSIS_FOUNDATION.md | 11_TEMPORAL_ANALYSIS_FOUNDATION.md | ✓ |
| 12 | 12_GOVERNANCE_OPERATIONS_FOUNDATION.md | 12_GOVERNANCE_OPERATIONS_FOUNDATION.md | ✓ |
| 13 | 13_ADR_INDEX_FOUNDATION.md | 13_ADR_INDEX_FOUNDATION.md | ✓ |
| 14 | 14_ARCHITECTURE_MAP_FOUNDATION.md | 14_ARCHITECTURE_MAP_FOUNDATION.md | ✓ |
| 15 | 15_CERTIFICATION_REGISTRY_FOUNDATION.md | 15_CERTIFICATION_REGISTRY_FOUNDATION.md | ✓ |
| 16 | 16_BLOCKER_REGISTRY_FOUNDATION.md | 16_BLOCKER_REGISTRY_FOUNDATION.md | ✓ |
| 17 | 17_BRIDGE_GOVERNANCE_FOUNDATION.md | 17_BRIDGE_GOVERNANCE_FOUNDATION.md | ✓ |
| 18 | 18_METRIC_REGISTRY_FOUNDATION.md | 18_METRIC_REGISTRY_FOUNDATION.md | ✓ |
| 19 | 19_KNOWLEDGE_GAP_REGISTRY_FOUNDATION.md | 19_KNOWLEDGE_GAP_REGISTRY_FOUNDATION.md | ✓ |

## Hash Validation

| Prüfung | Methode | Ergebnis |
|---|---|---|
| Anzahl Quelle/Ziel | Zählung | 18 = 18 ✓ |
| SHA256 je Datei (vor Stub-Erstellung) | `diff <(sha256sum …)` | EMPTY — 18/18 identisch ✓ |
| Aggregat-Inhalts-Hash (vor = nach) | Hash der sortierten Hash-Spalte | `9c047140bebcf5e52b9fe4037f68ae194f72421e5720251610961b93ce427a6e` ✓ |
| Keine Inhaltsänderung | `cp -p` ohne Nachbearbeitung; Ziel = Original-Inhalt nachgewiesen | bestätigt ✓ |
| Keine Namenskollision | Namensmengen-Diff | IDENTICAL ✓ |
| Keine Duplikate | `ls \| sort \| uniq -d` | 0 ✓ |
| Stub-Validierung | `stub == header + target` (18/18) | PASS ✓ |
| Manifest | `yaml.safe_load` + Asserts (phase M2, status M2_COMPLETE, 2 migrated_objects) | VALID ✓ |
| FOUNDATION_SOURCE_BINDING | Doc-Nummern/Quellen gegen Bestand abgeglichen | KONSISTENT (Doc 01/02 via reference/) ✓ |

## Redirect Status

- **18/18** Redirect-Stubs in `docs/audit/` erzeugt: Header
  `> **REDIRECT:** Diese Datei wurde migriert nach: \`knowledge/foundation/<DATEI>\``
- Original-Inhalt liegt unverändert unterhalb des Headers — **Historie bleibt erhalten** (keine Löschung, keine Inhaltskürzung).
- Stub-Erstellung idempotent (Marker `> **REDIRECT:**` → kein Doppel-Header).
- Hinweis: Die Stubs ändern die Altort-Dateien → deren Hashes weichen ab M2 von der M0-Baseline ab. Das ist erwartet (Migration) und im Manifest dokumentiert; die Baseline bleibt Rollback-Referenz.

## Blocker

1. **Keine Blocker.**
2. Vorbekannt, nicht M2-betreffend: 104 untracked Bridge-Artefakte (KG-12), RC-1/RC-2-Entscheidungen (Doc 15/16/17/19-Inhalte hängen daran, nicht der Transfer).
3. Frontmatter/Provenance-Layer weiterhin planmäßig in M4 (Auftrag: „Keine Frontmatter-Erweiterung in M2").
