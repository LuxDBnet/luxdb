"""Regressions for the independent review. All probe material is fabricated."""
import base64
import hashlib
import http.client
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "clients/python/src"))
from check_public import scan, text_checks, TRUSTED_FIXED
from generate_clients import expected, generate
from generate_js import outputs as js_outputs
from inventory import FILES
from schema_policy import validate_contract
from stage_public import stage
from luxdb_client import Client, TransportError
from luxdb_client.generated import API_BASE_URL
from luxdb_client.transport import HTTPTransport, Request


def plain_copy(source, target):
    target.mkdir()
    for rel in FILES:
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, dest)


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.copy = self.parent / "candidate"
        plain_copy(ROOT, self.copy)
        self.baseline = set(scan(self.copy))

    def append(self, payload, path="examples/demo.py"):
        with (self.copy / path).open("a") as stream:
            stream.write("\n" + payload + "\n")

    def blocked(self, category):
        findings = set(scan(self.copy)) - self.baseline
        self.assertIn(category, {f.category for f in findings})
        return findings

    def rehash_and_generate(self, spec):
        encoded = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
        (self.copy / "openapi/openapi.json").write_text(encoded)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        (self.copy / "config/schema-lock.json").write_text(json.dumps({"public_spec_sha256": digest}))
        # Deliberately refresh both consistency artifacts. This must not grant
        # semantic approval for a record hidden in an otherwise valid schema.
        name = json.loads((self.copy / "config/project.json").read_text())["project_name"]
        (self.copy / "clients/python/src/luxdb_client/generated.py").write_text(generate(spec, name, digest))
        for path, text in js_outputs(self.copy).items():
            (self.copy / path).write_text(text)
        self.assertEqual(expected(self.copy), (self.copy / "clients/python/src/luxdb_client/generated.py").read_text())

    def test_h1_object_enum_with_regenerated_lock_and_sdk(self):
        spec = json.loads((self.copy / "openapi/openapi.json").read_text())
        spec["components"]["schemas"]["Article"]["properties"]["price"]["enum"] = [{"price_usd": 19.9, "availability": "sellable"}]
        self.rehash_and_generate(spec)
        issues = self.blocked("schema-policy")
        self.assertNotIn("sdk-drift", {i.category for i in issues})

    def test_h1_array_enum_and_new_scalar_enum_need_semantic_approval(self):
        for enum in ([[19.9]], [19.9]):
            spec = json.loads((ROOT / "openapi/openapi.json").read_text())
            spec["components"]["schemas"]["Article"]["properties"]["price"]["enum"] = enum
            self.rehash_and_generate(spec)
            self.blocked("schema-policy")

    def test_h1_invalid_typed_keyword_cannot_carry_an_object(self):
        spec = json.loads((self.copy / "openapi/openapi.json").read_text())
        spec["components"]["schemas"]["Article"]["properties"]["price"]["nullable"] = {"price_usd": 19.9}
        self.rehash_and_generate(spec)
        self.blocked("schema-policy")

    def test_h1_json_inside_a_string_literal(self):
        self.append('payload = \'{"article":"SYNTHETIC-ITEM","price_usd":19.9,"availability":"sellable"}\'')
        self.blocked("record-values")

    def test_h1_nonliteral_dict_does_not_stop_field_inspection(self):
        self.append('payload = {"price_usd": float("19.9")}')
        self.blocked("record-literal")

    def test_h1_unknown_record_computation_requires_review(self):
        self.append('payload = {"price_usd": unreviewed_function()}')
        self.blocked("dynamic-record-value")

    def test_h1_license_filename_cannot_authorise_record_content(self):
        (self.copy / "LICENSE").write_text('{"article":"SYNTHETIC-ITEM","price_usd":19.9}\n')
        self.blocked("fixed-content-drift")
        self.blocked("record-values")

    def test_h1_modified_candidate_policy_cannot_approve_itself(self):
        spec = json.loads((self.copy / "openapi/openapi.json").read_text())
        spec["components"]["schemas"]["Article"]["properties"]["price"]["enum"] = [{"price_usd": 19.9}]
        self.rehash_and_generate(spec)
        policy_path = self.copy / "config/schema-policy.json"
        policy = json.loads(policy_path.read_text())
        policy["contract"] = spec
        policy_path.write_text(json.dumps(policy))
        self.blocked("fixed-content-drift")
        self.blocked("schema-policy")

    def test_m1_split_credential_is_folded_in_candidate_source(self):
        self.append('api_key = "ghp" + "_" + "fabricatedreviewonly123456"')
        self.blocked("credential-literal")
        self.blocked("secret-pattern")

    def test_m1_unknown_credential_computation_requires_review(self):
        self.append('api_key = unreviewed_function()')
        self.blocked("dynamic-credential-value")

    def test_m1_split_hostname_is_folded_in_candidate_source(self):
        self.append('endpoint = "https" + "://" + "lab" + "." + "invalid"')
        self.blocked("unapproved-host")

    def test_m1_base64_hostname_is_decoded(self):
        encoded = base64.b64encode(b"lab.invalid").decode()
        self.append("payload = " + repr(encoded))
        self.blocked("unapproved-host")

    def test_m1_base64_record_string_is_decoded(self):
        encoded = base64.b64encode(b'{"price_usd":19.9}').decode()
        self.append("payload = " + repr(encoded))
        self.blocked("record-values")

    def test_m1_unicode_fullwidth_hostname_is_normalised(self):
        self.append('endpoint = "https" + "://lab．invalid"')
        self.blocked("unapproved-host")

    def test_m1_confusable_hostname_is_normalised(self):
        self.append('endpoint = "https" + "://lаb.invalid"')
        self.blocked("unapproved-host")

    def test_m1_percent_hex_and_json_escapes(self):
        probes = ["lab%2Einvalid", b"lab.invalid".hex(), 'endpoint = "lab\\u002einvalid"']
        for payload in probes:
            source = payload if payload.startswith("endpoint") else "payload = " + repr(payload)
            self.assertIn("unapproved-host", text_checks(source, "examples/demo.py"))

    def test_l1_svg_inside_a_fixed_license_is_blocked(self):
        self.append('<svg><path d="M0 0L9 9"/></svg>', "LICENSES/CC-BY-4.0.txt")
        self.blocked("embedded-media")
        self.blocked("fixed-content-drift")

    def test_canonical_api_contract_is_copied_without_projection(self):
        source = json.loads((ROOT / "openapi/openapi.json").read_text())
        source["info"]["description"] = "Synthetic neutral contract copy test"
        for item in source["paths"].values():
            item["get"].pop("operationId", None)
        source_path = self.parent / "canonical-input.json"
        source_path.write_text(json.dumps(source))
        export = subprocess.run([sys.executable, "-I", "-B", str(self.copy / "tools/build_public_spec.py"), str(source_path), "--canonical"], cwd=self.parent, capture_output=True, text=True, timeout=30)
        self.assertEqual(export.returncode, 0, export.stderr)
        self.assertEqual(json.loads((self.copy / "openapi/openapi.json").read_text()), source)
        generated = subprocess.run([sys.executable, "-I", "-B", str(self.copy / "tools/generate_clients.py")], cwd=self.parent, capture_output=True, text=True, timeout=30)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        self.blocked("schema-policy")  # Copying a new contract is not approval.

    def test_policy_freezes_actual_license_bytes(self):
        self.assertEqual(hashlib.sha256((ROOT / "LICENSE").read_bytes()).hexdigest(), TRUSTED_FIXED["LICENSE"])
        self.assertEqual(hashlib.sha256((ROOT / "LICENSES/CC-BY-4.0.txt").read_bytes()).hexdigest(), TRUSTED_FIXED["LICENSES/CC-BY-4.0.txt"])

    def test_m2_fresh_checkout_and_ci_staging_from_another_cwd(self):
        if os.environ.get("PUBLIC_CHECKOUT_REGRESSION_CHILD") == "1":
            self.skipTest("avoid recursive child-suite spawning")
        checkout = self.parent / "checkout"
        plain_copy(ROOT, checkout)
        (checkout / ".git").mkdir()
        (checkout / ".git/HEAD").write_text("ref: refs/heads/synthetic-review\n")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PUBLIC_CHECKOUT_REGRESSION_CHILD="1")
        env.pop("LUXDB_API_KEY", None)
        direct = subprocess.run([sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", str(checkout / "tests"), "-q"], cwd=self.parent, env=env, capture_output=True, text=True, timeout=240)
        self.assertEqual(direct.returncode, 0, direct.stderr)
        candidate = self.parent / "staged"
        staged = subprocess.run([sys.executable, "-I", "-B", str(checkout / "tools/stage_public.py"), str(candidate)], cwd=self.parent, env=env, capture_output=True, text=True, timeout=240)
        self.assertFalse((candidate / ".git").exists())
        if self.baseline:
            self.assertNotEqual(staged.returncode, 0)
            self.assertEqual(set(scan(candidate)), self.baseline)
            print("Fresh checkout suite passed; publication staging correctly blocks upstream copy findings.")
            return
        self.assertEqual(staged.returncode, 0, staged.stderr)
        for script in ("render_public.py", "generate_clients.py"):
            result = subprocess.run([sys.executable, "-I", "-B", str(candidate / "tools" / script), "--check"], cwd=self.parent, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        suite = subprocess.run([sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", str(candidate / "tests"), "-q"], cwd=self.parent, env=env, capture_output=True, text=True, timeout=240)
        self.assertEqual(suite.returncode, 0, suite.stderr)
        self.assertEqual(scan(candidate), [])
        for label, result in (("Fresh checkout", direct), ("Plain CI staging", suite)):
            summary = " / ".join(line for line in result.stderr.splitlines() if line.startswith(("Ran ", "OK")))
            print(f"{label}: {summary}")
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertLess(workflow.index("stage_public.py"), workflow.index("unittest"))
        self.assertIn("working-directory: ${{ runner.temp }}/public-tree", workflow)


class TransportReviewRegressions(unittest.TestCase):
    def request(self):
        return Request("GET", API_BASE_URL + "/index?marker=SYNTHETIC-QUERY", {"X-API-Key": "SYNTHETIC-KEY"}, 1)

    def sanitised(self, call):
        try:
            call()
        except Exception as error:
            self.assertIsInstance(error, TransportError)
            message = "".join(traceback.format_exception(error))
            self.assertNotIn("SYNTHETIC-KEY", message)
            self.assertNotIn("SYNTHETIC-QUERY", message)
            self.assertTrue(error.__suppress_context__)
        else:
            self.fail("expected a sanitised transport error")

    def test_m4_bad_status_line_is_sanitised(self):
        with patch("subprocess.Popen", side_effect=http.client.BadStatusLine("SYNTHETIC-KEY SYNTHETIC-QUERY")):
            self.sanitised(lambda: HTTPTransport().send(self.request()))

    def test_m4_http_error_body_read_is_sanitised(self):
        from luxdb_client import _http_worker as worker
        class FailingBody(io.BytesIO):
            def read(self, *args):
                raise OSError("SYNTHETIC-KEY SYNTHETIC-QUERY")
        error = urllib.error.HTTPError(API_BASE_URL, 500, "synthetic", {}, FailingBody())
        request = {"url": API_BASE_URL, "headers": {}, "method": "GET", "timeout": 1}
        with patch.object(worker.sys, "stdin", io.StringIO(json.dumps(request))), patch("urllib.request.OpenerDirector.open", side_effect=error), patch.object(worker.sys, "stdout", io.StringIO()) as output:
            self.assertEqual(worker.main(), 1)
            self.assertEqual(output.getvalue(), "")

    def test_m4_request_creation_is_sanitised(self):
        with patch("subprocess.Popen", side_effect=ValueError("SYNTHETIC-KEY SYNTHETIC-QUERY")):
            self.sanitised(lambda: HTTPTransport().send(self.request()))

    def test_m4_injected_transport_is_sanitised_by_client(self):
        transport = Mock()
        transport.send.side_effect = RuntimeError("SYNTHETIC-KEY SYNTHETIC-QUERY")
        client = Client(api_key="SYNTHETIC-KEY", allow_paid=True, transport=transport)
        self.sanitised(client.snapshot)
        self.assertEqual(transport.send.call_count, 1)

    def test_m4_response_decoding_failures_are_sanitised(self):
        response = Mock()
        response.body.__len__ = Mock(side_effect=RuntimeError("SYNTHETIC-KEY SYNTHETIC-QUERY"))
        transport = Mock()
        transport.send.return_value = response
        self.sanitised(lambda: Client(transport=transport).snapshot())


class RoundTwoDeadline(unittest.TestCase):
    def supervised(self, code, timeout):
        from luxdb_client import TransportTimeout
        processes = []
        real_popen = subprocess.Popen
        def launch(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            processes.append(child)
            return child
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "synthetic_worker.py"
            script.write_text(code)
            transport = HTTPTransport()
            with patch.object(transport, "_command", return_value=[sys.executable, "-I", "-B", str(script)]), patch("subprocess.Popen", side_effect=launch):
                with self.assertRaises(TransportTimeout) as caught:
                    Client(timeout=timeout, transport=transport).snapshot()
            self.assertIsInstance(caught.exception, TimeoutError)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())
        self.assertTrue(processes[0].stdout.closed)
        self.assertTrue(processes[0].stdin.closed)

    def test_slow_drip_body_cannot_extend_overall_deadline(self):
        # Headers immediately, one body byte every 6 ms; no network.
        code = "import json,sys,time\nr=json.load(sys.stdin)\nsys.stdout.write('{\"status\":200,\"headers\":{},\"body\":\"');sys.stdout.flush()\nfor _ in range(200):\n sys.stdout.write('e');sys.stdout.flush();time.sleep(.006)\n"
        self.supervised(code, .01)
        self.supervised(code, .2)  # Also reaches the drip after worker startup.

    def test_connect_and_headers_stall_is_cancelled_and_reaped(self):
        self.supervised("import json,sys,time\njson.load(sys.stdin)\ntime.sleep(30)\n", .1)

    def test_error_body_drip_is_cancelled_and_reaped(self):
        self.supervised("import json,sys,time\njson.load(sys.stdin)\nsys.stdout.write('{\"status\":503,\"headers\":{},\"body\":\"');sys.stdout.flush()\nfor _ in range(200):\n sys.stdout.write('e');sys.stdout.flush();time.sleep(.006)\n", .2)

    def test_worker_byte_limit_applies_to_error_and_success(self):
        from luxdb_client._http_worker import exchange
        for status in (200, 503):
            response = Mock()
            response.status = status
            response.headers = {}
            response.read.return_value = b"x" * 9
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            opener = Mock()
            opener.open.return_value = response
            with patch("luxdb_client._http_worker.MAX_RESPONSE_BYTES", 8):
                with self.assertRaises(ValueError):
                    exchange({"url": API_BASE_URL, "method": "GET", "headers": {}, "timeout": 1}, opener)

    def test_supervisor_success_is_one_call(self):
        answer = {"status": 200, "headers": {}, "body": base64.b64encode(b'{"synthetic":true}').decode()}
        code = "import json,sys\njson.load(sys.stdin)\nsys.stdout.write(" + repr(json.dumps(answer)) + ")\n"
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "synthetic_worker.py"
            script.write_text(code)
            transport = HTTPTransport()
            with patch.object(transport, "_command", return_value=[sys.executable, "-I", "-B", str(script)]):
                self.assertEqual(Client(timeout=3, transport=transport).snapshot(), {"synthetic": True})


class RoundThreeWorkerEnvironment(unittest.TestCase):
    COMMON = {"PATH", "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy"}
    WINDOWS = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}

    def test_real_worker_only_gets_allowed_environment_and_stdin_key(self):
        from luxdb_client.transport import Request
        parent_env = {"PATH": os.defpath, "SYNTHETIC_SECRET": "SYNTHETIC-ENV-VALUE",
                      "HTTP_PROXY": "http://synthetic.invalid:9999", "http_proxy": "http://synthetic.invalid:9999",
                      "HTTPS_PROXY": "http://synthetic.invalid:9999", "https_proxy": "http://synthetic.invalid:9999",
                      "NO_PROXY": "synthetic.invalid", "no_proxy": "synthetic.invalid",
                      "ALL_PROXY": "http://synthetic.invalid:9999", "PYTHONPATH": "SYNTHETIC-IMPORT-PATH",
                      "REQUESTS_CA_BUNDLE": "SYNTHETIC-OTHER-CA"}
        if sys.platform == "win32":
            # The platform loader needs this value; all other test values are synthetic.
            for name in self.WINDOWS:
                if name in os.environ:
                    parent_env[name] = os.environ[name]
        worker = ROOT / "clients/python/src/luxdb_client/_http_worker.py"
        code = "import runpy,io,os,json\nw=runpy.run_path(" + repr(str(worker)) + ")\n" + """
class Answer(io.BytesIO):
    status = 200
    headers = {}
class Opener:
    def open(self, request, timeout):
        result = {'env_keys': sorted(os.environ),
                  'secret_absent': 'SYNTHETIC_SECRET' not in os.environ,
                  'http_absent': 'HTTP_PROXY' not in os.environ and 'http_proxy' not in os.environ,
                  'https_present': os.environ.get('HTTPS_PROXY') == os.environ.get('https_proxy') == 'http://synthetic.invalid:9999',
                  'bypass_present': os.environ.get('NO_PROXY') == os.environ.get('no_proxy') == 'synthetic.invalid',
                  'stdin_key_received': request.get_header('X-api-key') == ('SYNTHETIC-' + 'REQUEST-KEY')}
        return Answer(json.dumps(result).encode())
w['urllib'].request.build_opener = lambda *args: Opener()
raise SystemExit(w['main']())
"""
        processes, launches = [], []
        real_popen = subprocess.Popen
        def launch(*args, **kwargs):
            launches.append((args, kwargs))
            child = real_popen(*args, **kwargs)
            processes.append(child)
            return child
        transport = HTTPTransport()
        with patch.dict(os.environ, parent_env, clear=True), patch.object(transport, "_command", return_value=[sys.executable, "-I", "-B", "-c", code]), patch("subprocess.Popen", side_effect=launch):
            response = transport.send(Request("GET", API_BASE_URL + "/snapshot", {"X-API-Key": "SYNTHETIC-REQUEST-KEY"}, 3))
        result = json.loads(response.body)
        for name in ("secret_absent", "http_absent", "https_present", "bypass_present", "stdin_key_received"):
            self.assertTrue(result[name], name)
        allowed = self.COMMON | (self.WINDOWS if sys.platform == "win32" else set())
        self.assertLessEqual(set(result["env_keys"]), allowed)
        self.assertEqual(len(launches), 1)
        self.assertIn("env", launches[0][1])
        self.assertLessEqual(set(launches[0][1]["env"]), allowed)
        self.assertNotIn("SYNTHETIC-REQUEST-KEY", repr(launches[0][0]))
        self.assertIsNotNone(processes[0].poll())
        self.assertTrue(processes[0].stdin.closed)
        self.assertTrue(processes[0].stdout.closed)

    def test_unix_environment_drops_platform_and_unlisted_keys(self):
        from luxdb_client.transport import _worker_env
        invented = {name: "SYNTHETIC-ENV-VALUE" for name in self.COMMON | self.WINDOWS | {"SYNTHETIC_SECRET", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "PYTHONPATH"}}
        with patch.dict(os.environ, invented, clear=True), patch.object(sys, "platform", "linux"):
            self.assertEqual(_worker_env(), {name: invented[name] for name in self.COMMON})

    def test_windows_environment_only_adds_loader_and_temp_names(self):
        from luxdb_client.transport import _worker_env
        invented = {name: "SYNTHETIC-ENV-VALUE" for name in self.COMMON | self.WINDOWS | {"SYNTHETIC_SECRET", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "PYTHONPATH"}}
        with patch.dict(os.environ, invented, clear=True), patch.object(sys, "platform", "win32"):
            self.assertEqual(_worker_env(), {name: invented[name] for name in self.COMMON | self.WINDOWS})

    def test_absent_allowlisted_keys_are_not_invented(self):
        from luxdb_client.transport import _worker_env
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_worker_env(), {})


if __name__ == "__main__":
    unittest.main()
