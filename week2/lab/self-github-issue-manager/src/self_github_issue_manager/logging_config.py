import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from uuid import uuid4

from fastmcp.exceptions import NotFoundError, ToolError
from fastmcp.server.middleware import Middleware
from fastmcp.tools.tool import ToolResult
from filelock import FileLock
from pydantic import ValidationError

from .config import REPOSITORY, ROOT, SERVER
from .errors import AppError

call_context = ContextVar("call_context", default=None)


class SafeRotatingHandler(RotatingFileHandler):
    def emit(self, record):
        try:
            with FileLock(self.baseFilename + ".lock", timeout=0.2):
                # Reopen after another process may have rotated the file.
                if self.stream:
                    self.stream.close()
                    self.stream = None
                super().emit(record)
                # Windows cannot rename a file held open by another server process.
                if self.stream:
                    self.stream.close()
                    self.stream = None
        except Exception:
            pass

    def handleError(self, record):
        pass


class Audit:
    def __init__(self, path=None):
        self.logger = logging.Logger(f"{SERVER}.{uuid4()}")
        self.logger.propagate = False
        try:
            path = path or ROOT / "logs" / "mcp.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = SafeRotatingHandler(
                path, maxBytes=2_000_000, backupCount=3, encoding="utf-8", delay=True
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
        except OSError:
            self.logger.addHandler(logging.NullHandler())

    def emit(self, event, **fields):
        try:
            record = dict(
                timestamp=datetime.now(timezone.utc).isoformat(),
                server=SERVER,
                repository=REPOSITORY,
                **(call_context.get() or {}),
                event=event,
                **fields,
            )
            self.logger.info(json.dumps(record, ensure_ascii=False))
        except Exception:
            pass


class AuditMiddleware(Middleware):
    def __init__(self, audit):
        self.audit = audit

    async def on_call_tool(self, context, call_next):
        rid = str(uuid4())
        known = {"list_issues", "get_issue", "create_issue", "add_issue_labels"}
        name = context.message.name if context.message.name in known else "unknown"
        token = call_context.set(dict(request_id=rid, tool=name))
        start = time.monotonic()
        # Log shapes only, never title/body/label values or unknown input strings.
        args = context.message.arguments or {}
        params = {
            k + "_length": len(v)
            for k, v in args.items()
            if k in {"title", "body", "labels"} and isinstance(v, (str, list))
        }
        for key in ("issue_number", "page", "per_page"):
            if type(args.get(key)) is int:
                params[key] = args[key]
        if type(args.get("dry_run")) is bool:
            params["dry_run"] = args["dry_run"]
        if args.get("state") in ("open", "closed", "all"):
            params["state"] = args["state"]
        self.audit.emit("tool_start", parameters=params)
        try:
            result = await call_next(context)
            data = dict(result.structured_content or {})
            data["request_id"] = rid
            self.audit.emit(
                "tool_end",
                status="dry_run" if data.get("dry_run") else "success",
                duration_ms=round((time.monotonic() - start) * 1000, 3),
                result_summary={
                    "count": len(data.get("issues", [])),
                    "issue_number": data.get("issue_number"),
                    "labels_count": len(data.get("labels", data.get("labels_after", []))),
                },
            )
            return ToolResult(structured_content=data)
        except Exception as error:
            # FastMCP wraps domain exceptions; preserve the actionable error without its traceback.
            if isinstance(error, ToolError) and error.__cause__ is not None:
                error = error.__cause__
            if isinstance(error, AppError):
                info = error.data
            elif isinstance(error, (NotFoundError, ValidationError)):
                info = dict(
                    code="INVALID_INPUT",
                    message="Check tool name and input schema; issue_number must come from list_issues.",
                    retryable=False,
                )
            else:
                info = dict(
                    code="INTERNAL_ERROR",
                    message="Internal operation failed; check configuration and credential storage.",
                    retryable=False,
                )
            self.audit.emit(
                "tool_error",
                status="error",
                error_code=info["code"],
                duration_ms=round((time.monotonic() - start) * 1000, 3),
            )
            return ToolResult(structured_content=dict(request_id=rid, error=info))
        finally:
            call_context.reset(token)
