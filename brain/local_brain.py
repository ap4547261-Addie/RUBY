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
        if self.model is None:
            return "My brain isn't loaded yet."

        # --- Build transcript with clear scene boundaries ---
        lines = []
        lines.append("### SCENE ###")
        lines.append(description.strip())
        lines.append("### END SCENE ###")
        lines.append("")
        lines.append("### CHAT LOG ###")

        for msg in history:
            speaker = user_name if msg["role"] == "user" else "Ruby"
            lines.append(f"{speaker}: {msg['content']}")

        lines.append("Ruby:")

        prompt = "\n".join(lines)

        try:
            result = self.model(
                prompt,
                max_tokens=60,
                temperature=0.85,
                top_p=0.9,
                repeat_penalty=1.4,
                frequency_penalty=0.6,
                presence_penalty=0.4,
                echo=False,
                stop=[
                    f"{user_name}:",
                    "###",
                    "Ruby:",
                    "\n\n\n",
                ],
            )
            reply = result["choices"][0]["text"].strip()

            # Strip any leaked prefixes
            for junk in [f"{user_name}:", "Ruby:", "###"]:
                if junk in reply:
                    reply = reply.split(junk)[0].strip()

            return reply
        except Exception as error:
            print(f"❌ Generation error: {error}")
            return "..."
