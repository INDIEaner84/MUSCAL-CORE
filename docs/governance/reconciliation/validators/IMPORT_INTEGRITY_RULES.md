# Import Integrity Rules

**Version:** 1.0
**Status:** Specification

---

## Rule Set: IMP-IR

| Rule ID | Rule | Severity | Category | Auto-Fixable |
|---------|------|----------|----------|--------------|
| IMP-IR-001 | Every import in project Python files must resolve to an existing module | High | B | No |
| IMP-IR-002 | Plugin code must not import core modules | High | B | No |
| IMP-IR-003 | Third-party imports must be declared in requirements.txt | Medium | B | No |
| IMP-IR-004 | Deprecated module references must be updated | Medium | A | Yes |
| IMP-IR-005 | Wildcard imports are prohibited | Low | B | No |

---

## Rule Details

### IMP-IR-001: Module Resolvability

Every `import X` and `from X import Y` statement must resolve to a module
that exists either as a project file, installed package, or stdlib module.

**Detection:** Parse each `.py` file, extract imports, verify resolution.

**Fix:** Requires manual intervention (install missing package, fix import path).

---

### IMP-IR-002: Core Isolation

Plugins in `features/*/` must not import core modules directly
(e.g., `kernel.py`, `memory.py`, `mkc.py`).

**Detection:** In `features/*/` files, check all imports against the core
file list from `spec/IMMUTABILITY_CONTRACT.md`.

**Fix:** Refactor plugin to use hook API instead of direct core imports.

---

### IMP-IR-003: Dependency Declaration

Every third-party import must be traceable to an entry in `requirements.txt`
or the stdlib module list.

**Detection:** For each non-project import, verify it appears in
`requirements.txt` or is a known stdlib module.

**Fix:** Add missing dependency to `requirements.txt`.

---

### IMP-IR-004: Deprecated Module References

If a module has been renamed or removed, imports referencing the old name
must be updated.

**Detection:** Maintain a list of renamed/removed modules and scan for old names.

**Fix:** Update import to use new module name.

---

### IMP-IR-005: Wildcard Imports

`from X import *` is prohibited as it pollutes the namespace and makes
dependency tracking impossible.

**Detection:** Search for `import *` patterns.

**Fix:** Replace with explicit imports.

---

## Integration

| Scanner | Uses Rules |
|---------|-----------|
| Import Validator | IMP-IR-001 through IMP-IR-005 |
