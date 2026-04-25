#!/usr/bin/env python3
"""
One-time migration: copy rows from local jobapp.db (SQLite) to Postgres via DATABASE_URL
(target Supabase project nfgoyspfbcpnlrpmxpgv — same string as the running app).

Usage (from this repo root):
  export DATABASE_URL='postgresql://...'
  python migrate_sqlite_to_supabase.py [path/to/jobapp.db]

If the SQLite file is missing or has no table, the script exits 0.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import psycopg


def main() -> None:
    dsn = (os.environ.get("DATABASE_URL") or "").strip()
    if not dsn:
        print("MYDEBUG →", "set DATABASE_URL first")
        sys.exit(1)

    default = Path(__file__).resolve().parent / "jobapp.db"
    sqlite_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    if not sqlite_path.is_file():
        print("MYDEBUG →", f"no file at {sqlite_path}, nothing to migrate")
        sys.exit(0)

    sconn = sqlite3.connect(str(sqlite_path))
    sconn.row_factory = sqlite3.Row
    try:
        cur = sconn.execute(
            "SELECT id, created_at, job_url, job_text, resume_choice, job_title, salary, job_summary "
            "FROM job_applications"
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        print("MYDEBUG →", f"sqlite read failed: {e}")
        sconn.close()
        sys.exit(0)

    sconn.close()
    if not rows:
        print("MYDEBUG →", "0 rows in SQLite, nothing to migrate")
        sys.exit(0)

    with psycopg.connect(dsn) as pconn:
        with pconn.cursor() as c:
            for r in rows:
                d = dict(r)
                c.execute(
                    """
                    INSERT INTO job_applications (
                        id, created_at, job_url, job_text, resume_choice,
                        job_title, salary, job_summary
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        d["id"],
                        d["created_at"],
                        d["job_url"],
                        d["job_text"],
                        d["resume_choice"],
                        d["job_title"],
                        d["salary"],
                        d["job_summary"],
                    ),
                )
        pconn.commit()
        with pconn.cursor() as c:
            c.execute(
                "SELECT setval("
                "pg_get_serial_sequence('job_applications', 'id'), "
                "COALESCE((SELECT MAX(id) FROM job_applications), 1)"
                ")"
            )
        pconn.commit()

    print("MYDEBUG →", f"migrated {len(rows)} row(s) from {sqlite_path}")


if __name__ == "__main__":
    main()
