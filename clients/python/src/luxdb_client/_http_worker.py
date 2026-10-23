"""Private one-shot worker. Only the supervising transport launches this file."""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

# CPython may synthesize this during C-locale coercion even with an empty env.
# Locale is already configured; do not retain an extra environment entry.
os.environ.pop("LC_CTYPE", None)

MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def exchange(request, opener=None):
    opener = opener if opener is not None else urllib.request.build_opener(NoRedirect())
    req = urllib.request.Request(request["url"], headers=request["headers"], method=request["method"])
    try:
        response = opener.open(req, timeout=request["timeout"])
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("response exceeds the SDK byte limit")
        return {"status": response.status, "headers": dict(response.headers),
                "body": base64.b64encode(body).decode("ascii")}


def main():
    try:
        request = json.load(sys.stdin)
        answer = exchange(request)
        sys.stdout.write(json.dumps(answer))
    except Exception:
        # No traceback, URL, credentials or response content crosses stderr.
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
