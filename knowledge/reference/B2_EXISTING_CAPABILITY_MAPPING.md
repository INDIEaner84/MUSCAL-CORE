# B2_EXISTING_CAPABILITY_MAPPING

Phase 0.5 — Bestands-Analyse vorhandener B2-Komponenten (vor jeder EventStore-v2-Änderung)

- Datum: 02.08.2026
- Rolle: Senior Architecture Implementation Agent
- Modus: **READ ONLY** — keine Implementierung, keine Änderungen, keine Commits, keine Entscheidung
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Zweck: vollständige Übersicht der bereits vorhandenen B2-Bausteine → Wiederverwendungs-/Redundanz-Bewertung → Vermeidung von Doppelbau
- Quellen: Code-Inspektion 02.08.2026 (features/projection, features/verification, features/provenance, features/cognitive_unit, spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md), B2_EXECUTION_BASELINE_REPORT.md [B2B], MINIMAL_COGNITIVE_LEDGER_SPECIFICATION.md [MCLS], CLIC/CLAR/ESIA
- Status: **created, not committed (external KF layer)**

---

## 1. features/projection/

| Aspekt | Befund |
|--------|--------|
| **Zweck** | [F] Normalisierungs-/Canonicalisierungs-Schicht: rohe EventBus-EventMessages → validierte, normalisierte Events (PROJECTION_VERSION 2.0.0) [F: features/projection/graph_os_projection.py:17,108-166] |
| **Inputs** | [F] EventBus `EventMessage` (raw.topic, raw.payload, raw.source, raw.id, raw.timestamp) [F: graph_os_projection.py:114-115]; optional EventStore (nur seq-Auflösung via get_cursor) [F: graph_os_projection.py:168-174] |
| **Outputs** | [F] normalisiertes Event-Dict: event_id, event_type, event_version, timestamp, sequence_number, execution_id, correlation_id, causation_id, source, actor, execution_mode, execution_state, verification_state, provenance, payload (saniert) [F: graph_os_projection.py:140-156] |
| **Event-Abhängigkeiten** | [F] CANONICAL_EVENT_TYPES: NODE_CREATED, NODE_UPDATED, NODE_COMPLETED, NODE_FAILED, NODE_ARCHIVED, EDGE_CREATED, EDGE_REMOVED, EXECUTION_*, SIMULATION_*, VERIFICATION_PASSED/FAILED [F: :34-49]; CANONICAL_SOURCES (12 Erzeuger) [F: :19-32]; Validation via verify_state_transition [F: :92-105]; Sensitive-Field-Sanitizing [F: :51-62,80-89] |
| **Persistenz** | [F] persistiert **nicht** selbst — liefert normalisierte Dicts; EventStore nur als seq-Quelle [F: :110-112,168-174] |
| **Überschneidung mit geplanter Graph Projection** | [I] **komplementär, nicht redundant**: graph_os_projection = Eingangs-Normalisierung (raw → canonical, Eingangs-Validierung); geplante Graph Projection (B2MA §2/CLIC P3) = Ausgangs-Rekonstruktion (Events → GraphState) [I]. [I] Gemeinsame Schnittstelle: CANONICAL_EVENT_TYPES ist Referenz für die geplante Rebuild-Projektion (welche Typen zulässig sind) [I] |
| **Fehlende Event-Typen** | [F] NODE_REMOVED, EDGE_UPDATED, PRUNING_EXECUTED, FOCUS_CHANGED fehlen in CANONICAL_EVENT_TYPES [F: :34-49] — Phase-2-Typen müssten ergänzt werden (features/ — zulässig) [I: MCLS §1.5] |

## 2. features/verification/

| Aspekt | Befund |
|--------|--------|
| **Vorhandene CLAIM≠PROOF-Logik** | [F] IntegrityVerifier: prüft receipt.finalized + receipt.verify_integrity() → TAMPERED bei Verletzung [F: features/verification/verifier.py:31-75]; VerificationStatus (EXECUTED/VERIFIED/TAMPERED/NOT_SUPPORTED …) [F: verifier.py:9-12]; BUILTIN_VERIFIERS (integrity_check, math.add …) [F: verifier.py:25-26] |
| **Receipt-Verarbeitung** | [F] Orchestrator: Integrity-Verifier zuerst, dann Tool-Verifier; VerificationResult (verification_id, execution_id, receipt_id, expected/observed state, evidence, verified_at) [F: features/verification/orchestrator.py:58-80]; LIFECYCLE-Events VERIFICATION_PASSED/FAILED via EventBus [F: orchestrator.py:34-37]; store_and_publish [F: orchestrator.py:68] |
| **State Validation** | [F] verify_state_transition (features/identity/reality) im Orchestrator + Projection [F: orchestrator.py:12-15; graph_os_projection.py:101-105]; HardRuleViolation + RuleEngine (rules.py) [F: orchestrator.py:23] |
| **Persistenz-Anbindung** | [F] Receipt-/Verification-Persistenz via EventStore.store_receipt/store_verification (UTR-Callbacks gewirkt) [F: spec/OVERRIDE.md:1433-1434; runtime/event_store.py:154-272]; orchestrator hält eigene In-Memory _verification_store [F: orchestrator.py:49] |
| **Fehlende Funktionen (B2-Ziel)** | [I] Evidence-Events (evidence.attached/verified) fehlen [I: MCLS §1.2]; Entscheidungs-/Agent-Events fehlen [I: MCLS §1.1/§1.4]; Ketten-Hash auf Events fehlt [I: MCLS §4.2]; Governance-Autorisierung (agent.authorized) nicht im Verifier-Pfad [I: MCLS §1.4]; keine Verbindung zu muscal/verification (Parallel-Existenz) [I: STE E1.1] |

