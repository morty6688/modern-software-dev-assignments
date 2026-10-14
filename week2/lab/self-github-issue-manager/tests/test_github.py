import httpx
import pytest

from self_github_issue_manager.config import Config
from self_github_issue_manager.errors import AppError
from self_github_issue_manager.github_client import PREFIX, GitHub
from self_github_issue_manager.logging_config import Audit
from self_github_issue_manager.oauth import OAuth


@pytest.mark.parametrize(
    "status,code,retryable",
    [
        (401, "AUTH_REQUIRED", False),
        (403, "FORBIDDEN", False),
        (404, "NOT_FOUND", False),
        (422, "VALIDATION_FAILED", False),
        (429, "RATE_LIMITED", True),
        (500, "UPSTREAM_UNAVAILABLE", True),
    ],
)
def test_errors(status, code, retryable, store, tmp_path):
    client = GitHub(
        OAuth(Config("id", "secret"), store),
        Audit(tmp_path / "log"),
        httpx.MockTransport(lambda r: httpx.Response(status)),
        sleep=lambda _: None,
    )
    with pytest.raises(AppError) as e:
        client.request("GET", PREFIX + "/issues")
    assert e.value.data["code"] == code
    assert e.value.data["retryable"] == retryable


@pytest.mark.parametrize("timeout", [False, True])
def test_uncertain_write_never_retried(timeout, store, tmp_path):
    calls = []

    def handle(r):
        calls.append(r)
        if timeout:
            raise httpx.ReadTimeout("secret body should never escape")
        return httpx.Response(503)

    client = GitHub(
        OAuth(Config("id", "secret"), store), Audit(tmp_path / "log"), httpx.MockTransport(handle)
    )
    with pytest.raises(AppError) as e:
        client.request("POST", PREFIX + "/issues", json={"title": "test"})
    assert e.value.data["code"] == "WRITE_OUTCOME_UNKNOWN"
    assert not e.value.data["retryable"] and len(calls) == 1


def test_allowlist(store, tmp_path):
    client = GitHub(OAuth(Config("id", "secret"), store), Audit(tmp_path / "log"))
    with pytest.raises(AppError):
        client.request("GET", "/repos/other/repo/issues")
