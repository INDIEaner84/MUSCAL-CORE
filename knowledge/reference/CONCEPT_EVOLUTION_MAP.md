# CONCEPT_EVOLUTION_MAP — MUSCAL/ALITA concept definitions and evolution

**Audit:** MUSCAL-KRA-2026-08-01 · **Layer:** STRUCTURED KNOWLEDGE / INFERRED
**Purpose:** Base for the later Temporal Analysis (20-doc plan, doc 11) and Knowledge Graph (doc 04).

---

## 1. Concept Register

| Concept | First observed | Current definition (evidence) | Evolution |
|---------|---------------|-------------------------------|-----------|
| **MUSCAL** (Multi-Statement Cognitive Automation Language / Multi-Scale Context-Aware Learning) | 2026-05-27 ("MUSCAL Mode Aktivierung", S1) | "Modular cognitive operating system transforming natural language into structured execution" (M-ROOT); "kognitives Betriebssystem" (M-0.7) | two name expansions coexist; formal spec work 29.07 (S2) defines it as Cognitive OS + Distributed Multi-Agent Runtime + Governance Platform + Declarative Cognitive Language + Trust-preserving Execution Environment |
| **ALITA** | 2026-07-07 ("ALITA Design Book Konzept", S1) | desktop agent + HUD (PyQt), "Knowledge Architecture Engine" for MUSCAL (S1 OC Session-State Test 20.07) | active project name; GUIs (Muskel Alita 23.07) + external validation (23.07) |
| **MUSCAL CORE** | 2026-06 (kernel design milestone v0.1, ROADMAP) | v0.7 "Stable Prototype", ROADMAP v0.7 06.07; v0.8 changelog exists; audits through MC-TC-007 (31.07) | 0.1→0.7 rapid (June–July 2026); v0.8 undocumented in manual |
| **MREIL** | ≤2026-06 (in MPP pipeline list, S2 21.07) | evaluation stage of Prompt Pipeline (16-stage MPP: Intent Parser → … → MREIL Evaluator → Knowledge Distiller → Response Compiler) | stable concept within MPP |
| **MPP — MUSCAL Prompt Pipeline** | ≤2026-06-30 (S1 "MUSCAL Architektur Spezifikation") | 16 pipeline stages (documented in S2 21.07) | stable |
| **MCXF** | ≤2026-07-07 (S1 "MCXF Spezifikation und Bewertung") | interpreter superseded by compiler (D-001, 04.07) | 🗑 abandoned as execution path; still documented (spec/MSCE-SPECIFICATION_v0.1.md) |
| **MPES / MPIR** | ≤2026-07 (S1 keyword counts 64/379) | event/IR related modules within MUSCAL spec family | partially specified (see S2 "Spezifikation offen") |
| **EventBus** | v0.7 bounding (D-005) | "was passiert gerade?" (S2 21.07) | stable |
| **EventStore** | 2026-07-19/20 (commits b9b17f3, 763f6bf) | "was ist dauerhaft passiert?" — append-only, replay (S2 21.07 + code) | new layer, certified (MC-TC-004) |
| **AuditLog** | 2026-07-21 (S2) | "was muss nachvollziehbar protokolliert werden?" | concept stage |
| **Cognitive Kernel** | 2026-07-25 (S2 proposal) | authoritative separation of thinking vs acting; signed actions; edge hardware | planned (chat-only) |
| **Graph-OS** | ≤2026-07-23 (S2 Meta-UI, GUI Vorlage) | GraphState/SphereState visualization layer — **NOT certified, in-memory only** (MC-TC-007, 31.07) | active, with P0 blocker |
| **MUSCAL 2.0** | 2026-07-25 (S2 tournament) | hybrid architecture (durable execution + hierarchical multi-agent + event-driven verification) | planned (chat-only) |
| **MUSCAL Agent System** | 2026-07-21 (S2 orchestration) → 30.07 spec | Agent = role (Identity, CapabilitySet, Constraints, MemoryAccess, ToolAccess, Permissions, EvaluationMetrics); P1–P5 | evolving, spec v1.0 draft chat-only |
| **Cognitive Compiler** | 2026-07-30 (S2 spec) | prompts as declarative cognitive programs → semantic AST → CIR → agent graph | planned (chat-only) |
| **Trust Core** | ≤2026-07-23 (E3.2) | minimal set: identity, execution state, event persistence, verification | implemented + certified MC-TC-003F/004 |
| **KIR** | ≤2026-07-07 (S1 "MUSCAL KIR Spezifikation") | Cognitive Memory & Long-Term Learning architecture (CHECKPOINT 31) | documented in S1/S2 chats; repo status unclear |
| **HDR-001..004** | 2026-07-20 (PROJECT_STATE) | Architecture Council / PMGA / Master Coding AI / Requirements — HDR-001 blocks 3 | open since 20.07 |

