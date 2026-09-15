import re
from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.relationship_memory import RelationshipMemory


class MemoryConsolidation:
    """
    The brain of V0.4 — runs after each message.
    - Saves the raw episode
    - Extracts facts from the user's message
    - Updates the relationship
    """

    def __init__(self, user_name="Addie"):
        self.user_name = user_name
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.relationship = RelationshipMemory(user_name=user_name)

    # -------------------------
    # Fact extraction (rule-based)
    # -------------------------
    def extract_facts(self, text: str):
        """Look for simple patterns and save extracted facts."""
        text_lower = text.lower()

        patterns = [
            (r"my name is ([a-z\s]+?)(?:[.,!?]|$)", "name"),
            (r"i'?m ([a-z\s]+?)(?:[.,!?]|$)", "name"),
            (r"people call me ([a-z\s]+?)(?:[.,!?]|$)", "nickname"),
            (r"my favorite color is ([a-z\s]+?)(?:[.,!?]|$)", "favorite_color"),
            (r"my favourite color is ([a-z\s]+?)(?:[.,!?]|$)", "favorite_color"),
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
                # Don't save if it looks like a false positive (too long or contains weird stuff)
                if 0 < len(value) < 30 and not value.startswith("a "):
                    self.semantic.remember_fact(self.user_name, key, value)
                    print(f"💡 Learned fact: {key} = {value}")

    # -------------------------
    # Main entry point
    # -------------------------
    def process(self, user_message, ruby_reply):
        # 1. Save raw episode
        self.episodic.remember(user_message, ruby_reply)

        # 2. Extract facts from the user's message
        self.extract_facts(user_message)

        # 3. Update relationship
        self.relationship.increment_messages()

        # Small trust bump just for showing up
        self.relationship.add_trust(1)

        # 4. Slowly change mood based on trust level
        state = self.relationship.get_state()
        trust = state["trust_level"]
        count = state["message_count"]

        if count < 10:
            mood = "guarded"
        elif count < 30:
            mood = "curious"
        elif count < 100:
            mood = "warming"
        else:
            mood = "attached"

        self.relationship.set_mood(mood)

    # -------------------------
    # Context builder for the prompt
    # -------------------------
    def build_context(self, user_message: str) -> str:
        """Assemble what Ruby remembers into a short text block."""
        blocks = []

        # 1. Facts about the user
        facts = self.semantic.get_all_for(self.user_name)
        if facts:
            fact_lines = [f"- {k.replace('_', ' ')}: {v}" for k, v in facts]
            blocks.append("Facts you know about them:\n" + "\n".join(fact_lines))

        # 2. Relevant past episodes
        keywords = [w for w in user_message.lower().split() if len(w) >= 4]
        found = []
        for kw in keywords[:2]:
            for row in self.episodic.search(kw, limit=2):
                if row not in found:
                    found.append(row)

        if found:
            ep_lines = [f"- they said: {u}\n  you replied: {r}" for u, r, _ in found]
            blocks.append("Things you remember:\n" + "\n".join(ep_lines))

        # 3. Relationship state
        state = self.relationship.get_state()
        blocks.append(
            f"Relationship — messages exchanged: {state['message_count']}, "
            f"your current mood toward them: {state['mood']}"
        )

        return "\n\n".join(blocks)

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
