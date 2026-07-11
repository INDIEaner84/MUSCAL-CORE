# MUSCAL CORE — Architecture Blueprint

**Version:** 0.5 (Juli 2026)
**Zielgruppe:** Management, CTO, Architekten
**Umfang:** ~10 Seiten, kein Quellcode

---

## 1. System Purpose

MUSCAL CORE (Multi-Scale Context-Aware Learning) ist ein **kognitives Betriebssystem** — keine Bibliothek, kein Framework. Es orchestriert AI-Agents, führt Tasks aus, kompiliert natürliche Sprache in ausführbare Pläne und überwacht sich selbst durch einen mehrschichtigen Observability-Stack.

Anders als herkömmliche AI-Frameworks (LangChain, AutoGen, CrewAI) ist MUSCAL als **eigenständiges System** konzipiert: Kernel, OS-Layer, Compiler, Optimierer, API-Server und Frontend — alles in einer Codebasis.

### Kernprinzipien

| Prinzip | Beschreibung |
|---------|-------------|
| Determinismus | L1-Routing ist regelbasiert, kein LLM, <1µs |
| Single Writer | Nur ein Thread schreibt in die DB (CQRS) |
| Safety First | Jeder LLM-Input wird auf Injection geprüft |
| Layer-Trennung | Jede Schicht hat genau eine Verantwortung |
| Replayability | Jeder Task ist deterministisch wiederholbar |

---

## 2. 7-Schichten-Architektur

```
L7 FRONTEND         React/TypeScript (Dashboard, GraphView)
L6 API LAYER        Flask API (:5050), FastAPI (:8080)
L5 OS LAYER         BootManager, EventBus, Deployment-Modi
L4 COMPILER         MKC (MCXF), Bridge (Tool-Match), Optimizer
L3 EXECUTION        MEL (Tool-Dispatch), Browser Engine, Desktop Tools
L2 KERNEL           WriterThread (CQRS), Scheduler, Gate, Governance
L1 STORAGE          SQLite (WAL, 12 Tabellen), JSONL, ChromaDB, FAISS
```

### Datenfluss

```
User Input → RAG Context → MKC Compile (Text → MCXF)
→ Bridge (Tool Matching) → Optimizer Pipeline (DCE → Fusion → Parallel)
→ MEL Execute (Tool Dispatch) → Feedback Analysis → Memory Store
```

---

## 3. 4-Kernel-Perspektive

Die 7 Layer lassen sich in 4 logische Subkernel gruppieren:

| Kernel | Layer | Verantwortung |
|--------|-------|-------------|
| **L4 Observability** | L7+L6+L5 | Systemüberwachung, Metriken, UI, Replay |
| **L3 Control** | L5+L2 | Entscheidungen, Limits, Konsens, Strategie |
| **L2 Cognitive** | L4 | NL→Plan-Kompilierung, Optimierung |
| **L1 Runtime** | L3+L2 | Ausführung, Prozess-Isolation, Safety |
| **L0 Storage** | L1 | Persistenz, Indizes, State-Recovery |

---

## 4. Capability-First-Architektur

MUSCAL routet nicht nach Modell-Namen, sondern nach **Capabilities**. Jeder Task deklariert, welche Fähigkeit er benötigt (z.B. "memory.read", "tool.math"). Der Scheduler wählt den optimalen Worker basierend auf Capability-Match + MREIL-Score + Resource-Fit.

### Capability Registry (Auszug)

| Capability | Risiko | Beschreibung |
|-----------|--------|-------------|
| memory.read | niedrig | Kontext lesen |
| memory.write | mittel | Kontext schreiben |
| tool.math | niedrig | Mathematische Berechnung |
| tool.search | mittel | Informationssuche |
| tool.network | hoch | Externer IO |

---

## 5. MPIR Compiler Pipeline

```
Prompt (NL) → Tokenize → Parse AST → Normalize → Validate → Compile MPIR → Optimize → Execution DAG
```

Der Compiler transformiert natürliche Sprache in einen ausführbaren, validierten Graphen. Drei Normalisierungsregeln:
- **Intent Canonicalization**: Synonyme → standardisierte Tags
- **Operation Flattening**: Verschachtelte Befehle → lineare Nodes
- **Context Binding**: Implizite Referenzen → explizite Kanten

---

## 6. State Equivalence Layer (SEL)

SEL definiert eine formale Äquivalenzrelation über Systemzustände:

```
s1 ~ s2  ⇔  CanonicalState(s1) = CanonicalState(s2)
```

Zwei Event-Streams sind äquivalent, wenn ihre gefalteten Zustände äquivalent sind. Dies ermöglicht:
- Deterministischen Vergleich von Execution Runs
- Replay-Validierung
- State-basiertes Debugging

---

## 7. MREIL Evaluation System

Fünf Dimensionen der Systembewertung:

| Dimension | Bedeutung | Zielwert |
|-----------|-----------|----------|
| Memory | Kontext-Erhalt | >0.9 |
| Reasoning | Korrekte Schlussfolgerungen | >0.8 |
| Execution | Latenz | <100ms |
| Integrity | Abweichungsfreiheit | 1.0 |
| Load | Systemauslastung | <0.7 |

---

## 8. Produktionssystem (6-Layer)

```
L6: UI / Dashboard
L5: API Gateway (Auth, Rate-Limit)
L4: Policy Engine (Capability-Check)
L3: Sandbox (Process-Isolation, Podman)
L2: Execution Graph (DAG-Runtime, VM)
L1: Storage / Persistence (SQLite, Snapshots)
```

---

## 9. Status & Roadmap

| Bereich | Status |
|---------|--------|
| Core Pipeline | ✅ Working |
| OS Layer | ✅ Working |
| Optimizer | ✅ Working |
| API Server | ✅ Working |
| Safety System | ✅ Working |
| Consensus | ⚠️ Stubs (~80 Dateien) |
| Distributed | ⚠️ Stubs |
| Evolution | ⚠️ Stubs |
| Tests | ❌ Keine |
| CI/CD | ❌ Keine |
| Frontend | ⚠️ Prototyp |

**Nächste Meilensteine:**
1. Execution Graph Compiler (MAS-0301) implementieren
2. System Spine (system_spine.py) als Runtime-Komponente bauen
3. SEL als Bridge zwischen L2 Cognitive und L0 Storage
4. MAS-VM für determinstische Replay-Fähigkeit
5. Capability Registry in Produktion
