from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


class ResponseEngine:
    def __init__(self, brain):
        self.brain = brain
        self.short_term = ShortTermMemory(max_messages=10)
        self.long_term = LongTermMemory()

    def respond(self, user_message: str, ruby_prompt: str,
                user_name: str = "Addie") -> str:
        # --- Long-term context (if any memories match) ---
        memory_block = self.long_term.get_relevant_context(
            user_message, limit=3
        )

        description = ruby_prompt
        if memory_block:
            description = (
                f"{ruby_prompt}\n\n"
                f"Things Ruby remembers about {user_name}:\n{memory_block}"
            )

        # --- Add new user message to short-term history ---
        self.short_term.add("user", user_message)

        # --- Generate reply (transcript mode) ---
        reply = self.brain.generate(
            description=description,
            history=self.short_term.get_messages(),
            user_name=user_name,
        )

        # --- Store reply in short-term ---
        self.short_term.add("assistant", reply)

        # --- Persist both sides in SQLite ---
        self.long_term.remember(user_message, reply)

        return reply

    def clear_short_term(self):
        """Wipes the current session only."""
        self.short_term.clear()

    def wipe_all_memory(self):
        """Wipes everything — short-term AND long-term."""
        self.short_term.clear()
        self.long_term.wipe()

    def memory_count(self) -> int:
        return self.long_term.count()
