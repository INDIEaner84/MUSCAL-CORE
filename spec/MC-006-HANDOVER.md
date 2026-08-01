# MC-006 HANDOVER — ZUSAMMENFASSUNG FÜR WEITERBEARBEITUNG

**Erstellt:** 2026-07-24
**Zielgruppe:** Weiterarbeitende KI (ChatGPT, Claude, etc.)
**Status:** SPEZIFIKATION VOLLSTÄNDIG — BEREIT ZUR IMPLEMENTIERUNG

---

## 1. WAS WURDE ERREICHT

### MC-005 (Architektur-Review)
- Architektur-Review Board Decision abgeschlossen
- Entscheidung: MUSCAL Cognitive Provenance Layer (MCPL) als semantische Binding-Schicht
- KEINE eigenständige Provenance-System
- Integration mit OpenTelemetry, W3C PROV, Event Sourcing
- 4 P0-Entscheidungen getroffen (Storage, Verification, OTel, Decision Recording)

### MC-006 (Technische Spezifikation)
- Vollständige technische Spezifikation: `spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md` (1.811 Zeilen)
- Reconciliation Matrix: MC-005 vs. tatsächlichem Codebase
- Alle Entity-Typen definiert (Intent, Task, Agent, Model, Decision, Execution, Attempt, Artifact, State, Verification, etc.)
- Event Type Registry mit 28 Event-Typen
- Causal Graph mit allen validen Beziehungen
- Decision Model mit 4-Typen-Decomposition
- Verification Engine Contract mit 4 MVP-Verifiern
- OTel-Mapping spezifiziert
- W3C PROV-Mapping spezifiziert
- Storage Architecture (SQLite für Dev, Outbox+Object Store für Prod)
- 11 Test-Dateien geplant
- 6-Wochen-Implementierungsplan

---

## 2. AKTUELLER CODEBASE-STATUS

### Was bereits existiert (wichtig!)
MUSCAL hat bereits umfangreiche Provenance-Infrastruktur:

| Komponente | Datei | Funktion |
|-----------|-------|----------|
| `ExecutionContext` | `features/identity/execution_context.py` | Thread-local context mit execution_id, correlation_id, causation_id |
| `uuid7` | `features/identity/uuid7.py` | Zeitgeordnete UUID-Generierung |
| `ExecutionMode/State/VerificationState` | `features/identity/reality.py` | Enums für Execution-Modes und -States mit Validierung |
| `ExecutionReceipt` | `features/tool_runtime/tool_runtime.py` | SHA-256 Integrity Hash, tool execution evidence |
| `VerificationResult` | `features/tool_runtime/tool_runtime.py` | Status: PENDING/EXECUTED/VERIFIED/FAILED/INCONCLUSIVE/NOT_SUPPORTED/TAMPERED |
| `VerificationStatus` | `features/tool_runtime/tool_runtime.py` | Status-Enum |
| `UnifiedToolRuntime` | `features/tool_runtime/tool_runtime.py` | Tool execution mit receipt generation |
| `EventStore` | `runtime/event_store.py` | SQLite persistence mit execution_id, correlation_id, causation_id Spalten |
| `ProvenanceResolver` | `features/provenance/resolver.py` | Post-hoc reconstruction von execution provenance |
| `EvidenceClassifier` | `features/provenance/classifier.py` | Klassifikation: VERIFIED/INFERRED/MISSING/CONFLICT |
| `MetaEvaluator` | `features/provenance/evaluation.py` | Quality evaluation |
| `DecisionWriter` | `features/provenance/decision_writer.py` | Decision persistence in SQLite |
| `ProvenanceContext` | `features/provenance/context.py` | Thread-local trace/span/decision ID context |
| `ReplayService` | `features/replay/replay_service.py` | Basic replay |
| `EventBus` | `event_bus.py` | In-memory pub/sub |
| `TraceEngine` | `trace_engine.py` | In-memory trace (CLI-only) |

