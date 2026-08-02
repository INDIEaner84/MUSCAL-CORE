# 14 — Architecture Map Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only)
- Quellen: REPOSITORY_CENSUS (KF), PHASE_A_REMEDIATION_PLAN (PA-02/PA-03), G2_ADJUDICATION_REPORT (G2-01…G2-06), AGENTS.md (Core-Liste), SESSION_CONTINUITY_AUDIT §2 (7-Schichten), DECISION_REGISTRY (D-IDs), spec/ADR-INDEX.md, TECHNICAL_MANUAL (M-0.6/M-0.7/M-ROOT), REFERENCE_GRAPH (E-014), CONCEPT_EVOLUTION_MAP
- Prinzip: strikte Trennung IMPLEMENTED / DOCUMENTED / PLANNED / CHAT_ONLY; MUSCAL 2.0, Cognitive Kernel, Agent P1…P5, Cognitive Compiler **niemals IMPLEMENTED**

## 1 Purpose

Belegte Architektur-Landkarte des Repos: was ist tatsächlich implementiert, was nur dokumentiert, was geplant, was nur chat-basiert. Grundlage für Architektur-Entscheidungen und KF-2.

## 2 Scope

- Aufgenommen: Modul-/Schichten-Landschaft aus Census/Phase-A/G2 (Code), Dokumentations-Artefakte (ADRs/Manuals/Pläne), Plan- und Chat-Status (Registry D-IDs, REFERENCE_GRAPH).
- Nicht aufgenommen: Zukunftsarchitektur als IST; Einzeldateien ohne Status-Beleg.

## 3 Classification Model

| Klasse | Definition (belegt) | Confidence-Anforderung |
|---|---|---|
| IMPLEMENTED | Datei existiert im Repo (committet, Stand 70f630e) | C0/C1 |
| DOCUMENTED | Konzept in Autoritäts-Dokumenten (ADR-INDEX/Manual), keine Code-Wirkung | C0/C1 |
| PLANNED | in Registry als PLANNED registriert oder DRAFT im Repo (Kein Akzeptanz-Status) | C0/C2 |
| CHAT_ONLY | nur aus Chats belegt, kein Repo-Artefakt | C2 |

## 4 IMPLEMENTED (Code, committet)

### 4.1 Core (IMMUTABLE — AGENTS.md)

kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py, mkc_rules.py, config.py, event_bus.py, graph.py, feedback.py, muscal_os.py, main.py, main_boot.py, boot_manager.py, os_config.py, sphere.py, debugger.py, tools.py, rag.py, trace_engine.py, plugin_registry.py, plugin_loader.py; runtime/kernel/*, runtime/llm/*, runtime/optimizer/*, runtime/api/*, runtime/services/* (Quelle: AGENTS.md Core-Liste; C0).

### 4.2 EventStore/Replay-Cluster (G2-01, SANCTIONED)

runtime/event_store.py (+367: is_replayed-Column u. a., 6 neue Spalten), runtime/database.py (+283), runtime/kernel/writer.py (severity→priority, uuid), runtime/main.py (EventStore-Wiring), features/replay/replay_service.py. Commits: b9b17f3, 763f6bf, 99215ce, 2df80ab, 771d19f (C1; G2_ADJUDICATION_REPORT G2-01).

### 4.3 Features-Welle (PA-02, committet 1436ad6 et al.)

features/{agent_detection, boot, bootstrap, cognitive_unit, events, execution, execution_guard, identity, interface_gateway, kernel, knowledge, memory_fabric, monitoring, optimization, orchestration, projection, provenance, safety, streaming, supl, tool_runtime, tools, verification, worker}/; features/runtime/{checkpoint_manager, coordinator, models, observability, runtime_state, session_manager}.py; features/runtime_canonical.py; features/pipeline/* (C0; PHASE_A_REMEDIATION_PLAN PA-02). Beispielmodule: features/tools/{policy,approval,audit,executor}.py, features/interface_gateway/{policy_adapter,audit}.py (MC-TC-007-TRUST-GOVERNANCE, NO-GO-Befund), features/monitoring/execution_watchdog.py:96-119 (P0-2), features/tool_runtime/tool_runtime.py (Singleton-State, D-042).

### 4.4 Frontend (PA-02/PA-03, committet 8025f2f)

frontend/Dashboard.jsx (+3), ModeToggle.jsx, SemanticGraphView.jsx, SemanticOverlay.jsx, SuplApp.jsx, SuplExecutionView.jsx, useSuplWebSocket.js (C0).

### 4.5 Schichten-Architektur (S2/Census)

7 Layer, Capability-first, Plugin-Modell, EventStore via ADR-012/ADRs; Graph-OS-Freeze (30.07) und MUSCAL-2.0-Richtung fehlen im Baseline-Dokument (SESSION_CONTINUITY §2, C1). Topologie: Event-Sourcing-Kern (stored_events kanonisch, MC-TC-006), abgeleitete events-Tabelle (MC-TC-005.3/006).

## 5 DOCUMENTED (keine Code-Wirkung)

- ADR-INDEX (spec/ADR-INDEX.md) kanonisch (B1); ADR-001…014 + ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001, ADR-020, ADR-021 (B2); ADR-013 SUPERSEDED (PA-06, d5f5ce7); 4 DRAFT: ADR-022…025 (siehe §6).
- Manuals (Kanon: M-0.6 > M-0.7 > M-ROOT): TECHNICAL_MANUAL_v0.6 (1.935 Z., 12.07), v0.7 (371 Z., 15.07), ROOT (932 Z., 02.07); M-0.7 §4 enthält Modul-Zeilenzahlen (E-012, C0).
- Stale/veraltet (Doku-Status, belegt): TECHNICAL_BASELINE + ARCHITECTURE (12.07), DECISIONS.md (12.07), CHANGE_JOURNAL (endet 13.07), ROADMAP (08.07), TECHNICAL_BASELINE stale (Doc 19 KG-07/KG-08, SOURCE_OF_TRUTH_MAP).
- PROJECT_STATE.md (20.07, P0-Update 01.08); SESSION_RULES v2.0 (.opencode, 20.07).

## 6 PLANNED

- D-030…D-035: Registry-Status PLANNED (DECISION_REGISTRY; MUSCAL-2.0-Nachfolge; CHAT_ONLY-Basis).
- ADR-022…025: DRAFT im Repo, Review NICHT GESTARTET (RC-4a) — kein Akzeptanz-Status (ADR_REVIEW_MATRIX G7-03).
- D-042 (Global-State-ADR): Entwurf vorhanden, keine Akzeptierung (GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT; RC-3).

## 7 CHAT_ONLY (keine Autorität, kein Repo-Artefakt)

- D-010 (MUSCAL 2.0, Turnier-Chat 25.07, C2, E-010/E-016), D-011 (Cognitive Kernel, Proposal-Chat, C2, E-015), D-012 (Agent P1…P5, Spec-Chat 30.07, C2, E-011), D-013 (Cognitive Compiler, Spec-Chat 30.07, C2, E-011), D-014; D-030…D-035 (CHAT_ONLY-Satz, DECISION_REGISTRY).
- **Explizit NICHT IMPLEMENTED:** MUSCAL 2.0, Cognitive Kernel, Agent P1…P5, Cognitive Compiler — kein Code-Artefakt belegt (D-012/D-013: „no repo artifact", E-011; G2-M5: „MUSCAL 2.0/Cognitive-Kernel/Agent-Specs chat-only (Phase B)").
- MC-TC-007-Status-Zusammenfassung (31.07): Chat-Artefakt, committet 392734e; Inhalt 12/14 CONDITIONAL GO (E-006/E-007, C1).

## 8 Source Binding

| Abschnitt | Quelle(n) | Confidence |
|---|---|---|
| §4.1 Core-Liste | AGENTS.md | C0 |
| §4.2 EventStore/Replay | G2-01, git log | C1 |
| §4.3 Features-Welle | PA-02 (PHASE_A_REMEDIATION_PLAN), G2-06 (Commits) | C0 |
| §4.4 Frontend | PA-02/PA-03, 8025f2f | C0 |
| §4.5 Schichten | SESSION_CONTINUITY §2, MC-TC-006 | C1 |
| §5 Doku | ADR-INDEX, Manuals, MASTER_INDEX-Freshness | C0/C1 |
| §6/§7 Plan/Chat | DECISION_REGISTRY, REFERENCE_GRAPH E-010…E-016 | C0/C2 |

## 9 Known Limits

- TECHNICAL_BASELINE/ARCHITECTURE stale (12.07): Schichten-Modell hier aus SESSION_CONTINUITY (C1) und Modul-Existenz (C0) abgeleitet, nicht aus Baseline.
- Manual-Zahlen (M-0.6 §4) vs. Ist-Zahlen (611 py/77.376 LOC/1.209 Dateien): Kanon = Census (Doc 19 KG-03/KG-07; TC-Konflikte).
- 29 uncommitted Core-Änderungen (Pre-Audit) sind durch G2 adjudiziert und committet (70f630e) — Stand ist konsolidiert.
- MUSCAL-2.0-Welle: vollständig chat-only/geplant; keine Implementierungs-Checks möglich.

## 10 Validation

- Read-only: keine Datei verändert, keine neue Architektur-Aussage, keine Statusänderung, kein Code.
- Statusprüfung: IMPLEMENTED nur bei C0/C1 mit Repo-Beleg; DRAFT bleibt DRAFT (ADR-022…25); CHAT_ONLY bleibt CHAT_ONLY (D-010…014, D-030…035); MUSCAL 2.0/Cognitive Kernel/Agent P1…P5/Cognitive Compiler ausschließlich in §6/§7 — nirgends IMPLEMENTED.
- Confidence-Prüfung: C0/C1 nur bei Commit-/Datei-Beleg; C2 nur mit Chat-Quelle.
- Widerspruchsprüfung: konsistent mit Doc 04 (E-014/E-015/E-016), Doc 16 (RC-1/RC-3/RC-4a), Doc 19 (KG-07/KG-08/KG-11); kein Widerspruch zu G2-01 (SANCTIONED-Cluster).
