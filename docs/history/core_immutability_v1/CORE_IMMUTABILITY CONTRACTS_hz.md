# MUSCAL CORE — IMMUTABILITY CONTRACT

## CORE IS READ-ONLY

The following directories are IMMUTABLE:

- /core
- /kernel
- /runtime/core
- /architecture

---

## STRICT RULE

Any OpenCode session MUST NOT:

- modify files in /core
- add imports INTO /core from /features
- change execution flow in kernel
- alter memory, graph, or runtime initialization

---

## ALLOWED ACTIONS

Only allowed:

- read core files
- extend via /features/*
- register hooks
- create adapters

---

## ENFORCEMENT RULE

If a change requires core modification:

→ STOP execution
→ classify as ARCHITECTURE CHANGE
→ require explicit override file

---

## VIOLATION HANDLING

Any attempt to modify core:

→ must be rejected automatically
→ must not be partially applied
→ must be reported as "ARCHITECTURE VIOLATION"

---

END OF CONTRACT
