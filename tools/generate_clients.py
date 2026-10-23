"""Generate typed Python models and bounded calls from the canonical contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("clients/python/src/luxdb_client/generated.py")
METHOD_NAMES = {"/article": "article", "/search": "search", "/changes": "changes",
                "/family/{id}": "family", "/resolve": "resolve", "/index": "index",
                "/snapshot": "snapshot", "/openapi": "openapi"}
# These convenience methods return JSON only. Conditional downloads need an HTTP
# client that exposes response headers and a body-less 304; no implicit request
# or undocumented partial handling is introduced here.
UNSUPPORTED_HEADERS = {"/index": ("If-None-Match",)}


def identifier(value: str) -> str:
    if not value.isidentifier() or keyword.iskeyword(value):
        raise ValueError("identifier needs generator review")
    return value


def operation_name(path: str, op: dict) -> str:
    return identifier(op.get("operationId") or METHOD_NAMES[path])


def title(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[^A-Za-z0-9]+", value) if part)


def merge_schema(obj: dict, schemas: dict) -> dict:
    if "$ref" in obj:
        return merge_schema(schemas[obj["$ref"].split("/")[-1]], schemas)
    if "allOf" not in obj:
        return obj
    properties, required = {}, set()
    for child in obj["allOf"]:
        part = merge_schema(child, schemas)
        for name, definition in part.get("properties", {}).items():
            if name in properties and properties[name] != definition:
                raise ValueError("conflicting response properties")
            properties[name] = definition
        required.update(part.get("required", []))
    return {"type": "object", "properties": properties, "required": sorted(required)}


class Models:
    def __init__(self, schemas):
        self.schemas = schemas
        self.lines = []
        self.seen = {}

    def expr(self, obj: dict, hint: str) -> str:
        if "$ref" in obj:
            return identifier(obj["$ref"].split("/")[-1])
        if "const" in obj:
            return "Literal[" + repr(obj["const"]) + "]"
        if "enum" in obj and all(type(x) in {str, int, bool, type(None)} for x in obj["enum"]):
            return "Literal[" + ", ".join(repr(x) for x in obj["enum"]) + "]"
        alternatives = obj.get("oneOf", obj.get("anyOf"))
        if alternatives:
            return " | ".join(self.expr(child, hint + "Case" + str(i + 1)) for i, child in enumerate(alternatives))
        kind = obj.get("type")
        if isinstance(kind, list):
            return " | ".join(self.expr({**obj, "type": k, "nullable": False}, hint) for k in kind)
        if "allOf" in obj:
            return self.expr(merge_schema(obj, self.schemas), hint)
        if kind == "object":
            if "properties" in obj:
                result = self.register(hint, obj)
            else:
                extra = obj.get("additionalProperties")
                result = "dict[str, " + (self.expr(extra, hint + "Value") if isinstance(extra, dict) else "Any") + "]"
        elif kind == "array":
            result = "list[" + self.expr(obj.get("items", {}), hint + "Item") + "]"
        else:
            result = {"string": "str", "integer": "int", "number": "float", "boolean": "bool", "null": "None"}.get(kind, "Any")
        return result + (" | None" if obj.get("nullable") and result != "None" else "")

    def register(self, name: str, obj: dict) -> str:
        identifier(name)
        if name in self.seen:
            if self.seen[name] != obj:
                raise ValueError("model name collision")
            return name
        self.seen[name] = obj
        if obj.get("oneOf") or obj.get("anyOf"):
            expression = self.expr(obj, name)
            self.lines += [f"{name} = {expression}", "", ""]
            return name
        if obj.get("type") == "object" and "properties" not in obj:
            self.lines += [f"{name} = {self.expr(obj, name)}", "", ""]
            return name
        props, required = obj.get("properties", {}), set(obj.get("required", []))
        if not required <= set(props):
            raise ValueError("required fields lack definitions")
        annotations = {key: self.expr(value, name + title(key)) for key, value in props.items()}
        self.lines.append(f"class _{name}Required(TypedDict):")
        self.lines.extend([f"    {identifier(k)}: {v}" for k, v in annotations.items() if k in required] or ["    pass"])
        self.lines += ["", f"class {name}(_{name}Required, total=False):"]
        self.lines.extend([f"    {identifier(k)}: {v}" for k, v in annotations.items() if k not in required] or ["    pass"])
        self.lines += ["", ""]
        return name


def generate(spec: dict, name: str, digest: str) -> str:
    from client_compat import client_view
    spec = client_view(spec)
    schemas = spec["components"]["schemas"]
    models = Models(schemas)
    for schema_name, obj in schemas.items():
        models.register(schema_name, obj)
    for path, item in spec["paths"].items():
        op = item["get"]
        response_name = title(operation_name(path, op)) + "Response"
        obj = merge_schema(op["responses"]["200"]["content"]["application/json"]["schema"], schemas)
        models.register(response_name, obj)
    modes = schemas["Error"]["properties"].get("mode", {}).get("enum", [])
    lines = [f'"""{name} API models and operations: generated; do not edit."""',
             f"# Public spec SHA256: {digest}", "from __future__ import annotations", "",
             "import re", "from typing import Any, Literal, TypedDict, cast", "from urllib.parse import quote", "",
             f"API_BASE_URL = {spec['servers'][0]['url']!r}",
             f"ERROR_CODES = frozenset({schemas['Error']['properties']['code']['enum']!r})",
             f"ERROR_MODES = frozenset({modes!r})",
             f"UNSUPPORTED_REQUEST_HEADERS = {UNSUPPORTED_HEADERS!r}", "", ""] + models.lines
    lines += ["class GeneratedOperations:", '    """One request per call. No retries or automatic pagination."""', ""]
    for path, item in spec["paths"].items():
        op = item["get"]
        operation = operation_name(path, op)
        parameters = []
        for par in op.get("parameters", []):
            if par["in"] == "header":
                if par["name"] not in UNSUPPORTED_HEADERS.get(path, ()):
                    raise ValueError("new request header needs client review")
                continue
            identifier(par["name"])
            if par["in"] not in {"query", "path"} or par.get("schema", {}).get("type") != "string":
                raise ValueError("new parameter type needs generator review")
            parameters.append(par)
        required = [p for p in parameters if p.get("required")]
        optional = [p for p in parameters if not p.get("required")]
        args = ["self"] + [f"{p['name']}: str" for p in required]
        if optional:
            args += ["*"] + [f"{p['name']}: str | None = None" for p in optional]
        response_name = title(operation) + "Response"
        lines.append(f"    def {operation}({', '.join(args)}) -> {response_name}:")
        for par in required:
            arg = par["name"]
            lines += [f"        if not isinstance({arg}, str) or not {arg}.strip():",
                      '            raise ValueError("required parameter must be a nonempty string")']
        for par in parameters:
            pattern = par.get("schema", {}).get("pattern")
            if pattern:
                arg = par["name"]
                lines += [f"        if {arg} is not None and re.fullmatch({pattern!r}, {arg}, flags=re.ASCII) is None:",
                          '            raise ValueError("parameter does not match the documented format")']
        if path == "/article":
            lines += ['        if len(codes.split(",")) > 20 or any(not part.strip() for part in codes.split(",")):',
                      '            raise ValueError("codes must contain 1 to 20 nonempty codes")']
        path_expression = repr(path)
        for par in parameters:
            if par["in"] == "path":
                path_expression += f".replace('{{{par['name']}}}', quote({par['name']}, safe=''))"
        query = "{" + ", ".join(f"{p['name']!r}: {p['name']}" for p in parameters if p["in"] == "query") + "}"
        auth = op.get("security") != []
        lines += [f"        return cast({response_name}, self._request({path_expression}, {query}, authenticated={auth}))", ""]
    return "\n".join(lines) + "\n"


def expected(root: Path = ROOT) -> str:
    encoded = (root / "openapi/openapi.json").read_bytes()
    digest = hashlib.sha256(encoded).hexdigest()
    if json.loads((root / "config/schema-lock.json").read_text()) != {"public_spec_sha256": digest}:
        raise ValueError("public spec lock mismatch")
    project = json.loads((root / "config/project.json").read_text())
    return generate(json.loads(encoded), project["project_name"], digest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    from generate_js import outputs
    files = {OUTPUT.as_posix(): expected(), **outputs(ROOT)}
    for path, text in files.items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_text() != text:
                raise SystemExit("generated client differs from the canonical contract")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
    print("Python and JavaScript clients match the locked canonical contract.")


if __name__ == "__main__":
    main()
