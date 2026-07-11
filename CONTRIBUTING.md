# Contributing to MUSCAL CORE

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
# All tests (except slow)
make test

# Full suite including slow/stress
make test-full

# Single file
pytest tests/test_events.py -v
```

## Code Style

- Ruff with `select = ["E", "F", "W", "I"]`
- Line length: 100
- Target: Python 3.12
- Run before commit: `make lint`

## Project Structure

| Path | Purpose |
|------|---------|
| `kernel.py` | Main pipeline (CORE — read-only) |
| `features/` | All extensions as plugins |
| `runtime/` | Runtime infrastructure (CORE) |
| `tests/` | Pytest test suite |
| `spec/` | ADRs, Plugin API, Override Log |

## Adding a Plugin

1. Create `features/<category>/<name>.py` with a `Plugin` class
2. Implement `register(self, hooks)` and `execute(self, context)`
3. See `spec/PLUGIN_API.md` for the full contract

## Core Immutability

Files listed in `spec/IMMUTABILITY_CONTRACT.md` are read-only.
Changes require an override documented in `spec/OVERRIDE.md`.

## Before Committing

```bash
make lint
make test
```
