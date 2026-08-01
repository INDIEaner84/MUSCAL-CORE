# TECHNICAL_MANUAL_v0.8_SCOPE — Vorbereitung für das kanonische Handbuch

**Gate:** G6-02 · **Date:** 2026-08-01 · **Modus:** READ/WRITE (docs/audit/)
**Zweck:** Scope-Definition für das künftige `TECHNICAL_MANUAL_v0.8.md` — **das Manual selbst wird hier NICHT erzeugt** (Erzeugung = Phase-C-DOC-Item, TC-H3/RC-5).
**Referenz:** REPOSITORY_CENSUS.md (Zahlen), TECHNICAL_MANUAL_AUTHORITY_MAP.md (A1–A10), MANUAL_RECONCILIATION_FINAL.md, G5_READINESS_REPORT.

---

## 1. Verbindliche Zahlen (aus Census/Reconciliation — einzige zitierfähige Quelle)

| Kennzahl | Wert | Quelle | Gültigkeitsstand |
|----------|------|--------|------------------|
| Gesamtdateien (ohne node_modules/.git/__pycache__/build) | **1.209** | REPOSITORY_CENSUS §1 [C0] | 2026-08-01 |
| Python-Dateien | **611** | dito | 2026-08-01 |
| Python-LOC | **77.376** | dito | 2026-08-01 |
| Markdown-Dateien | **422** | dito | 2026-08-01 |
| YAML-Dateien | **108** | dito | 2026-08-01 |
| Frontend-Dateien (JSX/TS) | **21** | dito | 2026-08-01 |
| Root-Python-Module (Core) | **99** / 7.803 LOC | Census §4 | 2026-08-01 |
| Test-Dateien (`tests/`) | **204** | Census §1 | 2026-08-01 |
| Test-Funktionen (Summe) | **2.869** | Census + MASTER_INDEX | 2026-08-01 |
| Suite-Ergebnis (G2/G4/G5-Verifikation) | **2.347 passed / 19 failed (dokumentiert flaky, FL-01a) / 1 skipped** | pytest-Läufe | 2026-08-01 |
| Reconciliation-Baseline | EXPECTED_TOTAL **470** (14 A / 5 B / 412 C / 3 D / 36 E) | tests/reconciliation/test_regression_baseline.py | 18/18 grün |

> **Zitierregel (A8):** KEINE anderen Zahlen in v0.8 übernehmen (die 3 Alt-Manuals
> v0.5/v0.6/v0.7 enthalten unterzählte/kopierte Werte — TC-H1/TC-C2).

## 2. Aktuelle Architekturdefinition (nur implementierte Systeme)

| Ebene | Implementierter Stand | Evidence |
|-------|------------------------|----------|
| L0 Storage | SQLite-EventStore `stored_events` (Single Event Authority, MC-TC-005.3 CERTIFIED) | MC-TC-005.3, ADR-010/012 |
| L1 Kernel | Single Pipeline Authority (ADR-001 APPLIED); Core-Dateien immutable (ADR-007) | spec/ADR-001, ADR-007 |
| L2 Runtime | Unified Tool Runtime (ADR-014 ACCEPTED); EventStore-Replay (MC-TC-006 CERTIFIED) | ADR-014, MC-TC-006 |
| L3 Memory/Graph | GraphMemory in-memory (P0-1 offen — Rebuild-Code fehlt) | MC-TC-007 Phase H FAIL |
| L4 Verification | Verification Layer `features/event_sourcing/` (ADR-011; MC-TC-004 CERTIFIED) | ADR-011, MC-TC-004 |
| L5 Plugins/Features | `features/`-Plugin-System (ADR-004); Trust-Core-Features (Identity, Replay, UTR) | ADR-004, 771d19f…595533b |
| L6 Frontend | 21 JSX/TS-Dateien (bestehend) | Census §1 |
| System Spine | Enforcement vorhanden (D-002, M-0.6 §14; Re-Validierung 08/2026 ausstehend) | M-0.6, ADR-002 |

