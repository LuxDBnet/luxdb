"""Explicit reviewed rebaseline; never run from CI or automatic data sync.

This command records only requested policy permissions and changed-file hashes.
Owner approval and independent review are required; it cannot authorise publication.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import FILES
from schema_policy import (REVIEWED_PROSE_PATHS, approved_prose_paths, collect_keywords,
                           pointer_value, validate_contract)

ROOT = Path(__file__).resolve().parents[1]
DERIVED = {
    "README.md", "NOTICE.md", "SECURITY.md", "CONTRIBUTING.md", "MANIFEST.md",
    "docs/data-dictionary.md", "docs/houses.md", "docs/quickstart.md", "docs/api-compatibility.md", "docs/api-reference.md",
    "clients/python/src/luxdb_client/generated.py", "openapi/openapi.json",
    "config/schema-lock.json", "config/fixed-hashes.json",
}


def proposed_policy(spec: dict, previous: dict, *, adopt_reviewed_prose: bool = False, reviewed_prose_changes=()) -> dict:
    paths = list(approved_prose_paths(previous))
    if adopt_reviewed_prose:
        paths = list(REVIEWED_PROSE_PATHS)
    changed = {pointer for pointer in paths if pointer_value(spec, pointer) != pointer_value(previous["contract"], pointer)}
    if changed != set(reviewed_prose_changes):
        raise ValueError("changed approved prose requires exact explicit review pointers")
    policy = {"status": previous["status"], "keywords_by_path": collect_keywords(spec),
              "complex_enum_paths": previous["complex_enum_paths"], "contract": spec,
              "approved_prose_paths": paths}
    validate_contract(spec, policy)
    return policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-draft", action="store_true", required=True)
    parser.add_argument("--adopt-reviewed-prose", action="store_true", help="adopt only the five independently reviewed pointers")
    parser.add_argument("--changes", type=Path, help="private old/new hash audit outside the publication tree")
    parser.add_argument("--review-prose-change", action="append", default=[])
    parser.add_argument("--adopt-inventory", action="store_true")
    args = parser.parse_args()
    if args.changes and (args.changes.resolve() == ROOT or ROOT in args.changes.resolve().parents):
        raise SystemExit("private hash audit must stay outside the publication tree")
    old_policy = json.loads((ROOT / "config/schema-policy.json").read_text())
    old_fixed = json.loads((ROOT / "config/fixed-hashes.json").read_text())
    expected_paths = set(FILES) - DERIVED
    if set(old_fixed["sha256"]) != expected_paths and not args.adopt_inventory:
        raise SystemExit("inventory changes require separate review")
    spec = json.loads((ROOT / "openapi/openapi.json").read_text())
    policy = proposed_policy(spec, old_policy, adopt_reviewed_prose=args.adopt_reviewed_prose, reviewed_prose_changes=args.review_prose_change)
    (ROOT / "config/schema-policy.json").write_text(json.dumps(policy, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    hashes = {path: old_fixed["sha256"].get(path) for path in expected_paths}
    changes = []
    for path in sorted(expected_paths):
        digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if digest != hashes[path]:
            changes.append({"file": path, "old_sha256": hashes[path], "new_sha256": digest})
            hashes[path] = digest
    fixed = {**old_fixed, "sha256": hashes}
    (ROOT / "config/fixed-hashes.json").write_text(json.dumps(fixed, indent=2) + "\n")
    if args.changes:
        args.changes.write_text(json.dumps(changes, indent=2) + "\n")
    print(f"Reviewed rebaseline recorded: {len(changes)} changed hashes; unchanged entries preserved.")
    print("No publication performed or authorised.")


if __name__ == "__main__":
    main()
