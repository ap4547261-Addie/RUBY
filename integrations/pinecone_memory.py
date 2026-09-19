import os
import sys
from datetime import datetime

import requests


# ============================================================
# BUILD-TIME PINECONE CONFIG
# GitHub Actions replaces these values during APK build.
# ============================================================

# === BUILD_TIME_PINECONE_CONFIG ===
PINECONE_API_KEY = ""
PINECONE_INDEX_HOST = ""
PINECONE_INDEX_NAME = "ruby"
# === END_BUILD_TIME_PINECONE_CONFIG ===


# ============================================================
# RUNTIME FALLBACK
# ============================================================

# Environment variables can still override the build values.
PINECONE_API_KEY = os.getenv(
    "PINECONE_API_KEY",
    PINECONE_API_KEY,
)

PINECONE_INDEX_HOST = os.getenv(
    "PINECONE_INDEX_HOST",
    PINECONE_INDEX_HOST,
)

PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    PINECONE_INDEX_NAME or "ruby",
)


# ============================================================
# CONSTANTS
# ============================================================

API_VERSION = "2025-01"

# Your Pinecone index dimension.
# This value is informational here; Pinecone validates the
# actual vector dimension on upsert.
EMBEDDING_DIMENSION = 1025


# ============================================================
# PINECONE MEMORY
# ============================================================

