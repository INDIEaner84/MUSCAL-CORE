# 10_TEST_GOVERNANCE_FOUNDATION.md

**Doc:** KF-1/10 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources (autoritativ):** G2_EXECUTION_RESULT (Validation-Report §4) · G2_ADJUDICATION_REPORT.md (§1–§4) · G5_MEASUREMENT (G5 §1/§3) · DECISION_REGISTRY (D-016, D-017, D-040, D-041, D-042) · SESSION_RULES v2.0 (Plugin-Contract, Core-Immutable, Guards) · FL01A_FLAKINESS_REGISTER.md · MC-TC-004_ARB_DECISION / MC-TC-006-REPLAY-CERTIFICATION / MC-TC-007_STATUS_ZUSAMMENFASSUNG + TRUST-GOVERNANCE · REPOSITORY_CENSUS.md · MASTER_INDEX.md (TF-06)
**Modus:** Read-only Extraktion und Konsolidierung — **keine Testausführung, keine Neuberechnung, keine neuen Governance-Regeln, keine neuen Anforderungen**

---

## 1. Purpose

Dieses Dokument konsolidiert die Test-Governance des MUSCAL-CORE: Testlandschaft (Taxonomie), verbindliche Kennzahlen (Baseline-Registry), dokumentierte Defekte (FL-01a), Zertifizierungs-Stand (MC-TC-004/006/007) und offene Lücken. Es liefert die operative Referenz für M1-Evidence (Test-Suite) und macht die Zahlen-Kette (Census → G2 → G4/G5) nachvollziehbar.

**Grundsatz:** Alle Zahlen wörtlich aus belegten Quellen; unbekannte Zustände als GAP; Chat-Evidenz ausschließlich als CHAT_ONLY.

## 2. Scope

| In | Out (bewusst) |
|----|----------------|
| Testlandschaft, Baseline-Zahlen, Flakiness-Registry, Zertifizierungs-Stand, Gaps | Code-/Test-Änderungen, neue Testanforderungen, neue Metriken, Testausführung |
| Quellen: G2-Reports, G5, Registry D-IDs, FL-01a-Register, MC-TC-004/006/007, Census, MASTER_INDEX | ADR-/Status-Änderungen, FL-01a-Fix-Entscheidung |

## 3. Test Governance Model

| Element | Beleg | Quelle |
|---------|-------|--------|
| Lauf-Zustand: 19 failed / 2.347 passed / 1 skipped (nach FL-01b-Fix 01.08) | G4-M1, G5 §1 | G4_MEASUREMENT [C0] |
| Baseline-Vor-Fix-Zustand: 23 failed / 2.343 passed / 1 skipped (2.367 collected, 2× reproduziert) | FL-01a-Register §1 | Register [C0] |
| Governance-Durchsetzung: Pre-Commit-Hook + `reconciliation/`-Scanner + Guards | Census §2/§8 | Census [C0] |
| Core-Immutability: Guards validieren Core-Schreibzugriffe (OVERRIDE-Pflicht) | SESSION_RULES v2.0, D-020 | SESSION_RULES [C0] |
| Governance-Validierung G2: 0 Violations bei Phasen-Commits (Override-Pattern) | G2-Exekution | G2-Report [C0] |
| Test-Zahl-Autorität: 4 Quellen (547/812/431/384) widersprüchlich vs 2.869 real | Census §5, TF-06 | MASTER_INDEX [C1] |

## 4. Test Taxonomy

| Kategorie | Definition | Belege/Beispiele | Quelle |
|-----------|-----------|------------------|--------|
| **Unit** | Funktionen/Module isoliert | 204 Test-Dateien, 2.869 `def test_` (Census) | Census §1 [C0] |
| **Integration** | Modul-übergreifende Reihen | test_worker.py (6), test_tool_runtime_phase3.py (6), test_runtime_convergence.py (2), test_pipeline_phase4.py (1) | FL-01a-Register §3 [C0] |
| **Reconciliation** | Scanner-/Baseline-Tests (broken-link, ADR-Validator, Import-Validator, Drift) | `tests/reconciliation/test_regression_baseline.py`; **18/18 grün, 35s-Lauf** | MANUAL_RECONCILIATION_FINAL, G4-M1 [C0] |
| **Certification** | Zertifizierungs-relevante Testläufe | MC-TC-004: **431/431**, 33/33 Kriterien, 14/16 Invarianten | MC-TC-004_ARB_DECISION, D-016 [C0/C1] |
| **Governance** | Regel-/Hook-Validierung | Pre-Commit-Hook, `override_052_is_active()`==True, `guards/` | G2-Report, D-020 [C0] |

