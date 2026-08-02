# 06_CHAT_CODE_DOC_RECONCILIATION_FOUNDATION.md

**Doc:** KF-1B/06 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** CHAT_CODE_DOC_RECONCILIATION.md (MUSCAL-KRA, 20 Claims, 44-NEW-Tabelle) · DECISION_REGISTRY (D-IDs) · CONCEPT_EVOLUTION_MAP (Concept-Register) · REFERENCE_GRAPH (~120 Knoten/12 Edge-Typen) · MASTER_INDEX (Dok 5/7/8)
**Modus:** Read-only Extraktion — **keine neue Verifikation, keine Statusänderung, keine Entscheidung**
**Klassifikationen (nur bestehende):** IMPLEMENTED · DOCUMENTED · PLANNED · CHAT_ONLY · HISTORICAL · CONFLICTING (+ GAP für Unbekanntes)

---

## 1. Purpose

Dieses Dokument überführt die Chat-Code-Doc-Reconciliation (Audit, 01.08) in die Foundation: welche Chat-Claims (S1+S2) sind durch Repo-Belege verifiziert, welche bleiben CHAT_ONLY, welche sind widerlegt oder konfliktbehaftet. Es macht die Wissens-Herkunft jeder Entscheidung (D-IDs) nachvollziehbar und ist Eingangsquelle für M5 (Knowledge Coverage).

## 2. Scope

| In | Out |
|----|-----|
| 44-NEW-Konversations-Übersicht (17.–31.07), 20 verifizierte Claims, Chat-only-Kritik, Abandoned-Initiativen | neue Claim-Prüfungen, Repo-Deep-Reads, neue Klassifikationen |

**Coverage-Grenzen (belegt):** S2: 12/44 Chats deep-read, 32 topic-klassifiziert [C2]; S1: 10 Chats deep-read, Rest programmatisch [C3] (CHAT_CODE_DOC_RECONCILIATION §7).

## 3. Reconciliation Model

| Schritt | Beleg | Quelle |
|---------|-------|--------|
| Claim-Extraktion aus Chats (S1 Deep-Read-Sample + S2 vollständig 44 NEW) | 44 NEW, 43 Zeilen (1 Duplikat-Variante) [C0] | CHAT_CODE_DOC_RECONCILIATION §2 |
| Verifikation gegen Repo (S3, 1.209 Dateien), Governance (S4), Session-Docs (S5) | vollständiger Census | §1 |
| Urteils-Schema: ✅ implemented · 📄 documented · ⚠️ undocumented · 🧠 chat-only · 🧪 code-only · 🗑 abandoned · ❓ unverifiable | 20 Claims klassifiziert | §3/§4 |
| Status-Fortführung 01.08 (Repo-Spiegelungen, keine neuen Urteile): MC-TC-004 committet `392734e`; MC-TC-007-Status → PROJECT_STATE-P0 `d5f5ce7`; MUSCAL-2.0-Richtung → ADR-022 DRAFT `947d03e` | Commit-Belege | G2-Exekution, G4.5 B1 |

## 4. Claim Classification (nur bestehende Klassen)

| Klasse (Foundation) | Audit-Klasse | Anzahl | Claims |
|---------------------|--------------|-------:|--------|
| **IMPLEMENTED** | ✅ implemented | 2 | #8 (EventStore-Semantik-Trennung, C0), #9 (append-Signatur validated, C1) |
| **DOCUMENTED** | 📄 documented | 5 | #3 (E3.2-Closure, C1), #7 (E3.5.1 teilweise, C1), #11, #12, #13 (ADR-001/002/003, C0) |
| **CHAT_ONLY** | 🧠 chat-only | 8 | #4, #5, #16, #17, #18, #19, #20, #2 (alle C2) |
| **CONFLICTING** | ⚠️ undocumented/undocumented-in-git + ❌ | 6 | #1 (doc, nicht in git — seit `392734e` committet), #6 (teilweise, C2), #10 (falsifiziert, C0), #14 (Stub-Widerspruch, C0), #15 (stale, C0), #2 (chat-only vs Repo-Stand) |
| **HISTORICAL** | 🗑 superseded | 3 | MCXF-Interpreter-Pfad (ADR-001, C0), `simulation_mode: bool` (OVERRIDE MC-TC-003B, C0), EventBus-only (EventStore, C0) |
| **GAP** | 🧪 code-only | 1 | EventStore/ReplayService ohne kanonischen ADR (ADR-EVENT-001 nur in `spec/ADRs/`) |

## 5. Verified Claims (5 bestehende, mit Beleg)

