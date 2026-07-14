# MUSCAL CORE — Anlage-Strategie

## Ziel
Aus den ChatGPT-Rohdaten in `/home/hz/Downloads/` eine saubere, strukturierte MAS-RFC-Dokumentenlandschaft aufbauen:
- `archive/history/rfcs/` (MAS-RFCs, historisch)
- `spec/` (Architecture Decision Records)
- `docs/` (Blueprint + SDD + Manual)
- `white-paper/` (externe Kommunikation)

## Status-Legende
- ✅ Erstellt
- 🔄 In Arbeit
- ⏳ Geplant
- ❌ Entfällt (Stub ohne Inhalt)

---

## Phase 0: Struktur (erledigt)

| Aktion | Status | Pfad |
|--------|--------|------|
| Verzeichnisse anlegen | ✅ | `archive/history/rfcs/`, `spec/`, `specs/schemas/json/`, `specs/templates/`, `docs/`, `white-paper/` |
| ORDER.md | ✅ | `specs/ORDER.md` |
| RFC_TEMPLATE.md | ✅ | `specs/templates/RFC_TEMPLATE.md` |

---

## Phase 1A: MAS-Basisserie (MAS-0000 bis MAS-0010)

**Quelle:** `MAS Architektur Spezifikation.md` (3.276 Zeilen) + `MAS-0001 Architecture Principles.md` (14.497 Zeilen)

| RFC | Titel | Quelle | Status |
|-----|-------|--------|--------|
| MAS-0000 | Governance & Entwicklungsregeln | MAS Architektur Spezifikation §0 | ⏳ |
| MAS-0001 | Architecture Principles (10 Prinzipien) | MAS-0001.md + MAS Architektur Spezifikation §1 | ⏳ |
| MAS-0002 | Capability Registry & Lifecycle | MAS Architektur Spezifikation §2 | ⏳ |
| MAS-0003 | Event Bus & Causal State System | MAS Architektur Spezifikation §3 | ⏳ |
| MAS-0004 | MPIR Compiler & AST Transformation | MAS Architektur Spezifikation §4 | ⏳ |
| MAS-0005 | Execution Semantics & Deterministic Runtime | MAS Architektur Spezifikation §5 | ⏳ |
| MAS-0006 | Capability Security & Permissioned Tools | MAS Architektur Spezifikation §6 | ⏳ |
| MAS-0007 | MREIL Core Metric Engine | MAS Architektur Spezifikation §7 | ⏳ |
| MAS-0008 | System Orchestration Layer | MAS Architektur Spezifikation §8 | ⏳ |
| MAS-0009 | Distributed Execution Fabric | MAS Architektur Spezifikation §9 | ⏳ |
| MAS-0010 | System Closure Layer | MAS Architektur Spezifikation §10 | ⏳ |

---

## Phase 1B: Erweiterte RFCs

| RFC | Titel | Quelle | Status |
|-----|-------|--------|--------|
| MAS-0011 | State Equivalence Layer (SEL) | SEL + Reducer Confluence Kernel.md (951 Z.) | ⏳ |
| MAS-0012 | Observability System | Observability Spezifikation.md (6.032 Z.) | ⏳ |
| MAS-0100 | Storage API (Checkpoint v1.5) | MAS-0100 Architektur Checkpoint.md (5.748 Z.) | ⏳ |
| MAS-0300 | MAS Virtual Machine | MUSCAL CORE Prioritäten.md §15 (1.866 Z.) | ⏳ |
| MAS-0301 | Execution Graph Compiler | MUSCAL CORE Prioritäten.md §15 | ⏳ |
| MAS-0400 | Distributed Fabric (erweitert) | MUSCAL Production System.md (6.777 Z.) | ⏳ |
| MAS-0500 | Self-Evolving Optimization | MUSCAL AI Module 4 (2.055 Z.) | ⏳ |

---

## Phase 1C: ADRs

| ADR | Titel | Status |
|-----|-------|--------|
| ADR-001 | Execution Graph Compiler statt Interpreter | ⏳ |
| ADR-002 | Layer-Architektur mit Spine-Validierung | ⏳ |
| ADR-003 | Capability-First statt Model-First | ⏳ |

