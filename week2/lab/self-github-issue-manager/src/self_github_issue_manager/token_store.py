import hashlib
import json
import os
import sys
from pathlib import Path

from filelock import FileLock

from .config import SERVER
from .errors import AppError


class TokenStore:
    """Windows Credential Manager only; never fall back to plaintext keyring backends."""

    def __init__(self, client_id):
        if sys.platform != "win32":
            raise AppError(
                "SECURE_STORE_UNAVAILABLE",
                "This implementation requires Windows Credential Manager.",
            )
        from keyring.backends.Windows import WinVaultKeyring

        self.backend = WinVaultKeyring()
        self.account = client_id or "unconfigured"
        folder = Path(os.environ["LOCALAPPDATA"]) / SERVER
        digest = hashlib.sha256(self.account.encode()).hexdigest()[:20]
        self.lock_path = folder / f"{digest}.lock"

    @property
    def lock(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        return FileLock(self.lock_path, timeout=30)

    def load(self):
        raw = self.backend.get_password(SERVER, self.account)
        return json.loads(raw) if raw else None

    def save(self, bundle):
        # One credential write replaces both tokens and expiry timestamps together.
        self.backend.set_password(SERVER, self.account, json.dumps(bundle))
