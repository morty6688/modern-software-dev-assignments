import asyncio
import json

from fastmcp import Client

from self_github_issue_manager.logging_config import Audit
from self_github_issue_manager.server import create_server


async def test_concurrent_ids(tmp_path):
    path = tmp_path / "audit"
    audit = Audit(path)
    async with Client(create_server(github=object(), audit=audit)) as client:
        results = await asyncio.gather(
            *[client.call_tool("create_issue", {"title": str(i)}) for i in range(12)]
        )
    ids = {r.data["request_id"] for r in results}
    assert len(ids) == 12
    events = [json.loads(line) for line in path.read_text().splitlines()]
    for rid in ids:
        assert [e["event"] for e in events if e["request_id"] == rid] == ["tool_start", "tool_end"]


async def test_unwritable_log_does_not_break_tools(tmp_path, monkeypatch):
    audit = Audit(tmp_path / "audit")

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(audit.logger, "info", fail)
    async with Client(create_server(github=object(), audit=audit)) as client:
        result = await client.call_tool("create_issue", {"title": "preview"})
        assert result.data["dry_run"] is True


def test_rotation(tmp_path):
    path = tmp_path / "audit"
    audit = Audit(path)
    audit.logger.handlers[0].maxBytes = 300
    for _ in range(20):
        audit.emit("test", status="success")
    assert path.with_name("audit.1").exists()
    assert not path.with_name("audit.4").exists()
