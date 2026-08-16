import os
import subprocess
import winreg
from pathlib import Path


def get_installed_applications():
    applications = {}

    registry_locations = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
    ]

    for hive, path in registry_locations:

        try:
            key = winreg.OpenKey(hive, path)
            count = winreg.QueryInfoKey(key)[0]

            for i in range(count):

                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)

                    name = winreg.QueryValueEx(
                        subkey,
                        "DisplayName"
                    )[0]

                    try:
                        install_location = winreg.QueryValueEx(
                            subkey,
                            "InstallLocation"
                        )[0]
                    except OSError:
                        install_location = ""

                    try:
                        display_icon = winreg.QueryValueEx(
                            subkey,
                            "DisplayIcon"
                        )[0]
                    except OSError:
                        display_icon = ""

                    applications[name.lower()] = {
                        "name": name,
                        "location": install_location,
                        "icon": display_icon
                    }

                except (OSError, TypeError):
                    continue

        except OSError:
            continue

    return applications


def find_application(application_name: str):

    applications = get_installed_applications()

    query = application_name.lower().strip()

    # Exact match
    if query in applications:
        return applications[query]

    # Partial match
    for name, info in applications.items():

        if query in name:
            return info

    return None


def find_executable(application):

    # -----------------------------------
    # 1. Try DisplayIcon from registry
    # -----------------------------------

    icon = application.get("icon", "")

    if icon:

        # Remove command-line arguments if present
        icon = icon.split(",")[0].strip('"')

        if os.path.isfile(icon):
            return icon

    # -----------------------------------
    # 2. Search installation directory
    # -----------------------------------

    location = application.get("location", "")

    if location and os.path.isdir(location):

        location_path = Path(location)

        executables = list(location_path.glob("*.exe"))

        # Prefer executable matching application name
        app_name = application["name"].lower()

        for exe in executables:

            if app_name in exe.stem.lower():
                return str(exe)

        # Otherwise return first executable
        if executables:
            return str(executables[0])

    return None


def open_application(application_name: str):

    query = application_name.lower().strip()

    # Windows built-in / URI applications
    windows_apps = {
        "calculator": "calculator:",
        "calc": "calculator:",
        "settings": "ms-settings:",
        "camera": "microsoft.windows.camera:",
        "photos": "ms-photos:",
        "mail": "outlookmail:",
    }

    # Handle Windows URI applications first
    if query in windows_apps:

        try:
            os.startfile(windows_apps[query])
            return f"{application_name.title()} is opening."

        except Exception as error:
            return f"I couldn't open {application_name}: {error}"

    # Normal installed applications
    application = find_application(application_name)

    if application is None:
        return f"I couldn't find {application_name} installed on this computer."

    executable = find_executable(application)

    if executable is None:
        return (
            f"I found {application['name']}, "
            "but couldn't locate its executable."
        )

    try:

        subprocess.Popen([executable])

        return f"{application['name']} is opening."

    except Exception as error:

        return (
            f"I found {application['name']}, "
            f"but couldn't launch it: {error}"
        )