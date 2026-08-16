from app.ai.llm import SynoraLLM
from app.agent.router import route_command


def main():

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

        # First check for computer commands.
        result = route_command(user_input)

        if result:
            print(f"Synora: {result}\n")
            continue

        # Otherwise use the LLM.
        try:
            answer = ai.generate(user_input)
            print(f"Synora: {answer}\n")

        except Exception as error:
            print(f"Synora: Sorry, something went wrong: {error}\n")


if __name__ == "__main__":
    main()