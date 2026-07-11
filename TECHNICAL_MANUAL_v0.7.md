# MUSCAL CORE — Technisches Handbuch

**Version:** 0.7 (Juli 2026)
**Projektordner:** `/home/hz/AlitaProject/Codebase/MUSCAL CORE/`
**Sprache:** Python 3.12+
**Gesamtumfang:** ~184 Python-Dateien, ~10.744 Zeilen Code, ~225 Dateien gesamt
**Status:** Stable Prototype (Kernpipeline funktionsfähig, Graph/Memory gebounded)

---

## 1. PROJEKTÜBERSICHT

### 1.1 Was ist MUSCAL CORE?

MUSCAL CORE (Multi-Scale Context-Aware Learning) ist ein **kognitives Betriebssystem** — keine Bibliothek, kein Framework. Es orchestriert AI-Agents, führt Tasks aus, kompiliert natürliche Sprache in ausführbare Pläne und überwacht sich selbst durch einen mehrschichtigen Observability-Stack.

Anders als herkömmliche AI-Frameworks (LangChain, AutoGen, CrewAI) ist MUSCAL CORE als **eigenständiges System** konzipiert: Es hat einen Kernel, ein OS-Layer, Compiler, Optimierer, API-Server und Frontend — alles in einer Codebasis.

### 1.2 Entstehung

MUSCAL CORE wurde aus Code mehrerer AI-Modelle (Claude, ChatGPT, Mimo, Kimi, Minimax) in einer einzigartigen Symbiose entwickelt. Es vereint:
- **Compiler**-Architektur (MKC → Bridge → MEL)
- **OS**-Lifecycle (Boot → Health → Shutdown)
- **Optimizer** mit LLVM-artigen Passes
- **CQRS**-Datenhaltung (Command Query Responsibility Segregation)
- **Governance** mit Token/Iterations-Limits

### 1.3 Kern-Prinzipien

| Prinzip | Beschreibung |
|---------|-------------|
| **Determinismus** | L1-Routing ist regelbasiert, kein LLM, <1µs |
| **Single Writer** | Nur ein Thread schreibt in die DB (CQRS) |
| **Safety First** | Jeder LLM-Input wird auf Injection geprüft |
| **Layer-Trennung** | Jede Schicht hat genau eine Verantwortung |
| **Replayability** | Jeder Task ist deterministisch wiederholbar |
| **Bounded Growth** | Graph (5000 Nodes), Memory (10000 Einträge), Events (50000) |

---

## 2. ARCHITEKTUR (7 Schichten)

### 2.1 Schichtenmodell

```
                    ┌─────────────────────────────────────┐
  L7 FRONTEND       │  React JSX (Dashboard, GraphView)   │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L6 API LAYER      │  Flask API (:5050)                  │
                    │  FastAPI  (:8080)                    │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L5 OS LAYER       │  BootManager, EventBus,             │
                    │  Deployment-Modi, Graceful Shutdown │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L4 COMPILER       │  MKC (MCXF), Bridge (Tool-Match),  │
                    │  Optimizer (DCE/Fusion/Parallel),   │
                    │  Feedback, CognitiveDiff            │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L3 EXECUTION      │  MEL (Tool-Dispatch),               │
                    │  Browser Engine, Desktop Tools      │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L2 KERNEL         │  WriterThread (CQRS), Scheduler,    │
                    │  Gate, Governance, Sanitizer,       │
                    │  RAG Index, ChromaDB                │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
  L1 STORAGE        │  SQLite (WAL, CQRS, 12 Tabellen),   │
                    │  JSONL Logs, FAISS, ChromaDB,       │
                    │  MCXF Memory Store                   │
                     └─────────────────────────────────────┘
```

### 2.2 Pipeline (aktuelle Implementierung v0.7)

```
User Input (Text)
    │
    ▼
┌─────────────────────────────┐
│ RAG Context Retrieval       │ ← memory.get_recent(5)
│ + RAG Enrich                │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ MKC Compile                 │ ← mkc.py + mkc_rules.py
│ Text → MCXF {decisions,     │
│   tasks, architecture,      │
│   constraints, glossary}    │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Bridge (Tool Matching)      │ ← bridge.py
│ 9 Regex-Matcher: NL → Tool  │
│ filesystem.write, browser.*,│
│ math.add, console.print     │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Optimizer Pipeline          │ ← runtime/optimizer/
│ DCE → Fusion → Parallel    │
│ + CostModel + Verification  │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ MEL Execute                 │ ← mel.py + tools.py
│ TOOL_REGISTRY Dispatch      │
│ oder SystemAgentRuntime     │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Feedback Analysis           │ ← feedback.py
│ Confidence Adjustments      │
│ UNMAPPED_TOOL / WRONG_ARG   │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ Memory Store                │ ← memory.py
│ SQLite + JSONL + Graph      │
│ + Pruning (MAX_MEMORY_ENTRIES=10000) │
└──────────┬──────────────────┘
           ▼
      KernelResult
```

