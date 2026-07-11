# Alita / MUSCAL Wissensbasis

## 1. Was ist Alita/MUSCAL?

Alita/MUSCAL ist kein Framework und keine Bibliothek – es ist ein **Cognitive Operating System**. Anders als klassische KI-Frameworks (LangChain, CrewAI, AutoGen) die Agenten als Bibliotheken bereitstellen, hat MUSCAL einen eigenen **Kernel** mit:

- **Prozess-Isolation** (IPC zwischen Agenten, keine shared Memory)
- **Event-Sourced Ground Truth** (jeder Zustandswechsel ist ein Event im Stream)
- **Deterministischem L1-Routing** (0.44 µs median, Regel-basiert, kein LLM)
- **Hard Rules** (vom Menschen definierte, unveränderliche Architekturgrenzen)

Der Kernel läuft auf Consumer-Hardware (GTX 1080 Ti, 11 GB VRAM) und ist für den Dauerbetrieb als lokaler KI-Co-Pilot ausgelegt.

## 2. Die MUSCAL-Philosophie

**Kernel-First, nicht Compiler-First.**  
Die ursprüngliche Architektur setzte auf einen Compiler als Zentrum (Dokumente kompilieren → ausführen). Die Arena-Analyse mit 4 KI-Modellen (Claude, ChatGPT, Kimi, Mimo) ergab: Der Kernel muss zuerst existieren, der Compiler ist nur eine Schicht darüber.

**Single-Writer-Prinzip.**  
Nur genau ein Thread (der WriterThread) darf Daten schreiben. Leser greifen immer auf den konsistenten Snapshot zu. Das verhindert Race Conditions und macht das System deterministisch replizierbar.

**Event vs. Reasoning Stream.**  
- `stream='event'`: Der Ground Truth. Jedes Event ist ein state-changing Faktum. Replayable.  
- `stream='reasoning'`: Hat KEINEN State-Effekt. Gedanken, Analysen, LLM-Antworten. Darf nie in den Event-Stream schreiben.

**Cross-AI-Development.**  
MUSCAL wurde durch eine bewusste KI-Arena entwickelt: 4 Modelle mit unterschiedlichen Stärken – Claude (Diagnose), ChatGPT (Spezifikation), Mimo (ausführbarer Code), Kimi (Meta-Evaluation). Kein einzelnes Modell kann alles.

## 3. Hard Rules (RULE-1 bis RULE-5)

Diese Regeln sind MENSCHEN-DEFINIERT und dürfen von keiner KI überschrieben werden:

| Regel | Beschreibung |
|-------|-------------|
| **RULE-1** | Single-Writer: Nur genau ein Thread (WriterThread) darf in den Event-Stream schreiben |
| **RULE-2** | LLM-Sanitizer: Jeder Input an ein LLM muss durch `validate_no_injection()` |
| **RULE-3** | Gate-Check: Tasks werden atomar geprüft (Intent → Gate → Execution) |
| **RULE-4** | Reasoning kein State: Reasoning-Stream darf nie den Event-Stream beeinflussen |
| **RULE-5** | Deterministisches L1: L1-Routing muss in <1 µs rule-basiert sein, kein LLM |

## 4. Architektur: 4 Layer (L1–L4)

### L1 – Execution (Kernel)
- **WriterThread**: Single-Writer, ~21 Events/sec, WAL-basiert (Write-Ahead Log)
- **Router**: Rule-basiert (0.44 µs), leitet Tasks an zuständige Worker
- **Gate**: Prüft jede Intent auf Blocking-Unknowns vor Ausführung
- **Worker**: LLM-Prozesse (Qwen, DeepSeek R1, SmolLM2) mit isolierten Contexts

### L2 – Observation
- **ObservationLoop**: 5-Sekunden-Tick, überwacht Gate, Worker, Confidence
- **Governance**: Limit-Checks (max_iterations=25), Usage-Tracking, Violations
- Löst Alarm aus bei: Gate geschlossen, stuck Worker, Confidence-Drift, Governance-Violations

### L3 – Reflection
- **DeepSeek R1 8B**: Wird on-demand geladen (keep_alive=300s)
- Nur für komplexe Analyse, Architektur-Entscheidungen, Reflexion
- Kein Einfluss auf L1/L2 – reiner Reasoning-Kontext

### L4 – Projection
- **Flask API** (:5050): REST-Endpoints für Chat, Events, State, Governance
- **WebSocket** (:9090): EventDaemon für Echtzeit-UI-Updates
- **Dashboard / IDE** (:5050/ide): React-basiertes Frontend
- **Tauri HUD**: Overlay-Fenster (transparent, immer oben, ohne Rahmen)

## 5. Single-Writer-Prinzip (einzigartig)

Anders als die meisten KI-Frameworks (die auf Actor-Modelle oder shared-state setzen) verwendet MUSCAL einen **zentralen WriterThread**:

```
Worker → WriterQueue → WriterThread (serialisiert) → DB (SQLite + WAL)
```

Vorteile:
- **Keine Race Conditions**: Egal wie viele Worker gleichzeitig schreiben – die Serialisierung macht es deterministisch
- **Replayability**: Der WAL (Write-Ahead Log) kann jeden Zustand zu jedem Zeitpunkt rekonstruieren
- **Backup**: Einfaches Kopieren der DB + WAL = kompletter System-State

Nachteile (bewusst in Kauf genommen):
- Maximaler Write-Durchsatz = ~100 Events/sec (auf SQLite beschränkt)
- Lese-Zugriffe sind parallel (unbegrenzt), nur Schreiben ist serialisiert

## 6. CQRS/Hybrid – Event Stream vs. Reasoning Stream