## 3. features/provenance/

| Aspekt | Befund |
|--------|--------|
| **Provenance-Modell** | [F] MCPL-Schema v1.0.0: Intent, Task, Agent, Model, ModelOutput, Decision (MODEL_OUTPUT/AGENT_DECISION/POLICY_DECISION/HUMAN_DECISION), AgentDecision, PolicyDecision, HumanDecision (HumanAction APPROVE/REJECT/OVERRIDE/MODIFY), Execution, Attempt, ToolCall, Artifact, State (CREATED/MODIFIED/DELETED), Verification, Join (ALL/ANY/QUORUM/THRESHOLD/TIMEOUT/BEST_EFFORT), ProvenanceRecord [F: features/provenance/mcpl_schema.py:17-90] |
| **Lifecycle/Transitions** | [F] validierte Zustands-Übergänge: Execution (REQUESTED→AUTHORIZED→STARTED→RUNNING→…→COMPLETED/FAILED/CANCELLED), Attempt, Verification (REQUESTED→RUNNING→PASSED/FAILED/INCONCLUSIVE→OVERRIDDEN) [F: mcpl_schema.py:150-210]; ReplayClassification (REPLAYABLE/PARTIALLY_REPLAYABLE/NON_REPLAYABLE) [F: :87-90]; VerifierType (deterministic…human) [F: :59-68] |
| **Hash/Evidence-Unterstützung** | [F] Verification-Entity mit VerifierType/Status im Modell [F: mcpl_schema.py:50-68]; [I] Event-Hash-Kette (prev_hash) ist **nicht** Teil des MCPL-Modells (kein Hash-Feld gefunden) [I] — Lücke zu MCLS §4.2 [I] |
| **Integration mit EventStore** | [F] **keine direkte EventStore-Anbindung**: MCPLStore persistiert in eigenen `mcpl_*`-Tabellen (14 Tabellen, WAL) [F: features/provenance/mcpl_store.py:34-58]; mcpl_emitter sammelt Records in-memory/listener-basiert, kein event_store.append [F: mcpl_emitter.py:59,105]; Event-Mapping via mcpl_events (MCPLEventType → EventMapping) [F: mcpl_events.py:19,67-76]; decision_writer schreibt zusätzlich in Legacy-`decisions`-Tabelle [F: decision_writer.py:28-50] |
| **Bewertung** | [I] MCPL ist ein **viertes Event-/Daten-System parallel zu stored_events** — hohe Überschneidung mit Ledger-Ziel (Decision/Verification/State-Modelle existieren bereits) [I]; spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:84-86 deklariert stored_events als autoritativen Store, der um MCPL-Spalten **erweitert** werden soll — d. h. geplante Zusammenführung, kein Neubau [F] |

## 4. features/cognitive_unit/

| Aspekt | Befund |
|--------|--------|
| **Rolle im Pipeline-Kontext** | [F] Execution-Unit: governance.check → worker → safety_gate → tool_runtime.execute [F: features/cognitive_unit/cognitive_unit.py:15-59]; Rückgabe-Status: blocked_by_governance / blocked_by_safety / success / error / noop [F: :24-66]; registry + specialized-Varianten existieren [F: features/cognitive_unit/registry.py:1-37; specialized.py:1-296] |
| **Zustandsverwaltung** | [F] **stateless**: keine eigene Zustands-Persistenz; Ergebnis-Dicts werden zurückgegeben, kein State-Handling [F: cognitive_unit.py:22-66] |
| **Event-Erzeugung** | [F] **keine direkten Events**; Events entstehen nur indirekt über tool_runtime (Receipts) [F: cognitive_unit.py:49-59] |
| **B2-Bedeutung** | [I] CognitiveUnit ist der natürliche **Ankerpunkt für den Agent→Capability→Authorization→Execution→Evidence→Verification→Commit-Fluss** (B2PKG Teil 5): governance.check = Authorization, tool_runtime = Execution, Receipt = Evidence — aber: keine Ledger-Events (decision.*/agent.authorized/evidence.*) [I: MCLS §1.4; cognitive_unit.py:22-30] |

