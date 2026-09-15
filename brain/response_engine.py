from memory.short_term import ShortTermMemory
from memory.memory_consolidation import MemoryConsolidation


class ResponseEngine:
    def __init__(self, brain, user_name="Addie"):
        self.brain = brain
        self.user_name = user_name
        self.short_term = ShortTermMemory(max_messages=10)
        self.memory = MemoryConsolidation(user_name=user_name)

    def respond(self, user_message: str, ruby_prompt: str) -> str:
        # 1. Get memory context (facts + episodes + relationship state)
        context = self.memory.build_context(user_message)

        description = ruby_prompt
        if context:
            description = f"{ruby_prompt}\n\n{context}"

        # 2. Add new user message
        self.short_term.add("user", user_message)

        # 3. Generate reply
        reply = self.brain.generate(
            description=description,
            history=self.short_term.get_messages(),
            user_name=self.user_name,
        )

        # 4. Store reply in short-term
        self.short_term.add("assistant", reply)

        # 5. Consolidate into long-term memory
        self.memory.process(user_message, reply)

        return reply

    def clear_short_term(self):
        self.short_term.clear()

    def wipe_all_memory(self):
        self.short_term.clear()
        self.memory.wipe_all()

    def memory_stats(self):
        return self.memory.stats()
