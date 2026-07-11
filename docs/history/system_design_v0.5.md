# MUSCAL CORE — System Design Document (SDD)

**IEEE 1016-2009 konform**
**Version:** 0.5 (Juli 2026)
**Umfang:** ~30 Seiten, kein Quellcode

---

## 1. System Overview

### 1.1 System Identification

MUSCAL CORE ist ein kognitives Betriebssystem zur Orchestrierung von AI-Agents, Task-Ausführung und Selbstüberwachung. Es besteht aus ~184 Python-Dateien (~10.744 Zeilen), 7 React-JSX-Dateien und API-Servern in Flask und FastAPI.

### 1.2 System Context

Das System operiert in drei Umgebungen:
- **local_dev**: Entwicklung (Ollama optional)
- **production**: Produktion (Ollama erforderlich, Safety-Checks aktiv)
- **simulation**: Test (keine echten Agents, keine Persistenz)

## 2. Architectural Goals & Constraints

### 2.1 Goals

1. **Determinismus**: Gleicher Input → gleicher Output (bitgenau)
2. **Austauschbarkeit**: Jede Komponente ist hot-swappable
3. **Sicherheit**: Capability-basiertes Permission-Modell
4. **Beobachtbarkeit**: Jede Execution ist traceable + replayable

### 2.2 Constraints

- **Kein LLM in L1 Runtime** (L1 ist hart deterministisch)
- **Kein Schreiben aus L4 Observability** (read-only)
- **CQRS**: Nur der WriterThread schreibt in die DB
- **Event Ownership**: Jedes Event hat genau einen Origin- und einen Target-Layer

## 3. Component Decomposition

### 3.1 L1 Runtime Kernel

| Komponente | Schnittstellen | Abhängigkeiten |
|-----------|---------------|----------------|
| WriterThread | write(table, data) → Future | SQLite |
| Scheduler | route(task_type) → worker_id | Routing Policy |
| Gate | check(task_type, payload) → GateResult | Governance, Scheduler |
| Sanitizer | sanitize(input) → sanitized_input | — |
| MEL | execute(plan) → results | TOOL_REGISTRY |
| Browser Engine | open/click/type/scroll | Playwright |
| Desktop Tools | type/click/screenshot | PyAutoGUI |

### 3.2 L2 Cognitive Kernel

| Komponente | Schnittstellen | Abhängigkeiten |
|-----------|---------------|----------------|
| MKC | compile(text) → MCXF | mkc_rules |
| Bridge | match_tool(triple) → ToolMatch | 9 Regex-Matcher |
| Optimizer Pipeline | optimize(dag) → dag | DCE, Fusion, Parallel |
| Feedback | analyze(results) → feedback | — |
| RAG Index | search(query, top_k) → docs | Ollama Embedding |
| Chroma Index | search(query, top_k) → docs | ChromaDB |

### 3.3 L3 Control Kernel

| Komponente | Schnittstellen | Abhängigkeiten |
|-----------|---------------|----------------|
| Governance | check_limits() → bool, record_usage() | — |
| Cognitive Diff | diff(state_a, state_b) → 5D-Report | — |
| Permission Engine | check(tool, context) → bool | — |
| Consensus Engine | decide(options) → winner | — |

### 3.4 L4 Observability Kernel

| Komponente | Schnittstellen | Abhängigkeiten |
|-----------|---------------|----------------|
| EventBus | emit(event), subscribe(type, handler) | — |
| Observation Loop | tick() → observations | Gate, Workers, Governance |
| Trace Engine | log(event), get_trace(id) → trace | JSONL |
| Debugger | metrics() → DebugMetrics | Alle Subsysteme |
| GraphState | record(mcxf, plan, results) | — |

## 4. Data Design

### 4.1 Zentrale Datenmodelle

**KernelResult** — Pipeline-Output:
```json
{
  "mcxf": {"decisions": [], "tasks": [], "architecture": ""},
  "plan": {},
  "results": [],
  "feedback": {},
  "memory_id": 0
}
```

**Event** — System-Event:
```json
{
  "event_id": "uuid",
  "type": "task.submitted",
  "payload": {},
  "timestamp": "ISO-8601",
  "priority": 0
}
```

### 4.2 SQLite Schema (12 Tabellen)

| Tabelle | Zweck | Einträge (ca.) |
|---------|-------|----------------|
| events | Alle System-Events | 10.000+ |
| workers | Worker-Registry | 10–50 |
| tasks | Task-Queue | 1.000+ |
| decisions | Entscheidungen | 500+ |
| snapshots | DB-Snapshots | 10–100 |
| memory | Memory-Einträge | 5.000+ |
| governance_log | Governance-Verstöße | 100+ |

