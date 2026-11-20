"""Durable tasks storage and idempotency registry compatibility layer."""
import sqlite3
import json
import os
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(os.environ.get("AUTONOVEL_APP_DATA_DIR", Path(__file__).resolve().parent.parent)).resolve()
DB_PATH = BASE_DIR / "tasks.sqlite3"

def database_path():
    return DB_PATH

@contextmanager
def connection():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        project TEXT,
        operation TEXT,
        idem TEXT,
        state TEXT,
        pid INTEGER,
        payload TEXT
    )
    """)
    conn.commit()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def recover(db):
    pass

def read(job_id):
    with connection() as db:
        row = db.execute("SELECT payload FROM tasks WHERE id = ?", (job_id,)).fetchone()
        if not row: return None
        return json.loads(row[0])

def update(job_id, **kwargs):
    with connection() as db:
        row = db.execute("SELECT payload FROM tasks WHERE id = ?", (job_id,)).fetchone()
        if not row: return None
        job = json.loads(row[0])
        job.update(kwargs)
        state = job.get('status') or job.get('state') or 'running'
        db.execute("UPDATE tasks SET state = ?, payload = ? WHERE id = ?", (state, json.dumps(job), job_id))
        return job

def event(job_id, name, data=None):
    pass
