"""A small, credential-safe HTTP transport with no retries or redirects."""
from __future__ import annotations

import json
import math
import os
import re
import base64
import subprocess
import sys
import time
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .generated import API_BASE_URL, ERROR_CODES, ERROR_MODES

MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class TransportError(Exception):
    """No raw request URL, key or response body is included in this exception."""


class TransportTimeout(TransportError, TimeoutError):
    """The overall request deadline expired; the HTTP child has been reaped."""


class ApiError(Exception):
    def __init__(self, status: int, code: str, retry_after_seconds: int | None = None, mode: str | None = None, details: dict[str, Any] | None = None):
        self.details = dict(details or {})
        self.status = status
        self.code = code if code in ERROR_CODES else "http_error"
        self.retry_after_seconds = retry_after_seconds
        self.mode = mode if isinstance(mode, str) and mode in ERROR_MODES else None
        super().__init__(f"HTTP {status}: {self.code}")


@dataclass(frozen=True)
class Request:
    method: str
    url: str = field(repr=False)
    headers: Mapping[str, str] = field(repr=False)
    timeout: float


@dataclass(frozen=True)
class Response:
    status: int
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)


class Transport(Protocol):
    def send(self, request: Request) -> Response: ...


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _worker_env() -> dict[str, str]:
    """Only reviewed process/TLS/proxy settings cross the worker boundary."""
    names = {"PATH", "SSL_CERT_FILE", "SSL_CERT_DIR",
             "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy"}
    if sys.platform == "win32":
        names.update({"SYSTEMROOT", "WINDIR", "TEMP", "TMP"})
    return {name: os.environ[name] for name in names if name in os.environ}


class HTTPTransport:
    """One synchronous call, with all I/O in a short-lived, supervised child.

    A process boundary makes DNS, TLS, header and body reads cancellable together.
    Request secrets travel through stdin, never command arguments or a file.
    No worker or timer thread survives send(), including on interruption.
    """

    def _command(self):
        return [sys.executable, "-I", "-B", str(Path(__file__).with_name("_http_worker.py"))]

    def send(self, request: Request) -> Response:
        deadline = time.monotonic() + request.timeout
        child = None
        try:
            payload = json.dumps({"method": request.method, "url": request.url,
                                  "headers": dict(request.headers), "timeout": request.timeout}).encode()
            child = subprocess.Popen(self._command(), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=_worker_env())
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired("HTTP", request.timeout)
            raw, _ = child.communicate(payload, timeout=remaining)
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("HTTP", request.timeout)
            if child.returncode or len(raw) > (MAX_RESPONSE_BYTES * 4 // 3 + 65536):
                raise TransportError("HTTP transport failed")
            answer = json.loads(raw)
            body = base64.b64decode(answer["body"], validate=True)
            if len(body) > MAX_RESPONSE_BYTES:
                raise TransportError("response exceeds the SDK byte limit")
            return Response(answer["status"], answer["headers"], body)
        except subprocess.TimeoutExpired:
            raise TransportTimeout("HTTP request timed out") from None
        except Exception:
            raise TransportError("HTTP transport failed") from None
        finally:
            if child is not None:
                if child.poll() is None:
                    child.kill()
                # communicate closes pipes and joins any platform reader threads.
                child.communicate()



def _wait_seconds(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,9}", value):
        return int(value)
    return None


class BaseClient:
    def __init__(self, api_key: str = "demo", *, allow_paid: bool = False,
                 timeout: float = 20.0, transport: Transport | None = None):
        if not isinstance(api_key, str) or not api_key or any(ord(c) < 33 or ord(c) > 126 for c in api_key):
            raise ValueError("key must be nonempty printable header text")
        if api_key != "demo" and allow_paid is not True:
            raise ValueError("a non-demo key requires allow_paid=True")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        self._key = api_key
        self._timeout = float(timeout)
        self._transport = transport if transport is not None else HTTPTransport()

    def _request(self, path: str, query: dict[str, str | None], *, authenticated: bool = True) -> dict[str, Any]:
        values = {}
        for key, value in query.items():
            if value is not None:
                if not isinstance(value, str):
                    raise TypeError("query parameters must be strings")
                values[key] = value
        url = API_BASE_URL + path
        if values:
            url += "?" + urllib.parse.urlencode(values)
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["X-API-Key"] = self._key
        try:
            response = self._transport.send(Request("GET", url, headers, self._timeout))
        except TransportTimeout:
            raise TransportTimeout("HTTP request timed out") from None
        except Exception:
            raise TransportError("HTTP transport failed") from None
        try:
            return self._decode(response)
        except ApiError as error:
            raise error from None
        except Exception:
            raise TransportError("invalid service response") from None

    @staticmethod
    def _decode(response: Response) -> dict[str, Any]:
        if len(response.body) > MAX_RESPONSE_BYTES:
            raise TransportError("response exceeds the SDK byte limit")
        try:
            payload = json.loads(response.body)
        except (ValueError, UnicodeError, RecursionError):
            payload = None
        if not 200 <= response.status < 300:
            obj = payload if isinstance(payload, dict) else {}
            code = obj.get("code")
            safe_code = code if isinstance(code, str) and code in ERROR_CODES else "http_error"
            retry = next((v for k, v in response.headers.items() if k.lower() == "retry-after"), None)
            seconds = _wait_seconds(retry)
            if seconds is None:
                seconds = _wait_seconds(obj.get("retry_after_seconds"))
            raise ApiError(response.status, safe_code, seconds, obj.get("mode") if response.status == 503 else None, obj)
        if not isinstance(payload, dict):
            raise TransportError("expected a JSON object response")
        return payload

    def __repr__(self) -> str:
        return f"{type(self).__name__}(key=<redacted>)"
