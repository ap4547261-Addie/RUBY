# integrations/pinecone_memory.py — Ruby V1.9
# Pinecone semantic memory with layer support for StoryCache.

import os
import json
from datetime import datetime

import requests

# ============================================================
# PLACEHOLDERS — workflow injects real values at build time
# DO NOT put real keys here
# ============================================================
PINECONE_API_KEY    = "pcsk_3wtXBp_SsRhsVutqJDGz3tpTeUTx14CdFFAkvPX1kY34DZh8Gi9kaFHK9VgwUaW3njkS4g"
PINECONE_INDEX_HOST = "https://ruby-64ic35r.svc.aped-4627-b74a.pinecone.io"
PINECONE_INDEX_NAME = "ruby"
# ============================================================

DEBUG_INFO = (
    f"key_len={len(PINECONE_API_KEY) if PINECONE_API_KEY else 0}, "
    f"host={PINECONE_INDEX_HOST[:30] if PINECONE_INDEX_HOST else 'EMPTY'}, "
    f"name={PINECONE_INDEX_NAME}"
)

try:
    _lp = os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "pc_debug.txt")
    with open(_lp, "w", encoding="utf-8") as _f:
        _f.write(DEBUG_INFO + "\n")
except Exception:
    pass

API_VERSION = "2025-01"


class PineconeMemory:
    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.enabled = False
        self.host = None
        self.api_key = None

        if not PINECONE_API_KEY or PINECONE_API_KEY == "PLACEHOLDER_API_KEY":
            print("ℹ️ Pinecone: API key not set")
            return
        if not PINECONE_INDEX_HOST or PINECONE_INDEX_HOST == "PLACEHOLDER_INDEX_HOST":
            print("ℹ️ Pinecone: host not set")
            return

        self.api_key = PINECONE_API_KEY
        self.host = PINECONE_INDEX_HOST.rstrip("/")
        if not self.host.startswith("http"):
            self.host = "https://" + self.host
        self.enabled = True
        print(f"🔗 Pinecone ready: {PINECONE_INDEX_NAME}")

    # ============================================================
    # HEADERS
    # ============================================================

    def _headers(self):
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": API_VERSION,
        }

    # ============================================================
    # EMBEDDING
    # ============================================================

    def _embed(self, text):
        try:
            r = requests.post(
                "https://api.pinecone.io/embed",
                headers=self._headers(),
                json={
                    "model": "multilingual-e5-large",
                    "inputs": [{"text": text}],
                    "parameters": {"input_type": "passage", "truncate": "END"},
                },
                timeout=20,
            )
            if r.status_code != 200:
                return None
            return r.json()["data"][0]["values"]
        except Exception:
            return None

    # ============================================================
    # STORE
    # ============================================================

    def store(
        self,
        user_message,
        ruby_reply,
        category="conversation",
        importance=3,
        layer=None,
    ):
        """
        Store a memory in Pinecone.

        Optional `layer` is written to metadata so StoryCache can
        filter reads by memory layer (e.g., "childhood").
        """

        if not self.enabled:
            return

        vector = self._embed(f"User: {user_message}\nRuby: {ruby_reply}")
        if not vector:
            return

        mid = f"{self.user_name}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        metadata = {
            "user_name": self.user_name,
            "user_message": user_message[:500],
            "ruby_reply": ruby_reply[:500],
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

        if layer:
            metadata["layer"] = str(layer)

        try:
            requests.post(
                f"{self.host}/vectors/upsert",
                headers=self._headers(),
                json={"vectors": [{
                    "id": mid,
                    "values": vector,
                    "metadata": metadata,
                }]},
                timeout=20,
            )
        except Exception as e:
            print(f"⚠️ store failed: {e}")

    # ============================================================
    # SEARCH
    # ============================================================

    def search(self, query, limit=5, filter=None):
        """
        Search Pinecone for memories similar to `query`.

        `filter` (optional) is merged with the user_name filter.
        Example:
            filter={"category": "told_memory", "layer": "childhood"}
        """

        if not self.enabled:
            return []

        vector = self._embed(query)
        if not vector:
            return []

        # Build combined filter
        query_filter = {
            "user_name": {"$eq": self.user_name},
        }

        if filter and isinstance(filter, dict):
            for k, v in filter.items():
                if isinstance(v, dict):
                    query_filter[k] = v
                else:
                    query_filter[k] = {"$eq": v}

        try:
            r = requests.post(
                f"{self.host}/query",
                headers=self._headers(),
                json={
                    "vector": vector,
                    "topK": limit,
                    "includeMetadata": True,
                    "filter": query_filter,
                },
                timeout=20,
            )
            if r.status_code != 200:
                return []

            out = []
            for m in r.json().get("matches", []):
                meta = m.get("metadata", {}) or {}
                out.append({
                    "score": round(m.get("score", 0), 4),
                    "user_message": meta.get("user_message", ""),
                    "ruby_reply": meta.get("ruby_reply", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "category": meta.get("category", ""),
                    "layer": meta.get("layer", ""),
                    "metadata": meta,
                })
            return out

        except Exception as e:
            print(f"⚠️ search failed: {e}")
            return []

    # ============================================================
    # CONTEXT BUILDER
    # ============================================================

    def build_context(self, user_message, limit=3):
        """
        Build a prompt-friendly context block from relevant memories.
        Only memories with score >= 0.5 are included.
        """

        mems = self.search(user_message, limit=limit)
        if not mems:
            return ""

        lines = []
        for m in mems:
            if m["score"] < 0.5:
                continue
            lines.append(f"- he said: {m['user_message']}")
            lines.append(f"  you replied: {m['ruby_reply']}")

        return ("Semantically related memories:\n" + "\n".join(lines)) if lines else ""

    # ============================================================
    # STATUS
    # ============================================================

    def is_enabled(self):
        return self.enabled

    def stats(self):
        if not self.enabled:
            return {"status": "disabled", "debug": DEBUG_INFO}

        try:
            r = requests.post(
                f"{self.host}/describe_index_stats",
                headers=self._headers(),
                json={},
                timeout=20,
            )
            if r.status_code != 200:
                return {
                    "status": "error",
                    "code": r.status_code,
                    "debug": DEBUG_INFO,
                }

            return {
                "status": "connected",
                "total_vectors": r.json().get("totalVectorCount", 0),
                "debug": DEBUG_INFO,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)[:100],
                "debug": DEBUG_INFO,
            }

    # ============================================================
    # WIPE
    # ============================================================

    def wipe(self):
        """Delete all memories for this user."""

        if not self.enabled:
            return

        try:
            requests.post(
                f"{self.host}/vectors/delete",
                headers=self._headers(),
                json={"filter": {"user_name": {"$eq": self.user_name}}},
                timeout=20,
            )
        except Exception:
            pass
