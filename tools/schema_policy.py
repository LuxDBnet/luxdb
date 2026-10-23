"""Typed, path-specific public contract approval, independent of export/sync.

A policy change is a semantic-review decision, never an automatic consequence of
regenerating a spec hash or an SDK. The draft policy awaits API-owner acceptance.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REVIEWED_PROSE_PATHS = (
    "/components/schemas/Article/properties/article/description",
    "/components/schemas/SearchRow/properties/article/description",
    "/components/schemas/Article/properties/family_id/description",
    "/components/schemas/SearchRow/properties/family_id/description",
    "/paths/~1resolve/get/parameters/0/description",
)

SCHEMA_KEYWORDS = {
    "$ref", "type", "format", "nullable", "minimum", "maximum", "minItems",
    "maxItems", "minLength", "maxLength", "uniqueItems", "enum", "required",
    "properties", "$defs", "items", "additionalProperties", "not",
    "allOf", "anyOf", "oneOf", "description", "title", "pattern", "const", "example",
}


class PolicyError(ValueError):
    pass


def check_schema(node: object, path: str, approved: dict[str, list[str]], complex_enums: set[str]) -> None:
    if isinstance(node, bool):
        return
    if not isinstance(node, dict) or path not in approved:
        raise PolicyError("schema path is not approved")
    if set(node) != set(approved[path]) or set(node) - SCHEMA_KEYWORDS:
        raise PolicyError("schema keywords need path-specific review")
    for key, value in node.items():
        if key == "enum":
            if not isinstance(value, list) or not value:
                raise PolicyError("invalid enum")
            if any(isinstance(v, (dict, list)) for v in value) and path not in complex_enums:
                raise PolicyError("record-bearing enum is not approved")
        elif key in {"const", "example"}:
            if type(value) not in {str, int, float, bool, type(None)}:
                raise PolicyError("structured example or constant requires separate review")
        elif key == "required":
            if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
                raise PolicyError("required must be field names")
        elif key in {"type", "format", "$ref", "description", "title", "pattern"}:
            if key == "type" and isinstance(value, list):
                if not value or any(not isinstance(v, str) for v in value):
                    raise PolicyError("invalid type union")
            elif not isinstance(value, str):
                raise PolicyError("invalid string schema keyword")
        elif key in {"nullable", "uniqueItems"}:
            if type(value) is not bool:
                raise PolicyError("invalid boolean schema keyword")
        elif key in {"minimum", "maximum"}:
            if type(value) not in {int, float}:
                raise PolicyError("invalid numeric schema keyword")
        elif key in {"minItems", "maxItems", "minLength", "maxLength"}:
            if type(value) is not int or value < 0:
                raise PolicyError("invalid size schema keyword")
        elif key in {"properties", "$defs"}:
            if not isinstance(value, dict):
                raise PolicyError("invalid property map")
            for name, child in value.items():
                if not isinstance(name, str):
                    raise PolicyError("invalid property name")
                check_schema(child, path + "/" + key + "/" + name, approved, complex_enums)
        elif key in {"items", "additionalProperties", "not"}:
            check_schema(value, path + "/" + key, approved, complex_enums)
        elif key in {"allOf", "anyOf", "oneOf"}:
            if not isinstance(value, list) or not value:
                raise PolicyError("invalid schema alternatives")
            for i, child in enumerate(value):
                check_schema(child, path + "/" + key + "/" + str(i), approved, complex_enums)


def schema_roots(spec: dict):
    for name, node in spec["components"]["schemas"].items():
        yield "/components/schemas/" + name, node
    for path, item in spec["paths"].items():
        for method, op in item.items():
            prefix = "/paths/" + path + "/" + method
            for i, par in enumerate(op.get("parameters", [])):
                yield prefix + "/parameters/" + str(i) + "/schema", par["schema"]
            for code, response in op["responses"].items():
                for kind, obj in response.get("content", {}).items():
                    yield prefix + "/responses/" + code + "/content/" + kind + "/schema", obj["schema"]
                for name, header in response.get("headers", {}).items():
                    if "schema" in header:
                        yield prefix + "/responses/" + code + "/headers/" + name + "/schema", header["schema"]


def collect_keywords(spec: dict) -> dict[str, list[str]]:
    result = {}
    def walk(node, path):
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            raise PolicyError("invalid source schema")
        result[path] = sorted(node)
        for key, value in node.items():
            if key in {"properties", "$defs"}:
                for name, child in value.items():
                    walk(child, path + "/" + key + "/" + name)
            elif key in {"items", "additionalProperties", "not"}:
                walk(value, path + "/" + key)
            elif key in {"allOf", "anyOf", "oneOf"}:
                for i, child in enumerate(value):
                    walk(child, path + "/" + key + "/" + str(i))
    for path, node in schema_roots(spec):
        walk(node, path)
    return result


def exact_typed(actual: object, approved: object) -> bool:
    if type(actual) is not type(approved):
        return False
    if isinstance(actual, dict):
        return set(actual) == set(approved) and all(exact_typed(actual[k], approved[k]) for k in actual)
    if isinstance(actual, list):
        return len(actual) == len(approved) and all(exact_typed(a, b) for a, b in zip(actual, approved))
    return actual == approved


def pointer_parent(document: object, pointer: str):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise PolicyError("invalid JSON pointer")
    parts = pointer[1:].split("/")
    if any(re.search(r"~(?![01])", part) for part in parts):
        raise PolicyError("invalid JSON pointer escape")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in parts]
    node = document
    for i, part in enumerate(parts):
        if isinstance(node, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", part):
                raise PolicyError("invalid array index")
            key = int(part)
            if key >= len(node):
                raise PolicyError("array index is absent")
        elif isinstance(node, dict):
            key = part
            if key not in node:
                raise PolicyError("pointer is absent")
        else:
            raise PolicyError("pointer is not a container")
        if i == len(parts) - 1:
            return node, key
        node = node[key]
    raise PolicyError("empty JSON pointer")


def pointer_value(document: object, pointer: str):
    node, key = pointer_parent(document, pointer)
    return node[key]


def approved_prose_paths(policy: dict) -> list[str]:
    paths = policy.get("approved_prose_paths", [])
    if not isinstance(paths, list) or any(type(path) is not str for path in paths):
        raise PolicyError("prose paths must be a string list")
    if len(paths) != len(set(paths)):
        raise PolicyError("duplicate prose path")
    if paths and set(paths) != set(REVIEWED_PROSE_PATHS):
        raise PolicyError("prose path set needs separate review")
    for path in paths:
        if type(pointer_value(policy["contract"], path)) is not str:
            raise PolicyError("approved prose must be a string node")
    return paths


def validate_contract(spec: dict, policy: dict) -> None:
    required_keys = {"status", "keywords_by_path", "complex_enum_paths", "contract"}
    if set(policy) not in (required_keys, required_keys | {"approved_prose_paths"}) or policy["status"] not in {"draft_waiting_for_api_owner", "canonical_copy_review_pending"}:
        raise PolicyError("unapproved policy format")
    approved_prose_paths(policy)
    roots = list(schema_roots(spec))
    for path, node in roots:
        check_schema(node, path, policy["keywords_by_path"], set(policy["complex_enum_paths"]))
    # This also fixes each path's enum contents, reference, constraints, names and
    # document layout. SDK/spec hash equality alone is not publication approval.
    if not exact_typed(spec, policy["contract"]):
        raise PolicyError("contract semantics differ from reviewed path policy")


def read_policy(root: Path) -> dict:
    return json.loads((root / "config/schema-policy.json").read_text())
