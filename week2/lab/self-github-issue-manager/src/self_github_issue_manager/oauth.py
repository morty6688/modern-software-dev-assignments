import base64
import hashlib
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from filelock import Timeout

from .errors import AppError, auth_required

TOKEN_URL = "https://github.com/login/oauth/access_token"


def pkce():
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    return verifier, challenge


def authorization(config):
    verifier, challenge = pkce()
    state = secrets.token_urlsafe(32)
    query = urlencode(
        dict(
            client_id=config.client_id,
            redirect_uri=config.callback,
            state=state,
            code_challenge=challenge,
            code_challenge_method="S256",
            scope="offline_access",
        )
    )
    return "https://github.com/login/oauth/authorize?" + query, state, verifier


def validate_callback(path, state):
    u = urlparse(path)
    values = parse_qs(u.query)
    received = values.get("state", [])
    if (
        u.path != "/callback"
        or len(received) != 1
        or not secrets.compare_digest(received[0], state)
    ):
        raise AppError("INVALID_STATE", "OAuth callback state did not match; restart login.")
    if "error" in values:
        raise AppError("AUTH_DENIED", "Authorization was denied; restart login when ready.")
    codes = values.get("code", [])
    if len(codes) != 1:
        raise AppError("INVALID_CALLBACK", "Callback is missing a unique authorization code.")
    return codes[0]


class OAuth:
    def __init__(self, config, store, transport=None):
        self.config, self.store, self.transport = config, store, transport

    def exchange(self, fields):
        self.config.validate()
        try:
            with httpx.Client(
                timeout=20, transport=self.transport, follow_redirects=False
            ) as client:
                response = client.post(
                    TOKEN_URL,
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        **fields,
                    },
                )
            data = response.json()
        except (httpx.HTTPError, ValueError):
            raise AppError(
                "OAUTH_EXCHANGE_FAILED",
                "Token exchange could not be confirmed; run auth login again.",
            ) from None
        if response.status_code != 200 or "error" in data:
            raise auth_required()
        required = ("access_token", "refresh_token", "expires_in", "refresh_token_expires_in")
        if not all(data.get(k) for k in required):
            raise AppError(
                "EXPIRING_TOKENS_REQUIRED",
                "Enable expiring user tokens and authorize with offline_access.",
            )
        now = time.time()
        return dict(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=now + int(data["expires_in"]),
            refresh_expires_at=now + int(data["refresh_token_expires_in"]),
        )

    def access_token(self):
        if not self.config.client_id:
            raise auth_required()
        try:
            with self.store.lock:
                bundle = self.store.load()
                if not bundle or bundle.get("invalid"):
                    raise auth_required()
                if bundle["expires_at"] <= time.time() + 60:
                    if bundle["refresh_expires_at"] <= time.time():
                        raise auth_required()
                    # Mark pending before the non-idempotent exchange. A crash cannot replay a consumed token.
                    self.store.save({**bundle, "invalid": True})
                    bundle = self.exchange(
                        dict(grant_type="refresh_token", refresh_token=bundle["refresh_token"])
                    )
                    self.store.save(bundle)
                return bundle["access_token"]
        except Timeout:
            raise AppError(
                "AUTH_BUSY", "Another process is updating credentials.", True, retry_after=2
            ) from None

    def invalidate(self, rejected_token):
        with self.store.lock:
            current = self.store.load()
            if current and current.get("access_token") == rejected_token:
                self.store.save({**current, "invalid": True})

    def login(self):
        self.config.validate()
        url, state, verifier = authorization(self.config)
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Never log the callback URL (contains the code).

            def do_GET(self):
                try:
                    captured["code"] = validate_callback(self.path, state)
                    message, status = b"Authorization received. Return to the terminal.", 200
                except AppError as error:
                    captured["error"] = error
                    message, status = b"Authorization rejected. Restart login.", 400
                self.send_response(status)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(message)

        class CallbackServer(HTTPServer):
            def get_request(self):
                connection, address = super().get_request()
                connection.settimeout(2)
                return connection, address

        with CallbackServer(("127.0.0.1", urlparse(self.config.callback).port), Handler) as server:
            server.timeout = 1
            print("Complete GitHub authorization in the browser. Waiting up to 180 seconds.")
            if not webbrowser.open(url):
                print(url)
            deadline = time.monotonic() + 180
            while not captured and time.monotonic() < deadline:
                server.handle_request()
        if "error" in captured:
            raise captured["error"]
        if "code" not in captured:
            raise AppError("LOGIN_TIMEOUT", "No callback received within 180 seconds.")
        with self.store.lock:
            bundle = self.exchange(
                dict(
                    code=captured["code"], code_verifier=verifier, redirect_uri=self.config.callback
                )
            )
            self.store.save(bundle)
