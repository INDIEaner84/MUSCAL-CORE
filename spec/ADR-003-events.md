# ADR-003: Event Architecture — EventBus als zentrales Event-System

**Status:** APPLIED  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 hat **3 Event-Systeme**, davon 1 tot:

| # | System | Klasse | File | Mechanismus | Status |
|---|--------|--------|------|-------------|--------|
| 1 | **EventBus** | `EventBus` | `event_bus.py` (74 LOC) | Pub-Sub, Topics, Prioritäten, History 50K | Aktiv — OS-Lifecycle, Plugin-Events |
| 2 | **Graph Events** | `GraphState.on/emit` | `graph.py:191-201` | Type-basierte Listener, Update-Stream 50 | Aktiv — Pipeline-interner Sync |
| 3 | **EventBusSwarm** | `EventBus` | `event_bus_swarm.py` (10 LOC) | Subscriber-Liste, Broadcast | **Dead Code** — `swarm_system.py` importiert `WebRTCMesh` (existiert nicht) |

### Bestehende Bridge (Graph Events → EventBus)

`muscal_os.py:282-295` (`_wire_event_bus`) mapped 5 Graph-Event-Typen auf EventBus-Topics:

| Graph Event | EventBus Topic |
|---|---|
| `EVENT_NODE_CREATED` | `graph.node_created` |
| `EVENT_NODE_UPDATED` | `graph.node_updated` |
| `EVENT_EDGE_CREATED` | `graph.edge_created` |
| `EVENT_EXECUTION_STARTED` | `graph.execution_started` |
| `EVENT_EXECUTION_FINISHED` | `graph.execution_finished` |

### Event-Typen (8 Konstanten in `schema.py`)

```python
EVENT_NODE_CREATED, EVENT_NODE_UPDATED, EVENT_EDGE_CREATED
EVENT_EXECUTION_STARTED, EVENT_EXECUTION_FINISHED
EVENT_SYSTEM_ACTION_STARTED, EVENT_SYSTEM_ACTION_COMPLETED, EVENT_SYSTEM_ACTION_FAILED
```

Zusätzlich OS-Lifecycle-Events als Plain-Strings (nicht als Konstanten):
`"boot.init"`, `"kernel.initialized"`, `"plugins.initialized"`, `"runtime.initialized"`, `"runtime.skipped"`

### Probleme

1. **3 Event-Systeme** — Verwirrung über Zuständigkeit, `event_bus_swarm.py` ist dead code
2. **OS-Lifecycle-Events sind Plain-Strings** — kein Autocomplete, kein Type-Check, Risk von Tippfehlern
3. **Kein einheitliches Interface** — `EventBusProvider` Protocol (`interfaces.py:41`) definiert `publish(topic, payload, source, priority)`, aber Graph Events nutzen `emit(event_type, payload)` ohne source/priority
4. **Bridge unvollständig** — Graph→EventBus existiert, EventBus→Graph fehlt
5. **Events sind nicht persistent** — Weder EventBus noch Graph Events persistieren. Replay über Neustart hinweg nicht möglich
6. **Keine Event-IDs global** — EventBus generiert IDs (`f"{topic}_{idx}_{ms}"`), Graph Events haben keine

---

## Decision

### EventBus ist das zentrale Event-System

Architektur:

```
                    EventBus (event_bus.py)
                   /          |          \
                  /           |           \
        Graph Events       Plugins      OS-Lifecycle
        (graph.emit →     (subscribe    (muscal_os.py,
         EventBus)         to topics)    main.py)
```

### Scope-Zuordnung

| Scope | Primäres System | Routing | History | Persistenz |
|-------|----------------|---------|---------|------------|
| **OS-Lifecycle** (Boot, Init, Shutdown) | EventBus | Topic-basiert | 50K Ring | Optional (Post-ADR) |
| **Pipeline-intern** (Execute, Sync, Sphere) | Graph Events → EventBus (gespiegelt) | Typ+Topic | 50 Stream + 50K Bus | Optional |
| **Plugin-Kommunikation** | EventBus | Topic-basiert | 50K Ring | Optional |
| **System Runtime Actions** | Graph Events → EventBus (gespiegelt) | Konstanten | 50 Stream + 50K Bus | Optional |

### EventBusSwarm

