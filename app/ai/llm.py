import ollama
from app.ai.prompts import SYNORA_SYSTEM_PROMPT


class SynoraLLM:

    def __init__(self, model="qwen2.5:3b-instruct"):
        self.model = model

    def generate(self, prompt: str) -> str:

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYNORA_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False,
            keep_alive="10m",
            options={
                "num_ctx": 8192,
                "num_predict": 1800,
                "temperature": 0.4,
                "top_p": 0.9
            }
        )

        return (response.message.content or "").strip()
if __name__ == "__main__":

    ai = SynoraLLM()

    print("\n" + "=" * 55)
    print("                    SYNORA")
    print("=" * 55)
    print("Your personal AI assistant")
    print("Qwen2.5 3B • Fast Mode")
    print("Type 'exit' to quit.\n")

    while True:

        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Synora: Goodbye!")
            break

        try:
            answer = ai.generate(user_input)
            print(f"Synora: {answer}\n")

        except Exception as error:
            print(f"Synora: Error: {error}\n")