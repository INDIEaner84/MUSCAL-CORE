# Validation Report Template

**Scanner:** [scanner name]
**Date:** [YYYY-MM-DD]
**Session:** [Session ID]

---

## Summary

| Metric | Value |
|--------|-------|
| Total Findings | [count] |
| Category A (Auto-Fix) | [count] |
| Category B (Needs Review) | [count] |
| Category C (Needs ADR) | [count] |
| Category D (Historical) | [count] |
| Critical | [count] |
| High | [count] |
| Medium | [count] |
| Low | [count] |

---

## Findings

### Finding [ID-001] — [Short Title]

| Field | Value |
|-------|-------|
| **File** | [path/to/file] |
| **Line** | [line] |
| **Severity** | [Critical/High/Medium/Low] |
| **Category** | [A/B/C/D] |

**Description:**
[Description of finding]

**Current:**
```[value]```

**Expected:**
```[value]```

**Suggested Action:**
[Action description]

---

### Finding [ID-002] — [Short Title]

...

---

## Appendix: Raw Scanner Output

```json
{
  "scanner": "...",
  "findings": [...]
}
```
