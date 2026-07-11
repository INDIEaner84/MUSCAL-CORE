# MUSCAL Critical Path Test Specification v0.1

> **Ziel:** Critical Path Coverage für MUSCAL Core v0.8
> **Prinzip:** Jeder Layer hat einen definierten Input/Output-Kontrakt + Grenzfälle + Determinismus-Anforderung
> **Nichtziel:** 90% Coverage — Fokus auf die Pipeline: Input → MKC → Bridge → MEL → Memory → Replay

---

## Test-Architektur

```
tests/
├── core/
│   ├── test_boot.py              # Boot-Sequenz & State-Transitions
│   ├── test_state_transition.py  # Kernel-Lebenszyklus
│   └── test_events.py            # Event-Routing
├── compiler/
│   ├── test_mkc.py               # NL → MCXF Kompilierung
│   └── test_bridge.py            # MCXF → ExecutionPlan Mapping
├── execution/
│   └── test_mel.py               # Plan → Tool-Execution
├── memory/
│   └── test_memory.py            # Speicherung & Replay
├── graph/
│   └── test_graph.py             # GraphState-Operationen
├── api/
│   └── test_api_boot.py          # API-Endpunkt-Smoke-Tests
└── system/
    └── test_optimizer_pipeline.py # Optimizer-Durchstich
```

---

## Layer 1: Kernel — `test_boot.py`, `test_state_transition.py`, `test_events.py`

### Kontrakt: `MuscalKernel.__init__()`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | `enable_graph`, `enable_sphere`, optional `debugger` |
| **Output** | Instanz mit Sub-Modulen: `.mkc`, `.mel`, `.bridge`, `.feedback`, `.memory`, `.rag`, optional `.graph`, `.sphere` |
| **Nebenwirkung** | `memory.init()` wird aufgerufen |
| **Determinismus** | Gleiche Parameter → identische Submodul-Konfiguration |

### Tests

```
1. test_creation_default
   Input:  enable_graph=False, enable_sphere=False
   Erwartet: graph=None, sphere=None, alle Sub-Module existieren
   
2. test_creation_with_graph
   Input:  enable_graph=True, enable_sphere=False
   Erwartet: graph != None, sphere == None
   
3. test_creation_with_sphere
   Input:  enable_graph=True, enable_sphere=True
   Erwartet: graph != None, sphere != None, sphere.graph == graph
   
4. test_creation_with_debugger
   Input:  debugger=DebugEngine()
   Erwartet: self.debugger == debugger
```

### Kontrakt: `MuscalKernel.run(input_text)`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | `input_text: str` |
| **Output** | `KernelResult(mcxf, execution, memory_id, feedback, success, errors, execution_plan)` |
| **Nebenwirkung** | Graph-Nodes/Edges, Memory-Einträge, EventBus-Emissionen |
| **Determinismus** | Gleicher Input → gleicher Output (modulo timestamps, memory IDs) |

### Tests — Happy Path

```
5. test_run_simple_string
   Input:  "hello world"
   Erwartet: success=True/False (akzeptiert beide), execution list, memory_id > 0

6. test_run_produces_mcxf
   Input:  "print hello"
   Erwartet: result.mcxf.tasks > 0, result.mcxf ist MCXFDocument
   
7. test_run_produces_execution_plan
   Input:  "write hello.txt content=world"
   Erwartet: result.execution_plan.steps > 0
   
8. test_run_graph_growth
   Input:  "test"
   Vorher: graph.nodes zählen
   Nachher: graph.nodes > vorher
   
9. test_run_consecutive_unique_outputs
   Input:  run("a"), run("b"), run("c")
   Erwartet: Alle 3 haben unterschiedliche memory_id
```

### Tests — Edge Cases

