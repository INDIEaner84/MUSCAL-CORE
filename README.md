# MUSCAL CORE

Multi-Scale Context-Aware Learning — Cognitive Operating System

**Status:** Stable Prototype (READY WITH RISKS)

---

## Quick Start

```bash
pip install -r requirements.txt
python3 main.py
```

## Entrypoints

| Command | Description |
|---------|-------------|
| `python3 main.py` | REPL mode |
| `python3 main_boot.py` | OS mode with CLI args |
| `python3 runtime/main.py` | Flask API server (:5050) |
| `python3 api_server.py` | FastAPI control plane (:8080) |
| `docker compose up` | Containerized |

## Documentation

| Document | Path |
|----------|------|
| Project State | `docs/PROJECT_STATE.md` |
| Technical Baseline | `docs/TECHNICAL_BASELINE.md` |
| Documentation Map | `docs/Docs.md` |
| Architecture Decisions | `spec/` |
| Specifications | `archive/history/rfcs/` |
| Plugin SDK | `spec/PLUGIN_API.md` |

## License

Proprietary — All rights reserved.
