# MANUAL_RECONCILIATION_FINAL — v0.5 / v0.6 / v0.7

**Phase:** G4.5 · **Block:** B4 · **Date:** 2026-08-01
**Modus:** READ-ONLY gegenüber Manual-Inhalten — Resolution erfolgt durch **Autoritäts-Zuordnung** (B3-Map), nicht durch Editieren der Manuals.
**Basis:** TECHNICAL_MANUAL_CONFLICT_REPORT.md (Audit) + TECHNICAL_MANUAL_AUTHORITY_MAP.md (B3).

---

## 1. Konflikt-Matrix

| ID | Konflikt | Severity | Resolution | Status |
|----|----------|----------|------------|--------|
| TC-C1 | M-0.7 intern widersprüchlich: „Stable Prototype" vs §8 „Keine Tests (0 Test-Dateien)" + „~45% Stubs UNGELÖST" | CRITICAL | Autoritätsregel A8/A9: Status- und Zahlen-Aussagen von M-0.7 sind **nicht autoritativ**; verbindlich sind PROJECT_STATE (Status) + Census/Reconciliation (Zahlen). M-0.7 §8 bleibt als historische Notiz bestehen — widerspricht nichts mehr, weil nicht zitterfähig | ✅ RESOLVED |
| TC-C2 | Test-Counts inkonsistent (0/547/812/431/384/2.869) | CRITICAL | Einzige verbindliche Zahl: **2.347 passed / 19 failed (dokumentiert flaky) / 1 skipped**, Reconciliation-Baseline EXPECTED_TOTAL=470 (test_regression_baseline, 18/18 grün). Subset-Claims (431 Trust Core, 384, 812 E3.2) nur mit explizitem Scope verwenden | ✅ RESOLVED |
| TC-H1 | Kopierte LOC-Claims („~184/10.744/225" in M-0.7 aus M-0.6) | HIGH | Census-Zahlen (611 Python / 77.376 LOC / 1.209 Dateien) sind die einzige Quelle; jede weitere Zahl muss Scope benennen | ✅ RESOLVED |
| TC-H2 | Per-File-Line-Counts veraltet (M-0.7 §4 = 12.07-Snapshot) | HIGH | Dateigrößen werden aus aktuellem Code bestimmt; M-0.7 beschreibt einen historischen Snapshot (in Map als Nicht-Autorität für Zahlen gekennzeichnet) | ✅ RESOLVED |
| TC-H3 | Version-Hierarchie undefiniert (kein „supersedes X") | HIGH | Rangfolge in B3-Map definiert (Code > Zertifikate > PROJECT_STATE > ADRs > M-0.6 > M-0.7 > M-ROOT > history). **Explizite Supersession-Hinweise IN den Manuals: nicht erfolgt** (wäre Inhaltsänderung, verboten) | ⚠️ PARTIAL |
| TC-M1 | Dual-Codebase-Scope: nur M-ROOT beschreibt `muscal/` | MEDIUM | M-ROOT bleibt Autorität für Bereich A1 (`muscal/`-Legacy); CORE-Konsumenten von M-0.7/M-0.6 verlieren keine CORE-Information | ✅ RESOLVED |
| TC-M2 | Statusvokabular-Drift (4 Wörter) | MEDIUM | Status-Mapping (§2 unten): verbindlicher Status = PROJECT_STATE + MC-TC-Zertifikate; Manual-Statuswörter sind historisch | ✅ RESOLVED |
| TC-L1 | requirements.txt „vollständig" vs requirements.lock/spec.yaml | LOW | Keine Entscheidung getroffen — Autorität der Lock-/Spec-Dateien ist Teil des Paket-Governance-Konzepts (Phase C) | ⚠️ OPEN |
| TC-L2 | E3.1-PHASE2-REPORT.md + E3.3_EXECUTION_LEDGER.md untracked | LOW | Nicht committet (Disk-Existenz belegt). Commit als Phase-C-Dokumentations-Item empfohlen | ⚠️ OPEN |

---

## 2. Status-Mapping (TC-M2-Resolution)

| Manual-Status | Projekt-Status (verbindlich) | Gültigkeit |
|---------------|------------------------------|------------|
| „Late Alpha / Early Beta ~45% Stubs" (M-0.6) | historisch (12.07) | nicht zitterfähig |
| „Stable Prototype" (M-0.7) | historisch (15.07); widerspricht §8 intern (TC-C1) | nicht zitterfähig |
| PROJECT_STATE „READY WITH RISKS" | aktuell (20.07, +Audit-Update 01.08) | verbindlich |
| Audit „CONDITIONAL GO" (MC-TC-007) | aktuell (27.–30.07 Zertifikate) | verbindlich für Cert-Bereiche |

---

## 3. Offene Punkte (Phase C / Governance)

| # | Punkt | Verantwortlich | Blockiert durch |
|---|-------|----------------|-----------------|
| 1 | Erzeugung eines kanonischen `TECHNICAL_MANUAL_v0.8.md` aus Census-/Reconciliation-Daten | Phase-C-Dokumentationsteam | Freigabe G4.5-Startbedingungen (B5/B6-Entscheidungen) |
| 2 | Explizite Supersession-Hinweise in M-ROOT/M-0.6/M-0.7 (Header-Zeile) — Inhaltsänderung | Phase C | G4.5-Mandat („Keine Inhalte überschreiben") |
| 3 | requirements-Autorität (TC-L1): txt vs lock vs spec.yaml | Paket-Governance | Konzept-Definition |
| 4 | Commit der 2 untracked Reports (TC-L2) | Phase C | — |
| 5 | Manuelle Verifikation der B3-Autoritätsbereiche durch Doku-Review | Review-Runde | — |

---

## 4. Netto-Effekt

- **4 CRITICAL/HIGH-Konflikte gelöst** durch Autoritäts-Regeln (kein Inhalts-Edit).
- **1 PARTIAL** (TC-H3: Rangfolge definiert, Manual-Hinweise offen).
- **2 LOW offen** (TC-L1, TC-L2) — ohne Readiness-Wirkung.
- Keine Manual-Datei modifiziert (git-Verifikation).

---

*Referenz-Kette: AUDIT → TC-Report → B3-Autoritäts-Map → diese Finale. Manuals bleiben unverändert (README-konsistent: „baseline documents take precedence").*
