from pathlib import Path

from app.security.permissions import PermissionManager
from app.tools.file_tools import SPECIAL_FOLDERS


permissions = PermissionManager()


SUPPORTED_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".html",
    ".css",
    ".sql",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
}


def create_code_file(
    filename: str,
    content: str,
    location: str = "desktop",
):
    """
    Create a source-code or text file in an approved Synora folder.

    The file is written directly to disk and verified afterward.
    """

    location = location.lower().strip()

    if location not in SPECIAL_FOLDERS:
        return (
            f"I don't have access to the '{location}' folder."
        )

    folder = SPECIAL_FOLDERS[location]

    if not folder.exists() or not folder.is_dir():
        return (
            f"I couldn't find the '{location}' folder."
        )

    if not permissions.is_allowed(folder):
        return (
            "I don't have permission to create files "
            "in that folder."
        )

    filename = filename.strip().strip("\"'")

    if not filename:
        return "Please provide a filename."

    output_path = folder / filename

    # Prevent accidental directory traversal.
    try:
        output_path = output_path.resolve()
        folder_resolved = folder.resolve()

        if folder_resolved not in output_path.parents:
            return (
                "I can only create files inside the "
                "approved destination folder."
            )

    except Exception as error:
        return f"I couldn't validate the output path: {error}"

    extension = output_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return (
            f"I don't currently support creating "
            f"'{extension}' files."
        )

    if not content or not content.strip():
        return "I don't have any code/content to write."

    try:
        output_path.write_text(
            content,
            encoding="utf-8",
            newline="\n",
        )

    except Exception as error:
        return (
            f"I couldn't create {output_path.name}: {error}"
        )

    # Independent verification.
    if not output_path.exists():
        return (
            "The file operation finished, "
            "but I couldn't verify that the file was created."
        )

    if not output_path.is_file():
        return (
            "The output path exists, "
            "but it isn't a regular file."
        )

    try:
        file_size = output_path.stat().st_size
    except OSError:
        file_size = 0

    if file_size == 0:
        return (
            f"{output_path.name} was created, "
            "but the file is empty."
        )

    return (
        f"Created {output_path.name} in your "
        f"{location} folder."
    )


if __name__ == "__main__":

    test_code = """def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


if __name__ == "__main__":
    print(add(10, 5))
    print(subtract(10, 5))
"""

    print(
        create_code_file(
            filename="synora_code_test.py",
            content=test_code,
            location="desktop",
        )
    )