# 03_SOURCE_OF_TRUTH_MAP_FOUNDATION.md

**Doc:** KF-1/03 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** SESSION_RULES.md v2.0 (Prio-Kette 1–8, Konfliktregel) · SOURCE_OF_TRUTH_MAP.md (MUSCAL-KRA, 7 Domänen, Findings A1/A2, SO-1…SO-5) · 02_SOURCE_OF_TRUTH_ARCHITECTURE.md (5-stufige Konfliktregel) · MASTER_INDEX.md (TF-01…TF-07) · DECISION_REGISTRY.md (D-IDs, §E-Gaps) · Audit-Artefakte (Census, G4, G5, G6-04)
**Modus:** reine Konsolidierung — **keine neuen Autoritäten, keine Statusänderung, keine Entscheidung, keine Interpretation von CHAT_ONLY**

---

## 1. Purpose

Dieses Dokument bündelt die Autoritätslandschaft der 7 Wissens-Domänen des MUSCAL-CORE-Programms in eine **eine navigierbare Karte**: für jede Domäne Primär-/Sekundär-/Tertiärquelle, Konfliktregel und Evidence-Level. Es ist der operative Nachfolger der SOURCE_OF_TRUTH_MAP (MUSCAL-KRA) und setzt die Autoritätskette aus SESSION_RULES v2.0 um.

Zweck:
1. **Navigierbarkeit** — jede Domäne zeigt, wo die Wahrheit liegt und was Referenz ist (kein Suchen in 7+ Quellen).
2. **Konsistenz** — Konfliktregeln je Domäne sind verbindlich zitiert (SESSION_RULES v2.0), keine neuen Regeln.
3. **Gap-Sichtbarkeit** — belegte Autoritäts-Lücken (chat-only, stale, untracked) bleiben sichtbar, werden nicht aufgelöst.

## 2. Authority Domains

| Domäne | Quelle (Beleg) |
|--------|----------------|
| Architektur | SOURCE_OF_TRUTH_MAP §2.1 [C0] |
| Implementierung | SOURCE_OF_TRUTH_MAP §2.2 [C0] |
| Governance | SESSION_RULES v2.0 §Authoritative Documents + DECISION_REGISTRY §B (D-020…D-025) [C0/C1] |
| Session State | SOURCE_OF_TRUTH_MAP §2.4 [C0] |
| Projektstatus | SOURCE_OF_TRUTH_MAP §2.5 [C0/C2] |
| Historische Entscheidungen | SOURCE_OF_TRUTH_MAP §2.6 [C0/C1] |
| Zukunftsplanung | SOURCE_OF_TRUTH_MAP §2.7 [C1/C2] |

## 3. Authority Matrix

### 3.1 Architektur

| Ebene | Quelle |
|-------|--------|
| Primär | `docs/TECHNICAL_BASELINE.md` (Prio 3, SESSION_RULES) — ⚠️ stale 12.07 |
| Sekundär | `spec/ADR-*.md` (Prio 4; aktuell bis 28.07, ADR-014) + `docs/engineering/D-*.md` (Prio 5) |
| Tertiär | `docs/ARCHITECTURE.md` (Prio 7; stale 12.07), Implementierungs-Referenz: Root-`*.py` + `features/` + `runtime/` |
| Konfliktregel | MC-TC-Zertifizierung > PROJECT_STATE (nachgezogen) > Technical Baseline > ADRs > Engineering Decisions > Historisches [C0] |
| Evidence Level | C0 (Code/ADRs), C1 (Interpretationen) |

### 3.2 Implementierung

| Ebene | Quelle |
|-------|--------|
| Primär | Git History + Code (CHANGE_JOURNAL-Hierarchie: Git → CHANGE_JOURNAL → SESSION_REGISTRY) [C0] |
| Sekundär | `docs/governance/ACTIVE_TASKS.md`, `WORK_QUEUE.md` (stale 20.07); `docs/PROJECT_STATE.md` (Prio 1) |
| Tertiär | Test-Suite (204 Dateien/2.869 Funktionen, Baseline 470), Reconciliation-Baseline |
| Konfliktregel | Code/Git-Realität schlägt Dokumentation; D-022-Kette [C0]; uncommitted Arbeit = Risiko, keine Autorität |
| Evidence Level | C0 |

### 3.3 Governance

