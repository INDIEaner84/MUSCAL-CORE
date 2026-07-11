---
rfc: MAS-XXXX
title: "Kurzer, prägnanter Titel"
layer: L0–L4          # Storage | Runtime | Cognitive | Control | Observability
status: DRAFT          # DRAFT | RFC | ADR | SPEC | IMPL | TEST | FINAL
author: "System / Name"
date: YYYY-MM-DD
supersedes:            # Optional: welchen RFC ersetzt dies?
dependencies:          # Optional: welche RFCs werden vorausgesetzt?
  - MAS-XXXX
  - MAS-XXXX
---

# MAS-XXXX: Titel

## 1. Motivation

- Warum existiert dieser RFC?
- Welches Problem wird gelöst?
- Was passiert ohne diese Spezifikation?

## 2. Terminologie

| Begriff | Definition |
|---------|-----------|
| Fachbegriff A | Präzise, nicht-zirkuläre Definition |
| Fachbegriff B | ... |

## 3. Systemmodell

Textuelle Beschreibung des Subsystems, seiner Grenzen und seiner Umgebung.

```
┌─────────────────────────────────────────┐
│           Systemkontext                 │
│                                         │
│  ┌──────────┐    ┌──────────┐          │
│  │ Komp. A  │◄──►│ Komp. B  │          │
│  └──────────┘    └──────────┘          │
│       │                                 │
│       ▼                                 │
│  ┌──────────┐                           │
│  │ Komp. C  │                           │
│  └──────────┘                           │
└─────────────────────────────────────────┘
```

## 4. Architektur

### 4.1 Zuständigkeiten

| Komponente | Verantwortung | Konsumiert | Produziert |
|-----------|--------------|------------|------------|
| Komp. A | Kurzbeschreibung | Input-Typen | Output-Typen |

### 4.2 Invarianten

Zwingende Regeln, die dieses Subsystem einhalten muss.

## 5. API-Contracts

```
Schnittstelle: <Name>
  Input:
    - <Parameter>: <Typ> — <Beschreibung>
  Output:
    - <Feld>: <Typ> — <Beschreibung>
  Precondition:
    - <Bedingung>
  Postcondition:
    - <Zustand nach Aufruf>
  Error Cases:
    - <Fehlercode>: <Bedingung>
```

### 5.2 Events

| Event-Typ | Payload | Origin Layer | Target Layer |
|-----------|---------|-------------|-------------|
| `event.name` | `{...}` | L2 | L1 |

## 6. Datenmodelle

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "<EntityName>",
  "type": "object",
  "properties": {
    "id":            { "type": "string", "description": "..." },
    "type":          { "type": "string", "enum": ["a", "b"] },
    "payload":       { "type": "object" }
  },
  "required": ["id", "type"]
}
```

## 7. Fehlerfälle

| Fehler | Ursache | Erkennung | Reaktion |
|--------|---------|-----------|----------|
| <Name> | <Auslöser> | <Prüfung> | <Recovery> |

## 8. Sicherheit

- **Capability-Gating:** Welche Capability wird benötigt?
- **Validierung:** Welche Input-Validierung ist erforderlich?
- **Isolation:** Wie wird das Subsystem abgeschottet?
- **Audit:** Welche Events werden geloggt?

## 9. MREIL-Metriken

| Dimension | Metrik | Zielwert | Messmethode |
|-----------|--------|----------|-------------|
| Memory | <Name> | >0.9 | <Beschreibung> |
| Reasoning | <Name> | >0.8 | <Beschreibung> |
| Execution | <Name> | <100ms | <Beschreibung> |
| Integrity | <Name> | 1.0 | <Beschreibung> |
| Load | <Name> | <0.7 | <Beschreibung> |

## 10. ADR-Referenzen

- **ADR-XXX** — Kurzbeschreibung der Entscheidung

## 11. Offene Fragen

- [ ] Frage 1
- [ ] Frage 2

## 12. Conformance Implications

- Was muss ein System erfüllen, um MAS-XXXX-konform zu sein?
- Welche Tests sind minimal erforderlich?
