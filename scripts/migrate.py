#!/usr/bin/env python3
"""
Database migration script for Call It a Day.
Run this after updating to apply schema changes.
Each migration checks before applying — safe to run multiple times.

Usage:
    python3 scripts/migrate.py [/path/to/callitaday.db]

Default path: /var/lib/callitaday/callitaday.db
"""

import sqlite3
import sys
import os


def columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def run(db_path):
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    applied = []

    # ── Migrations ────────────────────────────────────────────────────────────

    # Add is_work to active_sessions (default true for existing rows)
    if "is_work" not in columns(cur, "active_sessions"):
        cur.execute(
            "ALTER TABLE active_sessions ADD COLUMN is_work BOOLEAN NOT NULL DEFAULT 1"
        )
        applied.append("active_sessions.is_work")

    # ── End of migrations ─────────────────────────────────────────────────────

    conn.commit()
    conn.close()

    if applied:
        for m in applied:
            print(f"  applied: {m}")
        print(f"{len(applied)} migration(s) applied.")
    else:
        print("Already up to date.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/var/lib/callitaday/callitaday.db"
    run(path)
