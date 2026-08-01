# MSCE Specification v0.1
## Multi-Session Coordination Engine — MUSCAL CORE

**Date:** 2026-07-16
**Status:** PROPOSED
**Scope:** Documentation-only governance layer. No runtime code.

---

## 1. Purpose

MSCE provides structured governance for multi-session coordination. It replaces ad-hoc session tracking with explicit, file-based state management.

**What MSCE solves:**
- Sessions run sequentially (one at a time) but leave state behind
- Next session needs to know: What happened? What's pending? What's blocked?
- Current governance files exist but aren't connected into a workflow

**What MSCE does NOT do:**
- No runtime code
- No automation
- No enforcement beyond file convention
- No modification of existing core files

---

## 2. Architecture

```
MSCE v0.1 (Documentation Layer)
├── SESSION_REGISTRY.md      ← Session tracking (exists, integrate)
├── ACTIVE_TASKS.md          ← Current session's task list
├── WORK_QUEUE.md            ← Pending work across sessions
├── CHECKPOINT_INDEX.md      ← Checkpoint snapshot index
└── HANDOVER_TEMPLATE.md     ← Template for session handover

Existing governance files (unchanged):
├── docs/TASK_BOARD.md       ← Architecture-impact task tracking
├── docs/SESSION_REGISTRY.md ← Session overview (informal)
├── docs/GOVERNANCE_CHECKPOINT.md ← Governance status
└── docs/CHANGE_JOURNAL.md   ← Change log
```

### Relationship to existing files

| MSCE File | Replaces? | Integrates with |
|-----------|-----------|-----------------|
| SESSION_REGISTRY.md | No — consolidates `docs/SESSION_REGISTRY.md` | Git history, CHANGE_JOURNAL |
| ACTIVE_TASKS.md | No — new file | TASK_BOARD.md (tasks with architecture impact) |
| WORK_QUEUE.md | No — new file | TASK_BOARD.md (OPEN tasks), ADR pipeline |
| CHECKPOINT_INDEX.md | No — new file | Git tags, session handovers |
| HANDOVER_TEMPLATE.md | No — new file | SESSION_HANDOVER convention |

---

## 3. Component Specifications

### 3.1 SESSION_REGISTRY.md

**Purpose:** Authoritative record of all sessions with structured metadata.

**Location:** `docs/governance/SESSION_REGISTRY.md`

**Schema:**
```markdown
| Session ID | Date | Status | Duration | Changed Files | Category | Checkpoint | Handover |
|------------|------|--------|----------|---------------|----------|------------|----------|
```

**Status values:**
- `ACTIVE` — Session in progress
- `COMPLETED` — Commit made, handover generated
- `BLOCKED` — Waiting on external dependency
- `ABANDONED` — Stopped without commit

**Category values (controlled vocabulary):**
- `BASELINE` — Initial setup or major reset
- `GOVERNANCE` — Governance layer changes
- `FEATURE` — Feature implementation
- `RECONCILIATION` — Reconciliation engine work
- `ADR` — Architecture Decision Record work
- `MAINTENANCE` — Cleanup, refactoring, documentation
- `AUDIT` — Audit, verification, compliance

**Update rule:** Last entry updated at session end. Previous entries immutable.

**Priority of truth:** Git History → CHANGE_JOURNAL → ADR Records → SESSION_HANDOVER → SESSION_REGISTRY

---

### 3.2 ACTIVE_TASKS.md

**Purpose:** Tasks for the current session only. Cleared at session end.

**Location:** `docs/governance/ACTIVE_TASKS.md`

**Schema:**
```markdown
| Task ID | Description | Status | Lock Level | Est. Impact | Notes |
|---------|-------------|--------|------------|-------------|-------|
```

**Status values:**
- `PENDING` — Not started
- `IN_PROGRESS` — Actively working
- `DONE` — Completed this session
- `BLOCKED` — Cannot proceed (dependency)
- `DEFERRED` — Moved to WORK_QUEUE

**Lifecycle:**
1. Session starts → copy relevant tasks from WORK_QUEUE or TASK_BOARD
2. During session → update status as work progresses
3. Session ends → move incomplete tasks to WORK_QUEUE, clear ACTIVE_TASKS

**Relationship to TASK_BOARD.md:**
- TASK_BOARD tracks tasks with architecture impact and approval requirements
- ACTIVE_TASKS is the working subset for the current session
- ACTIVE_TASKS does NOT track approval status (that's TASK_BOARD's job)

---

### 3.3 WORK_QUEUE.md

**Purpose:** Persistent backlog of work items across sessions.