| Ebene | Quelle |
|-------|--------|
| Primär | SESSION_RULES v2.0 (Prio-Kette 1–8, Konfliktregel, Forbidden Assumptions, Rekonstruktions-Checklist) [C0] |
| Sekundär | `spec/OVERRIDE.md` (Registry, rekonstruiert D-039; `override_052_is_active()==True`), `spec/IMMUTABILITY_CONTRACT.md` (D-020) |
| Tertiär | `docs/governance/` (WORK_QUEUE, ACTIVE_TASKS, CHECKPOINT_INDEX), D-021 (17 Handovers) |
| Konfliktregel | Registry + Guards entscheiden (Overrides ≠ Code-Wahrheit, v2.0-Forbidden-Assumption); ADR-Autorität: Baseline > Historisches (D-025) |
| Evidence Level | C0 (Regeln), C1 (Anwendungsstände) |

### 3.4 Session State

| Ebene | Quelle |
|-------|--------|
| Primär | `docs/PROJECT_STATE.md` (Prio 1; 20.07, P0-Sektion aktualisiert 01.08 d5f5ce7) [C0] |
| Sekundär | `docs/SESSION_REGISTRY.md` (28.07, S-2026-07-31-001 registry-only) [C0] |
| Tertiär | `docs/session_handovers/` (17 Dateien, 100 %, Backfill PB-01 c29c8b8) [C0] |
| Konfliktregel | neueste Handover + Checklist v2.0 (6 Quellen) bei Widerspruch zu stale Docs; S-07-31-Detail = UNKNOWN |
| Evidence Level | C0 |

### 3.5 Projektstatus

| Ebene | Quelle |
|-------|--------|
| Primär | `docs/PROJECT_STATE.md` (Prio 1) — mit P0-Sektion (01.08) + HDR-001-Status (20.07) |
| Sekundär | `docs/audit/MC-TC-*.md` (Prio 2, neueste Wahrheit ab 27.07; bis 30.07) |
| Tertiär | S2-Chats (31.07 MC-TC-007-Status, C2 — **nur Referenz, nie Autorität**) |
| Konfliktregel | MC-TC (Prio 2) > PROJECT_STATE (D-017 doc-level RESOLVED via Update 01.08); Chat-Status ohne Repo-Spiegelung = CHAT_ONLY |
| Evidence Level | C0/C1 (Repo), C2 (Chat) |

### 3.6 Historische Entscheidungen

| Ebene | Quelle |
|-------|--------|
| Primär | `docs/DECISIONS.md` (stale 12.07) + `spec/ADR-INDEX.md` (kanonisch, G4.5 B1) + DECISION_REGISTRY D-001…D-042 |
| Sekundär | `docs/CHANGE_JOURNAL.md` (endet 13.07), `docs/engineering/D-*.md` |
| Tertiär | `archive/history/adrs/` (6), `archive/history/rfcs/` (18) — **keine Autorität** (Prio 6) |
| Konfliktregel | kanonischer ADR-INDEX gewinnt; ADR-013-Fehllabel = F-03-Problem, keine Autoritätslösung |
| Evidence Level | C0/C1 |

### 3.7 Zukunftsplanung

| Ebene | Quelle |
|-------|--------|
| Primär | `docs/ROADMAP.md` (stale 08.07) — ❌ kein v0.9+-Plan |
| Sekundär | D-030…D-035 (Registry, PLANNED), ADR-022…025 (DRAFT, im Repo) |
| Tertiär | S2-Chats (MUSCAL 2.0-Turnier 25.07, D-010…D-014) — **CHAT_ONLY, keine Autorität** |
| Konfliktregel | Planung ohne Repo-Beleg = PLANNED/CHAT_ONLY; kein Plan-Doc = keine Roadmap-Wirkung (G6-04) |
| Evidence Level | C2 (chat-only), C1 (Registry) |

## 4. De-Jure vs De-Facto Findings (nur belegte)

