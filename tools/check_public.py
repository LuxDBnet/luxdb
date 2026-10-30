"""Pre-upload checks from the independently reviewed, trusted tooling copy.

Candidate code is never executed. Fixed content and typed schema semantics are
checked independently of candidate hashes and SDK regeneration. A draft PASS is
not publication approval; the API-owner contract review is still pending.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import ASSETS, FILES, manifest
from render_public import outputs
from generate_clients import expected, OUTPUT
from generate_js import outputs as js_outputs
from javascript_policy import inspect_javascript
from schema_policy import validate_contract, approved_prose_paths, pointer_parent, pointer_value
from content_policy import inspect_python, inspect_strings, json_strings, normalise, record_categories
from audit_canonical import inspect_contract, approved_demo_url

ROOT = Path(__file__).resolve().parents[1]
TRUSTED_FIXED_BYTES = (ROOT / "config/fixed-hashes.json").read_bytes()
TRUSTED_FIXED = json.loads(TRUSTED_FIXED_BYTES)["sha256"]
TRUSTED_SCHEMA = json.loads((ROOT / "config/schema-policy.json").read_text())
TRUSTED_DEMO = json.loads((ROOT / "config/public-demo.json").read_text())
DEMO_CODES = {row["article"] for row in TRUSTED_DEMO["articles"]}
ALLOWED_HOSTS = {"luxdb.net", "creativecommons.org"}
PUBLIC_URLS = {"https://luxdb.net/", "https://luxdb.net/pricing", "https://luxdb.net/docs/api", "https://luxdb.net/docs/data", "https://luxdb.net/catalog", "https://luxdb.net/api/v1", "https://creativecommons.org/licenses/by/4.0/legalcode.en"}
HEX_HASH = re.compile(r"[a-f0-9]{64}")
ACTION_PIN = re.search(r"actions/checkout@([a-f0-9]{40})", (ROOT / ".github/workflows/ci.yml").read_text()).group(1)
URL = re.compile(r"https?://[^\s<>\"'`]+")
HOST = re.compile(r"(?<![\w.-])(?:[a-zA-Z0-9-]+\.)+(?:com|net|org|io|lan|corp|local|internal|invalid|test)(?![\w.-])")
IP = re.compile(r"(?<![\w.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![\w.])")
IPV6 = re.compile(r"(?<![A-Za-z0-9])(?:[A-Fa-f0-9]{0,4}:){2,}[A-Fa-f0-9:.]{0,45}(?![A-Za-z0-9])")
# The one approved embedded-media block: the README template may start with
# exactly this text, and README.md with it rendered under the configured name.
# Any other img/picture/source markup, anywhere, still blocks.
README_LOGO = """<p align="center">
  <a href="https://luxdb.net/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/mark-dark.png">
      <source media="(prefers-color-scheme: light)" srcset="assets/mark-light.png">
      <img src="assets/mark-light.png" alt="{{PROJECT_NAME}}" width="120">
    </picture>
  </a>
</p>

