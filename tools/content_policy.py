"""Bounded, non-executing inspection of strings and structured record values."""
from __future__ import annotations

import ast
import base64
import binascii
import json
import re
import unicodedata
from urllib.parse import unquote

UNKNOWN = object()
MAX_TEXT = 65536
MAX_VARIANTS = 256
CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "х": "x", "у": "y", "і": "i", "ј": "j", "ѕ": "s",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M",
    "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "Х": "X", "Α": "A", "Β": "B", "Ε": "E", "Η": "H",
    "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O",
    "Ρ": "P", "Τ": "T", "Χ": "X", "ο": "o", "ρ": "p",
    "․": ".", "。": ".", "｡": ".",
})
PAID_FIELDS = {"price", "price_local", "price_usd", "usd_ref", "availability", "history", "image_url", "media_url"}
TEXT_FIELDS = {"description", "description_short", "features", "care"}
SECRET_FIELDS = {"api_key", "apikey", "token", "access_token", "secret", "password", "authorization", "x-api-key"}


def normalise(text: str) -> str:
    return unicodedata.normalize("NFKC", text).translate(CONFUSABLES)


def value(node: ast.AST, depth: int = 0):
    if depth > 16:
        return UNKNOWN
    if isinstance(node, ast.Constant):
        obj = node.value
        return obj if not isinstance(obj, str) or len(obj) <= MAX_TEXT else UNKNOWN
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = value(node.left, depth + 1), value(node.right, depth + 1)
        if isinstance(left, str) and isinstance(right, str) and len(left) + len(right) <= MAX_TEXT:
            return left + right
        return UNKNOWN
    if isinstance(node, ast.JoinedStr):
        chunks = []
        for part in node.values:
            obj = value(part.value, depth + 1) if isinstance(part, ast.FormattedValue) and part.conversion == -1 and part.format_spec is None else value(part, depth + 1)
            if not isinstance(obj, str):
                return UNKNOWN
            chunks.append(obj)
        text = "".join(chunks)
        return text if len(text) <= MAX_TEXT else UNKNOWN
    if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) <= 128:
        return [value(part, depth + 1) for part in node.elts]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"float", "int", "str"} and len(node.args) == 1 and not node.keywords:
        arg = value(node.args[0], depth + 1)
        if type(arg) in {str, float, int, bool}:
            try:
                return {"float": float, "int": int, "str": str}[node.func.id](arg)
            except (ValueError, OverflowError):
                return UNKNOWN
    return UNKNOWN


def empty(obj: object) -> bool:
    return obj is None or isinstance(obj, (str, list, dict)) and len(obj) == 0


def placeholder(obj: object) -> bool:
    return isinstance(obj, str) and (obj == "demo" or obj.startswith("SYNTHETIC-"))


def record_categories(obj: object) -> set[str]:
    result = set()
    if isinstance(obj, dict):
        for key, item in obj.items():
            if key in PAID_FIELDS or key in TEXT_FIELDS and "article" in obj:
                if not empty(item):
                    result.add("record-values")
            if isinstance(key, str) and normalise(key).lower() in SECRET_FIELDS and isinstance(item, str) and not placeholder(item):
                result.add("credential-literal")
            result.update(record_categories(item))
    elif isinstance(obj, list):
        for item in obj:
            result.update(record_categories(item))
    return result


def inspect_python(text: str) -> tuple[set[str], list[str]]:
    result, strings = set(), []
    try:
        tree = ast.parse(text)
    except (SyntaxError, RecursionError):
        return {"invalid-python"}, strings
    for node in ast.walk(tree):
        obj = value(node)
        if isinstance(obj, str):
            strings.append(obj)
        if isinstance(node, ast.Dict):
            pairs = [(value(k), value(v)) for k, v in zip(node.keys, node.values) if k is not None]
            keys = {k for k, _ in pairs if isinstance(k, str)}
            for key, item in pairs:
                if isinstance(key, str) and (key in PAID_FIELDS or key in TEXT_FIELDS and "article" in keys):
                    if item is UNKNOWN:
                        result.add("dynamic-record-value")
                    elif not empty(item):
                        result.add("record-literal")
                if isinstance(key, str) and normalise(key).lower() in SECRET_FIELDS and isinstance(item, str) and not placeholder(item):
                    result.add("credential-literal")
        target_names = []
        if isinstance(node, ast.keyword) and node.arg:
            target_names = [node.arg]
            obj = value(node.value)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_names = [t.id if isinstance(t, ast.Name) else t.attr for t in targets if isinstance(t, (ast.Name, ast.Attribute))]
            obj = value(node.value)
        if any(normalise(name).lower() in SECRET_FIELDS for name in target_names):
            if isinstance(obj, str) and not placeholder(obj):
                result.add("credential-literal")
            elif obj is UNKNOWN and not isinstance(node.value, ast.Name):
                result.add("dynamic-credential-value")
    return result, strings


def variants(text: str):
    queue, seen = [(text, 0)], set()
    while queue and len(seen) < MAX_VARIANTS:
        original, depth = queue.pop(0)
        if len(original) > MAX_TEXT or original in seen:
            continue
        seen.add(original)
        yield original
        if depth >= 3:
            continue
        transformed = normalise(original)
        if transformed != original:
            queue.append((transformed, depth + 1))
        if re.search(r"%[a-fA-F0-9]{2}", original):
            decoded = unquote(original)
            if decoded != original:
                queue.append((decoded, depth + 1))
        stripped = original.strip()
        if 8 <= len(stripped) <= 4096 and re.fullmatch(r"[A-Za-z0-9+/_-]+={0,2}", stripped):
            try:
                raw = base64.b64decode(stripped.translate(str.maketrans("-_", "+/")) + "=" * (-len(stripped) % 4), validate=True)
                decoded = raw.decode("utf-8")
                if decoded and all(c.isprintable() or c in "\n\r\t" for c in decoded):
                    queue.append((decoded, depth + 1))
            except (binascii.Error, UnicodeError, ValueError):
                pass
        if 8 <= len(stripped) <= 8192 and len(stripped) % 2 == 0 and re.fullmatch(r"[a-fA-F0-9]+", stripped):
            try:
                decoded = bytes.fromhex(stripped).decode("utf-8")
                if decoded and all(c.isprintable() or c in "\n\r\t" for c in decoded):
                    queue.append((decoded, depth + 1))
            except (ValueError, UnicodeError):
                pass


def inspect_strings(strings: list[str], check_text) -> set[str]:
    result = set()
    # Every literal gets its own bounded decoding queue; one large file cannot
    # exhaust a shared queue and hide later literals.
    for literal in strings:
        for decoded in variants(literal):
            result.update(check_text(decoded))
            try:
                obj = json.loads(decoded)
            except (ValueError, RecursionError):
                continue
            result.update(record_categories(obj))
            # JSON strings may themselves hold encoded JSON or host names.
            if isinstance(obj, str) and obj != decoded:
                for inner in variants(obj):
                    result.update(check_text(inner))
                    try:
                        result.update(record_categories(json.loads(inner)))
                    except (ValueError, RecursionError):
                        pass
    return result


def json_strings(obj: object):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, child in obj.items():
            yield key
            yield from json_strings(child)
    elif isinstance(obj, list):
        for child in obj:
            yield from json_strings(child)
