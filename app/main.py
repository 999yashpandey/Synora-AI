import re

from app.ai.llm import SynoraLLM
from app.agent.router import route_command
from app.agent.executor import SynoraExecutor
from app.memory.conversation import ConversationMemory
from app.core.identity import handle_identity_command

from app.voice.speech_to_text import listen_and_transcribe
from app.voice.text_to_speech import speak

from app.web.search import search_web


def build_memory_context(
    memory: ConversationMemory,
    limit: int = 10,
) -> str:

    messages = memory.get_recent_messages(
        limit=limit
    )

    if not messages:
        return ""

    lines = []

    for message in messages:

        role = message["role"].capitalize()
        content = message["content"]

        lines.append(
            f"{role}: {content}"
        )

    return "\n".join(lines)


def respond(
    response: str,
    voice_mode: bool = False,
):

    response = str(response or "").strip()

    if not response:
        return

    print(
        f"Synora: {response}\n"
    )

    if voice_mode:

        speak(response)


def extract_web_search_query(
    user_input: str,
) -> str | None:

    text = user_input.strip()

    if not text:
        return None

    lower = text.lower()

    # --------------------------------------------------
    # Direct web search commands
    # --------------------------------------------------

    search_patterns = [

        r"^(?:search|search the web|search web)\s+"
        r"(?:for\s+)?(.+)$",

        r"^(?:look up|lookup)\s+(.+)$",

        r"^(?:find on the web|find online)\s+(.+)$",
    ]

    for pattern in search_patterns:

        match = re.match(
            pattern,
            lower,
        )

        if match:

            query = match.group(1).strip()

            if query:
                return query

    # --------------------------------------------------
    # Latest news commands
    # --------------------------------------------------

    news_patterns = [

        r"^(?:what'?s|what is)\s+the\s+latest\s+"
        r"(?:news\s+)?(?:about|on)\s+(.+)$",

        r"^latest\s+(?:news\s+)?"
        r"(?:about|on)\s+(.+)$",

        r"^tell me\s+(?:the\s+)?latest\s+"
        r"(?:news\s+)?(?:about|on)\s+(.+)$",

        r"^give me\s+(?:the\s+)?latest\s+"
        r"(?:news\s+)?(?:about|on)\s+(.+)$",
    ]

    for pattern in news_patterns:

        match = re.match(
            pattern,
            lower,
        )

        if match:

            topic = match.group(1).strip()

            if topic:
                return f"{topic} latest news"

    return None


def process_request(
    user_input: str,
    ai: SynoraLLM,
    memory: ConversationMemory,
    executor: SynoraExecutor,
    voice_mode: bool = False,
) -> bool:

    user_input = user_input.strip()

    if not user_input:
        return True

    # --------------------------------------------------
    # EXIT
    # --------------------------------------------------

    if user_input.lower() in [
        "exit",
        "quit",
        "bye",
        "goodbye",
    ]:

        respond(
            "Goodbye!",
            voice_mode,
        )

        return False

    # --------------------------------------------------
    # WEB SEARCH
    # --------------------------------------------------

    web_query = extract_web_search_query(
        user_input
    )

    if web_query:

        print(
            f"[Synora Web] Searching for: "
            f"{web_query}"
        )

        try:

            result = search_web(
                web_query,
                summarize=True,
            )

            memory.add_message(
                "user",
                user_input,
            )

            memory.add_message(
                "assistant",
                result,
            )

            respond(
                result,
                voice_mode,
            )

        except Exception as error:

            error_message = (
                "I couldn't search the web: "
                f"{error}"
            )

            respond(
                error_message,
                voice_mode,
            )

        return True

    # --------------------------------------------------
    # IDENTITY COMMANDS
    # --------------------------------------------------

    identity_result = handle_identity_command(
        user_input
    )

    if identity_result:

        memory.add_message(
            "user",
            user_input,
        )

        memory.add_message(
            "assistant",
            identity_result,
        )

        respond(
            identity_result,
            voice_mode,
        )

        return True

    # --------------------------------------------------
    # TASK EXECUTOR
    # --------------------------------------------------

    try:

        result = executor.execute(
            user_input
        )

        if result:

            memory.add_message(
                "user",
                user_input,
            )

            memory.add_message(
                "assistant",
                result,
            )

            respond(
                result,
                voice_mode,
            )

            return True

    except Exception as error:

        error_message = (
            "I couldn't complete that task: "
            f"{error}"
        )

        respond(
            error_message,
            voice_mode,
        )

        return True

    # --------------------------------------------------
    # COMPUTER COMMAND ROUTER
    # --------------------------------------------------

    try:

        result = route_command(
            user_input
        )

    except Exception as error:

        error_message = (
            "I couldn't execute that command: "
            f"{error}"
        )

        respond(
            error_message,
            voice_mode,
        )

        return True

    if result:

        memory.add_message(
            "user",
            user_input,
        )

        memory.add_message(
            "assistant",
            result,
        )

        respond(
            result,
            voice_mode,
        )

        return True

    # --------------------------------------------------
    # NORMAL AI CONVERSATION
    # --------------------------------------------------

    memory.add_message(
        "user",
        user_input,
    )

    try:

        memory_context = build_memory_context(
            memory,
            limit=10,
        )

        if memory_context:

            prompt = f"""
Here is the recent conversation history:

{memory_context}

Use the history when it is relevant.

Do not mention the existence of the history.

Answer the user's latest message directly.

Latest user message:

{user_input}
"""

        else:

            prompt = user_input

        answer = ai.generate(
            prompt
        )

        memory.add_message(
            "assistant",
            answer,
        )

        respond(
            answer,
            voice_mode,
        )

    except Exception as error:

        error_message = (
            "Sorry, something went wrong: "
            f"{error}"
        )

        respond(
            error_message,
            voice_mode,
        )

    return True


