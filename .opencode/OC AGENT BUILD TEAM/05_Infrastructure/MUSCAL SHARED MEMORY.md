# MUSCAL SHARED MEMORY

## Zweck

Gemeinsamer Wissensspeicher für alle Agenten.

---

## Architektur

```
Agent 1 ─┐
Agent 2 ─┤
Agent 3 ─┼──► Shared Memory ──► Knowledge Graph
Agent 4 ─┤
Agent N ─┘
```

---

## Memory Layers

| Layer | Beschreibung | Zugriff |
|-------|--------------|---------|
| Working Memory | Temporäre Daten | Lesen/Schreiben |
| Short-Term Memory | Session-Daten | Lesen/Schreiben |
| Long-Term Memory | Persistente Daten | Lesen/Schreiben |
| Archive | Historische Daten | Nur Lesen |

---

## Memory Operations

| Operation | Beschreibung |
|-----------|--------------|
| Store | Daten speichern |
| Retrieve | Daten abrufen |
| Update | Daten aktualisieren |
| Delete | Daten löschen |
| Query | Daten durchsuchen |
| Index | Daten indizieren |

---

## Memory Schema

```yaml
Memory Entry:
  ID: [unique id]
  Category: [knowledge/decision/event/metric]
  Topic: [thema]
  Content: [daten]
  
  Metadata:
    Author: [agent name]
    Created: [timestamp]
    Updated: [timestamp]
    Expires: [optional timestamp]
    Confidence: [0-100]
    Sources: [liste]
  
  Tags: [liste]
  Relations: [liste]
```

---

## Knowledge Categories

| Kategorie | Beschreibung |
|-----------|--------------|
| Architecture | Architekturentscheidungen |
| Code | Code-bezogenes Wissen |
| Process | Prozesswissen |
| Decision | Entscheidungsprotokolle |
| Metric | Metriken und Messwerte |
| Event | Ereignisprotokolle |
| User | Benutzerpräferenzen |

---

## Access Control

```yaml
Access Control:
  Roles:
    - read: lesen
    - write: schreiben
    - admin: verwalten
  
  Permissions:
    Memory Architect: admin
    All Agents: read
    Originating Agent: write
```

---

## Cache Strategy

```yaml
Cache:
  Levels:
    - L1: In-Memory (Agent-local)
    - L2: Shared Cache (Redis)
    - L3: Persistent Storage
  
  Eviction:
    Strategy: LRU (Least Recently Used)
    Max Size: 1GB per agent
  
  Invalidation:
    - TTL based
    - Event based
    - Manual invalidation
```

---

## Query Language

```yaml
Query:
  Simple:
    GET /memory/{category}/{topic}
  
  Filtered:
    GET /memory?category={cat}&tag={tag}
  
  Full Text:
    GET /memory/search?q={query}
  
  Aggregated:
    GET /memory/aggregate?field={field}
```

---

## Consistency

```yaml
Consistency:
  Model: Eventual Consistency
  
  Guarantees:
    - Read-your-writes
    - Monotonic reads
    - Causal consistency
  
  Conflict Resolution:
    Strategy: Last-writer-wins
    Versioning: Vector clocks
```

---

## Dokumente

```
docs/memory/
├── SHARED_MEMORY_ARCHITECTURE.md
├── MEMORY_SCHEMA.md
├── ACCESS_CONTROL.md
├── CACHE_STRATEGY.md
└── CONSISTENCY_MODEL.md
```

---

## Abschluss

Memory Usage: __% 

Query Latency: __ms

Nächster Schritt: _______________
