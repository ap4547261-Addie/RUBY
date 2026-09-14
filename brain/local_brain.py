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
                n_ctx=1024,        # reduced from 2048 to save RAM
                n_threads=4,
                verbose=True,      # shows detailed loading info
            )

            self.model_path = model_path
            print("✅ Model loaded successfully.")

            # -----------------------------
            # RAW DIAGNOSTIC TEST
            # -----------------------------
            try:
                test = self.model(
                    "The capital of France is",
                    max_tokens=10,
                    echo=False,
                )
                raw_output = test["choices"][0]["text"]
                print(f"🧪 RAW TEST OUTPUT: {repr(raw_output)}")
            except Exception as test_err:
                print(f"🧪 RAW TEST FAILED: {test_err}")

            # -----------------------------
            # CHAT TEMPLATE TEST
            # -----------------------------
            try:
                chat_test = self.model.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say hello."},
                    ],
                    max_tokens=20,
                )
                chat_output = chat_test["choices"][0]["message"]["content"]
                print(f"🧪 CHAT TEST OUTPUT: {repr(chat_output)}")
            except Exception as chat_err:
                print(f"🧪 CHAT TEST FAILED: {chat_err}")

            return True

        except Exception as error:
            print(f"❌ Model loading failed: {error}")
            self.model = None
            return False

    def is_loaded(self) -> bool:
        return self.model is not None

    def generate(self, ruby_prompt: str, user_message: str) -> str:
        if self.model is None:
            return "I don't have my brain loaded yet. 😭"

        try:
            result = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": ruby_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=150,
                temperature=0.7,
                top_p=0.9,
            )
            return result["choices"][0]["message"]["content"].strip()

        except Exception as error:
            print(f"❌ Generation error: {error}")
            return "My brain glitched for a moment. 😭"
