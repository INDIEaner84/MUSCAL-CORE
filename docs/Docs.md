# MUSCAL CORE — Documentation Map

## Purpose

This document describes EVERY documentation file in the project:
- WHY it exists
- WHAT it is for
- WHO reads it
- Whether it is current

This prevents outdated or historical documents from being
interpreted as current project state.

---

## 🔴 FIRST REQUIRED READING

### `docs/PROJECT_STATE.md`

| Field | Value |
|-------|-------|
| Purpose | Current project status (phase, score, known TD) |
| Audience | EVERYONE entering the project (including OpenCode) |
| Status | ✅ Authoritative, current |
| Updated | At every milestone |

**Why?** — First document every OpenCode session MUST read.
Defines current state and prevents old audits from being
interpreted as truth.

> Rule: PROJECT_STATE.md takes precedence over all historical documents.

---

## 🏛️ ARCHITECTURE & BASELINE

### `docs/TECHNICAL_BASELINE.md`

| Field | Value |
|-------|-------|
| Purpose | Authoritative architecture description |
| Audience | Developers, architects, OpenCode |
| Status | ✅ Authoritative |
| Updated | At architecture changes (ADR) |

**Why?** — Defines the ONLY valid view of the current architecture.

> Rule: TECHNICAL_BASELINE.md takes precedence over
> ARCHITECTURE_BLUEPRINT.md and SYSTEM_DESIGN.md.

### `docs/ARCHITECTURE.md`

| Field | Value |
|-------|-------|
| Purpose | Overview diagram, layer boundaries, component interaction |
| Audience | New team members, architects |
| Status | ✅ Current |
| Updated | At ADR changes |

### `docs/DECISIONS.md`

| Field | Value |
|-------|-------|
| Purpose | Chronological overview of all architecture decisions |
| Audience | Developers, new session contexts |
| Status | ✅ Current |
| Updated | At new ADRs |

**Why?** — Prevents architecture decisions from being lost or
accidentally reversed.

### `docs/PROJECT_CHECKPOINTS.md`

| Field | Value |
|-------|-------|
| Purpose | Milestone protocol (what was achieved when) |
| Audience | Developers, management |
| Status | ✅ Current |
| Updated | At every milestone |

### `docs/ROADMAP.md`

| Field | Value |
|-------|-------|
| Purpose | Next milestones, priorities, planned features |
| Audience | Management, developers |
| Status | ✅ Current |
| Updated | After each milestone |

---

## ⚙️ GOVERNANCE

### `spec/IMMUTABILITY_CONTRACT.md`

| Field | Value |
|-------|-------|
| Purpose | Defines boundaries between Core (immutable) and Features (plugin) |
| Audience | All developers, OpenCode |
| Status | ✅ Authoritative |
| Updated | Only via ADR + override |

### `spec/PLUGIN_API.md`

| Field | Value |
|-------|-------|
| Purpose | Complete Plugin SDK documentation (288 lines) |
| Audience | Plugin developers, feature authors |
| Status | ✅ Current |
| Updated | At plugin API changes |

**Why?** — All extensions go through `features/` as plugins.
Without this API doc, no correct plugins can be written.

### `.opencode/SESSION_RULES.md`

| Field | Value |
|-------|-------|
| Purpose | Behavior rules for every OpenCode session |
| Audience | OpenCode (auto-read) |
| Status | ✅ Authoritative |
| Updated | As needed |

### `specs/ORDER.md`

| Field | Value |
|-------|-------|
| Purpose | RFC/ADR governance: rules for specification and implementation |
| Audience | Architects, RFC authors |
| Status | ✅ Authoritative |
| Updated | Only via new ADR |

### `docs/ANLAGE_PLAN.md`

| Field | Value |
|-------|-------|
| Purpose | Build plan for creating the RFC/ADR/Blueprint documents |
| Audience | Documentation team |
| Status | 📋 Historical (completed) |
| Updated | Not active |

**Why?** — Documents HOW the RFC/ADR landscape was built.
Useful as reference but no longer active.

---

## 📜 HISTORICAL DOCUMENTS

### `docs/history/`

All documents in this directory are NOT current.
They serve exclusively as reference and consultation archive.

| File | Contains | Why here? |
|------|----------|-----------|
| `architecture_blueprint_v0.5.md` | Management view of architecture | Outdated — mentions "0 tests" |
| `system_design_v0.5.md` | IEEE 1016 System Design | Outdated — mentions "global mutable state" |
| `opencode_prompts/` | 6 GPT prompt dumps | Archived session artifacts |
| `core_immutability_v1/` | CORE_IMMUTABILITY CONTRACT | Backup copy |

**Why historical?**
These documents are valuable for:
- Tracing architecture decisions
- Understanding WHY certain changes were needed
- But they must NOT be interpreted as current project state

> 🔴 RULE: If a historical document contradicts a baseline document,
> the baseline takes precedence.

---

## 📦 EXTERNAL DOCUMENTS

### `white-paper/MUSCAL_CORE_WHITEPAPER.md`

| Field | Value |
|-------|-------|
| Purpose | External communication (customers, partners, investors) |
| Audience | External (no code, no jargon) |
| Status | ✅ Current |
| Updated | At major releases |

### `specs/rfcs/MAS-XXXX.md`

| Field | Value |
|-------|-------|
| Purpose | MAS-RFC series (specifications) |
| Audience | Architects, developers |
| Status | 📋 Per RFC (DRAFT → FINAL) |

### `specs/adrs/ADR-XXX.md`

| Field | Value |
|-------|-------|
| Purpose | Architecture Decision Records |
| Audience | Architects |
| Status | ✅ Final (irrevocable per ORDER.md Rule 2) |

---

## SUMMARY TABLE

| Category | Document | Authoritative? | Audience | Currency |
|----------|----------|---------------|----------|----------|
| 🔴 Status | `PROJECT_STATE.md` | ✅ Yes | Everyone | current |
| 🏛️ Baseline | `TECHNICAL_BASELINE.md` | ✅ Yes | Developers | current |
| 🏛️ Decisions | `DECISIONS.md` | ✅ Yes | Developers | current |
| 🏛️ Checkpoints | `PROJECT_CHECKPOINTS.md` | ✅ Yes | Developers | current |
| 🏛️ Architecture | `ARCHITECTURE.md` | ✅ Yes | Developers | current |
| 🏛️ Roadmap | `ROADMAP.md` | ✅ Yes | Management | current |
| ⚙️ Governance | `spec/IMMUTABILITY_CONTRACT.md` | ✅ Yes | Developers | current |
| ⚙️ Plugin API | `spec/PLUGIN_API.md` | ✅ Yes | Plugin authors | current |
| ⚙️ Session | `.opencode/SESSION_RULES.md` | ✅ Yes | OpenCode | current |
| ⚙️ Order | `specs/ORDER.md` | ✅ Yes | Architects | current |
| 📜 History | `docs/history/*` | ❌ No | Reference | outdated |
| 📦 External | `white-paper/*` | — | External | current |
| 📦 RFCs | `specs/rfcs/*` | ✅ Yes | Developers | per RFC |
| 📦 ADRs | `specs/adrs/*` | ✅ Yes | Architects | final |
