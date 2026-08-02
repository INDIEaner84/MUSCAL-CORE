# ADR-002: Memory — GraphMemory als Standard-Interface

**Status:** ACCEPTED — Phase 1 ✅, Phase 3 ✅, Phase 4 ✅  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 hat **5+ Memory/Graph-Speicher-Implementierungen** mit inkompatiblen Interfaces:

| Klasse | Datei | Edge-Format | Query-API | Nutzer |
|--------|-------|-------------|-----------|--------|
| **GraphMemory** | `graph_memory.py` | `dict {from, to, relation}` | `get_node()`, `get_related()`, `query()` | `main_boot.py` |
| **GraphMemory (minimal)** | `minimal_graph_memory.py` | `tuple (from, rel, to)` | `query_related()` | `memory_system.py`, `graph_system_loop.py`, `self_reasoning_kernel.py`, `graph_builder.py`, `kernel_core.py` |
| **GraphState** | `graph.py` | `Edge`-Dataclass (source, target, type) | `trace_dependencies()`, `get_snapshot()` | `kernel.py`, `sphere.py` |
| **GraphStore** | `graph_store.py` | `dict {from, to, relation}` | Keine Query-Methoden | `causality_engine.py` |
| **GraphMemory (zweite)** | `minimal_graph_memory.py` (nach Fix) | Identisch mit `graph_memory.py` | Beide APIs | Konsolidiert |

Zusätzlich existieren 2 SQLite-Datenbanken (`memory.db` + `muscal.db`) ohne Sync-Mechanismus.

---

## Decision

**`graph_memory.GraphMemory` ist das Standard-Interface für flache Graph-Speicher.**

`graph.GraphState` bleibt parallel für den Event-getriebenen Kernel-Graphen (unterschiedliche Anforderungen: Events, Pruning, Focus).

### Interface-Kontrakt

```python
class GraphMemory:
    def __init__(self):
        self.nodes: dict = {}
        self.edges: list = []

    def add_node(self, node_id: str, content: Any) -> None
    def add_edge(self, from_id: str, to_id: str, relation: str) -> None
    def get_node(self, node_id: str) -> Any
    def get_related(self, node_id: str) -> List[Dict]
    def query(self, keyword: str) -> Dict
    def query_related(self, node_id: str) -> List[Dict]  # Alias
    def ingest(self, text: str) -> None                   # Platzhalter
```

### SQLite-Konsolidierung

```text
Ziel: Eine Storage Authority

memory.db (memory.py)
    ├── memory-Tabelle (store_snapshot, retrieve_by_id, search_by_keyword)
    ├── mcxf_store-Tabelle
    └── JSONL-Logs (audit, confidence, health, trace, logs)

muscal.db (runtime/database.py)
    ├── 12 Tabellen (events, workers, tasks, decisions, snapshots, ...)
    └── WAL-Modus, CQRS-Schema

Phase 1: Schema Mapping
Phase 2: Migrations-Pfad
Phase 3: muscal.db → memory.db
```

---

## Migration Plan

### Phase 1: Interface vereinheitlichen ✅ (DONE)

- `minimal_graph_memory.py` → re-export von `graph_memory.GraphMemory` (APPLIED via OVERRIDE-002)
- `graph_memory.py` → `query_related()`, `ingest()` hinzugefügt (APPLIED via OVERRIDE-002)
- `graph_builder.py` → `add_edge()`-Aufruf korrigiert (APPLIED via OVERRIDE-002)

### Phase 2: Konsumenten migrieren

| Datei | Aktuell | Ziel |
|-------|---------|------|
| `memory_system.py` | `from minimal_graph_memory import GraphMemory` | Funktioniert bereits (Alias) |
| `graph_system_loop.py` | `from minimal_graph_memory import GraphMemory` | Funktioniert bereits |
| `self_reasoning_kernel.py` | `from minimal_graph_memory import GraphMemory` | Funktioniert bereits |
| `kernel_core.py` | `from minimal_graph_memory import GraphMemory` | Funktioniert bereits |

### Phase 3: Redundante Implementierungen deprecaten ✅

| Klasse | Aktion | Status |
|--------|--------|--------|
| `graph_store.GraphStore` | Deprecated — DeprecationWarning hinzugefügt | ✅ APPLIED |
| `graph_memory.py` (eigenständig) | Bereits der Standard | ✅ |
| `minimal_graph_memory.py` | Verbleibt als re-export für Kompatibilität | ✅ |

### Phase 4: Consumer migrieren ✅

| Datei | Änderung | Status |
|-------|----------|--------|
| `causality_engine.py` | Von `GraphStore`-API auf `GraphMemory.get_related()` umgestellt | ✅ APPLIED |

### Phase 5: SQLite-Konsolidierung (separates ADR) 🔲

---

## Consequences

### Positive
- Einheitliches Interface für Graph-Speicher
- Keine stillen Datenkorruptionen durch inkompatible Edge-Formate
- Geringere kognitive Last für Entwickler

### Negative
- `graph_store.py` muss migriert werden (1 Consumer: `causality_engine.py`)
- Zwei SQLite-DBs bleiben vorerst parallel

---

## Compliance Checklist

- [x] Phase 1 — OVERRIDE-002: GraphMemory-Konsolidierung
- [x] Phase 2 — Alle Imports konsolidiert (minimal_graph_memory → Re-Export)
- [x] Phase 3 — `graph_store.py` deprecated
- [x] Phase 4 — `causality_engine.py` auf GraphMemory migriert
- [ ] Phase 5 — SQLite-Migrationsplan erstellt
