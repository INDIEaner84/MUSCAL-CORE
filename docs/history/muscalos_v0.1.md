# MUSCAL CORE — Betriebsanleitung

## 1. Übersicht

MUSCAL (Multi-Scale Context-Aware Learning) ist ein LLM-gestütztes
Ausführungssystem mit Compiler-Pipeline, optimierendem Runtime-Kernel und
deterministischem Replay.

Pipeline: `Input → RAG → MKC → Bridge → Optimizer → MEL → Feedback → Memory`

## 2. Systemanforderungen

### Hardware
- **RAM:** 8 GB+ (16 GB empfohlen für Ollama + Runtime)
- **CPU:** x86_64, 4+ Kerne
- **GPU (optional):** NVIDIA mit 4 GB+ VRAM für lokale LLMs

### Software
- **Python:** 3.11+
- **Ollama:** `>=0.5` (optional aber empfohlen)
- **Docker:** `>=24` (optional)

### Python-Pakete (installiert am 03.07.2026)
```
flask>=3.0, flask-cors, fastapi>=0.138, uvicorn>=0.49
chromadb>=1.5, streamlit>=1.58, websockets, requests
```

### Ollama-Modelle
```bash
# Konfiguriert in config.py:
ollama pull qwen2.5:1.5b       # Router/Chat
ollama pull deepseek-r1:8b     # Reasoning
ollama pull smollm2:360m       # Lightweight Chat
```

## 3. Schnellstart

### Minimal (ohne Ollama, Stub-LLM)
```bash
cd /home/hz/AlitaProject/Codebase/MUSCAL\ CORE

# 1. OS-Status prüfen (Smoketest):
python main_boot.py --status

# 2. Interaktive CLI:
python main.py

# 3. Loop-Demo (deterministisch):
python muscal_loop.py
```

### Mit Ollama
```bash
ollama serve &
ollama pull qwen2.5:1.5b
ollama pull smollm2:360m

cd /home/hz/AlitaProject/Codebase/MUSCAL\ CORE

# OS-Modus mit echtem LLM:
python main_boot.py --loop --ollama

# Runtime-Server (Flask API):
python runtime/main.py
```

### Docker
```bash
cd /home/hz/AlitaProject/Codebase/MUSCAL\ CORE
docker compose up --build
# → http://localhost:8000
```

## 4. Startmodi

### 4A. `main.py` — Einfache CLI
```bash
python main.py
```
- Initialisiert `MuscalKernel` mit Graph + Sphere
- `>>> ` REPL: Eingabe → Pipeline → Ausgabe
- Lädt **keine** externen Services

### 4B. `main_boot.py` — OS-Modus (Haupteinstieg)
```bash
# Standard:
python main_boot.py

# Optionen:
python main_boot.py --mode production          # Produktion
python main_boot.py --mode simulation           # Keine Side-Effects
python main_boot.py -c "drucke hallo"           # Einzelbefehl
python main_boot.py -e "open github"            # Evaluate + Exit (JSON)
python main_boot.py --status                    # Nur Status
python main_boot.py --loop --ollama             # Autonomer Loop + LLM
python main_boot.py --loop --ollama --trace     # + Execution-Trace
python main_boot.py --dashboard                 # + Streamlit Dashboard
python main_boot.py --max-iterations 10         # Loop-Iterationen
```

**Interaktive Befehle:**
| Befehl | Aktion |
|--------|--------|
| `/help` | Hilfe |
| `/status` | OS-Status |
| `/compile <PATH>` | .txt-Ordner → MCXF |
| `/rag <QUERY>` | RAG-Suche |
| `/shutdown` | Shutdown |

### 4C. `runtime/main.py` — Flask API Server
```bash
python runtime/main.py
# → http://localhost:5001
```
- SQLite-DB (WAL, CQRS): Events, Workers, Tasks, Snapshots
- `WriterThread`: Serialisierter Schreibpfad
- `ObservationLoop`: Watchdog für Stuck/Drit
- `RoutingPolicy`: Deterministisches Task-Routing
- `GovernanceSync`: Iterations-/Token-Limits
- LLM-Client: Qwen + SMOL via Ollama

### 4D. `api_server.py` — FastAPI Control Plane
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8080
# → http://localhost:8080
```
- Swarm-Nodes, Graph, Replay, Analyse
- WebSockets für Live-Streams
- Meta-Reasoning + Self-Improvement

### 4E. Dashboard (Streamlit)
```bash
python main_boot.py --dashboard
# Oder direkt:
streamlit run dashboard.py
# → http://localhost:8501
```
- MCXF Memory, RAG Search, Trace

## 5. Port-Übersicht

| Port | Protokoll | Dienst | Quelle |
|------|-----------|--------|--------|
| `5001` | HTTP | Flask Runtime API | `config.RUNTIME_FLASK_PORT` |
| `8080` | HTTP | FastAPI Control Plane | `api_server.py` |
| `8000` | HTTP | Docker uvicorn | `Dockerfile` |
| `8501` | HTTP | Streamlit Dashboard | `dashboard.py` |
| `11434` | HTTP | Ollama (extern) | `config.OLLAMA_BASE` |

## 6. API-Referenz

### Flask Runtime API (`http://localhost:5001`)