```
10. test_run_empty_string
    Input:  ""
    Erwartet: Kein Crash, success=False oder success=True
    
11. test_run_very_long_string
    Input:  "a" * 10000
    Erwartet: Kein Crash, keine Memory-Überlastung
    
12. test_run_special_characters
    Input:  "!@#$%^&*()_+\n\t\\"
    Erwartet: Kein Crash
    
13. test_run_unicode
    Input:  "Hällo Wörld 中文日本語"
    Erwartet: Kein UnicodeEncodeError
```

### Tests — Error Paths

```
14. test_run_mkc_failure
    Mock: mkc.compile() raised ValueError
    Erwartet: result.success=False, errors enthält Fehler
    
15. test_run_bridge_validation_failure
    Mock: bridge.validate() returns invalid
    Erwartet: result.success=False, result.errors == validation.errors
    Graph: Keine EXECUTION_PLAN-Nodes (oder nur plan_id mit invalid-Status)
    Memory: snapshot geschrieben mit error-Status
    
16. test_run_mel_execution_failure
    Mock: einzelner Tool-Call schlägt fehl
    Erwartet: result.success=False, execution enthält Fehlereintrag
```

### Kontrakt: `MuscalKernel` Event Wiring

```
17. test_event_wiring_all_events_trigger_sphere
    Emissions: Jedes Graph-Event (NODE_CREATED, NODE_UPDATED, ...)
    Erwartet: sphere.sync() wird für jedes Event aufgerufen
    (Kaskadierung durch on_action_event einberechnen)

18. test_event_wiring_system_actions_routed_to_handler
    Emission: SYSTEM_ACTION_STARTED
    Erwartet: system.on_action_event() wird aufgerufen
    
    Emission: EXECUTION_STARTED (kein System-Action)
    Erwartet: system.on_action_event() wird NICHT aufgerufen
```

---

## Layer 2: MKC — `test_mkc.py`

### Kontrakt: `mkc(text, raw_input=None) → dict`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | `text: str` (angereichert), optional `raw_input: str` |
| **Output** | `dict` mit Keys: `decisions: list`, `tasks: list`, `architecture: list`, `constraints: list`, `open_questions: list` |
| **Validierung** | `validate_mcxf(output)` muss `(True, [])` zurückgeben |
| **Determinismus** | Gleicher Input → identisches MCXF-Dict |
| **Abhängigkeit** | `mkc_rules.py` (SIGNAL_RULES) |

### Tests

```
1. test_mkc_returns_valid_structure
   Input:  "hello"
   Output: Hat alle 5 MCXF-Keys
   
2. test_mkc_output_passes_validation
   Input:  "print test"
   Output: validate_mcxf(result) == (True, [])
   
3. test_mkc_classifies_known_signals
   Input:  "write file.txt"
   Erwartet: tasks[0].predicate enthält "write" oder "file"
   
4. test_mkc_empty_input
   Input:  ""
   Erwartet: Kein Crash, gültiges MCXF
   
5. test_mkc_very_long_input
   Input:  "a" * 10000
   Erwartet: Kein Crash, gültiges MCXF
   
6. test_mkc_raw_input_used
   Input:  text="enriched: hello", raw_input="hello"
   Erwartet: raw_input taucht im Output auf
```

### Kontrakt: `mkc_rules.apply_feedback(report)`

```
7. test_apply_feedback_adjusts_confidence
   Input:  FeedbackReport mit confidence_adjustments
   Erwartet: SIGNAL_RULES-Konfidenzwerte wurden angepasst
   
8. test_apply_feedback_empty_report
   Input:  FeedbackReport()
   Erwartet: Keine Änderung an SIGNAL_RULES
```

---

## Layer 3: Bridge — `test_bridge.py`

### Kontrakt: `map_tasks(triples, intent="") → ExecutionPlan`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | `List[KnowledgeTriple]`, optional `intent: str` |
| **Output** | `ExecutionPlan(intent, steps: List[Dict])` |
| **Validierung** | `validate_plan(plan) → ValidationResult` |
| **Determinismus** | Gleiche Triples → identischer Plan |
| **Abhängigkeit** | `tools.py` (TOOL_REGISTRY, TOOL_SCHEMAS) |

