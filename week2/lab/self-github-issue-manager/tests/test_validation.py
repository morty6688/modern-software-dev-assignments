import httpx
import pytest
from fastmcp import Client

from self_github_issue_manager.config import Config
from self_github_issue_manager.github_client import GitHub
from self_github_issue_manager.logging_config import Audit
from self_github_issue_manager.oauth import OAuth
from self_github_issue_manager.server import create_server


@pytest.mark.parametrize("exception", [RuntimeError, ValueError])
async def test_internal_failure_is_not_input_error(tmp_path, exception):
    class BrokenGitHub:
        def issue(self, number):
            raise exception("sensitive internal detail")

    async with Client(
        create_server(github=BrokenGitHub(), audit=Audit(tmp_path / "log"))
    ) as client:
        result = (await client.call_tool("get_issue", {"issue_number": 1})).data
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "sensitive internal detail" not in str(result)


@pytest.mark.parametrize(
    "tool,args",
    [
        ("list_issues", {"state": "invalid"}),
        ("list_issues", {"per_page": 101}),
        ("get_issue", {"issue_number": True}),
        ("get_issue", {"issue_number": "7"}),
        ("create_issue", {"title": "   "}),
        ("create_issue", {"title": "ok", "dry_run": "false"}),
        ("add_issue_labels", {"issue_number": 7, "labels": []}),
        ("get_issue", {"issue_number": 7, "repo": "other/repo"}),
    ],
)
async def test_invalid_input_does_not_reach_github(tool, args, tmp_path):
    async with Client(create_server(github=object(), audit=Audit(tmp_path / "log"))) as client:
        result = (await client.call_tool(tool, args)).data
        assert result["error"]["code"] == "INVALID_INPUT"
        assert result["request_id"]


async def test_create_write_and_404(tmp_path, store, issue):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(201, json=issue) if request.method == "POST" else httpx.Response(404)

    audit = Audit(tmp_path / "log")
    github = GitHub(OAuth(Config("id", "secret"), store), audit, httpx.MockTransport(handle))
    async with Client(create_server(github, audit)) as client:
        created = (await client.call_tool("create_issue", {"title": "test", "dry_run": False})).data
        assert created["issue_number"] == 7 and calls[0].method == "POST"
        missing = (await client.call_tool("get_issue", {"issue_number": 999})).data
        assert missing["error"]["code"] == "NOT_FOUND" and not missing["error"]["retryable"]
