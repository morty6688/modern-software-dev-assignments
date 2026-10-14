import time
from urllib.parse import quote

import httpx

from .config import REPOSITORY
from .errors import AppError, auth_required

PREFIX = f"/repos/{REPOSITORY}"


class GitHub:
    def __init__(self, oauth, audit, transport=None, sleep=time.sleep):
        self.oauth, self.audit, self.transport, self.sleep = oauth, audit, transport, sleep

    def request(self, method, endpoint, **kwargs):
        if not endpoint.startswith(PREFIX + "/") or any(
            c in endpoint for c in ("..", "?", "#", "\\")
        ):
            raise AppError("REPOSITORY_FORBIDDEN", "Only the configured repository is accessible.")
        return self._request(method, endpoint, **kwargs)

    def _request(self, method, endpoint, **kwargs):
        token = self.oauth.access_token()
        write = method != "GET"
        for attempt in range(3 if not write else 1):
            started = time.monotonic()
            response = None
            try:
                with httpx.Client(
                    base_url="https://api.github.com",
                    timeout=20,
                    transport=self.transport,
                    follow_redirects=False,
                ) as client:
                    response = client.request(
                        method,
                        endpoint,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                        **kwargs,
                    )
            except httpx.HTTPError:
                pass
            # Endpoint values are application-generated; label names are omitted from logs.
            safe_endpoint = endpoint.split("/labels/")[0] + (
                "/labels/{name}" if "/labels/" in endpoint else ""
            )
            self.audit.emit(
                "github_api",
                method=method,
                endpoint=safe_endpoint,
                http_status=response.status_code if response is not None else None,
                duration_ms=round((time.monotonic() - started) * 1000, 3),
            )
            if response is None or response.status_code >= 500:
                if write:
                    raise AppError(
                        "WRITE_OUTCOME_UNKNOWN",
                        "GitHub may have applied the write; do not repeat it automatically.",
                        suggested_action="Use list_issues/get_issue to verify before requesting another write.",
                    )
                if attempt < 2:
                    self.sleep(0.25 * 2**attempt)
                    continue
                raise AppError(
                    "UPSTREAM_UNAVAILABLE",
                    "GitHub is temporarily unavailable.",
                    True,
                    retry_after=2,
                )
            status = response.status_code
            if status == 401:
                self.oauth.invalidate(token)
                raise auth_required()
            if status == 429 or (
                status == 403
                and (
                    response.headers.get("X-RateLimit-Remaining") == "0"
                    or "Retry-After" in response.headers
                )
            ):
                try:
                    delay = int(response.headers.get("Retry-After", "0")) or max(
                        1, int(response.headers.get("X-RateLimit-Reset", "0")) - int(time.time())
                    )
                except ValueError:
                    delay = 60
                raise AppError(
                    "RATE_LIMITED", "GitHub rate limit reached.", True, retry_after=delay
                )
            errors = {
                403: ("FORBIDDEN", "Check App Issues permissions, installation, and user access."),
                404: (
                    "NOT_FOUND",
                    "Issue/label does not exist or is inaccessible; verify the ID and installation.",
                ),
                422: (
                    "VALIDATION_FAILED",
                    "GitHub rejected input; check title and existing label names.",
                ),
            }
            if status in errors:
                raise AppError(*errors[status])
            if not 200 <= status < 300:
                raise AppError("HTTP_ERROR", "Unexpected GitHub response; check configuration.")
            try:
                return response.json(), response.links
            except ValueError:
                if write:
                    raise AppError(
                        "WRITE_OUTCOME_UNKNOWN",
                        "Write response could not be read; query before retrying.",
                    ) from None
                raise AppError("INVALID_RESPONSE", "GitHub returned invalid JSON.", True) from None

    def verify_installation(self):
        # Private internal endpoints, not exposed as arbitrary agent parameters.
        page = 1
        while True:
            data, links = self._request(
                "GET", "/user/installations", params={"per_page": 100, "page": page}
            )
            for install in data["installations"]:
                if install.get("app_slug") != "cs146s-w2-issue-manager-test-app":
                    continue
                repo_page = 1
                while True:
                    repos, more = self._request(
                        "GET",
                        f"/user/installations/{int(install['id'])}/repositories",
                        params={"per_page": 100, "page": repo_page},
                    )
                    if any(r["full_name"] == REPOSITORY for r in repos["repositories"]):
                        if install.get("permissions", {}).get("issues") != "write":
                            raise AppError(
                                "APP_PERMISSION_REQUIRED",
                                "Grant the App Issues read/write permission.",
                            )
                        return
                    if "next" not in more:
                        break
                    repo_page += 1
            if "next" not in links:
                break
            page += 1
        raise AppError(
            "APP_INSTALLATION_REQUIRED",
            "Install the configured App on the target repository and authorize an eligible user.",
        )

    def issue(self, number):
        data, _ = self.request("GET", f"{PREFIX}/issues/{number}")
        if "pull_request" in data:
            raise AppError(
                "NOT_AN_ISSUE",
                "This number identifies a pull request; use an issue_number from list_issues.",
            )
        return data

    def validate_labels(self, labels):
        for label in labels:
            self.request("GET", f"{PREFIX}/labels/{quote(label, safe='')}")


def shape(data, details=False):
    result = dict(
        issue_number=data["number"],
        title=data["title"],
        state=data["state"],
        labels=[label["name"] for label in data.get("labels", [])],
        url=data["html_url"],
    )
    if details:
        result.update(
            body=data.get("body"),
            creator=data.get("user", {}).get("login"),
            created_at=data.get("created_at"),
        )
    return result
