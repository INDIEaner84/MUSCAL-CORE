# MUSCAL Knowledge Architecture Audit

## 1. Existing Memory Systems

| Component | Path | Type | Status | Description |
|-----------|------|------|--------|-------------|
| memory.py | `/memory.py` | Core (immutable) | Active | SQLite-backed MCXF snapshot store with keyword search, audit log |
| graph_memory.py | `/graph_memory.py` | Core (immutable) | Active | In-memory graph with nodes/edges, keyword query, ingest stub |
| rag.py | `/rag.py` | Core (immutable) | Active | Keyword retrieval + context enrichment from memory.py |
| SQLiteMemoryAdapter | `features/memory/sqlite_adapter.py` | Feature | Active | Class-based adapter wrapping memory.py |
| UnifiedMemory | `features/memory/unified_memory.py` | Feature | Active | Combines GraphMemory + SQLiteMemoryAdapter |

## 2. Core Memory Module (`memory.py`) Capabilities

- **Tables:** `memory` (id, data), `mcxf_snapshots` (id, input_text, mcxf_json, result_json, feedback_json, created_at), `audit_log` (id, entry_type, payload, created_at)
- **Key functions:** `store`, `store_snapshot`, `retrieve_by_id`, `search_by_keyword`, `get_recent`, `log_jsonl`
- **Pruning:** `_prune_snapshots` caps at `MAX_MEMORY_ENTRIES=10000`
- **No knowledge-specific semantics** — stores raw MCXF snapshots with no classification, confidence, evidence level, or reuse conditions

## 3. GraphMemory (`graph_memory.py`) Capabilities

- In-memory only — not persisted
- Simple node/edge model
- `ingest()` method is a no-op stub
- No relationship typing beyond `relation` string
- No query for structured knowledge

## 4. RAG (`rag.py`) Capabilities

- Keyword-based retrieval from memory.py
- Context enrichment for prompts
- No semantic search, no embedding, no ranking beyond keyword match

## 5. Duplication Risks

| Risk | Severity | Notes |
|------|----------|-------|
| New knowledge database overlapping with memory.py | High | Must reuse memory.py/sqlite_adapter.py for storage |
| Second event system overlapping with EventStore | High | Must reuse RuntimeObservability + EventStore for events |
| Independent graph conflicting with graph_memory.py | Medium | Must enrich existing GraphMemory, not replace it |
| Separate RAG conflicting with rag.py | Medium | Must extend rag.py or work alongside it |

## 6. Recommended Ownership Model

| Domain | Authority | Storage | Extension |
|--------|-----------|---------|-----------|
| Raw execution snapshots | memory.py | Core SQLite | Immutable — do not modify |
| Knowledge candidates/entries | features/knowledge/ | memory.py via SQLiteMemoryAdapter | New feature module |
| Knowledge graph | features/knowledge/ | GraphMemory via UnifiedMemory | Enrich existing graph |
| Knowledge retrieval | features/knowledge/ | rag.py + new retriever | Extend, not replace |
| Knowledge lifecycle events | EventStore | RuntimeObservability | New event topics |
| Provenance | EventStore | Existing | Reuse correlation/causation IDs |

## 7. Gap Analysis

| Gap | Impact | Resolution |
|-----|--------|------------|
| No structured knowledge model | Cannot store reusable knowledge | Create KnowledgeCandidate/KnowledgeEntry models |
| No evidence classification | Cannot validate knowledge provenance | Add EvidenceLevel enum |
| No knowledge lifecycle states | Cannot track candidate→validated→superseded | Add KnowledgeState enum |
| No extraction from bridge executions | No knowledge distillation pipeline | Create KnowledgeExtractor |
| No validation pipeline | Risk of storing unverified knowledge | Create KnowledgeValidator |
| No runtime integration | Knowledge not part of execution flow | Extend RuntimeCoordinator |
