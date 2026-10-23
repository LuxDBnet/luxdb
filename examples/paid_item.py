"""One paid item request, after API opening, with explicit credit-usage consent."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "clients/python/src"))
from luxdb_client import ApiError, Client, TransportError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, help="your requested item code; no bulk traversal")
    parser.add_argument("--brand", default=None, help="house code if required for your item")
    parser.add_argument("--accept-credit-usage", action="store_true", help="consent to credits and possible balance charges")
    args = parser.parse_args()
    if not args.accept_credit_usage:
        parser.error("explicit --accept-credit-usage is required; this call may spend credits")
    if not args.code.strip() or "," in args.code:
        parser.error("supply one nonempty item code")
    key = os.environ.get("LUXDB_API_KEY")
    if not key or key == "demo":
        parser.error("set a paid key locally; never include it in a report")
    try:
        response = Client(api_key=key, allow_paid=True).article(args.code, brand=args.brand)
    except (ApiError, TransportError, ValueError) as error:
        print(str(error))
        return 1
    print("Credits charged:", response.get("credits_charged"))
    print("Credits bought:", response.get("credits_bought", 0))
    # Do not print or save the paid item response as a public example.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
