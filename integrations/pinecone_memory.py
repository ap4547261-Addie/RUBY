import os
import sys
import json
import hashlib
from datetime import datetime

import requests

# Import bundled secrets (this file is part of the app source, always bundled)
try:
    from integrations.secrets import (
        PINECONE_API_KEY,
        PINECONE_INDEX_HOST,
        PINECONE_INDEX_NAME,
    )
except ImportError:
    PINECONE_API_KEY = ""
    PINECONE_INDEX_HOST = ""
    PINECONE_INDEX_NAME = "ruby"

# Environment variables override (for local testing)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or PINECONE_API_KEY
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST") or PINECONE_INDEX_HOST
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME") or PINECONE_INDEX_NAME

# Write diagnostic to a file we can read on the phone
try:
    _log_path = os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "pinecone_debug.txt")
    with open(_log_path, "w", encoding="utf-8") as _f:
        _f.write(f"API_KEY: {'SET len=' + str(len(PINECONE_API_KEY)) if PINECONE_API_KEY else 'NOT SET'}\n")
        _f.write(f"HOST: {'SET' if PINECONE_INDEX_HOST else 'NOT SET'}\n")
        _f.write(f"NAME: {PINECONE_INDEX_NAME}\n")
except Exception:
    pass

EMBEDDING_DIMENSION = 384
API_VERSION = "2025-01"


class PineconeMemory:
    """
    Pure REST implementation. No pinecone-client needed.
    Works on any Python version. Uses `requests` which is already available.
    Silently disables itself if no API key or host.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.enabled = False
        self.host = None

        # Check for placeholder values (means secrets weren't injected)
        if PINECONE_API_KEY == "PLACEHOLDER_API_KEY":
            print("⚠️ Pinecone secrets were not injected during build.")
            print("ℹ️ Pinecone not configured. Using SQLite-only memory.")
            return

        if PINECONE_API_KEY and PINECONE_INDEX_HOST:
            self.api_key = PINECONE_API_KEY
            self.host = PINECONE_INDEX_HOST.rstrip("/")
            if not self.host.startswith("http"):
                self.host = "https://" + self.host
            self.enabled = True
            print(f"🔗 Pinecone REST client ready: {PINECONE_INDEX_NAME}")
        else:
            print("ℹ️ Pinecone not configured. Using SQLite-only memory.")

    def _headers(self):
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": API_VERSION,
        }

    def _embed(self, text):
        """Use Pinecone's hosted embedding inference API."""
        try:
            url = "https://api.pinecone.io/embed"
            body = {
                "model": "multilingual-e5-large",
                "inputs": [{"text": text}],
                "parameters": {"input_type": "passage", "truncate": "END"},
            }
            r = requests.post(url, headers=self._headers(), json=body, timeout=20)
            if r.status_code != 200:
                print(f"⚠️ Embed HTTP {r.status_code}: {r.text[:200]}")
                return None
            data = r.json()
            return data["data"][0]["values"]
        except Exception as e:
            print(f"⚠️ Embed failed: {e}")
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
            url = f"{self.host}/vectors/upsert"
            body = {
                "vectors": [{
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
                }]
            }
            r = requests.post(url, headers=self._headers(), json=body, timeout=20)
            if r.status_code not in (200, 201):
                print(f"⚠️ Upsert HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"⚠️ Pinecone store failed: {e}")

    def search(self, query, limit=5):
        if not self.enabled:
            return []
        vector = self._embed(query)
        if not vector:
            return []

        try:
            url = f"{self.host}/query"
            body = {
                "vector": vector,
                "topK": limit,
                "includeMetadata": True,
                "filter": {"user_name": {"$eq": self.user_name}},
            }
            r = requests.post(url, headers=self._headers(), json=body, timeout=20)
            if r.status_code != 200:
                print(f"⚠️ Query HTTP {r.status_code}: {r.text[:200]}")
                return []
            data = r.json()
            memories = []
            for m in data.get("matches", []):
                meta = m.get("metadata", {})
                memories.append({
                    "score": round(m.get("score", 0), 3),
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
        return ("Semantically related memories:\n" + "\n".join(lines)) if lines else ""

    def is_enabled(self):
        return self.enabled

    def stats(self):
        if not self.enabled:
            return {"status": "disabled"}
        try:
            url = f"{self.host}/describe_index_stats"
            r = requests.post(url, headers=self._headers(), json={}, timeout=20)
            if r.status_code != 200:
                return {"status": "error", "code": r.status_code}
            data = r.json()
            return {
                "status": "connected",
                "total_vectors": data.get("totalVectorCount", 0),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)[:100]}

    def wipe(self):
        if not self.enabled:
            return
        try:
            url = f"{self.host}/vectors/delete"
            body = {"filter": {"user_name": {"$eq": self.user_name}}}
            requests.post(url, headers=self._headers(), json=body, timeout=20)
            print(f"🗑️ Pinecone wiped for {self.user_name}")
        except Exception as e:
            print(f"⚠️ Pinecone wipe failed: {e}")
