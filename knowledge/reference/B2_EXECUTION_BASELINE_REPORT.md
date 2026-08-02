# B2_EXECUTION_BASELINE_REPORT

Phase 0 — Repository Reality Check (B2 HYBRID Production Readiness)

- Datum: 02.08.2026
- Rolle: Senior Architecture Implementation Agent
- Modus: **READ ONLY** (Phase 0) — keine Änderungen, kein Commit; Basisdokument für die Phasen 1–7
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Quellen: SESSION_RULES v2.0 [SR], PROJECT_STATE.md 01.08. [PST], spec/ADR-INDEX.md [ADR-IX], spec/OVERRIDE.md [OVR], AGENTS.md [AG], git-Status 02.08., pytest-Collection, features/-Census, B2PKG/B2MA/MCLS/CLIC/CLAR/ESIA
- Status: **created, not committed (external KF layer)**

---

## 1. Aktueller Zustand

### 1.1 Git / Repository

| Punkt | Befund |
|-------|--------|
| Branch | [F] `main` (git branch --show-current); PST:93 nennt `prototype-stable` → Diskrepanz-Doku nötig [F] |
| Letzter Commit | [F] `d64268e docs(kf-2): completion report …` (KF-2-Doku-Welle) |
| Modified tracked | [F] 0 Dateien — tracked sauber |
| Untracked | [F] **104 Dateien**, alle in `docs/bridge/handovers/` (handover_*.md/.yaml) — Bridge-Governance-Altlast (KG-12-Kontext) [F: PHASE_A_REMEDIATION_PLAN:15] |
| Commits | [F] **keine Commits durchgeführt** (Grundregel 4) |

### 1.2 Governance / Autorität

