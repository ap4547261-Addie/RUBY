from llama_cpp import Llama


class LocalBrain:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, model_path: str) -> bool:
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=4,
                verbose=False,
            )

            self.model_path = model_path

            print("✅ Qwen2.5 loaded.")
            return True

        except Exception as error:
            print(f"❌ Qwen2.5 loading failed: {error}")

            self.model = None
            return False

    def is_loaded(self) -> bool:
        return self.model is not None

    def generate(
        self,
        ruby_prompt: str,
        user_message: str,
    ) -> str:

        if self.model is None:
            return "I don't have my brain loaded yet. 😭"

        try:
            prompt = (
                "<|im_start|>system\n"
                f"{ruby_prompt}"
                "<|im_end|>\n"
                "<|im_start|>user\n"
                f"{user_message}"
                "<|im_end|>\n"
                "<|im_start|>assistant\n"
            )

            result = self.model(
                prompt,
                max_tokens=128,
                temperature=0.7,
                top_p=0.8,
                stop=[
                    "<|im_end|>",
                    "<|im_start|>",
                ],
            )

            response = result["choices"][0]["text"].strip()

            return response

        except Exception as error:
            print(f"❌ Generation error: {error}")

            return "My brain glitched for a moment. 😭"
