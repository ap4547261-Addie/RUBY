# ============================================================
# RUBY — PINECONE SEMANTIC MEMORY
# ============================================================

import os
import sys
from datetime import datetime

import requests


# ============================================================
# PROJECT ROOT
# ============================================================

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ============================================================
# PINECONE CONFIG
# ============================================================

PINECONE_API_KEY = None
PINECONE_INDEX_HOST = None
PINECONE_INDEX_NAME = "ruby"

_config_error = None


# ------------------------------------------------------------
# First: load config bundled into the APK
# ------------------------------------------------------------

try:
    from integrations.config_secrets import (
        PINECONE_API_KEY as _BUNDLED_API_KEY,
        PINECONE_INDEX_HOST as _BUNDLED_INDEX_HOST,
        PINECONE_INDEX_NAME as _BUNDLED_INDEX_NAME,
    )

    PINECONE_API_KEY = _BUNDLED_API_KEY
    PINECONE_INDEX_HOST = _BUNDLED_INDEX_HOST
    PINECONE_INDEX_NAME = _BUNDLED_INDEX_NAME or "ruby"

    print("✅ Bundled Pinecone config loaded")

except Exception as e:
    _config_error = repr(e)

    print(
        f"⚠️ Bundled Pinecone config failed: {_config_error}"
    )

    PINECONE_API_KEY = None
    PINECONE_INDEX_HOST = None
    PINECONE_INDEX_NAME = "ruby"


# ------------------------------------------------------------
# Second: environment variables as fallback
# ------------------------------------------------------------

if not PINECONE_API_KEY:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_INDEX_HOST:
    PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")

if not PINECONE_INDEX_NAME:
    PINECONE_INDEX_NAME = os.getenv(
        "PINECONE_INDEX_NAME",
        "ruby",
    )


# ============================================================
# DIAGNOSTIC FILE
# ============================================================

try:
    _storage_path = os.getenv(
        "FLET_APP_STORAGE_DATA",
        ".",
    )

    _log_path = os.path.join(
        _storage_path,
        "pinecone_debug.txt",
    )

    with open(
        _log_path,
        "w",
        encoding="utf-8",
    ) as _f:

        _f.write(
            f"PROJECT_ROOT: {_PROJECT_ROOT}\n"
        )

        _f.write(
            "CONFIG_FILE: "
            f"{os.path.exists(os.path.join(_PROJECT_ROOT, 'integrations', 'config_secrets.py'))}\n"
        )

        _f.write(
            "API_KEY: "
            + (
                f"SET len={len(PINECONE_API_KEY)}"
                if PINECONE_API_KEY
                else "NOT SET"
            )
            + "\n"
        )

        _f.write(
            "HOST: "
            + (
                "SET"
                if PINECONE_INDEX_HOST
                else "NOT SET"
            )
            + "\n"
        )

        _f.write(
            f"NAME: {PINECONE_INDEX_NAME}\n"
        )

        _f.write(
            f"CONFIG_ERROR: {_config_error}\n"
        )

except Exception as e:
    print(
        f"⚠️ Could not write Pinecone diagnostic: {e}"
    )


# ============================================================
# PINECONE SETTINGS
# ============================================================

# Your Pinecone index uses multilingual-e5-large.
# The index shown in Pinecone is dimension 1024.
EMBEDDING_DIMENSION = 1024

API_VERSION = "2025-01"


# ============================================================
# PINECONE MEMORY
# ============================================================

