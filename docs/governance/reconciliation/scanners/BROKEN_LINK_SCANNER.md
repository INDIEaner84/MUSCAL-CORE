# Broken Link Scanner Specification

**Version:** 1.0
**Status:** Specification

---

## 1. Purpose

Detect internal markdown link references that point to non-existent directories
or files within the MUSCAL CORE repository.

---

## 2. Scan Scope

All `*.md` files in the repository, excluding:
- `.git/` directory
- `node_modules/` (if present)
- `archive/` (historical documents — scanned but findings marked `Category D`)

---

## 3. Detection Rules

### Rule BLS-001: Directory Existence

```
If a markdown link contains a path `specs/adrs/` or `specs/rfcs/`:
  → Verify `spec/`, `archive/history/adrs/`, `archive/history/rfcs/` alternatives
  → Flag as Category A if alternative path exists and contains expected content
```

### Rule BLS-002: File Existence

```
If a markdown link references a specific file (e.g., `./ADR-001.md`):
  → Verify file exists at the specified path relative to repository root
  → If not found, search known locations:
    - `spec/`
    - `docs/`
    - `archive/history/adrs/`
    - `archive/history/rfcs/`
  → Flag as Category B if file exists at a different location
  → Flag as Category A if renamed file exists at same location
```

### Rule BLS-003: Anchor Validity

```
If a markdown link contains a `#section` anchor:
  → Verify that the target file contains a heading matching the anchor
  → Flag as Category B if anchor not found
```

### Rule BLS-004: Pattern Matching

```
Known outdated path patterns:
  - `specs/adrs/` → should be `spec/` or `archive/history/adrs/`
  - `specs/rfcs/` → should be `archive/history/rfcs/`
  - `docs/history/` → verify against SESSION_RULES.md priority list
```

---

## 4. Output Format

```json
{
  "scanner": "broken_link",
  "findings": [
    {
      "id": "BLS-001",
      "file": "docs/DECISIONS.md",
      "line": 15,
      "link": "specs/adrs/ADR-001.md",
      "category": "A",
      "suggested_fix": "spec/ADR-001-kernel.md"
    }
  ]
}
```

---

## 5. Integration

| Hook Point | Action |
|-----------|--------|
| Pre-Commit | Scan all staged `*.md` files |
| Session End | Full repository scan |
| CI/CD | Full repository scan on push |