| Route | Methode | Beschreibung |
|-------|---------|-------------|
| `/api/state` | GET | Systemzustand |
| `/api/health` | GET | Healthcheck |
| `/api/events` | GET | Events (Stream/Domain-Filter) |
| `/api/events/stats` | GET | Statistiken (Timeline, Severity) |
| `/api/task` | POST | Task einreichen |
| `/api/governance` | GET | Governance-Status |
| `/api/governance/reset` | POST | Governance zurücksetzen |
| `/api/worker/<id>/pause` | POST | Worker pausieren |
| `/api/worker/<id>/resume` | POST | Worker fortsetzen |
| `/api/chat` | POST | Chat (SMOL/Qwen + Slash-Befehle) |
| `/api/models` | GET | Modell-Liste |
| `/api/models/<name>/health` | GET | Modell-Health |
| `/api/rag/search` | POST | RAG-Suche |
| `/api/rag/reload` | POST | RAG-Index neu laden |
| `/api/fs/list` | GET | Dateisystem auflisten |
| `/api/fs/read` | GET | Datei lesen |
| `/api/fs/write` | POST | Datei schreiben |
| `/api/fs/delete` | POST | Datei löschen |
| `/api/snapshot` | POST | Snapshot auslösen |
| `/api/handoff` | GET | Session-Handoff |
| `/api/hud-action` | POST | HUD-Aktion (screenshot, url, cmd) |

### FastAPI Control Plane (`http://localhost:8080`)

| Route | Methode | Beschreibung |
|-------|---------|-------------|
| `/task` | POST | Task einreichen |
| `/nodes` | GET | Swarm-Knoten |
| `/graph` | GET | Graph-Zustand |
| `/replay/{id}` | GET | Node-Replay |
| `/explain/{id}` | GET | Decision Autopsy |
| `/meta-explain/{id}` | GET | Meta-Reasoning |
| `/self-improve/{id}` | GET | Selbstoptimierung |
| `/stream` | WS | Live-Event-Stream |
| `/graph/stream` | WS | Live-Graph-Updates |

### Chat-Befehle (POST /api/chat)

| Befehl | Aktion |
|--------|--------|
| `/help` | Hilfe anzeigen |
| `/status` | System-Zusammenfassung |
| `/workers` | Worker-Liste |
| `/events [N]` | Letzte N Events |
| `/gate` | Gate-Status |
| `/snapshot` | Snapshot auslösen |
| `/chat <text>` | Nachricht an Qwen |

## 7. Testen & Verifizieren

### Level 1: Syntax-Prüfung
```bash
cd /home/hz/AlitaProject/Codebase/MUSCAL\ CORE
python3 -c "
import py_compile, os
errors = []
for root, dirs, files in os.walk('.'):
    for f in files:
        if not f.endswith('.py'): continue
        if '/__pycache__' in root: continue
        try:
            py_compile.compile(os.path.join(root, f), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(str(e))
print(f'{len(errors)} Fehler') if errors else print('OK: Alle Python-Dateien syntaxkorrekt')
"
```

### Level 2: Smoketest
```bash
# OS-Status + Boot:
python main_boot.py --status

# Loop-Demo (deterministisch, kein Ollama):
python muscal_loop.py
```

### Level 3: Runtime-Server
```bash
# Server starten (3s warten, dann curl):
python runtime/main.py &
sleep 3
curl -s http://localhost:5001/api/health | python3 -m json.tool
# Erwartet: {"status": "ok", "event_count": >0, "writer_alive": true}

# Chat-Test:
curl -s -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hallo"}'
# → response + type

# Event-Test:
curl -s http://localhost:5001/api/events?limit=5 | python3 -m json.tool
```

### Level 4: Optimizer-Test
```bash
python3 -c "
from runtime.optimizer.pipeline import OptimizerPipeline
p = OptimizerPipeline()
plan = [
    {'tool': 'console.print', 'args': {'text': 'start'}},
    {'tool': 'validate', 'args': {}},
    {'tool': 'filesystem.write', 'args': {'path': '/tmp/t.txt', 'content': 'd'}},
]
opt, report = p.optimize(plan)
print(f'Nodes: {report.node_count_before} -> {report.node_count_after}')
print(f'Layers: {report.parallel_layers}')
print(f'Verification: {\"PASS\" if report.verification.get(\"passed\") else \"FAIL\"}')
print(report)
"
```

### Level 5: Integration
```bash
# Full Pipeline (eval mode):
python main_boot.py -e "drucke hallo"
# → JSON mit mcxf, execution, feedback, memory_id

# Dashboard:
python main_boot.py --dashboard
# → http://localhost:8501 (3 Tabs)
```

## 8. Optimizer (LLVM-Style)

Der Optimizer transformiert die flache `ExecutionPlan`-Liste in einen
optimierten DAG mit Parallel-Layern.

### Passes

