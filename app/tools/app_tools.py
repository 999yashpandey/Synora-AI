import os
import subprocess
import winreg
from pathlib import Path


# ============================================================
# KNOWN APPLICATION PATHS
# ============================================================

KNOWN_APPS = {
    "brave": [
        r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],

    "brave browser": [
        r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],

    "chrome": [
        r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
        r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ],

    "google chrome": [
        r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
        r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ],

    "edge": [
        r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe",
        r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
        r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
    ],

    "microsoft edge": [
        r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe",
        r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
        r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
    ],

    "firefox": [
        r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe",
        r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe",
        r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe",
    ],

    "mozilla firefox": [
        r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe",
        r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe",
        r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe",
    ],

    "notepad": [
        r"%WINDIR%\System32\notepad.exe",
    ],

    "calculator": [
        r"%WINDIR%\System32\calc.exe",
    ],

    "calc": [
        r"%WINDIR%\System32\calc.exe",
    ],
}


# ============================================================
# WINDOWS URI APPLICATIONS
# ============================================================

WINDOWS_URIS = {
    "settings": "ms-settings:",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
}


# ============================================================
# HELPERS
# ============================================================

def _expand_existing(paths):
    """Return the first existing file from a list of environment paths."""

    for path in paths:
        expanded = os.path.expandvars(path)

        if os.path.isfile(expanded):
            return expanded

    return None


def _safe_executable(path):
    """
    Validate that a path is a real executable and is not an
    installer, setup program, updater, or uninstaller.
    """

    if not path:
        return None

    try:
        path = Path(path)

        if not path.is_file():
            return None

        if path.suffix.lower() != ".exe":
            return None

        filename = path.name.lower()

        blocked_words = [
            "setup",
            "installer",
            "install",
            "uninstall",
            "updater",
            "update",
        ]

        if any(word in filename for word in blocked_words):
            return None

        return str(path)

    except (OSError, RuntimeError):
        return None


# ============================================================
# REGISTRY
# ============================================================

def get_installed_applications():
    """
    Read installed applications from the Windows uninstall registry.

    Returns:
        dict[str, dict]
    """

    applications = {}

    registry_locations = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    ]

    for hive, registry_path in registry_locations:

        try:
            key = winreg.OpenKey(
                hive,
                registry_path,
            )

            count = winreg.QueryInfoKey(key)[0]

            for index in range(count):

                try:
                    subkey_name = winreg.EnumKey(
                        key,
                        index,
                    )

                    subkey = winreg.OpenKey(
                        key,
                        subkey_name,
                    )

                    try:
                        display_name = winreg.QueryValueEx(
                            subkey,
                            "DisplayName",
                        )[0]

                    except (OSError, TypeError):
                        continue

                    if not isinstance(display_name, str):
                        continue

                    try:
                        install_location = winreg.QueryValueEx(
                            subkey,
                            "InstallLocation",
                        )[0]

                    except (OSError, TypeError):
                        install_location = ""

                    try:
                        display_icon = winreg.QueryValueEx(
                            subkey,
                            "DisplayIcon",
                        )[0]

                    except (OSError, TypeError):
                        display_icon = ""

                    application = {
                        "name": display_name,
                        "location": install_location,
                        "icon": display_icon,
                    }

                    # ------------------------------------------------
                    # IMPORTANT:
                    # Do not store obvious installer/setup entries.
                    # ------------------------------------------------

                    lower_name = display_name.lower()

                    blocked_name_words = [
                        "setup",
                        "installer",
                        "uninstaller",
                    ]

                    if any(
                        word in lower_name
                        for word in blocked_name_words
                    ):
                        continue

                    applications[lower_name] = application

                except (OSError, TypeError):
                    continue

        except (OSError, FileNotFoundError):
            continue

    return applications


# ============================================================
# APPLICATION SEARCH
# ============================================================

def find_application(application_name):
    """
    Find an installed application from the Windows registry.

    Exact matches are preferred over partial matches.
    Obvious installer/setup entries are ignored.
    """

    query = application_name.lower().strip()

    if not query:
        return None

    applications = get_installed_applications()

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if query in applications:
        return applications[query]

    # --------------------------------------------------------
    # Exact normalized name match
    # --------------------------------------------------------

    for name, application in applications.items():

        if query == name:
            return application

    # --------------------------------------------------------
    # Partial match
    #
    # Prefer shorter/more relevant names rather than blindly
    # returning the first registry entry.
    # --------------------------------------------------------

    candidates = []

    for name, application in applications.items():

        if query in name:

            candidates.append(
                (
                    len(name),
                    name,
                    application,
                )
            )

    if candidates:

        candidates.sort(
            key=lambda item: item[0]
        )

        return candidates[0][2]

    return None


# ============================================================
# FIND REAL EXECUTABLE
# ============================================================

