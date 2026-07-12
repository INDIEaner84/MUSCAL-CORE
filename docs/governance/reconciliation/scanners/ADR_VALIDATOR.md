# ADR Validator Specification

**Version:** 1.0
**Status:** Specification

---

## 1. Purpose

Validate that all Architecture Decision Records (ADRs) are structurally complete,
correctly indexed, and consistent with the ADR-INDEX.md registry.

---

## 2. Scan Scope

- `spec/ADR-*.md` (all ADR documents)
- `spec/ADR-INDEX.md` (ADR registry index)

---

## 3. Detection Rules

### Rule ADR-001: Required Fields

```
Every ADR MUST contain:
  - Title (line starting with `# ADR-NNN:`)
  - Status section (`**Status:**`)
  - Date section (`**Date:**`)
  - Context section (`## Context`)
  - Decision section (`## Decision`)

Missing fields → Category A (add missing section)
```

### Rule ADR-002: Index Consistency

```
Every ADR in `spec/ADR-*.md` MUST appear in `spec/ADR-INDEX.md`.
Every entry in `spec/ADR-INDEX.md` MUST have a corresponding file in `spec/`.

Missing index entry → Category A (add to index)
Orphaned index entry → Category A (remove from index)
```

### Rule ADR-003: Numbering

```
ADR numbers MUST be sequential with no gaps.
Duplicate numbers (e.g., two ADR-007 files) MUST be resolved:
  → The second ADR-007 gets the next available number
  → Category A for renamed duplicate
```

### Rule ADR-004: Status Validity

```
Valid statuses: PROPOSED, ACCEPTED, APPLIED, DEPRECATED, SUPERSEDED.
Invalid status → Category A (correct status)
Flag `SUPERSEDED` entries — verify superseding ADR exists → Category B if missing
```

### Rule ADR-005: File Naming Convention

```
Files MUST follow: `ADR-NNN-description.md` where NNN is 3 digits.
Non-compliant names → Category A (rename to convention)
```

---

## 4. Output Format

```json
{
  "scanner": "adr_validator",
  "findings": [
    {
      "id": "ADR-003",
      "file": "spec/ADR-005-pipeline.md",
      "line": 1,
      "issue": "Missing '## Consequences' section",
      "category": "A"
    }
  ]
}
```

---

## 5. Integration

| Hook Point | Action |
|-----------|--------|
| Session Start | Validate ADR-INDEX.md before work |
| ADR Creation | Run on new ADR before commit |
| CI/CD | Full ADR validation on push |
