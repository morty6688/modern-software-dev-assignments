import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_real_stdio_transport(tmp_path):
    # The real entrypoint, real JSON-RPC pipes; no GitHub access or credentials needed.
    environment = {**os.environ, "GITHUB_CLIENT_ID": "", "GITHUB_CLIENT_SECRET": ""}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "self_github_issue_manager.cli", "serve"],
        env=environment,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 4
            result = await session.call_tool("create_issue", {"title": "protocol smoke test"})
            assert result.structuredContent["dry_run"] is True
            rid = result.structuredContent["request_id"]
            invalid = await session.call_tool("get_issue", {"issue_number": "secret-invalid-value"})
            assert invalid.structuredContent["error"]["code"] == "INVALID_INPUT"
            unauthorized = await session.call_tool("list_issues", {})
            assert unauthorized.structuredContent["error"]["code"] == "AUTH_REQUIRED"
    path = Path(__file__).resolve().parents[1] / "logs" / "mcp.jsonl"
    raw = path.read_text(encoding="utf-8")
    assert "secret-invalid-value" not in raw
    events = [json.loads(line) for line in raw.splitlines()]
    assert [e["event"] for e in events if e.get("request_id") == rid] == ["tool_start", "tool_end"]
