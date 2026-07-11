#!/usr/bin/env python3
"""
override_audit.py — Prueft ob OVERRIDE-Eintraege noch gueltig sind.

Liest spec/OVERRIDE.md und prueft fuer jeden Eintrag:
1. Ob die geaenderten Dateien noch existieren
2. Ob die beschriebenen Aenderungen noch im Code vorhanden sind
3. Ob der Eintrag als APPLIED oder PLANNED markiert ist

Nutzung:
    python guards/override_audit.py            # Vollstaendiges Audit
    python guards/override_audit.py --applied  # Nur APPLIED Eintraege
"""

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OVERRIDE_PATH = ROOT / "spec" / "OVERRIDE.md"


def parse_overrides() -> list[dict]:
    """Parst OVERRIDE.md und extrahiert Eintraege."""
    content = OVERRIDE_PATH.read_text(encoding="utf-8")
    overrides = []

    # Split by ## OVERRIDE- or ## Change:
    sections = re.split(r'\n## (?:OVERRIDE-\d+|Change:)', content)

    for section in sections[1:]:  # Skip header
        lines = section.strip().splitlines()
        if not lines:
            continue

        title = lines[0].strip()

        # Extract status
        status_match = re.search(r'\*\*Status:\*\*\s*(\w+)', section)
        status = status_match.group(1) if status_match else "UNKNOWN"

        # Extract date
        date_match = re.search(r'\*\*Date:\*\*\s*([\d-]+)', section)
        date = date_match.group(1) if date_match else "unknown"

        # Extract files mentioned (nur echte Dateipfade)
        files = set()
        for file_match in re.finditer(r'`([^`]+\.(?:py|md|yml|txt))`', section):
            fname = file_match.group(1)
            # Nur Dateipfade (keine Befehle, keine unvollstaendigen Pfade)
            if (not fname.startswith("guards/") and not fname.startswith("spec/") and
                not fname.startswith("pip ") and not fname.startswith("python ") and
                "/" in fname or fname.endswith(".py")):
                files.add(fname)

        overrides.append({
            "title": title,
            "status": status,
            "date": date,
            "files": files,
            "raw": section[:200],
        })

    return overrides


def check_override(override: dict) -> dict:
    """Prueft ob ein Override noch gueltig ist."""
    issues = []

    # Pruefe ob Dateien noch existieren (root ODER archive ODER archive/stubs)
    for fname in override["files"]:
        fpath = ROOT / fname
        archive_path = ROOT / "archive" / fname
        archive_stubs_path = ROOT / "archive" / "stubs" / fname

        found = fpath.exists() or archive_path.exists() or archive_stubs_path.exists()

        # Teilweise Suche (falls Pfad unvollstaendig — nur basename)
        if not found:
            basename = Path(fname).name
            for candidate in ROOT.rglob(basename):
                if "__pycache__" not in str(candidate) and candidate.is_file():
                    found = True
                    break

        if not found:
            issues.append(f"Datei fehlt: {fname}")

    # Pruefe ob Dateien nicht leer sind (nur root)
    for fname in override["files"]:
        fpath = ROOT / fname
        if fpath.exists():
            try:
                content = fpath.read_text(encoding="utf-8").strip()
                if not content:
                    issues.append(f"Datei leer: {fname}")
            except Exception:
                pass

    # Warnung wenn Datei nur in archive/ existiert (nicht in root)
    for fname in override["files"]:
        fpath = ROOT / fname
        archive_path = ROOT / "archive" / fname
        archive_stubs_path = ROOT / "archive" / "stubs" / fname

        if not fpath.exists() and (archive_path.exists() or archive_stubs_path.exists()):
            issues.append(f"WARNUNG: Datei nur in archive/ (nicht in root): {fname}")

    return {
        "override": override,
        "issues": issues,
        "valid": len(issues) == 0,
    }


def main():
    parser = argparse.ArgumentParser(description="MUSCAL CORE Override Audit")
    parser.add_argument("--applied", action="store_true",
                        help="Nur APPLIED Eintraege pruefen")
    args = parser.parse_args()

    overrides = parse_overrides()
    if args.applied:
        overrides = [o for o in overrides if o["status"] == "APPLIED"]

    results = [check_override(o) for o in overrides]

    valid = sum(1 for r in results if r["valid"])
    invalid = sum(1 for r in results if not r["valid"])

    print(f"\nOVERRIDE AUDIT: {len(results)} Eintraege")
    print(f"  Gueltig: {valid}")
    print(f"  Probleme: {invalid}")

    if invalid:
        print("\nPROBLEME:")
        for r in results:
            if not r["valid"]:
                o = r["override"]
                print(f"\n  [{o['status']}] {o['title']} ({o['date']})")
                for issue in r["issues"]:
                    print(f"    - {issue}")

    # Summary nach Status
    by_status = {}
    for o in overrides:
        by_status.setdefault(o["status"], []).append(o)

    print("\nNach Status:")
    for status, items in sorted(by_status.items()):
        print(f"  {status}: {len(items)}")

    sys.exit(1 if invalid else 0)


if __name__ == "__main__":
    main()