## 5. MCPL (Gesamt-Prüfung)

| Prüfpunkt | Befund |
|-----------|--------|
| **Bestehende Projection** | [F] zwei: (a) graph_os_projection (Canonical-Normalisierung, features/projection) [F: graph_os_projection.py:108-166]; (b) MCPL-Event-Mapping (ProvenanceRecord → Events, mcpl_events.py:290+) [F] — beide **keine** GraphState-Rekonstruktions-Projektion [I] |
| **Lifecycle** | [F] vollständige Status-Enums + validierte Transitions (Execution/Attempt/Verification) [F: mcpl_schema.py:150-210]; Verification-OVERRIDDEN-Pfad explizit [F: :56,182-185] |
| **Datenmodell** | [F] 14 mcpl_*-Tabellen (intents, tasks, agents, models, model_outputs, decisions, executions, attempts, tool_calls, artifacts, states, verifications, joins, provenance_events) [F: mcpl_store.py:34-40]; DB_PATH = config.DB_PATH (gleiche SQLite-Datei wie stored_events) [F: mcpl_store.py:47] |
| **Replay** | [F] MCPL-Events sind über Event-Mapping emitierbar, aber nicht in stored_events gespeichert (kein EventStore-Kontakt) [F: mcpl_emitter.py:59,105; mcpl_events.py:290+] — **MCPL ist heute nicht replaybar über MC-TC-006-Pfad** [I] |
| **Kollision** | [F] spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:81-86: stored_events soll um MCPL-Schema erweitert werden — deckt sich mit MCLS-Schema-v2-Richtung (aggregate_id/-type, evidence, decisions) [I]; aber: Implementierung existiert als Parallel-Store, nicht als Erweiterung [F: mcpl_store.py] — **Kurskorrektur-Risiko** [I: B2B B-R10] |

---

## 6. COMPONENT_OVERLAP_MATRIX

| Komponente | Existiert | B2 Ziel | Überschneidung | Risiko | Entscheidung benötigt |
|------------|-----------|---------|----------------|--------|-----------------------|
| graph_os_projection (features/projection) | ✅ [F: graph_os_projection.py:108] | Graph Projection (State-Rekonstruktion) | [I] komplementär: Eingangs-Normalisierung vs. Ausgangs-Rebuild; CANONICAL_EVENT_TYPES als Typ-Referenz | [I] gering — keine Doppel-Funktion; Typ-Liste muss Phase-2-Typen aufnehmen | [I] Ja: Nutzung als Canonical-Eingangs-Stufe des Rebuilds (statt zweite Normalisierung) |
| features/verification (Verifier/Orchestrator/Rules) | ✅ [F: verifier.py:31-75; orchestrator.py:40] | Verification Layer (CLAIM≠PROOF) | [I] Kern-Verification existiert (Integrity→Tool-Verifier→Publish); fehlt: Evidence-/Decision-/Agent-Events, Ketten-Hash | [I] mittel — Gefahr Doppelbau mit muscal/verification (engine/states) | [I] Ja: Abgrenzung CORE-Verifier vs. muscal-Verifier (Phase 6-Mapping) |
| features/provenance (MCPL: Store/Schema/Events/Emitter) | ✅ [F: mcpl_store.py:43; mcpl_schema.py:10] | Cognitive Ledger (Decision/Evidence/Verification/State) | [I] **hoch** — MCPL-Modelle decken Ledger-Fachmodelle bereits ab (Decision/Verification/State/Agent) [F: mcpl_schema.py:17-90] | [I] **hoch** — viertes Event-System parallel zu stored_events; nicht replaybar über MC-TC-006 [I] | [I] **Ja — kritisch**: MCPL-Store → stored_events-Zusammenführung (spec-Richtung [F: MC-006-Spec:81-86]) oder bewusst separat halten; darf NICHT parallel weiterwachsen [I] |
| features/cognitive_unit | ✅ [F: cognitive_unit.py:4-66] | Agent-Governance-Fluss (Authorization/Execution) | [I] Authorization-/Execution-Anker vorhanden; keine Events, stateless | [I] mittel — stille Zustandsänderungen (MCLS-Invariante 5) ohne Ledger-Anbindung | [I] Ja: Event-Erzeugung (decision.*/evidence.*) aus Unit heraus — features/-Plugin-Pfad |
| muscal/ (Paket: verification, governance, claims, evidence) | ✅ [F: muscal/pyproject.toml; muscal/src/muscal/] | Verification + Governance Layer (B2-Phase 6) | [I] **hoch** — muscal/verification (engine/states) überlappt mit features/verification; muscal/governance mit cognitive_unit.governance | [I] **hoch** — Doppel-Verification (zwei Implementierungen gleicher Funktion) | [I] **Ja — kritisch**: Phase-6-Integrations-Map muss Rollen je Schicht festlegen (Adapter, keine Kopie) [I: MCLS §5.3] |
| EventStore stored_events | ✅ [F: runtime/event_store.py:36-37] | Single Truth + Cognitive Ledger-Kette | [I] zentraler Kern; Schema v2 additiv | [I] mittel — Trust-Boundary (OVERRIDE-Pflicht) | [F] Ja: RC-1a-Entscheidung offen (PENDING HUMAN) [F: PST:47] |
| Legacy `events` + `decisions`-Tabellen | ✅ [F: runtime/database.py:53-71,93-124] | — | [I] Doppel-Wahrheit (B-R1 CRITICAL [F: MC-TC-004-POST-REMEDIATION:540]); decision_writer schreibt parallel [F: decision_writer.py:28-50] | [I] hoch — Konsistenz ohne Reconcile nicht prüfbar | [I] Ja: Ablösungs-Strategie (Projektions-Leser vs. Abschaltung) |
| audit_log | ✅ [F: features/observability/event_persistence.py:40-59] | — (Ledger-Audit = stored_events) | [I] 30d-Retention ungeeignet für Ledger [F: :8,33] | [I] gering (Rollen-Klarstellung) | [I] Ja: Rolle festlegen (operativer Log ≠ Ledger-Audit) |