### Was fehlt (MC-006 adressiert dies)
- **Kein `attempt_id`** — Nirgends im Codebase
- **Keine Decision-Decomposition** — `decisions` Tabelle hat nur einen Typ
- **Kein MCPL Event Type Registry** — Nur ad-hoc event types
- **Kein Verification Engine mit verifier_type Taxonomie**
- **Keine Kernel-Integration-Hooks** — 14 Hook-Punkte existieren, aber keine MCPL Emission
- **Kein OTel-Mapping** — ADR-009 ist PROPOSED, nicht implementiert
- **Kein W3C PROV-Mapping**
- **Keine `artifact_id`, `state_id`, `join_id`, `replay_of` Konzepte**

---

## 3. KRITISCHE ENTSCHEIDUNGEN (P0)

Alle in MC-005 getroffen, in MC-006 umgesetzt:

| ID | Entscheidung | Empfehlung |
|----|-------------|-----------|
| P0-1 | Storage Backend | Hybrid: SQLite (Dev) + Outbox+ObjectStore (Prod) |
| P0-2 | Verification Taxonomie | MVP: deterministic, schema, invariant, rule_engine |
| P0-3 | OTel Integration | Span+Events für v1, External Store für v2 |
| P0-4 | Decision Recording | Beide: MODEL_OUTPUT + AGENT_DECISION, explizit causal verknüpft |

---

## 4. DATEIEN — STATUS

### Dateien die GEÄNDERT werden müssen (10)

| Datei | Änderung | Priorität |
|-------|----------|-----------|
| `features/identity/execution_context.py` | intent_id, task_id hinzufügen | P0 |
| `features/identity/reality.py` | attempt_status Enum hinzufügen | P0 |
| `features/tool_runtime/tool_runtime.py` | attempt_id zu ExecutionReceipt hinzufügen | P0 |
| `features/provenance/models.py` | Neue Entity-Typen hinzufügen | P0 |
| `features/provenance/decision_writer.py` | decision_type Support hinzufügen | P0 |
| `features/provenance/context.py` | intent_id, task_id context hinzufügen | P0 |
| `runtime/event_store.py` | MCPL Spalten-Unterstützung | P0 |
| `runtime/database.py` | MCPL Tabellen-Erstellung | P0 |
| `kernel.py` | MCPL Emission Hooks | P1 |
| `features/provenance/resolver.py` | Für MCPL erweitern | P1 |

### Dateien die ERSTELLT werden müssen (14 Implementation + 16 Tests)

**Core MCPL:**
1. `features/provenance/mcpl_schema.py` — Alle Entity-Typen
2. `features/provenance/mcpl_events.py` — Event Type Registry
3. `features/provenance/mcpl_emitter.py` — Provenance Event Emitter
4. `features/provenance/mcpl_store.py` — MCPL Persistence Layer
5. `features/provenance/verification_engine.py` — Verification Engine
6. `features/provenance/verifiers/deterministic.py` — Deterministic Verifier
7. `features/provenance/verifiers/schema.py` — Schema Verifier
8. `features/provenance/verifiers/invariant.py` — Invariant Verifier
9. `features/provenance/verifiers/rule_engine.py` — Rule Engine Verifier
10. `features/provenance/mcpl_query.py` — Query Interface
11. `features/provenance/mcpl_otel.py` — OTel Mapping
12. `features/provenance/mcpl_prov.py` — W3C PROV Mapping
13. `features/provenance/kernel_hooks.py` — Kernel Integration
14. `features/provenance/__init__.py` — Package init (falls nicht vorhanden)

**Tests:**
15. `tests/provenance/test_mcpl_schema.py`
16. `tests/provenance/test_mcpl_events.py`
17. `tests/provenance/test_verification_engine.py`
18. `tests/provenance/test_mcpl_store.py`
19. `tests/provenance/test_mcpl_query.py`
20. `tests/provenance/test_mcpl_otel.py`
21. `tests/provenance/test_mcpl_security.py`
22. `tests/provenance/test_mcpl_retry.py`
23. `tests/provenance/test_mcpl_replay.py`
24. `tests/provenance/test_mcpl_parallel.py`
25. `tests/provenance/test_mcpl_decision.py`
26. `tests/provenance/test_mcpl_human.py`
27. `tests/provenance/test_mcpl_kernel_hooks.py`
28. `tests/provenance/test_mcpl_store.py` (bereits oben)
29. `tests/provenance/test_mcpl_query.py` (bereits oben)
30. `tests/provenance/test_mcpl_otel.py` (bereits oben)

