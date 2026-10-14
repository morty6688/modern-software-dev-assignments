"""Only synthetic test credentials are written to pytest's temporary directory."""

import json
import multiprocessing
import time
from pathlib import Path

import httpx
from filelock import FileLock

from self_github_issue_manager.config import Config
from self_github_issue_manager.oauth import OAuth


class FakeDiskStore:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.lock = FileLock(self.folder / "refresh.lock", timeout=10)

    def load(self):
        return json.loads((self.folder / "synthetic.json").read_text())

    def save(self, bundle):
        (self.folder / "synthetic.json").write_text(json.dumps(bundle))


def refresh_worker(folder, queue):
    def exchange(request):
        with (Path(folder) / "exchange-count").open("a") as handle:
            handle.write("exchange\n")
        time.sleep(0.05)
        return httpx.Response(
            200,
            json=dict(
                access_token="synthetic-new",
                refresh_token="synthetic-rotated",
                expires_in=1000,
                refresh_token_expires_in=2000,
            ),
        )

    oauth = OAuth(
        Config("test-id", "synthetic-secret"), FakeDiskStore(folder), httpx.MockTransport(exchange)
    )
    queue.put(oauth.access_token())


def test_refresh_serialized_across_processes(tmp_path):
    store = FakeDiskStore(tmp_path)
    store.save(
        dict(
            access_token="synthetic-old",
            refresh_token="synthetic-refresh",
            expires_at=0,
            refresh_expires_at=time.time() + 1000,
        )
    )
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    processes = [ctx.Process(target=refresh_worker, args=(str(tmp_path), queue)) for _ in range(3)]
    try:
        for process in processes:
            process.start()
        assert [queue.get(timeout=30) for _ in processes] == ["synthetic-new"] * 3
        for process in processes:
            process.join(10)
            assert process.exitcode == 0
        assert (tmp_path / "exchange-count").read_text().splitlines() == ["exchange"]
        assert store.load()["refresh_token"] == "synthetic-rotated"
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)
        queue.close()