### Tests

```
1. test_map_tasks_empty_list
   Input:  []
   Erwartet: ExecutionPlan mit 0 steps, validate(plan).valid == False
   
2. test_map_tasks_known_tool
   Input:  [KnowledgeTriple(subject="system", predicate="write", object="file.txt")]
   Erwartet: steps[0].tool == "filesystem.write"
   
3. test_map_tasks_unmapped_tool
   Input:  [KnowledgeTriple(subject="system", predicate="fly", object="moon")]
   Erwartet: steps[0].tool == "UNMAPPED" oder validate(plan).valid == False
   
4. test_map_tasks_multiple_tools
   Input:  3 verschiedene Tool-Triples
   Erwartet: len(steps) == 3
   
5. test_map_tasks_intent_preserved
   Input:  triples=[...], intent="my intent"
   Erwartet: plan.intent == "my intent"
   
6. test_validate_plan_valid
   Input:  ExecutionPlan mit validen Tool-Schritten
   Erwartet: validation.valid == True
   
7. test_validate_plan_invalid
   Input:  ExecutionPlan mit unmapped Tools
   Erwartet: validation.valid == False, validation.errors != []
```

---

## Layer 4: MEL — `test_mel.py`

### Kontrakt: `execute(plan) → List[Dict]`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | `ExecutionPlan` oder `OptimizedPlan` |
| **Output** | `List[Dict]` — je ein Dict pro Schritt mit `tool`, `args`, `result`/`error` |
| **Determinismus** | Gleicher Plan → gleiche Tool-Ausführungsreihenfolge |
| **Abhängigkeit** | `tools.py` (TOOL_REGISTRY), `system_runtime.py` |

### Tests

```
1. test_execute_empty_plan
   Input:  ExecutionPlan(intent="", steps=[])
   Erwartet: [] (leere Liste)
   
2. test_execute_known_tool
   Input:  Plan mit einem "console.print"-Schritt
   Erwartet: result[0].tool == "console.print"
   
3. test_execute_tool_with_args
   Input:  Plan mit "filesystem.write", args={"path": "/tmp/test.txt", "content": "hello"}
   Erwartet: result[0]["status"] != "failed" (tatsächlicher Erfolg hängt von FS ab)
   
4. test_execute_unknown_tool
   Input:  Plan mit tool="nonexistent.tool"
   Erwartet: result[0].get("tool") existiert, kein Crash
   
5. test_execute_side_effects_isolated
   Input:  Plan
   Erwartet: Keine unerwarteten Seiteneffekte außerhalb der Tool-Definition
```

---

## Layer 5: Memory — `test_memory.py`

### Kontrakt: `store_snapshot(input, mcxf, result, feedback) → int`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | Input-String, MCXFDocument, Execution-Result, optional Feedback |
| **Output** | `int` (memory_id) |
| **Nebenwirkung** | SQLite-INSERT + JSONL-Append |
| **Determinismus** | Gleicher Input → unterschiedliche ID (AUTOINCREMENT), aber gleicher Inhalt |
| **Bound** | MAX_MEMORY_ENTRIES = 10000 |

### Kontrakt: `retrieve(query, top_k=3) → List[Dict]`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | Query-String, optional top_k |
| **Output** | Liste von Dicts mit memory-Einträgen |
| **Determinismus** | Gleicher DB-Zustand → gleiche Ergebnisse |

### Tests

