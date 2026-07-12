# Import Validator Specification

**Version:** 1.0
**Status:** Specification

---

## 1. Purpose

Detect Python import statements that reference non-existent modules,
packages, or symbols within the MUSCAL CORE project.

---

## 2. Scan Scope

All `*.py` files in the repository, excluding:
- `venv/`, `.venv/`, `__pycache__/`
- External dependencies (verified against `requirements.txt`)

---

## 3. Detection Rules

### Rule IMP-001: Module Existence

```
For every `import X` or `from X import Y` statement:
  → Verify X exists as:
    - A file `X.py` in the same directory or Python path
    - A directory `X/__init__.py`
    - An installed package (in requirements.txt or stdlib)
  → Flag as Category B if module does not exist
```

### Rule IMP-002: Symbol Existence

```
For every `from X import Y` statement where X is a project module:
  → Verify Y exists as a class/function/variable in X
  → Flag as Category B if symbol not found in X
```

### Rule IMP-003: Core Isolation

```
For every `import` in `features/*/plugin.py`:
  → Verify the import does NOT reference core modules
    (kernel.py, memory.py, mkc.py, etc.)
  → Flag as Category B if core import detected in plugin code
```

### Rule IMP-004: Dependency Declaration

```
For every third-party import:
  → Verify the package is listed in `requirements.txt`
  → Flag as Category B if dependency is missing from requirements.txt
```

---

## 4. Output Format

```json
{
  "scanner": "import_validator",
  "findings": [
    {
      "id": "IMP-001",
      "file": "features/mcxf_fusion.py",
      "line": 46,
      "import_statement": "from simple_rag import ...",
      "category": "B",
      "reason": "Module 'simple_rag' does not exist"
    }
  ]
}
```

---

## 5. Integration

| Hook Point | Action |
|-----------|--------|
| Pre-Commit | Scan staged Python files only |
| Session End | Full codebase scan |
| CI/CD | Full import validation on push |
