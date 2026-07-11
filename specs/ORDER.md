# MAS Governance Order

## Gültigkeit
Ab dem 04. Juli 2026 für das MUSCAL CORE-Projekt.

## Regeln (Hard Constraints)

### Regel 1 — RFC-Gating
Kein neues Modul ohne MAS-RFC. Jede Code-Erweiterung muss durch einen RFC spezifiziert sein.

### Regel 2 — ADR-Gating
Jede strukturelle Änderung benötigt einen ADR (Architecture Decision Record). Ein ADR ist unwiderruflich — er kann nur durch einen *neuen* ADR ersetzt werden.

### Regel 3 — Implementation Lock
Implementierung folgt ausschließlich der SPEC. Keine "Spontan-Features".

### Regel 4 — Capability Declaration
Jede Erweiterung muss eine definierte Capability besitzen: Input, Output, Constraints, Failure Modes.

### Regel 5 — Conformance First
Kein Runtime-System ohne bestandene Test Suite. Kein Merge ohne grüne Tests.

### Regel 6 — Drei Schichten
Jeder MAS-RFC besteht aus: SPEC → REFERENCE IMPLEMENTATION → TEST SUITE.

## Verzeichnisstruktur

```
specs/
├── rfcs/          # MAS-0001 bis MAS-0600
├── adrs/          # ADR-001 bis ADR-999
├── schemas/
│   ├── json/      # JSON-Schemas
│   ├── protobuf/  # (optional)
│   └── openapi/   # (optional)
├── templates/     # RFC_TEMPLATE.md
└── ORDER.md       # diese Datei
```

## RFC-Lebenszyklus

```
DRAFT → RFC → ADR → SPEC → REFERENCE IMPLEMENTATION → TEST SUITE → FINAL
```

| Status | Bedeutung |
|--------|-----------|
| DRAFT | Ideenskizze, 1–2 Seiten |
| RFC | Lösungsvorschlag zur Diskussion |
| ADR | Entscheidung dokumentiert |
| SPEC | Vollständige Spezifikation |
| IMPL | Referenzimplementierung existiert |
| TEST | Test Suite existiert und grün |
| FINAL | RFC ist abgeschlossen |

## Dateinamen-Konvention

- RFCs: `MAS-XXXX.md` (z.B. `MAS-0001.md`)
- ADRs: `ADR-XXX.md` (z.B. `ADR-001.md`)
- Schemas: `MAS-XXXX-entity.json` (z.B. `MAS-0001-capability.json`)
