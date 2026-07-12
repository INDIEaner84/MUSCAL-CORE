# RFC Validator Specification

**Version:** 1.0
**Status:** Specification

---

## 1. Purpose

Validate that all MAS-RFC documents are structurally complete and correctly
referenced from architecture documents.

---

## 2. Scan Scope

- `archive/history/rfcs/MAS-*.md` (RFC documents)
- References to MAS-RFCs in `docs/`, `spec/`, `specs/`

---

## 3. Detection Rules

### Rule RFC-001: Required Fields

```
Every RFC MUST contain:
  - Title (`# MAS-NNNN:`)
  - Status (`**Status:**`)
  - Date (`**Date:**`)
  - Context section
  - Proposal section

Missing fields → Category A (add missing section)
```

### Rule RFC-002: Cross-Reference Validity

```
If a document references `MAS-NNNN`:
  → Verify `archive/history/rfcs/MAS-NNNN.md` exists
  → Flag as Category B if RFC does not exist
```

### Rule RFC-003: Path Consistency

```
If a document links to `specs/rfcs/MAS-NNNN.md`:
  → Correct path is `archive/history/rfcs/MAS-NNNN.md`
  → Flag as Category A (update link)
```

---

## 4. Output Format

```json
{
  "scanner": "rfc_validator",
  "findings": [
    {
      "id": "RFC-002",
      "file": "docs/DECISIONS.md",
      "line": 15,
      "reference": "MAS-0301",
      "category": "A",
      "suggested_fix": "Update path to archive/history/rfcs/MAS-0301.md"
    }
  ]
}
```

---

## 5. Integration

| Hook Point | Action |
|-----------|--------|
| Session Start | Verify RFC references in SESSION_RULES.md |
| CI/CD | Full RFC validation on push |
