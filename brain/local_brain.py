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
                n_threads=3,
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

    # -------------------------
    # Cleanup — fixed so it doesn't delete her name
    # -------------------------
    def _clean(self, reply: str, user_name: str) -> str:
        """Strip markdown and role prefixes. Preserve legitimate name replies."""
        reply = reply.replace("**", "").replace("*", "").strip()

        # leading role prefixes
        if reply.lower().startswith("ruby:"):
            reply = reply[5:].strip()
        if reply.lower().startswith(f"{user_name.lower()}:"):
            reply = reply[len(user_name) + 1:].strip()

        # Split into lines, dropping empty ones
        lines = [l for l in reply.split("\n") if l.strip()]

        # ONLY strip the last line if there are other lines AND it's just a name
        if len(lines) > 1:
            last = lines[-1].rstrip(" .-—:").strip().lower()
            if last in ["ruby", "addie", "aditya", user_name.lower()]:
                lines = lines[:-1]
            reply = " ".join(lines)
        else:
            reply = lines[0] if lines else ""

        # Strip dash-signature endings only
        for sig in ["— Ruby", "- Ruby", "– Ruby", "—Ruby", "-Ruby"]:
            if reply.endswith(sig):
                reply = reply[:-len(sig)].rstrip(" .-—:")

        return " ".join(reply.split()).strip()

    # -------------------------
    # Generate
    # -------------------------
    def generate(self, description: str, history: list, user_name: str = "not_set") -> str:
        if self.model is None:
            return "My brain isn't loaded yet."

        messages = [{"role": "system", "content": description}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            result = self.model.create_chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.9,
                top_p=0.9,
                repeat_penalty=1.5,
                frequency_penalty=0.7,
                presence_penalty=0.5,
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
            return "..."
