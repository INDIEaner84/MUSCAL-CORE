# 15 — Certification Registry Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only; keine neue Zertifizierung, keine Statusänderung)
- Quellen (ausschließlich MC-TC-Artefakte): docs/audit/MC-TC-004_* (CERTIFICATION_REPORT, ARB_DECISION, ARCHITECTURE_REVIEW_DECISION, IMPLEMENTATION_REPORT), MC-TC-006-REPLAY-DETERMINISTIC-RECONSTRUCTION-CERTIFICATION.md, MC-TC-007-* (STATUS_ZUSAMMENFASSUNG, FULL_REALITY_CLOSURE_CERTIFICATION, TRUST_GOVERNANCE_CERTIFICATION), REFERENCE_GRAPH.md, G2_ADJUDICATION_REPORT (G2-01), SESSION_CONTINUITY (Doc 09 M-2)

## 1 Purpose

Registrierung aller bestehenden MC-TC-Zertifizierungsergebnisse (004, 006, 007) mit Status, Geltungsbereich, Beleg und Commit-Evidence. Keine neue Zertifizierung; nur Wiedergabe der vorhandenen Artefakte.

## 2 Scope

- Aufgenommen: MC-TC-004, MC-TC-006, MC-TC-007 (alle Artefakte mit Zertifizierungsergebnis), MC-TC-005 (Nicht-Zertifizierung, belegt).
- Nicht aufgenommen: MC-TC-001…003-Artefakte ohne Zertifizierungsergebnis; Implementierungsdetails ohne Statusrelevanz.

## 3 Certification Model

- **Geltungsbasis:** Zertifikate gelten nur für den im jeweiligen Artefakt genannten Scope und Review-Datum; MC-TC-004 = ARB-Freigabe mit COMMIT-WINDOW/RESTRICTED-SCOPE; MC-TC-006 = PURE OBSERVATION (kein Code geändert); MC-TC-007 = INDEPENDENT CERTIFICATION GATE (kein Code geändert).
- **Verbindlichkeit:** Zertifizierung nur über Artefakt + Commit (Audit-Welle `392734e`, 55 Artefakte, committet 01.08); bis dahin untracked = keine Commit-Autorität (REFERENCE_GRAPH N-DOC-07/08).

## 4 MC-TC-004 — Trust Core Hardening: CERTIFIED

| Feld | Wert | Beleg |
|---|---|---|
| Ergebnis | **CERTIFIED** (ARB, 30.07) | MC-TC-004_CERTIFICATION_REPORT.md, G2-01 („MC-TC-004 CERTIFIED 30.07“) |
| Pre-Gate | GO | MC-TC-004_ARCHITECTURE_REVIEW_DECISION.md |
| Implementierung | COMPLETE | MC-TC-004_IMPLEMENTATION_REPORT.md |
| Scope | S-01…S-04 (4 Items, alle ✅ IMPLEMENTED, keine Abweichung) | CERTIFICATION_REPORT §Scope Review |
| Kriterien | 7/7 je Item (S-01…S-04), 431/431 Trust-Core-Tests | CERTIFICATION_REPORT §Acceptance Criteria |
| Rahmen | ARB_DECISION: COMMIT-WINDOW 1h, RESTRICTED-SCOPE | MC-TC-004_ARB_DECISION.md |
| Status in KF-Docs | „MC-TC-004 CERTIFIED“ (committet 01.08) | Doc 09 M-2 |

## 5 MC-TC-006 — Replay & Deterministic Reconstruction: CERTIFIED

| Feld | Wert | Beleg |
|---|---|---|
| Ergebnis | **CERTIFIED / GO** (27.07) | MC-TC-006-…-CERTIFICATION.md, G2-01 („MC-TC-006 replay certification (27.07)“) |
| Modus | PURE OBSERVATION — kein Produktionscode geändert | CERTIFICATION §Audit Mode |
| Phasen | 14/14 PASS/CONDITIONAL (A–N): Canonical Authority, Dual-Authority-Elimination, Deterministic Replay, Idempotency (conditional), Crash Recovery 6/6, Receipt-/Verification-Rekonstruktion, Causal Chain, Cross-Boot 3 Zyklen, Legacy-Events-Unabhängigkeit, Projection-Rebuild, Determinism-Hash (3 Runs identisch), Failure-Matrix 6/6 | CERTIFICATION §Summary |
| Kernaussage | `stored_events` als einzige kanonische Event-Autorität unabhängig verifiziert (MC-TC-005.3-Claim) | CERTIFICATION (Abschluss) |
| Test-Suite | 51 Tests (MC-TC-005.3-Suite, tests/test_mc_tc_005_3_single_event_authority.py) | CERTIFICATION §Audit Artifacts |

## 6 MC-TC-007 — Full Reality Closure: CONDITIONAL GO / NO-GO (artefaktabhängig)

