"""Tests for the supplied canonical contract and current public definitions."""
import copy
import hashlib
import json
import sys
import typing
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "clients/python/src"))
from audit_canonical import inspect_contract
from export_dictionary import project
from check_public import inspection_text, text_checks, plain_checks
from schema_policy import (REVIEWED_PROSE_PATHS, PolicyError, approved_prose_paths,
                           pointer_parent, pointer_value, validate_contract)
from update_reviewed_policy import proposed_policy
from luxdb_client import ApiError, Client, Response
from luxdb_client import generated as models


class OneResponse:
    def __init__(self, value, status=200):
        self.value, self.status, self.calls = value, status, 0
    def send(self, request):
        self.calls += 1
        return Response(self.status, {}, json.dumps(self.value).encode())


class CanonicalTests(unittest.TestCase):
    def test_exact_supplied_contract_digest(self):
        sources = json.loads((ROOT / "config/sources.json").read_text())
        self.assertEqual(hashlib.sha256((ROOT / "openapi/openapi.json").read_bytes()).hexdigest(), sources["openapi_sha256"])

    def test_fields_digest_is_masked_only_at_its_reviewed_node(self):
        for path in ("openapi/openapi.json", "config/schema-policy.json"):
            with self.subTest(path=path):
                document = json.loads((ROOT / path).read_text())
                viewed = json.loads(inspection_text(json.dumps(document), path))
                contract = viewed["contract"] if path == "config/schema-policy.json" else viewed
                self.assertEqual(contract["info"]["x-luxdb-fields"], "SYNTHETIC-APPROVED-DIGEST")
                self.assertNotIn("high-entropy-secret", text_checks(json.dumps(contract), "openapi/openapi.json"))

    def test_fields_digest_changes_and_relocation_remain_scanned(self):
        for path in ("openapi/openapi.json", "config/schema-policy.json"):
            for change in ("replace", "relocate"):
                with self.subTest(path=path, change=change):
                    document = json.loads((ROOT / path).read_text())
                    contract = document["contract"] if path == "config/schema-policy.json" else document
                    digest = contract["info"]["x-luxdb-fields"]
                    if change == "replace":
                        contract["info"]["x-luxdb-fields"] = ("0" if digest[0] != "0" else "1") + digest[1:]
                    else:
                        contract["info"]["x-synthetic-extra"] = digest
                    viewed = json.loads(inspection_text(json.dumps(document), path))
                    viewed_contract = viewed["contract"] if path == "config/schema-policy.json" else viewed
                    key = "x-luxdb-fields" if change == "replace" else "x-synthetic-extra"
                    self.assertEqual(viewed_contract["info"][key], contract["info"][key])
                    self.assertIn("high-entropy-secret", text_checks(json.dumps(viewed_contract), "openapi/openapi.json"))

    def test_public_names_and_nullable_storefront_language(self):
        article = typing.get_type_hints(models.Article)
        spec = json.loads((ROOT / "openapi/openapi.json").read_text())["components"]["schemas"]
        self.assertIn("page_checked_snapshot", article)
        self.assertEqual(set(article), set(spec["Article"]["properties"]))
        counters = typing.get_type_hints(models.ArticleCounters)
        self.assertIn("photos_additional", counters)
        self.assertEqual(set(counters), set(spec["Article"]["properties"]["counters"]["properties"]))
        self.assertEqual(typing.get_type_hints(models.ArticlePriceByStorefrontItem)["language"], str | None)
        self.assertEqual(set(typing.get_args(article["features_source"])), {"page", "house_api", "same_model", "carried", None})
        self.assertEqual(set(typing.get_args(article["record_completeness"])), {"full", "partial", "catalog_only", "thin"})
        self.assertEqual(article["family_sizes"], list[str])

    def test_family_and_resolve_wrappers_and_union_cases(self):
        self.assertIn("family", models.FamilyResponse.__required_keys__)
        self.assertIn("resolved", models.ResolveResponse.__required_keys__)
        self.assertEqual(typing.get_type_hints(models.FamilyResponse)["family"], models.Family)
        cases = typing.get_args(models.Resolved)
        self.assertEqual(len(cases), 5)
        statuses = {typing.get_args(typing.get_type_hints(case)["status"])[0] for case in cases}
        self.assertEqual(statuses, {"product", "family", "variant", "not_in_catalog", "unrecognized_url"})
        transport = OneResponse({"family": {"family_id": "nvprod0v", "articles": []}})
        self.assertEqual(Client(transport=transport).family("nvprod0v")["family"]["articles"], [])
        self.assertEqual(transport.calls, 1)
        for status in statuses:
            response = OneResponse({"resolved": {"status": status}})
            self.assertEqual(Client(transport=response).resolve("synthetic-link")["resolved"]["status"], status)

    def test_402_and_service_mode(self):
        for code in ("payment_required", "member_limit_reached"):
            with self.assertRaises(ApiError) as caught:
                Client(transport=OneResponse({"code": code}, 402)).article("SYNTHETIC-ITEM")
            self.assertEqual(caught.exception.code, code)
        for mode in ("maintenance", "stopped", "SYNTHETIC-UNKNOWN"):
            with self.assertRaises(ApiError) as caught:
                Client(transport=OneResponse({"code": "maintenance", "mode": mode}, 503)).snapshot()
            self.assertEqual(caught.exception.mode, mode if mode != "SYNTHETIC-UNKNOWN" else None)
        self.assertEqual(models.ERROR_MODES, {"maintenance", "stopped"})

    def test_nullable_types_come_from_the_unmodified_contract(self):
        from client_compat import client_view
        original = json.loads((ROOT / "openapi/openapi.json").read_text())
        view = client_view(original)
        self.assertEqual(original["components"]["schemas"]["SearchRow"]["properties"]["price_usd_band"]["type"], ["string", "null"])
        self.assertEqual(view, original)
        self.assertIsNot(view, original)
        self.assertEqual(typing.get_type_hints(models.SearchRow)["price_usd_band"], str | None)
        dims = typing.get_type_hints(models.ArticleDimensions)
        self.assertEqual(dims["height_cm"], float | None)
        self.assertEqual(dims["height_in"], float | None)
        self.assertEqual(view["components"]["schemas"]["Article"]["properties"]["dimensions"]["properties"]["height_cm"]["type"], ["number", "null"])
        nullable = {"results": [{"price_usd_band": None}]}
        self.assertIsNone(Client(transport=OneResponse(nullable)).search()["results"][0]["price_usd_band"])

    def test_size_set_main_and_sandbox_prices_parse_without_losing_fields(self):
        card = {
            "article": "SYNTHETIC-MAIN",
            "size_set": [
                {"code": "SYNTHETIC-MAIN", "size_label": "S", "size_scale": "alpha",
                 "size_order": 1, "display_label": "Size S", "self": True, "regions": []},
                {"code": "SYNTHETIC-MEMBER", "size_label": "M", "size_scale": "alpha",
                 "size_order": None, "display_label": "Size M", "self": False,
                 "regions": [{"region": "synthetic_en", "availability": None, "priced": True}]},
            ],
            "price": {"countries": None, "by_storefront": [
                {"article": "SYNTHETIC-MEMBER", "size_display": "Size M"},
                {"article": None, "size_display": "Size M"},
            ]},
        }
        body = {"credits_charged": 0, "results": {"SYNTHETIC-MAIN": {"status": "ok", "article": card}}}
        transport = OneResponse(body)
        result = Client(transport=transport).article("SYNTHETIC-MAIN")
        self.assertEqual(result, body)
        self.assertEqual(transport.calls, 1)
        self.assertIsNone(result["results"]["SYNTHETIC-MAIN"]["article"]["price"]["by_storefront"][1]["article"])
        sandbox = copy.deepcopy(body)
        sandbox["results"]["SYNTHETIC-MAIN"]["article"]["size_set"][1]["code"] = None
        self.assertEqual(Client(transport=OneResponse(sandbox)).article("SYNTHETIC-MAIN"), sandbox)
        hints = typing.get_type_hints(models.Article)
        self.assertEqual(hints["size_set"], list[models.ArticleSizeSetItem] | None)
        size = typing.get_type_hints(models.ArticleSizeSetItem)
        self.assertEqual(size["size_order"], float | None)
        self.assertEqual(size["code"], str | None)
        self.assertEqual(set(models.ArticleSizeSetItem.__required_keys__), set(size))
        price = typing.get_type_hints(models.ArticlePriceByStorefrontItem)
        self.assertEqual(price["article"], str | None)
        self.assertEqual(price["size_display"], str | None)
        self.assertEqual(typing.get_type_hints(models.ArticlePrice)["countries"], int | None)

    def test_extra_error_keys_and_plain_404_405(self):
        for status, code in [(404, "not_found"), (405, "method_not_allowed")]:
            obj = {"code": code, "error": "synthetic", "hint": "synthetic", "batch_max": 20, "brands": [], "plan": "synthetic", "sandbox": True, "remaining_today": 0}
            with self.assertRaises(ApiError) as caught:
                Client(transport=OneResponse(obj, status)).snapshot()
            self.assertEqual(caught.exception.details, obj)
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn("synthetic", str(caught.exception))

    def test_current_public_dictionary_shape(self):
        data = json.loads((ROOT / "metadata/fields.json").read_text())
        self.assertEqual(set(data), {"status", "updates", "tables", "specifications"})
        names = {(table["name"], field["name"]) for table in data["tables"] for field in table["fields"]}
        self.assertIn(("product_client", "page_checked_snapshot"), names)
        self.assertIn(("product_stats", "photos_additional"), names)
        self.assertTrue(all(set(field) == {"name", "type", "unit", "meaning", "enum", "empty"} for table in data["tables"] for field in table["fields"]))
        for table in data["tables"]:
            self.assertEqual(set(table), {"name", "title", "fields"})
            for field in table["fields"]:
                self.assertEqual(set(field), {"name", "type", "unit", "meaning", "enum", "empty"})
        self.assertNotIn("filled_by_house", json.dumps(data))

    def test_dictionary_export_uses_public_names_and_omits_hidden_fields(self):
        source = {"tables": [{"name": "product_client", "rows": 99, "fields": [
            {"name": "raw_label", "public_name": "label", "hidden": False, "type": "text", "unit": "", "doc": "A short label.", "enum": [], "empty": "a", "filled": 99},
            {"name": "not_exported", "public_name": "not_exported", "hidden": True}
        ]}], "spec_keys": {}}
        output, _ = project(source)
        self.assertEqual([f["name"] for f in output["tables"][0]["fields"]], ["label"])
        self.assertNotIn("raw_label", json.dumps(output))
        self.assertNotIn("rows", output["tables"][0])
        self.assertNotIn("filled", output["tables"][0]["fields"][0])

    def test_brand_description_is_not_permitted_by_demo_membership(self):
        spec = json.loads((ROOT / "openapi/openapi.json").read_text())
        demo = json.loads((ROOT / "config/public-demo.json").read_text())
        props = spec["components"]["schemas"]["Article"]["properties"]
        props["article"]["example"] = demo["articles"][0]["article"]
        props["description"]["example"] = "Unapproved sample wording for a fabricated test."
        props["name_local"]["example"] = "SYNTHETIC-NAME"
        findings = inspect_contract(spec, demo)["findings"]
        self.assertTrue(any(f["pointer"].endswith("/properties/description/example") and "brand-text" in f["kind"] for f in findings))
        self.assertFalse(any(f["pointer"].endswith("/properties/name_local/example") and "brand-text" in f["kind"] for f in findings))

    def test_post_0241_storefront_price_types(self):
        row = typing.get_type_hints(models.ArticlePriceByStorefrontItem)
        self.assertEqual(row["last_checked_week"], str | None)
        self.assertEqual(row["local"], str | None)
        self.assertEqual(row["usd"], float | None)
        self.assertEqual(set(typing.get_args(row["state"])), {"current", "withdrawn", "not_checked"})

    def test_protocol_header_and_exact_placeholder_are_not_copy_leaks(self):
        spec = json.loads((ROOT / "openapi/openapi.json").read_text())
        demo = json.loads((ROOT / "config/public-demo.json").read_text())
        findings = inspect_contract(spec, demo)["findings"]
        for field in ("description", "description_short"):
            pointer = "/components/schemas/Article/properties/" + field + "/example"
            self.assertFalse(any(f["pointer"] == pointer and "brand-text" in f["kind"] for f in findings))
        header_pointer = "/components/schemas/Envelope/properties/snapshot/description"
        self.assertFalse(any(f["pointer"] == header_pointer for f in findings))
        spec["components"]["schemas"]["Envelope"]["properties"]["snapshot"]["description"] = "A weekly snapshot. Also X-Data-Snapshot."
        self.assertTrue(any(f["pointer"] == header_pointer for f in inspect_contract(spec, demo)["findings"]))

    def test_public_protocol_copy_is_allowed_without_masking_internal_additions(self):
        spec = json.loads((ROOT / "openapi/openapi.json").read_text())
        demo = json.loads((ROOT / "config/public-demo.json").read_text())
        self.assertEqual(inspect_contract(spec, demo)["findings"], [])
        spec["info"]["description"] += " PDP internal collection per address."
        findings = inspect_contract(spec, demo)["findings"]
        self.assertTrue(any(f["pointer"] == "/info/description" for f in findings))
        header = spec["paths"]["/article"]["get"]["responses"]["200"]["headers"]["X-RateLimit-Limit"]
        header["description"] += " A weekly snapshot of the CDN probe."
        self.assertTrue(any(f["pointer"].endswith("/X-RateLimit-Limit/description")
                            for f in inspect_contract(spec, demo)["findings"]))

    def test_evidenced_variant_is_allowed_only_in_its_exact_example_url(self):
        spec = json.loads((ROOT / "openapi/openapi.json").read_text())
        demo = json.loads((ROOT / "config/public-demo.json").read_text())
        approval = demo["approved_example_urls"][0]
        self.assertEqual(len(demo["articles"]), 31)
        self.assertFalse(any(r["article"] == approval["variant_article"] for r in demo["articles"]))
        # Exercise the historical narrow exception explicitly; the current URL uses a demo code.
        spec["components"]["schemas"]["Article"]["properties"]["lv_url"]["example"] = approval["value"]
        audit = inspect_contract(spec, demo)
        example = next(e for e in audit["examples"] if e["pointer"] == approval["json_pointer"])
        variant = next(r for r in example["codes"] if r["article"] == approval["variant_article"])
        self.assertTrue(variant["allowed_demo_url"])
        self.assertFalse(variant["public_demo"])
        self.assertFalse(any(f["pointer"] == approval["json_pointer"] for f in audit["findings"]))
        props = spec["components"]["schemas"]["Article"]["properties"]
        props["article"]["example"] = approval["variant_article"]
        self.assertTrue(any(f["pointer"].endswith("/properties/article/example") for f in inspect_contract(spec, demo)["findings"]))
        props["lv_url"]["example"] = approval["value"].replace(approval["variant_article"], "SYNTHETIC0")
        self.assertTrue(any(f["pointer"] == approval["json_pointer"] for f in inspect_contract(spec, demo)["findings"]))
        props["lv_url"]["example"] = approval["value"]
        props["name"]["example"] = approval["value"]
        self.assertTrue(any(f["pointer"].endswith("/properties/name/example") for f in inspect_contract(spec, demo)["findings"]))

    def test_demo_allowlist_and_examples_are_classified(self):
        demo = json.loads((ROOT / "config/public-demo.json").read_text())
        self.assertEqual(len(demo["articles"]), 31)
        self.assertEqual(len({(r["brand"], r["article"]) for r in demo["articles"]}), 31)
        spec = json.loads((ROOT / "openapi/openapi.json").read_text())
        audit = inspect_contract(spec, demo)
        self.assertTrue(audit["examples"])
        for example in audit["examples"]:
            for reference in example["codes"]:
                self.assertEqual(reference["public_demo"], any(row["article"] == reference["article"] for row in demo["articles"]))