class PineconeMemory:
    def __init__(self, user_name="not_set"):
        self.user_name = user_name

        self.enabled = False
        self.connected = False
        self.host = None
        self.api_key = None
        self.index_name = PINECONE_INDEX_NAME

        # ----------------------------------------------------
        # Validate configuration
        # ----------------------------------------------------

        if not PINECONE_API_KEY:
            print("❌ Pinecone API key is missing.")
            return

        if not PINECONE_INDEX_HOST:
            print("❌ Pinecone index host is missing.")
            return

        # ----------------------------------------------------
        # Prepare configuration
        # ----------------------------------------------------

        self.api_key = PINECONE_API_KEY.strip()
        self.host = PINECONE_INDEX_HOST.strip().rstrip("/")

        if not self.host.startswith("http://") and not self.host.startswith("https://"):
            self.host = "https://" + self.host

        self.index_name = (PINECONE_INDEX_NAME or "ruby").strip()

        # Configuration exists.
        self.enabled = True

        print("==========================================")
        print("🔗 PINECONE CONFIGURATION")
        print("==========================================")
        print(f"API KEY: SET ({len(self.api_key)} characters)")
        print(f"INDEX NAME: {self.index_name}")
        print(f"INDEX HOST: {self.host}")
        print("ENABLED: True")
        print("==========================================")

        # ----------------------------------------------------
        # Test connection immediately
        # ----------------------------------------------------

        self._test_connection()


    # ========================================================
    # HEADERS
    # ========================================================

    def _headers(self):
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": API_VERSION,
        }


    # ========================================================
    # CONNECTION TEST
    # ========================================================

    def _test_connection(self):
        if not self.enabled:
            return False

        try:
            url = f"{self.host}/describe_index_stats"

            response = requests.post(
                url,
                headers=self._headers(),
                json={},
                timeout=15,
            )

            print(
                f"🔌 Pinecone connection test: "
                f"HTTP {response.status_code}"
            )

            if response.status_code == 200:
                self.connected = True

                try:
                    data = response.json()
                    vectors = data.get("totalVectorCount", 0)
                    print(
                        f"✅ Pinecone connected — "
                        f"{vectors} vectors"
                    )
                except Exception:
                    print("✅ Pinecone connected.")

                return True

            print(
                "❌ Pinecone connection failed: "
                f"{response.text[:300]}"
            )

            self.connected = False
            return False

        except Exception as e:
            print(f"❌ Pinecone connection error: {e}")
            self.connected = False
            return False


    # ========================================================
    # EMBEDDING
    # ========================================================

    def _embed(self, text):
        if not self.enabled:
            return None

        try:
            url = "https://api.pinecone.io/embed"

            body = {
                "model": "multilingual-e5-large",
                "inputs": [
                    {
                        "text": text
                    }
                ],
                "parameters": {
                    "input_type": "passage",
                    "truncate": "END",
                },
            }

            response = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if response.status_code != 200:
                print(
                    f"⚠️ Pinecone embedding HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )
                return None

            data = response.json()

            values = data["data"][0]["values"]

            print(
                f"🧠 Pinecone embedding generated: "
                f"{len(values)} dimensions"
            )

            return values

        except Exception as e:
            print(f"⚠️ Pinecone embedding failed: {e}")
            return None


    # ========================================================
    # STORE MEMORY
    # ========================================================

    def store(
        self,
        user_message,
        ruby_reply,
        category="conversation",
        importance=3,
    ):
        if not self.enabled:
            print("ℹ️ Pinecone store skipped: disabled.")
            return False

        combined = (
            f"User: {user_message}\n"
            f"Ruby: {ruby_reply}"
        )

        vector = self._embed(combined)

        if not vector:
            return False

        memory_id = (
            f"{self.user_name}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )

        body = {
            "vectors": [
                {
                    "id": memory_id,
                    "values": vector,
                    "metadata": {
                        "user_name": self.user_name,
                        "user_message": user_message[:500],
                        "ruby_reply": ruby_reply[:500],
                        "category": category,
                        "importance": importance,
                        "timestamp": datetime.now().isoformat(
                            timespec="seconds"
                        ),
                    },
                }
            ]
        }

        try:
            url = f"{self.host}/vectors/upsert"

            response = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if response.status_code in (200, 201):
                print(
                    f"☁️ Pinecone memory stored: "
                    f"{memory_id}"
                )
                return True

            print(
                f"⚠️ Pinecone upsert HTTP "
                f"{response.status_code}: "
                f"{response.text[:300]}"
            )

            return False

        except Exception as e:
            print(f"⚠️ Pinecone store failed: {e}")
            return False


    # ========================================================
    # SEARCH
    # ========================================================

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
                "filter": {
                    "user_name": {
                        "$eq": self.user_name
                    }
                },
            }

            response = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if response.status_code != 200:
                print(
                    f"⚠️ Pinecone query HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )
                return []

            data = response.json()

            memories = []

            for match in data.get("matches", []):
                metadata = match.get("metadata", {})

                memories.append(
                    {
                        "score": round(
                            match.get("score", 0),
                            3,
                        ),
                        "user_message": metadata.get(
                            "user_message",
                            "",
                        ),
                        "ruby_reply": metadata.get(
                            "ruby_reply",
                            "",
                        ),
                        "timestamp": metadata.get(
                            "timestamp",
                            "",
                        ),
                        "category": metadata.get(
                            "category",
                            "",
                        ),
                    }
                )

            return memories

        except Exception as e:
            print(f"⚠️ Pinecone search failed: {e}")
            return []


    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    def build_context(self, user_message, limit=3):
        memories = self.search(
            user_message,
            limit=limit,
        )

        if not memories:
            return ""

        lines = []

        for memory in memories:
            if memory["score"] < 0.5:
                continue

            lines.append(
                f"- he said: {memory['user_message']}"
            )

            lines.append(
                f"  you replied: {memory['ruby_reply']}"
            )

        if not lines:
            return ""

        return (
            "Semantically related memories:\n"
            + "\n".join(lines)
        )


    # ========================================================
    # ENABLED
    # ========================================================

    def is_enabled(self):
        return self.enabled


    # ========================================================
    # STATS
    # ========================================================

    def stats(self):
        if not self.enabled:
            return {
                "status": "disabled",
                "index_name": self.index_name,
                "host_configured": False,
                "api_key_configured": False,
            }

        try:
            url = f"{self.host}/describe_index_stats"

            response = requests.post(
                url,
                headers=self._headers(),
                json={},
                timeout=15,
            )

            if response.status_code != 200:
                print(
                    f"⚠️ Pinecone stats HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )

                return {
                    "status": "error",
                    "code": response.status_code,
                    "index_name": self.index_name,
                    "host_configured": True,
                    "api_key_configured": True,
                }

            data = response.json()

            return {
                "status": "connected",
                "total_vectors": data.get(
                    "totalVectorCount",
                    0,
                ),
                "index_name": self.index_name,
                "host_configured": True,
                "api_key_configured": True,
            }

        except Exception as e:
            print(
                f"⚠️ Pinecone stats failed: {e}"
            )

            return {
                "status": "error",
                "message": str(e)[:200],
                "index_name": self.index_name,
                "host_configured": True,
                "api_key_configured": True,
            }


    # ========================================================
    # WIPE
    # ========================================================

    def wipe(self):
        if not self.enabled:
            return False

        try:
            url = f"{self.host}/vectors/delete"

            body = {
                "filter": {
                    "user_name": {
                        "$eq": self.user_name
                    }
                }
            }

            response = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if response.status_code in (200, 201):
                print(
                    f"🗑️ Pinecone wiped for "
                    f"{self.user_name}"
                )
                return True

            print(
                f"⚠️ Pinecone wipe HTTP "
                f"{response.status_code}: "
                f"{response.text[:300]}"
            )

            return False

        except Exception as e:
            print(
                f"⚠️ Pinecone wipe failed: {e}"
            )
            return False