| Pass | Aktion | Gewinn |
|------|--------|--------|
| `DeadCodeElimination` | Entfernt ungenutzte Nodes | ~15% |
| `NodeFusion` | Fasst validate+execute zusammen | ~25% |
| `ParallelizationPass` | Topological Sort + Layer | ~35% |

### CostVector (9 Dimensionen)

```
cpu, ram, latency, tokens, retries, estimated_cost, risk, tool_calls, graph_complexity
```

### Report

Nach jedem Compile wird ein `OptimizationReport` erzeugt:
```
Nodes: 4 -> 3 (1 removed)
Layers: 2
Fusion Count: 1
Cost Reduction: 0.333
Verification: PASS
Determinism: PASS
Replay Compatible: True
```

## 9. Architektur

### Verzeichnisstruktur
```
MUSCAL CORE/
├── main.py                        ← Simple CLI
├── main_boot.py                   ← OS-Modus (Haupteinstieg)
├── api_server.py                  ← FastAPI Control Plane
├── bootstrap.py                   ← Swarm-Demo
├── config.py                      ← Konfiguration (Pfade, Modelle, Ports)
├── kernel.py                      ← Kernel-Pipeline (RAG→MKC→Bridge→MEL→Feedback)
├── mel.py                         ← Memory Execution Layer
├── bridge.py                      ← Task → Tool Mapping
├── muscal_os.py                   ← OS-Lifecycle
├── muscal_loop.py                 ← Autonomer LLM-Loop
├── os_config.py                   ← Deployment-Konfig
├── runtime/
│   ├── main.py                    ← Flask-Server Entry Point
│   ├── database.py                ← SQLite (WAL, CQRS, 12 Tabellen)
│   ├── kernel/
│   │   ├── writer.py              ← WriterThread (serialisierter Schreibpfad)
│   │   ├── scheduler.py           ← RoutingPolicy (deterministisch)
│   │   ├── gate.py                ← Gate-Check (atomare Transaktion)
│   │   ├── bootstrap.py           ← Cold-Start Seed
│   │   ├── sanitizer.py           ← Injection-Schutz (RULE-2)
│   │   ├── governance.py          ← GovernanceSync + async Governance
│   │   ├── rag_index.py           ← RAG-Index
│   │   └── chroma_index.py        ← ChromaDB-Index
│   ├── llm/
│   │   ├── client.py              ← Ollama-Client (urllib, retry, async)
│   │   └── models.py              ← ask_smol, ask_qwen, ask_r1
│   ├── observation/
│   │   └── loop.py                ← ObservationLoop (Watchdog)
│   ├── services/
│   │   ├── snapshot.py            ← Event-Snapshots
│   │   └── handoff.py             ← Session-Export
│   ├── optimizer/
│   │   ├── pipeline.py            ← OptimizerPipeline + OptimizedPlan
│   │   ├── base_pass.py           ← OptimizationPass ABC
│   │   ├── graph.py               ← ExecutionDAG (topological_sort)
│   │   ├── dead_node.py           ← Dead-Code Elimination
│   │   ├── node_fusion.py         ← Tool-Fusion (4 Regeln)
│   │   ├── parallelization.py     ← Parallel Layer Assignment
│   │   ├── cost_optimizer.py      ← CostVector (9 Dim.)
│   │   ├── verification.py        ← FullVerificationResult
│   │   └── report.py              ← OptimizationReport
│   └── api/
│       ├── __init__.py            ← create_app(), Globals
│       ├── state.py               ← /api/state, /api/health
│       ├── chat.py                ← /api/chat + Slash-Befehle
│       ├── tasks.py               ← /api/task, Governance
│       ├── workers.py             ← Worker pause/resume
│       ├── events.py              ← Events + Stats
│       ├── models.py              ← Modell-Liste
│       ├── rag.py                 ← RAG-Suche
│       ├── fs.py                  ← Dateisystem
│       ├── admin.py               ← Snapshot, HUD
│       └── handoff.py             ← Handoff
├── docs/                          ← Wissen für RAG
├── storage/                       ← DBs + Snapshots
└── frontend/                      ← React-Komponenten (optional)
```

### Pipeline
```
INPUT
  ↓
RAG (Kontextabruf)
  ↓
MKC (MCXF-Compiler)
  ↓
Bridge (Task → Tool Mapping)
  ↓
Optimizer (DCE, Fusion, Parallel)
  ↓
MEL (Tool-Ausführung)
  ↓
Feedback (Analyse + Anpassung)
  ↓
Memory (Speicherung)
```

## 10. Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `ModuleNotFoundError: flask` | Paket fehlt | `pip install flask flask-cors` |
| `Ollama not reachable` | Ollama läuft nicht | `ollama serve &` |
| `Model X not found` | Modell nicht gepulled | `ollama pull <model>` |
| `curl: Connection refused` | Server läuft nicht | `python runtime/main.py &` |
| `storage/muscal.db` fehlt | DB nicht initialisiert | Wird automatisch beim Start angelegt |
| `port 5001 in use` | Anderer Service blockiert | `kill -9 $(lsof -ti:5001)` |
| `No module named runtime.main` | Falsches Verzeichnis | `cd /path/to/MUSCAL CORE/` |
