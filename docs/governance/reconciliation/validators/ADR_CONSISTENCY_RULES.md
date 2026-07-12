# ADR Consistency Rules

**Version:** 1.0
**Status:** Specification

---

## Rule Set: ADR-CR

| Rule ID | Rule | Severity | Category | Auto-Fixable |
|---------|------|----------|----------|--------------|
| ADR-CR-001 | Every ADR must have a unique number | High | A | Yes |
| ADR-CR-002 | Every ADR in `spec/` must be listed in ADR-INDEX.md | High | A | Yes |
| ADR-CR-003 | ADR-INDEX.md must not reference non-existent files | High | A | Yes |
| ADR-CR-004 | ADR status must be one of: PROPOSED, ACCEPTED, APPLIED, DEPRECATED, SUPERSEDED | Medium | A | Yes |
| ADR-CR-005 | APPLIED ADRs must have a date | Medium | A | Yes |
| ADR-CR-006 | SUPERSEDED ADRs must reference the superseding ADR | Medium | B | No |
| ADR-CR-007 | ADR numbers must be sequential without gaps | Low | B | No |
| ADR-CR-008 | Every ADR must have Context, Decision, and Consequences sections | Medium | A | Yes |
| ADR-CR-009 | ADR filenames must follow `ADR-NNN-description.md` | Low | A | Yes |
| ADR-CR-010 | PROJECT_STATE.md ADR table must match ADR-INDEX.md | High | A | Yes |

---

## Rule Details

### ADR-CR-001: Unique Number

Every ADR in `spec/` must have a unique number. Duplicate numbers (e.g.,
two ADR-007 files) indicate a naming collision. The second file must be
renamed to the next available number.

**Detection:** List all `spec/ADR-*.md` files, extract numbers, find duplicates.

**Fix:** Rename duplicate to next available number. Update ADR-INDEX.md.

---

### ADR-CR-002: Index Completeness

Every `spec/ADR-*.md` file must have a corresponding entry in
`spec/ADR-INDEX.md`.

**Detection:** Compare file list against index entries.

**Fix:** Add missing entry to ADR-INDEX.md.

---

### ADR-CR-003: Index Accuracy

Every entry in `spec/ADR-INDEX.md` must point to an existing file.

**Detection:** For each index entry, verify the linked file exists.

**Fix:** Remove orphaned index entries or restore missing files.

---

### ADR-CR-004: Valid Status

ADR status values are restricted to the defined set.

**Detection:** Scan ADR files for `**Status:**` field.

**Fix:** Correct status to one of the valid values.

---

### ADR-CR-005: Date Required for APPLIED

APPLIED ADRs must specify the date of application.

**Detection:** Scan APPLIED ADRs for `**Date:**` field.

**Fix:** Add date field if missing.

---

### ADR-CR-006: Superseding Reference

SUPERSEDED ADRs should document which ADR superseded them.

**Detection:** Scan SUPERSEDED ADRs for a `Superseded by` reference.

**Fix:** Requires manual review to identify the superseding ADR.

---

### ADR-CR-007: Sequential Numbering

ADR numbers 001 through N should be contiguous with no gaps.

**Detection:** Sort ADR numbers, check for gaps.

**Fix:** Requires renumbering (manual review needed).

---

### ADR-CR-008: Required Sections

Every ADR must have Context (`## Context`), Decision (`## Decision`),
and Consequences (`## Consequences`) sections.

**Detection:** Scan ADR files for section headings.

**Fix:** Add missing sections with appropriate content.

---

### ADR-CR-009: File Naming Convention

ADR files must follow `ADR-NNN-description.md` pattern.

**Detection:** List filenames, check against regex `^ADR-\d{3}-.+\.md$`.

**Fix:** Rename file to match convention.

---

### ADR-CR-010: PROJECT_STATE Alignment

The ADR table in `docs/PROJECT_STATE.md` must match `spec/ADR-INDEX.md`
in number of entries, statuses, and titles.

**Detection:** Compare PROJECT_STATE.md ADR table against ADR-INDEX.md.

**Fix:** Update PROJECT_STATE.md to match ADR-INDEX.md.
