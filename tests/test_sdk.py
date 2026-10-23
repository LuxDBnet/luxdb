"""Network-free SDK tests; every transport response is synthetic."""
import inspect
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "clients/python/src"))
from luxdb_client import ApiError, Client, Response, TransportError
from luxdb_client.generated import API_BASE_URL
from luxdb_client.transport import HTTPTransport, MAX_RESPONSE_BYTES, NoRedirect, Request


class MockTransport:
    def __init__(self, response=None):
        self.requests = []
        self.response = response or Response(200, {}, b'{"synthetic": true}')

    def send(self, request):
        self.requests.append(request)
        return self.response


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.network_guard = patch.object(HTTPTransport, "send", side_effect=AssertionError("network forbidden in tests"))
        self.network_guard.start()
        self.addCleanup(self.network_guard.stop)

    def test_all_eight_generated_operations(self):
        mock = MockTransport()
        client = Client(transport=mock)
        calls = [lambda: client.article("SYNTHETIC-ITEM", brand="lv"),
                 lambda: client.search(q="synthetic", page="1"),
                 lambda: client.changes("synthetic-week", page="1"),
                 lambda: client.family("nvprod0v"),
                 lambda: client.resolve("synthetic-url"),
                 lambda: client.index(), lambda: client.snapshot(), lambda: client.openapi()]
        for call in calls:
            self.assertEqual(call(), {"synthetic": True})
        self.assertEqual(len(mock.requests), 8)
        for request in mock.requests[:-1]:
            self.assertEqual(request.headers["X-API-Key"], "demo")
            self.assertEqual(request.method, "GET")
        self.assertNotIn("X-API-Key", mock.requests[-1].headers)
        self.assertEqual(urlsplit(mock.requests[0].url).path, "/api/v1/article")
        self.assertEqual(parse_qs(urlsplit(mock.requests[0].url).query)["codes"], ["SYNTHETIC-ITEM"])

    def test_paid_credentials_require_explicit_opt_in(self):
        with self.assertRaises(ValueError):
            Client(api_key="SYNTHETIC-KEY", transport=MockTransport())
        mock = MockTransport()
        client = Client(api_key="SYNTHETIC-KEY", allow_paid=True, transport=mock)
        self.assertEqual(mock.requests, [])
        client.snapshot()
        self.assertEqual(mock.requests[0].headers["X-API-Key"], "SYNTHETIC-KEY")
        self.assertNotIn("SYNTHETIC-KEY", repr(client))
        self.assertNotIn("SYNTHETIC-KEY", repr(mock.requests[0]))
        self.assertNotIn("SYNTHETIC-KEY", repr(Response(200, {"synthetic": "SYNTHETIC-KEY"}, b'SYNTHETIC-KEY')))

    def test_header_and_timeout_validation(self):
        for key in ("", "demo\n", "synthetic\rheader", None):
            with self.assertRaises(ValueError):
                Client(api_key=key, allow_paid=True, transport=MockTransport())
        for timeout in (0, -1, float("inf"), float("nan"), True, "20"):
            with self.assertRaises(ValueError):
                Client(timeout=timeout, transport=MockTransport())

    def test_batch_boundaries_and_no_extra_calls(self):
        mock = MockTransport()
        client = Client(transport=mock)
        client.article(",".join(["SYNTHETIC-ITEM"] * 20))
        for codes in ("", " ", ",", "SYNTHETIC-ITEM,", ",".join(["SYNTHETIC-ITEM"] * 21)):
            with self.assertRaises(ValueError):
                client.article(codes)
        self.assertEqual(len(mock.requests), 1)

    def test_query_and_path_encoding(self):
        mock = MockTransport()
        client = Client(transport=mock)
        client.search(q="synthetic & query", brand=None)
        params = parse_qs(urlsplit(mock.requests[-1].url).query)
        self.assertEqual(params, {"q": ["synthetic & query"]})
        with self.assertRaises(ValueError):
            client.family("SYNTHETIC/FAMILY ?")
        client.family("nvprod0v")
        self.assertTrue(mock.requests[-1].url.endswith("/family/nvprod0v"))
        with self.assertRaises(TypeError):
            client.search(page=1)
        with self.assertRaises(ValueError):
            client.changes("")
        for identifier in (".", ".."):
            with self.assertRaises(ValueError):
                client.family(identifier)

    def test_error_is_redacted_and_not_retried(self):
        body = json.dumps({"code": "maintenance", "error": "SYNTHETIC-KEY", "retry_after_seconds": 99}).encode()
        mock = MockTransport(Response(503, {"rEtRy-AfTeR": "3600"}, body))
        with self.assertRaises(ApiError) as caught:
            Client(transport=mock).snapshot()
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.retry_after_seconds), (503, "maintenance", 3600))
        self.assertNotIn("SYNTHETIC-KEY", str(caught.exception))
        self.assertEqual(len(mock.requests), 1)
        self.assertFalse(hasattr(caught.exception, "body"))

    def test_unknown_http_errors_and_retry_body(self):
        for body in (b'not json', b'{"code": "SYNTHETIC-KEY"}'):
            with self.assertRaises(ApiError) as caught:
                Client(transport=MockTransport(Response(401, {}, body))).search()
            self.assertEqual(caught.exception.code, "http_error")
        with self.assertRaises(ApiError) as caught:
            Client(transport=MockTransport(Response(429, {}, b'{"code":"rate_limited", "retry_after_seconds":7}'))).snapshot()
        self.assertEqual(caught.exception.retry_after_seconds, 7)

    def test_invalid_success_and_byte_limit(self):
        for body in (b'not json', b'[]', b'null', b'\xff'):
            with self.assertRaises(TransportError):
                Client(transport=MockTransport(Response(200, {}, body))).snapshot()
        with self.assertRaises(TransportError):
            Client(transport=MockTransport(Response(200, {}, b'x' * (MAX_RESPONSE_BYTES + 1)))).snapshot()

    def test_required_schema_parameter_signatures(self):
        self.assertEqual(inspect.signature(Client.article).parameters["codes"].default, inspect.Parameter.empty)
        self.assertEqual(inspect.signature(Client.changes).parameters["since"].default, inspect.Parameter.empty)
        self.assertEqual(inspect.signature(Client.resolve).parameters["url"].default, inspect.Parameter.empty)

    def test_redirect_policy_does_not_forward_a_request(self):
        redirect = NoRedirect()
        target = "https" + "://" + "synthetic" + ".invalid/"
        self.assertIsNone(redirect.redirect_request(None, None, 302, "redirect", {}, target))

    def test_http_transport_without_network(self):
        self.network_guard.stop()  # Exercise the real send method with a mocked opener.
        request = Request("GET", API_BASE_URL + "/snapshot", {}, 1.0)
        from luxdb_client._http_worker import exchange
        from unittest.mock import Mock
        opener = Mock()
        error = urllib.error.HTTPError(request.url, 503, "synthetic", {}, None)
        error.read = lambda size: b'{"code":"maintenance"}'
        opener.open.side_effect = error
        response = exchange({"url": request.url, "headers": {}, "method": "GET", "timeout": 1}, opener)
        self.assertEqual(response["status"], 503)
        with patch("subprocess.Popen", side_effect=urllib.error.URLError("SYNTHETIC-KEY")):
            with self.assertRaises(TransportError) as caught:
                HTTPTransport().send(request)
        self.assertNotIn("SYNTHETIC-KEY", str(caught.exception))



if __name__ == "__main__":
    unittest.main()