"""
README_LOGO_RENDERED = README_LOGO.replace("{{PROJECT_NAME}}", json.loads((ROOT / "config/project.json").read_text())["project_name"])
ASSET_PIN_LINES = {f'"{rel}": "{digest}",' for rel, digest in ASSETS.items()}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_CHUNKS = {b"IHDR", b"PLTE", b"tRNS", b"bKGD", b"IDAT", b"IEND"}
ITEM_CODE = re.compile(r"(?<![A-Za-z0-9_])(?:[MN][0-9]{5}|[0-9][A-Z0-9]{5}|LP[0-9]{4}|H[0-9]{6}[A-Z][A-Z0-9]*|P[0-9]{6}|[A-Z0-9]{8,}[-.][A-Z0-9]{2,}|[0-9]{8})(?![A-Za-z0-9_])")


@dataclass(frozen=True)
class Finding:
    category: str
    path: str


def tree_files(root: Path, *, checkout: bool = False) -> tuple[dict[str, Path], list[Finding]]:
    files, issues = {}, []
    if root.is_symlink() or not root.is_dir():
        return {}, [Finding("unsafe-root", "<root>")]
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if checkout and (rel == ".git" or rel.startswith(".git/")):
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            issues.append(Finding("symlink", rel if rel in FILES else "<unapproved path>"))
        elif stat.S_ISREG(mode):
            if rel not in FILES:
                issues.append(Finding("unapproved-file", "<unapproved path>"))
            else:
                files[rel] = path
        elif not stat.S_ISDIR(mode):
            issues.append(Finding("special-file", "<unapproved path>"))
        elif rel == ".git" or not any(name.startswith(rel + "/") for name in FILES):
            issues.append(Finding("unapproved-directory", "<unapproved path>"))
    for rel in set(FILES) - set(files):
        issues.append(Finding("missing-file", rel))
    return files, issues


def png_clean(raw: bytes) -> bool:
    """A well-formed PNG with image chunks only: no text, EXIF or time chunks."""
    if not raw.startswith(PNG_SIGNATURE):
        return False
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(raw):
        length = int.from_bytes(raw[offset:offset + 4], "big")
        kind = raw[offset + 4:offset + 8]
        if kind not in PNG_CHUNKS or offset + 12 + length > len(raw):
            return False
        offset += 12 + length
        if kind == b"IEND":
            return offset == len(raw)
    return False


def entropy(token: str) -> float:
    return -sum((token.count(c) / len(token)) * math.log2(token.count(c) / len(token)) for c in set(token))


def plain_checks(text: str, path: str, *, decoded: bool = False) -> set[str]:
    text = normalise(text)
    categories = set()
    if re.search(r"-----BEGIN (?:[A-Z ]*PRIVATE KEY)-----|(?:sk-|ghp_|github_pat_)[A-Za-z0-9_]{8,}", text):
        categories.add("secret-pattern")
    if re.search(r"(?:X-API-Key|Authorization)\s*:\s*(?!demo\b)[A-Za-z0-9_-]{12,}", text, re.I):
        categories.add("credential-header")
    if decoded and re.fullmatch(r"[A-Za-z0-9_-]{49}", text) and (any(c.isdigit() for c in text) or text.startswith(("luxdb_", "lxdb_", "ldb_"))):
        categories.add("key-shape-49")
    if re.search(r"\b(?:private|internal)-(?:session|worker)-[a-z0-9]+\b", text):
        categories.add("internal-agent-name")
    emails = re.findall(r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", text)
    if any(email != "support@luxdb.net" for email in emails):
        categories.add("foreign-email")
    if re.search(r"(?<![\w.-])localhost:[0-9]+(?![\w.-])", text, re.I):
        categories.add("unapproved-host")
    for line in text.splitlines():
        for token in re.findall(r"[A-Za-z0-9_+/-]{40,}={0,2}", line):
            is_hash = HEX_HASH.fullmatch(token) and not decoded and (
                path == "config/schema-lock.json" and "public_spec_sha256" in line or
                path == "clients/python/src/luxdb_client/generated.py" and line.startswith("# Public spec SHA256: ") or
                path == "config/fixed-hashes.json" and token in TRUSTED_FIXED.values()
            )
            is_action_pin = path == ".github/workflows/ci.yml" and token == ACTION_PIN and ("actions/checkout@" in line or decoded)
            is_file = any(token in name for name in FILES) and "/" in token
            is_name = not decoded and path.endswith(".py") and re.match(r"\s*(?:def|class)\s+" + re.escape(token) + r"[(:]", line)
            is_reviewed_pointer = path == "tools/schema_policy.py" and token in approved_prose_paths(TRUSTED_SCHEMA)
            if not (is_hash or is_action_pin or is_file or is_name or is_reviewed_pointer) and (re.fullmatch(r"[a-f0-9]{40,}", token) or entropy(token) > 4.0):
                categories.add("high-entropy-secret")
    for raw in URL.findall(text):
        url = raw.rstrip(".,;:)]}")
        try:
            parts = urlsplit(url)
            port = parts.port
        except ValueError:
            categories.add("unapproved-url")
            continue
        if url not in PUBLIC_URLS or parts.hostname not in ALLOWED_HOSTS or port or parts.username or parts.password:
            categories.add("unapproved-url")
    if any(host.lower() not in ALLOWED_HOSTS for host in HOST.findall(text)):
        categories.add("unapproved-host")
    for value in IP.findall(text) + IPV6.findall(text):
        try:
            ipaddress.ip_address(value)
        except ValueError:
            continue
        categories.add("ip-address")
    if re.search(r"(?:\/home\/|\/opt\/|\/srv\/|\/run\/|\/etc\/|\/var\/|[a-zA-Z]:\\Users\\)", text):
        categories.add("internal-path")
    if any(not match.startswith("SYNTHETIC-") and match not in DEMO_CODES for match in ITEM_CODE.findall(text)):
        categories.add("real-shaped-item-code")
    if re.search(r"<(?:img|video|iframe|svg|image|picture|object|embed)\b|data:image\/|data:video\/", text, re.I):
        categories.add("embedded-media")
    if any(0x1F000 <= ord(c) <= 0x1FAFF or 0x2600 <= ord(c) <= 0x27BF or ord(c) in {0xFE0F, 0x20E3} for c in text):
        categories.add("pictograph")
    return categories


def strict_json(text: str):
    def no_constant(_):
        raise ValueError("non-finite JSON is not allowed")
    def no_duplicate(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(text, parse_constant=no_constant, object_pairs_hook=no_duplicate)


def inspection_text(text: str, path: str) -> str:
    if path not in {"openapi/openapi.json", "config/schema-policy.json"}:
        return text
    try:
        obj = strict_json(text)
        document = obj["contract"] if path == "config/schema-policy.json" else obj
        changed = False
        for approval in TRUSTED_DEMO.get("approved_example_urls", []):
            pointer = approval["json_pointer"]
            if approved_demo_url(pointer, approval["value"], approval["variant_article"], TRUSTED_DEMO) is None:
                continue
            parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.lstrip("/").split("/")]
            node = document
            for part in parts[:-1]:
                node = node[part]
            if node.get(parts[-1]) == approval["value"]:
                node[parts[-1]] = "SYNTHETIC-APPROVED-URL"
                changed = True
        # Exact reviewed public demo URL, not arbitrary paths/strings.
        pointer = "/components/schemas/Article/properties/lv_url/example"
        node, key = pointer_parent(document, pointer)
        reviewed = pointer_value(TRUSTED_SCHEMA["contract"], pointer)
        if node[key] == reviewed and isinstance(reviewed, str) and reviewed.startswith("/") and not reviewed.startswith("//") and reviewed.rsplit("/", 1)[-1] in DEMO_CODES:
            node[key] = "SYNTHETIC-APPROVED-URL"
            changed = True
        for pointer in approved_prose_paths(TRUSTED_SCHEMA):
            node, key = pointer_parent(document, pointer)
            expected_text = pointer_value(TRUSTED_SCHEMA["contract"], pointer)
            if type(node[key]) is str and node[key] == expected_text:
                node[key] = "SYNTHETIC-APPROVED-PROSE"
                changed = True
        # The service's field-definition digest is public metadata. Mask only
        # this exact reviewed value at this node; all other hashes stay scanned.
        reviewed_digest = TRUSTED_SCHEMA["contract"].get("info", {}).get("x-luxdb-fields")
        if (isinstance(reviewed_digest, str) and HEX_HASH.fullmatch(reviewed_digest)
                and document.get("info", {}).get("x-luxdb-fields") == reviewed_digest):
            document["info"]["x-luxdb-fields"] = "SYNTHETIC-APPROVED-DIGEST"
            changed = True
        return json.dumps(obj, ensure_ascii=False) if changed else text
    except (ValueError, KeyError, TypeError, AttributeError):
        return text


def text_checks(text: str, path: str) -> set[str]:
    # Exact, evidenced URL nodes are screened as placeholders. No file content
    # is changed; digest, schema and semantic checks still use original bytes.
    text = inspection_text(text, path)
    logo = {"README.md": README_LOGO_RENDERED, "templates/README.md.in": README_LOGO}.get(path)
    if logo and text.startswith(logo):
        text = text[len(logo):]
    if path == "tools/check_public.py" and text.count(README_LOGO) == 1:
        text = text.replace(README_LOGO, "")
    categories = plain_checks(text, path)
    strings = []
    if path.endswith(".py"):
        ast_categories, strings = inspect_python(text)
        categories.update(ast_categories)
    if path.endswith((".js", ".mjs", ".ts")):
        js_categories, js_strings = inspect_javascript(text)
        categories.update(js_categories)
        strings.extend(js_strings)
    is_json = path.endswith(".json")
    try:
        obj = strict_json(text)
    except (ValueError, RecursionError):
        if is_json:
            categories.add("invalid-json")
    else:
        strings.extend(json_strings(obj))
        if path not in {"openapi/openapi.json", "config/schema-policy.json"}:
            categories.update(record_categories(obj))
    # JSON-bearing Markdown/code strings and transformed standalone tokens are
    # inspected even when the containing file is not named .json.
    if path == "tools/check_public.py":
        strings = [value for value in strings if value != README_LOGO]
    strings.extend(re.findall(r"[A-Za-z0-9+/_-]{8,}={0,2}", text))
    categories.update(inspect_strings(strings, lambda value: plain_checks(value, path, decoded=True)))
    return categories


def fixture_valid(obj: dict) -> bool:
    if set(obj) != {"synthetic", "response"} or obj["synthetic"] is not True:
        return False
    response = obj["response"]
    if not isinstance(response, dict):
        return False
    keys = {"credits_charged", "credits_subscription", "credits_retail", "resets_hour", "resets_day", "resets_month", "snapshot", "fields_refreshed_weekly", "field_age_median_weeks", "sandbox", "total", "page", "pages", "results"}
    if set(response) != keys:
        return False
    zeros = {"credits_charged", "credits_subscription", "credits_retail", "total", "pages"}
    return (all(type(response[k]) is int and response[k] == 0 for k in zeros)
            and type(response["page"]) is int and response["page"] == 1
            and response["results"] == [] and response["snapshot"] == "synthetic-week"
            and response["sandbox"] is True and response["fields_refreshed_weekly"] is False
            and response["field_age_median_weeks"] is None
            and all(response[k] == "2000-01-01T00:00:00Z" for k in {"resets_hour", "resets_day", "resets_month"}))


def scan(root: Path = ROOT) -> list[Finding]:
    files, issues = tree_files(root)
    contents = {}
    for rel, path in files.items():
        if path.stat().st_size > 1024 * 1024:
            issues.append(Finding("file-size", rel))
            continue
        if rel in ASSETS:
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != ASSETS[rel] or not png_clean(raw):
                issues.append(Finding("asset-drift", rel))
            continue
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except (UnicodeError, OSError):
            issues.append(Finding("non-text-file", rel))
            continue
        if "\x00" in text:
            issues.append(Finding("binary-content", rel))
            continue
        contents[rel] = text
        digest = hashlib.sha256(raw).hexdigest()
        fixed_match = rel in TRUSTED_FIXED and digest == TRUSTED_FIXED[rel]
        if rel in TRUSTED_FIXED and not fixed_match:
            issues.append(Finding("fixed-content-drift", rel))
            if rel == "metadata/fields.json":
                issues.append(Finding("dictionary-policy", rel))
            if rel == "metadata/houses.json":
                issues.append(Finding("unapproved-house-snapshot", rel))
        try:
            categories = text_checks(text, rel)
        except (ValueError, TypeError, RecursionError, OverflowError):
            categories = {"unanalysable-content"}
        # Accepted negative-test source intentionally contains fabricated attack
        # literals. The exception requires its exact reviewed content hash; adding
        # or changing any test disables the exception. All literals are inspected.
        if fixed_match and (rel.startswith("tests/test_") or rel.startswith("clients/js/test/")):
            categories -= {"foreign-email", "secret-pattern", "credential-literal", "high-entropy-secret", "key-shape-49", "internal-agent-name", "unapproved-host", "unapproved-url", "ip-address", "internal-path", "real-shaped-item-code", "embedded-media", "pictograph", "record-literal", "record-values", "dynamic-record-value", "javascript-dynamic-template", "javascript-unanalysable-literal", "javascript-record-literal", "javascript-obfuscated-source"}
        # These two hashes are bookkeeping, not credential strings. Their allowed
        # structure/contents are verified separately, not by an unrestricted path
        # exemption for arbitrary JSON values.
        if rel == "config/fixed-hashes.json" and raw == TRUSTED_FIXED_BYTES:
            categories.discard("high-entropy-secret")
        if rel in {"config/schema-policy.json", "config/sources.json", "config/public-demo.json"} and fixed_match:
            # Reviewed policy paths and source/evidence digests are frozen values.
            categories.discard("high-entropy-secret")
        if rel == "config/public-demo.json" and fixed_match:
            # This exact reviewed file records demo codes and one evidenced URL
            # variant. It does not add that variant to the global article set.
            categories.discard("real-shaped-item-code")
        if rel == "config/schema-lock.json":
            try:
                lock = strict_json(text)
                if set(lock) == {"public_spec_sha256"} and HEX_HASH.fullmatch(lock["public_spec_sha256"]):
                    categories.discard("high-entropy-secret")
            except (ValueError, TypeError, KeyError):
                pass
        if rel in {"clients/python/src/luxdb_client/generated.py", "clients/js/generated.js"}:
            # Only the generated hash comment, not additional arbitrary strings.
            clean = re.sub(r"(?m)^(?:#|//) Public spec SHA256: [a-f0-9]{64}$", "", text)
            if "high-entropy-secret" not in text_checks(clean, rel):
                categories.discard("high-entropy-secret")
        if rel == "tools/inventory.py":
            # Only the exact pin lines; each digest must also match its image
            # bytes (asset-drift above), so no other string can ride along.
            clean = "\n".join(line for line in text.splitlines() if line.strip() not in ASSET_PIN_LINES)
            if "high-entropy-secret" not in text_checks(clean, rel):
                categories.discard("high-entropy-secret")
        issues.extend(Finding(category, rel) for category in categories)
    if set(contents) != set(FILES) - set(ASSETS):
        return sorted(set(issues), key=lambda x: (x.path, x.category))
    try:
        if contents["config/fixed-hashes.json"].encode() != TRUSTED_FIXED_BYTES:
            issues.append(Finding("fixed-policy-drift", "config/fixed-hashes.json"))
        spec = strict_json(contents["openapi/openapi.json"])
        sources = strict_json(contents["config/sources.json"])
        if hashlib.sha256(contents["openapi/openapi.json"].encode()).hexdigest() != sources["openapi_sha256"]:
            issues.append(Finding("canonical-source-digest", "openapi/openapi.json"))
        for finding in inspect_contract(spec, TRUSTED_DEMO)["findings"]:
            issues.append(Finding("upstream-copy", "openapi/openapi.json" + finding["pointer"]))
        data_defs = strict_json(contents["metadata/fields.json"])
        for table in data_defs.get("tables", []):
            for field in table.get("fields", []):
                if "probe" in field["name"]:
                    issues.append(Finding("upstream-copy", "metadata/fields.json/" + table["name"] + "/" + field["name"]))
        try:
            validate_contract(spec, TRUSTED_SCHEMA)
        except (ValueError, KeyError, TypeError):
            issues.append(Finding("schema-policy", "openapi/openapi.json"))
            issues.append(Finding("unsafe-spec-structure", "openapi/openapi.json"))
        if contents["MANIFEST.md"] != manifest():
            issues.append(Finding("manifest-drift", "MANIFEST.md"))
        if not fixture_valid(strict_json(contents["tests/fixtures/synthetic-response.json"])):
            issues.append(Finding("non-synthetic-fixture", "tests/fixtures/synthetic-response.json"))
        for path, text in outputs(root).items():
            if contents[path] != text:
                issues.append(Finding("render-drift", path))
        for path, text in js_outputs(root).items():
            if contents[path] != text:
                issues.append(Finding("sdk-drift", path))
        if contents[OUTPUT.as_posix()] != expected(root):
            issues.append(Finding("sdk-drift", OUTPUT.as_posix()))
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError, OSError):
        issues.append(Finding("invalid-bundle-or-lock", "<metadata>"))
    return sorted(set(issues), key=lambda x: (x.path, x.category))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues = scan(args.root)
    if issues:
        for issue in issues:
            print(f"BLOCKED: {issue.category} in {issue.path}")
        raise SystemExit(1)
    print(f"PASS: {len(FILES) - len(ASSETS)} approved text files and {len(ASSETS)} pinned images; fixed content, typed schema and generated artifacts agree.")
    print("Independent review and owner authorisation are still required before publication.")


if __name__ == "__main__":
    main()
