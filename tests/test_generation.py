"""Determinism, source minimisation and explicitly limited draft acceptance."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_public_spec import sanitise
from generate_clients import generate, expected
from inventory import FILES, manifest
from render_public import outputs, render_houses
from check_public import tree_files


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.spec_bytes = (ROOT / "openapi/openapi.json").read_bytes()
        self.spec = json.loads(self.spec_bytes)
        self.config = json.loads((ROOT / "config/project.json").read_text())

    def test_generator_is_deterministic_and_current(self):
        digest = hashlib.sha256(self.spec_bytes).hexdigest()
        a = generate(self.spec, self.config["project_name"], digest)
        b = generate(self.spec, self.config["project_name"], digest)
        self.assertEqual(a, b)
        self.assertEqual(a, expected())
        self.assertEqual(a, (ROOT / "clients/python/src/luxdb_client/generated.py").read_text())
        compile(a, "generated", "exec")

    def test_all_local_references_resolve(self):
        def walk(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    ref = value["$ref"]
                    self.assertTrue(ref.startswith("#/components/schemas/"))
                    self.assertIn(ref.split("/")[-1], self.spec["components"]["schemas"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.spec)

    def test_canonical_validation_never_rewrites_prose_or_examples(self):
        source = copy.deepcopy(self.spec)
        source["info"]["description"] = "Synthetic canonical wording"
        source["info"]["x-synthetic-extra"] = "preserved"
        source["components"]["schemas"]["Article"]["example"] = "synthetic"
        exported = sanitise(source, self.config)
        self.assertIs(exported, source)
        self.assertEqual(exported["info"]["description"], "Synthetic canonical wording")
        self.assertIn("example", exported["components"]["schemas"]["Article"])

    def test_source_server_auth_and_route_changes_need_review(self):
        for mutate in (
            lambda obj: obj["servers"][0].update({"url": "https" + "://synthetic" + ".invalid"}),
            lambda obj: obj["security"].clear(),
            lambda obj: obj["paths"].update({"/synthetic": {}}),
            lambda obj: obj["paths"]["/openapi"]["get"].update({"security": [{"apiKey": []}]}),
        ):
            obj = copy.deepcopy(self.spec)
            mutate(obj)
            with self.assertRaises(ValueError):
                sanitise(obj, self.config)

    def test_manifest_is_exact_and_has_no_history(self):
        self.assertEqual((ROOT / "MANIFEST.md").read_text(), manifest())
        files, issues = tree_files(ROOT, checkout=True)
        self.assertEqual(issues, [])
        self.assertEqual(set(files), set(FILES))
        self.assertFalse(any(path == ".git" or path.startswith(".git/") for path in files))

    def test_dictionary_is_definitions_only_and_renders_current_sources(self):
        fields = json.loads((ROOT / "metadata/fields.json").read_text())
        self.assertEqual(set(fields), {"status", "updates", "tables", "specifications"})
        self.assertTrue(fields["tables"])
        for table in fields["tables"]:
            for field in table["fields"]:
                self.assertEqual(set(field), {"name", "type", "unit", "meaning", "enum", "empty"})
        for path, text in outputs().items():
            self.assertEqual((ROOT / path).read_text(), text)

    def test_house_renderer_handles_new_rows_but_has_no_live_feed(self):
        houses = json.loads((ROOT / "metadata/houses.json").read_text())
        houses["houses"].append({"code": "synthetic", "name": "Synthetic House"})
        text = render_houses(self.config["project_name"], houses)
        self.assertIn("Synthetic House", text)
        self.assertIn("auto-generated later", text)
        houses["status"] = "provisional"
        with self.assertRaises(ValueError):
            render_houses(self.config["project_name"], houses)

    def test_one_naming_source_updates_rendered_copy(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as directory:
            import shutil
            root = Path(directory) / "copy"
            shutil.copytree(ROOT, root)
            config = dict(self.config, project_name="Synthetic Project")
            (root / "config/project.json").write_text(json.dumps(config))
            rendered = outputs(root)
            for text in rendered.values():
                self.assertNotIn(self.config["project_name"], text)
            self.assertIn("Synthetic Project", rendered["README.md"])

    def test_null_schema_information_and_untyped_arrays_are_preserved(self):
        article = self.spec["components"]["schemas"]["Article"]["properties"]
        self.assertEqual(article["last_seen"]["type"], ["string", "null"])
        self.assertEqual(article["price"]["properties"]["by_storefront"]["items"]["properties"]["language"]["type"], ["string", "null"])
        generated = expected()
        self.assertIn("last_seen: str | None", generated)
        self.assertIn("history: list[dict[str, Any]]", generated)

    def test_offline_example_and_paid_consent_guard(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env.pop("LUXDB_API_KEY", None)
        offline = subprocess.run([sys.executable, "examples/demo.py"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(offline.returncode, 0, offline.stderr)
        self.assertIn("Synthetic offline response", offline.stdout)
        paid = subprocess.run([sys.executable, "examples/paid_item.py", "--code", "SYNTHETIC-ITEM"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(paid.returncode, 0)
        self.assertIn("explicit --accept-credit-usage", paid.stderr)

    def test_issues_off_and_local_readme_links_exist(self):
        import re
        self.assertEqual({p.name for p in (ROOT / ".github/ISSUE_TEMPLATE").iterdir()}, {"config.yml"})
        readme = (ROOT / "README.md").read_text()
        self.assertIn("The storefront and API are live", readme)
        self.assertIn("not affiliated with", readme)
        self.assertIn("does not mean discontinued", readme)
        for link in re.findall(r"\]\(([^)]+)\)", readme):
            if not link.startswith("https://luxdb.net/"):
                self.assertTrue((ROOT / link).is_file(), link)
        self.assertIn("MIT", (ROOT / "LICENSE").read_text())
        self.assertIn("CC-BY-4.0", (ROOT / "LICENSES/CC-BY-4.0.txt").read_text())


if __name__ == "__main__":
    unittest.main()
