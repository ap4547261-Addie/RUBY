from memory.short_term import ShortTermMemory


class ResponseEngine:
    def __init__(self, brain, short_term: ShortTermMemory = None):
        self.brain = brain
        self.memory = short_term or ShortTermMemory(max_messages=10)

    def respond(self, user_message: str, ruby_prompt: str) -> str:
        # Build full message list: system + history + new user message
        messages = [{"role": "system", "content": ruby_prompt}]
        messages.extend(self.memory.get_messages())
        messages.append({"role": "user", "content": user_message})

        # Generate reply using the full conversation
        reply = self.brain.generate(messages)

        # Store both messages in short-term memory
        self.memory.add("user", user_message)
        self.memory.add("assistant", reply)

        return reply

    def clear_history(self):
        self.memory.clear()