**Location:** `docs/governance/WORK_QUEUE.md`

**Schema:**
```markdown
| Queue ID | Task ID | Description | Priority | Added | Status | Blocked By |
|----------|---------|-------------|----------|-------|--------|------------|
```

**Priority values:**
- `CRITICAL` — Must be done before next milestone
- `HIGH` — Should be done soon
- `MEDIUM` — Normal priority
- `LOW` — When convenient
- `DEFERRED` — Explicitly postponed

**Status values:**
- `QUEUED` — Waiting to be picked up
- `IN_PROGRESS` — Someone is working on it (moved to ACTIVE_TASKS)
- `BLOCKED` — Cannot start (dependency)
- `DONE` — Completed
- `CANCELLED` — No longer needed

**Update rule:**
- Items added from: ACTIVE_TASKS (deferred), TASK_BOARD (new tasks), manual addition
- Items consumed by: ACTIVE_TASKS (picked up for current session)
- Items promoted from: WORK_QUEUE → TASK_BOARD (when architecture impact identified)

---

### 3.4 CHECKPOINT_INDEX.md

**Purpose:** Index of project checkpoints with session linkage.

**Location:** `docs/governance/CHECKPOINT_INDEX.md`

**Schema:**
```markdown
| Checkpoint | Version | Date | Session ID | Git Reference | Description | Tests Pass |
|------------|---------|------|------------|---------------|-------------|------------|
```

**Git Reference format:**
- Commit hash: `abc1234`
- Tag: `v0.25`
- Branch point: `main@abc1234`

**Relationship to Git:**
- Checkpoint index is a human-readable overlay on Git history
- Git remains the source of truth for actual state
- Checkpoint index adds: session linkage, test status, description

**Update rule:** Updated when a checkpoint is established (typically at session end or milestone).

---

### 3.5 HANDOVER_TEMPLATE.md

**Purpose:** Template for session handover documents.

**Location:** `docs/governance/HANDOVER_TEMPLATE.md`

**Template:**
```markdown
# SESSION HANDOVER — [SESSION_ID]

**Date:** [DATE]
**Duration:** [DURATION]
**Category:** [CATEGORY]

## Session Summary

[1-3 sentences describing what was accomplished]

## Files Changed

| File | Change Type | Reason |
|------|-------------|--------|
| [path] | [NEW/MODIFIED/DELETED] | [why] |

## State Changes

- [What state was modified]
- [What state was created]
- [What state was destroyed]

## Open Items

| Item | Status | Next Action |
|------|--------|-------------|
| [item] | [BLOCKED/DONE/DEFERRED] | [what to do next] |

## Blockers

- [Any blockers encountered]

## Verification

- [ ] Tests pass: [command]
- [ ] Git diff reviewed
- [ ] No core files modified (or override documented)

## Next Session Should

1. [First priority]
2. [Second priority]
3. [Third priority]
```

**Usage:**
- Created at session end (mandatory when files changed)
- Stored in `docs/session_handovers/`
- Referenced by SESSION_REGISTRY
- Read by next session at start

---

## 4. Session Lifecycle with MSCE

```
Session Start
    │
    ├─→ Read PROJECT_STATE.md
    ├─→ Read TASK_BOARD.md
    ├─→ Read WORK_QUEUE.md (pending items)
    ├─→ Read last SESSION_HANDOVER (from docs/session_handovers/)
    ├─→ Populate ACTIVE_TASKS.md (from WORK_QUEUE or TASK_BOARD)
    │
    ├─→ Determine Lock Level
    ├─→ Get Approval (if needed)
    │
    ├─→ Execute Work
    │   ├─→ Update ACTIVE_TASKS.md status
    │   └─→ Update CHANGE_JOURNAL.md
    │
    ├─→ Session End
    │   ├─→ Move incomplete tasks → WORK_QUEUE.md
    │   ├─→ Create SESSION_HANDOVER (from template)
    │   ├─→ Update SESSION_REGISTRY.md
    │   ├─→ Update CHECKPOINT_INDEX.md (if milestone)
    │   ├─→ Clear ACTIVE_TASKS.md
    │   └─→ Git Commit
    │
    └─→ Next Session reads handover
```

---

## 5. File Ownership Rules

| File | Created By | Updated By | Immutable After |
|------|-----------|------------|-----------------|
| SESSION_REGISTRY.md | Any session | Current session (last row only) | Never (append-only) |
| ACTIVE_TASKS.md | Session start | Current session | Session end (cleared) |
| WORK_QUEUE.md | Any session | Current session | Never |
| CHECKPOINT_INDEX.md | Any session | Current session (new rows only) | Never (append-only) |
| HANDOVER_TEMPLATE.md | MSCE creation | Never | Always (template) |

