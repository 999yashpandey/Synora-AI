import re


# ============================================================
# SYNORA IDENTITY
# ============================================================

SYNORA_IDENTITY = {
    "name": "Synora",
    "creator": "Yash Pandey",
    "description": (
        "Synora is a personal AI assistant designed to run locally "
        "on the user's computer."
    ),
    "model": "Qwen2.5 3B",
    "runtime": "Ollama",
}


def _clean(text: str) -> str:
    """Normalize user input for deterministic matching."""
    return re.sub(r"\s+", " ", text.strip().lower())


def handle_identity_command(user_input: str):
    """
    Handle questions about Synora's own identity.

    These responses are deterministic and do not depend on the LLM.
    """

    text = _clean(user_input)

    # --------------------------------------------------------
    # WHO ARE YOU?
    # --------------------------------------------------------

    identity_patterns = [
        r"^who are you\??$",
        r"^what are you\??$",
        r"^tell me about yourself\??$",
        r"^what is your name\??$",
        r"^what's your name\??$",
        r"^whats your name\??$",
        r"^who is synora\??$",
        r"^what is synora\??$",
        r"^what's synora\??$",
        r"^introduce yourself\??$",
    ]

    if any(re.match(pattern, text) for pattern in identity_patterns):
        return (
            "I'm Synora, your personal AI assistant running locally "
            "on your computer."
        )

    # --------------------------------------------------------
    # WHO CREATED YOU?
    # --------------------------------------------------------

    creator_patterns = [
        r"^who created you\??$",
        r"^who made you\??$",
        r"^who built you\??$",
        r"^who developed you\??$",
        r"^who is your creator\??$",
        r"^who's your creator\??$",
        r"^who is the creator of synora\??$",
        r"^who created synora\??$",
        r"^who made synora\??$",
        r"^who built synora\??$",
        r"^who developed synora\??$",
    ]

    if any(re.match(pattern, text) for pattern in creator_patterns):
        return (
            f"I was created by {SYNORA_IDENTITY['creator']}."
        )

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model_patterns = [
        r"^what model do you use\??$",
        r"^which model do you use\??$",
        r"^what ai model are you using\??$",
        r"^what llm do you use\??$",
        r"^which llm do you use\??$",
    ]

    if any(re.match(pattern, text) for pattern in model_patterns):
        return (
            f"I'm currently running on "
            f"{SYNORA_IDENTITY['model']} locally through "
            f"{SYNORA_IDENTITY['runtime']}."
        )

    # --------------------------------------------------------
    # CREATOR NAME
    # --------------------------------------------------------

    if re.search(
        r"\bwho is yash\b|\bwho's yash\b|\bwho is yash pandey\b",
        text,
    ):
        return (
            f"{SYNORA_IDENTITY['creator']} is the creator of Synora AI."
        )

    return None 