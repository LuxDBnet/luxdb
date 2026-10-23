# LuxDB

The storefront and API are live. API contract version: **2.3.1**.

LuxDB provides weekly price and availability history across luxury houses,
including items no longer listed. Delisted does not mean discontinued.

This developer repository includes Python and JavaScript/TypeScript clients,
OpenAPI and a snapshot of the field definitions. Access to
item records uses credits; the API response reports the charge.

## Start offline

Python 3.10 or later; Node 18 or later for JavaScript. No key, network or runtime dependency is needed for the demo.

```sh
python3 -B examples/demo.py
node examples/demo.mjs
python3 -B tools/render_public.py --check
python3 -B tools/generate_clients.py --check
python3 -B -m unittest discover -s tests -v
node --test clients/js/test/*.test.mjs
python3 -B tools/check_public.py
```

- [Quickstart](docs/quickstart.md)
- [API reference](docs/api-reference.md)
- [Data dictionary](docs/data-dictionary.md)
- [Python client notes](docs/api-compatibility.md)
- [JavaScript and TypeScript client](clients/js/README.md)
- [Houses](docs/houses.md)

Public pages: [LuxDB](https://luxdb.net/), [Pricing](https://luxdb.net/pricing),
[API documentation](https://luxdb.net/docs/api), [Data dictionary](https://luxdb.net/docs/data)
and [Catalogue](https://luxdb.net/catalog). Catalogue access depends on your account.

The client uses the demo key by default. Paid keys require explicit opt-in. There
are no automatic retries, redirects or background downloads. Never share keys or
paid responses in a public report.

## Demo limits and contract notes

The shared demo key allows **1 request per minute and 300 per day per address**.
Each live example makes one call. Wait at least 60 seconds before another; on 429,
follow Retry-After. Do not rely on the demo rate-remaining header.
The charge is the response body field credits_charged; there is no charge header.

The supplied 2.3.1 contract remains unchanged. Both clients allow null for
SearchRow.price_usd_band and Article.dimensions.height_cm / height_in because the
live service can return null there. HTTP errors retain extra keys in ApiError.details;
404 and 405 are ordinary API errors. See [compatibility notes](docs/api-compatibility.md).

## Support and licenses

Issues are off at launch. Contact support@luxdb.net privately for support or security.
Code and synthetic tests use [MIT](LICENSE); original docs use
[CC BY 4.0](LICENSES/CC-BY-4.0.txt). See [NOTICE](NOTICE.md) and
[Contributing](CONTRIBUTING.md). These licenses do not grant rights to catalogue data
or third-party material.

LuxDB is an independent service and is not affiliated with, endorsed by, or sponsored by any of the houses mentioned. Their names and trademarks belong to their respective owners.