class PineconeMemory:

    def __init__(self, user_name="not_set"):

        self.user_name = user_name
        self.enabled = False
        self.host = None
        self.api_key = None

        # ----------------------------------------------------
        # Validate configuration
        # ----------------------------------------------------

        if PINECONE_API_KEY and PINECONE_INDEX_HOST:

            self.api_key = PINECONE_API_KEY

            self.host = PINECONE_INDEX_HOST.rstrip("/")

            if not self.host.startswith("http"):
                self.host = "https://" + self.host

            self.enabled = True

            print(
                "🔗 Pinecone REST client ready: "
                f"{PINECONE_INDEX_NAME}"
            )

            print(
                f"🌐 Pinecone host: {self.host}"
            )

        else:

            print(
                "⚠️ Pinecone configuration incomplete."
            )

            if not PINECONE_API_KEY:
                print("   API key: MISSING")
            else:
                print("   API key: SET")

            if not PINECONE_INDEX_HOST:
                print("   Index host: MISSING")
            else:
                print("   Index host: SET")

            print(
                f"   Index name: {PINECONE_INDEX_NAME}"
            )


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
    # EMBEDDINGS
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
                    "⚠️ Pinecone Embed HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )

                return None

            data = response.json()

            values = data["data"][0]["values"]

            print(
                f"🧠 Embedding generated: "
                f"{len(values)} dimensions"
            )

            return values

        except Exception as e:

            print(
                f"⚠️ Pinecone embed failed: {e}"
            )

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
            return

        combined = (
            f"User: {user_message}\n"
            f"Ruby: {ruby_reply}"
        )

        vector = self._embed(combined)

        if not vector:
            return

        memory_id = (
            f"{self.user_name}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )

        try:

            url = (
                f"{self.host}/vectors/upsert"
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

            response = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if response.status_code not in (
                200,
                201,
            ):

                print(
                    "⚠️ Pinecone upsert HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )

            else:

                print(
                    f"💾 Pinecone memory stored: "
                    f"{memory_id}"
                )

        except Exception as e:

            print(
                f"⚠️ Pinecone store failed: {e}"
            )


    # ========================================================
    # SEARCH MEMORY
    # ========================================================

    def search(
        self,
        query,
        limit=5,
    ):

        if not self.enabled:
            return []

        vector = self._embed(query)

        if not vector:
            return []

        try:

            url = (
                f"{self.host}/query"
            )

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
                    "⚠️ Pinecone query HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )

                return []

            data = response.json()

            memories = []

            for match in data.get(
                "matches",
                [],
            ):

                metadata = match.get(
                    "metadata",
                    {},
                )

                memories.append(
                    {
                        "score": round(
                            match.get(
                                "score",
                                0,
                            ),
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

            print(
                f"⚠️ Pinecone search failed: {e}"
            )

            return []


    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    def build_context(
        self,
        user_message,
        limit=3,
    ):

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
                f"- he said: "
                f"{memory['user_message']}"
            )

            lines.append(
                f"  you replied: "
                f"{memory['ruby_reply']}"
            )

        if not lines:
            return ""

        return (
            "Semantically related memories:\n"
            + "\n".join(lines)
        )


    # ========================================================
    # ENABLED STATUS
    # ========================================================

    def is_enabled(self):

        return self.enabled


    # ========================================================
    # STATS / CONNECTION STATUS
    # ========================================================

    def stats(self):

        # ----------------------------------------------------
        # Configuration missing
        # ----------------------------------------------------

        if not self.enabled:

            return {
                "status": "error",
                "message": (
                    _config_error
                    or
                    "Pinecone API key or index host is missing"
                ),
            }

        # ----------------------------------------------------
        # Test actual Pinecone connection
        # ----------------------------------------------------

        try:

            url = (
                f"{self.host}/describe_index_stats"
            )

            response = requests.post(
                url,
                headers=self._headers(),
                json={},
                timeout=20,
            )

            if response.status_code != 200:

                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": response.text[:300],
                }

            data = response.json()

            return {
                "status": "connected",
                "total_vectors": data.get(
                    "totalVectorCount",
                    0,
                ),
            }

        except Exception as e:

            return {
                "status": "error",
                "message": str(e)[:300],
            }


    # ========================================================
    # WIPE RUBY'S PINECONE MEMORIES
    # ========================================================

    def wipe(self):

        if not self.enabled:
            return

        try:

            url = (
                f"{self.host}/vectors/delete"
            )

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

            if response.status_code not in (
                200,
                201,
            ):

                print(
                    "⚠️ Pinecone wipe HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:300]}"
                )

            else:

                print(
                    f"🗑️ Pinecone wiped for "
                    f"{self.user_name}"
                )

        except Exception as e:

            print(
                f"⚠️ Pinecone wipe failed: {e}"
            )