class HeaderTokenTests(unittest.TestCase):
    def findings(self, token):
        spec = {"info": {"description": f"The `{token}` header is documented."}}
        return inspect_contract(spec, {"articles": []})["findings"]

    def test_private_suffix_is_not_an_allowed_header(self):
        self.assertTrue(self.findings("X-RateLimit-Scope-Private"))

    def test_dot_suffix_is_not_an_allowed_header(self):
        self.assertTrue(self.findings("X-RateLimit-Scope.Internal"))

    def test_prefix_is_not_an_allowed_header(self):
        self.assertTrue(self.findings("Other-X-RateLimit-Scope"))

    def test_plain_header_in_prose_is_allowed(self):
        self.assertEqual(self.findings("X-RateLimit-Scope"), [])


class ReviewedProsePolicyTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / "openapi/openapi.json").read_text())
        self.policy = json.loads((ROOT / "config/schema-policy.json").read_text())

    def put(self, obj, pointer, value):
        parent, key = pointer_parent(obj, pointer)
        parent[key] = value

    def test_five_exact_nodes_and_mirror_only(self):
        self.assertEqual(set(approved_prose_paths(self.policy)), set(REVIEWED_PROSE_PATHS))
        original = copy.deepcopy(self.spec)
        viewed = json.loads(inspection_text(json.dumps(self.spec), "openapi/openapi.json"))
        mirror = json.loads(inspection_text(json.dumps(self.policy), "config/schema-policy.json"))["contract"]
        for pointer in REVIEWED_PROSE_PATHS:
            self.assertEqual(pointer_value(viewed, pointer), "SYNTHETIC-APPROVED-PROSE")
            self.assertEqual(pointer_value(mirror, pointer), "SYNTHETIC-APPROVED-PROSE")
        self.assertEqual(self.spec, original)
        self.assertEqual(text_checks(json.dumps(self.spec), "openapi/openapi.json"), set())
        self.assertFalse(text_checks(json.dumps(self.policy), "config/schema-policy.json") & {"real-shaped-item-code", "unapproved-host", "unapproved-url"})

    def test_changed_full_strings_are_not_masked(self):
        for pointer in REVIEWED_PROSE_PATHS:
            with self.subTest(pointer=pointer):
                candidate = copy.deepcopy(self.spec)
                value = pointer_value(candidate, pointer) + " M00000"
                self.put(candidate, pointer, value)
                viewed = json.loads(inspection_text(json.dumps(candidate), "openapi/openapi.json"))
                self.assertEqual(pointer_value(viewed, pointer), value)
                self.assertTrue(text_checks(json.dumps(candidate), "openapi/openapi.json") & {"real-shaped-item-code", "unapproved-host"})
                with self.assertRaises(PolicyError):
                    validate_contract(candidate, self.policy)

    def test_exact_match_is_before_unicode_normalisation(self):
        pointer = REVIEWED_PROSE_PATHS[-1]
        candidate = copy.deepcopy(self.spec)
        self.put(candidate, pointer, pointer_value(candidate, pointer).replace(".", "．"))
        self.assertIn("unapproved-host", text_checks(json.dumps(candidate), "openapi/openapi.json"))

    def test_same_prose_elsewhere_or_in_example_is_not_allowed(self):
        value = pointer_value(self.spec, REVIEWED_PROSE_PATHS[0]) + " M00000"
        for key in ("description", "example"):
            candidate = copy.deepcopy(self.spec)
            candidate["components"]["schemas"]["Article"]["properties"]["brand_name_en"][key] = value
            self.assertIn("real-shaped-item-code", text_checks(json.dumps(candidate), "openapi/openapi.json"))
        self.assertIn("real-shaped-item-code", text_checks(value, "NOTICE.md"))

    def test_domain_elsewhere_or_as_a_url_is_not_allowed(self):
        for value in (pointer_value(self.spec, REVIEWED_PROSE_PATHS[-1]), "https" + "://" + "louisvuitton" + ".com/item"):
            candidate = copy.deepcopy(self.spec)
            candidate["info"]["description"] = value
            self.assertIn("unapproved-host", text_checks(json.dumps(candidate), "openapi/openapi.json"))

    def test_neighbor_node_remains_scanned(self):
        candidate = copy.deepcopy(self.spec)
        candidate["paths"]["/resolve"]["get"]["parameters"][0]["example"] = "https" + "://" + "synthetic" + ".invalid/item"
        self.assertIn("unapproved-host", text_checks(json.dumps(candidate), "openapi/openapi.json"))

    def test_pointer_array_and_policy_shape_guards(self):
        pointer = REVIEWED_PROSE_PATHS[-1]
        self.assertIsInstance(pointer_value(self.spec, pointer), str)
        for changed in (list(REVIEWED_PROSE_PATHS) + [pointer], list(REVIEWED_PROSE_PATHS[:-1]), "all descriptions"):
            policy = copy.deepcopy(self.policy)
            policy["approved_prose_paths"] = changed
            with self.assertRaises(PolicyError):
                validate_contract(self.spec, policy)
        policy = copy.deepcopy(self.policy)
        self.put(policy["contract"], pointer, [])
        with self.assertRaises(PolicyError):
            approved_prose_paths(policy)
        policy = copy.deepcopy(self.policy)
        policy["unreviewed_permission"] = True
        with self.assertRaises(PolicyError):
            validate_contract(self.spec, policy)
        with self.assertRaises(PolicyError):
            pointer_value(self.spec, pointer.replace("/0/", "/01/"))

    def test_reviewed_pointer_literals_are_not_credential_exemptions(self):
        for pointer in REVIEWED_PROSE_PATHS:
            self.assertNotIn("high-entropy-secret", plain_checks(pointer, "tools/schema_policy.py", decoded=True))
        value = REVIEWED_PROSE_PATHS[0] + "/UnreviewedPayloadXz7"
        self.assertIn("high-entropy-secret", plain_checks(value, "tools/schema_policy.py", decoded=True))
        self.assertIn("high-entropy-secret", plain_checks(value, "NOTICE.md", decoded=True))

    def test_policy_rebuild_preserves_permissions_and_refuses_new_text(self):
        result = proposed_policy(self.spec, self.policy)
        self.assertEqual(result["approved_prose_paths"], self.policy["approved_prose_paths"])
        candidate = copy.deepcopy(self.spec)
        pointer = REVIEWED_PROSE_PATHS[-1]
        self.put(candidate, pointer, pointer_value(candidate, pointer) + " changed")
        with self.assertRaises(ValueError):
            proposed_policy(candidate, self.policy)


if __name__ == "__main__":
    unittest.main()
