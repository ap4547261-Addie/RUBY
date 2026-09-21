# memory/database.py
# Ruby's SQLite layer. Stores episodes, facts, relationship state.
# On Android, data must live in FLET_APP_STORAGE_DATA (writable).
# On desktop, falls back to the app directory.

import sqlite3
import os


def _db_path() -> str:
    # Android (and any Flet runtime) exposes a writable directory here.
    storage = os.getenv("FLET_APP_STORAGE_DATA")
    if storage:
        try:
            os.makedirs(storage, exist_ok=True)
            return os.path.join(storage, "ruby_memory.db")
        except Exception as e:
            print(f"⚠️ Could not use FLET_APP_STORAGE_DATA: {e}")

    # Desktop fallback
    return os.path.join(os.path.dirname(__file__), "ruby_memory.db")


DB_PATH = _db_path()


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # -------- Episodes: raw conversations --------
    c.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ruby_reply TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            importance INTEGER DEFAULT 3
        )
    """)

    # -------- Facts: semantic memory about the user --------
    c.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(subject, key)
        )
    """)

    # -------- Relationship: continuous emotional dimensions --------
    c.execute("""
        CREATE TABLE IF NOT EXISTS relationship (
            id INTEGER PRIMARY KEY,
            user_name TEXT UNIQUE NOT NULL,
            message_count INTEGER DEFAULT 0,
            trust REAL DEFAULT 0.0,
            familiarity REAL DEFAULT 0.0,
            attachment REAL DEFAULT 0.0,
            respect REAL DEFAULT 0.0,
            last_updated TEXT
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_ep_ts ON episodes(timestamp DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_fact_sub ON facts(subject)")

    conn.commit()
    conn.close()
    print(f"✅ Memory database initialized at {DB_PATH}")
