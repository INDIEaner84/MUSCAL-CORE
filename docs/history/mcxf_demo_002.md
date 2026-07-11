MCXF v0.3

00_IDENTITY:
- document_id: MCXF-002
- version: 0.3
- generated_from: "Chat-Log: MKC + MEL + RAG feature discussion"
- generator: "deepseek-v4-flash-free"

01_SUMMARY:
- User wants a system that compiles chat into structured knowledge.
- Assistant proposes MKC with MCXF output format.
- User requires task execution via MEL.
- Assistant confirms MEL handles deterministic tool execution.
- User adds requirements for conflict detection and RAG support.
- Assistant outlines role separation: RAG stores memory, MKC compiles knowledge.

02_DECISIONS:
- MKC is the compiler that transforms raw chat into structured MCXF output.
- MEL is the execution layer for tool calls, separate from MKC.
- RAG is responsible for memory storage, not compilation.
- MCXF is adopted as the structured knowledge format.
- Conflict detection is a required feature of MKC.

03_ARCHITECTURE:
- User Input → MKC (compiler) → MCXF document
- MCXF → MEL (executor) → tool calls → results
- RAG (memory store) ←→ MKC (knowledge injection)
- MKC and RAG are separate modules with distinct responsibilities.

04_GLOSSARY:
- MKC: Modular Knowledge Compiler — transforms chat into structured knowledge.
- MCXF: MUSCAL Context Exchange Format — structured document format.
- MEL: Modular Execution Layer — runs deterministic tool sequences.
- RAG: Retrieval-Augmented Generation — stores and retrieves memory.

05_CONSTRAINTS:
- None explicitly stated.

06_TASKS:
- [STATED] Build MKC with MCXF output format.
- [STATED] Implement MEL for tool execution.
- [STATED] Add conflict detection to MKC.
- [STATED] Add RAG support for memory storage.

07_CONFLICTS:
- None detected.

08_OPEN_QUESTIONS:
- UNKNOWN — No details on conflict detection algorithm were discussed.
- UNKNOWN — No details on RAG implementation (embeddings, retrieval strategy).
- UNKNOWN — No details on MEL tool registry or execution model.
- UNKNOWN — MCXF section schema not fully defined.

09_EXECUTION_MODEL:

Pipeline (deterministisch, 6 Stufen):

1. RAW → NORMALIZE
   - Whitespace trim, UTF-8 normalisieren
   - Turn > / User: / Assistant: in standardisiertes Role-Format umwandeln
   - Output: Liste von {"role": "user"|"assistant", "content": "str", "turn_index": int}

2. NORMALIZE → SEGMENT
   - Split nach Role-Wechsel (User ↔ Assistant)
   - Jedes Segment = {"role", "content", "turn_index"}
   - Segment-Grenzen = harte Trennpunkte für Extraktion

3. SEGMENT → EXTRACT
   - Pattern-Matching pro Segment gegen Signal-Wörter:
     - "should/must/need/will" → DECISION
     - "we build/implement/create/add" → TASK
     - "separate/distinct/split/responsibility" → ARCHITECTURE
     - "requires/constraint/only/never" → CONSTRAINT
     - "define/called/means/is a" → GLOSSARY
   - Jeder Treffer wird als {"section": str, "text": str, "turn": int} notiert
   - Mehrfachtreffer pro Segment möglich

4. EXTRACT → RESOLVE
   - Deduplizieren: gleicher Wortlaut + gleiche Sektion → 1 Eintrag
   - Konfliktprüfung (siehe 12_CONFLICT_MODEL)
   - Turn-Reihenfolge = Priorität (späterer Turn überschreibt früheren bei Konflikt)
   - Bei Gleichstand: ASSISTANT gewinnt vor USER

5. RESOLVE → STRUCTURE
   - Einsortieren der extrahierten Einträge in MCXF-Sektionen 01-08
   - Fehlende Sektionen → "None detected" (bei 07_CONFLICTS)
   - Fehlende Information → "UNKNOWN — <reason>" (bei 08_OPEN_QUESTIONS)

6. STRUCTURE → VERIFY
   - Output muss alle 13 MCXF-Sektionen enthalten (00-12)
   - Jede Sektion muss nicht-leeren Inhalt haben
   - Bei Fehler: Output wird verworfen, Rohdaten landen in 08_OPEN_QUESTIONS

Determinismus-Regel:
- Gleicher Input → immer gleicher Output (keine Zufallskomponenten)
- LLM-Variante (v0.4+) erlaubt temperatur=0 + fixed seed

10_TOOL_SCHEMA:

