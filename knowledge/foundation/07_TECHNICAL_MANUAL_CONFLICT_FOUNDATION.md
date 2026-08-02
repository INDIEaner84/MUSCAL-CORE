# 07_TECHNICAL_MANUAL_CONFLICT_FOUNDATION.md

**Doc:** KF-1B/07 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** TECHNICAL_MANUAL_CONFLICT_REPORT.md (TC-C1/C2/H1-H3/M1/M2/L1/L2) · TECHNICAL_MANUAL_AUTHORITY_MAP.md (B3, Rangfolge) · MANUAL_RECONCILIATION_FINAL.md (B4, Resolutionen) · Manual-Dateien (M-ROOT/M-0.6/M-0.7) · REPOSITORY_CENSUS (Zahlen)
**Modus:** Read-only Konsolidierung — **keine neue Reconciliation, keine Inhaltsänderung, keine neue Autorität**
**Referenz:** B3-Autoritätsbereiche: A1 = `muscal/`-Legacy (M-ROOT), A2 = CORE-Zahlen (Census/Reconciliation)

---

## 1. Purpose

Dieses Dokument macht die Manual-Konfliktlage (3 parallele Technical Manuals mit abweichenden Zahlen) und ihre **Autoritäts-Zuordnung** (nicht Editieren) nachvollziehbar. Es ist die operative Referenz für M4-Redundanz-Rest (R4) und die v0.8-Erzeugung (Phase C).

## 2. Compared Manuals

| ID | Datei | Version | Zeilen | Letzte Änderung | Kern-Claim | Quelle |
|----|-------|---------|-------:|-----------------|------------|--------|
| M-ROOT | `Codebase/TECHNICAL_MANUAL.md` | **v0.5** (englisch) | 932 | 02.07 | „~237 files across two coexisting codebases" | Conflict-Report §1 [C0] |
| M-0.6 | `MUSCAL CORE/docs/history/technical_manual_v0.6.md` | **v0.6** (deutsch) | 1.935 | 12.07 | „~184 Python-Dateien, ~10.744 LOC, ~225 gesamt", „~45% Stubs" | §1 [C0] |
| M-0.7 | `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md` | **v0.7** (deutsch, Kurzfassung 28 Sektionen) | 371 | 15.07 | gleiche Zahlen (kopiert), „Stable Prototype" | §1 [C0] |

**Struktur-Beleg [C0]:** M-0.7 (371 Z.) ist ein Auszug; M-0.6 das Voll-Manual; M-ROOT das einzige Manual für `muscal/` (Zwei-Codebase-Scope).

## 3. Authority Hierarchy (B3/B4-Rangfolge, nicht neu)

```
1. Code (IST-Zustand)             ← C0, wörtlich aus Census
2. Zertifikate (MC-TC-*)           ← neueste Wahrheit ab 27.07
3. PROJECT_STATE                   ← Status verbindlich (20.07 + Audit-Update 01.08)
4. ADRs (kanonischer INDEX)
5. M-0.6 (Voll-Manual)             ← nur Referenz für Struktur
6. M-0.7 (Auszug)                  ← nicht zitterfähig für Zahlen/Status
7. M-ROOT (v0.5)                   ← nur für Bereich A1 (`muscal/`-Legacy)
8. docs/history/*                  ← keine Autorität
```
Quelle: MANUAL_RECONCILIATION_FINAL TC-H3-Resolution [C0]; Conflict-Report §4.

## 4. Major Conflicts (CRITICAL/HIGH — durch B4 als RESOLVED dokumentiert)

