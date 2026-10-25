# LuxDB API reference

Definitions only. No item observations or response examples are included.
Requests use the public server in the linked [contract](../openapi/openapi.json).
Authenticated requests use X-API-Key or Bearer. The Python client uses X-API-Key.

A missing field differs from a field whose value is null. The tables use
the contract's exact names and types; prose is shortened for readability.

## GET `/article`

Read item details and history. One credit per item; see the response for charges.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `codes` | query | yes | string |  |
| `brand` | query | no | string |  |

Responses: 200, 400, 401, 402, 403, 404, 405, 429, 503.

The successful body includes `results` (object).

## GET `/search`

Search the catalogue and read a short result list.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `q` | query | no | string |  |
| `department` | query | no | string |  |
| `category` | query | no | string |  |
| `type` | query | no | string |  |
| `color` | query | no | string |  |
| `status` | query | no | string |  |
| `page` | query | no | string |  |
| `brand` | query | no | string |  |

Responses: 200, 400, 401, 403, 404, 405, 429, 503.

The successful body includes `total` (integer).
The successful body includes `page` (integer).
The successful body includes `pages` (integer).
The successful body includes `results` (array).

## GET `/changes`

Read changes since a chosen week.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `since` | query | yes | string |  |
| `page` | query | no | string |  |
| `brand` | query | no | string |  |

Responses: 200, 400, 401, 403, 404, 405, 429, 503.

The successful body includes `since` (string).
The successful body includes `departures_from` (string or null).
The successful body includes `total` (integer).
The successful body includes `page` (integer).
The successful body includes `pages` (integer).
The successful body includes `events` (array).

## GET `/family/{id}`

Read items in a family. IDs must match the documented format.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `id` | path | yes | string | ^nvprod\d+v$ |
| `brand` | query | no | string |  |

Responses: 200, 400, 401, 403, 404, 405, 429, 503.

The successful body includes `family` (Family).

## GET `/resolve`

Find an item or family from a storefront link.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `url` | query | yes | string |  |
| `brand` | query | no | string |  |

Responses: 200, 400, 401, 403, 404, 405, 429, 503.

The successful body includes `resolved` (Resolved).

## GET `/index`

Read the item index. Business access and the daily download limit apply.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `If-None-Match` | header | no | string |  |
| `brand` | query | no | string |  |

Responses: 200, 304, 400, 401, 403, 404, 405, 429, 503.

The successful body includes `count` (integer).
The successful body includes `index` (array).

The API accepts If-None-Match and can return 304 without a body.
That unchanged response does not use a download or credits.
The Python convenience client does not send this header or expose ETag;
its successful index calls use the download allowance even if unchanged.

## GET `/snapshot`

Read the latest weekly release details.

| Parameter | Location | Required | Type | Format |
|---|---|---|---|---|
| `brand` | query | no | string |  |

Responses: 200, 400, 401, 403, 404, 405, 429, 503.

The successful body includes `snapshot_id` (string).
The successful body includes `schema_version` (string).
The successful body includes `loaded_at` (string).

## GET `/openapi`

Read this API contract. No key is required.

Responses: 200.

## Response fields

### `Envelope`

| Field | Type | Required | Meaning | Allowed values |
|---|---|---|---|---|
| `credits_charged` | integer | yes | Credits this response spent. |  |
| `credits_subscription` | integer | yes | Subscription credits left after the charge. |  |
| `credits_retail` | integer | yes | Retail credits left after the charge. |  |
| `credits_member_left` | integer | no | Present only on a Business team member's key while the team owner has set a monthly limit per member: what this member may still spend this calendar month (UTC), after this response's charge. |  |
| `member_resets_at` | string | no | Present with credits_member_left: when the member's month turns, 00:00 UTC on the first of the next month. |  |
| `credits_bought` | integer | no | Present only when a pack was bought automatically on this request. |  |
| `resets_hour` | string | yes | When the hourly credit ceiling turns over for this account. |  |
| `resets_day` | string | yes | When the daily credit ceiling turns over for this account. |  |
| `resets_month` | string | yes | When the subscription's next allowance is credited: every 30 days from the start of the period, not the first of the calendar month. |  |
| `snapshot` | string | yes | Weekly data release identifier. |  |
| `fields_refreshed_weekly` | boolean | yes | Whether the descriptive fields are re-read weekly the way prices are. |  |
| `field_age_median_weeks` | number or null | yes | Median age of product details, in weeks; null if unavailable. |  |
| `account_status` | string | no | On a sandbox answer to a registered account: `registered` until the account has credits, then `active`. | `registered`, `active` |
| `sandbox` | boolean | no | Present when the answer came from the demo set rather than the catalogue. |  |

