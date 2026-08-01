# D-E3.0.2-001 — VECTOR RAG RECONCILIATION

**Status:** CORRECTED
**Supersedes:** D-E3.0-012 §3.2
**Date:** 2026-07-22

---

## 1. Previous Claim (E3.0)

Vector RAG is a "functioning component needing abstraction." It was listed as a blocker for E3.1 model abstraction contracts.

## 2. Corrected Claim

`runtime/kernel/rag_index.py:RAGIndex` is a **domain-specific utility** for embedding and searching a single document (`alita_wissen.md`). It uses `nomic-embed-text` via Ollama with a local disk cache. It is reachable through the Flask API runtime (WARM_PATH) but NOT through MuscalKernel.run() (HOT_PATH). It does NOT block E3.1.

## 3. Repository Evidence

| Evidence | Source |
|----------|--------|
| `rag_index.py` embeds `kernel/docs/alita_wissen.md` only | Line 20: `WISSEN_PATH = Path(__file__).parent / "docs" / "alita_wissen.md"` |
| Hardcoded embedding model | Line 19: `EMBED_MODEL = "nomic-embed-text"` |
| Hardcoded Ollama endpoint | Line 18: `OLLAMA_BASE = "http://localhost:11434"` |
| NOT imported by kernel.py | `grep` confirms zero imports from kernel.py |
| Imported by runtime/api/chat.py | Line 56: `from runtime.kernel.rag_index import get_rag_index` |
| Imported by runtime/api/rag.py | Lines 23, 35: imports `get_rag_index`, `reload_rag_index` |
| Kernel uses BM25 keyword RAG | `rag.py` uses `memory.search_by_keyword()` |
| Kernel pipeline rag call | `kernel.py:245`: `self.rag.retrieve(input_text)` → `rag.retrieve()` |

## 4. Call Graph

```
Flask API (runtime/main.py, supervisor.py)
  └── runtime/api/chat.py:api_chat()
        └── runtime/kernel/rag_index.py:get_rag_index()  ← WARM_PATH
  └── runtime/api/rag.py:api_rag_search()
        └── runtime/kernel/rag_index.py:get_rag_index()  ← WARM_PATH

MuscalKernel.run() (main.py, main_boot.py)
  └── rag.py:retrieve()  ← HOT_PATH (BM25 keyword, NOT vector)
```

## 5. Classification

**WARM_PATH** — reachable through an alternate production entry point (Flask API).

## 6. Architectural Impact

- Vector RAG does NOT need to be abstracted for the kernel path (kernel doesn't use it)
- The model-binding violation (`nomic-embed-text` hardcode) affects only the chat/rag API endpoints
- E3.1 model abstraction contracts should treat this as a **post-E3.1 cleanup ticket**, not a blocker
- The chat API's dependency on a single embedding model is a quality-of-service concern, not an architecture blocker

## 7. E3.1 Consequence

**NON-BLOCKER.** Can be addressed as a post-E3.1 cleanup. The model-binding abstraction should eventually cover embedding models, but the kernel hot path uses BM25 only — no embedding abstraction is needed for E3.1 kernel contracts.

## 8. Additional Model-Binding Audit

| Location | Hardcoded Value | Type | Classification |
|----------|----------------|------|----------------|
| `rag_index.py:19` | `nomic-embed-text` | Embedding model | WARM_PATH |
| `rag_index.py:18` | `http://localhost:11434` | Ollama endpoint | WARM_PATH |
| `scheduler.py:29` | `"qwen_router"` | Default fallback | WARM_PATH |
| `muscal_loop.py:18` | `qwen2.5:7b-instruct` | LLM model | EXPERIMENTAL |
| `muscal_loop.py:17` | `http://localhost:11434/api/generate` | Ollama endpoint | EXPERIMENTAL |