### 2.3 OS Boot-Lifecycle

```
[1] INIT ──────────────────► Config laden, Pfade setzen
[2] LOAD_CONFIG ───────────► os_config.py: deployment mode
[3] INIT_MODULES ──────────► MKC, Bridge, MEL (lazy), Feedback, Memory (lazy)
[4] START_SERVICES ────────► EventBus (max 50000 Events), Scheduler, WriterThread
[5] HEALTH_CHECK ──────────► Ollama ping, DB integrity
[6] READY ◄────────────────► Normalbetrieb
       │
       ├── SIGINT/SIGTERM ──► SHUTDOWN → Snapshot → Exit
       └── FAILED ──────────► ERROR → Snapshot → Exit
```

---

## 3. STABILISIERUNG (NEU in v0.7)

### 3.1 Patch Set 1 — Import-Stabilität

Alle module-level Import-Seiteneffekte wurden durch Lazy-Init ersetzt:

| Datei | Vorher | Nachher |
|-------|--------|---------|
| `memory.py` | `conn = sqlite3.connect(...)` bei Import | `_get_conn()` erstellt DB lazy + `os.makedirs("storage")` |
| `mel.py` | `_runtime = SystemAgentRuntime()` bei Import | `_get_runtime()` initialisiert Runtime lazy |
| `config.py` | `SESSION_ID = datetime.now(...)` bei Import | `get_session_id()` generiert ID lazy |
| `mkc_rules.py` | Globaler State ohne Reset | `reset_state()` + `DEFAULT_KEYWORDS` |

### 3.2 Patch Set 2 — Graph + Memory Bounding

| Limit | Datei | Wert | Verhalten |
|-------|-------|------|-----------|
| **MAX_NODES** | `graph.py` | 5000 | FIFO-Eviction alter Nodes |
| **MAX_EDGES** | `graph.py` | 10000 | FIFO-Eviction alter Edges |
| **MAX_MEMORY_ENTRIES** | `memory.py` | 10000 | SQLite DELETE nach jedem `store_snapshot()` |
| **Event History** | `event_bus.py` | 50000 | FIFO-Pop in `publish()` |
| **Kernel Safety Guard** | `kernel.py` | 10000 | Auto-Prune wenn Graph > 10000 Nodes |

### 3.3 Verifikation

Alle Patch-Sets wurden getestet:

```
# Import Chain (3 Tests)
python -c "from memory import init"              → PASS
python -c "from mel import execute"              → PASS
python -c "from config import get_session_id"    → PASS

# Pruning Validation
python -c "from graph import GraphState; ..."    → 5100→5000 Nodes: PASS

# Stress Test (100 Iterationen)
0 Crashes, 0 Failures, deterministisch: SAME    → PASS
```

---

## 4. KERNMODULE IM DETAIL

### 4.1 `kernel.py` — Hauptorchestrator (417 Zeilen)

**Klasse:** `MuscalKernel`

```python
class MuscalKernel:
    def __init__(self, enable_graph=True, enable_sphere=True, debugger=None):
        self.mkc = MKCModule()
        self.mel = MELModule()
        self.bridge = BridgeModule()
        self.feedback = FeedbackModule()
        self.memory = MemoryModule()
        self.rag = RAGModule()
        self.graph = GraphState() if enable_graph else None
        self.sphere = SphereState(self.graph) if enable_sphere else None
        self.system = SystemModule(graph=self.graph)
        self.debugger = debugger
        self.memory.init()

    def run(self, input_text: str) -> KernelResult:
        # Safety guard: auto-prune if graph > 10000 nodes
        if self.graph and len(self.graph.nodes) > 10000:
            self.graph.prune_graph()
        # 1. RAG
        # 2. MKC compile
        # 3. Bridge: MCXF → ExecutionPlan
        # 4. Optimizer Pipeline
        # 5. MEL execute
        # 6. Feedback
        # 7. Memory store + auto-prune
        return KernelResult(...)
```

### 4.2 `memory.py` — Lazy Inti + Bounded Storage (139 Zeilen)

```python
_conn = None
MAX_MEMORY_ENTRIES = 10000

def _get_conn():
    global _conn
    if _conn is None:
        os.makedirs("storage", exist_ok=True)
        _conn = sqlite3.connect("storage/memory.db")
    return _conn

def _prune_memory():
    c = _get_conn()
    c.execute("DELETE FROM mcxf_store WHERE id NOT IN (SELECT id FROM mcxf_store ORDER BY id DESC LIMIT ?)", (MAX_MEMORY_ENTRIES,))
    c.execute("DELETE FROM memory WHERE id NOT IN (SELECT id FROM memory ORDER BY id DESC LIMIT ?)", (MAX_MEMORY_ENTRIES,))
    c.commit()
```

### 4.3 `graph.py` — Bounded GraphState (219 Zeilen)

