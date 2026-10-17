# brain/local_brain.py
from llama_cpp import Llama
import re

# Ruby texts in short bursts. Each line of her reply is one chat bubble;
# anything past this many bubbles is folded into the last one.
MAX_BUBBLES = 3


class LocalBrain:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, model_path: str) -> bool:
        try:
            print(f"🔄 Loading model from: {model_path}")

            self.model = Llama(
                model_path=model_path,
                n_ctx=8192,          # Raised from 131072 → 8192 (fits in 16GB RAM)
                n_threads=6,
                n_gpu_layers=0,
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
        # Strip hallucinated control tags — BUT keep [SEND_SELFIE:...]
        # Qwen2.5 sometimes outputs things like:
        #   [GENERATE_IMAGE: sunset over the city]
        #   [SAVE_MEMORY: father reading stories]
        # These are NOT meant to be spoken. Remove them all.
        #
        # IMPORTANT: [SEND_SELFIE:filter] is a real command.
        # Extract it first, clean the text, then re-attach it.
        #
        # Line breaks are KEPT: each line is a separate chat bubble
        # (main.py splits on "\n"). Before, everything was flattened
        # into one line, so every reply looked like the same block.
        # ------------------------------------------------------
        selfie_match = re.search(r"\[SEND_SELFIE:\s*([^\]]+)\]", reply)
        selfie_token = ""
        if selfie_match:
            selfie_token = f"[SEND_SELFIE:{selfie_match.group(1).strip()}]"

        # Remove all bracket tags (including the selfie one temporarily)
        reply = re.sub(r"\[[A-Za-z_]+:[^\]]*\]", "", reply)
        reply = re.sub(r"\[[A-Za-z_]+\]", "", reply)

        # Normalise whitespace inside each line, keep the line breaks
        reply = reply.replace("\r", "")
        lines = [" ".join(line.split()) for line in reply.split("\n")]
        lines = [line.replace("**", "").replace("*", "").strip() for line in lines]
        lines = [line for line in lines if line]

        if lines and lines[0].lower().startswith("ruby:"):
            lines[0] = lines[0][5:].strip()

        if lines and lines[0].lower().startswith(f"{user_name.lower()}:"):
            lines[0] = lines[0][len(user_name) + 1:].strip()

        lines = [line for line in lines if line]

        # Drop a trailing line that is only a signature ("Ruby", "Addie", ...)
        if len(lines) > 1:
            last = lines[-1].rstrip(" .-—:").strip().lower()
            if last in ["ruby", "addie", "aditya", user_name.lower()]:
                lines = lines[:-1]

        # Drop an inline signature at the end of the last line
        if lines:
            for signature in ["— Ruby", "- Ruby", "– Ruby", "—Ruby", "-Ruby"]:
                if lines[-1].endswith(signature):
                    lines[-1] = lines[-1][:-len(signature)].rstrip(" .-—:")

        lines = [line for line in lines if line]

        # Cap the number of bubbles
        if len(lines) > MAX_BUBBLES:
            lines = lines[:MAX_BUBBLES - 1] + [" ".join(lines[MAX_BUBBLES - 1:])]

        reply = "\n".join(lines).strip()

        # 🔥 Re-attach the selfie token at the very end if it was there
        if selfie_token:
            reply = f"{reply} {selfie_token}".strip()

        return reply

    def generate(
        self,
        description: str,
        history: list,
        user_name: str = "not_set",
        max_tokens: int = 180,
    ) -> str:

        if self.model is None:
            return "My brain isn't loaded yet."

        messages = [{"role": "system", "content": description}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            result = self.model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.9,
                top_p=0.9,
                # Was 1.15 — high repeat penalties distort short casual
                # replies (avoids "I", "you", "the"...). Gentler is more natural.
                repeat_penalty=1.08,
                frequency_penalty=0.3,
                presence_penalty=0.2,
                stop=[f"{user_name}:", "Ruby:"],
            )

            reply = result["choices"][0]["message"]["content"].strip()
            reply = self._clean(reply, user_name)
            return reply

        except Exception as error:
            print(f"❌ Generation error: {error}")
            return f"[GEN ERROR] {type(error).__name__}: {error}"
