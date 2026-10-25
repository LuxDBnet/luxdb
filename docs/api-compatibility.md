# LuxDB Python client

Python 3.10 or later. Responses are JSON dictionaries with generated type hints;
they are not validated or converted at runtime. Unspecified fields stay untyped.

The client uses the demo key by default. A paid key requires allow_paid=True.
It makes one request per call, without retries, redirects or automatic paging.

Python timeout and JavaScript timeoutMs both set one overall monotonic deadline,
covering connection, headers and the whole success or error body. The Python
stdlib transport supervises one short-lived HTTP child, stops it on expiry and
reaps it before returning TransportTimeout (also a TimeoutError). Startup counts
towards the deadline; termination/reaping may add a small scheduling delay. No
background worker remains and no retry is attempted after an uncertain outcome.

The built-in transport honours HTTPS_PROXY/https_proxy and NO_PROXY/no_proxy
as urllib does. The API key travels inside TLS; choose trusted proxy and CA
settings. HTTP_PROXY/http_proxy and ALL_PROXY are not passed to the worker.
Its explicit environment allowlist contains PATH, SSL_CERT_FILE/SSL_CERT_DIR
and those HTTPS proxy/bypass settings; on Windows only, SYSTEMROOT, WINDIR,
TEMP and TMP are also allowed. No other application environment is inherited.

A custom Transport is trusted code: it receives the key and URL and must keep
the destination, forbid retries and redirects, enforce the response read limit
and honour the same overall timeout. The client cannot enforce I/O rules inside
an injected transport.

Family IDs must match the format in the contract. The index requires Business
access. Successful index downloads use the daily allowance, even if unchanged.
The client does not send If-None-Match, expose ETag, or return a 304 result; use
a conditional HTTP client for unchanged downloads. Do not poll the index.

On HTTP errors, check ApiError.status, code, mode and retry_after_seconds.
Mode is maintenance or stopped when supplied. On 402, inspect the code before
deciding whether to add credits or ask the team owner about an allowance.
Follow Retry-After when present. No failed request is retried automatically.

Nullable prices, dimensions and country counts come from the canonical
contract itself; neither client applies manual type overrides. Unknown error keys remain in
ApiError.details, without appearing in its message. Inspect details explicitly;
do not log it. 404 and 405 are ordinary HTTP API errors.

The demo key allows 1 request per minute and 300 per day per address.
Make one call or wait at least 60 seconds; on 429 follow Retry-After.
X-RateLimit-Remaining includes the request just served; at the one-request-
per-minute limit it reports 0. The charge is the body field
credits_charged; there is no charge header.

See the [API reference](api-reference.md) for exact fields and response shapes.
