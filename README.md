<p align="center">
  <a href="https://luxdb.net/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/mark-dark.png">
      <source media="(prefers-color-scheme: light)" srcset="assets/mark-light.png">
      <img src="assets/mark-light.png" alt="LuxDB" width="120">
    </picture>
  </a>
</p>

# LuxDB — luxury product archive and API: prices, availability, descriptions, specifications, photos

LuxDB archives recorded luxury product details alongside weekly price and
availability observations. Records can include descriptions, materials,
dimensions, sizes and photos, and remain available after an item leaves the
house's site. Descriptive fields are not necessarily re-read every week; use their
recorded source and observation dates.

[Pricing: choose a plan or buy credits](https://luxdb.net/pricing) ·
[Catalogue](https://luxdb.net/catalog) · [API docs](https://luxdb.net/docs/api)

Subscriptions start at **$29/month for Collector (1,000 credits; no paid API)**.
API access is available with retail credits from **$50 once**, Pro or Business.
One credit opens an item card. See the access options and repeat rules below.

For resellers, dealers, analysts, journalists and developers. Records cover
Louis Vuitton, Hermès, Dior, Loewe, Kenzo, Givenchy and Tiffany & Co.
Coverage and observation dates vary by house, item and storefront.

LuxDB is an independent service and is not affiliated with, endorsed by, or sponsored by any of the houses mentioned. Their names and trademarks belong to their respective owners.

The storefront and API are live. This repository contains Python and
JavaScript/TypeScript clients, an OpenAPI specification and field definitions;
the paid catalogue records are accessed through LuxDB, not downloaded
with this repository. API contract version: **2.6.0**.

## Choose catalogue or API access

| Option | Price in USD | Credits | Paid API access |
|---|---|---|---|
| Retail credits | From $50 once | 1,000 in the smallest pack; never expire | Included |
| Collector | $29/month or $279/year | 1,000/month | Not included |
| Pro | $149/month or $1,429/year | 6,000/month | 1 key |
| Business | $499/month or $4,790/year | 25,000/month, pooled | 1 key per seat |

For current prices, allowances and purchase terms, use the
[pricing page](https://luxdb.net/pricing). A paid record requires paid access;
the public `demo` API key is limited to demo data and needs no account.

## What the archive records

| Area | Recorded fields and available history | Where |
|---|---|---|
| Identity | House, reference code, model, names in English and in the local storefront's language, collection, season, campaigns | Card, API, export |
| Texts | The house's description, short text and feature list, care notes; the storefront and week a text comes from; a text kept from an earlier week when the page lost it | Card, API, export |
| Classification | Department, category, item type, audience | Card, API, filters |
| Materials and make | Material, composition with percentages, colour and colour group, country of manufacture | Card, API, filters |
| Dimensions | As published, and in centimetres and inches | Card, API |
| Sizes and variants | Sizes, shades and scents, other colours of the model, other spellings of the code | Card, API |
| Prices | Current price per storefront, and weekly price history per storefront with conversion to USD | Card, API, export |
| Availability | Recorded storefront availability, with the item's first and last observed week; historical coverage varies | Card, API |
| Lifecycle | Items stay in the archive after they leave the site; links per storefront with their status and the week checked | Card, API |
| Photos | The largest image the house provides (marked when below full resolution): views, size, and the first and last week each photo was in the gallery; photos removed from the house's site stay on the card | Paid card and its export only |
| Videos | The house's product videos and the weeks they were attached | Paid card and its export only |
| Weekly releases | One dated release per house per week | API, documentation |

Fields are filled where the house publishes them; coverage differs by house, item
and storefront. The API returns fields and media counts, not media files. The
public `demo` key shows the shape of a record on its sample selection, without the
houses' descriptions, feature lists or care notes. Brand texts and photos are
third-party material: access through LuxDB does not license them for reuse.

## Research with recorded product data

- **Resellers and dealers:** identify a piece from its recorded specifications,
  sizes and photos, and compare recorded storefront prices by country.
- **Researchers and journalists:** read the original description of an item that
  has left the house's site and see its recorded photos, with the weeks they were
  recorded; retain the observation dates when reporting.
- **Stylists and collectors:** inspect recorded sizes and shades and the storefront
  availability supplied for them.
- **Developers:** read specifications, texts, prices and availability through the
  REST API's documented JSON fields and the local Python or JavaScript/TypeScript
  clients.

Read the [data dictionary](https://luxdb.net/docs/data) to check the fields before
buying. Weekly observations are not a real-time stock guarantee. Storefront
prices are not resale transaction prices or an authentication of an item.

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
follow Retry-After. X-RateLimit-Remaining includes the request just served; at
the one-request-per-minute limit it reports 0.
The charge is the response body field credits_charged; there is no charge header.

Client types come directly from the supplied 2.6.0 contract, including nullable
prices and dimensions. A set main lists its sizes in size_set; its storefront
prices cover the set when size_set_one_price is true and show only the main size
when it is false. Each size's own prices are in size_set[].regions[]. A sandbox
member code can be null while its size and storefronts remain visible.
The sizes rows include shades and scents. also_written lists other spellings,
or is null. In the sandbox, a spelling that names any code but the card's own
(its article, or a code folded into it) becomes a null entry, without shortening
the list, even when that code is another demo card's. The clients keep size rows as opaque
objects, as the contract defines them.
HTTP errors retain extra keys in ApiError.details;
404 and 405 are ordinary API errors. The clients reject `.` and `..` as path identifiers
to prevent URL path normalization. See [compatibility notes](docs/api-compatibility.md).

## Questions before buying

### How does the 24-hour repeat work?

Opening an item card costs one credit. A repeat within its 24-hour window is
free. The website and API have separate repeat windows: opening on one does not
make the first opening on the other free. The API window is shared by the
account's keys. Check `credits_charged` in the response and the
[API documentation](https://luxdb.net/docs/api) for charging rules.

### Is LuxDB only price history?

No. Each item's record also keeps the house's description and feature list,
materials and composition, dimensions, sizes and variants, availability by
storefront and the photo gallery, where recorded; descriptive fields may come
from an earlier observation.
The API returns these fields and media counts; photos and videos come with the
paid card and its export. History starts with the observations available for that
item, and coverage differs by house, item and storefront.

### Can I research items no longer listed?

Yes, where LuxDB has recorded them. "Not listed this week" describes an
observation, not a manufacturing decision. Delisted does not mean discontinued.
History starts with the observations available for that item; it is not a promise
of complete history from launch.

### Does the API include original photos and videos?

The API returns documented fields and media counts, not the media files.
Original media is accessed through the paid website card and its export.
Check the [field definitions](docs/data-dictionary.md) and
[API reference](docs/api-reference.md) for what each interface returns.

### Can I keep my downloads?

Downloads are yours to keep. A download link can expire; save the files while the
link is valid. Repository code and documentation licenses do not license the
catalogue data or third-party material.

### Is this a free luxury dataset?

The repository's clients and field definitions are public. Full catalogue access
is paid. The offline examples use synthetic responses; the public `demo` API key
serves only its sample selection. It is not unrestricted access to the archive.

## Support and licenses

Issues are off at launch. Contact support@luxdb.net privately for support or security.
Code and synthetic tests use [MIT](LICENSE); original docs use
[CC BY 4.0](LICENSES/CC-BY-4.0.txt). See [NOTICE](NOTICE.md) and
[Contributing](CONTRIBUTING.md). These licenses do not grant rights to catalogue data
or third-party material.

