# Reconciliation Engine — Hook Registry (Conceptual)

**Version:** 1.0
**Status:** Concept / Future Integration

---

## 1. Purpose

This document conceptually registers integration points where the
Reconciliation Engine will connect to existing MUSCAL CORE infrastructure.
No code changes are specified — only interface contracts and trigger points.

---

## 2. Hook Points

### Hook: `pre-commit.reconciliation`

| Field | Value |
|-------|-------|
| **Trigger** | Before every `git commit` |
| **Action** | Run Broken Link Scanner on staged files |
| **Failure Mode** | WARN (log findings) or BLOCK (prevent commit) |
| **Category A Fix** | Auto-apply on staged files if safe |
| **Dependencies** | Scanner scripts (not yet implemented) |
| **Status** | Concept |

**Integration:**
```yaml
# .pre-commit-config.yaml (future)
- repo: local
  hooks:
    - id: reconciliation-link-check
      name: Reconciliation Link Check
      entry: python -m reconciliation.scanners.broken_link
      language: script
      files: \.md$
```

---

### Hook: `session.start.reconciliation`

| Field | Value |
|-------|-------|
| **Trigger** | OpenCode session start |
| **Action** | Check TASK_BOARD.md for open Category B findings |
| **Failure Mode** | WARN (list open findings) |
| **Dependencies** | SESSION_RULES.md reading |
| **Status** | Concept |

**Integration:**
```markdown
# In SESSION_RULES.md (future update)
## Reconciliation Check
Before starting work, check:
1. `docs/governance/reconciliation/AUTOFIX_REPORT.md` — recent fixes
2. `docs/TASK_BOARD.md` — open Category B findings
```

---

### Hook: `session.end.reconciliation`

| Field | Value |
|-------|-------|
| **Trigger** | Session handover creation |
| **Action** | Run full scanner suite, generate reconciliation report |
| **Failure Mode** | WARN (append findings to handover) |
| **Dependencies** | Scanner scripts, report template |
| **Status** | Concept |

**Integration:**
```markdown
# In SESSION_RULES.md (future update)
## Session End
After creating SESSION_HANDOVER:
1. Run `reconciliation/scanners/` suite
2. Append findings to session handover
3. Update TASK_BOARD.md with new findings
```

---

### Hook: `ci.reconciliation`

| Field | Value |
|-------|-------|
| **Trigger** | GitHub Actions push / PR |
| **Action** | Full scanner suite + validation rules |
| **Failure Mode** | WARN on Category B, WARN on Category A auto-fix suggestions |
| **Dependencies** | Scanner scripts, GitHub Actions workflow |
| **Status** | Concept |

**Integration:**
```yaml
# .github/workflows/reconciliation.yml (future)
name: Reconciliation Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Broken Link Scanner
        run: python -m reconciliation.scanners.broken_link
      - name: Run ADR Validator
        run: python -m reconciliation.scanners.adr_validator
      - name: Run Import Validator
        run: python -m reconciliation.scanners.import_validator
      - name: Run Drift Detector
        run: python -m reconciliation.scanners.drift_detector
```

---

### Hook: `release.reconciliation`

| Field | Value |
|-------|-------|
| **Trigger** | New git tag (v*) |
| **Action** | Full reconciliation + block on Critical findings |
| **Failure Mode** | BLOCK (prevent release) if Critical or High Category C findings exist |
| **Dependencies** | All scanners, human review |
| **Status** | Concept |

---

## 3. Hook Implementation Priority

| Priority | Hook | Effort | Impact |
|----------|------|--------|--------|
| 1 | `pre-commit.reconciliation` | Low | Prevents new broken links |
| 2 | `session.end.reconciliation` | Medium | Catches drift per session |
| 3 | `ci.reconciliation` | Medium | Automated enforcement |
| 4 | `release.reconciliation` | High | Quality gate for releases |
| 5 | `session.start.reconciliation` | Low | Awareness of open findings |

---

## 4. Technical Requirements

- Scanner scripts in `reconciliation/scanners/` (Python)
- Hook scripts in `guards/` matching existing pattern
- CI/CD integration via `.github/workflows/`
- Pre-commit integration via `.pre-commit-config.yaml`
- Session integration via `.opencode/SESSION_RULES.md` updates

---

## 5. Related Documents

| Document | Path |
|----------|------|
| Scanner Specifications | `scanners/BROKEN_LINK_SCANNER.md` |
| Scanner Specifications | `scanners/ADR_VALIDATOR.md` |
| Scanner Specifications | `scanners/RFC_VALIDATOR.md` |
| Scanner Specifications | `scanners/IMPORT_VALIDATOR.md` |
| Scanner Specifications | `scanners/DRIFT_DETECTOR.md` |
| Validation Rules | `validators/ADR_CONSISTENCY_RULES.md` |
| Validation Rules | `validators/LINK_INTEGRITY_RULES.md` |
| Validation Rules | `validators/IMPORT_INTEGRITY_RULES.md` |
| Validation Rules | `validators/SEMANTIC_DRIFT_RULES.md` |
