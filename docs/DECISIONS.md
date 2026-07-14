# MUSCAL CORE — Architecture Decisions

Chronological overview of all architecture decisions.

---

## 2026-07-04 — ADR-001: Execution Graph Compiler instead of Interpreter

**Decision:** Build an Execution Graph Compiler (MAS-0301) instead of
improving the existing MCXF interpreter.

**Rationale:** Interpreter had 3s+ latency at 50+ tasks.
Compiler estimated at <50ms.

**See:** `spec/ADR-001-kernel.md`, `archive/history/rfcs/MAS-0301.md`

---

## 2026-07-04 — ADR-002: Layer Architecture with Spine Validation

**Decision:** Adopt a 7-layer architecture (L0 Storage - L6 Frontend)
with 4 sub-kernels (Runtime, Cognitive, Control, Observability).

**Rationale:** Rejected flat architecture in favor of strict
layer separation with System Spine validation for event transitions.

**See:** `spec/ADR-002-memory.md`

---

## 2026-07-04 — ADR-003: Capability-First instead of Model-First

**Decision:** Fully switch to Capability-First routing.
Tasks are routed against capabilities, not model names.

**Rationale:** Model-First violated MAS-0001 Architecture Principles.

**See:** `spec/ADR-003-events.md`, `archive/history/rfcs/MAS-0001.md`

---

## 2026-07-06 — v0.7 Stabilization: Lazy Initialization

**Decision:** Replace all module-level import side effects with lazy init.

**Changes:**
- `memory.py`: `sqlite3.connect()` → lazy `_get_conn()`
- `mel.py`: `SystemAgentRuntime()` → lazy `_get_runtime()`
- `config.py`: `SESSION_ID` → lazy `get_session_id()`

**Rationale:** Import crashes were the #1 deployment blocker.

---

## 2026-07-06 — v0.7 Stabilization: Graph + Memory Bounding

**Decision:** Add hard limits to prevent unbounded growth.

**Limits:**
- Graph: 5000 Nodes / 10000 Edges (FIFO eviction)
- Memory: 10000 rows per table (SQLite DELETE)
- Events: 50000 (in-memory FIFO)

**Rationale:** Prevent OOM in long-running sessions.

---

## 2026-07-06 — v0.7 Stabilization: Plugin Architecture

**Decision:** All new features go through `features/` as plugins.
Core files become immutable.

**See:** `spec/IMMUTABILITY_CONTRACT.md`, `spec/PLUGIN_API.md`

---

## 2026-07-11 — ADR-011: Verification Layer Architecture

**Decision:** Verification Framework wird NICHT in Core-Dateien
implementiert, sondern als Plugin-Schicht in `features/event_sourcing/`.

**Rationale:** Direkte Integration würde 39 Core-Dateien gefährden.
Plugin-basierte Erweiterung schützt Core-Immutability.

**Phases:** 0-Konsolidierung, 1-Event Sourcing, 2-Hash Chains,
3-Replay Engine, 4-Verification & Proof

**See:** `spec/ADR-011-verification.md`,
`docs/VERIFICATION_CONFLICT_ANALYSIS.md`,
`docs/VERIFICATION_FRAMEWORK_PLAN.md`
