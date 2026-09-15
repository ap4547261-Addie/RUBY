from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


class ResponseEngine:
    def __init__(self, brain):
        self.brain = brain
        self.short_term = ShortTermMemory(max_messages=10)
        self.long_term = LongTermMemory()

    def respond(self, user_message: str, ruby_prompt: str, user_name: str = "Addie") -> str:
        # --- Get long-term memory as a natural note ---
        memory_block = self.long_term.get_relevant_context(user_message, limit=3)

        # --- Combine description + memory into one "who Ruby is right now" block ---
        description = ruby_prompt
        if memory_block:
            description = f"{ruby_prompt}\n\nThings Ruby remembers:\n{memory_block}"

        # --- Add the new user message to short-term history ---
        self.short_term.add("user", user_message)

        # --- Generate ---
        reply = self.brain.generate(
            description=description,
            history=self.short_term.get_messages(),
            user_name=user_name,
        )

        # --- Store the reply ---
        self.short_term.add("assistant", reply)

        # --- Persist to long-term memory ---
        self.long_term.remember(user_message, reply)

        return reply

    def clear_history(self):
        self.short_term.clear()

    def wipe_long_term(self):
        self.long_term.wipe()
        self.short_term.clear()