`event_bus_swarm.py` wird als **DEPRECATED** markiert. Kein Code ausserhalb von `swarm_system.py` importiert es, und `swarm_system.py` ist nicht lauffähig (fehlendes `WebRTCMesh`). Entfernung in v0.9.

### OS-Lifecycle-Konstanten

Alle OS-Lifecycle-Topic-Strings werden nach `schema.py` als Konstanten migriert:

```python
EVENT_BOOT_INIT = "boot.init"
EVENT_KERNEL_INITIALIZED = "kernel.initialized"
EVENT_PLUGINS_INITIALIZED = "plugins.initialized"
EVENT_RUNTIME_INITIALIZED = "runtime.initialized"
EVENT_RUNTIME_SKIPPED = "runtime.skipped"
```

### EventBusProvider Interface

Das bestehende Protocol in `interfaces.py:41` wird als verbindlich für alle Event-Kommunikation erklärt. Graph Events bleiben als interne Optimierung (kein Pub-Sub-Overhead für Pipeline-Sync), aber alle Pipeline-Events werden via Bridge an EventBus gespiegelt.

### Persistenz

Event-Persistenz wird in einem **separaten ADR** (Post-ADR-003) behandelt, da dies den Storage-Layer betrifft und mit der SQLite-Konsolidierung (ADR-002 Phase 5) koordiniert werden muss.

---

## Migration Plan

### Phase 1: Dokumentation & Markierung (v0.7)

- [x] ADR-003 finalized
- [x] EventBusSwarm als deprecated in Source-Commen markiert
- [x] OS-Lifecycle-Konstanten in schema.py definiert
- [x] Scope-Dokumentation in event_bus.py und graph.py ergänzt

### Phase 2: EventBus → Graph Bridge (v0.8)

Fehlende Bridge-Richtung ergänzt — OS-Events in den Kernel-Graphen spiegeln:

```python
# muscal_os.py _wire_event_bus() + _bridge_to_graph()
self.events.subscribe("*", self._bridge_to_graph)
```

Da EventBus nur `"*"` als Wildcard unterstützt (kein Globbing), abonniert die
Bridge alle Topics und filtert nicht. Der `_bridge_to_graph`-Callback erstellt
eine flache Kopie des Payloads und reichert ihn mit `_source`-Metadaten an.

### Phase 3: EventBusSwarm entfernen (v0.8)

- [x] `event_bus_swarm.py` gelöscht (existierte nicht mehr auf Disk)
- [x] `swarm_system.py` → `archive/` (toter Code, importiert nicht-existierendes WebRTCMesh)
- [x] `archive/swarm_main.py` gelöscht (importierte swarm_system)

### Phase 4: Event Persistence ADR (v0.9+)

Separates ADR für:
- Speicherformat (SQLite, JSON-Lines, oder hybrid)
- Replay-Garantien (at-least-once, exactly-once)
- Retention-Policy
- Event-Sourcing für Pipeline-Zustand

---

## Consequences

### Positive
- Einheitliches Event-System reduziert Architektur-Komplexität
- Bestehende Bridge wird durch fehlende Richtung ergänzt → vollständige Transparenz
- OS-Lifecycle-Events werden typsicher (Konstanten statt Strings)
- Dead Code wird identifiziert und zur Entfernung vorgemerkt
- Klare Scope-Regeln verhindern zukünftige Verwirrung

### Negative
- EventBus→Graph Bridge erzeugt doppelte Event-Streams für OS-Events
- Graph Events bleiben als zweites System (zusätzliche Komplexität), aber mit klarem Scope
- Persistenz-Lösung erfordert separates ADR (zeitliche Verzögerung)

---

## Compliance Check

- [x] Event-System-Zuständigkeit dokumentiert
- [x] EventBusSwarm als dead code identifiziert und deprecated
- [x] Bridge-Richtungen analysiert (Graph→Bus existiert, Bus→Graph fehlt)
- [x] Event-Typen katalogisiert (8 Konstanten + 5 OS-Plain-Strings)
- [x] EventBusProvider Interface als Standard dokumentiert
- [x] ADR-003 ACCEPTED statt PROPOSED
- [x] Phase 2 Bridge implementiert (EventBus→Graph in muscal_os.py)
- [x] Bridge-Test: EventBus-Events werden in Graph gespiegelt
- [x] Phase 3: EventBusSwarm + swarm_system entfernt
- [x] ADR-003 APPLIED (alle 3 Phasen abgeschlossen)
