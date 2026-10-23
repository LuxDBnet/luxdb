"""Copy a supplied canonical contract byte-for-byte; never rewrite its fields."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = {"/article": "article", "/search": "search", "/changes": "changes",
              "/family/{id}": "family", "/resolve": "resolve", "/index": "index",
              "/snapshot": "snapshot", "/openapi": "openapi"}


def validate_document(source: dict, project: dict) -> None:
    if source.get("openapi") != "3.1.0" or set(source.get("paths", {})) != set(OPERATIONS):
        raise ValueError("contract version or routes need review")
    if source.get("servers") != [{"url": project["api_base_url"]}]:
        raise ValueError("server needs review")
    auth = {"apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            "bearer": {"type": "http", "scheme": "bearer"}}
    if source.get("components", {}).get("securitySchemes") != auth or source.get("security") != [{"apiKey": []}, {"bearer": []}]:
        raise ValueError("authentication needs review")
    for path, item in source["paths"].items():
        if set(item) != {"get"}:
            raise ValueError("method needs review")
        if path == "/openapi" and item["get"].get("security") != []:
            raise ValueError("schema access needs review")
    def walk(obj):
        if isinstance(obj, dict):
            if "$ref" in obj and not str(obj["$ref"]).startswith("#/components/schemas/"):
                raise ValueError("external reference needs review")
            for child in obj.values():
                walk(child)
        elif isinstance(obj, list):
            for child in obj:
                walk(child)
    walk(source)


def sanitise(source: dict, project: dict) -> dict:
    """Legacy import name: validate only, without modifying the document."""
    validate_document(source, project)
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="supplied canonical API file")
    parser.add_argument("--canonical", action="store_true", help="compatibility flag; copying is always canonical")
    parser.add_argument("--sha256", help="expected input digest supplied by the API owner")
    args = parser.parse_args()
    raw = args.source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if args.sha256 is not None and digest != args.sha256:
        raise SystemExit("canonical input digest mismatch; no output changed")
    project = json.loads((ROOT / "config/project.json").read_text())
    validate_document(json.loads(raw), project)
    (ROOT / "openapi").mkdir(exist_ok=True)
    (ROOT / "openapi/openapi.json").write_bytes(raw)
    (ROOT / "config/schema-lock.json").write_text(json.dumps({"public_spec_sha256": digest}, indent=2) + "\n")
    print("Canonical bytes and digest copied unchanged. Publication checks remain independent.")


if __name__ == "__main__":
    main()
