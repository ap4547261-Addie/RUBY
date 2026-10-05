class GlobalWorkspace:
    def __init__(self):
        self.broadcast_data = {}

    def broadcast(self, source, data):
        """Receives information from a cognitive module."""
        self.broadcast_data[source] = data

    def build_prompt_context(self):
        """Compiles all broadcasted data into a single string for the LLM."""
        lines = []
        for source, data in self.broadcast_data.items():
            if data:
                lines.append(f"[{source.upper()}]: {data}")
        return "\n".join(lines)
    
    def clear(self):
        self.broadcast_data = {}