**Append-only files:** SESSION_REGISTRY, CHECKPOINT_INDEX — new rows only, no edits to existing rows.

---

## 6. Migration Path

### Phase 1: Specification (current)
- Create MSCE-SPECIFICATION_v0.1.md
- Create component files with empty schemas
- No behavioral changes

### Phase 2: Adoption (future)
- First session uses MSCE workflow
- Validate template works
- Adjust schemas if needed

### Phase 3: Enforcement (future)
- Governance validator checks MSCE file presence
- Session handover required before commit
- CHECKPOINT_INDEX synchronized with Git tags

---

## 7. Relationship to Existing Governance

```
Existing (stable):
├── AGENTS.md → Core rules, lock levels, write guard
├── SESSION_RULES.md → Session behavior rules
├── GOVERNANCE_CHECKPOINT.md → Governance component status
├── TASK_BOARD.md → Architecture-impact task tracking
├── SESSION_REGISTRY.md → Session overview (informal)
├── CHANGE_JOURNAL.md → Change log
├── LOCK_PROTOCOL.md → Lock level definitions
└── IMMUTABILITY_CONTRACT.md → Core immutability

MSCE v0.1 (new):
├── SESSION_REGISTRY.md → Consolidated, authoritative session record
├── ACTIVE_TASKS.md → Current session working set
├── WORK_QUEUE.md → Persistent backlog
├── CHECKPOINT_INDEX.md → Checkpoint overlay on Git history
└── HANDOVER_TEMPLATE.md → Standardized handover format
```

**Principle:** MSCE extends existing governance. It does not replace or conflict with AGENTS.md, SESSION_RULES.md, or any core governance document.

### Relationship to Knowledge Foundation

MSCE exists within MUSCAL CORE, which is itself evaluated by the Knowledge Foundation (KF v3.1).
KF provides cross-project analysis (5 codebases, 11 sources, 71 decisions) and identifies
MUSCAL CORE as a "Master Candidate" (7/10 score).

**Key distinction:**
- KF answers: WHAT was decided and WHY (knowledge layer)
- MSCE answers: WHEN was what done and WHAT is pending (session continuity)

**No direct integration required.** KF and MSCE operate at different scopes:
- KF: cross-project, static, append-only
- MSCE: project-scoped, dynamic, per-session

KF does not reference MSCE. MSCE does not reference KF. This is architecturally correct.
Cross-references are limited to navigation and traceability.

---

## 8. Validation Questions

### ✓ Does MSCE introduce runtime code?
**NO.** All MSCE components are Markdown files. No Python, no imports, no execution.

### ✓ Does MSCE modify core files?
**NO.** MSCE creates new files in `docs/governance/`. Core files (kernel.py, etc.) are untouched.

### ✓ Does MSCE conflict with AGENTS.md?
**NO.** MSCE supplements AGENTS.md by providing structured file formats for session tracking. AGENTS.md remains the authority for rules and lock levels.

### ✓ Is MSCE mandatory?
**NOT YET.** v0.1 is the specification. Adoption is voluntary until governance enforcement is added (Phase 3).

### ✓ What happens if MSCE files are missing?
**Graceful degradation.** The workflow falls back to existing governance files (TASK_BOARD, SESSION_REGISTRY, CHANGE_JOURNAL). MSCE files are additive.

---

## 9. Implementation Checklist

### Specification (this document)
- [x] MSCE-SPECIFICATION_v0.1.md created
- [ ] SESSION_REGISTRY.md schema defined
- [ ] ACTIVE_TASKS.md schema defined
- [ ] WORK_QUEUE.md schema defined
- [ ] CHECKPOINT_INDEX.md schema defined
- [ ] HANDOVER_TEMPLATE.md template defined

### Component Files (docs/governance/)
- [ ] SESSION_REGISTRY.md — created with schema headers
- [ ] ACTIVE_TASKS.md — created empty
- [ ] WORK_QUEUE.md — created empty
- [ ] CHECKPOINT_INDEX.md — created empty
- [ ] HANDOVER_TEMPLATE.md — created with template content

### Integration
- [ ] SESSION_REGISTRY.md replaces `docs/SESSION_REGISTRY.md` reference
- [ ] GOVERNANCE_CHECKPOINT.md updated to reference MSCE
- [ ] First session handover uses HANDOVER_TEMPLATE

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-16 | Initial specification — 5 component files, no code |