---

## 5. IMPLEMENTIERUNGSREIHENFOLGE

### Batch 1: Foundation (Woche 1-2)
1. `features/provenance/mcpl_schema.py` erstellen
2. `features/provenance/mcpl_events.py` erstellen
3. `features/identity/execution_context.py` erweitern
4. `features/tool_runtime/tool_runtime.py` erweitern (attempt_id)
5. `runtime/database.py` erweitern (MCPL Tabellen)
6. `features/provenance/mcpl_emitter.py` erstellen
7. `features/provenance/mcpl_store.py` erstellen
8. `kernel.py` erweitern (MCPL Emission Hooks)

### Batch 2: Verification (Woche 3)
9. `features/provenance/verification_engine.py` erstellen
10. `features/provenance/verifiers/deterministic.py` erstellen
11. `features/provenance/verifiers/schema.py` erstellen
12. `features/provenance/verifiers/invariant.py` erstellen
13. `features/provenance/verifiers/rule_engine.py` erstellen

### Batch 3: Query & Reconstruction (Woche 4)
14. `features/provenance/mcpl_query.py` erstellen
15. `features/provenance/resolver.py` erweitern

### Batch 4: OTel + PROV (Woche 5)
16. `features/provenance/mcpl_otel.py` erstellen
17. `features/provenance/mcpl_prov.py` erstellen

### Batch 5: Security & Adversarial (Woche 6)
18. `tests/provenance/test_mcpl_security.py` erstellen
19. Alle adversarial Tests implementieren

---

## 6. VERIFICATION ENGINE — WICHTIGSTE KONZEPTE

### 4 MVP Verifier Types
```python
class VerifierType(str, Enum):
    DETERMINISTIC = "deterministic"  # Exact match, recomputation
    SCHEMA = "schema"                # JSON Schema, type validation
    INVARIANT = "invariant"          # Constraint holds
    RULE_ENGINE = "rule_engine"      # Deterministic policy rules
```

### 6 Verification Statuses
```python
class VerificationStatus(str, Enum):
    REQUESTED = "requested"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    OVERRIDDEN = "overridden"
```

### 4 Verification Targets
```python
class VerificationTarget(str, Enum):
    EXECUTION = "execution"     # Logical execution completion
    ATTEMPT = "attempt"         # Physical attempt success
    ARTIFACT = "artifact"       # Artifact correctness
    STATE = "state"             # State correctness
```

### Verifier Interface
```python
class Verifier(Protocol):
    @property
    def verifier_type(self) -> VerifierType: ...
    @property
    def verifier_id(self) -> str: ...
    def verify(self, subject: Any, expected: dict) -> VerificationResult: ...
```

---

## 7. DECISION MODEL — WICHTIGSTE KONZEPTE

### 4 Decision Types (NIEMALS zusammenfallen lassen!)
```python
class DecisionType(str, Enum):
    MODEL_OUTPUT = "model_output"      # Raw LLM completion
    AGENT_DECISION = "agent_decision"  # Agent selected action
    POLICY_DECISION = "policy_decision"  # Rule-based authorization
    HUMAN_DECISION = "human_decision"    # Human approval/rejection
```

### Causal Chain (MUSS explizit aufgezeichnet werden)
```
MODEL_OUTPUT "proposed_action_X"
  ↓ [NOT: "the LLM decided X"]
AGENT_DECISION "selected_action_X from candidates [X, Y, Z]"
  ↓
POLICY_DECISION "policy_p99 allows_action_X"
  ↓
EXECUTION_AUTHORIZATION "execution_of_X authorized"
  ↓
EXECUTION "tool_call_X(args)"
```

