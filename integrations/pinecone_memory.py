import os
import sys
import json
import hashlib
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


# ============================================================
# LOAD BUNDLED CONFIG
# ============================================================

# The GitHub Actions workflow creates:
#
# integrations/config_secrets.py
#
# before building the APK.

try:
    from integrations.config_secrets import (
        PINECONE_API_KEY as _BUNDLED_API_KEY,
        PINECONE_INDEX_HOST as _BUNDLED_INDEX_HOST,
        PINECONE_INDEX_NAME as _BUNDLED_INDEX_NAME,
    )

    PINECONE_API_KEY = _BUNDLED_API_KEY
    PINECONE_INDEX_HOST = _BUNDLED_INDEX_HOST
    PINECONE_INDEX_NAME = (
        _BUNDLED_INDEX_NAME or "ruby"
    )

    print("✅ Bundled Pinecone config loaded")

except Exception as e:
    _config_error = repr(e)

    print(
        f"⚠️ Bundled Pinecone config failed: "
        f"{_config_error}"
    )


# ============================================================
# ENVIRONMENT FALLBACK
# ============================================================

if not PINECONE_API_KEY:
    PINECONE_API_KEY = os.getenv(
        "PINECONE_API_KEY"
    )

if not PINECONE_INDEX_HOST:
    PINECONE_INDEX_HOST = os.getenv(
        "PINECONE_INDEX_HOST"
    )

if not PINECONE_INDEX_NAME:
    PINECONE_INDEX_NAME = os.getenv(
        "PINECONE_INDEX_NAME",
        "ruby",
    )


# ============================================================
# DIAGNOSTICS
# ============================================================

# This writes a small diagnostic file to Ruby's app storage.
# IMPORTANT:
# It NEVER writes the actual API key.
# It only records whether a key exists and its length.