- [F] SESSION_RULES v2.0 gelesen: Autoritätskette (MC-TC-Zertifizierung > PROJECT_STATE > Baseline > ADRs > Engineering > Historisch); CORE-IMMUTABLE-Liste (kernel.py, graph.py, event_bus.py, muscal_os.py … runtime/kernel|llm|optimizer|api|services/*); Erweiterungen nur features/; VIOLATION-Pfad (STOP → ARCHITECTURE CHANGE → OVERRIDE.md → `--allow-core-write`) [F: SR:12-79; AG]
- [F] OVERRIDE.md existiert (1.541 Zeilen, OVERRIDE-020…055-Baseline; OVERRIDE-052-Mechanismus reaktiviert) [F: PST:126; OVR]
- [F] Audit-Status: MC-TC-004 CERTIFIED (30.07), MC-TC-006 CERTIFIED (27.07), MC-TC-007 CONDITIONAL GO (31.07) mit 2 P0-Blockern, MC-TC-005 NOT AUTHORIZED [F: PST:20-23]
- [F] P0-Blocker: P0-1 GraphState nur in-memory (nicht rekonstruierbar), P0-2 Watchdog ohne EventStore-Persistenz — beide OFFEN, Entscheidung ausstehend [F: PST:47-48]
- [F] HDR-001 READY FOR HUMAN DECISION (9 Dependencies); HDR-002…004 BLOCKED [F: PST:116-119]
- [F] G2-Adjudikation: 29 Immutability-Dateien adjudiziert (22 committet, 6 retroaktiv sanktioniert, 0 Reverts); Repo wieder sauber [F: PST:125-130]

### 1.3 ADR-Registry

- [F] ADR-INDEX kanonisch (G4.5 B1): ADR-001…014 kanonisch (APPLIED/ACCEPTED); ADR-022…025 DRAFT/PROPOSED (MUSCAL-2.0-Hybrid, Cognitive Kernel, Agent-Architektur, Cognitive Compiler) [F: ADR-IX]
- [F] ADR-EVENT-001 (EventStore-Boundary): eine SQLite-Datei, zwei append-Pfade, keine zweiten Autoritäten [F: spec/ADRs/ADR-EVENT-001-eventstore-boundary.md:11-20]
- [F] ADR-007 Core Immutability (Write Guard Policy) ACCEPTED [F: ADR-IX]

### 1.4 Tests

- [F] pytest-Collection: **2367 Tests** (02.08., collection-only) — deutlich über den 547 aus PST:38 (TF-06-Kontradiktion, Neu-Verifikation ausstehend) [F: PST:41]
- [F] Voll-Lauf in Phase 0 bewusst nicht ausgeführt (kein Änderungskontext); Baseline-Messung erfolgt in Phase 1 VALIDIERUNG [I]

### 1.5 Code-Zustand (Phase-relevant)

- [F] EventStore: stored_events (17 Spalten, event_id UNIQUE, append-only) [F: runtime/event_store.py:50-67]; `_migrate_add_columns` additiv [F: runtime/event_store.py:274-303]; `_EXECUTION_REQUIRED_TOPICS` ohne EXECUTION_FAILED [F: event_store.py:21-32]
- [F] Graph: Mutationen ohne Events (remove/prune/focus), NODE_UPDATED ohne Delta [F: graph.py:103-165]; `_replaying`-Flag [F: graph.py:56,226-229]
- [F] Watchdog: liest Store, schreibt nur Bus [F: features/monitoring/execution_watchdog.py:60-119]
- [F] **Wichtiger Neubefund:** features/-Landschaft umfasst bereits `projection/` (graph_os_projection.py), `verification/` (bridge_verifier, orchestrator, rules, verifier), `provenance/` (MCPL: mcpl_store, mcpl_schema, mcpl_events, decision_writer, evaluation), `cognitive_unit/` — diese können Phasen-Bausteine sein oder überlappen [F: ls features/]
- [F] muscal/ = eigenes Paket (pyproject, 24 Module) [F: muscal/pyproject.toml; muscal/src/muscal/]
- [F] Replay-Service-Cursor In-Memory (E-6) [F: features/replay/replay_service.py:20,84-90]

---

## 2. Risiken (Stand Phase 0)

| ID | Risiko | Stufe | Quelle |
|----|--------|-------|--------|
| B-R1 | Doppel-Wahrheit stored_events vs. legacy `events` (kein Reconcile) | CRITICAL | [F: MC-TC-004-POST-REMEDIATION:540] |
| B-R2 | Rebuild-Treue ohne Log-Vollständigkeit (E-1…E-5; Struktur ≈78 %, Zustand ≈46 %) | HIGH | [F: STE §4] |
| B-R3 | Genesis-Hash-Lücke bei v2-Einführung | HIGH | [H: CLRA §4] |
| B-R4 | Phase-2 (Graph-Events) verlangt graph.py-Änderung = CORE/Immutable (D-020) | HIGH | [F: SR; AG] |
| B-R5 | Phase-1 (Schema v2) betrifft MC-TC-004/006-Trust-Boundary (SANCTIONED G2-01) | HIGH | [F: OVR:1523] |
| B-R6 | 104 untracked Bridge-Handover-Dateien (KG-12 offen) | MEDIUM | [F: git status] |
| B-R7 | Testzahlen-Diskrepanz 547 vs. 2367 (TF-06) — Baseline-Messung nötig | MEDIUM | [F: PST:41] |
| B-R8 | HDR-001 offen (RC-2) → Governance-Form unverbindlich | MEDIUM | [F: PST:116] |
| B-R9 | MC-TC-005 NOT AUTHORIZED (Verification-Layer-Scope) | MEDIUM | [F: PST:23] |
| B-R10 | bestehende features/-Bausteine (projection/verification/provenance) können mit geplanten Phasen kollidieren — Überlappungs-Prüfung VOR Bau | MEDIUM | [F: ls features/] |

---

## 3. Betroffene Dateien (je Phase, Vorausplanung)

| Phase | Betroffene Dateien | Zone | D-Prüfung |
|-------|--------------------|------|-----------|
| 1 Schema v2 | `runtime/event_store.py` (+ Tests) | Trust-Boundary (nicht CORE-Liste, aber MC-TC-004/006-SANCTIONED) | [I] OVERRIDE-Klassifikation + Doku VOR Änderung [F: AG VIOLATION; OVR] |
| 2 Graph-Events | `graph.py` (NODE_*-Deltas) **oder** features/-Projection-Erzeuger; `features/projection/graph_os_projection.py` (Bestand prüfen) | graph.py = CORE/Immutable; features/ = frei | [I] D-020: graph.py nur mit OVERRIDE; bevorzugt features/-Weg [I: CLIC §2] |
| 3 Snapshot/Restore | neu in features/ (Snapshot-Modul); `muscal_os.py:_load_snapshot` bleibt unverändert | features/ | [I] kein CORE-Write; Anrufpunkt-Klassifikation [I: CLIC §2 P4] |
| 4 Watchdog | `features/monitoring/execution_watchdog.py` (+ event_adapter-Nutzung) | features/ (D-006-konform) | [F] kein CORE-Import nötig außer bestehendem event_bus [F: execution_watchdog.py:97] |
| 5 Ledger-Layer | neu in features/ (decision/evidence/agent-Event-Erzeuger); `runtime/event_store.py` (Attributions-Pflicht, E-8) | features/ + Trust-Boundary | [I] OVERRIDE für event_store-Validierung [I] |
| 6 muscal-Adapter | neu in features/ (Integrations-Adapter); muscal/-Paket unverändert | features/ + externes Paket | [I] Boundary-Tests (keine CORE-Imports von muscal/) [I: CLIC §2 P5] |
| 7 Validation | Tests, MC-TC-Artefakte, Reports | Doku/Tests | [I] keine Code-Änderung |

---

## 4. Geplante Änderungen (Übersicht je Phase)

| Phase | Ziel | Art | Erlaubnisfrage |
|-------|------|-----|----------------|
| 1 | Schema v2: aggregate_id, aggregate_type, metadata, payload_delta, parent_event_id, prev_hash, logical_time, schema_version — additiv, kein Rewrite | Trust-Boundary-Migration | [I] OVERRIDE-Doku + Impact-Analyse VOR Änderung (Regel 1) [I] |
| 2 | GraphState → Projection: NODE_CREATED/UPDATED/REMOVED, EDGE_CREATED/UPDATED/REMOVED, PRUNING_EXECUTED, FOCUS_CHANGED; payload_delta-Pflicht | features/-Erzeuger + ggf. graph.py-OVERRIDE | [I] Bevorzugt features/-Weg; graph.py nur mit OVERRIDE (D-020) [I: CLIC §2 P2] |
| 3 | Snapshot (event_sequence, graph_state, hash, timestamp) + Restore (Snap → Replay → Hash → Validate) | features/ (neu) | [I] keine CORE-Änderung [I] |
| 4 | Watchdog → EventStore.append() + Bus; idempotency_key `orphan_{execution_id}`; Dedup via event_id UNIQUE | features/monitoring | [F] D-006-konform [F] |
| 5 | Ledger-Events: decision.*, evidence.*, agent.*; Invarianten CLAIM≠PROOF, verified⇒receipt, Attribution | features/ (neu) + event_store-Validierung | [I] OVERRIDE für Attributions-Pflicht [I] |
| 6 | muscal/-Adapter (verification, truth state machine, governance, agent registry) | features/ (neu), keine Kopie | [I] Boundary-Vertrag [I] |
| 7 | MC-TC-004/006-Rerun, Regression, Negative-Tests, M1…M5-Messwerte | Tests/Doku | [I] keine Code-Änderung |

- [F] Geplante Änderungen übersetzen MCLS/CLIC in ausführbare Blöcke; Reihenfolge entspricht CLIC §1 [I].
- [F] Grundregeln 1–5 übernommen: Impact-Analyse+OVER RIDE vor CORE-Berührung; keine Entscheidungen; jede Änderung nachvollziehbar/testbar/reversibel/dokumentiert; keine Commits; Status+Tests+Risiken nach jedem Block [F: dieser Report].

---

## 5. Offene Punkte vor Phase 1

| # | Punkt | Art |
|---|-------|-----|
| O-1 | Impact-Analyse + OVERRIDE-Doku für event_store.py-Schema-v2 (Trust-Boundary) — Regel-1-Pflicht | Vorbereitung |
| O-2 | Bestand-prüfen: features/projection/graph_os_projection.py — evtl. schon Projection-Bausteine (Überlappung mit Phase 2/3) | Vorbereitung |
| O-3 | Bestand-prüfen: features/provenance/ (MCPL, decision_writer) — evtl. Ledger-Überlappung (Phase 5) | Vorbereitung |
| O-4 | Baseline-Testlauf (2367 Tests) als Referenzmessung VOR Phase-1-Änderungen | Vorbereitung |
| O-5 | Human-Entscheidungen unverändert offen: RC-1a/RC-1b, RC-2 (HDR-001), RC-4a — bei Berührung: STOP + HUMAN_DECISION_REQUIRED.md | Gate |

---

## Validation

- Phase 0 read-only: keine Datei verändert (außer diesem Report), kein Commit, keine Entscheidung getroffen.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H] gekennzeichnet.
- Nächster Schritt laut Prompt: **STOP nach Erstellung**.

**STOP (Phase 0 abgeschlossen).**