### `Error`

| Field | Type | Required | Meaning | Allowed values |
|---|---|---|---|---|
| `error` | string | yes | A sentence for a person. |  |
| `code` | string | yes | Machine-readable error code. | `unauthorized`, `plan`, `payment_required`, `rate_limited`, `search_cap`, `account_paused`, `account_closed`, `member_limit_reached`, `not_found`, `method_not_allowed`, `bad_request`, `api_disabled`, `maintenance`, `internal_error` |
| `mode` | string | no | When present on 503, the service is under maintenance or stopped. | `maintenance`, `stopped` |
| `scope` | string | no | Whose account allowance the error concerns. | `member` |
| `member_limit` | integer | no | On `member_limit_reached`: the member's monthly limit. |  |
| `member_used` | integer | no | On `member_limit_reached`: credits this member spent this month. |  |
| `resets_at` | string | no | On `member_limit_reached`: 00:00 UTC on the first of the next month. |  |
| `retry_after_seconds` | integer | no | On 429 and 503. |  |
| `hint` | string | no | A further sentence for a person: what to do next, or which limit applied. |  |
| `batch_max` | integer | no | On a batch with too many codes: the most one request may ask for. |  |
| `brands` | array | no | On an unknown or not yet open brand: the houses that are open. |  |
| `plan` | string | no | On `plan` (403): the plan the key belongs to. |  |
| `sandbox` | boolean | no | On a sandbox refusal: true, the limit was the sandbox's. |  |
| `remaining_today` | integer | no | On a sandbox refusal: requests left today for this address or account. |  |

### `Family`

| Field | Type | Required | Meaning | Allowed values |
|---|---|---|---|---|
| `family_id` | string | yes | The family id asked. |  |
| `articles` | array | yes | Every member of the family, in code order. |  |
| `articles[].article` | string | yes | The member's article code. |  |
| `articles[].name` | string or null | yes | Its English name, or the house's own when there is none. |  |
| `articles[].color` | string or null | yes | Its colour, once your account has bought it; null before. |  |
| `articles[].status` | string or null | yes | Its status, as on the card. |  |
| `articles[].size_scale` | string or null | yes | Its size scale, once your account has bought it; null before. |  |

### `Resolved`

| Field | Type | Required | Meaning | Allowed values |
|---|---|---|---|---|
| ` (case 1).status` | string | yes | What kind of page the link is. | `product` |
| ` (case 1).article` | string | yes | The article the link is the page of. |  |
| ` (case 1).region` | string or null | yes | The storefront the link belongs to. |  |
| ` (case 1).lv_url_status` | string or null | yes | The link's status, as lv_url_status on the card. |  |
| ` (case 2).status` | string | yes | What kind of page the link is. | `family` |
| ` (case 2).family_id` | string | yes | The family the link is the page of. |  |
| ` (case 2).articles` | array | yes | The family's article codes. |  |
| ` (case 2).region` | string or null | yes | The storefront the link belongs to. |  |
| ` (case 3).status` | string | yes | What kind of page the link is. | `variant` |
| ` (case 3).key` | string | yes | The code in the link. |  |
| ` (case 3).variant_of` | string or null | yes | The article that has the card, once your account has bought it; null before. |  |
| ` (case 3).variant_kind` | string or null | yes | Size or colour, once your account has bought it; null before. |  |
| ` (case 3).label` | string or null | yes | The variation's label, once your account has bought it; null before. |  |
| ` (case 3).region` | string or null | yes | The storefront the link belongs to. |  |
| ` (case 4).status` | string | yes | What kind of page the link is. | `not_in_catalog` |
| ` (case 4).key` | string | yes | The code in the link. |  |
| ` (case 4).region` | string or null | yes | The storefront the link belongs to. |  |
| ` (case 5).status` | string | yes | What kind of page the link is. | `unrecognized_url` |

