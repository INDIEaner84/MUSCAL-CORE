# 01_REPOSITORY_INVENTORY.md

**Doc:** KF-1/01 · **Date:** 2026-08-02 · **Layer:** RAW FACT / EXTRACTED METADATA
**Sources:** REPOSITORY_CENSUS.md (MUSCAL-KRA-2026-08-01), SOURCE_OF_TRUTH_MAP.md §2.1–2.2, GIT-Pre-Commit-State, laufende Dateizählungen [C0]
**Validation:** jede Zahl mit Confidence-Tag; Delta zum Census explizit

---

## 1. Repository-Struktur (Top-Level, C0)

| Verzeichnis | Dateien (Census 01.08) | Klasse | Quelle |
|-------------|------------------------|--------|--------|
| `docs/` | 402 | Doku/Governance/Audit | Census §2 |
| `tests/` | 204 | Testbasis | Census §2 |
| `features/` | 187 | Plugin/Feature-Implementierung (42 Plugin-Dirs) | Census §2 |
| `runtime/` | 62 | Core-Runtime (IMMUTABLE) | Census §2, SESSION_RULES |
| `.opencode/` | 59 | Session-Infrastruktur (SESSION_RULES v2.0) | Census §2 |
| `archive/` | 49 | Historie (ADRs 6, RFCs 18, 1 Stub) | Census §2 |
| `spec/` | 26 | Governance/ADRs/Contracts (kanonisch) | Census §2, SO-4 |
| `reconciliation/` | 25 | Governance-Enforcement (Scanner/Runner/Report) | Census §2 |
| `frontend/` | 14 | Dashboard-UI (JSX) | Census §2 |
| `guards/` | 12 | Pre-commit/CI-Guards | Census §2 |
| `muscal-mvp/` | 11 | **Zweite Implementierung** (`core/engine/mcir/ve`) | Census §2, §5 |
| `storage/` | 10 | Runtime-Storage | Census §2 |
| `baseline/` | 6 | Test-Baseline (470, 18/18) | Census §2, MANUAL_RECONCILIATION_FINAL |
| `.github/` | 5 | CI-Workflows | Census §2 |
| `scripts/` | 3 | Utilities | Census §2 |
| `specs/` (Plural) | 3 | **Duplikat-Kandidat** (ORDER.md, adrs/, schemas/, templates/) | Census §2, §5 |
| Root `*.py` | 99 | Core-Module (7.803 LOC) | Census §2, §4 |

**Delta-Status (C0, Zählung 2026-08-02):**

| Pfad | Census 01.08 | aktuell 02.08 | Änderung | Quelle |
|------|--------------|---------------|----------|--------|
| `docs/audit/` | 55 | **75** | +20 (G2…G7 + KF-00…03, committet) | Zählung |
| `docs/session_handovers/` | 14 | **17** | +3 (Backfill S-2026-07-28/30/31, PB-01) | Zählung, SESSION_CONTINUITY_AUDIT |
| `docs/governance/` | 21 | **23** | +2 | Zählung |
| Git-Commit-Anzahl | (Gap bis 20.07) | **80** | Governance-Welle 01.–02.08 committet | git log |

## 2. Komponentenklassen

| Klasse | Definition | Beispiele | Status (Charter) | Quelle |
|--------|-----------|-----------|------------------|--------|
| **Core-Immutable** | SESSION_RULES-IMMUTABLE, Root `*.py` | `kernel.py` (708 Z.), `graph.py` (279), `event_bus.py` (111), `memory.py` (162) | IMPLEMENTED | Census §4 (C0) |
| **Runtime-Systeme** | `runtime/` + `storage/` | EventStore-Layer, Graph-OS (freeze) | IMPLEMENTED (MC-TC-002…004) | Census §2, G5-Report |
| **Plugins/Features** | `features/` (alle Erweiterungen) | 42 Plugin-Dirs | IMPLEMENTED (Plugin-Contract) | Census §2, SESSION_RULES |
| **Test-/Enforcement** | `tests/`, `reconciliation/`, `guards/` | Baseline 470, Pre-Commit-Hook | IMPLEMENTED | Census §2, Reconciliation-Final |
| **Zertifikats-Infrastruktur** | `docs/audit/MC-TC-*` | 55 Cert-Docs (+20 Governance-Docs) | DOCUMENTED (C0/C1) | Census §3, G5 |
| **Frontend** | `frontend/` | Dashboard (21 JSX/TS gesamt) | IMPLEMENTED (ohne Zertifizierung) | Census §1 |
| **Zweit-Implementierung** | `muscal-mvp/` | `core/engine/mcir/ve` | CONFLICTING (Duplikat) | Census §5 (C0) |

