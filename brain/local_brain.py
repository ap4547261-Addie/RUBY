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

    def generate(self, messages: list) -> str:
        if self.model is None:
            return "I don't have my brain loaded yet. 😭"

        try:
            result = self.model.create_chat_completion(
                messages=messages,
                max_tokens=100,
                temperature=0.75,
                top_p=0.9,
                repeat_penalty=1.3,          # ← stops emoji/word looping
                frequency_penalty=0.5,       # ← discourages repetition
                presence_penalty=0.3,
            )
            return result["choices"][0]["message"]["content"].strip()
        except Exception as error:
            print(f"❌ Generation error: {error}")
            return "My brain glitched for a moment. 😭"
