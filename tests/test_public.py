"""Negative pre-upload tests. Injected material is fabricated, never real data."""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_public import scan, main as scanner_main
from stage_public import stage
from inventory import FILES


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.copy = self.parent / "candidate"
        self.copy.mkdir()
        for rel in FILES:
            target = self.copy / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, target)
        self.baseline = set(scan(self.copy))
        for finding in self.baseline:
            declared = finding.category == "upstream-copy" and finding.path.startswith(("openapi/openapi.json/", "metadata/fields.json/"))
            canonical_example = finding.category in {"real-shaped-item-code", "unapproved-host", "unapproved-url"} and finding.path in {"openapi/openapi.json", "config/schema-policy.json"}
            self.assertTrue(declared or canonical_example, finding)

    def categories(self):
        return {issue.category for issue in set(scan(self.copy)) - self.baseline}

    def append(self, text, path="NOTICE.md"):
        with (self.copy / path).open("a") as stream:
            stream.write("\n" + text + "\n")

    def mutate_json(self, path, fn):
        target = self.copy / path
        obj = json.loads(target.read_text())
        fn(obj)
        target.write_text(json.dumps(obj, indent=2) + "\n")

    def test_definition_tree_retains_declared_upstream_blockers(self):
        self.assertEqual(set(scan(self.copy)), self.baseline)
        if self.baseline:
            self.assertTrue(any(f.category == "upstream-copy" for f in self.baseline))

    def test_49_character_key_shape_and_agent_marker(self):
        fake = "luxdb_" + "x" * 43
        self.append("value = " + repr(fake), "examples/demo.py")
        self.assertIn("key-shape-49", self.categories())
        self.append("label = " + repr("private-session-fictional"), "examples/demo.py")
        self.assertIn("internal-agent-name", self.categories())

    def test_round_two_semantic_boundaries(self):
        from check_public import plain_checks, text_checks
        import base64
        cases = [("reviewer@example.edu", "foreign-email"),
                 ("localhost:3200", "unapproved-host"),
                 ("127.0.0.1:3200", "ip-address"),
                 ("10.0.0.1:3200", "ip-address"),
                 ("172.16.0.1:3200", "ip-address"),
                 ("192.168.0.1:3200", "ip-address")]
        cases += [("synthetic." + suffix, "unapproved-host") for suffix in ("lan", "corp", "internal", "local")]
        cases += [("/" + part + "/synthetic", "internal-path") for part in ("home", "opt", "srv", "var")]
        for value, category in cases:
            with self.subTest(value=value):
                self.assertIn(category, plain_checks(value, "NOTICE.md"))
                encoded = base64.b64encode(value.encode()).decode()
                self.assertIn(category, text_checks(encoded, "NOTICE.md"))
        self.assertNotIn("foreign-email", plain_checks("support@luxdb.net", "NOTICE.md"))

    def test_private_key_pattern(self):
        header = "-----" + "BEGIN " + "PRIVATE KEY-----"
        self.append(header)
        self.assertIn("secret-pattern", self.categories())

    def test_entropy_and_credential_literals(self):
        invented = hashlib.sha256(b"fabricated test, not a credential").hexdigest()
        assignment = "api_" + "key = " + repr(invented)
        self.append(assignment, "examples/demo.py")
        categories = self.categories()
        self.assertIn("high-entropy-secret", categories)
        self.assertIn("credential-literal", categories)

    def test_unapproved_host_url_port_and_ip(self):
        host = "synthetic" + ".invalid"
        self.append("https" + "://" + host + ":1234/" + " " + "10" + ".0.0.1")
        self.assertTrue({"unapproved-url", "unapproved-host", "ip-address"} <= self.categories())

    def test_private_path_and_signed_url(self):
        self.append("/" + "home/" + "synthetic/" + " " + "https" + "://luxdb.net/media/synthetic?signature=synthetic")
        self.assertTrue({"internal-path", "unapproved-url"} <= self.categories())

    def test_ipv6_and_provider_key_patterns(self):
        self.append(":" + ":1")
        self.assertIn("ip-address", self.categories())
        self.append("ghp" + "_" + "SyntheticInventedNotACredential")
        self.assertIn("secret-pattern", self.categories())

    def test_spec_examples_paid_fields_and_media_are_blocked(self):
        def mutate(spec):
            spec["components"]["schemas"]["Article"]["example"] = dict([( "article", "SYNTHETIC-ITEM"), ("price_" + "usd", 19.9)])
            spec["components"]["schemas"]["Article"]["properties"]["gallery"]["default"] = "synthetic-only"
        self.mutate_json("openapi/openapi.json", mutate)
        self.assertIn("unsafe-spec-structure", self.categories())

    def test_paid_record_literals_are_blocked(self):
        payload = json.dumps(dict([("price_" + "usd", 19.9)]))
        self.append("payload = " + payload, "examples/demo.py")
        self.assertIn("record-literal", self.categories())

    def test_fixture_cannot_become_a_dataset(self):
        def mutate(fixture):
            fixture["response"]["results"] = [{"article": "SYNTHETIC-ITEM"}]
        self.mutate_json("tests/fixtures/synthetic-response.json", mutate)
        self.assertIn("non-synthetic-fixture", self.categories())

    def test_real_shaped_code_in_docs_is_blocked(self):
        self.append("M" + "00001")
        self.assertIn("real-shaped-item-code", self.categories())

    def test_files_images_history_and_symlinks_are_blocked(self):
        for name in ("synthetic.png", "synthetic.csv", ".env", "extra.md"):
            (self.copy / name).write_bytes(b"synthetic")
        (self.copy / ".git").mkdir()
        (self.copy / "linked.md").symlink_to(self.copy / "README.md")
        self.assertTrue({"unapproved-file", "unapproved-directory", "symlink"} <= self.categories())

    def test_embedded_media_binary_and_pictographs(self):
        self.append("<" + "img src='synthetic'>" + chr(0x1F600))
        self.assertTrue({"embedded-media", "pictograph"} <= self.categories())
        self.append("\x00")
        self.assertIn("binary-content", self.categories())

    def test_external_ref_and_new_route_blocked(self):
        def mutate(spec):
            spec["components"]["schemas"]["Article"]["properties"]["price"] = {"$ref": "synthetic" + ".json"}
        self.mutate_json("openapi/openapi.json", mutate)
        self.assertIn("invalid-bundle-or-lock", self.categories())
        def add_route(spec):
            spec["paths"]["/synthetic-private"] = {"get": {}}
        self.mutate_json("openapi/openapi.json", add_route)
        self.assertIn("invalid-bundle-or-lock", self.categories())

    def test_extra_metadata_and_unapproved_house_blocked(self):
        self.mutate_json("metadata/fields.json", lambda obj: obj.update({"records": []}))
        self.assertIn("dictionary-policy", self.categories())
        self.mutate_json("metadata/houses.json", lambda obj: obj["houses"].append({"code": "synthetic", "name": "Synthetic House"}))
        self.assertIn("unapproved-house-snapshot", self.categories())

    def test_scanner_output_does_not_echo_payload(self):
        invented = hashlib.sha256(b"another fabricated credential").hexdigest()
        self.append(invented)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), patch.object(sys, "argv", ["check_public", "--root", str(self.copy)]):
            with self.assertRaises(SystemExit) as caught:
                scanner_main()
        self.assertEqual(caught.exception.code, 1)
        self.assertNotIn(invented, out.getvalue())
        self.assertNotIn(str(self.copy), out.getvalue())

    def test_staging_never_copies_history(self):
        git = self.copy / ".git"
        git.mkdir()
        (git / "synthetic-history").write_text("synthetic")
        destination = self.parent / "staged"
        if self.baseline:
            with self.assertRaises(ValueError):
                stage(self.copy, destination, checkout=True)
        else:
            stage(self.copy, destination, checkout=True)
        self.assertFalse((destination / ".git").exists())
        self.assertEqual(set(scan(destination)), self.baseline)
        with self.assertRaises(ValueError):
            stage(self.copy, destination, checkout=True)

    def test_staging_rejects_unapproved_file_and_symlink(self):
        (self.copy / "extra.json").write_text("{}")
        with self.assertRaises(ValueError):
            stage(self.copy, self.parent / "rejected")
        self.assertFalse((self.parent / "rejected").exists())

    def test_staging_source_and_destination_are_separate(self):
        with self.assertRaises(ValueError):
            stage(self.copy, self.copy / "nested")


if __name__ == "__main__":
    unittest.main()
