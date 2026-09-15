import sqlite3
import os


DB_PATH = os.path.join(os.path.dirname(__file__), "ruby_memory.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ruby_reply TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            category TEXT DEFAULT 'conversation',
            importance INTEGER DEFAULT 3
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp
        ON memories (timestamp DESC)
    """)
    conn.commit()
    conn.close()
    print("✅ Memory database initialized.")


def insert_memory(user_message, ruby_reply, timestamp,
                  category="conversation", importance=3):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO memories (user_message, ruby_reply, timestamp, category, importance)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_message, ruby_reply, timestamp, category, importance),
    )
    conn.commit()
    conn.close()


def get_recent(limit=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT user_message, ruby_reply, timestamp
        FROM memories
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def search_by_keyword(keyword, limit=5):
    if not keyword or len(keyword) < 3:
        return []
    conn = get_connection()
    c = conn.cursor()
    like = f"%{keyword.lower()}%"
    c.execute(
        """
        SELECT user_message, ruby_reply, timestamp
        FROM memories
        WHERE LOWER(user_message) LIKE ? OR LOWER(ruby_reply) LIKE ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (like, like, limit),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def count_memories():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM memories")
    n = c.fetchone()[0]
    conn.close()
    return n


def clear_all():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM memories")
    conn.commit()
    conn.close()
    print("🗑️ All memories cleared.")