def run_text_mode(
    ai: SynoraLLM,
    memory: ConversationMemory,
    executor: SynoraExecutor,
):

    print("\n" + "=" * 55)
    print("                    SYNORA")
    print("=" * 55)
    print("Text Mode")
    print("Type 'exit' to quit.\n")

    while True:

        try:

            user_input = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\nSynora: Goodbye!"
            )

            break

        if not user_input:
            continue

        should_continue = process_request(
            user_input,
            ai,
            memory,
            executor,
            voice_mode=False,
        )

        if not should_continue:
            break


def run_voice_mode(
    ai: SynoraLLM,
    memory: ConversationMemory,
    executor: SynoraExecutor,
):

    print("\n" + "=" * 55)
    print("                    SYNORA")
    print("=" * 55)
    print("Voice Mode")
    print("Speak in English.")
    print("Say 'exit' or 'quit' to stop.\n")

    speak(
        "Voice mode is ready. How can I help you?"
    )

    while True:

        try:

            print(
                "\n[Synora] Listening..."
            )

            user_input = listen_and_transcribe()

            if not user_input:

                print(
                    "[Synora] "
                    "I didn't catch that. "
                    "Please try again."
                )

                continue

            print(
                f"\nYou: {user_input}"
            )

            should_continue = process_request(
                user_input,
                ai,
                memory,
                executor,
                voice_mode=True,
            )

            if not should_continue:
                break

        except KeyboardInterrupt:

            print(
                "\nSynora: Goodbye!"
            )

            break

        except Exception as error:

            print(
                "\n[Synora Voice] "
                f"Error: {error}"
            )

            speak(
                "Sorry, something went wrong."
            )


def main():

    ai = SynoraLLM()

    memory = ConversationMemory()

    executor = SynoraExecutor()

    print("\n" + "=" * 55)
    print("                    SYNORA")
    print("=" * 55)
    print("Your personal AI assistant")
    print("Qwen2.5 3B • Fast Mode")
    print("Persistent local memory enabled")
    print("Task execution enabled")
    print("Web search enabled")

    print("\nChoose input mode:")
    print("1. Text Mode")
    print("2. Voice Mode")

    while True:

        try:

            choice = input(
                "\nChoose mode (1/2): "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\nSynora: Goodbye!"
            )

            return

        if choice == "1":

            run_text_mode(
                ai,
                memory,
                executor,
            )

            break

        if choice == "2":

            run_voice_mode(
                ai,
                memory,
                executor,
            )

            break

        print(
            "Please choose 1 or 2."
        )


if __name__ == "__main__":
    main()