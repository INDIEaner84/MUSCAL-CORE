# MUSCAL Knowledge Layer

**Version:** v1.0 · **Migration:** MUSCAL-KNOWLEDGE-MIGRATION-001 (M1_COMPLETE)
**Referenz:** KNOWLEDGE_CONSOLIDATION_PLAN.md V1.0, KNOWLEDGE_CONSOLIDATION_EXECUTION.md, M0_BASELINE_REPORT.md

---

## Zweck des Knowledge Layer

Der `knowledge/`-Layer ist die **versionierte, kanonische Wissensbasis** des MUSCAL-Projekts (Entscheidung X-1: Git-integriert statt extern). Er vereinheitlicht die bislang fragmentierten Wissensquellen (KF-Audit-Layer, Foundation-Docs, ADRs, Registry) unter einer einzigen Ablage mit einheitlichen Regeln.

## Struktur

```
knowledge/
├── README.md         # Dieser Layer-Index
├── reference/        # Read-only Audit-Artefakte (migriert aus KNOWLEDGE_FOUNDATION/audit/, M1)
├── foundation/       # Doc 00–19 Foundation-Dokumente (M2)
├── adr/              # Kanonische ADRs + ADR_TEMPLATE.md (M3)
├── registry/         # DECISION_REGISTRY, HDR-Records (M3/M2)
└── schema/           # document.schema.json v1.0, reference_graph.schema.json (M4)
```

> Namenskollision: `features/knowledge/` ist ein Python-Plugin (Code) — getrennte Ebene, kein Bezug zu diesem Layer.

## Source of Truth Regeln

Autoritätskette (SESSION_RULES v2.0, 8 Ebenen — unverändert):

1. `docs/PROJECT_STATE.md`
2. Audit/Zertifikate
3. Technical Baseline
4. **ADRs (`knowledge/adr/`)**
5. Engineering-Decisions
6. Historisches
7. Architektur
8. README

Layer-Regeln:

- `knowledge/reference/` ist **immutable** (Read-only-Referenz, keine Edits).
- `knowledge/foundation/` ist der einzige Ort, der referenziert statt dupliziert (KNOWLEDGE_FOUNDATION_MAPPING PB-05).
- Altorte (externes `KNOWLEDGE_FOUNDATION/`, `docs/audit/`, `spec/`) bleiben bis Gate M6 als Stubs/Referenzen bestehen — **es wird nichts gelöscht**.
- Konfliktfall entscheidet die Autoritätskette; Unklarheiten gehen in den DECISION_REGISTRY-Eintrag, nie in Direktedits.

## Schreibrechte (Agent Access Model, Plan §7)

| Ebene | Subjekt | Lesen | Schreiben |
|---|---|---|---|
| L0 | Runtime-Plugins (SUPL, Orchestrator) | via Projektion (SQLite/Chroma, ab M5) | nie `knowledge/` |
| L1 | Agenten (OpenCode, Build-Team) | via Projektion/RAG, mit `source`-Pflicht | nur über registrierte Prozesse, mit Frontmatter-Validierung |
| L2 | Human / ARB | voll | einzige Autorität für Statusänderungen (ACCEPTED, HDR, Deprecation) |

## Provenance Prinzip (X-3)

Jedes migrierte Artefakt führt seinen Identitäts-/Herkunftsnachweis (ab M4 als YAML-Frontmatter, bis dahin über `MIGRATION_MANIFEST.yaml` + M1/M0-Reports):

- `canonical_id` — stabiler, eindeutiger Bezeichner (Referenz-Key, bricht nie bei Pfadwechsel)
- `aliases` — frühere Namen/Referenzen
- `previous_locations` — alle Altorte mit Entferndatum
- `migration_history` — append-only Log der Konsolidierungsschritte (M1…M6)
- `provenance.*` — `source_type`, `source_location`, `validation_method`

Grundsatz: **Migration ist vollständig rückverfolgbar und rückgängig machbar** (Rollback-Strategie: git-revert je Schritt, Projektionen regenerierbar, externer Altbestand als dritte Sicherungsebene).

## Migrationsstatus

| Phase | Status | Commit |
|---|---|---|
| M0 — Freeze & Baseline | M0_COMPLETE | — (uncommittet, Artefakte in `knowledge/`) |
| M1 — Struktur + reference/ | M1_COMPLETE | (siehe Git-Log) |
| M2 — foundation/ | pending | — |
| M3 — adr/ | pending | — |
| M4 — Metadaten/Schema | pending | — |
| M5 — Projektionen | pending | — |
| M6 — Gate | pending | — |