try:
    _log_path = os.path.join(
        os.getenv(
            "FLET_APP_STORAGE_DATA",
            ".",
        ),
        "pinecone_debug.txt",
    )

    _config_file_path = os.path.join(
        _PROJECT_ROOT,
        "integrations",
        "config_secrets.py",
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
            f"{os.path.exists(_config_file_path)}\n"
        )

        _f.write(
            "API_KEY: "
            + (
                "SET len="
                + str(len(PINECONE_API_KEY))
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

except Exception:
    pass


# ============================================================
# PINECONE SETTINGS
# ============================================================

# Your Pinecone index dimension is 1025.
#
# This constant is currently informational.
# The REST API receives the actual embedding returned
# by Pinecone's embedding service.

EMBEDDING_DIMENSION = 1024

API_VERSION = "2025-01"


# ============================================================
# PINECONE MEMORY
# ============================================================

class PineconeMemory:
    """
    Pure REST implementation.

    No pinecone-client package is required.

    Uses requests to communicate with Pinecone.

    Pinecone is considered configured when both:
        - API key exists
        - Index host exists
    """

    def __init__(self, user_name="not_set"):

        self.user_name = user_name

        self.enabled = False

        self.host = None

        # ----------------------------------------------------
        # CONFIG CHECK
        # ----------------------------------------------------

        if (
            PINECONE_API_KEY
            and PINECONE_INDEX_HOST
        ):

            self.api_key = PINECONE_API_KEY

            self.host = (
                PINECONE_INDEX_HOST
                .rstrip("/")
            )

            if not self.host.startswith(
                "http"
            ):
                self.host = (
                    "https://"
                    + self.host
                )

            self.enabled = True

            print(
                "🔗 Pinecone REST client ready: "
                f"{PINECONE_INDEX_NAME}"
            )

            print(
                f"🔗 Pinecone host: {self.host}"
            )

        else:

            print(
                "ℹ️ Pinecone not configured. "
                "Using SQLite-only memory."
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
    # EMBEDDING
    # ========================================================

    def _embed(self, text):
        """
        Use Pinecone's hosted embedding inference API.
        """

        try:

            url = (
                "https://api.pinecone.io/embed"
            )

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

            r = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if r.status_code != 200:

                print(
                    "⚠️ Embed HTTP "
                    f"{r.status_code}: "
                    f"{r.text[:300]}"
                )

                return None

            data = r.json()

            values = data["data"][0]["values"]

            print(
                "🧮 Pinecone embedding "
                f"dimension: {len(values)}"
            )

            return values

        except Exception as e:

            print(
                f"⚠️ Embed failed: {e}"
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

        vector = self._embed(
            combined
        )

        if not vector:
            return

        memory_id = (
            f"{self.user_name}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )

        try:

            url = (
                f"{self.host}"
                "/vectors/upsert"
            )

            body = {
                "vectors": [
                    {
                        "id": memory_id,

                        "values": vector,

                        "metadata": {
                            "user_name": self.user_name,

                            "user_message":
                                user_message[:500],

                            "ruby_reply":
                                ruby_reply[:500],

                            "category":
                                category,

                            "importance":
                                importance,

                            "timestamp":
                                datetime.now().isoformat(
                                    timespec="seconds"
                                ),
                        },
                    }
                ]
            }

            r = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if r.status_code not in (
                200,
                201,
            ):

                print(
                    "⚠️ Upsert HTTP "
                    f"{r.status_code}: "
                    f"{r.text[:300]}"
                )

            else:

                print(
                    "✅ Pinecone memory stored: "
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

        vector = self._embed(
            query
        )

        if not vector:
            return []

        try:

            url = (
                f"{self.host}"
                "/query"
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

            r = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if r.status_code != 200:

                print(
                    "⚠️ Query HTTP "
                    f"{r.status_code}: "
                    f"{r.text[:300]}"
                )

                return []

            data = r.json()

            memories = []

            for m in data.get(
                "matches",
                [],
            ):

                meta = m.get(
                    "metadata",
                    {},
                )

                memories.append(
                    {
                        "score": round(
                            m.get(
                                "score",
                                0,
                            ),
                            3,
                        ),

                        "user_message":
                            meta.get(
                                "user_message",
                                "",
                            ),

                        "ruby_reply":
                            meta.get(
                                "ruby_reply",
                                "",
                            ),

                        "timestamp":
                            meta.get(
                                "timestamp",
                                "",
                            ),

                        "category":
                            meta.get(
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

        for m in memories:

            if m["score"] < 0.5:
                continue

            lines.append(
                "- he said: "
                f"{m['user_message']}"
            )

            lines.append(
                "  you replied: "
                f"{m['ruby_reply']}"
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
    # PINECONE STATS / CONNECTION
    # ========================================================

    def stats(self):

        if not self.enabled:

            return {
                "status": "disabled"
            }

        try:

            url = (
                f"{self.host}"
                "/describe_index_stats"
            )

            r = requests.post(
                url,
                headers=self._headers(),
                json={},
                timeout=20,
            )

            if r.status_code != 200:

                print(
                    "⚠️ Pinecone stats HTTP "
                    f"{r.status_code}: "
                    f"{r.text[:300]}"
                )

                return {
                    "status": "error",
                    "code": r.status_code,
                }

            data = r.json()

            return {
                "status": "connected",

                "total_vectors":
                    data.get(
                        "totalVectorCount",
                        0,
                    ),
            }

        except Exception as e:

            print(
                f"⚠️ Pinecone stats failed: {e}"
            )

            return {
                "status": "error",
                "message": str(e)[:100],
            }

    # ========================================================
    # WIPE PINECONE MEMORY
    # ========================================================

    def wipe(self):

        if not self.enabled:
            return

        try:

            url = (
                f"{self.host}"
                "/vectors/delete"
            )

            body = {
                "filter": {
                    "user_name": {
                        "$eq": self.user_name
                    }
                }
            }

            r = requests.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=20,
            )

            if r.status_code == 200:

                print(
                    "🗑️ Pinecone wiped "
                    f"for {self.user_name}"
                )

            else:

                print(
                    "⚠️ Pinecone wipe HTTP "
                    f"{r.status_code}: "
                    f"{r.text[:300]}"
                )

        except Exception as e:

            print(
                f"⚠️ Pinecone wipe failed: {e}"
            )
