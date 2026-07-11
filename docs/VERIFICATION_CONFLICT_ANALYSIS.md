# MUSCAL VERIFICATION FRAMEWORK — Conflict Analysis

Analyse des Dokuments `MUSCAL Verifikationsframework (Band III)`
gegenüber der aktuellen MUSCAL CORE Implementierung.

---

## 1. Was das Framework fordert

```
Input → Event → Event History → Replay → State → Proof
```

Kernprinzipien:
- **Event** ist die zentrale Einheit (nicht State)
- **State = f(Event History)** — State wird aus Events abgeleitet
- **Events sind immutable** — keine Änderung, nur neue Events
- **Event Chain** — kryptografisch verkettete Historie (previous_hash)
- **Runtime** darf State NICHT direkt verändern
- **Replay Engine** — State-Rekonstruktion aus Event-Log
- **Verification Layer** — proof-basierte Integritätsprüfung
- **Determinismus** — gleicher Input → gleiches Verhalten

---

## 2. Was das System aktuell hat

| Komponente | Status | Fundort |
|---|---|---|
| **Pipeline** | Linearer Orchestrator | `kernel.py` (488 LOC) |
| **Events (In-Memory)** | Graph-Events flüchtig | `graph.py` / `event_bus.py` |
| **Events (Persistent)** | SQLite events table (Runtime) | `runtime/database.py` |
| **State** | GraphState (mutable, pruned) | `graph.py` |
| **Replay** | `ReplayEngine` existiert als Print-Only | `kernel_diff_engine.py` |
| **Hash Verification** | Nur im Optimizer (DAG-Hash) | `runtime/optimizer/verification.py` |
| **Proof** | Existiert nicht | — |
| **Immutable Core** | 39 Dateien durch write_guard geschützt | `guards/write_guard.py` |
| **Plugin System** | Hook-basiert in `features/` | `plugin_registry.py` |

---

## 3. Kernkonflikt: Zwei parallele Event-Welten

```
WELT 1 (Kernel Pipeline):          WELT 2 (Runtime Layer):
  kernel.py → graph.emit()           WriterThread → SQLite events
  → in-memory GraphState             → idempotent, persistent
  → verliert bei Neustart            → überlebt Neustart
  → FIFO-Prune nach 5000 Nodes       → querybar, versioniert
```

Das Framework beschreibt **eine** konsistente Event-Kette.
Das aktuelle System hat **zwei unverbundene Welten**.

---

## 4. Direkte Konflikte

| Framework-Forderung | Aktueller Status | Konfliktgrad |
|---|---|---|
| Event = zentrale Einheit | Kernel nutzt In-Memory-Graph | **KRITISCH** |
| State = f(Event History) | State wird direkt geschrieben | **KRITISCH** |
| Events immutable | Graph-Events: mutable dicts | **HOCH** |
| Event Chain (previous_hash) | `caused_by` existiert, ungenutzt | **HOCH** |
| Runtime darf State NICHT verändern | WriterThread schreibt direkt in SQLite | **KRITISCH** |
| Replay Engine (echt) | Nur Print-Only-Implementierung | **HOCH** |
| Hash Verification (Kernel-State) | Nur Optimizer-DAG, nicht Kernel | **HOCH** |
| Proof Generation | Existiert nicht | **HOCH** |

---

## 5. Instabilitätsrisiken bei direkter Integration

### 5.1 Core Immutability Bruch
Das Framework würde `kernel.py`, `memory.py`, `graph.py` fundamental umbauen. Diese sind **IMMUTABLE** (39 Dateien, write_guard). Jede Änderung erfordert OVERRIDE-Dokumentation und gefährdet 32+ bestehende Tests.

### 5.2 State-Rekonstruktion vs. CRUD
`memory.py` ist pure CRUD (store/retrieve). Das Framework verlangt:
```
State(n) = Replay(Event[0:n])
```
Kein direktes Schreiben mehr → fundamentaler Architekturwandel.

### 5.3 Nicht-Determinismus
Das Framework verlangt `gleicher Input → gleiches Verhalten`. Aktuelle nicht-deterministische Elemente:
- RAGModule (vektorbasierte externe Suche)
- LLM-Aufrufe
- FeedbackModule (variiert)

### 5.4 Doppelte Architektur
`muscal_loop.py` (565 LOC) dupliziert Teile von `kernel.py` (488 LOC).
Das Framework setzt eine einzige Pipeline-Autorität voraus.

---

## 6. Entscheidung

**Direkte Integration: ❌ zu riskant**

**Plugin-Layer als Erweiterung: ✅ empfohlen**

Das Verification Framework wächst als zusätzliche Vertrauensschicht
über dem stabilisierten Core — nicht als Core-Umbau.

Siehe: `spec/ADR-011-verification.md`
Siehe: `docs/VERIFICATION_FRAMEWORK_PLAN.md`

---

*Analyse: 2026-07-11*
*Status: ARCHITECTURE DECISION — no implementation*
