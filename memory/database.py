import sqlite3
import os


DB_PATH = os.path.join(os.path.dirname(__file__), "ruby_memory.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Episodes: raw conversations
    c.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ruby_reply TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            importance INTEGER DEFAULT 3
        )
    """)

    # Facts: semantic memory about the user (e.g. "name" -> "Addie")
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

    # Relationship: trust level, message count, mood toward user
    c.execute("""
        CREATE TABLE IF NOT EXISTS relationship (
            id INTEGER PRIMARY KEY,
            user_name TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            trust_level INTEGER DEFAULT 0,
            mood TEXT DEFAULT 'guarded',
            last_updated TEXT
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_ep_ts ON episodes(timestamp DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_fact_sub ON facts(subject)")

    conn.commit()
    conn.close()
    print("✅ Memory database initialized.")
