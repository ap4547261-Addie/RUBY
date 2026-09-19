import os
import json
from datetime import datetime

import requests

# ============================================================
# PASTE YOUR REAL VALUES HERE (between the quotes)
# ============================================================
PINECONE_API_KEY    = "pcsk_3wtXBp_SsRhsVutqJDGz3tpTeUTx14CdFFAkvPX1kY34DZh8Gi9kaFHK9VgwUaW3njkS4g"
PINECONE_INDEX_HOST = "https://ruby-64ic35r.svc.aped-4627-b74a.pinecone.io"
PINECONE_INDEX_NAME = "ruby"
# ============================================================

# Debug string — shown in Settings so we can SEE what loaded
DEBUG_INFO = (
    f"key_len={len(PINECONE_API_KEY) if PINECONE_API_KEY else 0}, "
    f"host={PINECONE_INDEX_HOST[:30] if PINECONE_INDEX_HOST else 'EMPTY'}, "
    f"name={PINECONE_INDEX_NAME}"
)

# Write to file so we can read on phone
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

        if not PINECONE_API_KEY or PINECONE_API_KEY == "PASTE_KEY_HERE":
            print("ℹ️ Pinecone: API key not set")
            return
        if not PINECONE_INDEX_HOST or PINECONE_INDEX_HOST == "PASTE_HOST_HERE":
            print("ℹ️ Pinecone: host not set")
            return

        self.api_key = PINECONE_API_KEY
        self.host = PINECONE_INDEX_HOST.rstrip("/")
        if not self.host.startswith("http"):
            self.host = "https://" + self.host
        self.enabled = True
        print(f"🔗 Pinecone ready: {PINECONE_INDEX_NAME}")

    def _headers(self):
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": API_VERSION,
        }

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

    def store(self, user_message, ruby_reply, category="conversation", importance=3):
        if not self.enabled:
            return
        vector = self._embed(f"User: {user_message}\nRuby: {ruby_reply}")
        if not vector:
            return
        mid = f"{self.user_name}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        try:
            requests.post(
                f"{self.host}/vectors/upsert",
                headers=self._headers(),
                json={"vectors": [{
                    "id": mid,
                    "values": vector,
                    "metadata": {
                        "user_name": self.user_name,
                        "user_message": user_message[:500],
                        "ruby_reply": ruby_reply[:500],
                        "category": category,
                        "importance": importance,
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                    },
                }]},
                timeout=20,
            )
        except Exception as e:
            print(f"⚠️ store failed: {e}")

    def search(self, query, limit=5):
        if not self.enabled:
            return []
        vector = self._embed(query)
        if not vector:
            return []
        try:
            r = requests.post(
                f"{self.host}/query",
                headers=self._headers(),
                json={
                    "vector": vector,
                    "topK": limit,
                    "includeMetadata": True,
                    "filter": {"user_name": {"$eq": self.user_name}},
                },
                timeout=20,
            )
            if r.status_code != 200:
                return []
            out = []
            for m in r.json().get("matches", []):
                meta = m.get("metadata", {})
                out.append({
                    "score": round(m.get("score", 0), 3),
                    "user_message": meta.get("user_message", ""),
                    "ruby_reply": meta.get("ruby_reply", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "category": meta.get("category", ""),
                })
            return out
        except Exception:
            return []

    def build_context(self, user_message, limit=3):
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
                return {"status": "error", "code": r.status_code, "debug": DEBUG_INFO}
            return {
                "status": "connected",
                "total_vectors": r.json().get("totalVectorCount", 0),
                "debug": DEBUG_INFO,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)[:100], "debug": DEBUG_INFO}

    def wipe(self):
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
