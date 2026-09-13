from llama_cpp import Llama


class LocalBrain:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, model_path: str) -> bool:
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )

            self.model_path = model_path

            print("✅ TinyLlama loaded.")
            return True

        except Exception as error:
            print(
                f"❌ TinyLlama loading failed: {error}"
            )

            self.model = None
            return False

    def is_loaded(self) -> bool:
        return self.model is not None

    def generate(self, prompt: str) -> str:
        if self.model is None:
            return (
                "I don't have my brain loaded yet. 😭"
            )

        try:
            result = self.model.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=256,
                temperature=0.7,
            )

            return (
                result["choices"][0]["message"]["content"]
                .strip()
            )

        except Exception as error:
            print(
                f"❌ Generation error: {error}"
            )

            return (
                "My brain glitched for a moment. 😭"
            )
