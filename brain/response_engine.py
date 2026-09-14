class ResponseEngine:
    def __init__(self, brain):
        self.brain = brain

    def respond(self, user_message: str, ruby_prompt: str):
        return self.brain.generate(
            ruby_prompt,
            user_message,
        )
