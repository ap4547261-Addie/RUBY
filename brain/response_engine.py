from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


class ResponseEngine:
    def __init__(self, brain):
        self.brain = brain
        self.short_term = ShortTermMemory(max_messages=10)
        self.long_term = LongTermMemory()

    def respond(self, user_message: str, ruby_prompt: str) -> str:
        # 1. Get relevant long-term memory context
        memory_context = self.long_term.get_relevant_context(
            user_message, limit=3
        )

        # 2. Inject into the system prompt
        system_content = ruby_prompt
        if memory_context:
            system_content = f"{ruby_prompt}\n\n{memory_context}"

        # 3. Build full message list
        messages = [{"role": "system", "content": system_content}]
        messages.extend(self.short_term.get_messages())
        messages.append({"role": "user", "content": user_message})

        # 4. Generate
        reply = self.brain.generate(messages)

        # 5. Save to short-term (immediate context)
        self.short_term.add("user", user_message)
        self.short_term.add("assistant", reply)

        # 6. Save to long-term (persists across restarts)
        self.long_term.remember(user_message, reply)

        return reply

    def clear_history(self):
        self.short_term.clear()

    def wipe_long_term(self):
        self.long_term.wipe()
        self.short_term.clear()
