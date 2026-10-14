import time
from threading import RLock

import pytest


class MemoryStore:
    def __init__(self, bundle=None):
        self.bundle = bundle
        self.lock = RLock()

    def load(self):
        return self.bundle.copy() if self.bundle else None

    def save(self, bundle):
        self.bundle = bundle.copy()


@pytest.fixture
def store():
    return MemoryStore(
        dict(
            access_token="ghu_SECRET",
            refresh_token="ghr_SECRET",
            expires_at=time.time() + 1000,
            refresh_expires_at=time.time() + 5000,
        )
    )


@pytest.fixture
def issue():
    return dict(
        number=7,
        title="Example",
        body="private body",
        state="open",
        labels=[{"name": "bug"}],
        html_url="https://github.com/morty6688/cs146s-w2-issue-manager-test/issues/7",
        user={"login": "tester"},
        created_at="2026-10-14T00:00:00Z",
    )