```python
MAX_NODES = 5000
MAX_EDGES = 10000

class GraphState:
    def add_node(self, ...):
        # ... add logic ...
        self.prune_graph()  # ← automatic pruning hook
        return node_id

    def add_edge(self, ...):
        # ... add logic ...
        self.prune_graph()  # ← automatic pruning hook

    def prune_graph(self):
        if len(self.nodes) > MAX_NODES:
            # FIFO eviction (oldest timestamp first)
            sorted_nodes = sorted(self.nodes.items(), key=lambda x: x[1].timestamp)
            for i in range(len(self.nodes) - MAX_NODES):
                self.remove_node(sorted_nodes[i][0])
        if len(self.edges) > MAX_EDGES:
            for _ in range(len(self.edges) - MAX_EDGES):
                self.edges.pop(0)
```

### 4.4 `event_bus.py` — Bounded History (74 Zeilen)

```python
class EventBus:
    def __init__(self):
        self._max_history: int = 50000
        # ...
    def publish(self, topic, ...):
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history.pop(0)
```

---

## 5. RESSOURCEN-GRENZEN (Übersicht)

| Ressource | Max | Datei | Eviction |
|-----------|-----|-------|----------|
| Graph Nodes | 5000 | `graph.py` | FIFO (ältester Timestamp zuerst) |
| Graph Edges | 10000 | `graph.py` | FIFO (erste in Liste) |
| Memory DB (mcxf_store) | 10000 Zeilen | `memory.py` | ORDER BY id DESC LIMIT |
| Memory DB (memory) | 10000 Zeilen | `memory.py` | ORDER BY id DESC LIMIT |
| Event History | 50000 | `event_bus.py` | POP(0) bei Überlauf |
| Kernel Safety Guard | 10000 Nodes | `kernel.py` | Auto-Prune in `run()` |
| SIGNAL_RULES Adjustment | -0.3 bis +0.1 | `mkc_rules.py` | Hard-Clamped |
| Keyword Additions | max 5 | `mkc_rules.py` | Hard-Capped |

---

## 6. EINSTIEGSPUNKTE

| Befehl | Beschreibung |
|--------|-------------|
| `pip install -r requirements.txt` | **Installation** (einmalig) |
| `python3 main.py` | Einfacher REPL-Modus |
| `python3 main_boot.py` | **Haupt-Einstieg**: OS-Modus mit CLI |
| `python3 muscal_loop.py` | Autonomer LLM-Loop |
| `python3 runtime/main.py` | Flask API Server (:5050) |
| `python3 api_server.py` | FastAPI Control Plane (:8080) |
| `python3 dashboard.py` | Streamlit Dashboard (:8501) |
| `docker compose up` | Containerisiert |

---

## 7. ABHÄNGIGKEITEN (NEU in v0.7)

### `requirements.txt` (vollständig):

```
fastapi>=0.100.0
uvicorn>=0.23.0
websockets>=11.0
flask>=3.0.0
flask-cors>=4.0.0
requests>=2.31.0
numpy>=1.24.0
chromadb>=0.4.0
playwright>=1.40.0
pyautogui>=0.9.54
streamlit>=1.28.0
```

---

## 8. BEKANNTE PROBLEME

### Kritisch (v0.7)

| # | Problem | Dateien | Status |
|---|---------|---------|--------|
| 1 | **Keine Tests** (0 Test-Dateien) | Alle | ❌ Ungelöst |
| 2 | **~45% Stubs** (~80 Dateien <20 Zeilen) | Consensus, Distributed, Evolution | ❌ Ungelöst |
| 3 | **SIGNAL_RULES Drift** — Confidence-Werte mutieren | `mkc_rules.py` | ⚠️ `reset_state()` vorhanden, kein Auto-Reset |
| 4 | **FIFO Pruning** — Keine semantische Selektion | `graph.py` | ⚠️ Älteste Nodes werden entfernt, nicht unwichtigste |
| 5 | **Keine DB-Migrationen** | `runtime/database.py` | ❌ Ungelöst |
| 6 | **Keine CI/CD** | — | ❌ Ungelöst |

---

## 9. CHANGELOG (v0.6 → v0.7)

| Änderung | Datei | Typ |
|----------|-------|-----|
| Lazy Database Connection | `memory.py` | Bugfix |
| Lazy Runtime Initialization | `mel.py` | Bugfix |
| Lazy SESSION_ID | `config.py` | Bugfix |
| Graph Bounding (5000/10000) | `graph.py` | Feature |
| Memory Bounding (10000) | `memory.py` | Feature |
| Event Bus Limit (50000) | `event_bus.py` | Feature |
| Reset State Funktion | `mkc_rules.py` | Feature |
| Safe Entrypoint | `main.py` | Bugfix |
| Vollständige requirements.txt | `requirements.txt` | Bugfix |
| Dockerfile Fix | `Dockerfile` | Bugfix |
| Stress Test Suite | `tests/stress_test.py` | Neu |
| Dokumentation v0.7 | `TECHNICAL_MANUAL_v0.7.md` | Neu |
