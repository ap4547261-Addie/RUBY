from llama_cpp import Llama


class LocalBrain:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, model_path: str) -> bool:
        try:
            print(f"🔄 Loading model from: {model_path}")
            self.model = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            self.model_path = model_path
            print("✅ Model loaded.")
            return True
        except Exception as error:
            print(f"❌ Model loading failed: {error}")
            self.model = None
            return False

    def is_loaded(self) -> bool:
        return self.model is not None

    def generate(self, description: str, history: list, user_name: str = "Addie") -> str:
        """
        Builds a raw transcript and lets the model continue it as Ruby.
        No system prompt, no assistant role — just a conversation.
        """
        if self.model is None:
            return "My brain isn't loaded yet."

        # --- Build transcript ---
        lines = [description.strip(), ""]

        for msg in history:
            speaker = user_name if msg["role"] == "user" else "Ruby"
            lines.append(f"{speaker}: {msg['content']}")

        lines.append("Ruby:")
        prompt = "\n".join(lines)

        try:
            result = self.model(
                prompt,
                max_tokens=80,
                temperature=0.85,
                top_p=0.9,
                repeat_penalty=1.3,
                frequency_penalty=0.4,
                echo=False,
                stop=[f"{user_name}:", "\n\n\n"],
            )
            reply = result["choices"][0]["text"].strip()

            # clean trailing junk
            if f"{user_name}:" in reply:
                reply = reply.split(f"{user_name}:")[0].strip()

            return reply
        except Exception as error:
            print(f"❌ Generation error: {error}")
            return "..."
