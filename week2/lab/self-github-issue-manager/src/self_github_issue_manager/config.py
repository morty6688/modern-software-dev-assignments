import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "morty6688/cs146s-w2-issue-manager-test"
SERVER = "self-github-issue-manager"


@dataclass(frozen=True)
class Config:
    client_id: str = ""
    client_secret: str = ""
    callback: str = "http://localhost:18765/callback"

    @classmethod
    def load(cls):
        load_dotenv(ROOT / ".env")
        return cls(
            os.getenv("GITHUB_CLIENT_ID", ""),
            os.getenv("GITHUB_CLIENT_SECRET", ""),
            os.getenv("GITHUB_CALLBACK_URL", "http://localhost:18765/callback"),
        )

    def validate(self):
        from .errors import AppError

        u = urlparse(self.callback)
        if not self.client_id or not self.client_secret:
            raise AppError(
                "CONFIG_REQUIRED", "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env."
            )
        if (
            u.scheme != "http"
            or u.hostname not in {"localhost", "127.0.0.1"}
            or not u.port
            or u.path != "/callback"
            or u.query
            or u.fragment
            or u.username
        ):
            raise AppError(
                "INVALID_CALLBACK", "Use http://localhost:PORT/callback matching the App settings."
            )