```
1. test_store_and_retrieve
   Actions: store("hello", mcxf, result), dann retrieve("hello")
   Erwartet: retrieve-Ergebnisse enthalten den gespeicherten Eintrag
   
2. test_store_returns_int
   Input:  "test", mcxf, result
   Erwartet: type(memory_id) == int
   
3. test_store_consecutive_ids
   Actions: store 2x
   Erwartet: id2 > id1
   
4. test_retrieve_empty_db
   Input:  retrieve("anything")
   Erwartet: [] (leere Liste, kein Crash)
   
5. test_retrieve_top_k
   Actions: store 5 Einträge mit ähnlichem Inhalt
   Input:  retrieve("similar", top_k=3)
   Erwartet: len(results) <= 3
   
6. test_prune_at_limit
   Setup: MAX_MEMORY_ENTRIES auf 5 setzen
   Actions: store 7 Einträge
   Erwartet: DB enthält höchstens 5 Einträge
   
7. test_log_jsonl
   Actions: log_jsonl({"test": "data"})
   Erwartet: JSONL-Datei existiert, enthält gültiges JSON
```

---

## Layer 6: Graph — `test_graph.py`

### Kontrakt: `GraphState.add_node(type, payload) → int`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | Node-Type (String), Payload (Dict) |
| **Output** | `int` (node_id) |
| **Nebenwirkung** | Node zu `.nodes` hinzugefügt, Event `NODE_CREATED` emittiert |
| **Bound** | MAX_NODES = 5000 |

### Kontrakt: `GraphState.add_edge(source, target, type)`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | source_id, target_id, edge_type |
| **Nebenwirkung** | Edge zu `.edges` hinzugefügt, Event `EDGE_CREATED` emittiert |
| **Bound** | MAX_EDGES = 10000 |

### Tests

```
1. test_add_node
   Input:  add_node("INTENT", {"text": "hello"})
   Erwartet: node_id >= 0, nodes[id].type == "INTENT"
   
2. test_add_node_emits_event
   Mock: graph.on("NODE_CREATED", handler)
   Input:  add_node("TEST", {})
   Erwartet: handler wurde aufgerufen
   
3. test_add_edge
   Setup: 2 Nodes
   Input:  add_edge(id1, id2, "DERIVES_FROM")
   Erwartet: edges[-1] == {"from": id1, "to": id2, "type": "DERIVES_FROM"}
   
4. test_add_edge_emits_event
   Mock: graph.on("EDGE_CREATED", handler)
   Input:  add_edge(id1, id2, "TEST")
   Erwartet: handler wurde aufgerufen
   
5. test_prune_nodes
   Setup: MAX_NODES=3, add 5 Nodes
   Erwartet: len(nodes) == 3, älteste Nodes wurden entfernt
   
6. test_prune_edges
   Setup: MAX_EDGES=3, add 5 Edges
   Erwartet: len(edges) == 3, älteste Edges wurden entfernt
   
7. test_set_focus
   Input:  set_focus(node_id)
   Erwartet: graph.focus == node_id
   
8. test_snapshot
   Input:  snapshot()
   Erwartet: Dict mit nodes, edges, focus
```

---

## Layer 7: EventBus — `test_events.py` (shared)

### Kontrakt: `EventBus.publish(topic, payload, source, priority)`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | topic (String), payload (Any), optional source/priority |
| **Nebenwirkung** | An Subscriber dispatchen, in History speichern |
| **Bound** | MAX_HISTORY = 50000 |

### Tests

```
1. test_publish_subscribe
   Mock: handler
   Actions: subscribe("test", handler), publish("test", {"data": 1})
   Erwartet: handler({"data": 1}) wurde aufgerufen
   
2. test_publish_no_subscriber
   Input:  publish("nonexistent", {})
   Erwartet: Kein Fehler
   
3. test_unsubscribe
   Mock: handler
   Actions: subscribe("test", handler), unsubscribe("test", handler), publish("test", {})
   Erwartet: handler wurde NICHT aufgerufen
   
4. test_history_limit
   Setup: MAX_HISTORY=3
   Actions: publish 5 events
   Erwartet: len(history) == 3, älteste Events wurden verworfen
   
5. test_multiple_subscribers
   Mocks: handler1, handler2
   Actions: subscribe("test", h1), subscribe("test", h2), publish("test", {})
   Erwartet: h1 und h2 wurden beide aufgerufen
```

---

## Layer 8: Optimizer Pipeline — `test_optimizer_pipeline.py`