def find_executable(application):
    """
    Locate the real executable for a registry application.
    """

    name = application.get(
        "name",
        "",
    ).lower()

    location = application.get(
        "location",
        "",
    )

    executable_names = []

    # --------------------------------------------------------
    # Known application executable mappings
    # --------------------------------------------------------

    if "brave" in name:
        executable_names.append("brave.exe")

    elif "chrome" in name:
        executable_names.append("chrome.exe")

    elif "edge" in name:
        executable_names.append("msedge.exe")

    elif "firefox" in name:
        executable_names.append("firefox.exe")

    elif "visual studio code" in name:
        executable_names.append("code.exe")

    elif name == "vlc" or "vlc media player" in name:
        executable_names.append("vlc.exe")

    # --------------------------------------------------------
    # Installation directory
    # --------------------------------------------------------

    if location and os.path.isdir(location):

        base = Path(location)

        # Direct executable first
        for executable_name in executable_names:

            candidate = base / executable_name

            safe = _safe_executable(candidate)

            if safe:
                return safe

        # Then search subdirectories
        try:

            for executable_name in executable_names:

                for candidate in base.rglob(
                    executable_name
                ):

                    safe = _safe_executable(candidate)

                    if safe:
                        return safe

        except (PermissionError, OSError):
            pass

    # --------------------------------------------------------
    # DisplayIcon
    # --------------------------------------------------------

    display_icon = application.get(
        "icon",
        "",
    )

    if display_icon:

        icon_path = display_icon.split(",")[0]

        icon_path = icon_path.strip('"')

        safe = _safe_executable(
            icon_path
        )

        if safe:
            return safe

    # --------------------------------------------------------
    # IMPORTANT:
    # Never perform a random *.exe search here.
    #
    # This prevents files such as:
    #
    # BraveBrowserSetup-BRV010.exe
    #
    # from being launched.
    # --------------------------------------------------------

    return None


# ============================================================
# SPECIAL APPLICATION RESOLVERS
# ============================================================

def _find_brave():
    """
    Find the actual Brave Browser executable.

    This is intentionally independent from the Windows
    uninstall registry because registry entries can include
    Brave installers or updater components.
    """

    brave_paths = [
        r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]

    executable = _expand_existing(
        brave_paths
    )

    if executable:
        return _safe_executable(
            executable
        )

    return None


def _find_chrome():
    """Find the real Google Chrome executable."""

    chrome_paths = [
        r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
        r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ]

    executable = _expand_existing(
        chrome_paths
    )

    if executable:
        return _safe_executable(
            executable
        )

    return None


# ============================================================
# OPEN APPLICATION
# ============================================================

def open_application(application_name):

    query = application_name.lower().strip()

    if not query:
        return "Please tell me which application to open."

    # --------------------------------------------------------
    # BRAVE
    # --------------------------------------------------------
    #
    # Brave gets a dedicated resolver.
    #
    # This prevents:
    #
    # "open brave"
    #
    # from accidentally selecting:
    #
    # BraveBrowserSetup-BRV010.exe
    #
    # --------------------------------------------------------

    if query in {
        "brave",
        "brave browser",
    }:

        executable = _find_brave()

        if executable:

            try:
                subprocess.Popen(
                    [
                        executable
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )

                return "Brave is opening."

            except Exception as error:

                return (
                    f"I couldn't open Brave: "
                    f"{error}"
                )

        return (
            "I couldn't find the actual Brave Browser "
            "executable on this computer. "
            "I did not launch any installer or setup file."
        )

    # --------------------------------------------------------
    # CHROME
    # --------------------------------------------------------

    if query in {
        "chrome",
        "google chrome",
    }:

        executable = _find_chrome()

        if executable:

            try:
                subprocess.Popen(
                    [
                        executable
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )

                return "Google Chrome is opening."

            except Exception as error:

                return (
                    f"I couldn't open Google Chrome: "
                    f"{error}"
                )

    # --------------------------------------------------------
    # KNOWN APPLICATIONS
    # --------------------------------------------------------

    if query in KNOWN_APPS:

        executable = _expand_existing(
            KNOWN_APPS[query]
        )

        if executable:

            safe = _safe_executable(
                executable
            )

            if not safe:

                return (
                    f"I found {application_name}, "
                    "but the executable did not pass "
                    "Synora's safety check."
                )

            try:

                subprocess.Popen(
                    [
                        safe
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )

                return (
                    f"{application_name.title()} "
                    "is opening."
                )

            except Exception as error:

                return (
                    f"I couldn't open "
                    f"{application_name}: {error}"
                )

    # --------------------------------------------------------
    # WINDOWS URI
    # --------------------------------------------------------

    if query in WINDOWS_URIS:

        try:

            os.startfile(
                WINDOWS_URIS[query]
            )

            return (
                f"{application_name.title()} "
                "is opening."
            )

        except Exception as error:

            return (
                f"I couldn't open "
                f"{application_name}: {error}"
            )

    # --------------------------------------------------------
    # REGISTRY
    # --------------------------------------------------------

    application = find_application(
        application_name
    )

    if application is None:

        return (
            f"I couldn't find "
            f"{application_name} installed "
            "on this computer."
        )

    executable = find_executable(
        application
    )

    if executable is None:

        return (
            f"I found {application['name']}, "
            "but couldn't locate its real "
            "application executable."
        )

    # --------------------------------------------------------
    # FINAL SAFETY CHECK
    # --------------------------------------------------------

    safe = _safe_executable(
        executable
    )

    if safe is None:

        return (
            f"I found {application['name']}, "
            "but Synora refused to launch the "
            "executable because it failed the "
            "application safety check."
        )

    try:

        subprocess.Popen(
            [
                safe
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )

        return (
            f"{application['name']} "
            "is opening."
        )

    except Exception as error:

        return (
            f"I couldn't launch "
            f"{application['name']}: {error}"
        )