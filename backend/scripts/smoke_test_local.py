import json
import os
import sys
from urllib.request import urlopen


def main() -> int:
    api_base = os.getenv("SMOKE_API_BASE", "http://127.0.0.1:8000")
    url = f"{api_base.rstrip('/')}/api/health"

    try:
        with urlopen(url, timeout=5) as response:
            if response.status != 200:
                print(f"Health check failed: HTTP {response.status}", file=sys.stderr)
                return 1
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"Health check request failed: {exc}", file=sys.stderr)
        return 1

    if payload.get("status") != "ok":
        print(f"Unexpected health payload: {payload}", file=sys.stderr)
        return 1

    print("Smoke test passed", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

