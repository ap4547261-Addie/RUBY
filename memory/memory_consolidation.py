import re
from memory import database
from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.relationship_memory import RelationshipMemory


class MemoryConsolidation:

    def __init__(self, user_name="not_set"):
        database.init_db()
        self.user_name = user_name
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.relationship = RelationshipMemory(user_name=user_name)

    # -------------------------
    # Display name
    # -------------------------
    def _display_name(self):
        if not self.user_name or self.user_name == "not_set":
            return "the stranger"
        return self.user_name

    # -------------------------
    # Signal detection
    # -------------------------
    def _is_long_message(self, text, words=12):
        return len(text.split()) >= words

    def _is_personal_reveal(self, text):
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
        t = text.lower()
        return any(m in t for m in [
            "shut up", "stupid", "dumb", "idiot",
            "you're useless", "you are useless",
            "do it now", "obey", "command",
        ])

    def _is_pushy(self, text):
        t = text.lower()
        return any(m in t for m in [
            "send me", "show me now", "do this for me",
            "you must", "you have to",
        ])

    # -------------------------
    # Fact extraction
    # -------------------------
    def extract_facts(self, text):
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
        self.episodic.remember(user_message, ruby_reply)
        self.extract_facts(user_message)
        self.relationship.add_message()
        self.relationship.grow_familiarity(0.02)

        if self._is_personal_reveal(user_message):
            self.relationship.grow_trust(0.15)
            print("📈 +trust (personal reveal)")
        elif self._is_long_message(user_message):
            self.relationship.grow_trust(0.05)

        if self._is_clever(user_message):
            self.relationship.grow_respect(0.10)
            print("📈 +respect (clever)")

        if self._is_rude(user_message):
            self.relationship.shrink_trust(0.15)
            self.relationship.shrink_respect(0.10)
            print("📉 -trust -respect (rude)")

        if self._is_pushy(user_message):
            self.relationship.shrink_respect(0.05)

        self.relationship.grow_attachment(0.005)

    # -------------------------
    # Context builder (prose, cold thresholds)
    # -------------------------
    def build_context(self, user_message):
        parts = []
        display = self._display_name()

        # 1. Facts about the user — hide name/nickname
        facts = self.semantic.get_all_for(self.user_name)
        if facts:
            filtered = [(k, v) for k, v in facts
                        if k.lower() not in ("name", "nickname")]
            if filtered:
                fact_bits = [f"{k.replace('_', ' ')} is {v}" for k, v in filtered]
                parts.append(f"You remember about {display}: {', '.join(fact_bits)}.")

        # 2. Relevant past episode
        keywords = [w for w in user_message.lower().split() if len(w) >= 4]
        found = []
        for kw in keywords[:2]:
            for row in self.episodic.search(kw, limit=1):
                if row not in found:
                    found.append(row)
        if found:
            u, r, _ = found[0]
            parts.append(f'You remember {display} saying "{u}" and you answered "{r}".')

        # 3. Emotional state — COLD for a long time
        s = self.relationship.get_state()
        trust = s["trust"]
        attach = s["attachment"]
        respect = s["respect"]
        count = s["message_count"]

        if trust < 3 and attach < 3:
            mood = (f"You barely know {display}. Stay cold, guarded, and brief. "
                    f"Do NOT act friendly. Do NOT ask how they are. "
                    f"Do NOT say 'nice to meet you'. Do NOT offer to meet up.")
        elif trust < 10 and attach < 10:
            mood = (f"You're slowly getting used to {display}. Still guarded, "
                    f"but occasionally interested when they say something real.")
        elif trust < 25 and attach < 25:
            mood = (f"You've started to trust {display}. You can say real things — "
                    f"rarely, and only when it matters.")
        else:
            mood = (f"You're deeply attached to {display}. You love them, "
                    f"though it's hard to show.")

        if respect > 3:
            mood += f" You respect {display}."
        elif respect < -1:
            mood += f" You've lost some respect for {display}."

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