| # | Finding | De-jure | De-facto | Beleg |
|---|---------|---------|----------|-------|
| A1 | Architektur-Baseline stale | BASELINE/ARCHITECTURE (Prio 3/7) | 12.07; v0.8/MC-TC-Welle nur in Audit+Code | [C0] SOURCE_OF_TRUTH §2.1 |
| A2 | Neuester Projektstatus nur im Chat | PROJECT_STATE (Prio 1) | 20.07; neuester Stand S2 31.07 (MC-TC-007, 2 P0) | [C1] SOURCE_OF_TRUTH §2.5 |
| — | Git-Lücke (197 uncommitted) | Git = technische Wahrheit (D-022) | 11 Tage unsichtbar (Audit-Welle untracked) | [C0] SOURCE_OF_TRUTH §2.2, TF-01 |
| — | Test-Zahl-Wahrheit unklar | PROJECT_STATE 547 | 4 Quellen (547/812/431/384) vs 2.869 real; Baseline 470 (18/18) erklärt | [C1] Census §5, MANUAL_RECONCILIATION_FINAL |
| — | Roadmap stale | ROADMAP (Priorität) | 08.07; Richtung 25.–31.07 nur chat | [C0] SOURCE_OF_TRUTH §2.3 |
| — | ADR-014-Statuskonflikt | Datei aktualisiert 28.07 | PROJECT_STATE 20.07 PROPOSED | [C1] SOURCE_OF_TRUTH §2.6; **G2 RESOLVED** (D-038 ACCEPTED) |
| — | 28.–31.07-Entscheidungen chat-only | DECISIONS/Journal | Journal endet 13.07; Registry D-030…035 macht referenzierbar | [C1] SOURCE_OF_TRUTH §2.6, G4 §M5 |

**Status der SO-Empfehlungen (belegt, keine Erfindung):**

| Empfehlung | Status (01.08→02.08) | Beleg |
|------------|----------------------|-------|
| SO-1 SOURCE_OF_TRUTH-Manifest | **offen** — nicht erstellt | SOURCE_OF_TRUTH §4 |
| SO-2 Git-Gap schließen | **teilweise** — G2-Exekution (15 Commits) + Phasen A/B/G6/G7/KF; 104 Bridge untracked verbleiben | G2-Report, G4 §M1 |
| SO-3 Chat-Status migrieren | **teilweise** — MC-TC-007 → PROJECT_STATE 01.08 (d5f5ce7); MUSCAL-2.0-Richtung → ADR-022 DRAFT (947d03e); D-033…035 weiter CHAT_ONLY (G6-04) | D-017-Resolution, G4.5 B1, G6-04 |
| SO-4 ADR-Standorte konsolidieren | **teilweise** — ADR-INDEX kanonisch (B1); 4-Standorte physisch, `specs/adrs/`-Leiche (F-03) offen | G4.5 B1, G6-01 |
| SO-5 Manual-Versionen angleichen | **offen** — v0.8 fehlt (G6-02-Scope erstellt), Triple bleibt | G6-02, TC_H3_CLOSURE |

## 5. Conflict Resolution Process (bestehende 5-Stufen-Regel, 02_SOURCE_OF_TRUTH_ARCHITECTURE §3)

| Stufe | Vorgehen | Beispiel (belegt) |
|-------|----------|-------------------|
| 1. Erkennen | Quellen-Abgleich bei Doc-Erstellung/Review | Manual-Zeilenzahlen vs Code (Census §4) |
| 2. Klassifizieren | Konfliktgrad (LOW/MEDIUM/HIGH) + Confidence beider Seiten | D-017 HIGH; D-018 MEDIUM (Registry §D) |
| 3. Dokumentieren | CONFLICTING-Status (Charter §4); keine stille Auflösung | ADR-014-Statuskonflikt (D-018) |
| 4. Eskalieren | höhere Prio-Kette entscheidet; Human/ARB bei Unklarheit | D-017 → G2 §G-Resolution (PROJECT_STATE 01.08) |
| 5. Schließen | Resolution im Registry, Status-Mutation mit Evidence | D-038 (ADR-014 ACCEPTED), D-039 (OVERRIDE-052) |

**Grundregel [C0]:** Konflikte dokumentieren, nicht stillschweigend auflösen (SESSION_RULES v2.0).

## 6. Staleness Analysis (belegte Altersunterschiede, keine Neuberechnung)

| Bereich | Neueste belegte Quelle | Stand | Befund |
|---------|------------------------|-------|--------|
| ROADMAP | `docs/ROADMAP.md` | **08.07** | ❌ stale — v0.8 weitgehend umgesetzt, kein v0.9+-Plan [C0] SOURCE_OF_TRUTH §2.3 |
| PROJECT_STATE | `docs/PROJECT_STATE.md` | **20.07**; P0-Sektion **01.08** (d5f5ce7) | ⚠️ teilweise aktuell — Status-Basis 20.07, P0/HDR-Teil 01.08 [C0] |
| HANDOVERS | `docs/session_handovers/` | Census-Neueste 27.07 → nach PB-01-Backfill **17/17 inkl. 28./30./31.07** (c29c8b8) | ✅ geschlossen — Lücke 28.–31.07 beseitigt [C0] Census §3, G4 §M3 |
| AUDIT | `docs/audit/MC-TC-*` | bis **30.07** (MC-TC-004); Docs heute 02.08 (G6/G7/KF, 75 Dateien) | ✅ laufend gepflegt — neueste Governance-Wahrheit (Prio 2) [C0] |
| CHATS | S2 (17.–31.07) | neuester **31.07** (MC-TC-007-Status, D-017) | ⚠️ neueste Statusaussage teilweise chat-only (D-033…035) — CHAT_ONLY bleibt [C2] SOURCE_OF_TRUTH §2.5, G6-04 |