TOOL_REGISTRY Format (pro Eintrag):

{
  "<tool_name>": {
    "fn": <callable>,
    "input_schema": {"<param>": "<type>"},
    "output_schema": {"<field>": "<type>"},
    "sandbox": { "<rule>": "<value>" }
  }
}

Definierte Tools:

1. filesystem.write
   - input_schema: {"path": "str", "content": "str"}
   - output_schema: {"status": "str", "path": "str"}
   - sandbox: {"allowed_paths": ["/tmp/*", "./storage/*"], "max_size_bytes": 1048576}
   - constraint: path darf nicht existierende Datei überschreiben ohne explizite Freigabe

2. math.add
   - input_schema: {"a": "int|float", "b": "int|float"}
   - output_schema: {"result": "int|float"}
   - sandbox: {"pure": true, "no_side_effects": true}
   - constraint: keine IO, keine Exception außer TypeError

3. console.print
   - input_schema: {"message": "str"}
   - output_schema: {"printed": "str"}
   - sandbox: {"side_effect": "stdout", "max_length": 4096}

Execution Constraints:
- Jeder Tool-Call wird vor Dispatch gegen input_schema validiert (Type-Check)
- Output wird nach Ausführung gegen output_schema validiert
- Sandbox-Verstoß → ToolException → Step wird skippped → Fehler in Result vermerkt
- Unbekanntes Tool → Exception, gesamter Plan schlägt fehl

11_RAG_SPEC:

Retrieval Strategy (Stage 1 — simple):
- Chronologischer Retrieval: beim Start von MKC werden die letzten N logs.jsonl-Einträge prepended
- N = 10 (konfigurierbar via config.max_context_logs)
- Keine Embeddings, keine semantische Suche
- Relevanz = chronologische Nähe (je neuer, desto relevanter)

Context Injection Point:
- Vor SEGMENT-Step (Stufe 2 der Pipeline)
- Format: "<context>\\n---\\n<raw_input>"
- context = concatenated "{role}: {content}" der letzten N Einträge

Storage Assumptions:
- memory.db speichert plan+result pairs → wird von RAG nicht gelesen, nur von MEMORY
- logs.jsonl ist die RAG-Quelle (append-only, zeilenweise JSON)
- Log-Retention: unbegrenzt [SPECULATION: später rotation via max_size oder max_age]

Future RAG (v0.4+) [SPECULATION]:
- embedding column in memory.db: vector(float, 384)
- cosine-similarity query statt chronologisch
- retrieval threshold: min_similarity = 0.75
- context injection: top-3 matches statt last N

12_CONFLICT_MODEL:

Detection Rules (angewandt auf EXTRACT-Output vor RESOLVE):

1. SAME_SECTION_DIFF_VALUE
   - Zwei DECISIONS mit gleichem Subjekt aber gegensätzlichem Wert
   - Signal: "X is A" vs "X is not A" / "X should Y" vs "X should not Y"
   - Score: 0.8
   - Beispiel: "MKC is rule-based" vs "MKC is LLM-driven" → CONFLICT

2. TASK_OVERRIDE_DECISION
   - Späterer TASK widerspricht früherer DECISION
   - Signal: DECISION "no deps" + TASK "install openai"
   - Score: 0.9
   - Beispiel: DECISION "no external dependencies" + TASK "add pip install openai" → CONFLICT

3. ROLE_MISMATCH
   - User sagt A, Assistant sagt non-A (gleicher Turn-Bereich)
   - Signal: User: "we need X" + Assistant: "X is not needed"
   - Score: 0.5
   - Beispiel: User: "RAG should store memory" + Assistant: "RAG is for retrieval, not storage" → CONFLICT

4. UNDEFINED_TERM
   - Begriff wird in DECISION oder TASK verwendet aber nicht in GLOSSARY definiert
   - Score: 0.3 (warning, kein harter Konflikt)
   - Konsequenz: Eintrag in OPEN_QUESTIONS, kein Block

Scoring Method:
- Jeder Konflikt erhält score ∈ [0.0, 1.0]
- Höherer Score = schwerwiegender
- Konflikte mit score < 0.3 werden ignoriert (Rauschen)

Resolution Strategy:
- Bei Konflikt: höherer Score gewinnt
- Bei Gleichstand: späterer Turn gewinnt
- Wenn Turn ebenfalls gleich: ASSISTANT gewinnt vor USER
- Ergebnis-Konflikt wird in 07_CONFLICTS dokumentiert:
  Format: "- Score X.X: <A> vs <B> → resolved to <winner>"
