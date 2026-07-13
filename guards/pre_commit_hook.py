#!/usr/bin/env python3
"""
pre_commit_hook.py — Git Pre-Commit Hook fuer MUSCAL CORE Governance v1.1.

Ablauf:
  1. get_staged_files()
  2. check_override_scope()
  3. Core Protection (bei NONE)
  4. Governance Validation
  5. Session Handover Check

Installation:
    bash guards/install_hook.sh

Nutzung (manuell):
    python guards/pre_commit_hook.py [--staged-files file1 file2 ...]
    python guards/pre_commit_hook.py --allow-core-write [--staged-files ...]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from guards.write_guard import CORE_FILES, CORE_DIRS
from guards.governance_validator import (
    check_override_scope,
    validate_staged_files,
    check_session_handover,
    generate_markdown_report,
)


def get_staged_files() -> list[str]:
    """Holt die Liste der staged Files aus git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True,
            cwd=str(ROOT)
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def check_violation(filepath: str) -> str | None:
    """Prueft ob eine Datei gegen Core-Schutz verstoesst."""
    rel = os.path.relpath(filepath, str(ROOT))
    filename = os.path.basename(rel)
    rel_dir = os.path.dirname(rel)

    if filename in CORE_FILES:
        return (
            f"ARCHITECTURE VIOLATION\n\n"
            f"Attempted commit of protected core file:\n"
            f"  {rel}\n\n"
            f"CORE IS IMMUTABLE.\n"
            f"Extensions must go in /features/.\n"
            f"See spec/IMMUTABILITY_CONTRACT.md\n\n"
            f"To override: commit with --allow-core-write flag"
        )

    for core_dir in CORE_DIRS:
        if rel_dir.startswith(core_dir) or core_dir.startswith(rel_dir):
            return (
                f"ARCHITECTURE VIOLATION\n\n"
                f"Attempted commit of file in protected core directory:\n"
                f"  {rel}\n\n"
                f"CORE IS IMMUTABLE.\n"
                f"Extensions must go in /features/.\n\n"
                f"To override: commit with --allow-core-write flag"
            )

    return None


def run_governance_validation(files: list) -> bool:
    """Fuehrt Governance Validation aus. Gibt True zurueck wenn bestanden."""
    report = validate_staged_files(files)

    if report.has_violations():
        print("GOVERNANCE VALIDATION FAILED")
        print("=" * 50)
        for v in report.violations:
            print(f"BLOCKED: {v['file']} ({v['category']} Level {v['level']})")
            print(f"  {v.get('message', '')}")
        return False

    if report.has_warnings():
        print("GOVERNANCE VALIDATION PASSED WITH WARNINGS")
        print("=" * 50)
        for w in report.warnings:
            print(f"WARNING: {w['file']}: {w.get('message', '')}")

    return True


def run_session_handover_check(files: list) -> bool:
    """Prueft SESSION_HANDOVER Existenz. Gibt True zurueck wenn bestanden."""
    result = check_session_handover(files)
    if result:
        print(f"SESSION HANDOVER CHECK: {result}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="MUSCAL CORE Pre-Commit Governance Hook v1.1")
    parser.add_argument("--staged-files", nargs="*", default=None,
                        help="Manuelle Liste von Dateien ( fuer Testing )")
    parser.add_argument("--allow-core-write", action="store_true",
                        help="Core-Schutz umgehen (erfordert OVERRIDE-Dokumentation)")
    args = parser.parse_args()

    if args.staged_files is not None:
        files = args.staged_files
    else:
        files = get_staged_files()

    if not files:
        sys.exit(0)

    # ──────────────────────────────────────────────
    # Schritt 1: OVERRIDE-052 Scope Check
    # ──────────────────────────────────────────────
    override_scope = check_override_scope(files)

    if override_scope == "BLOCK":
        print("=" * 60)
        print("PRE-COMMIT BLOCKED: OVERRIDE-052 SCOPE VIOLATION")
        print("=" * 60)
        print()
        print("OVERRIDE-052 erlaubt ausschliesslich:")
        print("  guards/")
        print("  .github/")
        print("  .pre-commit-config.yaml")
        print()
        print("Core Files sind IMMER blockiert:")
        print("  kernel.py, config.py, event_bus.py, muscal_os.py")
        print("  plugin_loader.py, plugin_registry.py")
        print("  runtime/kernel/, runtime/llm/, runtime/api/, runtime/optimizer/")
        print()
        print("Betroffene Dateien:")
        for f in files:
            print(f"  - {f}")
        print("=" * 60)
        sys.exit(1)

    if override_scope == "ALLOW_INFRA":
        print("OVERRIDE-052 active — infrastructure changes allowed")
        if not run_governance_validation(files):
            sys.exit(1)
        if not run_session_handover_check(files):
            sys.exit(1)
        print("Governance validation passed")
        sys.exit(0)

    # ──────────────────────────────────────────────
    # Schritt 2: Core Protection Check (NONE)
    # ──────────────────────────────────────────────
    violations = []
    for filepath in files:
        full_path = str(ROOT / filepath) if not os.path.isabs(filepath) else filepath
        if not os.path.exists(full_path):
            continue
        violation = check_violation(full_path)
        if violation:
            violations.append(violation)

    if violations:
        if args.allow_core_write:
            print("WARNING: Core write override active")
            print("Ensure this change is documented in spec/OVERRIDE.md")
            for v in violations:
                print(f"\n{v}")
            sys.exit(0)

        print("=" * 60)
        print("PRE-COMMIT BLOCKED: ARCHITECTURE VIOLATION")
        print("=" * 60)
        for v in violations:
            print(f"\n{v}")
        print("\n" + "=" * 60)
        print("To override: git commit --allow-core-write ...")
        print("Document the override in spec/OVERRIDE.md")
        print("=" * 60)
        sys.exit(1)

    # ──────────────────────────────────────────────
    # Schritt 3: Governance Validation
    # ──────────────────────────────────────────────
    if not run_governance_validation(files):
        sys.exit(1)

    # ──────────────────────────────────────────────
    # Schritt 4: Session Handover Check
    # ──────────────────────────────────────────────
    if not run_session_handover_check(files):
        print("TIP: Create a SESSION_HANDOVER before committing")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
