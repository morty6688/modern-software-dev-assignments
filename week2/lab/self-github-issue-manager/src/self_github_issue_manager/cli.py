import argparse
import json
import sys
import time

from .config import Config
from .errors import AppError
from .github_client import GitHub
from .logging_config import Audit
from .oauth import OAuth
from .token_store import TokenStore


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve")
    auth = commands.add_parser("auth").add_subparsers(dest="action", required=True)
    auth.add_parser("login")
    auth.add_parser("status")
    args = parser.parse_args()
    try:
        if args.command == "serve":
            from .server import create_server

            create_server().run(transport="stdio", show_banner=False)
            return
        config = Config.load()
        store = TokenStore(config.client_id)
        oauth = OAuth(config, store)
        if args.action == "login":
            oauth.login()
            GitHub(oauth, Audit()).verify_installation()
            print(
                "Authorized; target repository installation and Issues write permission verified."
            )
        else:
            if not config.client_id:
                bundle = None
            else:
                with store.lock:
                    bundle = store.load()
            print(
                json.dumps(
                    dict(
                        authorized=bool(bundle and not bundle.get("invalid")),
                        expires_in=max(0, int(bundle["expires_at"] - time.time()))
                        if bundle
                        else None,
                        note="Local cache status only; does not prove remote authorization remains valid.",
                    )
                )
            )
    except AppError as error:
        print(json.dumps({"error": error.data}), file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:
        print(
            "Operation failed; check callback port and Windows credential storage.", file=sys.stderr
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
