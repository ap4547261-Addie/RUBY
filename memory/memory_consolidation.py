import re
from memory import database
from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.relationship_memory import RelationshipMemory


class MemoryConsolidation:

    def __init__(self, user_name="Addie"):
        # Ensure all tables exist BEFORE creating any memory objects
        database.init_db()

        self.user_name = user_name
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.relationship = RelationshipMemory(user_name=user_name)

    # -------------------------
    # Signal detection
    # -------------------------
    def _has_question(self, text):
        return "?" in text

    def _is_long_message(self, text, words=12):
        return len(text.split()) >= words

    def _is_personal_reveal(self, text):
        """Detects when user shares something real about themselves."""
        markers = [
            "i feel", "i felt", "i think", "i believe",
            "my mother", "my father", "my family", "my life",
            "i'm scared", "i am scared", "i'm sad", "i am sad",
            "i love", "i hate", "i miss", "i lost",
            "i remember", "i dream", "i wish", "i hope",
        ]
        t = text.lower()
        return any(m in t for m in markers)

    def _is_clever(self, text):
        """Detects wit, humor, or insight (rough heuristics)."""
        t = text.lower().strip()
        if len(text.split()) < 3:
            return False
        clever_markers = [
            "actually", "imagine", "what if", "suppose",
            "i wonder", "why does", "how come",
            "funny", "ironic", "paradox",
        ]
        return any(m in t for m in clever_markers)

    def _is_rude(self, text):
        """Detects rudeness or pushiness."""
        t = text.lower()
        rude_markers = [
            "shut up", "stupid", "dumb", "idiot",
            "you're useless", "you are useless",
            "do it now", "obey", "command",
        ]
        return any(m in t for m in rude_markers)

    def _is_pushy(self, text):
        """Detects demanding behavior."""
        t = text.lower()
        return any(m in t for m in [
            "send me", "show me now", "do this for me",
            "you must", "you have to",
        ])

    # -------------------------
    # Fact extraction (rule-based)
    # -------------------------
    def extract_facts(self, text: str):
        text_lower = text.lower()
        patterns = [
            (r"my name is ([a-z\s]+?)(?:[.,!?]|$)", "name"),
            (r"i'?m ([a-z\s]+?)(?:[.,!?]|$)", "name"),
            (r"people call me ([a-z\s]+?)(?:[.,!?]|$)", "nickname"),
            (r"my favorite color is ([a-z\s]+?)(?:[.,!?]|$)", "favorite_color"),
            (r"my favorite food is ([a-z\s]+?)(?:[.,!?]|$)", "favorite_food"),
            (r"my dog'?s? name is ([a-z\s]+?)(?:[.,!?]|$)", "dog_name"),
            (r"my cat'?s? name is ([a-z\s]+?)(?:[.,!?]|$)", "cat_name"),
            (r"i am (\d+) years old", "age"),
            (r"i'?m (\d+) years old", "age"),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip()
                if 0 < len(value) < 30:
                    self.semantic.remember_fact(self.user_name, key, value)
                    print(f"💡 Fact: {key} = {value}")

    # -------------------------
    # Main entry point
    # -------------------------
    def process(self, user_message, ruby_reply):
        # 1. Save raw episode
        self.episodic.remember(user_message, ruby_reply)

        # 2. Extract facts
        self.extract_facts(user_message)

        # 3. Count message
        self.relationship.add_message()

        # 4. Grow familiarity for showing up
        self.relationship.grow_familiarity(0.02)

        # 5. Reward quality
        if self._is_personal_reveal(user_message):
            self.relationship.grow_trust(0.15)
            print("📈 +trust (personal reveal)")
        elif self._is_long_message(user_message):
            self.relationship.grow_trust(0.05)

        if self._is_clever(user_message):
            self.relationship.grow_respect(0.10)
            print("📈 +respect (clever)")

        # 6. Penalize bad behavior
        if self._is_rude(user_message):
            self.relationship.shrink_trust(0.15)
            self.relationship.shrink_respect(0.10)
            print("📉 -trust -respect (rude)")

        if self._is_pushy(user_message):
            self.relationship.shrink_respect(0.05)

        # 7. Attachment grows very slowly — time + consistency only
        self.relationship.grow_attachment(0.005)

    # -------------------------
    # Context builder — infinite scale
    # -------------------------
    def build_context(self, user_message: str) -> str:
    """Return a short narrative about Ruby's state — no headers, no rules."""
    parts = []

    # 1. Facts (as a natural sentence)
    facts = self.semantic.get_all_for(self.user_name)
    if facts:
        fact_bits = [f"{k.replace('_', ' ')} is {v}" for k, v in facts]
        parts.append(f"You remember: {', '.join(fact_bits)}.")

    # 2. Relevant episodes (as a quiet memory)
    keywords = [w for w in user_message.lower().split() if len(w) >= 4]
    found = []
    for kw in keywords[:2]:
        for row in self.episodic.search(kw, limit=1):
            if row not in found:
                found.append(row)
    if found:
        u, r, _ = found[0]
        parts.append(f'You remember him saying "{u}" and you answered "{r}".')

    # 3. Emotional state — prose, not bullets
    s = self.relationship.get_state()
    trust = s["trust"]
    fam = s["familiarity"]
    attach = s["attachment"]
    respect = s["respect"]
    count = s["message_count"]

    # build ONE natural sentence describing her state
    if trust < 0.5 and attach < 0.5:
        mood = "You barely know him. You're guarded and cold."
    elif trust < 3 and attach < 3:
        mood = "You're starting to notice him. Still guarded, but a little curious."
    elif trust < 10 and attach < 10:
        mood = "You trust him. You can say real things. You're warming up."
    else:
        mood = "You're deeply attached to him. You love him, though it's hard to show."

    if respect > 3:
        mood += " You respect him. You take him seriously."
    elif respect < -1:
        mood += " You've lost some respect for him."

    parts.append(f"{mood} (exchanged {count} messages so far)")

    return " ".join(parts)
    # -------------------------
    # Utilities
    # -------------------------
    def wipe_all(self):
        self.episodic.wipe()
        self.semantic.wipe()
        self.relationship.wipe()

    def stats(self):
        return {
            "episodes": self.episodic.count(),
            "facts": len(self.semantic.get_all_for(self.user_name)),
            "relationship": self.relationship.get_state(),
        }
