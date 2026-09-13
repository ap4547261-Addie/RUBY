class ResponseEngine:
    def __init__(self, brain):
        self.brain = brain

    def respond(self, user_message: str, ruby_prompt: str):
        prompt = f"""
{ruby_prompt}

User:
{user_message}

Ruby:
"""

        return self.brain.generate(prompt)
