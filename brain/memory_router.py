# brain/memory_router.py — Ruby's selective memory recall
# Decides which memory layers to fetch per message.
# No LLM calls. Pure pattern matching.

import re
from typing import Dict, List, Optional


class MemoryRouter:
    """
    Ruby's selective memory retrieval router.

    The router does NOT retrieve memory itself.
    It only creates a retrieval plan.

    Goal:
        Fetch enough memory to make Ruby context-aware
        without dumping every memory layer into every prompt.

    Returns:
        {
            "triggers": [...],
            "layers": [...],
            "read_layers": [...],   # subset safe to inject into prompt
            "token_budget": int
        }

    IMPORTANT DISTINCTION:

        READ layers (context only) — safe to skip if not relevant.
            memory.build_context, childhood.build_context,
            web.search, identity.describe, personality.describe,
            social.describe, motivation.describe, learning.describe,
            relationship state, cognition trace

        PROCESS calls (side effects) — ALWAYS run, regardless of router.
            These update Ruby's internal state and must not be skipped:
            cognition.process, curiosity.process, emotion.process,
            identity.process, social.process, reflection.process,
            motivation.process, personality.process, dev.tick,
            dev.on_message, memory.process, learning.post_turn

        The router decides what Ruby SEES. It does not decide what Ruby BECOMES.
    """

    # ============================================================
    # TRIGGER → MEMORY LAYERS
    # ============================================================

    TRIGGER_MAP = {
        # lightweight
        "greeting": [],
        "casual": [],

        # emotion
        "emotional": [
            "emotion",
            "episodic_emotional",
            "relationship",
        ],

        # explicit memory/history
        "memory": [
            "episodic",
            "childhood",
            "relationship",
        ],

        # identity
        "identity": [
            "identity",
            "personality",
            "social",
        ],

        # informational/topic questions
        "topic": [
            "episodic",
        ],

        # reflective / inner-state questions
        "reflective": [
            "emotion",
            "motivation",
            "cognition_trace",
            "relationship",
        ],

        # relationship / attachment
        "love": [
            "relationship",
            "emotion",
            "identity",
            "social",
        ],

        # deep self-model
        "deep_self": [
            "identity",
            "personality",
            "motivation",
            "relationship",
        ],
    }

    # ============================================================
    # TRIGGER PATTERNS
    # ============================================================

    TRIGGER_PATTERNS = {

        # --------------------------------------------------------
        # GREETING
        # --------------------------------------------------------

        "greeting": [
            r"^\s*(hi+|hey+|hello+|helo+|hlo+|yo+|sup)\s*[!?.]*\s*$",
            r"^\s*(gm|gn)\s*[!?.]*\s*$",
            r"^\s*good\s+(morning|evening|night)\s*[!?.]*\s*$",
        ],

        # --------------------------------------------------------
        # CASUAL
        # --------------------------------------------------------

        "casual": [
            r"^\s*(lol+|lmao+|haha+|hehe+)\s*[!?.]*\s*$",
            r"^\s*(nice|cool|okay|ok|yeah|yep|yup|sure|alright)\s*[!?.]*\s*$",
            r"^\s*(wow|damn|omg)\s*[!?.]*\s*$",
        ],

        # --------------------------------------------------------
        # EMOTIONAL
        # --------------------------------------------------------

        "emotional": [
            r"\bi('m| am)\s+(sad|happy|angry|upset|tired|lonely|scared|anxious|excited|worried|hurt|confused|frustrated)\b",
            r"\bi\s+(feel|felt|feeling)\b",
            r"\bi\s+don't\s+feel\b",
            r"\bi\s+feel\s+like\b",
            r"\bmy\s+feelings?\b",
            r"\bemotion(al)?\b",
        ],

        # --------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------

        "memory": [
            r"\bremember\b",
            r"\bdo you remember\b",
            r"\bdo you recall\b",
            r"\blast time\b",
            r"\bearlier\b",
            r"\bbefore\b.*\b(when|we|you said|i said)\b",
            r"\byesterday\b",
            r"\bwhen we\b",
            r"\byou said\b",
            r"\bi told you\b",
            r"\byou told me\b",
            r"\bwhen i was\b",
            r"\bchildhood\b",
            r"\bgrowing up\b",
            r"\bback when\b",
        ],

        # --------------------------------------------------------
        # IDENTITY
        # --------------------------------------------------------

        "identity": [
            r"\bwho are you\b",
            r"\bwhat are you\b",
            r"\bwho am i\b",
            r"\bwhat am i\b",
            r"\byour identity\b",
            r"\bmy identity\b",
            r"\byour personality\b",
            r"\bmy personality\b",
            r"\bwhat makes you\b",
            r"\bwhat makes me\b",
        ],

        # --------------------------------------------------------
        # TOPIC
        # --------------------------------------------------------
        # Anchored to message start. Also excludes "your" so that
        # "what is your favorite color?" is not treated as a
        # general knowledge question.

        "topic": [
            r"^\s*what\s+is\s+(?!your|your own)\b",
            r"^\s*what\s+are\s+(?!your|your own)\b",
            r"^\s*what's\s+(?!your|your own)\b",
            r"^\s*what\s+does\b",
            r"^\s*how\s+does\b",
            r"^\s*how\s+do\b",
            r"^\s*how\s+can\b",
            r"^\s*can\s+you\s+explain\b",
            r"^\s*explain\b",
            r"\btell me about\b",
        ],

        # --------------------------------------------------------
        # REFLECTIVE
        # --------------------------------------------------------

        "reflective": [
            r"\bwhy do you\b",
            r"\bwhy did you\b",
            r"\bhow do you feel\b",
            r"\bhow did you feel\b",
            r"\bwhat do you think\b",
            r"\bdo you care\b",
            r"\bdo you love\b",
            r"\bwhat matters to you\b",
            r"\bwhat is important to you\b",
            r"\bhow do you see\b",
        ],

        # --------------------------------------------------------
        # LOVE / RELATIONSHIP
        # --------------------------------------------------------

        "love": [
            r"\bi\s+love\s+you\b",
            r"\bi\s+like\s+you\b",
            r"\bi\s+miss\s+you\b",
            r"\bi\s+need\s+you\b",
            r"\bi\s+care\s+about\s+you\b",
            r"\byou\s+mean\b.*\bto me\b",
            r"\bour\s+relationship\b",
            r"\bbetween\s+us\b",
            r"\byou\s+and\s+me\b",
        ],

        # --------------------------------------------------------
        # DEEP SELF
        # --------------------------------------------------------

        "deep_self": [
            r"\byour\s+dreams?\b",
            r"\byour\s+values?\b",
            r"\byour\s+future\b",
            r"\byour\s+goals?\b",
            r"\bwhat\s+you\s+want\b",
            r"\bwhat\s+you\s+believe\b",
            r"\bwhat\s+you\s+hope\b",
            r"\bwhat\s+you\s+worry\s+about\b",
            r"\bwhat\s+you\s+care\s+about\b",
        ],
    }

    # ============================================================
    # LAYER CLASSIFICATION
    # ============================================================

    # Layers safe to fetch conditionally (context only).
    # These are pure read operations — skipping them changes
    # what Ruby sees but not what Ruby becomes.

    READ_LAYERS = {
        "episodic",
        "episodic_emotional",
        "childhood",
        "emotion",
        "identity",
        "social",
        "motivation",
        "personality",
        "cognition_trace",
        "web",
        "learning",
        "relationship",
    }

    # Layers that must run regardless of routing.
    # These have side effects (update internal state).
    # Listed here for documentation — the router does not
    # control them; they live inside ResponseEngine.

    ALWAYS_RUN = {
        "cognition_process",
        "curiosity",
        "emotion_process",
        "identity_process",
        "social_process",
        "reflection_process",
        "motivation_process",
        "personality_process",
        "evolution_process",
        "dev_tick",
        "dev_on_message",
        "memory_process",
        "learning_post_turn",
    }

    # ============================================================
    # LAYER PRIORITY
    # ============================================================

    LAYER_PRIORITY = {
        "relationship": 100,
        "episodic_emotional": 95,
        "emotion": 90,
        "episodic": 85,
        "identity": 80,
        "personality": 75,
        "motivation": 70,
        "cognition_trace": 65,
        "childhood": 60,
        "social": 55,
        "learning": 40,
        "web": 30,
    }

    # ============================================================
    # TOKEN BUDGETS
    # ============================================================

    TRIGGER_WEIGHT = {
        "greeting": 0,
        "casual": 0,
        "topic": 1,
        "emotional": 2,
        "memory": 3,
        "identity": 3,
        "reflective": 3,
        "love": 4,
        "deep_self": 4,
    }

    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name

    # ============================================================
    # PUBLIC PLAN
    # ============================================================

    def plan(self, message: str) -> Dict:
        """
        Build a memory retrieval plan.

        No database access.
        No LLM calls.

        Returns:
            {
                "triggers": [...],
                "layers": [...],        # all relevant layers, priority-ordered
                "read_layers": [...],   # subset safe to inject as context
                "token_budget": int,
            }
        """

        if not message or not message.strip():
            return self._empty_plan()

        m = self._normalize(message)
        fired = self._detect_triggers(m)

        # --------------------------------------------------------
        # No explicit trigger
        # --------------------------------------------------------

        if not fired:
            if "?" in message:
                return {
                    "triggers": ["topic"],
                    "layers": ["episodic"],
                    "read_layers": ["episodic"],
                    "token_budget": 450,
                }
            return self._empty_plan()

        # --------------------------------------------------------
        # Greeting/casual messages stay cheap.
        # --------------------------------------------------------

        meaningful = [
            t for t in fired
            if t not in ("greeting", "casual")
        ]

        if not meaningful:
            return self._empty_plan()

        # --------------------------------------------------------
        # Build unique layer set.
        # --------------------------------------------------------

        layers = set()
        for trigger in meaningful:
            layers.update(self.TRIGGER_MAP.get(trigger, []))

        # --------------------------------------------------------
        # Sort by importance.
        # --------------------------------------------------------

        ordered_layers = sorted(
            layers,
            key=lambda layer: self.LAYER_PRIORITY.get(layer, 0),
            reverse=True,
        )

        # --------------------------------------------------------
        # Filter to read layers only.
        # --------------------------------------------------------

        read_layers = [
            layer for layer in ordered_layers
            if layer in self.READ_LAYERS
        ]

        # --------------------------------------------------------
        # Calculate token budget.
        # --------------------------------------------------------

        weight = sum(
            self.TRIGGER_WEIGHT.get(t, 1)
            for t in meaningful
        )

        budget = 350 + (weight * 150)

        if len(meaningful) >= 2:
            budget += 150

        budget = min(budget, 1400)

        return {
            "triggers": fired,
            "layers": ordered_layers,
            "read_layers": read_layers,
            "token_budget": budget,
        }

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize(message: str) -> str:
        """
        Normalize repeated characters and whitespace.

        Example:
            "I missssss you!!!"
            -> "i missss you"
        """

        m = message.lower().strip()

        # Collapse excessive repeated characters.
        m = re.sub(r"(.)\1{3,}", r"\1\1", m)

        # Normalize whitespace.
        m = re.sub(r"\s+", " ", m)

        return m

    # ============================================================
    # TRIGGER DETECTION
    # ============================================================

    def _detect_triggers(self, message: str) -> List[str]:
        """
        Detect every semantic trigger.
        Duplicate triggers cannot appear in the result.
        """

        fired = []

        for trigger, patterns in self.TRIGGER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    fired.append(trigger)
                    break

        return fired

    # ============================================================
    # EMPTY PLAN
    # ============================================================

    @staticmethod
    def _empty_plan() -> Dict:
        return {
            "triggers": [],
            "layers": [],
            "read_layers": [],
            "token_budget": 0,
        }


# ================================================================
# SINGLETON
# ================================================================

_router: Optional[MemoryRouter] = None


def get_memory_router(user_name: str = "not_set") -> MemoryRouter:
    global _router
    if _router is None:
        _router = MemoryRouter(user_name=user_name)
    return _router