| Artefakt | Ergebnis | Kernbefund | Beleg |
|---|---|---|---|
| STATUS_ZUSAMMENFASSUNG (31.07, Chat) | CONDITIONAL GO — 12/14 Kriterien ✅ | FAIL: H (Graph-OS Rekonstruktion: GraphState/SphereState in-memory, kein Rebuild — P0), Kriterium 12 (2 neue P0 + 4 neue P1) | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md |
| FULL_REALITY_CLOSURE_CERTIFICATION | CONDITIONAL GO | Phasen 0–L: 384/384 Tests; H ❌ FAIL; F ⚠️ PASS* (Watchdog-Events nicht persistiert); J: H_live == H_replayed == H_restarted == H_continued | MC-TC-007-FULL-REALITY-CLOSURE-CERTIFICATION.md |
| TRUST_GOVERNANCE_CERTIFICATION | **NO-GO ❌** | ToolPolicy/InterfacePolicyAdapter/ApprovalManager/ToolAudit/InterfaceAudit/ToolExecutor: alle Entscheidungs-/Audit-Zustände in-memory, keine Persistenz/Replay/Audit-IDs | MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION.md |

Hinweis (belegt, keine Interpretation): Die drei 007-Artefakte haben unterschiedliche Scopes (Reality-Closure vs. Trust-Governance); die Ergebnisse CONDITIONAL GO bzw. NO-GO werden unverändert übernommen. P0-1 (Graph-OS) und P0-2 (Watchdog-Persistenz) daraus sind in RC-1 erfasst (DECISION_CLOSURE_PACKAGE, G7-01).

## 7 MC-TC-005 — Kein Zertifizierungsstatus

- MC-TC-005 (Scope-Erweiterung): **NOT AUTHORIZED** — keine Zertifizierung; Scope-Grenze unbekannt (Doc 09 M-2, REFERENCE_GRAPH N-AUD).
- Teil-Artefakte 005.1 (CLOSURE-TRUTH-AUDIT) und 005.3 (SINGLE EVENT AUTHORITY CONSOLIDATION, COMPLETE, 51 Tests) existieren; 005.3-Ergebnis ist nur als Grundlage der MC-TC-006-Verifikation registriert, nicht als eigenständiges Zertifikat.

## 8 Status History

| Datum | Ereignis | Beleg |
|---|---|---|
| 19.–20.07 | EventStore-Implementierung (append-only, Replay) — Commits b9b17f3, 763f6bf, 99215ce | DECISION_REGISTRY D-008, REFERENCE_GRAPH E-014 |
| 27.07 | MC-TC-006 CERTIFIED (Replay/Deterministic Reconstruction) | MC-TC-006-Zertifikat, G2-01 |
| 30.07 | MC-TC-004 CERTIFIED (ARB, 431/431); ARB_DECISION mit COMMIT-WINDOW/RESTRICTED-SCOPE | MC-TC-004-Artefakte, G2-01 |
| 30.07–31.07 | MC-TC-007-Artefakte erstellt (Status-Zusammenfassung 31.07) — zunächst untracked | REFERENCE_GRAPH N-DOC-07/12 |
| 01.08 | Audit-Welle committet: MC-TC-002…007 (55 Artefakte) — `392734e`; danach KF-Doc 09 registriert CERTIFIED/NOT AUTHORIZED | git log, Doc 09 M-2 |
| 01.08 | G2-01: EventStore/Replay-Cluster SANCTIONED (Keept as-is) — `771d19f`; Replay-Suppression `2df80ab` | G2_ADJUDICATION_REPORT G2-01 |

## 9 Commit Evidence

| Commit | Bedeutung | Beleg |
|---|---|---|
| b9b17f3 | EventStore — append-only persistence with replay | git log runtime/event_store.py |
| 763f6bf, 99215ce | Replay-Commits (EventStore/Replay) | Doc 06 §5 Claim 8 (D-008) |
| 2df80ab | Replay-Suppression (replay events aus Persistenz) | git log |
| 771d19f | G2-01 Adjudication: C1-EventStore/Replay-Cluster SANCTIONED | G2_ADJUDICATION_REPORT G2-01 |
| 392734e | MC-TC-002…007-Zertifizierungswelle (55 Artefakte) committet | git log, PA-01 (PHASE_A_REMEDIATION_PLAN) |

## 10 Validation

- Read-only: keine Datei verändert, keine neue Zertifizierung, keine Statusänderung, keine ADR-Akzeptierung, kein Code.
- Alle Zertifikate wörtlich aus MC-TC-Artefakten übernommen (Ergebnis, Scope, Datum, Testzahlen); Quellen- und Statusprüfung: Zertifikate existieren als Dateien, Zertifikationswelle committet (392734e) — geprüft.
- Confidence: Zertifikate C0 (Datei + Commit); Datum MC-TC-006 (27.07) aus G2-01-Zitat (C0); 007-Chat-Anteil markiert (31.07, Chat).
- Keine Widersprüche zu KF-Docs (Doc 09 M-2, Doc 06 §5, Doc 19 KG-15/KG-06).
