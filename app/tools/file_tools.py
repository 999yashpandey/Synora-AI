import os
from pathlib import Path

from app.security.permissions import PermissionManager


# ==========================================================
# PERMISSION MANAGER
# ==========================================================

permissions = PermissionManager()

HOME = Path.home()


# ==========================================================
# SPECIAL FOLDERS
# ==========================================================

def get_special_folders():

    folders = {}

    # Normal Windows folders

    desktop = HOME / "Desktop"

    if desktop.exists():
        folders["desktop"] = desktop

    downloads = HOME / "Downloads"

    if downloads.exists():
        folders["downloads"] = downloads

    pictures = HOME / "Pictures"

    if pictures.exists():
        folders["pictures"] = pictures

    # OneDrive folders

    one_drive = HOME / "OneDrive"

    if one_drive.exists():

        onedrive_desktop = one_drive / "Desktop"

        if onedrive_desktop.exists():
            folders["desktop"] = onedrive_desktop

        onedrive_downloads = one_drive / "Downloads"

        if onedrive_downloads.exists():
            folders["downloads"] = onedrive_downloads

        onedrive_pictures = one_drive / "Pictures"

        if onedrive_pictures.exists():
            folders["pictures"] = onedrive_pictures

    return folders


SPECIAL_FOLDERS = get_special_folders()


# ==========================================================
# ACCESS CHECK
# ==========================================================

def check_access(path):

    return permissions.is_allowed(path)


# ==========================================================
# OPEN FOLDER
# ==========================================================

def open_folder(folder_name: str):

    folder_name = folder_name.lower().strip()

    if folder_name not in SPECIAL_FOLDERS:

        return (
            f"I don't have access to the folder "
            f"'{folder_name}'."
        )

    path = SPECIAL_FOLDERS[folder_name]

    if not path.exists():

        return f"I couldn't find the folder '{folder_name}'."

    if not check_access(path):

        return (
            "I don't have permission to access that folder."
        )

    try:

        os.startfile(str(path))

        return f"Opening {path.name}."

    except Exception as error:

        return f"I couldn't open {path.name}: {error}"


# ==========================================================
# OPEN FILE USING PATH
# ==========================================================

def open_file(file_path: str):

    path = Path(file_path).expanduser()

    if not path.exists():

        return f"I couldn't find '{file_path}'."

    if not path.is_file():

        return f"'{file_path}' is not a file."

    if not check_access(path):

        return (
            "I found the file, but Synora doesn't have "
            "permission to access its location."
        )

    try:

        os.startfile(str(path))

        return f"Opening {path.name}."

    except Exception as error:

        return (
            f"I found {path.name}, "
            f"but couldn't open it: {error}"
        )


# ==========================================================
# FIND FILE
# ==========================================================

def find_file(filename: str):

    filename = (
        filename
        .strip()
        .strip("\"'")
        .lower()
    )

    filename_stem = Path(filename).stem.lower()

    search_locations = [
        path
        for path in permissions.allowed_directories
        if path.exists()
    ]

    # ------------------------------------------------------
    # EXACT NAME
    # ------------------------------------------------------

    for location in search_locations:

        try:

            for item in location.rglob("*"):

                if not item.is_file():
                    continue

                if item.name.lower() == filename:

                    return item

        except (PermissionError, OSError):

            continue

    # ------------------------------------------------------
    # NAME WITHOUT EXTENSION
    # ------------------------------------------------------

    for location in search_locations:

        try:

            for item in location.rglob("*"):

                if not item.is_file():
                    continue

                if item.stem.lower() == filename_stem:

                    return item

        except (PermissionError, OSError):

            continue

    # ------------------------------------------------------
    # PARTIAL MATCH
    # ------------------------------------------------------

    for location in search_locations:

        try:

            for item in location.rglob("*"):

                if not item.is_file():
                    continue

                if filename_stem in item.stem.lower():

                    return item

        except (PermissionError, OSError):

            continue

    return None


# ==========================================================
# OPEN FILE BY NAME
# ==========================================================

def open_named_file(filename: str):

    file_path = find_file(filename)

    if file_path is None:

        return None

    return open_file(str(file_path))


# ==========================================================
# LIST FOLDER
# ==========================================================

def list_folder(folder_path: str = "."):

    path = Path(folder_path).expanduser()

    if not path.exists():

        return f"I couldn't find '{folder_path}'."

    if not path.is_dir():

        return f"'{folder_path}' is not a folder."

    if not check_access(path):

        return (
            "I don't have permission to access that folder."
        )

    try:

        items = list(path.iterdir())

    except PermissionError:

        return (
            f"I don't have permission to access "
            f"{path.name}."
        )

    if not items:

        return f"{path.name} is empty."

    result = []

    for item in items[:30]:

        if item.is_dir():

            result.append(
                f"[Folder] {item.name}"
            )

        else:

            result.append(
                f"[File] {item.name}"
            )

    if len(items) > 30:

        result.append(
            f"...and {len(items) - 30} more items."
        )

    return "\n".join(result)