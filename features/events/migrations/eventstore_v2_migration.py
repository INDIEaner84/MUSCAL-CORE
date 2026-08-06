"""EventStore v2 additive schema migration (P0-1).

PURPOSE
-------
Adds the missing v2 fields to the canonical ``stored_events`` table in a
strictly ADDITIVE way:

* no rows are modified or deleted (legacy v1 events stay byte-identical)
* no table is recreated
* no Writer architecture change
* idempotent: running the migration multiple times is a no-op after the first
* rollback-capable: added columns are only dropped when they still carry
  default values (i.e. no data loss is possible)

ABSOLUTE CONSTRAINTS
--------------------
* Existing events: NEVER touched
* Table: NEVER recreated
* Legacy events: NEVER modified
* Writer architecture: NEVER changed

Usage
-----
    python eventstore_v2_migration.py --check <db>
    python eventstore_v2_migration.py --migrate <db> [--backup]
    python eventstore_v2_migration.py --rollback <db> [--dry-run]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

MIGRATION_VERSION = "2.0.0"

TABLE = "stored_events"

# Fields requested by the P0-1 mission. Fields that already exist in the
# current schema are skipped by the idempotency check (see `existing`).
V2_FIELDS: Dict[str, str] = {
    "event_version": "INTEGER NOT NULL DEFAULT 2",
    "source": "TEXT NOT NULL DEFAULT ''",
    "agent_id": "TEXT NOT NULL DEFAULT ''",
    "task_id": "TEXT NOT NULL DEFAULT ''",
    "previous_hash": "TEXT NOT NULL DEFAULT ''",
    "event_hash": "TEXT NOT NULL DEFAULT ''",
    "confidence": "REAL NOT NULL DEFAULT 0.0",
    "verification_state": "TEXT NOT NULL DEFAULT 'unverified'",
    "metadata": "TEXT NOT NULL DEFAULT '{}'",
}

# Columns that were added by THIS migration module (rollback scope).
MIGRATION_ADDED_FIELDS = (
    "event_version",
    "agent_id",
    "task_id",
    "previous_hash",
    "event_hash",
    "confidence",
)

# Values a rolled-back column must still carry to be droppable without data
# loss (defaults per column).
DEFAULT_VALUES = {
    "event_version": 2,
    "agent_id": "",
    "task_id": "",
    "previous_hash": "",
    "event_hash": "",
    "confidence": 0.0,
}


class MigrationError(RuntimeError):
    """Raised when the migration violates one of the absolute constraints."""


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (TABLE,),
    ).fetchone()
    return row is not None


def current_columns(conn: sqlite3.Connection) -> List[str]:
    if not table_exists(conn):
        raise MigrationError(
            f"table '{TABLE}' missing - cannot migrate; refusing to create it "
            "(absolute constraint: no table recreation)"
        )
    return [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE})").fetchall()]


def schema_status(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Report which of the v2 fields exist and which are missing."""
    cols = current_columns(conn)
    existing = [f for f in V2_FIELDS if f in cols]
    missing = [f for f in V2_FIELDS if f not in cols]
    return {
        "table": TABLE,
        "column_count_before": len(cols),
        "existing": existing,
        "missing": missing,
    }


def run_migration(db_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Apply the additive v2 migration (idempotent)."""
    conn = _connect(db_path)
    try:
        status = schema_status(conn)
        if not table_exists(conn):
            raise MigrationError("table missing - abort")
        if not status["missing"]:
            result = {
                "status": "ALREADY_UP_TO_DATE",
                "migration_version": MIGRATION_VERSION,
                "applied_columns": [],
                **status,
            }
        elif dry_run:
            result = {
                "status": "DRY_RUN",
                "migration_version": MIGRATION_VERSION,
                "would_add": status["missing"],
                **status,
            }
        else:
            conn.execute("BEGIN IMMEDIATE")
            try:
                for field in status["missing"]:
                    conn.execute(
                        f"ALTER TABLE {TABLE} ADD COLUMN {field} {V2_FIELDS[field]}"
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            applied = status["missing"]
            result = {
                "status": "MIGRATED",
                "migration_version": MIGRATION_VERSION,
                "applied_columns": applied,
                "column_count_after": len(current_columns(conn)),
                **status,
            }
        return result
    finally:
        conn.close()


def rollback_migration(db_path: Path, dry_run: bool = True) -> Dict[str, Any]:
    """Drop columns added by this migration -- ONLY when all values are the
    column defaults (no data loss possible). Refuses otherwise."""
    conn = _connect(db_path)
    try:
        cols = current_columns(conn)
        added = [c for c in MIGRATION_ADDED_FIELDS if c in cols]
        if not added:
            return {
                "status": "NOTHING_TO_ROLLBACK",
                "droppable": [],
                "refused": [],
            }

        droppable: List[str] = []
        refused: List[str] = []
        for field in added:
            default = DEFAULT_VALUES[field]
            if isinstance(default, str):
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {TABLE} WHERE {field} != ?", (default,)
                ).fetchone()[0]
            else:
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {TABLE} WHERE {field} != ?", (default,)
                ).fetchone()[0]
            if n == 0:
                droppable.append(field)
            else:
                refused.append(field)

        if refused:
            return {
                "status": "REFUSED",
                "reason": "non-default values present - rollback would lose data",
                "droppable": droppable,
                "refused": refused,
            }

        if dry_run:
            return {"status": "DRY_RUN", "droppable": droppable, "refused": []}

        conn.execute("BEGIN IMMEDIATE")
        try:
            for field in droppable:
                conn.execute(f"ALTER TABLE {TABLE} DROP COLUMN {field}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return {
            "status": "ROLLED_BACK",
            "dropped_columns": droppable,
            "column_count_after": len(current_columns(conn)),
        }
    finally:
        conn.close()


def backup_db(db_path: Path) -> Path:
    """Consistent backup copy via the SQLite backup API (no data loss)."""
    backup_path = db_path.with_name(db_path.name + ".bak-v2")
    src = _connect(db_path)
    try:
        dst = sqlite3.connect(str(backup_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(description="EventStore v2 additive migration")
    parser.add_argument("mode", choices=["check", "migrate", "rollback"])
    parser.add_argument("db", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true", help="backup before migrate")
    args = parser.parse_args()

    try:
        if args.mode == "check":
            conn = _connect(args.db)
            try:
                status = schema_status(conn)
            finally:
                conn.close()
            print(status)
        elif args.mode == "migrate":
            if args.backup:
                backup_path = backup_db(args.db)
                print(f"backup created: {backup_path}")
            result = run_migration(args.db, dry_run=args.dry_run)
            print(result)
        elif args.mode == "rollback":
            result = rollback_migration(args.db, dry_run=not args.dry_run)
            print(result)
        return 0
    except MigrationError as exc:
        print(f"MIGRATION_ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI wrapper
        print(f"UNEXPECTED_ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
