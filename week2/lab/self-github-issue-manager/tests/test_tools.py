import json
from uuid import UUID

import httpx
from fastmcp import Client

from self_github_issue_manager.config import Config
from self_github_issue_manager.github_client import GitHub
from self_github_issue_manager.logging_config import Audit
from self_github_issue_manager.oauth import OAuth
from self_github_issue_manager.server import create_server


async def test_protocol_chain_and_logs(tmp_path, store, issue):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/issues"):
            return httpx.Response(200, json=[issue, {**issue, "pull_request": {}}])
        return httpx.Response(200, json=issue)

    path = tmp_path / "audit.jsonl"
    audit = Audit(path)
    github = GitHub(OAuth(Config("id", "secret"), store), audit, httpx.MockTransport(handle))
    async with Client(create_server(github, audit)) as client:
        tools = await client.list_tools()
        assert len(tools) == 4
        listed = (await client.call_tool("list_issues", {})).data
        details = (
            await client.call_tool(
                "get_issue", {"issue_number": listed["issues"][0]["issue_number"]}
            )
        ).data
        preview = (
            await client.call_tool("create_issue", {"title": "SECRET-title", "body": "SECRET-body"})
        ).data
        invalid = (await client.call_tool("get_issue", {"issue_number": -1})).data
    assert details["body"] == "private body"
    assert len(listed["issues"]) == 1
    assert preview["dry_run"] and len(requests) == 2
    assert invalid["error"]["code"] == "INVALID_INPUT"
    ids = {v["request_id"] for v in (listed, details, preview, invalid)}
    assert len(ids) == 4
    for rid in ids:
        UUID(rid, version=4)
    raw = path.read_text(encoding="utf-8")
    for secret in ("SECRET-title", "SECRET-body", "ghu_SECRET", "private body"):
        assert secret not in raw
    events = [json.loads(line) for line in raw.splitlines()]
    for rid in ids:
        matching = [e for e in events if e["request_id"] == rid]
        assert matching[0]["event"] == "tool_start"
        assert matching[-1]["event"] in {"tool_end", "tool_error"}
        assert matching[-1]["duration_ms"] >= 0


async def test_empty_pr_page_and_pr_rejection(tmp_path, store, issue):
    def handle(r):
        data = {**issue, "pull_request": {}}
        if r.url.path.endswith("/issues"):
            return httpx.Response(
                200, json=[data], headers={"Link": '<https://api.github.com/page=2>; rel="next"'}
            )
        return httpx.Response(200, json=data)

    audit = Audit(tmp_path / "log")
    github = GitHub(OAuth(Config("id", "secret"), store), audit, httpx.MockTransport(handle))
    async with Client(create_server(github, audit)) as client:
        data = (await client.call_tool("list_issues", {})).data
        assert data["issues"] == [] and data["next_page"] == 2
        for tool, args in [
            ("get_issue", {"issue_number": 7}),
            ("add_issue_labels", {"issue_number": 7, "labels": ["bug"]}),
        ]:
            result = (await client.call_tool(tool, args)).data
            assert result["error"]["code"] == "NOT_AN_ISSUE"


async def test_labels_append_and_dry_run(tmp_path, store, issue):
    writes = []

    def handle(r):
        if r.method == "POST":
            writes.append(json.loads(r.content))
            return httpx.Response(200, json=[{"name": "bug"}, {"name": "help"}])
        return httpx.Response(200, json=issue if "/issues/" in r.url.path else {"name": "help"})

    audit = Audit(tmp_path / "log")
    github = GitHub(OAuth(Config("id", "secret"), store), audit, httpx.MockTransport(handle))
    async with Client(create_server(github, audit)) as client:
        preview = (
            await client.call_tool("add_issue_labels", {"issue_number": 7, "labels": ["help"]})
        ).data
        assert preview["labels_after"] == ["bug", "help"] and not writes
        result = (
            await client.call_tool(
                "add_issue_labels", {"issue_number": 7, "labels": ["help"], "dry_run": False}
            )
        ).data
        assert result["labels"] == ["bug", "help"]
        assert writes == [{"labels": ["help"]}]
