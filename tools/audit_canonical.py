"""Audit canonical buyer copy and classify reference codes against public demos.

This never rewrites the upstream contract. Quotes are for a private review report;
publication scanning emits categories and JSON pointers only.
"""
from __future__ import annotations

import re

JARGON = re.compile(r"\b(?:FAT|PLP|PDP|CDN|probe|sibling|snapshots?)\b", re.I)
RULES = re.compile(r"X-RateLimit-Scope|counted\s*=|basis\s*=|presence_current|code.lookup|ladder|per.address", re.I)
CODE = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Z0-9][A-Z0-9_.-]{5,}|[HPV][A-Z0-9]{5,}v[A-Za-z0-9]+)(?![A-Za-z0-9_])")


def escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def codes(text: str) -> list[str]:
    result = []
    for match in CODE.finditer(text):
        code = match.group(0).rstrip(".")
        if not any(c.isdigit() for c in code) or not any(c.isalpha() for c in code) and not (len(code) == 8 and code.isdigit()):
            continue
        if re.fullmatch(r"[0-9]{4}-W[0-9]{2}|ISO[0-9-]+", code):
            continue
        result.append(code)
    return sorted(set(result))


def approved_demo_url(pointer: str, value: object, code: str, public_demo: dict) -> dict | None:
    parents = {(row["brand"], row["article"]) for row in public_demo["articles"]}
    for approval in public_demo.get("approved_example_urls", []):
        if (approval["json_pointer"] == pointer and approval["value"] == value
                and approval["variant_article"] == code
                and (approval["brand"], approval["demo_article"]) in parents
                and isinstance(value, str) and value.startswith("/") and not value.startswith("//")):
            return approval
    return None


def inspect_contract(spec: dict, public_demo: dict) -> dict:
    membership = {}
    for row in public_demo["articles"]:
        membership.setdefault(row["article"], []).append(row["brand"])
    findings, examples = [], []
    def walk(obj, pointer="", key=""):
        if isinstance(obj, dict):
            for name, value in obj.items():
                target = pointer + "/" + escape(name)
                if "probe" in name.lower() and name not in {"examples", "example"}:
                    findings.append({"kind": "internal field name", "pointer": target, "quote": name, "status": "upstream fix needed"})
                if name in {"example", "examples", "default"}:
                    text_field = pointer.rsplit("/", 1)[-1]
                    if pointer.startswith("/components/schemas/Article/properties/") and text_field in {"description", "description_short", "description_local", "features", "care", "sustainability"}:
                        placeholder = isinstance(value, str) and (not value.strip() or value.startswith("SYNTHETIC-") or value.strip().lower() in {"part of a paid card", "part of paid card", "[placeholder]", "synthetic", "the brand's description and the local-language name are part of a paid card."})
                        if value is not None and not placeholder:
                            findings.append({"kind": "brand-text example; no demo exception", "pointer": target, "quote": value, "status": "upstream fix needed"})
                    references = []
                    for code in codes(value) if isinstance(value, str) else []:
                        brands = membership.get(code, [])
                        approval = approved_demo_url(target, value, code, public_demo)
                        references.append({"article": code, "public_demo": bool(brands), "brands": brands,
                                           "allowed_demo_url": approval is not None,
                                           "demo_article": approval["demo_article"] if approval else None})
                        if not brands and approval is None:
                            findings.append({"kind": "example outside public demo", "pointer": target, "quote": code, "status": "upstream fix needed"})
                    examples.append({"pointer": target, "value": value, "codes": references})
                walk(value, target, name)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, pointer + "/" + str(i), key)
        elif isinstance(obj, str) and key in {"description", "summary", "title"}:
            reasons = []
            # Public protocol identifiers and the published demo allowance are not
            # collection jargon. Remove only these spellings before the prose scan;
            # surrounding text (including any added internal terms) remains checked.
            prose_text = re.sub(r"\bX-(?:Data-Snapshot|RateLimit-Scope)\b|`snapshot`", "", obj)
            if pointer == "/info/description":
                prose_text = prose_text.replace("one request a minute and 300 a day per address", "")
            if JARGON.search(prose_text):
                reasons.append("buyer jargon")
            if RULES.search(prose_text):
                reasons.append("internal rule or response header wording")
            if "Louis Vuitton article archive" in obj or "LV article code" in obj:
                reasons.append("single-house API introduction")
            if reasons:
                findings.append({"kind": "; ".join(reasons), "pointer": pointer, "quote": obj, "status": "upstream fix needed"})
    walk(spec)
    return {"findings": findings, "examples": examples}
