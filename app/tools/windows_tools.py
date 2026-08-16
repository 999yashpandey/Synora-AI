import subprocess
import psutil


def close_application(application_name: str):

    target = application_name.lower().strip()

    found = False

    for process in psutil.process_iter(["name"]):

        try:
            process_name = process.info["name"]

            if not process_name:
                continue

            if target in process_name.lower():
                process.terminate()
                found = True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if found:
        return f"{application_name.title()} has been closed."

    return f"I couldn't find {application_name} running."


def open_folder(path: str):

    try:
        subprocess.Popen(
            ["explorer.exe", path]
        )

        return f"Opening {path}."

    except Exception as error:
        return f"I couldn't open that folder: {error}"
    