# web/knowledge_ingestion.py — Store learned web content in SQLite.

import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


def _default_db_path() -> str:
    storage = os.getenv("FLET_APP_STORAGE_DATA", ".")
    return os.path.join(storage, "ruby_web.db")


class KnowledgeIngestion:
    """SQLite-backed knowledge store for web content."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _default_db_path()
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._init_db()
        print(f"📚 KnowledgeIngestion ready → {self.db_path}")

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS web_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                title TEXT,
                summary TEXT,
                keywords TEXT,
                body TEXT,
                content_hash TEXT UNIQUE,
                importance INTEGER DEFAULT 2,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS web_sources (
                url TEXT PRIMARY KEY,
                title TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                times_seen INTEGER DEFAULT 1
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_web_hash ON web_knowledge(content_hash)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_web_url ON web_knowledge(url)")
        conn.commit()
        conn.close()

    def ingest(self, learned: Dict) -> Dict:
        """Store processed web_learning output. Returns {ok, id, is_new}."""
        url = learned.get("url", "")
        title = learned.get("title", "")
        summary = learned.get("summary", "")
        keywords = learned.get("keywords", [])
        text = learned.get("text", "")
        importance = int(learned.get("importance", 2))

        if not text:
            return {"ok": False, "error": "empty text"}

        content_hash = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()

        conn = self._conn()
        c = conn.cursor()

        c.execute("SELECT id FROM web_knowledge WHERE content_hash = ?", (content_hash,))
        existing = c.fetchone()

        is_new = existing is None
        row_id = None

        if is_new:
            c.execute("""
                INSERT INTO web_knowledge
                (url, title, summary, keywords, body, content_hash, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (url, title, summary, ", ".join(keywords), text, content_hash, importance))
            row_id = c.lastrowid
        else:
            row_id = existing[0]

        # upsert source
        c.execute("""
            INSERT INTO web_sources (url, title, last_seen, times_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(url) DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                times_seen = times_seen + 1,
                title = excluded.title
        """, (url, title))

        conn.commit()
        conn.close()

        return {"ok": True, "id": row_id, "is_new": is_new, "importance": importance}

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search stored web knowledge."""
        if not query.strip():
            return []

        conn = self._conn()
        c = conn.cursor()

        pattern = f"%{query.strip()}%"
        c.execute("""
            SELECT id, url, title, summary, keywords, importance, created_at
            FROM web_knowledge
            WHERE title LIKE ? OR summary LIKE ? OR keywords LIKE ? OR body LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """, (pattern, pattern, pattern, pattern, limit))

        rows = c.fetchall()

        results = []
        for row in rows:
            c.execute("""
                UPDATE web_knowledge
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (row[0],))
            results.append({
                "id": row[0], "url": row[1], "title": row[2],
                "summary": row[3], "keywords": row[4],
                "importance": row[5], "created_at": row[6],
            })

        conn.commit()
        conn.close()
        return results

    def stats(self) -> Dict:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM web_knowledge")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM web_sources")
        sources = c.fetchone()[0]
        c.execute("SELECT SUM(access_count) FROM web_knowledge")
        total_access = c.fetchone()[0] or 0
        conn.close()
        return {
            "total_pages": total,
            "unique_sources": sources,
            "total_accesses": total_access,
        }

    def wipe(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute("DELETE FROM web_knowledge")
        c.execute("DELETE FROM web_sources")
        conn.commit()
        conn.close()


if __name__ == "__main__":
    ki = KnowledgeIngestion(db_path="test_web.db")
    print("stats:", ki.stats())
