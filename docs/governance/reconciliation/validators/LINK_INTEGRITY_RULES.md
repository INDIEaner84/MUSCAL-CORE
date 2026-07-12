# Link Integrity Rules

**Version:** 1.0
**Status:** Specification

---

## Rule Set: LNK-IR

| Rule ID | Rule | Severity | Category | Auto-Fixable |
|---------|------|----------|----------|--------------|
| LNK-IR-001 | All markdown links must point to existing paths | High | A | Yes |
| LNK-IR-002 | `specs/adrs/` references must be updated to `spec/` or `archive/history/adrs/` | High | A | Yes |
| LNK-IR-003 | `specs/rfcs/` references must be updated to `archive/history/rfcs/` | High | A | Yes |
| LNK-IR-004 | Cross-document links in authoritative docs must be valid | High | A | Yes |
| LNK-IR-005 | Relative links must resolve correctly from the referencing file's location | Medium | B | No |

---

## Rule Details

### LNK-IR-001: Path Existence

Every markdown link that references a file path must point to an existing file
on disk. This includes both absolute (from repo root) and relative paths.

**Detection:** Extract all `[text](path)` patterns, resolve paths, check existence.

**Fix:** Update path to correct location.

---

### LNK-IR-002: Obsolete ADR Path

The `specs/adrs/` directory is obsolete. Current ADRs are in `spec/`.
Historical ADRs are in `archive/history/adrs/`.

**Detection:** Search for `specs/adrs/` in all markdown files.

**Fix:**
- If referencing a current ADR → `spec/ADR-NNN-description.md`
- If referencing a historical ADR → `archive/history/adrs/ADR-NNN.md`

---

### LNK-IR-003: Obsolete RFC Path

The `specs/rfcs/` directory does not exist. RFCs are in `archive/history/rfcs/`.

**Detection:** Search for `specs/rfcs/` in all markdown files.

**Fix:** Replace `specs/rfcs/` with `archive/history/rfcs/`.

---

### LNK-IR-004: Authoritative Document Links

Documents listed in SESSION_RULES.md section "Authoritative Documents" must
have valid cross-references. A broken link in an authoritative document
is a HIGH severity finding.

**Detection:** For each authoritative document, verify all links.

**Fix:** Correct broken links immediately.

---

### LNK-IR-005: Relative Link Resolution

Relative links (e.g., `../spec/ADR-001.md`) must resolve correctly from the
referencing file's directory.

**Detection:** Resolve each relative link from its parent directory.

**Fix:** Adjust path to account for file location.

---

## Integration

| Scanner | Uses Rules |
|---------|-----------|
| Broken Link Scanner | LNK-IR-001 through LNK-IR-005 |