| ID | Konflikt | Severity | Resolution (B4, Autoritäts-Zuordnung) | Status |
|----|----------|----------|----------------------------------------|--------|
| TC-C1 | M-0.7 intern: „Stable Prototype" vs §8 „Keine Tests (0 Test-Dateien)" + „~45% Stubs UNGELÖST" | CRITICAL | M-0.7-Status-/Zahlen-Aussagen nicht autoritativ; verbindlich PROJECT_STATE (Status) + Census/Reconciliation (Zahlen) | ✅ RESOLVED |
| TC-C2 | Test-Counts inkonsistent (0/547/812/431/384/2.869) | CRITICAL | einzig verbindlich: 2.347 passed / 19 flaky / 1 skipped; Baseline EXPECTED_TOTAL=470 (18/18); Subset-Claims nur mit Scope | ✅ RESOLVED |
| TC-H1 | Kopierte LOC-Claims („~184/10.744/225") | HIGH | Census-Zahlen (611/77.376/1.209) einzige Quelle; weitere Zahlen müssen Scope nennen | ✅ RESOLVED |
| TC-H2 | Per-File-Line-Counts veraltet (12.07-Snapshot) | HIGH | Dateigrößen aus aktuellem Code (kernel 708, memory 162, graph 279, event_bus 111) | ✅ RESOLVED |

## 5. Resolved Conflicts (B4-Resolutionen, unverändert)

| ID | Konflikt | Resolution | Status |
|----|----------|------------|--------|
| TC-M1 | Dual-Codebase-Scope: nur M-ROOT beschreibt `muscal/` | M-ROOT bleibt Autorität für Bereich A1; CORE-Info nicht verloren | ✅ RESOLVED |
| TC-M2 | Statusvokabular-Drift (4 Wörter: Late Alpha / Stable Prototype / READY WITH RISKS / CONDITIONAL GO) | Status-Mapping: Manual-Wörter historisch; verbindlich PROJECT_STATE + MC-TC-Zertifikate | ✅ RESOLVED |

## 6. Partial Conflicts

| ID | Konflikt | Stand | Offener Teil |
|----|----------|-------|--------------|
| TC-H3 | Version-Hierarchie undefiniert (kein „supersedes X") | Rangfolge definiert (B3-Map, §3) | **Explizite Supersession-Hinweise IN den Manuals fehlen** (Inhaltsänderung, Phase C, blockiert durch B5/B6-Entscheidungen) |

## 7. Open Conflicts (Status unverändert)

| ID | Konflikt | Severity | Offen seit | Anmerkung |
|----|----------|----------|------------|-----------|
| TC-L1 | requirements.txt „vollständig" vs requirements.lock/spec.yaml | LOW | 01.08 (B4) | Autorität Teil Paket-Governance-Konzept (Phase C) |
| TC-L2 | E3.1-PHASE2-REPORT.md + E3.3_EXECUTION_LEDGER.md untracked | LOW | 01.08 (B4) | Commit als Phase-C-Item empfohlen (kein Beschluss) |

## 8. Canonical Numbers (verbindlich — aus Census/Reconciliation, kein neuer Wert)

| Kennzahl | Wert | Quelle |
|----------|------|--------|
| Python-Dateien | **611** | Census §1 [C0] |
| Python-LOC | **77.376** | Census §1 [C0] |
| Gesamt-Dateien | **1.209** | Census §1 [C0] |
| Test-Funktionen | **2.869** (204 Dateien) | Census §1 [C0] |
| Suite (nach FL-01b-Fix) | **2.347 passed / 19 flaky / 1 skipped** | Reconciliation-Final TC-C2 [C0] |
| Reconciliation-Baseline | **EXPECTED_TOTAL=470, 18/18 grün (35s)** | Reconciliation-Final [C0] |
| `kernel.py` / `memory.py` / `graph.py` / `event_bus.py` | 708 / 162 / 279 / 111 Zeilen | Census §4 [C0] |

## 9. Validation

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Keine neue Reconciliation | ✅ alle Resolutionen/Status wörtlich aus B4 (01.08); keine neue Messung |
| Keine Inhaltsänderung an Manuals | ✅ nur Referenz; keine Datei modifiziert (B4-Netto-Effekt) |
| Keine neue Autorität | ✅ Rangfolge aus B3/B4 zitiert; v0.8 nur als Phase-C-Item referenziert (nicht erzeugt) |
| Jede Aussage mit Provenance | ✅ Tabellen mit Quelle/Confidence (Conflict-Report [C0/C1/C2], Census [C0], B4 [C0]) |
| Unbekanntes als GAP | ✅ TC-L1 (Paket-Governance-Konzept fehlt), TC-L2-Commit-Status, v0.8-Erzeugung |
| Markdown only | ✅ docs/audit/07_TECHNICAL_MANUAL_CONFLICT_FOUNDATION.md |

---

*Erstellt als konsolidierte Manual-Konflikt-Referenz — keine Inhaltsänderung, keine neue Reconciliation. Stand: 02.08.2026.*
