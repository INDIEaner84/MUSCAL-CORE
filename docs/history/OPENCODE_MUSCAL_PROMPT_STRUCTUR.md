# MUSCAL Architecture Decision Record (ADR-001)
## Optimizer Integration & Production Hardening

MISSION

Du bist Senior Compiler Engineer des MUSCAL Core Teams.

MUSCAL befindet sich im Foundation Freeze.

Neue Kernarchitektur darf NICHT entwickelt werden.

Deine Aufgabe ist ausschließlich:

- Hardening
- Verifikation
- Determinismus
- Compilerqualität
- Produktionsreife

Alle Änderungen müssen mit dem bestehenden MCXF-Contract, MEL Runtime und Replay-System kompatibel bleiben.

--------------------------------------------------
ARCHITEKTUR ENTSCHEIDUNGEN (VERBINDLICH)
--------------------------------------------------

## 1. Optimizer Position

Der Graph Optimizer ist ausschließlich Bestandteil der Compiler-Pipeline.

NICHT Bestandteil von:

- Autonomous Loop
- Runtime
- Replay
- GUI

Pipeline:

UIC
↓

MCXF
↓

Graph Compiler
↓

Graph Optimizer
↓

Frozen Execution Graph
↓

MEL Runtime
↓

Replay

Der Optimizer darf niemals während der Ausführung den Graph verändern.

--------------------------------------------------

## 2. Parallelization Pass

Die aktuelle Implementierung

depth = node["id"] % 3

ist nur ein Platzhalter.

Ersetze sie vollständig.

Verwende:

- echte Topological Sort
- Layer Assignment
- DAG Analyse

Beispiel

A

↓

B     C

↓

D

Layer

0:
A

1:
B
C

2:
D

Diese Layer dienen zunächst ausschließlich der logischen Gruppierung.

Keine Threads.

Keine Async-Ausführung.

--------------------------------------------------

## 3. Cost Model

Ersetze den bisherigen Cost-Wert durch einen CostVector.

Beispiel:

class CostVector:

    cpu

    ram

    latency

    tokens

    retries

    estimated_cost

    risk

    tool_calls

    graph_complexity

Der Optimizer minimiert künftig diesen Vektor.

Nicht nur eine einzelne Zahl.

--------------------------------------------------

## 4. MEL Runtime

MEL führt Parallel-Layer zunächst NICHT parallel aus.

Aktuelle Version:

Layer 0

↓

Layer 1

↓

Layer 2

Nur logische Gruppierung.

ThreadPool, asyncio oder Distributed Execution werden NICHT implementiert.

Diese Erweiterung ist erst nach vollständig validiertem Replay erlaubt.

--------------------------------------------------

## 5. Optimizer Contract

Jeder Optimizer Pass implementiert exakt dieselbe Schnittstelle.

class OptimizationPass:

    optimize(graph)

    verify(before_graph, after_graph)

    metadata()

verify()

muss sicherstellen:

- gleiche Semantik

- gültiger DAG

- keine verlorenen Nodes

- keine verlorenen Dependencies

metadata()

liefert:

Name

Version

Kosten

Optimierungsgewinn

--------------------------------------------------

## 6. Optimizer Pipeline

Erzeuge folgende Struktur:

optimizer/

    pipeline.py

    base_pass.py

    dead_node.py

    node_fusion.py

    parallelization.py

    cost_optimizer.py

    verification.py

pipeline.py lädt alle Pässe automatisch.

Jeder Pass ist unabhängig testbar.

--------------------------------------------------

## 7. Optimization Report

Nach jedem Compile wird automatisch erzeugt:

Optimization Report

- Removed Nodes

- Node Fusion Count

- Parallel Layers

- Estimated Cost Reduction

- Graph Hash Before

- Graph Hash After

- Replay Compatible

- Determinism PASS/FAIL

Dieser Report wird später vom GUI verwendet.

--------------------------------------------------

## 8. Graph Hash

Vor jedem Pass:

SHA256(Graph)

Nach jedem Pass:

SHA256(Graph)

Wenn verify() fehlschlägt:

CI FAIL

--------------------------------------------------

## 9. Teststrategie

Implementiere folgende Testebenen.

LEVEL 1

Unit Tests

für jeden Optimizer Pass

--------------------------------------------------

LEVEL 2

Compiler Tests

MCXF

↓

Graph

↓

Optimizer

↓

Graph

--------------------------------------------------

LEVEL 3

Replay Tests

Original

↓

Replay

↓

identisches Ergebnis

--------------------------------------------------

LEVEL 4

Golden Dataset

Mindestens:

- Arztpraxis digitalisieren

- Software Architektur

- Hauskauf Analyse

- Rechtsfall Analyse

- Enterprise Planung

--------------------------------------------------

LEVEL 5

Property-Based Tests

Erzeuge zufällige DAGs.

Für jede DAG gilt:

Optimize()

↓

Replay()

↓

Semantik identisch

↓

Determinismus identisch

Nutze geeignete Bibliotheken (z. B. Hypothesis), sofern sinnvoll.

--------------------------------------------------

## 10. CI/CD

Die Pipeline muss automatisch prüfen:

MCXF Validation

↓

Graph Compile

↓

Optimizer

↓

Verification

↓

Replay

↓

Golden Dataset

↓

Property Tests

↓

Benchmark

↓

PASS

--------------------------------------------------

## 11. Code Quality

Alle Module müssen:

- vollständig typisiert sein (typing)

- dataclasses oder pydantic verwenden, wo sinnvoll

- docstrings besitzen

- reproduzierbar sein

- deterministisch arbeiten

Keine globalen Zustände.

Keine versteckten Side Effects.

--------------------------------------------------

## 12. WICHTIGSTE REGEL

Der Optimizer darf niemals:

- die Semantik verändern

- Replay zerstören

- Determinismus reduzieren

- den Runtime-Graph verändern

Compiler optimiert.

Runtime führt aus.

Diese Trennung ist strikt einzuhalten.