### Kontrakt: `OptimizerPipeline.optimize(plan) → (OptimizedPlan, OptimizationReport)`

| Aspekt | Erwartung |
|--------|-----------|
| **Input** | `ExecutionPlan` |
| **Output** | `OptimizedPlan` mit Layern, `OptimizationReport` mit Dauer/Verbesserung |
| **Determinismus** | Gleicher Plan → gleiche Optimierung |
| **Abhängigkeit** | `runtime/optimizer/` — DCE, Fusion, Parallelization, Cost, Verification |

### Tests

```
1. test_optimize_empty_plan
   Input:  ExecutionPlan(intent="", steps=[])
   Erwartet: OptimizedPlan mit 0 Layern
   
2. test_optimize_single_step
   Input:  Plan mit 1 Tool
   Erwartet: min_layers >= 1, keine DCE/Optimierung nötig
   
3. test_optimize_dead_code_elimination
   Input:  Plan mit 3 Schritten, davon 1 unmappbar
   Erwartet: report.nodes_before > report.nodes_after
   
4. test_optimize_parallelization
   Input:  Plan mit 2 unabhängigen Tools
   Erwartet: optimized_plan.layers >= 1 (Parallelisierung möglich)
   
5. test_optimize_verification
   Input:  Beliebiger Plan
   Erwartet: report.verification["passed"] == True/False (nie Crash)
```

---

## Layer 9: API — `test_api_boot.py`

### Kontrakt: API-Endpunkte

| Endpunkt | Methode | Erwartung |
|----------|---------|-----------|
| `/api/health` | GET | `{"status": "ok"}` |
| `/api/state` | GET | Aktueller System-Status |
| `/api/chat` | POST | Antwort auf Input |

### Tests

```
1. test_health_endpoint
   Erwartet: HTTP 200, JSON mit status=ok
   
2. test_state_endpoint
   Erwartet: HTTP 200, JSON mit running/mode/uptime
   
3. test_chat_endpoint
   Input:  POST {"input": "hello"}
   Erwartet: HTTP 200, JSON mit response/status
   
4. test_404_endpoint
   Input:  GET /nonexistent
   Erwartet: HTTP 404
```

---

## Test-Runner Script

`run_tests.sh` — Ein Befehl für alle Tests:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== MUSCAL Critical Path Tests ==="
echo ""

# Legacy tests
echo "--- Legacy Plugin Tests ---"
python3 tests/test_plugin_loading.py
python3 tests/test_plugin_health.py
python3 tests/test_plugin_audit.py
python3 tests/test_plugin_confidence.py
python3 tests/stress_test.py

echo ""
echo "--- Pytest Suite ---"
python3 -m pytest tests/ -v --tb=short

echo ""
echo "=== ALL TESTS PASSED ==="
```

---

## Coverage Targets

| Phase | Ziel | Metrik |
|-------|------|--------|
| v0.8 | Critical Path | Alle Tests in dieser Spezifikation implementiert |
| v0.9 | Core Coverage | Kernel + MKC + Bridge + MEL + Memory + Graph: >70% |
| v0.10 | Full Coverage | Gesamte Codebase (exkl. Stubs): >60% |

---

## Test-Implementierungs-Reihenfolge

```
Priority 1 (sofort)
├── test_graph.py           # Fundament, keine Dependencies
├── test_boot.py            # Kernel-Erzeugung
└── test_state_transition.py # Kernel.run() Happy Path

Priority 2 (nach P1)
├── test_events.py          # EventBus + Graph-Events
├── test_mkc.py             # MKC-Compiler
└── test_bridge.py          # Bridge-Mapping

Priority 3 (nach P2)
├── test_mel.py             # Tool-Execution
├── test_memory.py          # Persistence
└── test_optimizer_pipeline.py

Priority 4 (nach P3)
├── test_api_boot.py        # API-Smoke
└── test_mkc_edge_cases.py  # MKC-Grenzfälle
```
