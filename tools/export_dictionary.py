"""Export public field definitions only, never rows, coverage or example values."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLES = {"product_client": "Item details", "product_stats": "Coverage and status",
          "department": "Departments", "region": "Storefronts", "product_spec": "Specifications",
          "size_variant": "Sizes and colours", "article_variant": "Item variations",
          "price_current": "Current prices", "price_observation": "Price history",
          "presence_observation": "Listing history", "presence_current": "Current listings",
          "region_url": "Item links", "image": "Photos", "video": "Videos",
          "fx_rate": "Currency conversion", "snapshot": "Weekly releases", "demo_set": "Public demo selection"}
OVERRIDES = {
    "product_client.name_en": "Display name used on English-language cards.",
    "product_client.name_en_source": "Origin of the display name used on English-language cards.",
    "product_stats.regions_present": "Number of storefronts with a recorded listing.",
    "product_stats.regions_observed": "Number of storefronts where listing was observed.",
    "product_stats.regions_declared": "Number of storefronts reported by the house.",
    "product_stats.countries_present": "Number of countries with a recorded listing.",
    "product_stats.countries_observed": "Number of countries where listing was observed.",
    "product_stats.countries_declared": "Number of countries reported by the house.",
    "product_stats.weeks_unlisted": "Consecutive weeks without a listing or price.",
    "product_stats.status": "Listing status: in_catalog, e1_only or gone. Delisted does not mean discontinued.",
    "product_client.category_source": "Category origin as reported in the data.",
    "product_client.record_completeness": "How much item detail is available.",
    "product_client.features_source": "Origin of the feature list.",
    "product_client.care": "Care instructions supplied by the house, when available.",
    "price_current.price_state": "Whether the price is current, no longer shown, or awaiting an update.",
    "fx_rate.source": "Reference used for the currency conversion rate.",
    "snapshot.started_at": "When observations for the week started.",
    "snapshot.finished_at": "When observations for the week finished.",
}


def plain_definition(table: str, public_name: str, doc: str) -> tuple[str, str]:
    key = table + "." + public_name
    if key in OVERRIDES:
        return OVERRIDES[key], "plain wording override"
    if public_name == "brand":
        return "House identifier.", "multi-house wording"
    if doc.startswith("Article —"):
        return "Item reference code, used together with the house identifier.", "omit real-code illustrations"
    # Keep the definition, not illustrations, coverage figures or longer house
    # notes. The source input remains outside the publication tree.
    text = re.split(r"(?<!incl\.)(?<!excl\.)(?<!e\.g\.)(?<!i\.e\.)(?<=[.!?])\s+", doc.strip(), maxsplit=1)[0]
    text = re.sub(r"\bsnapshots?\b", "weekly release", text, flags=re.I)
    text = re.sub(r"\bcollection\b", "observations", text) if table in {"snapshot", "fx_rate", "presence_observation", "price_observation", "price_current"} else text
    text = text.replace("not captured", "not recorded")
    return text, "first definition sentence"


def project(source: dict) -> tuple[dict, list[dict]]:
    tables, audit = [], []
    for ti, table in enumerate(source["tables"]):
        fields = []
        for fi, field in enumerate(table["fields"]):
            pointer = f"/tables/{ti}/fields/{fi}"
            if field.get("hidden"):
                audit.append({"pointer": pointer, "action": "hidden field omitted"})
                continue
            public_name = field["public_name"]
            meaning, action = plain_definition(table["name"], public_name, field.get("doc", ""))
            if not public_name or not meaning:
                raise ValueError("public name and definition are required")
            kind = field["type"].replace("snapshot_id (ISO week)", "ISO week")
            fields.append({"name": public_name, "type": kind, "unit": field.get("unit", ""),
                           "meaning": meaning, "enum": field.get("enum", []),
                           "empty": field.get("empty", "")})
            audit.append({"pointer": pointer, "public_field": table["name"] + "." + public_name,
                          "action": action, "source_quote": field.get("doc", ""), "output": meaning})
        tables.append({"name": table["name"], "title": TITLES[table["name"]], "fields": fields})
    specifications = []
    for name, obj in sorted(source["spec_keys"].items()):
        label = re.sub(r"\bLV\b", "Louis Vuitton", obj["label_en"])
        specifications.append({"name": name, "type": obj["kind"], "unit": obj.get("unit", ""), "meaning": label})
        if label != obj["label_en"]:
            audit.append({"pointer": "/spec_keys/" + name + "/label_en", "action": "expand house abbreviation", "source_quote": obj["label_en"], "output": label})
    return {"status": "definitions_only", "updates": "auto-generated later", "tables": tables,
            "specifications": specifications}, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--audit", type=Path, help="private review report outside the publication tree")
    args = parser.parse_args()
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise SystemExit("dictionary input digest mismatch")
    metadata, audit = project(json.loads(raw))
    (ROOT / "metadata/fields.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    if args.audit:
        if ROOT == args.audit.resolve() or ROOT in args.audit.resolve().parents:
            raise SystemExit("raw-definition audit must stay outside the publication tree")
        args.audit.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
    print("Exported public definitions only; hidden fields, observations and coverage values excluded.")


if __name__ == "__main__":
    main()
