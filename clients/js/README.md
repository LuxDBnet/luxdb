# LuxDB JavaScript and TypeScript client

Zero runtime dependencies. Node 18 or later, or a browser with fetch, streams and
AbortController. The ESM entry point is index.js; index.d.ts supplies types.
Use this reviewed checkout; no npm registry release is claimed. The package is
private until a separately authorised registry release.

```js
import {Client} from './clients/js/index.js';
const client = new Client();
const response = await client.search({q: 'synthetic', page: '1'});
console.log(response.credits_charged);
```

This example makes one live demo request. For an entirely offline example run
`node examples/demo.mjs` from the repository root. To run synthetic tests:
`node --test clients/js/test/*.test.mjs`.

The default key is demo. A different key requires both apiKey and allowPaid: true.
Creating a client makes no request. Every method makes one GET, without retries,
redirects, background downloads or automatic paging. Article calls may charge
credits and may buy more according to the account settings. Read credits_charged
from the response; never infer a charge from the request.

Methods take a single parameter object. See the API reference for parameters and
responses. Types are generated from the committed contract, without runtime
validation of all fields. No arbitrary base URL is accepted. A supplied fetch
implementation is trusted code and must honour redirect and abort options.

ApiError exposes status, code, mode and retryAfterSeconds. Error messages do not
contain keys, queries or response bodies. Follow Retry-After yourself; no retry is
scheduled. Redirect responses, including 304, are refused. Conditional index
requests require an HTTP client that handles ETag and a body-less response. An
index download may consume its daily allowance; do not poll it.

The client bounds response bodies to 8 MiB and requests to timeoutMs (20 seconds
by default). No service-side maximum response size is promised by that limit.
Code uses MIT; the documentation uses the repository's CC BY 4.0 terms. LuxDB is
independent of the houses named in the documentation.

Types come directly from the canonical 2.5.3 contract, including nullable prices,
dimensions and country counts. There are no client-only type overrides.
A set main includes size_set. Its storefront rows identify whose price is shown
with article and size_display; a sandbox member code can be null.
The sizes rows include shades and scents. also_written lists other spellings,
or is null. In the sandbox, a spelling that names any code but the card's own
(its article, or a code folded into it) becomes a null entry, without shortening
the list, even when that code is another demo card's. Size rows remain opaque objects
in the generated declarations, as in the contract.
Unknown error properties are retained in ApiError.details (non-enumerable), for
explicit inspection only; never log it. 404 and 405 are ordinary API errors.
The demo allows 1 request per minute and 300 per day per address. Make one call,
or wait at least 60 seconds between calls; follow Retry-After on 429.
X-RateLimit-Remaining includes the request just served; at the one-request-per-
minute limit it reports 0. There is no charge header.
