"""LuxDB API models and operations: generated; do not edit."""
# Public spec SHA256: 09edbc37fc1f7a36ae4f0f8b143479781799008a2e3e468eed97a7ab080ea818
from __future__ import annotations

import re
from typing import Any, Literal, TypedDict, cast
from urllib.parse import quote

API_BASE_URL = 'https://luxdb.net/api/v1'
ERROR_CODES = frozenset(['unauthorized', 'plan', 'payment_required', 'rate_limited', 'search_cap', 'account_paused', 'account_closed', 'member_limit_reached', 'not_found', 'method_not_allowed', 'bad_request', 'api_disabled', 'maintenance', 'internal_error'])
ERROR_MODES = frozenset(['maintenance', 'stopped'])
UNSUPPORTED_REQUEST_HEADERS = {'/index': ('If-None-Match',)}


class _EnvelopeRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None

class Envelope(_EnvelopeRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool


class _ErrorRequired(TypedDict):
    error: str
    code: Literal['unauthorized', 'plan', 'payment_required', 'rate_limited', 'search_cap', 'account_paused', 'account_closed', 'member_limit_reached', 'not_found', 'method_not_allowed', 'bad_request', 'api_disabled', 'maintenance', 'internal_error']

class Error(_ErrorRequired, total=False):
    mode: Literal['maintenance', 'stopped']
    scope: Literal['member']
    member_limit: int
    member_used: int
    resets_at: str
    retry_after_seconds: int
    hint: str
    batch_max: int
    brands: list[str]
    plan: str
    sandbox: bool
    remaining_today: int


class _FamilyArticlesItemRequired(TypedDict):
    article: str
    name: str | None
    color: str | None
    status: str | None
    size_scale: str | None

class FamilyArticlesItem(_FamilyArticlesItemRequired, total=False):
    pass


class _FamilyRequired(TypedDict):
    family_id: str
    articles: list[FamilyArticlesItem]

class Family(_FamilyRequired, total=False):
    pass


class _ResolvedCase1Required(TypedDict):
    status: Literal['product']
    article: str
    region: str | None
    lv_url_status: str | None

class ResolvedCase1(_ResolvedCase1Required, total=False):
    pass


class _ResolvedCase2Required(TypedDict):
    status: Literal['family']
    family_id: str
    articles: list[str]
    region: str | None

class ResolvedCase2(_ResolvedCase2Required, total=False):
    pass


class _ResolvedCase3Required(TypedDict):
    status: Literal['variant']
    key: str
    variant_of: str | None
    variant_kind: str | None
    label: str | None
    region: str | None

class ResolvedCase3(_ResolvedCase3Required, total=False):
    pass


class _ResolvedCase4Required(TypedDict):
    status: Literal['not_in_catalog']
    key: str
    region: str | None

class ResolvedCase4(_ResolvedCase4Required, total=False):
    pass


class _ResolvedCase5Required(TypedDict):
    status: Literal['unrecognized_url']

class ResolvedCase5(_ResolvedCase5Required, total=False):
    pass


Resolved = ResolvedCase1 | ResolvedCase2 | ResolvedCase3 | ResolvedCase4 | ResolvedCase5


class _ArticleRequestedRequired(TypedDict):
    code: str
    article: str | None
    size_label: str | None
    alias_kind: str | None

class ArticleRequested(_ArticleRequestedRequired, total=False):
    pass


class _ArticleDimensionsRequired(TypedDict):
    pass

class ArticleDimensions(_ArticleDimensionsRequired, total=False):
    raw: str | None
    unit_raw: str | None
    axes: str | None
    length_cm: float | None
    height_cm: float | None
    width_cm: float | None
    length_in: float | None
    height_in: float | None
    width_in: float | None


class _ArticleSizeSetItemRegionsItemRequired(TypedDict):
    region: str
    availability: str | None
    priced: bool | None

class ArticleSizeSetItemRegionsItem(_ArticleSizeSetItemRegionsItemRequired, total=False):
    pass


class _ArticleSizeSetItemRequired(TypedDict):
    code: str | None
    size_label: str | None
    size_scale: str | None
    size_order: float | None
    display_label: str | None
    self: bool
    regions: list[ArticleSizeSetItemRegionsItem]

class ArticleSizeSetItem(_ArticleSizeSetItemRequired, total=False):
    pass


class _ArticlePriceByStorefrontItemRequired(TypedDict):
    pass

class ArticlePriceByStorefrontItem(_ArticlePriceByStorefrontItemRequired, total=False):
    region: str
    country: str
    language: str | None
    tax_note: str
    price_includes_tax: bool | None
    currency: str
    local: str | None
    usd: float | None
    availability: Literal['sellable', 'no', 'backorder', 'InStoreOnly', 'not_sold_online', 'not_in_region', '', None]
    observed_at: str
    snapshot_id: str
    is_current: bool
    state: Literal['current', 'withdrawn', 'not_checked']
    last_checked_week: str | None
    article: str | None
    size_display: str | None


class _ArticlePriceRequired(TypedDict):
    pass

class ArticlePrice(_ArticlePriceRequired, total=False):
    usd_ref: float | None
    usd_min: float | None
    usd_max: float | None
    usd_fr: float | None
    usd_us: float | None
    countries: int | None
    single_market: bool
    single_market_country: str | None
    last_known_usd: float | None
    last_known_snapshot: str | None
    by_storefront: list[ArticlePriceByStorefrontItem]


class _ArticleCountersRequired(TypedDict):
    pass

class ArticleCounters(_ArticleCountersRequired, total=False):
    regions_with_price: int | None
    regions_present: int
    regions_observed: int
    regions_declared: int | None
    regions_present_ex_e1: int
    countries_with_price: int | None
    countries_present: int
    countries_observed: int
    countries_declared: int | None
    weeks_of_history: int
    price_events: int
    photos: int | None
    photos_ever: int | None
    photos_additional: int | None
    videos: int | None


class _ArticleGalleryRequired(TypedDict):
    pass

class ArticleGallery(_ArticleGalleryRequired, total=False):
    photos: int | None
    videos: int | None
    links: str | None
    note: str


class _ArticleRequired(TypedDict):
    pass

class Article(_ArticleRequired, total=False):
    article: str
    requested: ArticleRequested | None
    brand: Literal['lv', 'dior', 'loewe', 'tiffany', 'kenzo', 'givenchy', 'hermes']
    brand_name_en: str
    slug: str
    name: str | None
    name_source: Literal['brand_english_page', 'dictionary', 'partial', 'model_name', 'original_language', 'brand_english']
    name_lang: str
    family_id: str
    family_alias_of: str | None
    department: Literal['Accessories', 'Bags & Small Leather Goods', 'Beauty', 'Books', 'Equestrian', 'Eyewear', 'Fashion Jewelry', 'Fine Jewelry', 'Fragrance', 'Home', 'Other', 'Ready-to-Wear', 'Shoes', 'Tech & Objects', 'Travel', 'Watches']
    category: str | None
    product_type: str | None
    collection: str | None
    season: str | None
    audience: Literal['Women', 'Men', 'Unisex', 'Kids', None]
    campaign: list[str] | None
    material: str | None
    material_line: str | None
    composition: list[dict[str, Any]] | None
    color: str | None
    color_group: Literal['Black', 'Blue', 'Brown', 'Beige', 'White', 'Grey', 'Pink', 'Gold', 'Green', 'Silver', 'Red', 'Orange', 'Yellow', 'Multicolor', 'Natural', 'Purple', None]
    made_in: str | None
    made_in_countries: list[str] | None
    customizable: bool
    dimensions: ArticleDimensions | None
    measures: dict[str, Any]
    specs_json: dict[str, Any]
    sizes: list[dict[str, Any]]
    family_sizes: list[str]
    colors: list[str]
    colors_untranslated: float
    status: Literal['in_catalog', 'e1_only', 'gone']
    status_as_of: str | None
    weeks_unlisted: int
    variants: dict[str, Any]
    size_variants: list[dict[str, Any]]
    size_set: list[ArticleSizeSetItem] | None
    variant_codes: list[dict[str, Any]]
    first_seen: str
    last_seen: str | None
    record_completeness: Literal['full', 'partial', 'catalog_only', 'thin']
    text_lang: str
    text_source_region: str
    lv_url: str
    lv_url_status: Literal['alive', 'repointed', 'gone_all', 'unverified', 'none']
    page_checked_snapshot: str | None
    storefront_urls: list[dict[str, Any]]
    description: str | None
    description_short: str | None
    description_local: str | None
    description_source: Literal['own', 'same_model', 'carried', None]
    description_short_redundant: bool | None
    name_local: str | None
    name_lv: str | None
    features: list[str] | None
    care: list[str] | None
    sustainability: list[str] | None
    unparsed: list[str] | None
    features_source: Literal['page', 'house_api', 'same_model', 'carried', None]
    description_from: str | None
    names_by_lang: dict[str, Any] | None
    carried_fields: list[str] | None
    text_source_snapshot: str | None
    color_group_lv: Literal['Black', 'Blue', 'Brown', 'Beige', 'White', 'Grey', 'Pink', 'Gold', 'Green', 'Silver', 'Red', 'Orange', 'Yellow', 'Multicolor', 'Natural', 'Purple', None]
    color_group_differs: bool
    composition_secondary: str | None
    made_in_multi_country: bool
    size_run: list[str] | None
    size_run_region: str | None
    size_scale: Literal['EU', 'US', 'UK', 'US/UK', 'inches', 'cm', 'alpha', 'ring', 'ml', 'months', 'years', 'one_size', 'numeric', 'other', 'shade', 'scent', None]
    sold_per_unit: bool
    lv_url_region: str
    last_price_countries: int | None
    last_price_regions: int | None
    sellable_anywhere: bool
    price: ArticlePrice | None
    counters: ArticleCounters
    history: list[dict[str, Any]]
    gallery: ArticleGallery


class _SearchRowRequired(TypedDict):
    pass

class SearchRow(_SearchRowRequired, total=False):
    article: str
    name: str | None
    family_id: str
    department: Literal['Accessories', 'Bags & Small Leather Goods', 'Beauty', 'Books', 'Equestrian', 'Eyewear', 'Fashion Jewelry', 'Fine Jewelry', 'Fragrance', 'Home', 'Other', 'Ready-to-Wear', 'Shoes', 'Tech & Objects', 'Travel', 'Watches']
    category: str | None
    product_type: str | None
    color_group: Literal['Black', 'Blue', 'Brown', 'Beige', 'White', 'Grey', 'Pink', 'Gold', 'Green', 'Silver', 'Red', 'Orange', 'Yellow', 'Multicolor', 'Natural', 'Purple', None]
    status: Literal['in_catalog', 'e1_only', 'gone']
    price_usd_band: str | None
    regions_with_price: int | None
    countries_with_price: int | None
    weeks_of_history: int
    photos: int | None
    videos: int | None


class _ArticleResponseResultsValueRequired(TypedDict):
    pass

class ArticleResponseResultsValue(_ArticleResponseResultsValueRequired, total=False):
    status: Literal['ok', 'not_found', 'error']
    reason: str
    code: str
    article: Article


class _ArticleResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None

class ArticleResponse(_ArticleResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool
    results: dict[str, ArticleResponseResultsValue]


class _SearchResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None

class SearchResponse(_SearchResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool
    total: int
    page: int
    pages: int
    results: list[SearchRow]


class _ChangesResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None

class ChangesResponse(_ChangesResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool
    since: str
    departures_from: str | None
    total: int
    page: int
    pages: int
    events: list[dict[str, Any]]


class _FamilyResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None
    family: Family

class FamilyResponse(_FamilyResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool


class _ResolveResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None
    resolved: Resolved

class ResolveResponse(_ResolveResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool


class _IndexResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None

class IndexResponse(_IndexResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool
    count: int
    index: list[dict[str, Any]]


class _SnapshotResponseRequired(TypedDict):
    credits_charged: int
    credits_subscription: int
    credits_retail: int
    resets_hour: str
    resets_day: str
    resets_month: str
    snapshot: str
    fields_refreshed_weekly: bool
    field_age_median_weeks: float | None

class SnapshotResponse(_SnapshotResponseRequired, total=False):
    credits_member_left: int
    member_resets_at: str
    credits_bought: int
    account_status: Literal['registered', 'active']
    sandbox: bool
    snapshot_id: str
    schema_version: str
    loaded_at: str


OpenapiResponse = dict[str, Any]


class GeneratedOperations:
    """One request per call. No retries or automatic pagination."""

    def article(self, codes: str, *, brand: str | None = None) -> ArticleResponse:
        if not isinstance(codes, str) or not codes.strip():
            raise ValueError("required parameter must be a nonempty string")
        if len(codes.split(",")) > 20 or any(not part.strip() for part in codes.split(",")):
            raise ValueError("codes must contain 1 to 20 nonempty codes")
        return cast(ArticleResponse, self._request('/article', {'codes': codes, 'brand': brand}, authenticated=True))

    def search(self, *, q: str | None = None, department: str | None = None, category: str | None = None, type: str | None = None, color: str | None = None, status: str | None = None, page: str | None = None, brand: str | None = None) -> SearchResponse:
        return cast(SearchResponse, self._request('/search', {'q': q, 'department': department, 'category': category, 'type': type, 'color': color, 'status': status, 'page': page, 'brand': brand}, authenticated=True))

    def changes(self, since: str, *, page: str | None = None, brand: str | None = None) -> ChangesResponse:
        if not isinstance(since, str) or not since.strip():
            raise ValueError("required parameter must be a nonempty string")
        return cast(ChangesResponse, self._request('/changes', {'since': since, 'page': page, 'brand': brand}, authenticated=True))

    def family(self, id: str, *, brand: str | None = None) -> FamilyResponse:
        if not isinstance(id, str) or not id.strip():
            raise ValueError("required parameter must be a nonempty string")
        if id is not None and re.fullmatch('^nvprod\\d+v$', id, flags=re.ASCII) is None:
            raise ValueError("parameter does not match the documented format")
        return cast(FamilyResponse, self._request('/family/{id}'.replace('{id}', quote(id, safe='')), {'brand': brand}, authenticated=True))

    def resolve(self, url: str, *, brand: str | None = None) -> ResolveResponse:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("required parameter must be a nonempty string")
        return cast(ResolveResponse, self._request('/resolve', {'url': url, 'brand': brand}, authenticated=True))

    def index(self, *, brand: str | None = None) -> IndexResponse:
        return cast(IndexResponse, self._request('/index', {'brand': brand}, authenticated=True))

    def snapshot(self, *, brand: str | None = None) -> SnapshotResponse:
        return cast(SnapshotResponse, self._request('/snapshot', {'brand': brand}, authenticated=True))

    def openapi(self) -> OpenapiResponse:
        return cast(OpenapiResponse, self._request('/openapi', {}, authenticated=False))

