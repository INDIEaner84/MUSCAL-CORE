MCXF v1

00_IDENTITY:
- document_id: MCXF-001
- generated_from: "Chat-Log (Session 2026-07-02): MUSCAL Bootstrap v0.1 Setup + MKC v0.2 Spec"
- generator: "deepseek-v4-flash-free (opencode)"

01_SUMMARY:
- A minimal MUSCAL Bootstrap Kit v0.1 was specified, implemented, and tested locally.
- The system consists of MKC (rule-based compiler), MEL (execution engine), Tools (filesystem.write, math.add, console.print), and Memory (SQLite + JSONL).
- All 9 project files were written to /home/hz/AlitaProject/Codebase/MUSCAL CORE/ and passed 3 test scenarios (write, add, print).
- A specification for MKC v0.2 was then introduced, defining an LLM-powered Knowledge Compiler that outputs MCXF documents.
- The conversation established a 3-phase build plan: Phase 1 = MCXF Proof, Phase 2 = Code Integration, Phase 3 = Loop.

02_DECISIONS:
- Project files are placed flat in /home/hz/AlitaProject/Codebase/MUSCAL CORE/ (no nested subdirectory).
- MUSCAL Bootstrap v0.1 uses zero external dependencies (stdlib only: sqlite3, json, typing).
- Execution model is deterministic and synchronous (no async, no autonomous tool access).
- MKC v0.1 is rule-based; MKC v0.2 upgrades to LLM-driven structured extraction.
- MCXF v1 is adopted as the structured output format for MKC v0.2.
- Phase order is fixed: MCXF Proof → Architecture Integration → Loop Stabilization.
- RAG is deferred to a later version (stub only in v0.1).

03_ARCHITECTURE:
- Pipeline: User Input → MKC (Compiler) → Execution Plan → MEL (Executor) → Tools → Memory (SQLite + JSONL).
- MKC v0.1 uses if/elif string matching to classify input as "write", "add", or "print".
- MKC v0.2 replaces string matching with an LLM that outputs strict MCXF format.
- MEL consumes an ExecutionPlan (list of {tool, args} steps) and dispatches to TOOL_REGISTRY.
- Memory stores plan+result pairs in SQLite and logs every interaction to JSONL.
- TOOL_REGISTRY is a dict mapping string names to callable functions.
- MCXF v1 has 9 mandatory sections: 00_IDENTITY through 08_OPEN_QUESTIONS.

04_GLOSSARY:
- MUSCAL: Modular Unified Structured Compiler and Execution Layer.
- MKC: Mini (or Modular) Knowledge Compiler — extracts structure from raw chat.
- MEL: Modular Execution Layer — runs deterministic tool sequences.
- MCXF: MUSCAL Context Exchange Format — structured document with 9 sections.
- Execution Plan: A dict with "intent" (string) and "steps" (list of {tool, args}).
- TOOL_REGISTRY: Central registry mapping tool names to Python functions.
- RAG: Retrieval-Augmented Generation — planned for future embeddings-based retrieval.
- SQLite + JSONL: Dual persistence layer (structured DB + append-only log).

05_CONSTRAINTS:
- No external dependencies are permitted (stdlib only).
- Execution must be fully deterministic.
- No autonomous tool access (MEL only runs explicitly planned steps).
- MCXF output must not hallucinate or use external assumptions.
- Only provided chat content may be used for extraction.
- Unknown information must be marked as UNKNOWN, not inferred.

06_TASKS:
- [DONE] Create spec.yaml with project definition.
- [DONE] Implement schema.py with type aliases.
- [DONE] Implement tools.py with 3 tools + TOOL_REGISTRY.
- [DONE] Implement mkc.py with rule-based classification.
- [DONE] Implement mel.py with plan execution engine.
- [DONE] Implement memory.py with SQLite + JSONL persistence.
- [DONE] Implement rag.py with stub retrieve().
- [DONE] Implement main.py with REPL loop.
- [DONE] Create storage/ directory.
- [DONE] Verify all 3 tool paths (write, add, print).
- [PENDING] Phase 1: MCXF Proof — validate LLM can produce correct MCXF.
- [PENDING] Phase 2: Replace rule-based MKC with LLM-driven compiler.
- [PENDING] Phase 2: Add Ollama/OpenAI integration layer.
- [PENDING] Phase 2: Implement conflict detection in MKC.
- [PENDING] Phase 3: Close the loop — LLM output feeds back into stable system.

07_CONFLICTS:
- None detected.

08_OPEN_QUESTIONS:
- How should memory versioning work across MKC versions (v0.1 vs v0.2)?
- Should MCXF be extended with a 09_METADATA section for timestamps/versioning?
- Which LLM backend should be default — Ollama (local) or OpenAI (cloud)?
- Should MEL v0.2 support async execution graphs or stay synchronous?
- Is the current SQLite schema sufficient for future RAG queries, or does it need embedding columns?
