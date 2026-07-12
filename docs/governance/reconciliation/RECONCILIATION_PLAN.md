# MUSCAL CORE — Reconciliation Engine Plan

**Version:** 1.0
**Status:** Foundation Phase (Checkpoint 0.26)
**Session:** S-2026-07-12-002

---

## 1. Purpose

The Reconciliation Engine is a permanent governance subsystem that detects,
classifies, tracks, and resolves semantic inconsistencies across the MUSCAL CORE
repository. It bridges documentation, code, and architecture decisions,
ensuring long-term consistency without modifying runtime behavior.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Reconciliation Engine                      │
├─────────────┬───────────────┬───────────────┬───────────────┤
│  Scanners   │  Validators   │  Classifiers  │  Generators   │
├─────────────┼───────────────┼───────────────┼───────────────┤
│ Link        │ ADR Rules     │ Category A    │ Autofix       │
│ ADR         │ Link Rules    │ Category B    │ Handover      │
│ RFC         │ Import Rules  │ Category C    │ Report        │
│ Import      │ Drift Rules   │ Category D    │ Task Board    │
│ Drift       │               │               │               │
└─────────────┴───────────────┴───────────────┴───────────────┘
        │              │               │               │
        ▼              ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Report / Action Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Finding Report → Validation Report → Reconciliation Report │
│  Task Board Update  →  Session Handover  →  Git Commit      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Scanner Specifications

| Scanner | Scope | Specification |
|---------|-------|---------------|
| Broken Link Scanner | `*.md` files in repository | `scanners/BROKEN_LINK_SCANNER.md` |
| ADR Validator | `spec/ADR-*.md`, `spec/ADR-INDEX.md` | `scanners/ADR_VALIDATOR.md` |
| RFC Validator | `archive/history/rfcs/MAS-*.md` | `scanners/RFC_VALIDATOR.md` |
| Import Validator | `*.py` files importing project modules | `scanners/IMPORT_VALIDATOR.md` |
| Drift Detector | ADR/RFC decisions vs code vs docs | `scanners/DRIFT_DETECTOR.md` |

---

## 4. Validation Rules

| Rule Set | Applied To | Specification |
|----------|-----------|---------------|
| ADR Consistency Rules | ADR documents | `validators/ADR_CONSISTENCY_RULES.md` |
| Link Integrity Rules | All markdown files | `validators/LINK_INTEGRITY_RULES.md` |
| Import Integrity Rules | Python source files | `validators/IMPORT_INTEGRITY_RULES.md` |
| Semantic Drift Rules | ADR → Code → Docs trace | `validators/SEMANTIC_DRIFT_RULES.md` |

---

## 5. Classification System

| Category | Meaning | Action | Example |
|----------|---------|--------|---------|
| A | Safe auto-fix | Execute immediately | Broken link, docstring typo |
| B | Needs review | Create task, assign | Non-existent import, missing dependency |
| C | Needs ADR | Propose ADR | Architectural inconsistency |
| D | Historical | Archive or ignore | Outdated reference in history doc |

---

## 6. Report Templates

| Template | Purpose | Location |
|----------|---------|----------|
| Finding Report | Single inconsistency finding | `templates/FINDING_TEMPLATE.md` |
| Validation Report | Full scanner run output | `templates/VALIDATION_REPORT.md` |
| Reconciliation Report | Multi-scanner reconciliation | `templates/RECONCILIATION_REPORT.md` |

---

## 7. Integration Hooks (Conceptual)

| Hook Point | Integration | Specification |
|-----------|-------------|---------------|
| Pre-Commit | Run Link Scanner before commit | `hooks/HOOK_REGISTRY.md` |
| Session Start | Check TASK_BOARD for open findings | `hooks/HOOK_REGISTRY.md` |
| Session End | Generate reconciliation report | `hooks/HOOK_REGISTRY.md` |
| CI/CD | Full scanner suite on push | `hooks/HOOK_REGISTRY.md` |

---

## 8. Lifecycle

```
Checkpoint Planning
    ↓
Scanning Phase (scanners run)
    ↓
Validation Phase (rules applied)
    ↓
Classification Phase (Category A/B/C/D)
    ↓
Action Phase (auto-fix / task / ADR / archive)
    ↓
Reporting Phase (report generated)
    ↓
Validation Phase (fixes verified)
    ↓
Session Handover
    ↓
Git Commit
```

---

## 9. Future Evolution

| Phase | Scope | Checkpoint |
|-------|-------|------------|
| Foundation | Documentation, scanner specs, validator rules | 0.26 |
| Automation | Scanner scripts, pre-commit hooks, CI/CD integration | 0.27+ |
| ADR Integration | ADR-driven reconciliation workflow | 0.28+ |
| Full Autonomy | Automated Category-A + B triage | 0.29+ |

---

## 10. Related Documents

| Document | Path |
|----------|------|
| Auto-Fix Report | `AUTOFIX_REPORT.md` |
| Governance Checkpoint | `docs/GOVERNANCE_CHECKPOINT.md` |
| Lock Protocol | `docs/LOCK_PROTOCOL.md` |
| Session Rules | `.opencode/SESSION_RULES.md` |
| Immutability Contract | `spec/IMMUTABILITY_CONTRACT.md` |