## 3. Abgrenzung implementiert vs geplant (Pflicht-Kapitel in v0.8)

**NUR als „geplant/Entwurf" darstellen — nicht als implementiert:**

| System | Status | Referenz |
|--------|--------|----------|
| MUSCAL 2.0 Hybrid-Architektur | **DRAFT/PROPOSED** (ADR-022) — kein Code | ADR-022 |
| Cognitive Kernel + Authoritative Runtime (Edge) | **DRAFT/PROPOSED** (ADR-023) — kein Code | ADR-023 |
| Agent-Architektur P1–P5 | **DRAFT/PROPOSED** (ADR-024) — kein Code | ADR-024 |
| Cognitive Compiler / RFC-Serie | **DRAFT/PROPOSED** (ADR-025) — kein Code | ADR-025 |
| E3.6 Knowledge Distillation | **PLANNED** (D-030) — kein Code | DECISION_REGISTRY |
| SLM-Datenstrategie / Benchmark / Closed-Source | **PLANNED** (D-033…D-035, chat-only) | DECISION_REGISTRY |
| MC-TC-005 | **NOT AUTHORIZED** — keine Umsetzung | MC-TC-004_ARB_DECISION |

**Abgrenzungsregel für v0.8:** Jedes System erscheint nur mit einer Status-
Kennzeichnung aus {IMPLEMENTED [Evidence], PARTIAL [Evidence], CERTIFIED
[Zertifikat], DRAFT, PLANNED, NOT AUTHORIZED}. Kein „geplant"-System darf in
Kapiteln über Architektur- oder API-Beschreibungen erscheinen.

## 4. Verweis auf Audit Authority Map

- **Autoritätsbereiche:** TECHNICAL_MANUAL_AUTHORITY_MAP.md (A1–A10) — v0.8 übernimmt die Zuständigkeiten: `muscal/`-Legacy → M-ROOT bleibt Quelle (A1); CORE-Referenz → v0.8 löst M-0.6 ab (A2–A4); Stabilisierungs-/Changelog-Kapitel → M-0.7 (A5–A7); Zahlen → §1 dieser Datei (A8); Status → PROJECT_STATE + Zertifikate (A9).
- **Rangfolge nach v0.8-Existenz:** Code > Zertifikate > PROJECT_STATE > ADRs > **v0.8** > M-0.6 > M-0.7 > M-ROOT > history.
- **Supersession-Effekt:** v0.8 ist der Nachfolger aller drei Manuals; die expliziten Header-Hinweise (TC-H3) sind Bestandteil des v0.8-Freigabe-Artefakts (G6-03-Matrix: PARTIAL→RESOLVED).

## 5. Scope-Grenzen (bewusst ausgeschlossen)

| Ausgeschlossen | Begründung |
|----------------|------------|
| `node_modules/`, `build/`, `__pycache__/` | nicht Teil der Dokumentation |
| `docs/bridge/handovers/` (Live-Artefakte) | Laufzeitgeneriert, Artefakt-Governance offen |
| Veraltete Manual-Inhalte (v0.5–v0.7-Zahlen) | TC-H1/TC-C2 — nicht zitierfähig |
| Zukünftige Systeme als Implementierungs-Kapitel | §3-Abgrenzung |

## 6. Nächste Schritte (Phase C, nach Freigabe)

1. Freigabe dieses Scopes (Governance-Review).
2. Generierung `TECHNICAL_MANUAL_v0.8.md` aus Census/Reconciliation/Zertifikaten.
3. Header-Supersession-Hinweise (TC-H3) in v0.5/v0.6/v0.7.
4. `docs/history/`-Archivierung der Alt-Manuals (keine Löschung).

---

*G6-02 erstellt — Scope-Dokument, kein Manual-Inhalt. Keine zukünftigen Systeme als implementiert dargestellt.*
