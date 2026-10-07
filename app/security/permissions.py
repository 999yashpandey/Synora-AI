from pathlib import Path


class PermissionManager:
    """
    Controls which directories Synora is allowed to access.

    Synora only searches directories explicitly listed here.
    """

    def __init__(self):
        self.home = Path.home()

        self.allowed_directories = self._build_allowed_directories()

    def _build_allowed_directories(self):
        candidates = [
            self.home / "Desktop",
            self.home / "Downloads",
            self.home / "Pictures",
            self.home / "Documents",

            # OneDrive
            self.home / "OneDrive" / "Desktop",
            self.home / "OneDrive" / "Downloads",
            self.home / "OneDrive" / "Pictures",
            self.home / "OneDrive" / "Documents",
        ]

        allowed = []

        for path in candidates:
            try:
                if path.exists() and path.is_dir():
                    resolved = path.resolve()

                    if resolved not in allowed:
                        allowed.append(resolved)

            except (OSError, RuntimeError):
                continue

        return allowed

    def is_allowed(self, path):
        """
        Return True only when path is inside an approved directory.
        """

        try:
            target = Path(path).expanduser().resolve()

            for directory in self.allowed_directories:
                try:
                    target.relative_to(directory)
                    return True
                except ValueError:
                    continue

        except (OSError, RuntimeError):
            return False

        return False

    def get_allowed_directories(self):
        return list(self.allowed_directories)