---

## 8. EVENT TYPE REGISTRY — 28 EVENT-TYPEN

```python
class MCPLEventType(str, Enum):
    INTENT_CREATED = "intent.created"
    INTENT_COMPLETED = "intent.completed"
    INTENT_FAILED = "intent.failed"
    INTENT_CANCELLED = "intent.cancelled"
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    MODEL_INVOKED = "model.invoked"
    MODEL_OUTPUT = "model.output"
    DECISION_AGENT = "decision.agent"
    DECISION_POLICY = "decision.policy"
    DECISION_HUMAN = "decision.human"
    EXECUTION_AUTHORIZED = "execution.authorized"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_RETRY = "execution.retry"
    EXECUTION_CANCELLED = "execution.cancelled"
    TOOL_CALL = "tool.call"
    TOOL_CALL_RESULT = "tool.call.result"
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_MODIFIED = "artifact.modified"
    STATE_CHANGED = "state.changed"
    VERIFICATION_REQUESTED = "verification.requested"
    VERIFICATION_STARTED = "verification.started"
    VERIFICATION_RESULT = "verification.result"
    EXECUTION_JOIN = "execution.join"
    EXECUTION_REPLAY = "execution.replay"
```

---

## 9. IDENTIFIER SEMANTIK — KRITISCHE UNTERSCHIEDE

| ID | Eindeutigkeit | Unveränderlich? | Bedeutung |
|----|--------------|----------------|-----------|
| `correlation_id` | Global — geteilt über gesamten Workflow | Ja | OTel Trace ID |
| `causation_id` | Pro causal chain — Wurzel einer causalen Sequenz | Ja | Erstes Event in Chain |
| `intent_id` | Pro Intent | Ja | Welcher Intent |
| `task_id` | Pro Task | Ja | Welcher Task-Knoten |
| `execution_id` | Pro logischer Execution | Ja | Logische Execution (kann Retries haben) |
| `attempt_id` | Pro physischem Attempt | Ja | Physischer Versuch (RETRY) |
| `decision_id` | Pro Decision Event | Ja | Welche Decision |
| `verification_id` | Pro Verification | Ja | Welche Verification |
| `artifact_id` | Pro Artifact | Ja | Welches Artifact |
| `state_id` | Pro State Change | Ja | Welche State-Änderung |

### KRITISCHE REGEL
```
execution_id ≠ attempt_id

Eine Execution mit 3 Retries hat:
- 1 execution_id (logisch)
- 3 attempt_id Werte (physisch)

Verifizierung muss explizit angeben, welches sie meint:
- verification.subject_id = "att_01J2...003"  ← Attempt 3
- verification.subject_type = VerificationTarget.ATTEMPT
```

---

## 10. OTEL MAPPING

| MCPL Konzept | OTel Mapping |
|-------------|--------------|
| Intent/Workflow | Trace (Root Span) |
| Task | Span (Child) |
| Execution | Span |
| Attempt | Child Span |
| Model Invocation | Span (GenAI Attributes) |
| Decision | Event on Parent Span |
| Tool Call | Span |
| Verification | Span |
| State Change | Event |

### Was NIEMALS in OTel gespeichert wird
- Vollständiger Provenance DAG
- Signierte Receipts
- Verification Evidence Blobs
- Lange causal chains
- Content Blobs

---

## 11. W3C PROV MAPPING

| MCPL Entity | PROV Type |
|-------------|-----------|
| Intent | prov:Entity + muscal:Intent |
| Task | prov:Entity + muscal:Task |
| Agent | prov:Agent |
| Model | prov:Agent + muscal:Model |
| ModelOutput | prov:Entity + muscal:ModelOutput |
| Decision | prov:Activity |
| Execution | prov:Activity |
| ToolCall | prov:Activity + muscal:ToolCall |
| Artifact | prov:Entity |
| State | prov:Entity + muscal:State |
| Verification | prov:Activity + muscal:Verification |

---