## 5. Baseline Registry (verbindliche Kennzahlen — keine Neuberechnung)

| Kennzahl | Wert | Beleg | Confidence |
|----------|------|-------|------------|
| Reconciliation-Baseline | **470** (EXPECTED_TOTAL) | MANUAL_RECONCILIATION_FINAL; Recalibrierung D-041 (94/471 → 470, test-only, `5d728c7`) | C0 |
| Reconciliation-Tests | **18/18 grün** (35s-Lauf) | G4-M1, MANUAL_RECONCILIATION_FINAL | C0 |
| Passed (Suite, nach Fix) | **2.347** | G4-M1, G5 §1 | C0 |
| Flaky (FL-01a) | **19** | FL-01a-Register §2/§3 (vollständiges Register) | C0 |
| Vor-Fix-Zustand | 23 failed / 2.343 passed / 1 skipped (2.367 collected) | Register §1 (2× reproduziert) | C0 |
| Collekted gesamt | 2.367 | Register §1 | C0 |

**Hinweis (belegt, kein Rechenartefakt):** 2.343 (vor) vs 2.347 (nach FL-01b-Fix) sind zwei dokumentierte Messzustände — 470er-Baseline erklärt die Reconciliation-Zahl; Gesamt-Testfläche bleibt 2.869 Funktionen (Census).

## 6. Flakiness Registry (FL-01a)

| Feld | Inhalt | Quelle |
|------|--------|--------|
| ID | FL-01a — 19 reihenfolge-abhängige Fehlschläge | G2 §2, Register §2 |
| Betroffene Module | test_worker.py (6), test_tool_runtime_phase3.py (6), test_specialized_cu_phase5.py (3), test_runtime_convergence.py (2), test_pipeline_phase4.py (1), test_phase6_production_readiness.py (1) | Register §2 [C0] |
| Root Cause | **Globale Singleton-Zustände** ohne Test-Reset: `_UTR`/`set_global_utr()` (`tools.py:9-24`), `set_global_event_store()` (`tool_runtime.py:28-33`), `set_global_default_timeout()` (`tool_runtime.py:37-42`), `_GLOBAL_EVENT_STORE`-Registry (MC-TC-005.1) | Register §4 [C1] |
| Verhalten | 100 % grün isoliert/Subset (verifiziert 177/177, 176+1); `AttributeError`-Muster, fehlende Capabilities | Register §2/§4 [C0/C1] |
| Impact | (a) CI-Reihenfolge-abhängige Fehlschläge; (b) Recalibrierungs-Drift-Risiko (EXPECTED_TOTAL könnte erneut falsch); (c) falsche Alarmierung verschleiert echte Regressionen | G5 §3 B7 [C1] |
| Current Status | **DOCUMENTED (D-040)** — NICHT gefixt (Mission-Control-Direktive); Fix deferred: test-scoped autouse Fixtures (test-only) + **D-042 Global-State-ADR** als Follow-up; ARB-Freigabe erforderlich (RC-3) | Register §5/§6, G5 §3 B7, DECISION_REGISTRY D-040/D-042 [C1] |
| Mitigation heute | Subset-Lauf / Isolation dokumentiert; CI-Ordnungs-Pinning **nicht konfiguriert** (GAP) | Register §6 [C0] |

## 7. Certification Registry

| Zertifikat | Ergebnis | Datum | Beleg | Status (Registry) |
|------------|----------|-------|-------|-------------------|
| **MC-TC-004** Trust Core | **CERTIFIED** — 33/33 Kriterien, 431/431 Tests, 14/16 Invarianten | 30.07 | MC-TC-004_ARB_DECISION + CERTIFICATION_REPORT (10 Artefakte, committet `392734e` 01.08) | D-016 IMPLEMENTED [C1] |
| **MC-TC-006** Replay & Deterministic Reconstruction | **CERTIFIED / GO** — PURE OBSERVATION, kein Produktionscode geändert | 27.07 | MC-TC-006-REPLAY-DETERMINISTIC-RECONSTRUCTION-CERTIFICATION | D-036-Basis (C1-Cluster) [C1] |
| **MC-TC-007** (Reihe) | **CONDITIONAL GO** (31.07) — Graph-OS-Layer **nicht zertifiziert**, 2 P0-Blocker (P0-1 Reconstruction, P0-2 Watchdog-Persistenz); Trust-Governance-Teil: **NO-GO** (30.07) | 27.–31.07 | MC-TC-007_STATUS_ZUSAMMENFASSUNG (31.07, Status-Statement ursprünglich **CHAT_ONLY**, gespiegelt 01.08 in PROJECT_STATE-P0, d5f5ce7), MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION (NO-GO), MC-TC-007-FULL-REALITY-CLOSURE (27.07) | D-017 DOCUMENTED [C2→C1 nach Spiegelung] |