## 5. Interface Design

### 5.1 Flask API (:5050)

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | /api/state | System-Status |
| GET | /api/health | Health-Check |
| POST | /api/chat | Chat + RAG |
| GET | /api/events | Gefilterte Events |
| POST | /api/task | Task submit |
| POST | /api/fs/write | Datei schreiben |
| POST | /api/snapshot | Snapshot erstellen |

### 5.2 FastAPI (:8080)

| Methode | Pfad | Zweck |
|---------|------|-------|
| POST | /task | Swarm-Execution |
| GET | /graph | Graph-Status |
| GET | /replay/{id} | Replay-Pfad |
| WS | /stream | Heartbeat-Events |

### 5.3 Event-Interface

```json
{
  "event_id": "uuid",
  "type": "string",
  "payload": {},
  "timestamp": "ISO-8601",
  "priority": 0
}
```

## 6. Dynamic Behavior

### 6.1 Boot-Lifecycle

```
INIT → LOAD_CONFIG → INIT_MODULES → START_SERVICES → HEALTH_CHECK → READY
```

### 6.2 Task Execution Flow

```
User Input → RAG Retrieve → MKC Compile → Bridge Match → Optimizer → MEL Execute → Feedback → Memory Store
```

### 6.3 Observation Loop (5s-Tick)

Prüft: Blocking Unknowns, Stuck Workers (>5min), Confidence Drift (>0.3), Governance Violations, Ollama Health.

## 7. Layer Governance

### 7.1 Transition-Matrix

| Origin → Target | L0 | L1 | L2 | L3 | L4 |
|-----------------|----|----|----|----|----|
| L0 Storage | ✅ | ✅ | ❌ | ❌ | ⛓️ |
| L1 Runtime | ✅ | ✅ | ✅ | ✅ | ✅ |
| L2 Cognitive | ⛓️ | ✅ | ✅ | ✅ | ✅ |
| L3 Control | ⛓️ | ✅ | ✅ | ✅ | ✅ |
| L4 Observability | ✅ | ❌ | ❌ | ❌ | ✅ |

✅=ALLOWED ❌=FORBIDDEN ⛓️=NEEDS_BRIDGE

### 7.2 Determinismus-Zonen

| Zone | Layer | LLM erlaubt? | Deterministisch? |
|------|-------|-------------|-----------------|
| Hart deterministisch | L0+L1 | Nein | Ja (100%) |
| Deterministisch + LLM | L2 | Ja, gecaged | Ja (RAG fest) |
| Strategisch | L3 | Optional | Nein (probabilistisch) |
| Read-only | L4 | Nein | N/A |

## 8. Security Model

- **Capability-Gating**: Jeder Task benötigt deklarierte Capability
- **Injection-Schutz**: Sanitizer filtert LLM-Input (HTML, SQL, Shell)
- **Default Deny**: Keine impliziten Berechtigungen
- **Audit-Log**: Jeder Tool-Call wird geloggt
- **Sandbox**: Process-Isolation via Podman (Production)

## 9. MREIL Metrics

| ID | Metrik | Messmethode | Ziel |
|----|--------|------------|------|
| M01 | Memory Retention | retained_context / total_context | >0.9 |
| R01 | Reasoning Accuracy | correct_outputs / steps | >0.8 |
| E01 | Execution Latency | avg(node_duration) | <100ms |
| I01 | Integrity | deviation(reference, actual) | 0.0 |
| L01 | Load | cpu/ram/network utilization | <0.7 |

## 10. Deployment

### 10.1 Local Development

```bash
python3 main_boot.py       # OS-Modus
python3 runtime/main.py    # Flask API (:5050)
python3 api_server.py      # FastAPI (:8080)
```

### 10.2 Production (Docker)

```bash
docker compose up
```

Port 8000, Container-Isolation, Health-Checks.

### 10.3 Abhängigkeiten

| Layer | Packages | Typ |
|-------|----------|-----|
| Core | stdlib only (0 extern) | obligatorisch |
| API | fastapi, uvicorn, websockets | obligatorisch |
| Runtime | flask, flask-cors, streamlit | obligatorisch |
| Optional | playwright, pyautogui, chromadb, faiss | optional |

## 11. Known Issues

- 0 Test-Dateien (keine automatisierte Qualitätssicherung)
- ~45% Stubs (~80 Dateien <20 Zeilen)
- Global Mutable State (memory.py)
- Keine DB-Migrationen
- Kein Auth/Authorization
- Kein Rate-Limiting
- Frontend nicht buildbar (JSX ohne Bundler)

---

*Generiert 2026-07-04. Basis: TECHNICAL_MANUAL.md + MAS-RFC-Reihe (MAS-0000 bis MAS-0500).*
