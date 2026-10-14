import base64
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from self_github_issue_manager.config import Config
from self_github_issue_manager.errors import AppError
from self_github_issue_manager.oauth import OAuth, authorization, validate_callback

CONFIG = Config("id", "client_SECRET")


def test_pkce_state():
    url, state, verifier = authorization(CONFIG)
    query = parse_qs(urlparse(url).query)
    assert query["code_challenge"] == [
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    ]
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == ["offline_access"]
    assert authorization(CONFIG)[1] != state
    assert validate_callback(f"/callback?state={state}&code=code", state) == "code"


@pytest.mark.parametrize(
    "path",
    [
        "/callback?state=bad&code=secret",
        "/callback?state=ok",
        "/other?state=ok&code=x",
        "/callback?state=ok&state=ok&code=x",
        "/callback?state=ok&error=access_denied",
    ],
)
def test_bad_callback(path):
    with pytest.raises(AppError):
        validate_callback(path, "ok")


def test_exchange_refresh_concurrent_rotation(store):
    calls = []

    def handle(request):
        calls.append(request.content.decode())
        return httpx.Response(
            200,
            json=dict(
                access_token="new-access",
                refresh_token="new-refresh",
                expires_in=28800,
                refresh_token_expires_in=15897600,
            ),
        )

    oauth = OAuth(CONFIG, store, httpx.MockTransport(handle))
    bundle = oauth.exchange(dict(code="only-in-memory", code_verifier="verifier"))
    assert bundle["refresh_token"] == "new-refresh"
    assert "only-in-memory" not in str(bundle)
    store.bundle["expires_at"] = 0
    with ThreadPoolExecutor(4) as pool:
        assert list(pool.map(lambda _: oauth.access_token(), range(8))) == ["new-access"] * 8
    assert len(calls) == 2
    assert "refresh_token=ghr_SECRET" in calls[1]
    assert store.load()["refresh_token"] == "new-refresh"


def test_revoked_and_refresh_failure(store):
    store.bundle["expires_at"] = 0
    oauth = OAuth(
        CONFIG,
        store,
        httpx.MockTransport(lambda r: httpx.Response(200, json={"error": "bad_refresh_token"})),
    )
    with pytest.raises(AppError, match="Authorization"):
        oauth.access_token()
    assert store.bundle["invalid"] is True
    with pytest.raises(AppError):
        oauth.access_token()


def test_old_rejection_does_not_invalidate_new_token(store):
    oauth = OAuth(CONFIG, store)
    oauth.invalidate("old")
    assert not store.bundle.get("invalid")
    oauth.invalidate("ghu_SECRET")
    with pytest.raises(AppError):
        oauth.access_token()


def test_refresh_expired(store):
    store.bundle.update(expires_at=0, refresh_expires_at=time.time() - 1)
    with pytest.raises(AppError):
        OAuth(CONFIG, store).access_token()