## 7. Known Authority Gaps (nur bestehende, unverändert)

| Domäne | Autorität vorhanden? | Aktuell? | Git-sichtbar? | Chat-only-Inhalt | Quelle |
|--------|----------------------|----------|---------------|------------------|--------|
| Architektur | ✅ (Baseline+ADRs) | ⚠️ Baseline stale | ⚠️ teilweise | MC-015 2.0-Turnier, Cognitive Kernel | SOURCE_OF_TRUTH §3 |
| Implementierung | ✅ (Code) | ✅ Code, ❌ Git | ❌ 104 untracked (Bridge) | Agent-Architecture-Spec (30.07) | SOURCE_OF_TRUTH §3; G4 §M1 |
| Roadmap | ✅ (ROADMAP.md) | ❌ stale 08.07 | ✅ | MUSCAL 2.0, E3.6 Knowledge Distillation | SOURCE_OF_TRUTH §3 |
| Session State | ✅ (PROJECT_STATE) | ⚠️ Basis 20.07 | ⚠️ | OC-Session-State-Test (20.07) | SOURCE_OF_TRUTH §3 |
| Projektstatus | ✅ (PROJECT_STATE) | ⚠️ P0-Teil 01.08, Rest 20.07 | ⚠️ | MC-TC-007-Status (31.07, gespiegelt), D-033…035 | SOURCE_OF_TRUTH §3; G6-04 |
| Historische Entscheidungen | ✅ (DECISIONS/ADR/Journal) | ⚠️ Journal endet 13.07 | ⚠️ | Decision-Registry-Chat-Ausgaben (D-010…014 gespiegelt via ADR-022…25 DRAFT) | SOURCE_OF_TRUTH §3 |
| Zukunftsplanung | ✅ (ROADMAP) | ❌ | ✅ | Benchmark-Framework, Datenstrategie SLM (D-034/035) | SOURCE_OF_TRUTH §3 |

**Weitere belegte Gaps (DECISION_REGISTRY §E, unverändert):**

| Gap | Evidence |
|-----|----------|
| Kein ADR für EventStore/ReplayService-Einführung | `spec/ADRs/ADR-EVENT-001` nur dort, nicht kanonisch |
| Kein ADR für v0.8 (CHANGELOG_v0.8.md, kein ADR-015+) | CHANGELOG_v0.8.md |
| Keine dokumentierte MC-015 → ADR-Konvertierung | S2 25.07 (D-010, ADR-022 DRAFT) |
| MKSD (MUSCAL Kernel Specification Document) fehlt | S2 `Spezifikation offen` 28.07 |
| Bridge-Artefakte (104) ohne Artefakt-Governance | G4 §M1; git status (untracked) |

## 8. Validation

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Jede Aussage besitzt Quelle | ✅ alle Domänen/Findings/Gaps mit Beleg (SOURCE_OF_TRUTH_MAP, SESSION_RULES, Census, G4/G5/G6) |
| Keine neuen Autoritäten erfunden | ✅ nur bestehende Quellen (Prio-Kette 1–8) referenziert; Chat immer als Referenz/CHAT_ONLY |
| Keine Statusänderungen | ✅ SO-Empfehlungs-Status mit Commit-Belegen aus Artefakten; keine ID/Status neu gesetzt |
| Keine Entscheidungen erzeugt | ✅ keine neuen IDs, keine Resolutionen, keine Staleness-Berechnung |
| Markdown only | ✅ docs/audit/03_SOURCE_OF_TRUTH_MAP_FOUNDATION.md |

---

*Erstellt als Karte der bestehenden Autoritätslandschaft — keine neuen Regeln, keine Interpretation. Stand: 02.08.2026, konsistent zu Gate-Kette G5/G6.*
