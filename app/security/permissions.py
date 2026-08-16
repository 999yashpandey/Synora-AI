from pathlib import Path


class PermissionManager:
    """
    Controls which directories Synora is allowed to access.

    Synora does NOT get unrestricted access to the computer.
    Only explicitly approved user directories are allowed.
    """

    def __init__(self):

        self.home = Path.home()

        self.allowed_directories = []

        self._add_existing_directory(
            self.home / "Desktop"
        )

        self._add_existing_directory(
            self.home / "Downloads"
        )

        self._add_existing_directory(
            self.home / "Pictures"
        )

        # --------------------------------------------------
        # OneDrive
        # --------------------------------------------------

        one_drive = self.home / "OneDrive"

        if one_drive.exists():

            self._add_existing_directory(
                one_drive / "Desktop"
            )

            self._add_existing_directory(
                one_drive / "Downloads"
            )

            self._add_existing_directory(
                one_drive / "Pictures"
            )

        # --------------------------------------------------
        # Dedicated Synora workspace
        # --------------------------------------------------

        synora_workspace = self.home / "Synora"

        if synora_workspace.exists():

            self._add_existing_directory(
                synora_workspace
            )

    # ======================================================
    # ADD EXISTING DIRECTORY
    # ======================================================

    def _add_existing_directory(self, path):

        try:

            path = path.expanduser().resolve()

        except (OSError, RuntimeError):

            return

        if path.exists() and path.is_dir():

            if path not in self.allowed_directories:

                self.allowed_directories.append(path)

    # ======================================================
    # CHECK WHETHER PATH IS ALLOWED
    # ======================================================

    def is_allowed(self, path):

        try:

            path = Path(path).expanduser().resolve()

        except (OSError, RuntimeError):

            return False

        for allowed in self.allowed_directories:

            try:

                allowed = allowed.resolve()

                # Exact directory
                if path == allowed:
                    return True

                # File/subdirectory inside allowed directory
                if allowed in path.parents:
                    return True

            except (OSError, RuntimeError):

                continue

        return False

    # ======================================================
    # GET ALLOWED DIRECTORIES
    # ======================================================

    def get_allowed_directories(self):

        return [
            str(path)
            for path in self.allowed_directories
        ]

    # ======================================================
    # ADD DIRECTORY MANUALLY
    # ======================================================

    def add_directory(self, path):

        try:

            path = Path(path).expanduser().resolve()

        except (OSError, RuntimeError):

            return False

        if not path.exists():
            return False

        if not path.is_dir():
            return False

        if path not in self.allowed_directories:

            self.allowed_directories.append(path)

        return True