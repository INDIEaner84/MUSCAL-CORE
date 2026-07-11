#!/usr/bin/env python3
"""
confidence_guard.py — Schutz gegen Confidence-Drift in SIGNAL_RULES.

Prueft ob die Confidence-Adjustments die erlaubten Grenzen
ueberschreiten oder eine kritische Drift zeigen.

Nutzung:
    python guards/confidence_guard.py              # Pruefen
    python guards/confidence_guard.py --auto-reset # Auto-Reset bei Drift
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mkc_rules import (
    SIGNAL_RULES, CONFIDENCE_RANGE,
    get_signal_rules_snapshot, reset_state
)

# Schwellwerte
DRIFT_WARNING = 0.15    # Warnung bei Drift > 0.15
DRIFT_CRITICAL = 0.25   # Kritisch bei Drift > 0.25


def check_drift() -> dict:
    """Prueft Confidence-Drift und gibt Status zurueck."""
    snapshot = get_signal_rules_snapshot()
    issues = []

    for section, rules in snapshot.items():
        adj = rules["adjustment"]
        base = rules["base_confidence"]
        effective = base + adj

        # Grenzen pruefen
        if adj < CONFIDENCE_RANGE["min"]:
            issues.append({
                "section": section,
                "type": "UNDERFLOW",
                "adjustment": adj,
                "threshold": CONFIDENCE_RANGE["min"],
                "severity": "CRITICAL"
            })
        elif adj > CONFIDENCE_RANGE["max"]:
            issues.append({
                "section": section,
                "type": "OVERFLOW",
                "adjustment": adj,
                "threshold": CONFIDENCE_RANGE["max"],
                "severity": "CRITICAL"
            })

        # Absolute Drift pruefen
        abs_adj = abs(adj)
        if abs_adj >= DRIFT_CRITICAL:
            issues.append({
                "section": section,
                "type": "CRITICAL_DRIFT",
                "adjustment": adj,
                "threshold": DRIFT_CRITICAL,
                "severity": "CRITICAL"
            })
        elif abs_adj >= DRIFT_WARNING:
            issues.append({
                "section": section,
                "type": "WARNING_DRIFT",
                "adjustment": adj,
                "threshold": DRIFT_WARNING,
                "severity": "WARNING"
            })

        # Effektive Confidence pruefen
        if effective < 0.3:
            issues.append({
                "section": section,
                "type": "LOW_EFFECTIVE",
                "effective": effective,
                "threshold": 0.3,
                "severity": "WARNING"
            })

    return {
        "snapshot": snapshot,
        "issues": issues,
        "status": "CRITICAL" if any(i["severity"] == "CRITICAL" for i in issues)
                  else "WARNING" if issues
                  else "OK"
    }


def main():
    parser = argparse.ArgumentParser(description="MUSCAL CORE Confidence Guard")
    parser.add_argument("--auto-reset", action="store_true",
                        help="Auto-Reset bei kritischer Drift")
    args = parser.parse_args()

    result = check_drift()
    snapshot = result["snapshot"]
    issues = result["issues"]
    status = result["status"]

    # Snapshot ausgeben
    print("\nCONFIDENCE SNAPSHOT:")
    for section, rules in snapshot.items():
        adj = rules["adjustment"]
        effective = rules["base_confidence"] + adj
        flag = ""
        if abs(adj) >= DRIFT_CRITICAL:
            flag = " << CRITICAL"
        elif abs(adj) >= DRIFT_WARNING:
            flag = " << WARNING"
        print(f"  {section:15s} base={rules['base_confidence']:.2f} "
              f"adj={adj:+.2f} eff={effective:.2f}{flag}")

    # Issues ausgeben
    if issues:
        print(f"\nDRIFT ISSUES ({len(issues)}):")
        for issue in issues:
            sev = issue["severity"]
            print(f"  [{sev}] {issue['section']}: {issue['type']}")
    else:
        print("\nNo drift issues detected.")

    # Status
    symbol = {"OK": "OK", "WARNING": "WARN", "CRITICAL": "FAIL"}[status]
    print(f"\nCONFIDENCE GUARD: {symbol}")

    if status == "CRITICAL" and args.auto_reset:
        print("\nAUTO-RESET: Setting all adjustments to 0.0")
        reset_state()
        print("State reset complete.")

    sys.exit(1 if status == "CRITICAL" else 0)


if __name__ == "__main__":
    main()
