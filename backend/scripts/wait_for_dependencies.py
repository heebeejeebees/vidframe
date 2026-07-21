import os
import socket
import sys
import time
from urllib.parse import urlparse


def _parse_host_port(url_value: str, default_port: int) -> tuple[str, int]:
    parsed = urlparse(url_value)
    host = parsed.hostname
    port = parsed.port or default_port
    if not host:
        raise ValueError(f"Unable to parse host from URL: {url_value}")
    return host, int(port)


def _wait_for_port(name: str, host: str, port: int, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"[wait] {name} ready on {host}:{port}")
                return
        except OSError:
            time.sleep(1)
    raise TimeoutError(f"Timed out waiting for {name} on {host}:{port}")


def main() -> int:
    timeout_seconds = int(os.getenv("DEPENDENCY_WAIT_TIMEOUT_SECONDS", "60"))

    database_url = os.getenv("DATABASE_URL", "")
    redis_url = os.getenv("REDIS_URL", "")

    try:
        if database_url.startswith("postgresql"):
            db_host, db_port = _parse_host_port(database_url, default_port=5432)
            _wait_for_port("postgres", db_host, db_port, timeout_seconds)
        elif database_url.startswith("sqlite"):
            print("[wait] sqlite database configured; no network check required")

        if redis_url:
            redis_host, redis_port = _parse_host_port(redis_url, default_port=6379)
            _wait_for_port("redis", redis_host, redis_port, timeout_seconds)

        return 0
    except Exception as exc:
        print(f"[wait] dependency check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