---

## 7. Bewertung: Wiederverwendung / Redundanz / Doppelbau-Verbot

### Wiederverwendbar (reuse)

| Komponente | Nutzung im B2-Pfad |
|------------|--------------------|
| graph_os_projection | [I] Canonical-Eingangs-Stufe des Rebuild-/Projection-Pfads; CANONICAL_EVENT_TYPES erweitern (Phase 2) [I] |
| features/verification (IntegrityVerifier, Orchestrator, RuleEngine) | [I] CORE-seitige Execution-Verification; Evidence-/Decision-Events ergänzen [I] |
| MCPL-Schema (Enums, Transitions, Modelle) | [I] Fachmodell für decision.*/evidence.*/agent.*-Events (Mapping auf stored_events statt Parallel-Store) [I: MC-006-Spec:81-86] |
| mcpl_schema Transitions (Execution/Verification) | [I] direkt als Invarianten-Quelle für Ledger-Events (verifizierte Übergänge) [I] |
| cognitive_unit (governance/safety/tool-flow) | [I] als Authorization-/Execution-Anker im Agent-Fluss; Event-Erzeugung ergänzen [I] |

### Redundant (darf NICHT doppelt weiterwachsen)

| Komponente | Begründung |
|------------|------------|
| MCPLStore (14 mcpl_*-Tabellen) | [I] Parallel-Speicher zu stored_events ohne Replay-Integration — hohes Redundanz-Risiko (B2B B-R10); spec sieht Erweiterung von stored_events vor [F: MC-006-Spec:84-86] — Zusammenführung statt Ausbau [I] |
| muscal/verification (engine/states) | [I] Doppel-Implementierung zur features/verification — Phase 6 muss eine Schicht als ausführend (Adapter) und eine als Referenz definieren; keine zweite Laufzeit kopieren [I] |
| event-Erzeugung pro Komponente (ad-hoc) | [I] jede neue Komponente darf nur über den Store-append-/Projection-Pfad Events erzeugen (MCLS-Invariante 5), nicht eigene Logs öffnen [I] |

### Doppelbau-Verbot (hart)

1. [I] **Kein zweiter EventStore**: alle Events gehen in stored_events (event_id UNIQUE) [F: runtime/event_store.py:57]
2. [I] **Keine zweite Graph-Normalisierung**: graph_os_projection ist die Eingangs-Stufe; Rebuild-Projektion ist die Ausgangs-Stufe [I]
3. [I] **Keine zweite Verification-Engine**: features/verification (CORE-Seite) vs. muscal/verification (Layer) — Zuordnung in Phase-6-Map, keine neue dritte [I]
4. [I] **Kein vierter Event-/Daten-Speicher**: MCPL-Store wird in die stored_events-Erweiterung überführt oder bleibt ausschließlich Lese-Projektion [I: MC-006-Spec:81-86]

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), keine Implementierung, kein Commit, keine Entscheidung getroffen.
- Alle [F] mit Datei:Zeile; [H]/[I] gekennzeichnet; Konsistenz mit B2B/MCLS/CLIC/ESIA und spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md geprüft.
- Nächster Schritt laut Prompt: **Ende nach Erstellung**.

**ENDE (Phase 0.5 abgeschlossen).**
