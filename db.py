import sqlite3
from pathlib import Path
import logging
from fastapi import HTTPException

from jobapp_tracker.web_app.models import JobInfo

DB_PATH = Path(__file__).parent / "jobapp.db"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def create_tables():

    try:
        with sqlite3.connect(DB_PATH) as dbconn:

            dbconn.execute(
                """CREATE TABLE IF NOT EXISTS job_applications (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL,              -- e.g. ISO-8601 from Python
                job_url       TEXT,
                job_text      TEXT NOT NULL,
                resume_choice TEXT,
                job_title     TEXT,
                salary        TEXT,
                job_summary   TEXT
                );"""
                )
            dbconn.commit()
    except (sqlite3.Error, OSError) as e:
        logger.exception("create_tables failed")
        raise HTTPException(503, "Could not connect to database.")


def add_job(info_to_add: JobInfo) -> None:
    try:
        with sqlite3.connect(DB_PATH) as dbconn:
            dbconn.execute(
                """
            INSERT into job_applications (
                created_at, job_url, job_text, resume_choice,
                job_title, salary, job_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?) 
            """,
            (info_to_add.created_at, 
            info_to_add.job_url, 
            info_to_add.job_text,
            info_to_add.resume_choice, 
            info_to_add.job_title, 
            info_to_add.salary,
            info_to_add.job_summary
            ),
        )
        dbconn.commit()
    except (sqlite3.Error, OSError) as e:
        logger.exception("add_job failed", exc_info=True)
        raise HTTPException(503, "Could not save job")

def del_job(job_id: int) -> int:
    """Delete a row by id. Returns number of rows removed (0 if id did not exist)."""
    try:
        with sqlite3.connect(DB_PATH) as dbconn:
            cur = dbconn.execute(
                "DELETE FROM job_applications WHERE id = ?",
                (job_id,),
            )
            dbconn.commit()
            return int(cur.rowcount)
    except (sqlite3.Error, OSError) as e:
        logger.exception("del_job failed", exc_info=True)
        raise HTTPException(503, "Could not delete job") from e


def get_jobs():
    try:
        with sqlite3.connect(DB_PATH) as dbconn:     
            dbconn.row_factory = sqlite3.Row

            cur = dbconn.execute(
                """
                SELECT id, created_at, job_url, job_text, resume_choice,
                       job_title, salary, job_summary
                FROM job_applications
                ORDER BY id DESC
                """)
            #OR
            # cur = dbconn.execute("""SELECT * FROM job_applications""")
            # jobs = cur.fetchall()
            return [dict(row) for row in cur.fetchall()]

    except (sqlite3.Error, OSError) as e:
        logger.exception("get_jobs failed", exc_info=True)
        raise HTTPException(503, "Could not load jobs")
