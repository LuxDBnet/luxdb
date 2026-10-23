"""Offline demo by default; a live sandbox call requires --live after opening."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "clients/python/src"))
from luxdb_client import ApiError, Client, Response, TransportError


class MockDemo:
    def send(self, request):
        fixture = json.loads((ROOT / "tests/fixtures/synthetic-response.json").read_text())
        return Response(200, {}, json.dumps(fixture["response"]).encode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="opt into one sandbox call after service opening")
    args = parser.parse_args()
    client = Client() if args.live else Client(transport=MockDemo())
    try:
        response = client.search(q="synthetic", page="1")
    except (ApiError, TransportError) as error:
        print(str(error))
        return 1
    print("Live sandbox request" if args.live else "Synthetic offline response")
    print("Credits charged:", response.get("credits_charged"))
    print("Result count:", response.get("total"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
