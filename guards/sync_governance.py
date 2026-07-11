#!/usr/bin/env python3
"""
sync_governance.py — Synchronisiert CORE_FILES/CORE_DIRS zwischen
guards/write_guard.py und spec/IMMUTABILITY_CONTRACT.md

Nutzung:
    python guards/sync_governance.py --check   # Nur prüfen, nicht ändern
    python guards/sync_governance.py --fix     # Differenzen beheben
"""

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = ROOT / "guards" / "write_guard.py"
CONTRACT_PATH = ROOT / "spec" / "IMMUTABILITY_CONTRACT.md"


def _extract_frozenset(varname: str, content: str) -> set[str]:
    """Hilfsfunktion: Extrahiert String-Elemente aus einem frozenset(...)-Block."""
    match = re.search(rf"{varname}\s*=\s*frozenset\(\{{(.*?)\}}\)", content, re.DOTALL)
    if not match:
        return set()
    return {re.sub(r'[^a-zA-Z0-9_./]', '', line.strip())
            for line in match.group(1).splitlines()
            if re.sub(r'[^a-zA-Z0-9_./]', '', line.strip())}


def parse_guard_files() -> set[str]:
    """Extrahiert CORE_FILES aus write_guard.py."""
    return _extract_frozenset("CORE_FILES", GUARD_PATH.read_text(encoding="utf-8"))


def parse_guard_dirs() -> set[str]:
    """Extrahiert CORE_DIRS aus write_guard.py."""
    return _extract_frozenset("CORE_DIRS", GUARD_PATH.read_text(encoding="utf-8"))


def parse_contract_files() -> set[str]:
    """Extrahiert Dateiliste aus IMMUTABILITY_CONTRACT.md (```-Blöcke unter Root-Dateien)."""
    content = CONTRACT_PATH.read_text(encoding="utf-8")
    files = set()
    in_files_section = False
    in_code_block = False
    for line in content.splitlines():
        if "### Root-Dateien" in line:
            in_files_section = True
            continue
        if in_files_section and line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
                in_files_section = False
                continue
            in_code_block = True
            continue
        if in_code_block and line.strip():
            # Format: "filename.py" oder "filename.py  Description" oder "filename.py  # Desc"
            raw = line.strip()
            # Kommentar entfernen
            if "#" in raw:
                raw = raw.split("#")[0].strip()
            # Nur den Dateinamen nehmen (erstes Token)
            fname = raw.split()[0] if raw.split() else ""
            if fname and re.match(r'^[\w.-]+\.py$', fname):
                files.add(fname)
    return files


def parse_contract_dirs() -> set[str]:
    """Extrahiert Verzeichnisliste aus IMMUTABILITY_CONTRACT.md."""
    content = CONTRACT_PATH.read_text(encoding="utf-8")
    dirs = set()
    in_dirs_section = False
    in_code_block = False
    for line in content.splitlines():
        if "### Runtime-Verzeichnisse" in line:
            in_dirs_section = True
            continue
        if in_dirs_section and line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
                in_dirs_section = False
                continue
            in_code_block = True
            continue
        if in_code_block and line.strip():
            raw = line.strip()
            if "#" in raw:
                raw = raw.split("#")[0].strip()
            # Nur Verzeichnisname (vor Leerzeichen/Kommentar)
            raw = raw.split()[0] if raw.split() else ""
            raw = raw.rstrip("/")
            if raw and re.match(r'^[\w/.-]+$', raw):
                dirs.add(raw)
    return dirs


def update_contract_files(contract_files: set[str], guard_files: set[str]):
    """Aktualisiert die Dateiliste im IMMUTABILITY_CONTRACT.md."""
    content = CONTRACT_PATH.read_text(encoding="utf-8")

    new_block = "### Root-Dateien\n\n```\n"
    for f in sorted(guard_files):
        comment = ""
        if f in contract_files:
            old_line = [l for l in content.splitlines()
                        if l.strip().startswith(f)][0]
            comment = ""
            if "#" in old_line:
                comment = " " + old_line.split("#", 1)[1]
        new_block += f"{f}{comment}\n"
    new_block += "```\n"

    pattern = r"### Root-Dateien\n\n```\n.*?```"
    content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    CONTRACT_PATH.write_text(content, encoding="utf-8")


def update_contract_dirs(contract_dirs: set[str], guard_dirs: set[str]):
    """Aktualisiert die Verzeichnisliste im IMMUTABILITY_CONTRACT.md."""
    content = CONTRACT_PATH.read_text(encoding="utf-8")

    new_block = "### Runtime-Verzeichnisse\n\n```\n"
    for d in sorted(guard_dirs):
        comment = ""
        if d in contract_dirs:
            old_line = [l for l in content.splitlines()
                        if l.strip().startswith(d)][0]
            if "#" in old_line:
                comment = " " + old_line.split("#", 1)[1]
        new_block += f"{d}/{comment}\n"
    new_block += "```\n"

    pattern = r"### Runtime-Verzeichnisse\n\n```\n.*?```"
    content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    CONTRACT_PATH.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronisiert CORE_FILES/CORE_DIRS zwischen "
                    "write_guard.py und IMMUTABILITY_CONTRACT.md"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="Nur prüfen, Exit-Code 1 bei Differenz")
    group.add_argument("--fix", action="store_true",
                       help="Differenzen beheben (Contract an Guard anpassen)")
    args = parser.parse_args()

    guard_files = parse_guard_files()
    guard_dirs = parse_guard_dirs()
    contract_files = parse_contract_files()
    contract_dirs = parse_contract_dirs()

    missing_in_contract = guard_files - contract_files
    extra_in_contract = contract_files - guard_files
    dirs_missing_in_contract = guard_dirs - contract_dirs
    dirs_extra_in_contract = contract_dirs - guard_dirs

    issues = []
    if missing_in_contract:
        issues.append(
            f"Files in Guard aber NICHT im Contract ({len(missing_in_contract)}):\n"
            + "\n".join(f"  + {f}" for f in sorted(missing_in_contract))
        )
    if extra_in_contract:
        issues.append(
            f"Files im Contract aber NICHT im Guard ({len(extra_in_contract)}):\n"
            + "\n".join(f"  - {f}" for f in sorted(extra_in_contract))
        )
    if dirs_missing_in_contract:
        issues.append(
            f"Dirs in Guard aber NICHT im Contract ({len(dirs_missing_in_contract)}):\n"
            + "\n".join(f"  + {d}" for d in sorted(dirs_missing_in_contract))
        )
    if dirs_extra_in_contract:
        issues.append(
            f"Dirs im Contract aber NICHT im Guard ({len(dirs_extra_in_contract)}):\n"
            + "\n".join(f"  - {d}" for d in sorted(dirs_extra_in_contract))
        )

    if not issues:
        print("GOVERNANCE SYNC: OK")
        print(f"  Guard Files:  {len(guard_files)}")
        print(f"  Contract Files: {len(contract_files)}")
        print(f"  Guard Dirs:   {len(guard_dirs)}")
        print(f"  Contract Dirs: {len(contract_dirs)}")
        sys.exit(0)

    if args.fix:
        print("GOVERNANCE SYNC: FIXING")
        update_contract_files(contract_files, guard_files)
        update_contract_dirs(contract_dirs, guard_dirs)
        print(f"  Contract aktualisiert: {CONTRACT_PATH}")
        sys.exit(0)

    print("GOVERNANCE SYNC: DRIFT DETECTED")
    for issue in issues:
        print(f"\n{issue}")
    sys.exit(1)


if __name__ == "__main__":
    main()
