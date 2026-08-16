import re

from app.tools.app_tools import open_application
from app.tools.windows_tools import close_application

from app.tools.file_tools import (
    open_folder,
    open_file,
    open_named_file,
    list_folder,
    SPECIAL_FOLDERS,
)

from app.tools.system_tools import (
    get_time,
    get_date,
    get_battery,
)


def route_command(user_input: str):

    text = user_input.lower().strip()

    if not text:
        return None

    # ======================================================
    # LIST FOLDER
    # ======================================================

    list_match = re.search(
        r"\b(list|show|what.*inside|what.*in)\b.*\b"
        r"(downloads?|desktop|pictures?)\b",
        text,
    )

    if list_match:

        folder_match = re.search(
            r"\b(downloads?|desktop|pictures?)\b",
            text,
        )

        if folder_match:

            folder = folder_match.group(1)

            folder_map = {
                "download": "downloads",
                "downloads": "downloads",
                "desktop": "desktop",
                "picture": "pictures",
                "pictures": "pictures",
            }

            folder = folder_map.get(folder)

            if folder:

                return list_folder(
                    str(SPECIAL_FOLDERS[folder])
                )

    # ======================================================
    # OPEN SPECIAL FOLDER
    # ======================================================

    folder_match = re.search(
        r"\b(open|show|go to|access)\b.*\b"
        r"(downloads?|desktop|pictures?)\b",
        text,
    )

    if folder_match:

        folder = folder_match.group(2)

        folder_map = {
            "download": "downloads",
            "downloads": "downloads",
            "desktop": "desktop",
            "picture": "pictures",
            "pictures": "pictures",
        }

        folder = folder_map.get(folder)

        if folder:

            return open_folder(folder)

    # ======================================================
    # OPEN FILE
    # ======================================================

    open_match = re.search(
        r"\b(open|show|view)\b\s+(.+)",
        text,
    )

    if open_match:

        target = open_match.group(2).strip()

        target = re.sub(
            r"\b(the|file|photo|picture|image|document)\b",
            "",
            target,
        ).strip()

        folder_names = {
            "downloads",
            "download",
            "desktop",
            "pictures",
            "picture",
        }

        if target not in folder_names:

            file_result = open_named_file(target)

            if file_result is not None:

                return file_result

    # ======================================================
    # CLOSE APPLICATION
    # ======================================================

    close_match = re.search(
        r"\b(close|quit|exit|stop|terminate)\b\s+(.+)",
        text,
    )

    if close_match:

        application = close_match.group(2).strip()

        application = re.sub(
            r"\b(the|app|application|program|software)\b",
            "",
            application,
        ).strip()

        if application:

            return close_application(application)

    # ======================================================
    # OPEN APPLICATION
    # ======================================================

    if open_match:

        application = open_match.group(2).strip()

        application = re.sub(
            r"\b(the|app|application|program|software)\b",
            "",
            application,
        ).strip()

        if application not in {
            "downloads",
            "download",
            "desktop",
            "pictures",
            "picture",
        }:

            return open_application(application)

    # ======================================================
    # TIME
    # ======================================================

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

    # ======================================================
    # DATE
    # ======================================================

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

    # ======================================================
    # BATTERY
    # ======================================================

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

    # ======================================================
    # NORMAL AI REQUEST
    # ======================================================

    return None