| # | Claim | Beleg | Evidence |
|---|-------|-------|----------|
| 3 | E3.2 Trust Boundary CLOSED (9 Bypasses, OVERRIDE-067…073) | `docs/engineering/D-E3.2-001-TRUST-BOUNDARY-CLOSURE.md` + OVERRIDE.md | C1 (D-015 IMPLEMENTED) |
| 8 | EventBus/EventStore/AuditLog semantische Trennung | `runtime/event_store.py` + Replay-Commits (99215ce, 763f6bf, b9b17f3) | C0 (D-008 IMPLEMENTED) |
| 9 | EventStore.append()-Signatur-Mismatch validiert | append-Signatur in `runtime/event_store.py` | C1 (D-009 IMPLEMENTED) |
| 11 | ADR-001: Execution-Graph-Compiler statt Interpreter | `spec/ADR-001-kernel.md`, MAS-0301 | C0 (D-001 IMPLEMENTED) |
| 12/13 | 7-Layer + Capability-First | ADR-002, ADR-003 | C0 (D-002/D-003) |

## 6. Unverified Claims (GAP-Status, belegt)

| # | Claim | Grund (unverifiziert) |
|---|-------|------------------------|
| 1 | MC-TC-004 „CERTIFIED" — Audit-Zeitpunkt: existierte, aber **nicht in git** | Untracked bis 01.08; committet `392734e` → seitdem Repo-Beleg [C0] |
| 7 | Reality-Score 55/100 | Score chat-only (C2); G2-Re-Messung 61.0 belegt (D-031 DOCUMENTED) |
| 17 | MKSD fehlt | Kein MKSD im Repo; `spec/MSCE-SPECIFICATION_v0.1.md` ist MSCE-spezifisch [C1] — Gap bestätigt |
| 6 | MPP-Pipeline „16 Stages" | teilweise: Code vorhanden (features/), Spec chat-only [C2] |

## 7. Chat Only Findings (unverändert CHAT_ONLY — D-010…D-014 bleiben PLANNED/CHAT_ONLY)

| # | Finding | Quelle | Repo-Bezug 01.08 |
|---|---------|--------|------------------|
| 4 | MC-015-Turnier: Hybrid gewinnt (MUSCAL 2.0) | S2 25.07 | ADR-022 **DRAFT** (947d03e) — kein Akzeptanz-Status (D-010) |
| 5 | Cognitive Kernel + Authoritative Runtime | S2 25.07 | ADR-023 **DRAFT** (D-011) |
| 16 | Agentengetriebene Selbstentwicklung | S2 21.07 | kein ADR (D-032) |
| 18 | Cognitive Compiler Spec v1.0 | S2 30.07 | ADR-025 **DRAFT** (D-013) |
| 19 | Agent Architecture Spec v1.0 (P1–P5) | S2 30.07 | ADR-024 **DRAFT** (D-012) |
| 20 | Externe Validierungsmatrix-Methode | S2 23.07 | echo AUDIT_SCOPE-Layers [C2] |

## 8. Code Only Findings (GAP)

| Finding | Beleg | Status |
|---------|-------|--------|
| EventStore/ReplayService implementiert, kein kanonischer ADR zum Einführungszeitpunkt | Commits 07-19/20; ADR-EVENT-001 nur in `spec/ADRs/` | Registry-§E-Gap; via B1-INDEX aufgenommen (kein neuer ADR) |

## 9. Documentation Gaps

| # | Gap | Beleg |
|---|-----|-------|
| D-G1 | 32/44 S2-Chats nur topic-klassifiziert (keine Deep-Verifikation) | §7 [C2] |
| D-G2 | S1-Claim-Vollständigkeit C3 (programmatischer Scan) | §7 [C3] |
| D-G3 | MUSCAL-2.0-Richtung nur als ADR-DRAFT sichtbar (Akzeptanz offen, RC-4a) | ADR_REVIEW_MATRIX |
| D-G4 | D-033…035 weiterhin ohne Repo-Plan-Docs | G6-04 |

## 10. Validation

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Nur bestehende Klassifikationen | ✅ 6 Foundation-Klassen aus Audit-Urteilen abgebildet, keine neuen |
| Keine neue Verifikation/Testausführung | ✅ alle Urteile/Commits aus Quellen (Audit 01.08, G2/G4.5-Commits) |
| Keine Statusänderung | ✅ D-010…D-014/D-030…D-035 bleiben PLANNED/CHAT_ONLY; keine neuen D-IDs |
| CHAT_ONLY bleibt CHAT_ONLY | ✅ §7 unverändert; Repo-DRAFTs als „kein Akzeptanz-Status" markiert |
| Unbekanntes als GAP | ✅ §6/§8/§9 |
| Markdown only | ✅ docs/audit/06_CHAT_CODE_DOC_RECONCILIATION_FOUNDATION.md |

---

*Erstellt als konsolidierte Reconciliation-Referenz — kein neues Urteil, keine neue Prüfung. Stand: 02.08.2026.*
