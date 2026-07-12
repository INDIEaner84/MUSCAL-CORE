# MUSCAL CORE — OpenCode Session Rules

## Project Status

This project has a valid technical baseline.
Every session MUST read `docs/PROJECT_STATE.md` first.

## Authoritative Documents

| Priority | Document | Path |
|----------|----------|------|
| 1 | Project State | `docs/PROJECT_STATE.md` |
| 2 | Technical Baseline | `docs/TECHNICAL_BASELINE.md` |
| 3 | ADRs | `spec/ADR-*.md` |
| 4 | Historical ADRs/RFCs | `archive/history/adrs/*`, `archive/history/rfcs/*` |
| 5 | Architecture | `docs/ARCHITECTURE.md` |
| 6 | README | `README.md` |

Historical documents have NO authority over baseline documents.

## CORE IS READ-ONLY

These files are IMMUTABLE and must NOT be modified:

```
kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py, mkc_rules.py,
config.py, event_bus.py, graph.py, feedback.py, muscal_os.py, main.py,
main_boot.py, boot_manager.py, os_config.py, sphere.py, debugger.py,
tools.py, rag.py, trace_engine.py, plugin_registry.py, plugin_loader.py

runtime/kernel/*, runtime/llm/*, runtime/optimizer/*, runtime/api/*, runtime/services/*
```

Full contract: `spec/IMMUTABILITY_CONTRACT.md`

## ALL EXTENSIONS GO TO /features/

New features MUST be implemented as plugins in `features/`.

Plugin contract: `spec/PLUGIN_API.md`

## HISTORICAL DOCUMENTS

Documents in `docs/history/` are NOT current.
They serve as reference only.

If a historical document contradicts a baseline document,
the baseline document takes precedence.

## Verification Framework

Before implementing verification features:
→ `docs/VERIFICATION_FRAMEWORK_PLAN.md` — full implementation plan
→ `docs/VERIFICATION_CONFLICT_ANALYSIS.md` — conflict analysis
→ `spec/ADR-011-verification.md` — architecture decision

Implementation rule: Plugin-only in `features/event_sourcing/`.
Core files are NOT modified.

## VIOLATION HANDLING

If a task requires core modification:

1. STOP — do not execute
2. Classify as ARCHITECTURE CHANGE
3. Document in `spec/OVERRIDE.md`
4. Only execute with `--allow-core-write` flag

---

## SESSION HANDOVER (MANDATORY)

Every session with file changes MUST create a SESSION_HANDOVER before completion.

### SESSION_HANDOVER Template

```markdown
# SESSION_HANDOVER

**Session ID:** [S-YYYY-MM-DD-XXX]
**Date:** [YYYY-MM-DD]
**Status:** [COMPLETED / BLOCKED / ABORTED]

---

## Changed Files

| File | Category | Lock Level |
|------|----------|------------|
| [Filename] | [Core/Feature/Documentation/Infrastructure] | [0/1/2/3] |

---

## Change Category

[Description of the type of change]

---

## Open Tasks

- [ ] [Task 1]
- [ ] [Task 2]

---

## Recommended Next Action

[What should be done next]

---

## Known Risks

- [Risk 1]
- [Risk 2]
```

### Storage

SESSION_HANDOVERs are stored in `docs/session_handovers/`.
Filename: `HANDOVER_[Session_ID].md`

### Update

After creating the SESSION_HANDOVER:
1. Update `docs/SESSION_REGISTRY.md`
2. Update `docs/TASK_BOARD.md` (if new tasks emerged)
3. Git Commit with subject: "Session Handover: [Session ID]"
