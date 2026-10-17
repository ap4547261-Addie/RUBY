class ShortTermMemory:
    def __init__(self, max_messages=10):
        self.max_messages = max_messages
        self.messages = []

    def add(self, role, content):
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def discard_last(self):
        """Drop the newest message (used when generation failed)."""
        if self.messages:
            self.messages.pop()

    def get_messages(self):
        return self.messages.copy()

    def clear(self):
        self.messages.clear()