### `Article`

| Field | Type | Required | Meaning | Allowed values |
|---|---|---|---|---|
| `article` | string | no | Article — the brand's reference code for the item; with brand, the key of every table. |  |
| `requested` | object or null | no | Null when the code asked is this card's own. |  |
| `requested.code` | string | yes | Machine-readable error code. |  |
| `requested.article` | string or null | yes | The card the asked code has of its own — for a duplicate code, the card it duplicates; null when it has none. |  |
| `requested.size_label` | string or null | yes | The size the asked code stands for, when it stands for one. |  |
| `requested.alias_kind` | string or null | yes | How the asked code relates to this card, when it is a size code. |  |
| `brand` | string | no | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | string | no | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `slug` | string | no | The stable, opaque address of this article on the storefront, not the house's product identifier. |  |
| `name` | string or null | no | Item name in English, as the brand writes it. |  |
| `name_source` | string | no | Origin of the display name. | `brand_english_page`, `dictionary`, `partial`, `model_name`, `original_language`, `brand_english` |
| `name_lang` | string | no | Language of the name (en, pt, es, de, fr, it, zh, ko, ja…); may differ from text_lang. |  |
| `family_id` | string | no | Model: the brand's page or code that groups the colours and sizes of one model. |  |
| `family_alias_of` | string or null | no | Main article of the same product, listed by the brand under another code on another model page. |  |
| `department` | string | no | Product department. | `Accessories`, `Bags & Small Leather Goods`, `Beauty`, `Books`, `Equestrian`, `Eyewear`, `Fashion Jewelry`, `Fine Jewelry`, `Fragrance`, `Home`, `Other`, `Ready-to-Wear`, `Shoes`, `Tech & Objects`, `Travel`, `Watches` |
| `category` | string or null | no | Category within the department, in English, one name per department; the storefront's own name is in category_raw. |  |
| `product_type` | string or null | no | Type of item in English (sneaker, ankle boot, tote, card holder, bracelet, belt, watch strap…), for filtering. |  |
| `collection` | string or null | no | The brand's named line, as the brand shows it. |  |
| `season` | string or null | no | Show or collection season: "Fall-Winter 2026", "Spring-Summer 2026", "Pre-Fall 2026". |  |
| `audience` | string or null | no | Who the item is for: Women, Men, Unisex or Kids, as the brand labels it or as its menu, name or description states it. | `Women`, `Men`, `Unisex`, `Kids`, `null` |
| `campaign` | array or null | no | Campaigns featuring the item, such as gift guides, seasonal capsules and collaborations (list). |  |
| `material` | string or null | no | Material in English; several differing values are joined by " · ". |  |
| `material_line` | string or null | no | The brand's named material line (a signature canvas or leather), only when the item is made of it: a print of the line's motif on cotton is not the line. |  |
| `composition` | array or null | no | Fibre composition as a list of {fiber, pct}, e.g. from "57% Wool, 25% Cashmere…". |  |
| `color` | string or null | no | Colour in English. |  |
| `color_group` | string or null | no | Colour group for the filter, one of 16 values (Black, White, Brown, Beige, Grey, Blue, Green, Red, Pink, Purple, Yellow, Orange, Gold, Silver, Multicolor, Natural). | `Black`, `Blue`, `Brown`, `Beige`, `White`, `Grey`, `Pink`, `Gold`, `Green`, `Silver`, `Red`, `Orange`, `Yellow`, `Multicolor`, `Natural`, `Purple`, `null` |
| `made_in` | string or null | no | Country or countries of manufacture in English, e.g. "Italy" or "France · Spain · Italy". |  |
| `made_in_countries` | array or null | no | Countries of manufacture as ISO 3166 codes (list, same order as made_in) — a filter. |  |
| `customizable` | boolean | no | The item can be personalised; no colour applies. |  |
| `dimensions` | object or null | no | Raw and parsed measurements, in centimetres and inches where the house publishes them. |  |
| `dimensions.raw` | string or null | no | Dimensions as published on the storefront ("29 x 17.5 x 10 cm", "33.5 x 45.3 x 23.6 inches"). |  |
| `dimensions.unit_raw` | string or null | no | Unit of the published dimensions (cm, inches, mm). |  |
| `dimensions.axes` | string or null | no | Labels of the dimensions, e.g. L×W or D×H. |  |
| `dimensions.length_cm` | number or null | no | Length in centimetres (converted when published in inches or millimetres). |  |
| `dimensions.height_cm` | number or null | no | Height in centimetres. |  |
| `dimensions.width_cm` | number or null | no | Width or depth in centimetres; for round items the diameter. |  |
| `dimensions.length_in` | number or null | no | Length in inches (centimetres / 2.54). |  |
| `dimensions.height_in` | number or null | no | Height in inches. |  |
| `dimensions.width_in` | number or null | no | Width in inches. |  |
| `measures` | object | no | Measurements that apply to this kind of thing only: heel height, case diameter, carat, karat. |  |
| `specs_json` | object | no | The house's own specification rows for this article, as published. |  |
| `sizes` | array | no | Every size row the house lists for this article, with the storefront each was read from. |  |
| `family_sizes` | array | no | Sizes the family offers that this item does not list. |  |
| `colors` | array | no | Colour names we hold in English. |  |
| `colors_untranslated` | number | no | Number of colour names not available in English. |  |
| `status` | string | no | Status (see Status names): in_catalog — In catalog (with weeks_unlisted = 1: Not listed this week) · gone — Delisted. | `in_catalog`, `e1_only`, `gone` |
| `status_as_of` | string or null | no | Last week the item was seen; for delisted items, the week it was last seen ("delisted as of"). |  |
| `weeks_unlisted` | integer | no | Consecutive weeks without a listing or price. |  |
| `variants` | object | no | How many size and colour codes resolve to this card, and in how many countries. |  |
| `size_variants` | array | no | The full size rows, not a count: matching a marketplace listing needs the size, the storefront and the code. |  |
| `size_set` | array or null | no | Every size of the set this card is the main of, in size order: the house sells each size under its own code, and one card stands for all of them. |  |
| `size_set[].code` | string or null | yes | Machine-readable error code. |  |
| `size_set[].size_label` | string or null | yes | The size as the house labels it. |  |
| `size_set[].size_scale` | string or null | yes | The scale the label belongs to (alpha, UK, ring…). |  |
| `size_set[].size_order` | number or null | yes | Sort position of the size within its scale; the elements come in this order, nulls last. |  |
| `size_set[].display_label` | string or null | yes | The size in words, as the card prints it (the same words as requested). |  |
| `size_set[].self` | boolean | yes | True on the element that is this card's own size. |  |
| `size_set[].regions` | array | yes | The storefronts that list this size, by storefront code. |  |
| `size_set[].regions[].region` | string | yes | Storefront code. |  |
| `size_set[].regions[].availability` | string or null | yes | Availability the storefront showed for this size; null when it showed none. |  |
| `size_set[].regions[].priced` | boolean or null | yes | Whether the storefront showed a price for this size. |  |
| `variant_codes` | array | no | Related product codes published by the house. |  |
| `first_seen` | string | no | First week the item was seen: listed on a storefront, live at its address, priced, or on a product page. |  |
| `last_seen` | string or null | no | Last week the item was seen (see Status names). |  |
| `record_completeness` | string | no | Product detail coverage. | `full`, `partial`, `catalog_only`, `thin` |
| `text_lang` | string | no | Language of the item's description (ISO 639-1). |  |
| `text_source_region` | string | no | Storefront the text comes from; English storefronts are preferred. |  |
| `lv_url` | string | no | Link to the item on the brand's site: an English storefront where the page is live, otherwise a local one; see lv_url_status and page_checked_snapshot. |  |
| `lv_url_status` | string | no | Link status: alive — live this week · repointed — points to another storefront where the page is live · gone_all — not found on any storefront at the latest check · unverified — not confirmed live this week · none — no link known. | `alive`, `repointed`, `gone_all`, `unverified`, `none` |
| `page_checked_snapshot` | string or null | no | Week the link was last checked. |  |
| `storefront_urls` | array | no | The article's page on each regional storefront, with its status (alive, repointed, gone) and the weeks it was first seen, last seen and last checked. |  |
| `description` | string or null | no | Marketing description in the brand's words; sizes, dimensions, care and "Made in" are in their own fields. |  |
| `description_short` | string or null | no | The brand's short blurb — the opening text of the card; in lists it stands in for the description. |  |
| `description_local` | string or null | no | Description in the language of the local storefront. |  |
| `description_source` | string or null | no | Where the English description comes from: the item's own page, the English page of the same model (the colour may differ), or an earlier week. | `own`, `same_model`, `carried`, `null` |
| `description_short_redundant` | boolean or null | no | True when the description contains the whole short blurb (then it is not shown separately). |  |
| `name_local` | string or null | no | Item name in the language of the local storefront, when a local version exists. |  |
| `name_lv` | string or null | no | Original product name when the displayed name comes from another source. |  |
| `features` | array or null | no | Features in the brand's own words, one per line, as listed on the product page (materials, hardware, closures, pockets, fit); the marketing text is in description. |  |
| `care` | array or null | no | Care and storage notes from the product page. |  |
| `sustainability` | array or null | no | Responsible-sourcing notes from the brand's sustainability section (Leather Working Group tanneries, Responsible Jewellery Council, Kimberley Process, origin). |  |
| `unparsed` | array or null | no | Additional details in the brand's own wording, as "label: value" lines. |  |
| `features_source` | string or null | no | Source of the product features. | `page`, `house_api`, `same_model`, `carried`, `null` |
| `description_from` | string or null | no | Article whose English page the description comes from. |  |
| `names_by_lang` | object or null | no | The brand's own name for the item in each storefront language, as published (ISO 639-1 → list of names); the English name is in name_en. |  |
| `carried_fields` | array or null | no | Text fields taken from an earlier week: description · features · care. |  |
| `text_source_snapshot` | string or null | no | Week the English text is from, when it is older than this week: the latest page had no English, so description, features and care come from that week. |  |
| `color_group_lv` | string or null | no | The brand's own colour group, mapped to the same 16 groups (Preto / 블랙 / ブラック → Black); shown next to color_group on the card, while the filter uses color_group. | `Black`, `Blue`, `Brown`, `Beige`, `White`, `Grey`, `Pink`, `Gold`, `Green`, `Silver`, `Red`, `Orange`, `Yellow`, `Multicolor`, `Natural`, `Purple`, `null` |
| `color_group_differs` | boolean | no | True when color_group and the brand's own colour group (color_group_lv) are both present and differ (e.g. White against the brand's Beige); false otherwise, including when one of them is empty. |  |
| `composition_secondary` | string or null | no | Secondary materials: "Lining: 100% Polyamide · Other: Lamb" (lining, inserts, other). |  |
| `made_in_multi_country` | boolean | no | True when more than one country of manufacture is stated. |  |
| `size_run` | array or null | no | Sizes listed on the item page, labels as sold, for items whose sizes are not listed in size_variants. |  |
| `size_run_region` | string or null | no | Storefront the size list comes from (its country's size scale applies). |  |
| `size_scale` | string or null | no | Size scale of the item: EU · US · UK · cm · inches · alpha · ring · ml · months · years · one_size · numeric · other. | `EU`, `US`, `UK`, `US/UK`, `inches`, `cm`, `alpha`, `ring`, `ml`, `months`, `years`, `one_size`, `numeric`, `other`, `null` |
| `sold_per_unit` | boolean | no | True when the brand sells the item per unit (single earrings, studs, cufflinks). |  |
| `lv_url_region` | string | no | Storefront the link points to. |  |
| `last_price_countries` | integer or null | no | Number of countries with a price in the last week with a price (goes with price_usd_last). |  |
| `last_price_regions` | integer or null | no | Number of storefronts with a price in that week. |  |
| `sellable_anywhere` | boolean | no | True when at least one storefront showing the item this week offers it for online purchase. |  |
| `price` | object or null | no | The reference price across storefronts, the range, and each storefront's own. |  |
| `price.usd_ref` | number or null | no | USD price for lists: the median of current prices across countries (two storefronts of one country count once). |  |
| `price.usd_min` | number or null | no | Lowest price across storefronts in USD (on the card). |  |
| `price.usd_max` | number or null | no | Highest price across storefronts in USD (on the card). |  |
| `price.usd_fr` | number or null | no | Price on the French storefront in USD (EU price incl. VAT 20%). |  |
| `price.usd_us` | number or null | no | Price on the US storefront in USD (excl. sales tax). |  |
| `price.countries` | integer or null | no | Number of countries with a current price (the USD price is the median across them). |  |
| `price.single_market` | boolean | no | True when the price is known in one country only: the USD price is that storefront's price, not a median across markets. |  |
| `price.single_market_country` | string or null | no | ISO code of that single country when price.single_market is true; otherwise empty. |  |
| `price.last_known_usd` | number or null | no | Last known USD price: the median across countries in the last week with a price; equals price.usd_ref for items with a price this week. |  |
| `price.last_known_snapshot` | string or null | no | Week of the last known price. |  |
| `price.by_storefront` | array | no | One row per storefront that has published a price for this article: the local price and currency, the dollar figure, tax, availability and the week it is from. |  |
| `price.by_storefront[].region` | string | no | Storefront code (language_country, e.g. eng_NL): the brand's site for one country and language; see the region table for the country. |  |
| `price.by_storefront[].country` | string | no | Country of the storefront. |  |
| `price.by_storefront[].language` | string or null | no | Language of the storefront (ISO 639). |  |
| `price.by_storefront[].tax_note` | string | no | Tax basis in words: "incl. VAT 20%", "excl. sales tax", "no VAT or sales tax". |  |
| `price.by_storefront[].price_includes_tax` | boolean or null | no | True when storefront prices include tax (VAT/GST): EU, UK, Switzerland, Australia, Japan, China, Brazil, Mexico, Korea, UAE; false for the United States, Canada and Hong Kong. |  |
| `price.by_storefront[].currency` | string | no | Currency of the storefront (ISO 4217). |  |
| `price.by_storefront[].local` | string or null | no | Price as published on the storefront (decimal; JPY and KRW without fraction), only when price_state = current. |  |
| `price.by_storefront[].usd` | number or null | no | Price in USD at the week's rate (the last ECB rate before the week); empty when price_state is not current (see last_price_usd). |  |
| `price.by_storefront[].availability` | string or null | no | Availability on the storefront: sellable · no · backorder · InStoreOnly · not_sold_online · empty (not reported by the storefront). | `sellable`, `no`, `backorder`, `InStoreOnly`, `not_sold_online`, `not_in_region`, ``, `null` |
| `price.by_storefront[].observed_at` | string | no | When this row was seen (UTC). |  |
| `price.by_storefront[].snapshot_id` | string | no | Week identifier. |  |
| `price.by_storefront[].is_current` | boolean | no | true — the price is current (price_state = current); false — no current price: price is empty, price_state says why, and the last known price is in last_price*. |  |
| `price.by_storefront[].state` | string | no | Price observation status. | `current`, `withdrawn`, `not_checked` |
| `price.by_storefront[].last_checked_week` | string or null | no | Last week the storefront price was checked; null if never checked. |  |
| `price.by_storefront[].article` | string or null | no | The code whose price this row is: the article itself, or on a size set's main the size that stands for this storefront. |  |
| `price.by_storefront[].size_display` | string or null | no | On a size set's main, the size this row's price is for, in words ("Size UK 5.5"), when another size of the set stands for the storefront; null on the article's own rows. |  |
| `counters` | object | no | Product coverage and media counts. |  |
| `counters.regions_with_price` | integer or null | no | Number of storefronts with a current price (0 = no prices). |  |
| `counters.regions_present` | integer | no | Storefronts where the item is listed. |  |
| `counters.regions_observed` | integer | no | Storefronts where listing was observed. |  |
| `counters.regions_declared` | integer or null | no | Storefronts reported by the house. |  |
| `counters.regions_present_ex_e1` | integer | no | Number of country storefronts that showed the item (see Status names), not counting the international storefront. |  |
| `counters.countries_with_price` | integer or null | no | Number of countries with a current price (same as price.countries). |  |
| `counters.countries_present` | integer | no | Countries where the item is listed. |  |
| `counters.countries_observed` | integer | no | Countries where listing was observed. |  |
| `counters.countries_declared` | integer or null | no | Countries reported by the house. |  |
| `counters.weeks_of_history` | integer | no | Number of weeks with a price on at least one storefront. |  |
| `counters.price_events` | integer | no | Number of weeks in which the price changed on at least one storefront. |  |
| `counters.photos` | integer or null | no | Number of photos in the current gallery, as shown on the brand's page. |  |
| `counters.photos_ever` | integer or null | no | How many photos the gallery has ever had, including photos the brand later removed (see image.last_seen). |  |
| `counters.photos_additional` | integer or null | no | Number of additional product photos not shown on the product page. |  |
| `counters.videos` | integer or null | no | Number of distinct videos. |  |
| `history` | array | no | Every price observation the archive holds for this article, by storefront and week, in the local currency and in dollars at that week's rate. |  |
| `gallery` | object | no | Photo and video counts. |  |
| `gallery.photos` | integer or null | no | Number of photos in the current gallery, as shown on the brand's page. |  |
| `gallery.videos` | integer or null | no | Number of distinct videos. |  |
| `gallery.links` | string or null | no | Media links. |  |
| `gallery.note` | string | no | Why links is null, in words. |  |

### `SearchRow`

| Field | Type | Required | Meaning | Allowed values |
|---|---|---|---|---|
| `article` | string | no | Article — the brand's reference code for the item; with brand, the key of every table. |  |
| `name` | string or null | no | Item name in English, as the brand writes it. |  |
| `family_id` | string | no | Model: the brand's page or code that groups the colours and sizes of one model. |  |
| `department` | string | no | Product department. | `Accessories`, `Bags & Small Leather Goods`, `Beauty`, `Books`, `Equestrian`, `Eyewear`, `Fashion Jewelry`, `Fine Jewelry`, `Fragrance`, `Home`, `Other`, `Ready-to-Wear`, `Shoes`, `Tech & Objects`, `Travel`, `Watches` |
| `category` | string or null | no | Category within the department, in English, one name per department; the storefront's own name is in category_raw. |  |
| `product_type` | string or null | no | Type of item in English (sneaker, ankle boot, tote, card holder, bracelet, belt, watch strap…), for filtering. |  |
| `color_group` | string or null | no | Colour group for the filter, one of 16 values (Black, White, Brown, Beige, Grey, Blue, Green, Red, Pink, Purple, Yellow, Orange, Gold, Silver, Multicolor, Natural). | `Black`, `Blue`, `Brown`, `Beige`, `White`, `Grey`, `Pink`, `Gold`, `Green`, `Silver`, `Red`, `Orange`, `Yellow`, `Multicolor`, `Natural`, `Purple`, `null` |
| `status` | string | no | Status (see Status names): in_catalog — In catalog (with weeks_unlisted = 1: Not listed this week) · gone — Delisted. | `in_catalog`, `e1_only`, `gone` |
| `price_usd_band` | string or null | no | The price band the article's dollar reference price falls in. |  |
| `regions_with_price` | integer or null | no | Number of storefronts with a current price (0 = no prices). |  |
| `countries_with_price` | integer or null | no | Number of countries with a current price (same as price_ref_countries). |  |
| `weeks_of_history` | integer | no | Number of weeks with a price on at least one storefront. |  |
| `photos` | integer or null | no | Number of photos in the current gallery, as shown on the brand's page. |  |
| `videos` | integer or null | no | Number of distinct videos. |  |

## Errors

Check the HTTP status and the error code. No request is retried automatically.
On 402, payment_required means credits are unavailable; member_limit_reached
means a team member's allowance is used. On 503, mode is maintenance or stopped.
Follow Retry-After when present. No credits are charged for a refused request.
