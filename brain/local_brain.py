from llama_cpp import Llama
import re


class LocalBrain:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, model_path: str) -> bool:
        try:
            print(f"🔄 Loading model from: {model_path}")

            self.model = Llama(
                model_path=model_path,

                # Context window
                n_ctx=131072,

                # CPU threads
                n_threads=6,

                # GPU acceleration
                # Set to -1 later to offload all possible layers.
                # Keeping 0 for the first clean test.
                n_gpu_layers=0,

                # Let llama.cpp use the GGUF model's
                # own chat template.
                verbose=False,
            )

            self.model_path = model_path

            print("✅ Model loaded.")
            return True

        except Exception as error:
            print(f"❌ Model loading failed: {error}")
            self.model = None
            self.model_path = None
            return False

    def is_loaded(self) -> bool:
        return self.model is not None

    def _clean(self, reply: str, user_name: str) -> str:
        # ------------------------------------------------------
        # Strip hallucinated control tags.
        # Qwen2.5 sometimes outputs things like:
        #   [GENERATE_IMAGE: sunset over the city]
        #   [SAVE_MEMORY: father reading stories]
        #   [ADD_MEMORY: ...]
        # These are NOT meant to be spoken. Remove them all.
        # ------------------------------------------------------
        reply = re.sub(r"\[[A-Za-z_]+:[^\]]*\]", "", reply)
        reply = re.sub(r"\[[A-Za-z_]+\]", "", reply)
        reply = " ".join(reply.split()).strip()

        reply = reply.replace("**", "").replace("*", "").strip()

        if reply.lower().startswith("ruby:"):
            reply = reply[5:].strip()

        if reply.lower().startswith(f"{user_name.lower()}:"):
            reply = reply[len(user_name) + 1:].strip()

        lines = [line for line in reply.split("\n") if line.strip()]

        if len(lines) > 1:
            last = lines[-1].rstrip(" .-—:").strip().lower()

            if last in [
                "ruby",
                "addie",
                "aditya",
                user_name.lower(),
            ]:
                lines = lines[:-1]

            reply = " ".join(lines)

        else:
            reply = lines[0] if lines else ""

        for signature in [
            "— Ruby",
            "- Ruby",
            "– Ruby",
            "—Ruby",
            "-Ruby",
        ]:
            if reply.endswith(signature):
                reply = reply[:-len(signature)].rstrip(" .-—:")

        return " ".join(reply.split()).strip()

    def generate(
        self,
        description: str,
        history: list,
        user_name: str = "not_set",
        max_tokens: int = 180,
    ) -> str:

        if self.model is None:
            return "My brain isn't loaded yet."

        messages = [
            {
                "role": "system",
                "content": description,
            }
        ]

        for msg in history:
            messages.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )

        try:
            result = self.model.create_chat_completion(
                messages=messages,

                # Generation
                max_tokens=max_tokens,

                # Sampling
                temperature=0.9,
                top_p=0.9,

                # Repetition control
                repeat_penalty=1.15,
                frequency_penalty=0.3,
                presence_penalty=0.2,

                # Prevent the model from continuing
                # as another speaker.
                stop=[
                    f"{user_name}:",
                    "Ruby:",
                ],
            )

            reply = result["choices"][0]["message"]["content"].strip()

            reply = self._clean(
                reply,
                user_name,
            )

            return reply

        except Exception as error:
            print(f"❌ Generation error: {error}")

            return (
                f"[GEN ERROR] "
                f"{type(error).__name__}: {error}"
            )
