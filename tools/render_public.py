"""Render short public guides and definition-only references."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_reference import render_reference

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {"templates/README.md.in": "README.md", "templates/quickstart.md.in": "docs/quickstart.md",
             "templates/CONTRIBUTING.md.in": "CONTRIBUTING.md", "templates/SECURITY.md.in": "SECURITY.md",
             "templates/NOTICE.md.in": "NOTICE.md"}


def disclaimer(name: str) -> str:
    return (f"{name} is an independent service and is not affiliated with, endorsed by, "
            "or sponsored by any of the houses mentioned. Their names and trademarks "
            "belong to their respective owners.")


def render_houses(name: str, metadata: dict) -> str:
    if metadata.get("status") != "draft_snapshot" or metadata.get("updates") != "auto-generated later":
        raise ValueError("live house list is not implemented in this draft")
    lines = [f"# {name} houses", "", "Static draft list; **auto-generated later**.", "",
             "| Code | House |", "|---|---|"]
    lines += [f"| `{row['code']}` | {row['name']} |" for row in metadata["houses"]]
    return "\n".join(lines) + "\n"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_fields(name: str, metadata: dict, spec: dict | None = None) -> str:
    if metadata.get("status") != "definitions_only":
        raise ValueError("definitions-only dictionary expected")
    lines = [f"# {name} data dictionary", "", "Field definitions only. No item records, prices, images or coverage figures are included.",
             "The public field names below come from the data dictionary. API response names",
             "and types are listed separately in the [API reference](api-reference.md).", "",
             "Dictionary snapshot; it may lag the API contract. See the API reference for newer response fields.", "",
             "An empty value can mean not stated by the house, not recorded, or not applicable.",
             "It does not mean zero. Refer to the field's meaning and allowed values.", ""]
    for table in metadata["tables"]:
        lines += ["## " + table["title"], "", "Table: `" + table["name"] + "`.", "",
                  "| Field | Type | Unit | Meaning | Allowed values |", "|---|---|---|---|---|"]
        seen = set()
        for field in table["fields"]:
            if field["name"] in seen or set(field) != {"name", "type", "unit", "meaning", "enum", "empty"}:
                raise ValueError("duplicate or unexpected dictionary field")
            seen.add(field["name"])
            values = ", ".join("`" + ("null" if x is None else str(x)) + "`" for x in field["enum"])
            lines.append("| " + " | ".join(map(cell, ["`" + field["name"] + "`", field["type"], field["unit"], field["meaning"], values])) + " |")
        lines.append("")
    lines += ["## Specification fields", "", "| Field | Type | Unit | Meaning |", "|---|---|---|---|"]
    for field in metadata["specifications"]:
        lines.append("| " + " | ".join(map(cell, ["`" + field["name"] + "`", field["type"], field["unit"], field["meaning"]])) + " |")
    return "\n".join(lines) + "\n"


def outputs(root: Path = ROOT) -> dict[str, str]:
    project = json.loads((root / "config/project.json").read_text())
    name = project["project_name"]
    replacements = {"{{PROJECT_NAME}}": name, "{{CONTACT}}": project["contact"], "{{DISCLAIMER}}": disclaimer(name)}
    result = {}
    for source, target in TEMPLATES.items():
        text = (root / source).read_text()
        for marker, value in replacements.items():
            text = text.replace(marker, value)
        if "{{" in text:
            raise ValueError("unexpanded template variable")
        result[target] = text
    spec = json.loads((root / "openapi/openapi.json").read_text())
    result["docs/houses.md"] = render_houses(name, json.loads((root / "metadata/houses.json").read_text()))
    result["docs/data-dictionary.md"] = render_fields(name, json.loads((root / "metadata/fields.json").read_text()))
    result["docs/api-reference.md"] = render_reference(name, spec)
    result["docs/api-compatibility.md"] = (
        f"# {name} Python client\n\n"
        "Python 3.10 or later. Responses are JSON dictionaries with generated type hints;\n"
        "they are not validated or converted at runtime. Unspecified fields stay untyped.\n\n"
        "The client uses the demo key by default. A paid key requires allow_paid=True.\n"
        "It makes one request per call, without retries, redirects or automatic paging.\n\n"
        "Python timeout and JavaScript timeoutMs both set one overall monotonic deadline,\n"
        "covering connection, headers and the whole success or error body. The Python\n"
        "stdlib transport supervises one short-lived HTTP child, stops it on expiry and\n"
        "reaps it before returning TransportTimeout (also a TimeoutError). Startup counts\n"
        "towards the deadline; termination/reaping may add a small scheduling delay. No\n"
        "background worker remains and no retry is attempted after an uncertain outcome.\n\n"
        "The built-in transport honours HTTPS_PROXY/https_proxy and NO_PROXY/no_proxy\n"
        "as urllib does. The API key travels inside TLS; choose trusted proxy and CA\n"
        "settings. HTTP_PROXY/http_proxy and ALL_PROXY are not passed to the worker.\n"
        "Its explicit environment allowlist contains PATH, SSL_CERT_FILE/SSL_CERT_DIR\n"
        "and those HTTPS proxy/bypass settings; on Windows only, SYSTEMROOT, WINDIR,\n"
        "TEMP and TMP are also allowed. No other application environment is inherited.\n\n"
        "A custom Transport is trusted code: it receives the key and URL and must keep\n"
        "the destination, forbid retries and redirects, enforce the response read limit\n"
        "and honour the same overall timeout. The client cannot enforce I/O rules inside\n"
        "an injected transport.\n\n"
        "Family IDs must match the format in the contract. The index requires Business\n"
        "access. Successful index downloads use the daily allowance, even if unchanged.\n"
        "The client does not send If-None-Match, expose ETag, or return a 304 result; use\n"
        "a conditional HTTP client for unchanged downloads. Do not poll the index.\n\n"
        "On HTTP errors, check ApiError.status, code, mode and retry_after_seconds.\n"
        "Mode is maintenance or stopped when supplied. On 402, inspect the code before\n"
        "deciding whether to add credits or ask the team owner about an allowance.\n"
        "Follow Retry-After when present. No failed request is retried automatically.\n\n"
        "Nullable prices, dimensions and country counts come from the canonical\n"
        "contract itself; neither client applies manual type overrides. Unknown error keys remain in\n"
        "ApiError.details, without appearing in its message. Inspect details explicitly;\n"
        "do not log it. 404 and 405 are ordinary HTTP API errors.\n\n"
        "The demo key allows 1 request per minute and 300 per day per address.\n"
        "Make one call or wait at least 60 seconds; on 429 follow Retry-After.\n"
        "X-RateLimit-Remaining includes the request just served; at the one-request-\n"
        "per-minute limit it reports 0. The charge is the body field\n"
        "credits_charged; there is no charge header.\n\n"
        "See the [API reference](api-reference.md) for exact fields and response shapes.\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = outputs()
    if args.check:
        if any(not (ROOT / path).exists() or (ROOT / path).read_text() != text for path, text in result.items()):
            raise SystemExit("rendered public copy is stale")
        print("Public guides and references match their definition sources.")
    else:
        for path, text in result.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        print("Rendered definition-only data and API references.")


if __name__ == "__main__":
    main()
