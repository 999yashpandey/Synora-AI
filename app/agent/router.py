import re

from app.tools.app_tools import open_application
from app.tools.windows_tools import close_application

from app.tools.file_tools import (
    open_folder,
    open_named_file,
    list_folder,
    SPECIAL_FOLDERS,
)

from app.tools.system_tools import (
    get_time,
    get_date,
    get_battery,
)


# ============================================================
# SPECIAL FOLDER NAMES
# ============================================================

SPECIAL_FOLDER_NAMES = {
    "download": "downloads",
    "downloads": "downloads",

    "desktop": "desktop",

    "picture": "pictures",
    "pictures": "pictures",

    "document": "documents",
    "documents": "documents",
}


# ============================================================
# APPLICATION ALIASES
# ============================================================

APPLICATION_ALIASES = {
    "brave": "brave",
    "brave browser": "brave",

    "chrome": "chrome",
    "google chrome": "chrome",
    "google chrome browser": "chrome",

    "edge": "edge",
    "microsoft edge": "edge",
    "edge browser": "edge",

    "firefox": "firefox",
    "mozilla firefox": "firefox",
    "firefox browser": "firefox",

    "calculator": "calculator",
    "calc": "calculator",
}


# ============================================================
# HELPERS
# ============================================================

def _normalize_text(text: str) -> str:
    """
    Normalize text coming from both keyboard and Whisper.

    Handles:
    - capitalization
    - punctuation
    - extra spaces
    """

    text = str(text or "").lower().strip()

    # Replace punctuation with spaces.
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    # Collapse multiple spaces.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _clean_target(target: str) -> str:
    """
    Clean natural-language application/file targets.
    """

    target = _normalize_text(target)

    # Remove common filler words.
    target = re.sub(
        r"\b(the|app|application|program|software)\b",
        "",
        target,
        flags=re.IGNORECASE,
    )

    # "browser" is useful for voice commands such as:
    # "Open Brave browser"
    #
    # It should not prevent application alias matching.
    target = re.sub(
        r"\bbrowser\b",
        "",
        target,
        flags=re.IGNORECASE,
    )

    # Collapse spaces again after removing words.
    target = re.sub(
        r"\s+",
        " ",
        target,
    )

    return target.strip()


def _normalize_application_name(target: str):
    """
    Convert common application aliases into the canonical
    application name used by app_tools.py.
    """

    target = _normalize_text(target)

    # Direct alias lookup.
    if target in APPLICATION_ALIASES:

        return APPLICATION_ALIASES[target]

    # Handle natural voice variations.
    #
    # Examples:
    # "brave browser" -> brave
    # "open brave browser" is cleaned before this function.
    #
    # These checks also make the router more tolerant
    # of Whisper's punctuation/casing.
    if re.fullmatch(
        r"(brave)(\s+browser)?",
        target,
    ):
        return "brave"

    if re.fullmatch(
        r"(chrome|google chrome)(\s+browser)?",
        target,
    ):
        return "chrome"

    if re.fullmatch(
        r"(edge|microsoft edge)(\s+browser)?",
        target,
    ):
        return "edge"

    if re.fullmatch(
        r"(firefox|mozilla firefox)(\s+browser)?",
        target,
    ):
        return "firefox"

    if target in {
        "calculator",
        "calc",
    }:

        return "calculator"

    return target


# ============================================================
# ROUTER
# ============================================================

def route_command(user_input: str):

    text = _normalize_text(user_input)

    if not text:
        return None

    # ========================================================
    # LIST / SHOW SPECIAL FOLDERS
    # ========================================================

    list_match = re.search(
        r"\b(list|show|what.*inside|what.*in)\b.*\b"
        r"(downloads?|desktop|pictures?|documents?)\b",
        text,
    )

    if list_match:

        folder_match = re.search(
            r"\b(downloads?|desktop|pictures?|documents?)\b",
            text,
        )

        if folder_match:

            folder = SPECIAL_FOLDER_NAMES.get(
                folder_match.group(1)
            )

            if folder and folder in SPECIAL_FOLDERS:

                return list_folder(
                    str(SPECIAL_FOLDERS[folder])
                )

    # ========================================================
    # OPEN / LAUNCH APPLICATION OR FILE
    # ========================================================

    open_match = re.search(
        r"^\s*(open|show|view|launch|start|run|go to)\s+(.+?)\s*$",
        text,
    )

    if open_match:

        raw_target = open_match.group(2)

        target = _clean_target(
            raw_target
        )

        if not target:
            return None

        # ----------------------------------------------------
        # SPECIAL FOLDERS
        # ----------------------------------------------------

        if target in SPECIAL_FOLDER_NAMES:

            folder = SPECIAL_FOLDER_NAMES[target]

            if folder in SPECIAL_FOLDERS:

                return open_folder(folder)

        # ----------------------------------------------------
        # APPLICATION ALIASES
        #
        # This is deliberately checked BEFORE file lookup.
        #
        # Therefore:
        #
        # "Open Brave"
        # "Open Brave Browser"
        # "Open Brave."
        #
        # all resolve to:
        #
        # open_application("brave")
        # ----------------------------------------------------

        normalized_application = (
            _normalize_application_name(
                target
            )
        )

        if normalized_application in {
            "brave",
            "chrome",
            "edge",
            "firefox",
            "calculator",
        }:

            return open_application(
                normalized_application
            )

        # ----------------------------------------------------
        # EXACT APPLICATION NAMES
        # ----------------------------------------------------

        if target in {
            "brave",
            "brave browser",

            "chrome",
            "google chrome",
            "google chrome browser",

            "edge",
            "microsoft edge",
            "edge browser",

            "firefox",
            "mozilla firefox",
            "firefox browser",

            "calculator",
            "calc",

            "notepad",
            "settings",
            "camera",
            "photos",
        }:

            return open_application(
                target
            )

        # ----------------------------------------------------
        # FILE LOOKUP
        # ----------------------------------------------------

        file_result = open_named_file(
            target
        )

        if file_result is not None:

            return file_result

        # ----------------------------------------------------
        # GENERIC APPLICATION LOOKUP
        # ----------------------------------------------------

        return open_application(
            target
        )

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    close_match = re.search(
        r"^\s*(close|quit|terminate|stop)\s+(.+?)\s*$",
        text,
    )

    if close_match:

        application = _clean_target(
            close_match.group(2)
        )

        application = _normalize_application_name(
            application
        )

        if application:

            return close_application(
                application
            )

    # ========================================================
    # TIME
    # ========================================================

    if re.search(
        r"\b("
        r"what time is it|"
        r"what's the time|"
        r"whats the time|"
        r"current time|"
        r"tell me the time"
        r")\b",
        text,
    ):

        return get_time()

    # ========================================================
    # DATE
    # ========================================================

    if re.search(
        r"\b("
        r"what date is it|"
        r"what's today's date|"
        r"whats today's date|"
        r"today's date|"
        r"todays date|"
        r"what day is it|"
        r"current date"
        r")\b",
        text,
    ):

        return get_date()

    # ========================================================
    # BATTERY
    # ========================================================

    if re.search(
        r"\b("
        r"battery|"
        r"battery percentage|"
        r"battery level|"
        r"battery status|"
        r"how much battery"
        r")\b",
        text,
    ):

        return get_battery()

    return None
