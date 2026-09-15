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
                n_ctx=1024,          
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

    def generate(self, description: str, history: list, user_name: str = "not_set") -> str:
        if self.model is None:
            return "My brain isn't loaded yet."

        # Build messages list — Qwen's chat template is applied automatically
        messages = [{"role": "system", "content": description}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            result = self.model.create_chat_completion(
                messages=messages,
                max_tokens=40,
                temperature=0.85,
                top_p=0.9,
                repeat_penalty=1.3,
                frequency_penalty=0.5,
                presence_penalty=0.3,
                stop=[
                    f"{user_name}:",
                    "Ruby:",
                    "###",
                    "\n\n",
                    "**",
                ],
            )
            reply = result["choices"][0]["message"]["content"].strip()

            # ---- cleanup pass ----
            # strip markdown
            reply = reply.replace("**", "").replace("*", "").strip()
            # strip role prefixes if leaked
            if reply.lower().startswith("ruby:"):
                reply = reply[5:].strip()
            if reply.lower().startswith(f"{user_name.lower()}:"):
                reply = reply[len(user_name) + 1:].strip()
            # collapse newlines into a single space
            reply = " ".join(reply.split())

            return reply

        except Exception as error:
            print(f"❌ Generation error: {error}")
            return "..."
