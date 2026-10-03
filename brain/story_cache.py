# brain/story_cache.py — Ruby's rendered-memory cache.
#
# When Ruby tells a memory, save the rendered version.
# When a highly similar request appears later, reuse the existing
# story instead of unnecessarily generating the same story again.
#
# No LLM calls.
# Pinecone is optional.
#
# IMPORTANT:
# Semantic similarity is not treated as proof that two situations
# are identical. Verbatim reuse therefore requires a high threshold
# plus basic metadata checks.
#
# V1.9.1 — also filters hallucinated control tags so Ruby never
# re-learns her own broken output.

import re
from typing import Optional, Dict, Any


class StoryCache:
    """
    Semantic cache for Ruby's previously told memories.

    Modes:

        hit
            Very strong match.
            Existing story can be reused directly.

        soft
            Related match.
            Existing story is supplied as context and Ruby may
            rephrase it.

        None
            No useful cached story.

    The cache is intentionally conservative because a wrong
    memory reuse is worse than generating the story again.
    """

    # ============================================================
    # THRESHOLDS
    # ============================================================

    HIT_THRESHOLD = 0.92
    SOFT_THRESHOLD = 0.80
    MIN_STORY_LEN = 40
    MAX_STORY_LEN = 2500
    CATEGORY = "told_memory"

    # ============================================================
    # TAG FILTER
    # ============================================================
    # Matches [GENERATE_IMAGE: ...], [SAVE_MEMORY: ...], [TAG], etc.
    # Anything in square brackets that looks like a control tag.

    _TAG_PATTERN = re.compile(r"\[[A-Za-z_]+:[^\]]*\]")
    _BARE_TAG_PATTERN = re.compile(r"\[[A-Za-z_]+\]")

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        pinecone_memory,
        user_name: str = "not_set",
    ):
        self.pinecone = pinecone_memory
        self.user_name = user_name

    # ============================================================
    # LOOKUP
    # ============================================================

    def lookup(
        self,
        query: str,
        layer: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self._available():
            return None

        if not query or not query.strip():
            return None

        query = query.strip()

        try:
            matches = self._search(query, layer)
        except Exception as e:
            print(f"⚠️ story cache lookup failed: {e}")
            return None

        if not matches:
            return None

        best_soft = None

        for match in matches:
            if not isinstance(match, dict):
                continue

            if not self._is_story_match(match, layer):
                continue

            score = self._get_score(match)

            if score <= 0:
                continue

            story = self._get_story(match)

            if not story:
                continue

            if score >= self.HIT_THRESHOLD:
                print(f"🎯 story cache HIT (score={score:.2f})")
                return {
                    "mode": "hit",
                    "story": story,
                    "score": score,
                    "layer": self._get_layer(match),
                }

            if score >= self.SOFT_THRESHOLD:
                candidate = {
                    "mode": "soft",
                    "story": story,
                    "score": score,
                    "layer": self._get_layer(match),
                }
                if best_soft is None or score > best_soft["score"]:
                    best_soft = candidate

        if best_soft:
            print(f"🟡 story cache SOFT (score={best_soft['score']:.2f})")
            return best_soft

        return None

    # ============================================================
    # SEARCH
    # ============================================================

    def _search(
        self,
        query: str,
        layer: Optional[str],
    ):
        if layer:
            try:
                return self.pinecone.search(
                    query,
                    limit=8,
                    filter={
                        "category": self.CATEGORY,
                        "layer": layer,
                    },
                )
            except TypeError:
                pass

        try:
            return self.pinecone.search(
                query,
                limit=8,
                filter={"category": self.CATEGORY},
            )
        except TypeError:
            return self.pinecone.search(query, limit=8)

    # ============================================================
    # MATCH VALIDATION
    # ============================================================

    def _is_story_match(
        self,
        match: Dict[str, Any],
        requested_layer: Optional[str],
    ) -> bool:
        category = str(match.get("category", "")).strip().lower()

        if category != self.CATEGORY:
            return False

        if requested_layer:
            stored_layer = self._get_layer(match)
            if stored_layer and stored_layer != requested_layer:
                return False

        return True

    # ============================================================
    # SCORE
    # ============================================================

    @staticmethod
    def _get_score(match: Dict[str, Any]) -> float:
        try:
            score = float(match.get("score", 0))
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(score, 1.0))

    # ============================================================
    # TAG STRIPPING
    # ============================================================

    @classmethod
    def _strip_tags(cls, text: str) -> str:
        if not text:
            return ""
        text = cls._TAG_PATTERN.sub("", text)
        text = cls._BARE_TAG_PATTERN.sub("", text)
        text = " ".join(text.split()).strip()
        return text

    @classmethod
    def _has_tags(cls, text: str) -> bool:
        if not text:
            return False
        return bool(
            cls._TAG_PATTERN.search(text)
            or cls._BARE_TAG_PATTERN.search(text)
        )

    # ============================================================
    # STORY EXTRACTION
    # ============================================================

    def _get_story(
        self,
        match: Dict[str, Any],
    ) -> str:
        story = (
            match.get("ruby_reply")
            or match.get("story")
            or ""
        )

        story = str(story).strip()

        # Strip any hallucinated tags from cached stories
        story = self._strip_tags(story)

        if len(story) < self.MIN_STORY_LEN:
            return ""

        if len(story) > self.MAX_STORY_LEN:
            story = story[:self.MAX_STORY_LEN].rstrip()

        if self._is_error_reply(story):
            return ""

        return story

    # ============================================================
    # LAYER
    # ============================================================

    @staticmethod
    def _get_layer(
        match: Dict[str, Any],
    ) -> str:
        metadata = match.get("metadata")

        if isinstance(metadata, dict):
            layer = metadata.get("layer")
            if layer:
                return str(layer)

        layer = match.get("layer")
        if layer:
            return str(layer)

        return ""

    # ============================================================
    # ERROR DETECTION
    # ============================================================

    @staticmethod
    def _is_error_reply(story: str) -> bool:
        low = story.lower().strip()

        error_markers = (
            "[gen error]",
            "[system2 error]",
            "[fast error]",
            "[llm error]",
            "[error]",
        )

        return any(marker in low for marker in error_markers)

    # ============================================================
    # AVAILABILITY
    # ============================================================

    def _available(self) -> bool:
        if not self.pinecone:
            return False
        try:
            return bool(self.pinecone.is_enabled())
        except Exception:
            return False

    # ============================================================
    # STORE
    # ============================================================

    def store(
        self,
        query: str,
        story: str,
        layer: str = "memory",
    ) -> bool:
        if not self._available():
            return False

        if not query or not query.strip():
            return False

        if not story or len(story.strip()) < self.MIN_STORY_LEN:
            return False

        story = story.strip()

        # Block hallucinated control tags from being cached
        if self._has_tags(story):
            print("🚫 blocked tagged story from cache")
            return False

        if self._is_error_reply(story):
            return False

        layer = (
            str(layer).strip()
            if layer
            else "memory"
        )

        try:
            try:
                self.pinecone.store(
                    user_message=query.strip(),
                    ruby_reply=story,
                    category=self.CATEGORY,
                    importance=4,
                    layer=layer,
                )
            except TypeError:
                self.pinecone.store(
                    user_message=query.strip(),
                    ruby_reply=story,
                    category=self.CATEGORY,
                    importance=4,
                )

            print(f"💾 story cached ({len(story)} chars, layer={layer})")
            return True

        except Exception as e:
            print(f"⚠️ story cache store failed: {e}")
            return False


# ================================================================
# SINGLETON
# ================================================================

_cache_instance: Optional[StoryCache] = None


def get_story_cache(
    pinecone_memory,
    user_name: str = "not_set",
) -> StoryCache:

    global _cache_instance

    if _cache_instance is None:
        _cache_instance = StoryCache(
            pinecone_memory,
            user_name=user_name,
        )

    return _cache_instance
