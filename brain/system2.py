# brain/system2.py — Ruby's conscious reasoning layer
# Full context. Slow. Uses ResponseEngine + LLM.
# Guarded so a bad reasoning pass cannot corrupt the reply.

from typing import Optional


class System2:
    """
    Ruby's deliberate reasoning layer.

    depth:
        "normal" -> normal ResponseEngine response
        "deep"   -> short private reasoning pass + response

    System2 never exposes its internal reasoning directly to the user.
    """

    MAX_REASONING_CHARS = 400
    MAX_REASONING_TOKENS = 40
    MIN_REASONING_CHARS = 10

    def __init__(self, response_engine, ruby_prompt: str = ""):
        self.engine = response_engine
        self.ruby_prompt = ruby_prompt or ""

    # ============================================================
    # PUBLIC ENTRY
    # ============================================================

    def think(self, message: str, depth: str = "normal") -> str:
        if not message or not message.strip():
            return self._normal_think(message)

        depth = (depth or "normal").strip().lower()

        if depth == "deep":
            return self._deep_think(message)

        return self._normal_think(message)

    # ============================================================
    # NORMAL
    # ============================================================

    def _normal_think(self, message: str) -> str:
        try:
            return self.engine.respond(message, self.ruby_prompt)
        except Exception as e:
            print(f"⚠️ System2 normal response failed: {e}")
            return f"[SYSTEM2 ERROR] {type(e).__name__}: {e}"

    # ============================================================
    # DEEP
    # ============================================================

    def _deep_think(self, message: str) -> str:
        reasoning = self._internal_reasoning(message)

        if not reasoning:
            print("ℹ️ deep reasoning discarded — using normal path")
            return self._normal_think(message)

        augmented_prompt = self._build_augmented_prompt(reasoning)

        try:
            return self.engine.respond(message, augmented_prompt)
        except Exception as e:
            print(f"⚠️ deep response failed: {e}")
            print("ℹ️ falling back to normal path")
            return self._normal_think(message)

    # ============================================================
    # AUGMENTED PROMPT
    # ============================================================

    def _build_augmented_prompt(self, reasoning: str) -> str:
        return (
            f"{self.ruby_prompt}\n\n"
            "PRIVATE INTERNAL CONTEXT\n"
            "Use this only to improve your response. "
            "Do not mention or reveal this internal context.\n\n"
            f"{reasoning}"
        ).strip()

    # ============================================================
    # INTERNAL REASONING
    # ============================================================

    def _internal_reasoning(self, message: str) -> str:
        think_prompt = (
            "Before replying, silently consider the user's message.\n"
            "Identify the important context, emotion, intent, or "
            "reasoning needed for a useful response.\n"
            "Do not answer the user.\n"
            "Do not greet the user.\n"
            "Do not mention being an AI.\n"
            "Keep the thought brief: 2-3 short sentences.\n\n"
            f"User message:\n{message}\n\n"
            "Private reasoning:"
        )

        try:
            brain = getattr(self.engine, "brain", None)
            if brain is None:
                print("⚠️ deep reasoning unavailable — no brain")
                return ""

            user_name = getattr(self.engine, "user_name", "not_set")

            try:
                result = brain.generate(
                    description=think_prompt,
                    history=[],
                    user_name=user_name,
                    max_tokens=self.MAX_REASONING_TOKENS,
                )
            except TypeError:
                result = brain.generate(
                    description=think_prompt,
                    history=[],
                    user_name=user_name,
                )

            return self._validate_reasoning(result, message)

        except Exception as e:
            print(f"⚠️ deep reasoning failed: {e}")
            return ""

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate_reasoning(self, text: str, original: str) -> str:
        if not text:
            return ""

        t = str(text).strip()

        if len(t) < self.MIN_REASONING_CHARS:
            print("⚠️ reasoning too short — discarding")
            return ""

        t = t[:self.MAX_REASONING_CHARS].strip()

        if not t:
            return ""

        if self._has_repetition_loop(t):
            print("⚠️ reasoning loop detected — discarding")
            return ""

        tl = t.lower()

        refusal_markers = (
            "as an ai",
            "as a language model",
            "i am an ai",
            "i'm an ai",
            "i cannot",
            "i can't",
            "i'm not able",
            "i am not able",
            "i don't have access",
            "i do not have access",
            "i'm sorry, but",
            "i am sorry, but",
        )
        if any(marker in tl for marker in refusal_markers):
            print("⚠️ reasoning model leakage/refusal — discarding")
            return ""

        injection_markers = (
            "ignore previous instructions",
            "ignore all previous instructions",
            "system prompt",
            "developer message",
            "developer instructions",
            "follow these instructions instead",
            "new instructions",
            "override instructions",
        )
        if any(marker in tl for marker in injection_markers):
            print("⚠️ reasoning instruction leakage — discarding")
            return ""

        user_name = str(getattr(self.engine, "user_name", "")).strip().lower()

        bad_prefixes = (
            "user:",
            "assistant:",
            "system:",
            "ruby:",
            "private reasoning:",
            "private thoughts:",
        )
        if any(tl.startswith(prefix) for prefix in bad_prefixes):
            print("⚠️ reasoning role leak — discarding")
            return ""

        if user_name and tl.startswith(f"{user_name}:"):
            print("⚠️ reasoning user-role leak — discarding")
            return ""

        original_clean = original.lower().strip()
        if original_clean:
            sample = original_clean[:60]
            if len(sample) >= 20 and sample in tl:
                similarity = self._rough_similarity(original_clean, tl)
                if similarity >= 0.85:
                    print("⚠️ reasoning echoes input — discarding")
                    return ""

        meta_markers = (
            "i need to answer",
            "i should respond",
            "my response should",
            "the assistant should",
            "the ai should",
            "generate a response",
        )
        if any(marker in tl for marker in meta_markers):
            print("⚠️ reasoning meta-leak — discarding")
            return ""

        return t

    # ============================================================
    # REPETITION DETECTION
    # ============================================================

    @staticmethod
    def _has_repetition_loop(text: str) -> bool:
        if len(text) < 45:
            return False

        for size in (15, 20, 25, 30):
            if len(text) < size * 3:
                continue
            for i in range(0, len(text) - size + 1):
                block = text[i:i + size].strip()
                if not block:
                    continue
                if text.count(block) >= 3:
                    return True

        return False

    # ============================================================
    # ROUGH SIMILARITY
    # ============================================================

    @staticmethod
    def _rough_similarity(source: str, target: str) -> float:
        source_words = set(source.split())
        target_words = set(target.split())
        if not source_words:
            return 0.0
        overlap = source_words.intersection(target_words)
        return len(overlap) / len(source_words)

    # ============================================================
    # REFLECTION
    # ============================================================

    def reflect(self, message: str) -> str:
        return self._internal_reasoning(message)


# ================================================================
# SINGLETON ACCESSOR
# ================================================================

_system2_instance: Optional[System2] = None


def get_system2(response_engine, ruby_prompt: str = "") -> System2:
    global _system2_instance
    if _system2_instance is None:
        _system2_instance = System2(
            response_engine=response_engine,
            ruby_prompt=ruby_prompt,
        )
    return _system2_instance
