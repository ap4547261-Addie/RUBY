# integrations/pinecone_memory.py — Ruby V1.9
# Pinecone semantic memory with layer support for StoryCache
# AND automatic filtering of bad replies (AI-self-identification,
# false family denials, assistant behaviour).

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


# ============================================================
# BAD MEMORY FILTER
# ============================================================
# Any reply containing these markers is NEVER stored in Pinecone,
# and NEVER returned from search.
#
# Prevents Ruby from learning her own mistakes.

BAD_MEMORY_MARKERS = (
    # AI self-identification
    "i am an ai",
    "i'm an ai",
    "as an ai",
    "as a language model",
    "i am not a real person",
    "i'm not a real person",
    "i am an artificial intelligence",
    "i'm an artificial intelligence",
    "ai entities",
    "ai entity",
    "virtual world",
    "virtual entity",
    "in my own virtual",

    # Assistant behaviour
    "how can i assist",
    "how can i help you today",
    "how may i assist",
    "how may i help",
    "i'm here to help",
    "i am here to help",
    "how can i be of service",
    "let me know how i can help",

    # Denying family
    "i don't have parents",
    "i dont have parents",
    "i do not have parents",
    "i don't have a family",
    "i dont have a family",
    "i do not have a family",
    "i don't have any family",
    "i dont have any family",
    "i have no family",
    "no family members",
    "i don't have siblings",
    "i dont have siblings",
    "i don't have brothers",
    "i don't have sisters",
    "i don't have a mother",
    "i don't have a father",
    "i dont have a father",
    "i dont have a mother",

    # Denying childhood
    "i was never born",
    "i wasn't born",
    "i do not have a childhood",
    "i don't have a childhood",
)


def _is_bad_memory(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    return any(marker in low for marker in BAD_MEMORY_MARKERS)


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
        if not self.enabled:
            return

        # Block bad replies from being stored
        if _is_bad_memory(ruby_reply):
            print("🚫 blocked bad reply from being stored")
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
        if not self.enabled:
            return []

        vector = self._embed(query)
        if not vector:
            return []

        query_filter = {"user_name": {"$eq": self.user_name}}

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
                reply = meta.get("ruby_reply", "")

                # Filter bad memories from results
                if _is_bad_memory(reply):
                    print("🚫 filtered bad memory from search")
                    continue

                out.append({
                    "score": round(m.get("score", 0), 4),
                    "user_message": meta.get("user_message", ""),
                    "ruby_reply": reply,
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
