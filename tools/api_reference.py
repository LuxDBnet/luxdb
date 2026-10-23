"""Render definition-only API documentation from the canonical contract."""
from __future__ import annotations

import re

SUMMARIES = {"/article": "Read item details and history. One credit per item; see the response for charges.",
              "/search": "Search the catalogue and read a short result list.",
              "/changes": "Read changes since a chosen week.",
              "/family/{id}": "Read items in a family. IDs must match the documented format.",
              "/resolve": "Find an item or family from a storefront link.",
              "/index": "Read the item index. Business access and the daily download limit apply.",
              "/snapshot": "Read the latest weekly release details.",
              "/openapi": "Read this API contract. No key is required."}
PROSE_OVERRIDES = {
    "brand": "House identifier.",
    "name_source": "Origin of the display name.",
    "snapshot": "Weekly data release identifier.",
    "snapshot_id": "Week identifier.",
    "weeks_unlisted": "Consecutive weeks without a listing or price.",
    "family_sizes": "Sizes the family offers that this item does not list.",
    "regions_present": "Storefronts where the item is listed.",
    "regions_observed": "Storefronts where listing was observed.",
    "regions_declared": "Storefronts reported by the house.",
    "countries_present": "Countries where the item is listed.",
    "countries_observed": "Countries where listing was observed.",
    "countries_declared": "Countries reported by the house.",
    "code": "Machine-readable error code.",
    "scope": "Whose account allowance the error concerns.",
}
UNSUITABLE = re.compile(r"\b(?:FAT|PLP|PDP|CDN|probe|sibling|ladder)\b|X-RateLimit-Scope|counted\s*=|basis\s*=|presence_current|code.lookup", re.I)


def prose(text: str, name: str = "") -> str:
    if name in PROSE_OVERRIDES:
        return PROSE_OVERRIDES[name]
    first = re.split(r"(?<!incl\.)(?<!excl\.)(?<!e\.g\.)(?<!i\.e\.)(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    if UNSUITABLE.search(first):
        return ""
    first = re.sub(r"\bsnapshots?\b", "weekly release", first, flags=re.I)
    return re.sub(r"\bLV\b", "Louis Vuitton", first)


def kind(obj: dict) -> str:
    if "$ref" in obj:
        return obj["$ref"].split("/")[-1]
    if "oneOf" in obj or "anyOf" in obj:
        return "one of " + ", ".join(kind(child) for child in obj.get("oneOf", obj.get("anyOf")))
    value = obj.get("type", "object")
    return " or ".join(value) if isinstance(value, list) else str(value)


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def field_rows(node: dict, prefix="", required=False):
    if "$ref" in node:
        return
    if node.get("oneOf") or node.get("anyOf"):
        for i, case in enumerate(node.get("oneOf", node.get("anyOf"))):
            yield from field_rows(case, prefix + f" (case {i + 1})", required)
        return
    for name, child in node.get("properties", {}).items():
        path = prefix + ("." if prefix else "") + name
        enum = child.get("enum", [child["const"]] if "const" in child else [])
        yield path, kind(child), name in node.get("required", []), prose(child.get("description", ""), name), enum
        if "properties" in child or child.get("oneOf") or child.get("anyOf"):
            yield from field_rows(child, path)
        if "items" in child and isinstance(child["items"], dict):
            yield from field_rows(child["items"], path + "[]")


def render_reference(name: str, spec: dict) -> str:
    lines = [f"# {name} API reference", "", "Definitions only. No item observations or response examples are included.",
             "Requests use the public server in the linked [contract](../openapi/openapi.json).",
             "Authenticated requests use X-API-Key or Bearer. The Python client uses X-API-Key.", "",
             "A missing field differs from a field whose value is null. The tables use", "the contract's exact names and types; prose is shortened for readability.", ""]
    for path, item in spec["paths"].items():
        op = item["get"]
        lines += [f"## GET `{path}`", "", SUMMARIES[path], ""]
        if op.get("parameters"):
            lines += ["| Parameter | Location | Required | Type | Format |", "|---|---|---|---|---|"]
            for par in op["parameters"]:
                constraint = par["schema"].get("pattern", "")
                lines.append("| " + " | ".join(map(cell, [f"`{par['name']}`", par["in"], "yes" if par.get("required") else "no", kind(par["schema"]), constraint])) + " |")
            lines.append("")
        codes = ", ".join(op.get("responses", {}))
        lines += ["Responses: " + codes + ".", ""]
        success = op["responses"]["200"].get("content", {}).get("application/json", {}).get("schema", {})
        if "allOf" in success:
            for part in success["allOf"]:
                for key, obj in part.get("properties", {}).items():
                    lines.append(f"The successful body includes `{key}` ({kind(obj)}).")
            lines.append("")
        if path == "/index":
            lines += ["The API accepts If-None-Match and can return 304 without a body.",
                      "That unchanged response does not use a download or credits.",
                      "The Python convenience client does not send this header or expose ETag;",
                      "its successful index calls use the download allowance even if unchanged.", ""]
    lines += ["## Response fields", ""]
    for schema_name, node in spec["components"]["schemas"].items():
        lines += [f"### `{schema_name}`", "", "| Field | Type | Required | Meaning | Allowed values |", "|---|---|---|---|---|"]
        for path, type_, required, meaning, enum in field_rows(node):
            values = ", ".join("`" + ("null" if x is None else str(x)) + "`" for x in enum)
            lines.append("| " + " | ".join(map(cell, [f"`{path}`", type_, "yes" if required else "no", meaning, values])) + " |")
        lines.append("")
    lines += ["## Errors", "", "Check the HTTP status and the error code. No request is retried automatically.",
              "On 402, payment_required means credits are unavailable; member_limit_reached",
              "means a team member's allowance is used. On 503, mode is maintenance or stopped.",
              "Follow Retry-After when present. No credits are charged for a refused request.", ""]
    source_name = spec["info"]["title"].removesuffix(" API")
    return "\n".join(lines).replace(source_name, name)