## 8. Known Gaps (Status unverändert)

| # | Gap | Status | Quelle |
|---|-----|--------|--------|
| G-1 | FL-01a ungefixt — 19 Tests reihenfolge-abhängig | DOCUMENTED (D-040); Fix deferred (Phase B, RC-3) | Register §5, G5-B7 |
| G-2 | D-042 Global-State-ADR (Singleton-Policy `_UTR`/Event-Store) | PLANNED; ARB-Freigabe offen (RC-3) | DECISION_REGISTRY D-042, G5-B7 |
| G-3 | P0-1/P0-2 (Graph-OS Reconstruction, Watchdog-Persistenz) | **PENDING HUMAN** (RC-1) — blockiert MC-TC-007-Vollzertifizierung | G5 §3 B5, PROJECT_STATE:45-49 |
| G-4 | CI-Ordnungs-Pinning nicht konfiguriert | offen (Register §6) | FL-01a-Register |
| G-5 | Recalibrierungs-Drift-Risiko (EXPECTED_TOTAL könnte erneut falsch sein) | offen (B7-Risiko) | G5 §3 B7 |
| G-6 | Test-Zahl-Autorität: 4 widersprüchliche Claims (547/812/431/384) | teilaufgelöst (Baseline 470/18-18 grün erklärt; Rest offen) | Census §5, TF-06, MANUAL_RECONCILIATION_FINAL |

## 9. Validation Rules (dieses Dokument)

| # | Regel |
|---|-------|
| 1 | Read-only Dokumentation — keine Datei außer diesem Dokument verändert |
| 2 | Keine Testausführung (alle Laufzahlen aus belegten Quellen, Stand 01.08) |
| 3 | Keine Neuberechnung — 470/18/2.347/19 wörtlich übernommen; Vor-/Nach-Fix-Zustand getrennt dokumentiert |
| 4 | Jede Aussage mit Provenance (Quelle + Confidence in Tabellen) |
| 5 | Chat-Evidenz ausschließlich CHAT_ONLY: MC-TC-007-Status-Statement 31.07 (gespiegelt 01.08 → DOCUMENTED, d5f5ce7) |
| 6 | IMPLEMENTED nur bei C0/C1: D-016/D-036 (MC-TC-004/006, Cert-Artefakte), D-040/D-041 (Register, Commit `5d728c7`) |
| 7 | Unbekanntes als GAP: Pinning-Status, Recalibrierungs-Zukunft (G-4, G-5) |
| 8 | Keine neuen Metriken, keine neuen Governance-Regeln, keine neuen Testanforderungen |

## 10. Evidence Binding

| Kennzahl/Status | Quelle | Evidence Level | Status |
|-----------------|--------|----------------|--------|
| Suite 19/2.347/1 | G4-M1, G5 §1 | C0 | aktuell (01.08) |
| Suite 23/2.343/1 (Vor-Fix) | FL-01a-Register §1 | C0 | historisch (01.08, vor `5d728c7`) |
| Baseline 470, 18/18 | MANUAL_RECONCILIATION_FINAL, G4-M1 | C0 | aktuell |
| FL-01a Root Cause | Register §4, G2 §2 | C1 | dokumentiert (D-040) |
| MC-TC-004 CERTIFIED | ARB_DECISION, D-016 | C1 | committet (392734e) |
| MC-TC-006 CERTIFIED/GO | 006-Replay-Certification, G2-01 | C1 | committet |
| MC-TC-007 CONDITIONAL GO | 007-Status (31.07, CHAT_ONLY→PROJECT_STATE d5f5ce7) | C2/C1 | DOCUMENTED (D-017) |
| MC-TC-007 Trust-Governance NO-GO | 007-TRUST-GOVERNANCE-CERTIFICATION | C1 | DOCUMENTED |
| Testfläche 2.869 / 204 Dateien | Census §1 | C0 | Stand 01.08 |
| Claim-Widersprüche 547/812/431/384 | Census §5, MASTER_INDEX TF-06 | C1 | teilaufgelöst (G-6) |

---

*Erstellt als konsolidierte Test-Governance-Referenz — keine neue Ausführung, keine neuen Regeln, keine Neuberechnung. Stand: 02.08.2026.*
