# LuxDB data dictionary

Field definitions only. No item records, prices, images or coverage figures are included.
The public field names below come from the data dictionary. API response names
and types are listed separately in the [API reference](api-reference.md).

Dictionary snapshot; it may lag the API contract. See the API reference for newer response fields.

An empty value can mean not stated by the house, not recorded, or not applicable.
It does not mean zero. Refer to the field's meaning and allowed values.

## Item details

Table: `product_client`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `family_id` | text |  | Model: the brand's page or code that groups the colours and sizes of one model. |  |
| `name` | text |  | Item name in English, as the brand writes it. |  |
| `name_en` | text |  | Display name used on English-language cards. |  |
| `name_en_source` | text (enum) |  | Origin of the display name used on English-language cards. | `brand_english_page`, `dictionary`, `partial`, `model_name`, `original_language`, `brand_english` |
| `name_lang` | text (ISO 639-1) |  | Language of the name (en, pt, es, de, fr, it, zh, ko, ja…); may differ from text_lang. |  |
| `sold_per_unit` | bool |  | True when the brand sells the item per unit (single earrings, studs, cufflinks). |  |
| `name_local` | text |  | Item name in the language of the local storefront, when a local version exists. |  |
| `text_lang` | text (ISO 639-1) |  | Language of the item's description (ISO 639-1). |  |
| `text_source_region` | text (storefront code) |  | Storefront the text comes from; English storefronts are preferred. |  |
| `department` | text (enum) |  | Department code; see the department table for its name and order. | `Bags_SLG`, `RTW`, `Shoes`, `SoftAccessories`, `FineJewelry`, `FashionJewelry`, `Watches`, `Travel`, `Home`, `Eyewear`, `Fragrance`, `Beauty`, `Books`, `TechMisc`, `Equestrian`, `UNMAPPED` |
| `department_raw` | text (enum) |  | Department as the brand's storefront groups the item. | `Bags_SLG`, `RTW`, `Shoes`, `SoftAccessories`, `FineJewelry`, `FashionJewelry`, `Watches`, `Travel`, `Home`, `Eyewear`, `Fragrance`, `Beauty`, `Books`, `TechMisc`, `Equestrian`, `UNMAPPED` |
| `category` | text |  | Category within the department, in English, one name per department; the storefront's own name is in category_raw. |  |
| `category_raw` | text |  | Category exactly as the brand's storefront names it (e.g. "Shoulder bags", "Boots", "Calças"). |  |
| `category_source` | text (enum) |  | Category origin as reported in the data. | `main_category`, `category_path`, `standard_category`, `sitemap`, `collection`, `type`, `broad` |
| `collection` | text |  | The brand's named line, as the brand shows it. |  |
| `campaign` | text[] — JSON array of strings |  | Campaigns featuring the item, such as gift guides, seasonal capsules and collaborations (list). |  |
| `season` | text |  | Show or collection season: "Fall-Winter 2026", "Spring-Summer 2026", "Pre-Fall 2026". |  |
| `product_type` | text |  | Type of item in English (sneaker, ankle boot, tote, card holder, bracelet, belt, watch strap…), for filtering. |  |
| `product_type_raw` | text |  | Type of item exactly as the brand's storefront names it, only when it differs from product_type (e.g. "knitwear" → sweater). |  |
| `audience` | text (enum) |  | Who the item is for: Women, Men, Unisex or Kids, as the brand labels it or as its menu, name or description states it. | `Women`, `Men`, `Unisex`, `Kids` |
| `audience_source` | text (enum) |  | Where the audience comes from: the brand's product data, the storefront menu or category, the item name, or the description. | `house_api`, `category`, `name`, `description` |
| `material` | text |  | Material in English; several differing values are joined by " · ". |  |
| `material_source` | text (enum) |  | Where the material comes from: the product page, the brand's material code, the line under the name, or the item name. | `page`, `page_field`, `house_api`, `several_sources`, `subtitle`, `name` |
| `material_all` | text[] — JSON array of strings |  | All material values as published, by source (for reference; API only). |  |
| `composition` | text[] — JSON array of strings |  | Fibre composition as a list of {fiber, pct}, e.g. from "57% Wool, 25% Cashmere…". |  |
| `composition_secondary` | text |  | Secondary materials: "Lining: 100% Polyamide · Other: Lamb" (lining, inserts, other). |  |
| `material_local` | text |  | Material in the language of the local storefront (only when the text is not English). |  |
| `material_line` | text |  | The brand's named material line (a signature canvas or leather), only when the item is made of it: a print of the line's motif on cotton is not the line. |  |
| `color` | text |  | Colour in English. |  |
| `color_all` | text[] — JSON array of strings |  | All differing colour values as published (for reference). |  |
| `color_group` | text (enum) |  | Colour group for the filter, one of 16 values (Black, White, Brown, Beige, Grey, Blue, Green, Red, Pink, Purple, Yellow, Orange, Gold, Silver, Multicolor, Natural). | `Black`, `Blue`, `Brown`, `Beige`, `White`, `Grey`, `Pink`, `Gold`, `Green`, `Silver`, `Red`, `Orange`, `Yellow`, `Multicolor`, `Natural`, `Purple` |
| `color_groups` | text[] — JSON array of strings |  | All colour groups of a two-tone item ("Black / White" → [Black, White]); the item is found under each. |  |
| `color_group_lv` | text (enum) |  | The brand's own colour group, mapped to the same 16 groups (Preto / 블랙 / ブラック → Black); shown next to color_group on the card, while the filter uses color_group. | `Black`, `Blue`, `Brown`, `Beige`, `White`, `Grey`, `Pink`, `Gold`, `Green`, `Silver`, `Red`, `Orange`, `Yellow`, `Multicolor`, `Natural`, `Purple` |
| `color_group_differs` | bool |  | True when color_group and the brand's own colour group (color_group_lv) are both present and differ (e.g. White against the brand's Beige); false otherwise, including when one of them is empty. |  |
| `customizable` | bool |  | The item can be personalised; no colour applies. |  |
| `color_local` | text |  | Shade in the language of the local storefront (only when the text is not English). |  |
| `made_in` | text |  | Country or countries of manufacture in English, e.g. "Italy" or "France · Spain · Italy". |  |
| `made_in_countries` | text[] — JSON array of strings |  | Countries of manufacture as ISO 3166 codes (list, same order as made_in) — a filter. |  |
| `made_in_all` | text[] — JSON array of strings |  | For reference: [countries from the storefront's made-in field, countries from the description], in English. |  |
| `made_in_multi_country` | bool |  | True when more than one country of manufacture is stated. |  |
| `made_in_raw` | text |  | The country-of-manufacture phrase exactly as published on the storefront. |  |
| `description` | text |  | Marketing description in the brand's words; sizes, dimensions, care and "Made in" are in their own fields. |  |
| `description_short` | text |  | The brand's short blurb — the opening text of the card; in lists it stands in for the description. |  |
| `description_short_redundant` | bool |  | True when the description contains the whole short blurb (then it is not shown separately). |  |
| `description_local` | text |  | Description in the language of the local storefront. |  |
| `description_en_source` | text (enum) |  | Where the English description comes from: the item's own page, the English page of the same model (the colour may differ), or an earlier week. | `own`, `same_model`, `carried` |
| `text_source_snapshot` | ISO week |  | Week the English text is from, when it is older than this week: the latest page had no English, so description, features and care come from that week. |  |
| `carried_fields` | text[] — JSON array of strings |  | Text fields taken from an earlier week: description · features · care. |  |
| `description_en_from` | text |  | Article whose English page the description comes from. |  |
| `dimensions_raw` | text |  | Dimensions as published on the storefront ("29 x 17.5 x 10 cm", "33.5 x 45.3 x 23.6 inches"). |  |
| `dimensions_unit_raw` | text |  | Unit of the published dimensions (cm, inches, mm). |  |
| `dim_axes` | text |  | Labels of the dimensions, e.g. L×W or D×H. |  |
| `dim_length_cm` | numeric | cm | Length in centimetres (converted when published in inches or millimetres). |  |
| `dim_height_cm` | numeric | cm | Height in centimetres. |  |
| `dim_width_cm` | numeric | cm | Width or depth in centimetres; for round items the diameter. |  |
| `dim_length_in` | numeric | in | Length in inches (centimetres / 2.54). |  |
| `dim_height_in` | numeric | in | Height in inches. |  |
| `dim_width_in` | numeric | in | Width in inches. |  |
| `names_by_lang` | json (JSON object) |  | The brand's own name for the item in each storefront language, as published (ISO 639-1 → list of names); the English name is in name_en. |  |
| `dimensions_by_size` | json (JSON object) |  | Dimensions per size as the brand lists them in the description (trunks and luggage, books, sets), e.g. {"50": "50 x 18 x 37 cm"}. |  |
| `heel_height_cm` | numeric | cm | Heel height in centimetres ("Heel, 4.5cm/1.8 inch"). |  |
| `platform_height_cm` | numeric | cm | Platform or sole height in centimetres. |  |
| `belt_width_mm` | numeric | mm | Belt width in millimetres, from the name ("40mm Reversible Belt"). |  |
| `case_diameter_mm` | numeric | mm | Watch case diameter in millimetres, from the name (e.g. "…, 44mm, steel"). |  |
| `weight_kg` | numeric | kg | Weight in kilograms. |  |
| `diamond_count` | int |  | Number of diamonds (other stones are not counted). |  |
| `diamond_carat_total` | numeric | ct | Total diamond weight in carats, the centre stone included when it is a diamond; other stones are not included. |  |
| `diamond_color_grade` | text |  | Diamond colour grade (GIA), e.g. "D to G". |  |
| `metal_fineness` | int |  | Metal fineness: 750 (18 kt), 925 (silver), 950 (platinum). |  |
| `gold_karat` | int | kt | Gold purity in carats (e.g. 18), only when gold is the main material (not a buckle or hands). |  |
| `gold_fineness` | int |  | Gold fineness (750). |  |
| `is_platinum` | bool |  | True when platinum is the material. |  |
| `specs_raw` | json (JSON object) |  | The page's specifications as published (JSON), API only. |  |
| `unparsed` | text[] — JSON array of strings |  | Additional details in the brand's own wording, as "label: value" lines. |  |
| `features` | text[] — JSON array of strings |  | Features in the brand's own words, one per line, as listed on the product page (materials, hardware, closures, pockets, fit); the marketing text is in description. |  |
| `care` | text[] — JSON array of strings |  | Care instructions supplied by the house, when available. |  |
| `features_local` | text[] — JSON array of strings |  | Features in the language of the local storefront, when they are not in English; features is then empty and features_lang names the language. |  |
| `care_local` | text[] — JSON array of strings |  | Care lines in the language of the local storefront that have no English version; care holds the English lines. |  |
| `features_lang` | text (ISO 639-1) |  | Language of the features and care text. |  |
| `sustainability` | text[] — JSON array of strings |  | Responsible-sourcing notes from the brand's sustainability section (Leather Working Group tanneries, Responsible Jewellery Council, Kimberley Process, origin). |  |
| `features_source` | text (enum) |  | Origin of the feature list. | `page`, `house_api`, `same_model`, `carried` |
| `size_run` | text[] — JSON array of strings |  | Sizes listed on the item page, labels as sold, for items whose sizes are not in size_variant. |  |
| `size_run_region` | text (storefront code) |  | Storefront the size list comes from (its country's size scale applies). |  |
| `size_scale` | text (enum) |  | Size scale of the item: EU · US · UK · cm · inches · alpha · ring · ml · months · years · one_size · numeric · other. | `EU`, `US`, `UK`, `US/UK`, `inches`, `cm`, `alpha`, `ring`, `ml`, `months`, `years`, `one_size`, `numeric`, `other` |
| `lv_url` | text (URL) |  | Link to the item on the brand's site: an English storefront where the page is live, otherwise a local one; see lv_url_status and page_checked_snapshot. |  |
| `page_checked_snapshot` | ISO week |  | Week the link was last checked. |  |
| `lv_url_status` | text (enum) |  | Link status: alive — live this week · repointed — points to another storefront where the page is live · gone_all — not found on any storefront at the latest check · unverified — not confirmed live this week · none — no link known. | `alive`, `repointed`, `gone_all`, `unverified`, `none` |
| `lv_url_region` | text (storefront code) |  | Storefront the link points to. |  |
| `record_completeness` | text (enum) |  | How much item detail is available. | `full`, `partial`, `catalog_only`, `thin` |
| `family_alias_of` | text |  | Main article of the same product, listed by the brand under another code on another model page. |  |
| `duplicate_of` | text |  | Main article, when this record is a second listing of the same product under another code. |  |

## Coverage and status

Table: `product_stats`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `status` | text (enum) |  | Listing status: in_catalog, e1_only or gone. Delisted does not mean discontinued. | `in_catalog`, `e1_only`, `gone` |
| `status_as_of` | ISO week |  | Last week the item was seen; for delisted items, the week it was last seen ("delisted as of"). |  |
| `regions_present` | int |  | Number of storefronts with a recorded listing. |  |
| `regions_observed` | int |  | Number of storefronts where listing was observed. |  |
| `regions_declared` | int |  | Number of storefronts reported by the house. |  |
| `weeks_unlisted` | int |  | Consecutive weeks without a listing or price. |  |
| `regions_with_price` | int |  | Number of storefronts with a current price (0 = no prices). |  |
| `price_usd_ref` | numeric | USD | USD price for lists: the median of current prices across countries (two storefronts of one country count once). |  |
| `price_ref_countries` | int |  | Number of countries with a current price (the USD price is the median across them). |  |
| `price_ref_single_market` | bool |  | True when the price is known in one country only: the USD price is that storefront's price, not a median across markets. |  |
| `price_ref_country` | text (ISO 3166-1 alpha-2) |  | ISO code of that single country when price_ref_single_market is true; otherwise empty. |  |
| `countries_present` | int |  | Number of countries with a recorded listing. |  |
| `countries_observed` | int |  | Number of countries where listing was observed. |  |
| `countries_declared` | int |  | Number of countries reported by the house. |  |
| `countries_with_price` | int |  | Number of countries with a current price (same as price_ref_countries). |  |
| `last_price_countries` | int |  | Number of countries with a price in the last week with a price (goes with price_usd_last). |  |
| `price_usd_fr` | numeric | USD | Price on the French storefront in USD (EU price incl. VAT 20%). |  |
| `price_usd_us` | numeric | USD | Price on the US storefront in USD (excl. sales tax). |  |
| `price_usd_min` | numeric | USD | Lowest price across storefronts in USD (on the card). |  |
| `price_usd_max` | numeric | USD | Highest price across storefronts in USD (on the card). |  |
| `weeks_of_history` | int | week | Number of weeks with a price on at least one storefront. |  |
| `price_events` | int |  | Number of weeks in which the price changed on at least one storefront. |  |
| `first_seen` | ISO week |  | First week the item was seen: listed on a storefront, live at its address, priced, or on a product page. |  |
| `last_seen` | ISO week |  | Last week the item was seen (see Status names). |  |
| `price_usd_last` | numeric | USD | Last known USD price: the median across countries in the last week with a price; equals price_usd_ref for items with a price this week. |  |
| `last_price_snapshot` | ISO week |  | Week of the last known price. |  |
| `last_price_regions` | int |  | Number of storefronts with a price in that week. |  |
| `sellable_anywhere` | bool |  | True when at least one storefront showing the item this week offers it for online purchase. |  |
| `regions_present_ex_e1` | int |  | Number of country storefronts that showed the item (see Status names), not counting the international storefront. |  |
| `photos_ever` | int |  | How many photos the gallery has ever had, including photos the brand later removed (see image.last_seen). |  |
| `photos` | int |  | Number of photos in the current gallery, as shown on the brand's page. |  |
| `photos_additional` | int |  | Number of further photos of the item that the brand has but does not show on its page; not included in photos. |  |
| `videos` | int |  | Number of distinct videos. |  |
| `audience` | text (enum) |  | Who the item is for: Women, Men, Unisex or Kids, as the brand labels it or as its menu, name or description states it. | `Women`, `Men`, `Unisex`, `Kids` |
| `variants_n` | int |  | Number of variation codes (sizes, colours or materials without a card of their own) that belong to this card (see article_variant). |  |
| `variants_countries_n` | int |  | Number of countries whose storefronts listed the variations; they count for the main card. |  |
| `variants_last_seen` | ISO week |  | Last week any variation was seen. |  |

## Departments

Table: `department`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `department` | text (enum) |  | Department code (as in product_client). | `Bags_SLG`, `RTW`, `Shoes`, `SoftAccessories`, `FineJewelry`, `FashionJewelry`, `Watches`, `Travel`, `Home`, `Eyewear`, `Fragrance`, `Beauty`, `Books`, `TechMisc`, `Equestrian`, `UNMAPPED` |
| `department_en` | text |  | Department name. |  |
| `sort_order` | int |  | Display order in navigation. |  |

## Storefronts

Table: `region`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `region` | text (storefront code) |  | Storefront code (language_country, e.g. eng_NL): the brand's site for one country and language; see the region table for the country. |  |
| `country` | text |  | Country of the storefront. |  |
| `language` | text (ISO 639-1) |  | Language of the storefront (ISO 639). |  |
| `currency` | text |  | Currency of the storefront (ISO 4217). |  |
| `is_international` | bool |  | True for an international storefront without a country (no prices). |  |
| `price_includes_tax` | bool |  | True when storefront prices include tax (VAT/GST): EU, UK, Switzerland, Australia, Japan, China, Brazil, Mexico, Korea, UAE; false for the United States, Canada and Hong Kong. |  |
| `tax_note` | text |  | Tax basis in words: "incl. VAT 20%", "excl. sales tax", "no VAT or sales tax". |  |
| `coverage` | text (enum) |  | Coverage of the storefront's data for the week: full or partial. | `full`, `partial` |

## Specifications

Table: `product_spec`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `spec_key` | text |  | Specification key (English, e.g. strap_drop_cm, lining, w_power_reserve_h); see Specification keys. |  |
| `spec_value` | text |  | Value in the unit of the key (see Specification keys); local-language text is given in English where possible. |  |

## Sizes and colours

Table: `size_variant`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `sku` | text |  | SKU of the size or colour variant. |  |
| `article` | text |  | Article the variant belongs to. |  |
| `family_id` | text |  | Model: the brand's page or code that groups the colours and sizes of one model. |  |
| `size_label` | text |  | Size label as sold: "7.5", "38", "90 cm", "One size". |  |
| `size_label_raw` | text |  | Label exactly as in the brand's data ("07.5", "S0", "NSA"). |  |
| `variant_kind` | text (enum) |  | What varies: size · color (colour only) · one_size · volume (ml) · age (months). | `size`, `color`, `one_size`, `volume`, `age` |
| `size_order` | numeric |  | Display order within the size run. |  |
| `size_scale` | text (enum) |  | Size scale of the run: EU · US · UK · cm · inches · alpha · ring · ml · months · years · one_size · numeric · other. | `EU`, `US`, `UK`, `US/UK`, `inches`, `cm`, `alpha`, `ring`, `ml`, `months`, `years`, `one_size`, `numeric`, `other` |
| `scope` | text (enum) |  | article — a variant of this article · family — another colour of the same model; the exact article is not known. | `article`, `family` |
| `source_article` | text |  | Article whose page the variant comes from (for reference). |  |
| `region` | text (storefront code) |  | Storefront of the size; its country's size scale applies (see the region table). |  |
| `color` | text |  | Variant colour in English where available (Noir / Preto → Black); shade names without a translation keep the brand's wording. |  |
| `color_raw` | text |  | Variant colour exactly as on the storefront (for reference). |  |
| `price` | numeric |  | Variant price in the storefront currency when it was seen. |  |
| `currency` | text |  | Currency of the storefront (ISO 4217). |  |
| `sellable` | bool |  | In stock on that storefront this week; never true on the international storefront. |  |
| `observed_at` | timestamp (UTC) |  | When this row was seen (UTC). |  |
| `lv_url` | text (URL) |  | Link to the variant on the brand's site. |  |
| `image_url` | text (URL) |  | Link to the variant photo on the brand's server, for reference only; the brand may change or remove it. |  |

## Item variations

Table: `article_variant`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `variant_article` | text |  | Variation code: an article of the brand that has no card of its own (a size, colour or material of the main article). |  |
| `article` | text |  | Main article (the card this variation belongs to): "code X is the size-46 variation of Y". |  |
| `family_id` | text |  | Model page of the variation (see family_id in product_client). |  |
| `kind` | text (enum) |  | What varies: a size, a colour or finish, a metal or stone, or a part of a belt set. | `size`, `colour`, `material`, `leather`, `buckle`, `finish`, `unknown` |
| `size_label` | text |  | Size label of the variation as sold (as in size_variant). |  |
| `color` | text |  | Colour of the variation in English: for a size, the colour of the main card; for a colour, its own shade. |  |
| `color_raw` | text |  | Colour of the variation exactly as on the storefront (for reference). |  |
| `link_source` | text (enum) |  | How the variation is linked to the card: a size or colour row of a card of the same model, the same model page, or the colour choice on a product page. | `sku`, `family`, `variant_page` |
| `regions` | text[] — JSON array of strings |  | Storefronts (region codes) that listed the variation. |  |
| `regions_n` | int |  | Number of such storefronts. |  |
| `first_seen` | ISO week |  | First week a storefront listed the variation. |  |
| `last_seen` | ISO week |  | Last week the variation was listed or its page was live. |  |
| `registry_status` | text (enum) |  | Status of the variation's pages at the latest check: alive — at least one was live · gone — none was live · unverified — not checked yet. | `alive`, `gone`, `unverified` |
| `lv_url` | text (URL) |  | Link to the variation page on the brand's site (an English storefront is preferred). |  |
| `sellable_anywhere` | bool |  | True if a storefront showed the variation in stock this week (see size_variant). |  |

## Current prices

Table: `price_current`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `region` | text (storefront code) |  | Storefront code (language_country, e.g. eng_NL): the brand's site for one country and language; see the region table for the country. |  |
| `currency` | text |  | Currency of the storefront (ISO 4217). |  |
| `price` | numeric |  | Price as published on the storefront (decimal; JPY and KRW without fraction), only when price_state = current. |  |
| `price_usd` | numeric | USD | Price in USD at the week's rate (the last ECB rate before the week); empty when price_state is not current (see last_price_usd). |  |
| `price_eur` | numeric | EUR | Price in EUR at the week's rate; empty when price_state is not current. |  |
| `availability` | text (enum) |  | Availability on the storefront: sellable · no · backorder · InStoreOnly · not_sold_online · empty (not reported by the storefront). | `sellable`, `no`, `backorder`, `InStoreOnly`, `not_sold_online`, `not_in_region`, `` |
| `observed_at` | timestamp (UTC) |  | When the observation was made (UTC). |  |
| `snapshot_id` | ISO week |  | Week of the observations (ISO week), e.g. 2026-W36. |  |
| `is_latest_run` | bool |  | true — the price is current (price_state = current); false — no current price: price is empty, price_state says why, and the last known price is in last_price*. |  |
| `price_state` | text (enum) |  | Whether the price is current, no longer shown, or awaiting an update. | `current`, `withdrawn`, `not_checked` |
| `last_checked_week` | ISO week |  | Last week this storefront was checked for the item (with or without a price). |  |
| `last_price` | numeric |  | Last known price on this storefront, given when price_state is not current (the price fields are then empty). |  |
| `last_price_currency` | text |  | Currency of the last known price (the storefront currency). |  |
| `last_price_usd` | numeric | USD | Last known price in USD at the rate of its own week. |  |
| `last_price_snapshot` | ISO week |  | Week of the last known price (equals snapshot_id of this row). |  |

## Price history

Table: `price_observation`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `region` | text (storefront code) |  | Storefront code (language_country, e.g. eng_NL): the brand's site for one country and language; see the region table for the country. |  |
| `snapshot_id` | ISO week |  | Week of the observation. |  |
| `currency` | text |  | Currency of the storefront (ISO 4217). |  |
| `price` | numeric |  | Price as published on the storefront. |  |
| `price_usd` | numeric | USD | Price in USD at the week's rate. |  |
| `availability` | text (enum) |  | Availability on the storefront (see price_current). | `sellable`, `no`, `backorder`, `InStoreOnly`, `not_sold_online`, `not_in_region`, `` |
| `source` | text (enum) |  | Where the price was read: the product page, a listing page, the brand's price list, or the China storefront page. | `product_page`, `listing_page`, `house_price_list`, `` |
| `observed_at` | timestamp (UTC) |  | When the observation was made (UTC). |  |

## Listing history

Table: `presence_observation`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `region` | text (storefront code) |  | Storefront code (language_country, e.g. eng_NL): the brand's site for one country and language; see the region table for the country. |  |
| `source` | text (enum) |  | Where the listing was seen: the storefront's site map, the item page, a listing page, or the brand's own data and links. | `rechecked`, `checked_gone`, `house_api`, `sitemap`, `carried`, `model_link`, `product_page`, `listing_page` |
| `snapshot_id` | ISO week |  | Week of the observations (ISO week), e.g. 2026-W36. |  |
| `present` | bool |  | True = listed on the storefront, false = not listed. |  |
| `observed_at` | timestamp (UTC) |  | When the observation was made (UTC). |  |

## Current listings

Table: `presence_current`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `region` | text (storefront code) |  | Storefront code (language_country, e.g. eng_NL): the brand's site for one country and language; see the region table for the country. |  |
| `present` | bool |  | Latest known state; a live page counts over a listing. |  |
| `basis` | text (enum) |  | What the listing rests on: observed — we saw the item on this storefront (item page, site map, listing or price) · declared — only linked by the brand from another storefront; not seen there. | `observed`, `declared` |
| `counted` | bool |  | True when this storefront counts in the item's storefront numbers: present, and seen recently enough (this week, unless stated below). |  |
| `first_seen` | ISO week |  | First week the item was listed on this storefront. |  |
| `last_seen` | ISO week |  | Last week the item was listed on this storefront. |  |
| `snapshot_id` | ISO week |  | Week of the latest observation. |  |
| `is_latest_run` | bool |  | True if the observation is from this week. |  |

## Item links

Table: `region_url`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Article (the brand's reference code). |  |
| `region` | text (storefront code) |  | Storefront code (as in price_current and region). |  |
| `source_url` | text (URL) |  | Link to the item page on this storefront; the brand may change or remove it. |  |
| `url_status` | text (enum) |  | alive — the page was at this address this week · gone — no page at the latest check · unknown — not checked this week; show the link only for alive. | `alive`, `gone`, `unknown` |
| `checked_week` | ISO week |  | Week the address was last checked (show as "checked in week …"). |  |
| `first_seen` | ISO week |  | First week the address was seen. |  |
| `last_seen` | ISO week |  | Last week the address was seen or live. |  |

## Photos

Table: `image`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `seq` | int |  | Order of the view; 1 = the main photo. |  |
| `view` | text |  | View as the brand names it, e.g. Front view · Side view · Interior view · Worn view · Back view · Detail view. |  |
| `media_ref` | text |  | A stable identifier of the image; the same image keeps it across exports. |  |
| `width` | int | px | Width of the original photo in pixels. |  |
| `height` | int | px | Height of the original photo in pixels. |  |
| `has_alpha` | bool |  | Whether the original has a transparent background (true for PNG with transparency). |  |
| `bytes` | int |  | Size of the original file in bytes. |  |
| `is_capped` | bool |  | True when the stored original is the largest image the brand provides and it is below full resolution. |  |
| `frame_source` | text (enum) |  | Where the photo comes from: shown on the storefront page, the brand's own photo not shown on its page (not counted in photos), or kept from an earlier week. | `page`, `additional_photo`, `carried`, `` |
| `first_seen` | ISO week |  | First week the photo was in the gallery (photos from before 2026-W24 are dated 2026-W24). |  |
| `last_seen` | ISO week |  | Last week the photo was in the gallery. |  |

## Videos

Table: `video`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Item reference code, used together with the house identifier. |  |
| `seq` | int |  | Order of the clip on the item page (1 = first). |  |
| `media_ref` | text |  | A stable identifier of the clip; the same clip keeps it across exports. |  |
| `bytes` | int |  | File size in bytes. |  |
| `mime` | text |  | File type (video/mp4). |  |
| `duration_s` | numeric | s | Duration in seconds. |  |
| `width` | int | px | Frame width in pixels. |  |
| `height` | int | px | Frame height in pixels. |  |
| `source_url` | text |  | The clip's address on the brand's server, for reference only. |  |
| `first_seen` | ISO week |  | First week the clip was attached to the item. |  |
| `last_seen` | ISO week |  | Last week the clip was listed for the item. |  |

## Currency conversion

Table: `fx_rate`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `snapshot_id` | ISO week |  | Week of the observations (ISO week), e.g. 2026-W36. |  |
| `currency` | text |  | Currency of the storefront (ISO 4217). |  |
| `units_per_usd` | numeric |  | Units of the currency per 1 USD in the week (JPY 156.25): price_usd = price / units_per_usd. |  |
| `units_per_eur` | numeric |  | Units of the currency per 1 EUR (from the same rates): price_eur = price / units_per_eur. |  |
| `source` | text |  | Reference used for the currency conversion rate. |  |
| `as_of` | timestamp (UTC) |  | When the rate was recorded (UTC). |  |

## Weekly releases

Table: `snapshot`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `snapshot_id` | ISO week |  | ISO week of the observations. |  |
| `started_at` | timestamp (UTC) |  | When observations for the week started. |  |
| `finished_at` | timestamp (UTC) |  | When observations for the week finished. |  |
| `health_status` | text |  | Completeness of the week's data: ok — complete · suspect — looks incomplete (for example far fewer items than usual). |  |

## Public demo selection

Table: `demo_set`.

| Field | Type | Unit | Meaning | Allowed values |
|---|---|---|---|---|
| `brand` | text (enum) |  | House identifier. | `lv`, `dior`, `loewe`, `tiffany`, `kenzo`, `givenchy`, `hermes` |
| `brand_name_en` | text |  | Brand name in English for the brand code (Louis Vuitton, Dior, Hermès, …). |  |
| `article` | text |  | Article of the brand's demo set. |  |
| `roles` | text[] — JSON array of strings |  | Properties the item demonstrates: price_event · gone · maturing (Not listed this week, with a last known price) · price_spread · e1_only · video · family_size · alnum_code (letters and digits in the code) · price_ladder_top (top of the price range). |  |
| `status` | text (enum) |  | Status this week (see Status names). | `in_catalog`, `e1_only`, `gone` |
| `price_events` | int |  | Price changes in the history. |  |
| `price_spread_ratio` | numeric |  | Highest to lowest USD price across storefronts. |  |
| `videos` | int |  | Videos. |  |
| `family_size` | int |  | Articles on the same model page. |  |
| `checks_ok` | bool |  | True when the item still shows every property it was chosen for this week. |  |
| `checks_failed` | text[] — JSON array of strings |  | Properties this item no longer demonstrates. |  |

## Specification fields

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `a_depth_cm` | numeric | cm | Depth (accessory) |
| `a_diameter_cm` | numeric | cm | Diameter (accessory) |
| `a_height_cm` | numeric | cm | Height (accessory) |
| `a_width_cm` | numeric | cm | Width (accessory) |
| `adjustable` | bool |  | Adjustable |
| `ageing` | text |  | Ageing |
| `b_ingredients` | text |  | Ingredients (beauty) |
| `battery_life` | text |  | Battery life |
| `binding` | enum |  | Binding |
| `book_author` | text |  | Author |
| `book_illustrator` | text |  | Illustrator |
| `book_pages` | numeric |  | Pages |
| `book_photographer` | text |  | Photographer |
| `bracelet_length_cm` | numeric | cm | Bracelet length |
| `bracelet_length_max_cm` | numeric | cm | Bracelet length (max) |
| `buckle` | text |  | Buckle |
| `buckle_height_cm` | numeric | cm | Buckle height |
| `buckle_raw` | text |  | Buckle (as written) |
| `buckle_type` | enum |  | Buckle type |
| `buckle_width_cm` | numeric | cm | Buckle width |
| `burn_time_h` | numeric | h | Burn time |
| `capacity` | text |  | Max. capacity |
| `capacity_max_kg` | numeric | kg | Max. load |
| `card_slots` | numeric |  | Card slots |
| `carry_style` | text |  | Carry style |
| `case_width_mm` | numeric | mm | Case width |
| `chain` | text |  | Chain |
| `chain_drop_cm` | numeric | cm | Chain drop |
| `chain_drop_max_cm` | numeric | cm | Chain drop (max) |
| `chain_length_cm` | numeric | cm | Chain length |
| `charging_time` | text |  | Charging time |
| `cites_restricted` | bool |  | CITES-restricted material |
| `closure` | text |  | Closure |
| `closure_type` | enum |  | Closure type |
| `collar_neckline` | text |  | Collar / neckline |
| `composition_pct` | text | % | Composition |
| `construction` | text |  | Construction |
| `crystal` | enum |  | Crystal |
| `designer` | text |  | Designer |
| `diamond_center_carat` | numeric | ct | Center stone |
| `dishwasher_safe` | bool |  | Dishwasher safe |
| `domestic_table_size` | text |  | Table size |
| `e_bridge_mm` | numeric | mm | Bridge |
| `e_filter` | numeric |  | Lens filter category |
| `e_lens_width_mm` | numeric | mm | Lens width |
| `e_temple_mm` | numeric | mm | Temple length |
| `e_uv_pct` | numeric | % | UV protection |
| `e_vlt_pct` | numeric | % | Visible light transmission |
| `each_module` | text |  | Each module |
| `edge_finish` | enum |  | Edge finish |
| `engravable` | bool |  | Can be engraved |
| `engraving_available` | bool |  | Engraving available |
| `f_ingredients` | text |  | Ingredients |
| `f_key_notes` | text |  | Key notes (listing) |
| `finish` | text |  | Finish |
| `fit` | enum |  | Fit |
| `fits` | text |  | Fits |
| `fj_height_mm` | numeric | mm | Height |
| `fj_length_mm` | numeric | mm | Length (fashion jewellery) |
| `fj_weight_g` | numeric | g | Weight (fashion jewellery) |
| `fj_width_mm` | numeric | mm | Width (fashion jewellery) |
| `fragrance_formats` | text |  | Formats |
| `fragrance_key_notes` | text |  | Key notes |
| `gold_karat_spec` | numeric | kt | Gold |
| `hand_stitched_vamp` | bool |  | Hand-stitched vamp |
| `handle` | text |  | Handle |
| `handle_drop_cm` | numeric | cm | Handle drop |
| `handle_drop_max_cm` | numeric | cm | Handle drop (max) |
| `hardware_color` | text |  | Hardware colour |
| `hardware_finish` | enum |  | Hardware finish |
| `heel_cm` | numeric | cm | Heel height |
| `home_depth_cm` | numeric | cm | Depth |
| `home_diameter_cm` | numeric | cm | Diameter |
| `home_height_cm` | numeric | cm | Height |
| `home_width_cm` | numeric | cm | Width |
| `illustrations` | text |  | Illustrations |
| `insole` | text |  | Insole |
| `is_refill` | bool |  | Refill |
| `j_band_width_mm` | numeric | mm | Band width |
| `j_center_stone_color` | text |  | Centre stone colour |
| `j_chain_length_cm` | numeric | cm | Chain length (jewellery) |
| `j_clarity` | text |  | Clarity |
| `j_clarity_range` | text |  | Centre stone clarity range |
| `j_color_range` | text |  | Centre stone colour range |
| `j_diameter_mm` | numeric | mm | Diameter |
| `j_height_mm` | numeric | mm | Height (jewellery) |
| `j_length_mm` | numeric | mm | Length (jewellery) |
| `j_setting_size_mm` | numeric | mm | Setting size |
| `j_width_mm` | numeric | mm | Width (jewellery) |
| `key_ingredients` | text |  | Key ingredients |
| `language_edition` | text |  | Language edition |
| `length_cm` | numeric | cm | Length |
| `limited_edition` | text |  | Limited edition |
| `lining` | text |  | Lining |
| `lining_material` | text |  | Lining material |
| `lug_to_lug_mm` | numeric | mm | Lug to lug |
| `max_load` | text |  | Maximum load |
| `metal_fineness_spec` | numeric | ‰ | Metal fineness |
| `metal_type` | enum |  | Metal |
| `microwave_safe` | bool |  | Microwave safe |
| `min_order_qty` | numeric |  | Minimum order quantity |
| `model_size` | text |  | Model wears size |
| `model_wrist_cm` | numeric | cm | Model's wrist size |
| `model_wrist_female_cm` | numeric | cm | Female model's wrist size |
| `motif_size_mm` | numeric | mm | Motif size |
| `numbered_edition` | text |  | Numbered edition |
| `origin_assembly` | text |  | Origin: assembly |
| `origin_confection` | text |  | Origin: confection |
| `origin_dye` | text |  | Origin: dyeing |
| `origin_finishing` | text |  | Origin: finishing |
| `origin_print` | text |  | Origin: printing |
| `origin_stitching` | text |  | Origin: stitching |
| `origin_weaving` | text |  | Origin: weaving |
| `pockets` | text |  | Pockets |
| `print_technique` | enum |  | Print technique |
| `printed_in` | text |  | Printed in |
| `purchase_limit` | numeric |  | Purchase limit per customer |
| `r_lining` | text |  | Lining (garment) |
| `r_main_material` | text |  | Main material |
| `r_model_measurements` | text |  | Model measurements |
| `r_other_materials` | text |  | Other materials |
| `r_ref` | text |  | Reference |
| `refillable` | bool |  | Refillable |
| `reversible` | bool |  | Reversible |
| `seat_height_cm` | numeric | cm | Seat height |
| `shade_code` | text |  | Shade code |
| `shoe_closure` | enum |  | Closure (shoes) |
| `sole` | text |  | Sole |
| `sole_material` | enum |  | Sole material |
| `sole_material_raw` | text |  | Sole (as written) |
| `spec_reference_size` | numeric |  | Specifications given for size |
| `stone_carat_total` | numeric | ct | Stone weight (non-diamond, total) |
| `stones` | text |  | Stones |
| `strap` | text |  | Strap |
| `strap_adjustable` | bool |  | Strap adjustable |
| `strap_drop_cm` | numeric | cm | Strap drop |
| `strap_drop_max_cm` | numeric | cm | Strap drop (max) |
| `strap_interchangeable` | bool |  | Interchangeable strap |
| `strap_length_cm` | numeric | cm | Strap length |
| `strap_length_max_cm` | numeric | cm | Strap length (max) |
| `strap_removable` | bool |  | Strap removable |
| `strap_width_mm` | numeric | mm | Strap width |
| `structure` | text |  | Structure |
| `top_handle_length_cm` | numeric | cm | Top handle length |
| `trim` | text |  | Trim |
| `trim_material` | text |  | Trim material |
| `upholstery` | text |  | Upholstery |
| `volume_l` | numeric | l | Volume |
| `volume_ml` | numeric | ml | Volume |
| `w_caliber` | text |  | Caliber |
| `w_case_diameter_mm` | numeric | mm | Case diameter |
| `w_frequency_vph` | numeric | vph | Frequency |
| `w_functions` | text |  | Functions |
| `w_jewels` | numeric |  | Jewels |
| `w_material` | text |  | Case material |
| `w_movement` | text |  | Movement |
| `w_movement_diameter_mm` | numeric | mm | Movement diameter |
| `w_oscillating_weight` | text |  | Oscillating weight |
| `w_power_reserve_h` | numeric | h | Power reserve |
| `w_thickness_mm` | numeric | mm | Case thickness |
| `w_water_resistance_m` | numeric | m | Water resistance (watch) |
| `water_resistance_m` | numeric | m | Water resistance |
| `wear_claims` | text |  | Wear claims (Louis Vuitton instrumental tests) |
| `weight_g` | numeric | g | Weight |
| `wrap_count` | numeric |  | Wraps around the wrist |