## 3. Implementierungsbereiche (nur belegte)

| Bereich | Beleg | Confidence | Quelle |
|---------|-------|-----------|--------|
| Trust Core (MC-TC-004) | CERTIFIED | C0 | MC-TC-004, G5 |
| EventStore-Layer (E3.2) | abgeschlossen | C0 | G5, SOURCE_OF_TRUTH §2.1 |
| Graph-OS | Freeze, **nicht zertifiziert** (MC-TC-007 CONDITIONAL GO) | C0/C2 | G5 §3, Chat-Status 31.07 |
| Tool-Runtime (ADR-014) | Datei aktualisiert, Status PROPOSED (Konflikt vs PROJECT_STATE) | C1 | SOURCE_OF_TRUTH §2.6 |
| MUSCAL 2.0 / Cognitive Kernel | **CHAT_ONLY**, kein Repo-Beleg | C2 | SOURCE_OF_TRUTH §2.7 |
| D-033…035 (E3.5/E3.6 etc.) | PLANNED, chat-only | C2 | G6-04 |

## 4. Archiv-/Historie-Trennung

| Ort | Inhalt | Autorität | Quelle |
|-----|--------|-----------|--------|
| `archive/history/adrs/` (6) | historische ADRs | **keine** (Prio 6) | SESSION_RULES v2.0, Census §3 |
| `archive/history/rfcs/` (18) | historische RFCs (MAS) | **keine** | SESSION_RULES, Census §3 |
| `docs/history/` (11) | Manual v0.6, Session-Notizen | **keine** | SESSION_RULES, Census §3 |
| `spec/` + `spec/ADRs/` | kanonische ADRs (14) + Satellit (3) | **kanonisch** (SO-4: spec/ deklariert) | SOURCE_OF_TRUTH §4 SO-4 |
| `specs/` (Plural) | Duplikat-Kandidat | offen — Konsolidierung | Census §5 |
| Root-`TECHNICAL_MANUAL.md` (v0.5), `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md` | Manual-Versionen | Referenz, nie Autorität | Charter §2, SO-5 |

## 5. Offene Klassifizierungen

| Punkt | Zustand | Klärung | Quelle |
|-------|---------|---------|--------|
| 104 untracked Bridge-Handovers (`docs/bridge/handovers/`) | laufende Artefakte, nicht committet | Artefakt-Governance (Doc 17, P3) | git status [C0] |
| `muscal-mvp/` vs Core | beide beanspruchen `core/engine/mcir/ve` | Duplikations-Resolution offen | Census §5 (C0) |
| 4× ADR-Locations | spec/ (14), spec/ADRs/ (3), specs/adrs/ (1), archive (6) | SO-4 teilumgesetzt (INDEX kanonisch); F-03-Rest | Census §5, ADR_CANONICAL_MAP |
| Test-Zahl-Autorität | 4 widersprüchliche Angaben (547 / 812 / 431 / 384) | Baseline 470 (Reconciliation) erklärt (18/18) | Census §5 (C1), MANUAL_RECONCILIATION_FINAL |
| ADR-013-Fehllabel | Datei ADR-013 enthält ADR-007-Inhalt | Umbennung offen (F-03) | Census §5 (C0) |
| M3-Stale-Docs | BASELINE/ARCHITECTURE (12.07), PROJECT_STATE (20.07) | Update optional (Doc 03) | SOURCE_OF_TRUTH §2.1–2.4 |
| v0.8-Manual | fehlt; v0.8-Changelog existiert | Phase C (G6-02-Scope) | Census §6, G6-02 |

---

*Erstellt aus REPOSITORY_CENSUS + SOURCE_OF_TRUTH_MAP + laufender Zählung. Keine Implementierungsannahmen — alle Zukunftskomponenten als CHAT_ONLY/PLANNED klassifiziert.*