---

## Phase 2: Architecture Blueprint

| Datei | Beschreibung | Status |
|-------|-------------|--------|
| `docs/ARCHITECTURE_BLUEPRINT.md` | Management-Sicht, ~10 Seiten, kein Code | ⏳ |

---

## Phase 3: System Design Document

| Datei | Beschreibung | Status |
|-------|-------------|--------|
| `docs/SYSTEM_DESIGN.md` | IEEE 1016-2009, ~30 Seiten, kein Code | ⏳ |

---

## Phase 4: White Paper

| Datei | Beschreibung | Status |
|-------|-------------|--------|
| `white-paper/MUSCAL_CORE_WHITEPAPER.md` | Extern, ~20 Seiten, kein Code | ⏳ |

---

## Phase 5: TECHNICAL_MANUAL.md erweitern

| Sektion | Titel | Quelle | Status |
|---------|-------|--------|--------|
| §15 | MAS RFC-Architektur | MAS-0000 | ⏳ |
| §16 | Capability System | MAS-0002, MAS-0006 | ⏳ |
| §17 | MPIR Compiler Pipeline & MREIL | MAS-0004, MAS-0007 | ⏳ |
| §18 | State Equivalence Layer (SEL) | MAS-0011 | ⏳ |
| §19 | MAS-VM & Formal Verification | MAS-0300, MAS-0301 | ⏳ |
| §20 | MUSCAL Production System | MAS-0400 | ⏳ |
| §21 | Observability System | MAS-0012 | ⏳ |
| §22 | Ausblick & Roadmap | Querschnitt | ⏳ |

---

## Downloads — Relevanzmatrix

| Datei | Größe | Relevanz | Verwendung | Status |
|-------|-------|----------|------------|--------|
| MAS-0001 Architecture Principles.md | 14.497 Z. | Hoch | MAS-0001 RFC | ⏳ |
| MAS-0100 Architektur Checkpoint.md | 5.748 Z. | Hoch | MAS-0100 RFC | ⏳ |
| MAS Architektur Spezifikation.md | 3.276 Z. | Hoch | MAS-0000 bis MAS-0010 | ⏳ |
| MUSCAL Production System.md | 6.777 Z. | Hoch | MAS-0400 + §20 | ⏳ |
| MUSCAL CORE Prioritäten.md | 1.866 Z. | Hoch | MAS-0300, MAS-0301 | ⏳ |
| SEL + Reducer Confluence Kernel.md | 951 Z. | Hoch | MAS-0011 + §18 | ⏳ |
| MUSCAL Observability Spezifikation.md | 6.032 Z. | Hoch | MAS-0012 + §21 | ⏳ |
| MUSCAL AI Module 4 | 2.055 Z. | Mittel | MAS-0500 | ⏳ |
| Module 3,5,6,7,8,9 | 11 Z. | ❌ | Stubs ohne Inhalt | ❌ |
| MUSCAL Architektur und Analyse.md | 10.260 Z. | Mittel | Querschnitts-Validierung | ⏳ |
| MUSCAL TEAM MASTER.md | 10.016 Z. | Mittel | Querschnitts-Validierung | ⏳ |
| MUSCAL Team Review.md | 32.111 Z. | Mittel | Qualitätskontrolle | ⏳ |

---

## Reihenfolge (kritischer Pfad)

```
Phase 0: Struktur          ✅
    │
    ▼
Phase 1A: MAS-0000–0010
    │
    ▼
Phase 1B: MAS-0011, -0012, -0100, -0300, -0301, -0400, -0500
    │
    ▼
Phase 1C: ADR-001–003
    │
    ▼
Phase 2: ARCHITECTURE_BLUEPRINT.md
    │
    ▼
Phase 3: SYSTEM_DESIGN.md
    │
    ▼
Phase 4: WHITEPAPER.md
    │
    ▼
Phase 5: TECHNICAL_MANUAL.md §15–22
```
