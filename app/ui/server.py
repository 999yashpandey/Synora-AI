from __future__ import annotations

import re
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from flask import Flask, jsonify, render_template, request

from app.ai.llm import SynoraLLM
from app.agent.executor import SynoraExecutor
from app.agent.router import route_command
from app.memory.conversation import build_memory_context
from app.web.search import search_web
from app.voice.speech_to_text import listen_and_transcribe
from app.voice.text_to_speech import speak


app = Flask(__name__)

llm = SynoraLLM()
executor = SynoraExecutor()


# ==========================================================
# HELPERS
# ==========================================================

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def save_conversation(user_text: str, assistant_text: str):
    """
    Save conversation using the same memory system already
    used by Synora.
    """

    try:
        from app.memory.conversation import ConversationMemory

        memory = ConversationMemory()

        memory.add_message("user", user_text)
        memory.add_message("assistant", assistant_text)

    except Exception as error:
        print(f"[Synora Memory] {error}")


# ==========================================================
# SPECIAL COMMANDS
# ==========================================================

def special_command(user_input: str) -> str | None:

    text = clean_text(user_input)

    if not text:
        return None

    lower = text.lower()

    # ------------------------------------------------------
    # TIME
    # ------------------------------------------------------

    if lower in {
        "time",
        "what time is it",
        "what is the time",
        "tell me the time",
        "current time",
    }:

        return (
            "The current time is "
            f"{datetime.now().strftime('%I:%M %p')}."
        )

    # ------------------------------------------------------
    # DATE
    # ------------------------------------------------------

    if lower in {
        "date",
        "what is the date",
        "what's the date",
        "what is today's date",
        "what's today's date",
        "today's date",
        "current date",
    }:

        return (
            "Today is "
            f"{datetime.now().strftime('%A, %d %B %Y')}."
        )

    # ------------------------------------------------------
    # NOTES
    # ------------------------------------------------------

    note_match = re.match(
        r"^(?:take a note|take note|write a note|save a note)"
        r"\s*(.*)$",
        text,
        re.IGNORECASE,
    )

    if note_match:

        note = note_match.group(1).strip()

        if not note:
            return "Tell me what you want me to write."

        desktop = Path.home() / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)

        note_file = desktop / "Synora_Notes.txt"

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        with note_file.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                f"[{timestamp}] {note}\n"
            )

        return (
            f"Note saved to {note_file.name} "
            "on your Desktop."
        )

    # ------------------------------------------------------
    # SCREENSHOT
    # ------------------------------------------------------

    if lower in {
        "screenshot",
        "take a screenshot",
        "capture screenshot",
    }:

        try:

            from PIL import ImageGrab

            desktop = Path.home() / "Desktop"
            desktop.mkdir(parents=True, exist_ok=True)

            filename = (
                "Synora_Screenshot_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )

            path = desktop / filename

            image = ImageGrab.grab()
            image.save(path)

            return (
                f"Screenshot saved as {filename} "
                "on your Desktop."
            )

        except Exception as error:

            return (
                "I couldn't take the screenshot. "
                f"{error}"
            )

    # ------------------------------------------------------
    # PLAY MUSIC
    # ------------------------------------------------------

    if lower in {
        "play music",
        "play some music",
        "play song",
        "play a song",
    }:

        webbrowser.open(
            "https://www.youtube.com/results?search_query="
            + quote_plus("music")
        )

        return "Opening music on YouTube."

    # ------------------------------------------------------
    # PLAY SPECIFIC SONG
    # ------------------------------------------------------

    music_match = re.match(
        r"^(?:play|play the song)\s+(.+)$",
        text,
        re.IGNORECASE,
    )

    if music_match:

        query = music_match.group(1).strip()

        if query:

            webbrowser.open(
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

            return (
                f"Searching YouTube for {query}."
            )

    # ------------------------------------------------------
    # WEBSITE
    # ------------------------------------------------------

    website_match = re.match(
        r"^(?:open|go to|visit)\s+"
        r"(https?://[^\s]+|www\.[^\s]+|"
        r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$",
        text,
        re.IGNORECASE,
    )

    if website_match:

        url = website_match.group(1)

        if not url.startswith(
            ("http://", "https://")
        ):

            url = "https://" + url

        webbrowser.open(url)

        return f"Opening {url}."

    # ------------------------------------------------------
    # GOOGLE SEARCH
    # ------------------------------------------------------

    google_match = re.match(
        r"^(?:google|google search|search google)"
        r"\s+(.+)$",
        text,
        re.IGNORECASE,
    )

    if google_match:

        query = google_match.group(1).strip()

        webbrowser.open(
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        return f"Searching Google for {query}."

    # ------------------------------------------------------
    # JOKE
    # ------------------------------------------------------

    if lower in {
        "tell me a joke",
        "tell a joke",
        "say a joke",
        "make me laugh",
    }:

        try:

            return llm.generate(
                "Tell me one short, clean joke. "
                "Return only the joke."
            )

        except Exception:

            return (
                "Why did the programmer quit his job? "
                "Because he didn't get arrays."
            )

    return None


# ==========================================================
# WEB SEARCH
# ==========================================================

def extract_web_search_query(
    user_input: str,
) -> str | None:

    text = clean_text(user_input)

    if not text:
        return None

    lower = text.lower()

    search_patterns = [
        r"^(?:search|search the web|search web)"
        r"\s+(?:for\s+)?(.+)$",

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


# ==========================================================
# MAIN PROCESSING PIPELINE
# ==========================================================
def identity_command(user_input: str) -> str | None:
    """
    Deterministic identity handling for Synora.

    These facts must never be decided by the LLM.
    """

    text = clean_text(user_input)
    lower = text.lower()

    # ------------------------------------------------------
    # CREATOR
    # ------------------------------------------------------

    creator_patterns = [
        "who created you",
        "who made you",
        "who built you",
        "who developed you",
        "who is your creator",
        "who's your creator",
        "who is the creator of synora",
        "who created synora",
        "who made synora",
        "who developed synora",
        "who built synora",
    ]

    if lower in creator_patterns:
        return "I was created and developed by Yash Pandey."

    # ------------------------------------------------------
    # IDENTITY
    # ------------------------------------------------------

    if lower in {
        "what are you",
        "who are you",
        "what is synora",
        "what is synora ai",
    }:
        return (
            "I am Synora AI, a local personal AI assistant "
            "created and developed by Yash Pandey."
        )

    return None

def process_request(
    user_input: str,
) -> str:

    user_input = clean_text(user_input)

    if not user_input:
        return "I didn't receive a command."

    print(
        f"[Synora] User: {user_input}"
    )

    # ------------------------------------------------------
    # 1. SPECIAL COMMANDS
    # ------------------------------------------------------

    special = special_command(
        user_input
    )

    if special:

        save_conversation(
            user_input,
            special,
        )

        print(
            f"[Synora] Synora: {special}"
        )

        return special

    # ------------------------------------------------------
    # 2. FILE / DOCUMENT / CODE EXECUTOR
    # ------------------------------------------------------

    try:

        executor_result = executor.execute(
            user_input
        )

        if executor_result:

            result = str(
                executor_result
            ).strip()

            if result:

                save_conversation(
                    user_input,
                    result,
                )

                print(
                    f"[Synora] Synora: {result}"
                )

                return result

    except Exception as error:

        print(
            f"[Synora Executor] {error}"
        )

    # ------------------------------------------------------
    # 3. COMPUTER / APPLICATION COMMANDS
    # ------------------------------------------------------

    try:

        route_result = route_command(
            user_input
        )

        if route_result:

            result = str(
                route_result
            ).strip()

            if result:

                save_conversation(
                    user_input,
                    result,
                )

                print(
                    f"[Synora] Synora: {result}"
                )

                return result

    except Exception as error:

        print(
            f"[Synora Router] {error}"
        )

    # ------------------------------------------------------
    # 4. WEB SEARCH
    # ------------------------------------------------------

    web_query = extract_web_search_query(
        user_input
    )

    if web_query:

        try:

            print(
                f"[Synora Web] Searching: "
                f"{web_query}"
            )

            result = search_web(
                web_query,
                summarize=True,
            )

            if result:

                result = str(result).strip()

                save_conversation(
                    user_input,
                    result,
                )

                print(
                    f"[Synora] Web result ready."
                )

                return result

        except Exception as error:

            print(
                f"[Synora Web] {error}"
            )

            return (
                "I couldn't complete the web "
                f"search: {error}"
            )

    # ------------------------------------------------------
    # 5. LOCAL QWEN
    # ------------------------------------------------------

    memory_context = build_memory_context(
        limit=10
    )

    prompt_parts = [
        "Respond as Synora, a concise local personal AI assistant.",
        "Be direct and helpful.",
        "Do not reveal hidden reasoning.",
    ]

    if memory_context:

        prompt_parts.append(
            "\nRecent conversation memory:\n"
            + memory_context
        )

    prompt_parts.append(
        "\nUser request:\n"
        + user_input
    )

    prompt = "\n".join(
        prompt_parts
    )

    try:

        response = llm.generate(
            prompt
        )

        response = (
            response
            or "I couldn't generate a response."
        ).strip()

    except Exception as error:

        print(
            f"[Synora LLM] {error}"
        )

        response = (
            "I encountered an error while "
            "processing your request."
        )

    save_conversation(
        user_input,
        response,
    )

    print(
        f"[Synora] Synora: {response}"
    )

    return response


# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ----------------------------------------------------------
# TEXT CHAT
# ----------------------------------------------------------

@app.route(
    "/api/chat",
    methods=["POST"],
)
def chat():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        message = clean_text(
            data.get("message", "")
        )

        if not message:

            return jsonify(
                {
                    "success": False,
                    "error": "Message is required.",
                }
            ), 400

        response = process_request(
            message
        )

        should_speak = bool(
            data.get("speak", False)
        )

        if should_speak:

            try:

                speak(
                    response,
                    blocking=True,
                )

            except Exception as error:

                print(
                    f"[Synora TTS] {error}"
                )

        return jsonify(
            {
                "success": True,
                "response": response,
            }
        )

    except Exception as error:

        print(
            f"[Synora API] {error}"
        )

        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 500


# ----------------------------------------------------------
# VOICE LISTEN
# ----------------------------------------------------------

@app.route(
    "/api/voice/listen",
    methods=["POST"],
)
def voice_listen():

    try:

        transcript = listen_and_transcribe()

        if not transcript:

            return jsonify(
                {
                    "success": False,
                    "error": "No speech detected.",
                }
            )

        return jsonify(
            {
                "success": True,
                "transcript": transcript,
            }
        )

    except Exception as error:

        print(
            f"[Synora STT] {error}"
        )

        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 500


# ----------------------------------------------------------
# VOICE RESPOND
# ----------------------------------------------------------

@app.route(
    "/api/voice/respond",
    methods=["POST"],
)
def voice_respond():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        message = clean_text(
            data.get("message", "")
        )

        if not message:

            return jsonify(
                {
                    "success": False,
                    "error": "Message is required.",
                }
            ), 400

        response = process_request(
            message
        )

        # IMPORTANT:
        # Blocking=True ensures the Flask request does
        # not finish before Windows SAPI5 completes speech.

        try:

            speak(
                response,
                blocking=True,
            )

        except Exception as error:

            print(
                f"[Synora TTS] {error}"
            )

        return jsonify(
            {
                "success": True,
                "transcript": message,
                "response": response,
            }
        )

    except Exception as error:

        print(
            f"[Synora Voice API] {error}"
        )

        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 500


# ----------------------------------------------------------
# LEGACY VOICE ENDPOINT
# ----------------------------------------------------------

@app.route(
    "/api/voice",
    methods=["POST"],
)
def legacy_voice():

    return voice_respond()


# ----------------------------------------------------------
# STATUS
# ----------------------------------------------------------

@app.route(
    "/api/status",
    methods=["GET"],
)
def status():

    try:

        conversation_count = (
            __import__(
                "app.memory.conversation",
                fromlist=["ConversationMemory"],
            )
            .ConversationMemory()
            .count_conversations()
        )

    except Exception:

        conversation_count = 0

    return jsonify(
        {
            "status": "online",
            "model": getattr(
                llm,
                "model",
                "qwen2.5:3b-instruct",
            ),
            "memory": True,
            "web": True,
            "voice": True,
            "security": True,
            "conversation_count": conversation_count,
        }
    )


# ==========================================================
# START SERVER
# ==========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("              SYNORA AI")
    print("              LOCAL UI")
    print("=" * 60)
    print()
    print("Model: Qwen2.5 3B Instruct")
    print("Memory: SQLite")
    print("Web Search: Enabled")
    print("Voice STT: Local Whisper")
    print("Voice TTS: Windows SAPI5")
    print()
    print("Open:")
    print("http://127.0.0.1:5000")
    print()
    print("Press CTRL+C to stop.")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
    )