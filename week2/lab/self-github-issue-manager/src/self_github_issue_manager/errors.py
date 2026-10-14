class AppError(Exception):
    def __init__(self, code, message, retryable=False, **details):
        super().__init__(message)
        self.data = dict(code=code, message=message, retryable=retryable, **details)


def auth_required():
    return AppError(
        "AUTH_REQUIRED",
        "Authorization is missing, expired or revoked.",
        suggested_action="Run issue-manager auth login outside MCP, then retry.",
    )
