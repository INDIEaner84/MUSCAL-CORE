#!/usr/bin/env python3
"""
pre_commit_hook.py — Git Pre-Commit Hook fuer MUSCAL CORE Governance.

Prueft ob staged Dateien gegen CORE_FILES/CORE_DIRS verstoessen.
Bei Verletzung wird der Commit blockiert.

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
    """Prueft ob eine Datei gegen Core-Schutz verstoesst. Gibt Fehlermeldung zurueck."""
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


def main():
    parser = argparse.ArgumentParser(description="MUSCAL CORE Pre-Commit Governance Hook")
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

    violations = []
    for filepath in files:
        full_path = str(ROOT / filepath) if not os.path.isabs(filepath) else filepath
        if not os.path.exists(full_path):
            continue
        violation = check_violation(full_path)
        if violation:
            violations.append(violation)

    if not violations:
        sys.exit(0)

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


if __name__ == "__main__":
    main()
