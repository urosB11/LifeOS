"""Application configuration.

Settings are read from environment variables with sensible defaults for local
development. All values are documented here; no secrets are stored in this file.
"""

import os
from functools import lru_cache


class Settings:
    """Application settings.

    Network:
        - Host is restricted to loopback by default (SECURITY.md).
        - Port defaults to 8000.

    Database:
        - SQLite by default, stored outside the repository.
        - LIFEOS_DATA_DIR overrides the data directory.
    """

    def __init__(self) -> None:
        # Network (SECURITY: bind only to loopback)
        self.host: str = os.getenv("LIFEOS_HOST", "127.0.0.1")
        self.port: int = int(os.getenv("LIFEOS_PORT", "8000"))

        # Allowed hosts for the Host header validation (SECURITY.md)
        self.allowed_hosts: list[str] = [
            h.strip()
            for h in os.getenv(
                "LIFEOS_ALLOWED_HOSTS", "127.0.0.1:8000,localhost:8000"
            ).split(",")
            if h.strip()
        ]

        # Data directory (DATABASE.md section 11)
        data_dir = os.getenv("LIFEOS_DATA_DIR")
        if data_dir:
            self.data_dir: str = data_dir
        else:
            # Default per-platform location (DATABASE.md 11)
            if os.name == "nt":  # Windows
                self.data_dir = os.path.join(
                    os.getenv("LOCALAPPDATA", os.path.expanduser("~")),
                    "LifeOS",
                )
            elif os.name == "posix":
                xdg = os.getenv("XDG_DATA_HOME")
                if xdg:
                    self.data_dir = os.path.join(xdg, "life-os")
                elif os.name == "posix" and "darwin" in os.uname().sysname.lower():
                    self.data_dir = os.path.join(
                        os.path.expanduser("~"),
                        "Library",
                        "Application Support",
                        "LifeOS",
                    )
                else:
                    self.data_dir = os.path.join(
                        os.path.expanduser("~"), ".local", "share", "life-os"
                    )
            else:
                self.data_dir = os.path.join(os.path.expanduser("~"), ".life-os")

        # Database URL (DATABASE.md: SQLite, outside repo)
        self.database_url: str = os.getenv(
            "LIFEOS_DATABASE_URL",
            f"sqlite:///{os.path.join(self.data_dir, 'lifeos.db')}",
        )

        # API
        self.api_v1_prefix: str = "/api/v1"

        # Application
        self.app_name: str = "Life OS"
        self.app_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()