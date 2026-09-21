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
                n_ctx=4096,             # fits the full ResponseEngine prompt
                n_threads=6,            # ← was 3 — use more CPU cores
                verbose=False,
                chat_format="chatml",
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

    def _clean(self, reply: str, user_name: str) -> str:
        reply = reply.replace("**", "").replace("*", "").strip()

        if reply.lower().startswith("ruby:"):
            reply = reply[5:].strip()
        if reply.lower().startswith(f"{user_name.lower()}:"):
            reply = reply[len(user_name) + 1:].strip()

        lines = [l for l in reply.split("\n") if l.strip()]

        if len(lines) > 1:
            last = lines[-1].rstrip(" .-—:").strip().lower()
            if last in ["ruby", "addie", "aditya", user_name.lower()]:
                lines = lines[:-1]
            reply = " ".join(lines)
        else:
            reply = lines[0] if lines else ""

        for sig in ["— Ruby", "- Ruby", "– Ruby", "—Ruby", "-Ruby"]:
            if reply.endswith(sig):
                reply = reply[:-len(sig)].rstrip(" .-—:")

        return " ".join(reply.split()).strip()

    def generate(
        self,
        description: str,
        history: list,
        user_name: str = "not_set",
        max_tokens: int = 80,        # ← was hardcoded 200
    ) -> str:
        if self.model is None:
            return "My brain isn't loaded yet."

        messages = [{"role": "system", "content": description}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            result = self.model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,     # ← respects caller's value
                temperature=0.9,
                top_p=0.9,
                repeat_penalty=1.15,
                frequency_penalty=0.3,
                presence_penalty=0.2,
                stop=[
                    f"{user_name}:",
                    "Ruby:",
                ],
            )
            reply = result["choices"][0]["message"]["content"].strip()
            reply = self._clean(reply, user_name)
            return reply
        except Exception as error:
            print(f"❌ Generation error: {error}")
            return f"[GEN ERROR] {type(error).__name__}: {error}"
