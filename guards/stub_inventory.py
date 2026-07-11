#!/usr/bin/env python3
"""
stub_inventory.py — Automatisiertes Stub-Inventar fuer MUSCAL CORE.

Klassifiziert alle Python-Dateien <20 Zeilen als:
  - DEAD:   Keine Imports, nicht importiert, nur Stub-Code
  - MINIMAL: Importiert nur von archive/ Code
  - ACTIVE: Klein aber aktiv genutzt
  - __init__: Package-Marker

Nutzung:
    python guards/stub_inventory.py            # Vollstaendiges Inventar
    python guards/stub_inventory.py --dead     # Nur tote Dateien
    python guards/stub_inventory.py --fix      # Dead-Stubs nach archive/ verschieben
"""

import argparse
import ast
import os
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
THRESHOLD = 20


def count_lines(filepath: Path) -> int:
    try:
        return len(filepath.read_text(encoding="utf-8").splitlines())
    except Exception:
        return 0


def get_imports(filepath: Path) -> list[str]:
    """Extrahiert Import-Statements aus einer Python-Datei."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def find_importers(target_name: str, all_py: list[Path]) -> list[str]:
    """Findet Dateien die ein bestimmtes Modul importieren."""
    importers = []
    for pyfile in all_py:
        if "__pycache__" in str(pyfile) or "archive" in str(pyfile):
            continue
        try:
            content = pyfile.read_text(encoding="utf-8")
        except Exception:
            continue
        # Einfacher Check: Name als Import oder als Teil von Import
        if re.search(rf'\bimport\b.*\b{re.escape(target_name)}\b', content) or \
           re.search(rf'\bfrom\b.*\b{re.escape(target_name)}\b', content):
            importers.append(str(pyfile.relative_to(ROOT)))
    return importers


def classify_file(filepath: Path, all_py: list[Path]) -> str:
    """Klassifiziert eine Datei als DEAD, MINIMAL, ACTIVE oder __init__."""
    rel = filepath.relative_to(ROOT)
    name = filepath.stem

    if filepath.name == "__init__.py":
        content = filepath.read_text(encoding="utf-8").strip()
        if not content:
            return "__init__"
        return "__init__+"

    lines = count_lines(filepath)
    if lines >= THRESHOLD:
        return "ACTIVE"

    # Pruefe ob von active Code importiert
    importers = find_importers(name, all_py)
    if importers:
        return "ACTIVE"

    # Pruefe ob von archive Code importiert
    try:
        content = filepath.read_text(encoding="utf-8")
        archive_importers = []
        for pyfile in all_py:
            if "archive" not in str(pyfile):
                continue
            try:
                arch_content = pyfile.read_text(encoding="utf-8")
            except Exception:
                continue
            if re.search(rf'\bimport\b.*\b{re.escape(name)}\b', arch_content) or \
               re.search(rf'\bfrom\b.*\b{re.escape(name)}\b', arch_content):
                archive_importers.append(str(pyfile.relative_to(ROOT)))
        if archive_importers:
            return "MINIMAL"
    except Exception:
        pass

    # Pruefe ob nur Stub-Code enthaelt
    try:
        content = filepath.read_text(encoding="utf-8").strip()
        if content in ("", "pass", "...", "raise NotImplementedError()"):
            return "DEAD"
    except Exception:
        pass

    return "DEAD"


def main():
    parser = argparse.ArgumentParser(description="MUSCAL CORE Stub Inventory")
    parser.add_argument("--dead", action="store_true",
                        help="Nur tote Dateien anzeigen")
    parser.add_argument("--fix", action="store_true",
                        help="Dead-Stubs nach archive/stubs/ verschieben")
    parser.add_argument("--update-doc", action="store_true",
                        help="docs/STUB_INVENTORY.md aktualisieren")
    args = parser.parse_args()

    all_py = [p for p in ROOT.rglob("*.py") if "__pycache__" not in str(p)]

    small_files = []
    for pyfile in all_py:
        lines = count_lines(pyfile)
        if lines < THRESHOLD and "archive" not in str(pyfile):
            small_files.append(pyfile)

    results = {"DEAD": [], "MINIMAL": [], "ACTIVE": [], "__init__": [], "__init__+": []}
    for f in small_files:
        cat = classify_file(f, all_py)
        results[cat].append(f)

    # Output
    print(f"\nSTUB INVENTORY: {len(small_files)} Dateien < {THRESHOLD} Zeilen")
    print(f"  DEAD:    {len(results['DEAD'])}")
    print(f"  MINIMAL: {len(results['MINIMAL'])}")
    print(f"  ACTIVE:  {len(results['ACTIVE'])}")
    print(f"  __init__: {len(results['__init__']) + len(results['__init__+'])}")

    if args.dead or not args.fix:
        if results["DEAD"]:
            print("\nDEAD STUBS (koennen geloescht/verschoben werden):")
            for f in sorted(results["DEAD"]):
                rel = f.relative_to(ROOT)
                lines = count_lines(f)
                print(f"  {rel} ({lines} lines)")

        if results["MINIMAL"]:
            print("\nMINIMAL (importiert nur von archive/):")
            for f in sorted(results["MINIMAL"]):
                rel = f.relative_to(ROOT)
                lines = count_lines(f)
                print(f"  {rel} ({lines} lines)")

    if args.fix:
        archive_stubs = ROOT / "archive" / "stubs"
        archive_stubs.mkdir(parents=True, exist_ok=True)
        moved = 0
        for f in results["DEAD"]:
            dest = archive_stubs / f.name
            if dest.exists():
                print(f"  SKIP (exists): {f.name}")
                continue
            shutil.move(str(f), str(dest))
            print(f"  MOVED: {f.relative_to(ROOT)} -> archive/stubs/{f.name}")
            moved += 1
        print(f"\n{moved} Dateien verschoben nach archive/stubs/")

    if args.update_doc:
        doc_path = ROOT / "docs" / "STUB_INVENTORY.md"
        lines = [
            "# MUSCAL CORE — Stub Inventory",
            "",
            f"**Automatisch generiert:** 2026-07-10",
            f"**Schwellwert:** < {THRESHOLD} Zeilen",
            "",
            "## Zusammenfassung",
            "",
            f"| Kategorie | Anzahl |",
            f"|-----------|--------|",
            f"| DEAD | {len(results['DEAD'])} |",
            f"| MINIMAL | {len(results['MINIMAL'])} |",
            f"| ACTIVE | {len(results['ACTIVE'])} |",
            f"| __init__ | {len(results['__init__']) + len(results['__init__+'])} |",
            "",
        ]
        if results["DEAD"]:
            lines.append("## DEAD Stubs\n")
            lines.append("| Datei | Zeilen |")
            lines.append("|-------|--------|")
            for f in sorted(results["DEAD"]):
                lines.append(f"| `{f.relative_to(ROOT)}` | {count_lines(f)} |")
            lines.append("")
        doc_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nDokument aktualisiert: {doc_path}")


if __name__ == "__main__":
    main()