## 2. Concept Stability

| Stability | Concepts | Evidence |
|-----------|----------|----------|
| **Stable core** (unchanged since 06/07.2026) | MUSCAL CORE layers (7-layer), EventBus, plugin model (features/), capability-first routing, immutability contract | ADRs D-001..D-007 all APPLIED/ACCEPTED [C0] |
| **Evolving** (definition shifting) | Agent system (21.07 idea → 30.07 spec), MUSCAL 2.0 direction (25.07), Graph-OS (23–31.07), Compiler (interpreter → graph compiler → cognitive compiler) | S2 chat evolution [C2] |
| **Abandoned** | MCXF interpreter execution path, `simulation_mode: bool`, kernel_core.py (deleted, PROJECT_STATE) | ADR-001, OVERRIDE MC-TC-003B [C1] |
| **Reintroduced/renamed** | "Prompt AST" (61 hits S1) → later "Semantic AST / Cognitive Intermediate Representation" (S2 30.07) | [C2] |

## 3. Temporal Map (wave summary)

| Window | Knowledge wave | Sources |
|--------|----------------|---------|
| 2024-02 → 2025-12 | pre-MUSCAL: diverse topics (audio, writing, relationships, Linux, jailbreak/ethics, music) | S1 titles |
| 2026-01 → 2026-04 | gap/low activity; transition | S1 monthly counts |
| 2026-05 | MUSCAL activation ("MUSCAL Mode Aktivierung") | S1 |
| 2026-06 | architecture strategy, milestones, definition discourse, loop v2 audit, compiler determinism | S1 |
| 2026-07-01..15 | RFC/KIR/Execution-Graph/22MUSCAL wave; export cut | S1 |
| 2026-07-16..22 | consolidation, OC session tests, reconciliation report, agent orchestration | S2 |
| 2026-07-23..25 | E3.2 closure, external validation, MUSCAL 2.0 tournament, Cognitive Kernel proposal | S2 |
| 2026-07-27..31 | reality closure, execution-gap benchmark, formal spec, compiler/agent specs, audit status | S2 |

## 4. Open Concept-Level Questions

| Question | Evidence | Type |
|----------|----------|------|
| Is "MUSCAL" an OS, a language, or a framework? (all three claimed) | M-ROOT vs formal spec | Naming/definition conflict |
| Is "ALITA" the same as "MUSCAL CORE" frontend or a separate project? | S1 OC Session-State vs repo | Identity ambiguity |
| Where does KIR fit relative to Memory architecture? | S1 KIR spec vs `docs/memory/` | Spec layering |
| Is Graph-OS a separate layer or the future frontend of MUSCAL 2.0? | S2 23–31.07 | Architecture |

---

*Provenance: S1 conversation titles + keyword hits; S2 headers/content; repo ROADMAP/DECISIONS/PROJECT_STATE; git log. Concept definitions marked C0 where documented, C2 where chat-derived.*