MUSCAL implementiert ein modifiziertes CQRS (Command Query Responsibility Segregation):

**Event-Stream** (Command Side):
- `event_type` + `actor` + `domain` + `layer` + `payload`
- Wird persistent in SQLite gespeichert (muscal.db)
- Nur der WriterThread darf schreiben
- Alle Zustandsänderungen sind Events

**Reasoning-Stream** (Query Side):
- LLM-Antworten, Analysen, Gedankengänge
- KEIN State-Effekt
- Darf nicht in der DB persistiert werden (außer als Log)
- Kann parallel gelesen/verarbeitet werden

Das ist anders als z.B. LangGraph (das State-Graphen zentral verwaltet) oder AutoGen (das Agent-Chats als zentrales Konzept hat).

## 7. Consumer Hardware Optimization

MUSCAL ist von Grund auf für **GTX 1080 Ti (11 GB VRAM)** optimiert:

| Modell | VRAM | Status |
|--------|------|--------|
| Qwen 3.5 DeepSeek Flash | ~9 GB | Dauerhaft geladen (keep_alive=-1) |
| DeepSeek R1 8B | ~6 GB | On-Demand (keep_alive=300s) |
| SmolLM2 360M | ~300 MB | Für rasche Vorlagen |
| Qwen 3 0.6B | ~500 MB | SLM für einfache Chats |

**Warum Dense statt MoE?**  
MoE-Modelle (Mixture of Experts) wie DeepSeek V2 brauchen mehr VRAM pro Batch als Dense-Modelle. Für 11 GB VRAM sind Dense-Modelle effizienter. Qwen 3.5 DeepSeek Flash ist eine optimierte Architektur speziell für Consumer-GPUs.

## 8. Self-Evolution

Alita lernt aus Fehlern:

1. Ein Task schlägt fehl oder ein Command wird falsch interpretiert
2. Die Korrektur wird (optional) in ChromaDB als Vektor gespeichert
3. Bei ähnlichen Anfragen wird der Korrektur-Pfad automatisch in den Context eingewoben

Der Korrektur-Pfad enthält:
- Ursprüngliche Anfrage (Embedding)
- Falsche Interpretation
- Korrektur durch den User
- Lösung

Das ist anders als Fine-Tuning: Es wird kein Modell neu trainiert, sondern der Kontext dynamisch angereichert.

## 9. MUSCAL Compiler

Der MUSCAL-Compiler übersetzt `.muscal`-Dokumente in ausführbare Tasks:

**MUSCALParser:**
- Extrahiert Frontmatter (YAML-Header mit metadata, routing, governance)
- Parst den Machine-Layer (strukturierte Anweisungen zwischen `---`)
- Erzeugt einen DOM-ähnlichen Baum

**MUSCALCompiler:**
- Hash-basierter Cache (gleiches Dokument → gleicher Output)
- Generiert Worker-Stubs und ausführbare Tasks
- Write-Back: Kompilierte Tasks werden direkt in die DB geschrieben

Das `.muscal`-Format ist das Herzstück der menschlichen KI-Zusammenarbeit:  
Menschen schreiben semi-strukturierte Dokumente → der Compiler macht ausführbare Einheiten daraus.

## 10. Unterschied zu anderen Frameworks

| Aspekt | MUSCAL | LangChain | CrewAI | AutoGen |
|--------|--------|-----------|--------|---------|
| **Kernel** | Eigenständiger Cognitive OS Kernel | Kein Kernel | Kein Kernel | Kein Kernel |
| **State** | Event-Sourced (WAL+SQLite) | Shared Memory | In-Memory | In-Memory |
| **Writer** | Single-Writer (deterministisch) | Beliebig | Beliebig | Beliebig |
| **IPC** | Ja (Prozess-Isolation) | Nein | Nein | Nein |
| **Router** | 0.44 µs, rule-basiert | LLM-basiert | Fest verdrahtet | Fest verdrahtet |
| **Compile** | Ja (.muscal → Tasks) | Nein | Nein | Nein |
| **Overlay** | Ja (Tauri HUD) | Nein | Nein | Nein |
| **Lokal** | Vollständig (nur ollama) | Cloud bevorzugt | Cloud bevorzugt | Cloud bevorzugt |
| **Hardware** | GTX 1080 Ti optimiert | Hoch | Hoch | Hoch |

**Das Alleinstellungsmerkmal:** MUSCAL verbindet OS-Konzepte (Kernel, IPC, Prozess-Isolation, Single-Writer) mit KI. Es ist kein Framework für KI – es ist ein Betriebssystem, in dem KI als Bürger erster Klasse läuft.

## 11. Kompilieren / Build

Das Projekt besteht aus einem Python-Backend und optionalem Tauri-Frontend:

| Komponente | Befehl | Output |
|------------|--------|--------|
| Runtime Server | `python runtime_server.py` (bzw. `python runtime/main.py`) | Flask :5050 + WS :9090 |
| Tauri HUD | `cd muscal-hud && npm install && npx tauri build` | Overlay-Binärdatei |
| Dashboard | via Server `/api/health` → `/muscal_dashboard.html` | HTML/CSS/JS |
| IDE | via Server `/ide` → `/muscal_ide.html` | 395 kB React-basiert |
| Tests | `python3 -m pytest test_*.py -v` | Alle Tests |

## 12. Governance

Governance ist der zentrale Regel-Mechanismus des Kernels:

- **Limits**: max_iterations (25), max_tokens, rate_limits
- **Usage-Tracking**: Wie viele Iterationen pro Session/Agent
- **Violations**: Überschreitungen werden geloggt und optional bestraft
- **Hard Resets**: Nur über dediziertes API-Ende (`/api/governance/reset`)
