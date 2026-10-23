"""Synthetic JavaScript policy negatives; no candidate execution or real keys."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_public import text_checks


class JavaScriptPolicyTests(unittest.TestCase):
    def test_split_and_escaped_hostnames_are_scanned(self):
        for source in ['const v = "lab" + ".invalid";', r'const v = "lab\u002einvalid";', r'const v = "lab\x2einvalid";']:
            self.assertIn('unapproved-host', text_checks(source, 'examples/demo.mjs'))

    def test_javascript_credential_literal_is_rejected(self):
        self.assertIn('credential-literal', text_checks('const apiKey = "invented-not-a-key";', 'clients/js/index.js'))

    def test_javascript_json_and_object_records_are_rejected(self):
        self.assertIn('javascript-record-literal', text_checks('const a = {price_usd: 19.9};', 'examples/demo.mjs'))
        self.assertIn('record-values', text_checks('const a = \'{"price_usd":19.9}\';', 'examples/demo.mjs'))

    def test_dynamic_templates_need_review(self):
        self.assertIn('javascript-dynamic-template', text_checks('const a = `synthetic ${value}`;', 'examples/demo.mjs'))

    def test_unknown_escape_literal_needs_review(self):
        self.assertIn('javascript-unanalysable-literal', text_checks('const a = "\\uZZZZ";', 'examples/demo.mjs'))

    def test_dynamic_code_and_decoders_need_review(self):
        self.assertIn('javascript-obfuscated-source', text_checks('const a = atob("synthetic");', 'examples/demo.mjs'))

    def test_public_links_are_exact_not_prefix_permissions(self):
        self.assertFalse(text_checks('https://luxdb.net/docs/api', 'README.md'))
        self.assertIn('unapproved-url', text_checks('https://luxdb.net/docs/api?key=synthetic', 'README.md'))

    def test_demo_url_mask_requires_exact_pointer_and_reviewed_value(self):
        import copy, json
        from check_public import inspection_text, TRUSTED_SCHEMA
        spec = copy.deepcopy(TRUSTED_SCHEMA["contract"])
        props = spec["components"]["schemas"]["Article"]["properties"]
        original = props["lv_url"]["example"]
        self.assertEqual(json.loads(inspection_text(json.dumps(spec), "openapi/openapi.json"))["components"]["schemas"]["Article"]["properties"]["lv_url"]["example"], "SYNTHETIC-APPROVED-URL")
        props["lv_url"]["example"] = original + "?synthetic=1"
        self.assertEqual(json.loads(inspection_text(json.dumps(spec), "openapi/openapi.json"))["components"]["schemas"]["Article"]["properties"]["lv_url"]["example"], original + "?synthetic=1")
        props["name"]["example"] = original
        self.assertEqual(json.loads(inspection_text(json.dumps(spec), "openapi/openapi.json"))["components"]["schemas"]["Article"]["properties"]["name"]["example"], original)

if __name__ == '__main__':
    unittest.main()