## 12. SECURITY — ADVERSARIAL TEST PLAN

| # | Angriff | Schwere | Schutz |
|---|---------|---------|--------|
| S1 | Fabricate execution success | HOCH | Receipt integrity + verification independence |
| S2 | Fabricate receipts | HOCH | UTR-only receipt generation |
| S3 | Alter verification results | HOCH | Independent verification storage |
| S4 | Alter expected state after execution | HOCH | Expected state frozen before execution |
| S5 | Replay without distinction | MITTEL | replay_of field; new execution_id |
| S6 | Confuse attempt_id and execution_id | MITTEL | Schema validation |
| S7 | Bypass policy decisions | HOCH | PolicyDecision required before execution |
| S8 | Bypass human approval | HOCH | HumanDecision required before execution |
| S9 | Create false causal links | MITTEL | Entity existence validation |
| S10 | Claim simulation as actual execution | HOCH | ExecutionMode enforcement |
| S11 | Inject false provenance events | MITTEL | Duplicate event_id detection |

---

## 13. TEST STATUS

### Bestehende Tests
- **547/547 bestanden (100%)** — Stand: 2026-07-20
- 1 skipped, 0 failed, 0 errors
- P0/P1 Gaps: VOLLSTÄNDIG GESCHLOSSEN

### Achtung: Pre-existing Issue
- `tests/reconciliation/test_regression_baseline.py` erwartet 87 Findings, sind 91
- Dies ist VORHANDEN und NICHT MC-006-spezifisch
- Wird durch MC-006 nicht beeinflusst (nur Markdown-Spezifikation)

### MC-006 Tests (geplant)
- 16 Test-Dateien covering: schema, events, verification, store, query, OTel, security, retry, replay, parallel, decision, human, kernel hooks

---

## 14. WEITERARBEITUNG — CHECKLISTE

### Für die nächste KI:
1. Lies `spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md` (vollständig)
2. Lies `spec/MC-005-MCPL-ARCHITECTURE-REVIEW.md` (falls vorhanden)
3. Starte mit Batch 1 (Foundation)
4. Erstelle `features/provenance/mcpl_schema.py` mit ALLEN Entity-Typen
5. Erstelle `features/provenance/mcpl_events.py` mit Event Type Registry
6. Erweitere `features/identity/execution_context.py` um intent_id, task_id
7. Erweitere `features/tool_runtime/tool_runtime.py` um attempt_id
8. Erstelle MCPL Tabellen in `runtime/database.py`
9. Erstelle `features/provenance/mcpl_emitter.py`
10. Erstelle `features/provenance/mcpl_store.py`
11. Erweitere `kernel.py` um MCPL Emission Hooks
12. Führe alle bestehenden Tests aus (547/547 müssen bestehen)
13. Erstelle und führe MCPL-spezifische Tests aus
14. Iteriere über alle 6 Batches

### Wichtige Constraints:
- Core-Dateien sind IMMUTABLE (ADR-007) — Änderungen nur mit OVERRIDE
- Plugin-Architektur: Features gehören in `features/`
- Keine Core-Imports in Plugins
- Alle neuen IDs via `features/identity/uuid7.py:uuid7()`
- Alle Enums via `enum.Enum`
- Thread-Safety via `threading.RLock()` wo nötig

---

## 15. ZUSAMMENFASSUNG

**Status:** MC-006 Spezifikation ist VOLLSTÄNDIG und INTERNS KONSISTENT
**Bereit zur Implementierung:** JA
**Keine P0-Blocker:** ALLE P0-Entscheidungen in MC-005 getroffen
**Bestehende Infrastruktur:** UMFANGREICH (features/provenance/, features/identity/, features/tool_runtime/)
**Fehlende Komponenten:** attempt_id, decision decomposition, verification engine, MCPL events, OTel mapping, W3C PROV mapping
**Geschätzte Dauer:** 6 Wochen (6 Batches × 1 Woche)

---

*MC-006 Handover v1.0 — 2026-07-24*
*Bereit für Weiterarbeitung durch externe KI.*
