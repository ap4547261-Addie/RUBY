import os
from datetime import datetime


# Try environment first (for local testing), then bundled config
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ruby-memory")

if not PINECONE_API_KEY:
    try:
        # This file is created by GitHub Actions at build time
        from config_secrets import (
            PINECONE_API_KEY,
            PINECONE_INDEX_HOST,
            PINECONE_INDEX_NAME,
        )
        print("🔑 Loaded Pinecone config from bundled secrets.")
    except ImportError:
        # Not set anywhere — Pinecone stays disabled
        pass

EMBEDDING_DIMENSION = 384


class PineconeMemory:
    """
    Ruby's semantic memory — stored in Pinecone as vector embeddings.

    Every message + reply is embedded and stored. When Ruby needs context,
    she searches by MEANING, not keywords.

    No caps. Every memory is stored forever.
    Falls back to SQLite-only if Pinecone is unavailable.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.enabled = False
        self.index = None
        self.pc = None

        if PINECONE_API_KEY:
            self._init_pinecone()

    def _init_pinecone(self):
        try:
            from pinecone import Pinecone

            self.pc = Pinecone(api_key=PINECONE_API_KEY)

            if PINECONE_INDEX_HOST:
                self.index = self.pc.Index(host=PINECONE_INDEX_HOST)
            else:
                self.index = self.pc.Index(PINECONE_INDEX_NAME)

            self.enabled = True
            print(f"🔗 Pinecone connected: {PINECONE_INDEX_NAME}")

        except Exception as e:
            print(f"⚠️ Pinecone init failed: {e}")
            print("   Falling back to SQLite-only memory.")
            self.enabled = False

    def _embed(self, text):
        if not self.pc:
            return None
        try:
            result = self.pc.inference.embed(
                model="multilingual-e5-large",
                inputs=[text],
                parameters={"input_type": "passage", "truncate": "END"},
            )
            return result.data[0].values
        except Exception as e:
            print(f"⚠️ Embedding failed: {e}")
            return None

    def store(self, user_message, ruby_reply, category="conversation", importance=3):
        if not self.enabled:
            return

        combined = f"User: {user_message}\nRuby: {ruby_reply}"
        vector = self._embed(combined)
        if not vector:
            return

        memory_id = f"{self.user_name}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        try:
            self.index.upsert(
                vectors=[{
                    "id": memory_id,
                    "values": vector,
                    "metadata": {
                        "user_name": self.user_name,
                        "user_message": user_message[:500],
                        "ruby_reply": ruby_reply[:500],
                        "category": category,
                        "importance": importance,
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                    },
                }],
            )
        except Exception as e:
            print(f"⚠️ Pinecone store failed: {e}")

    def search(self, query, limit=5):
        if not self.enabled:
            return []

        vector = self._embed(query)
        if not vector:
            return []

        try:
            result = self.index.query(
                vector=vector,
                top_k=limit,
                include_metadata=True,
                filter={"user_name": self.user_name},
            )
            memories = []
            for match in result.get("matches", []):
                meta = match.get("metadata", {})
                memories.append({
                    "score": round(match.get("score", 0), 3),
                    "user_message": meta.get("user_message", ""),
                    "ruby_reply": meta.get("ruby_reply", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "category": meta.get("category", ""),
                })
            return memories
        except Exception as e:
            print(f"⚠️ Pinecone search failed: {e}")
            return []

    def build_context(self, user_message, limit=3):
        memories = self.search(user_message, limit=limit)
        if not memories:
            return ""

        lines = []
        for m in memories:
            if m["score"] < 0.5:
                continue
            lines.append(f"- he said: {m['user_message']}")
            lines.append(f"  you replied: {m['ruby_reply']}")

        if not lines:
            return ""
        return "Semantically related memories:\n" + "\n".join(lines)

    def is_enabled(self):
        return self.enabled

    def stats(self):
        if not self.enabled:
            return {"status": "disabled"}
        try:
            info = self.index.describe_index_stats()
            return {
                "status": "connected",
                "total_vectors": info.get("total_vector_count", 0),
            }
        except Exception:
            return {"status": "error"}

    def wipe(self):
        if not self.enabled:
            return
        try:
            self.index.delete(filter={"user_name": self.user_name})
            print(f"🗑️ Pinecone wiped for {self.user_name}")
        except Exception as e:
            print(f"⚠️ Pinecone wipe failed: {e}")
