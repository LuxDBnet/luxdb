# Draft publication manifest

This is a plain, clean publication tree. No internal history is included.
The raw inputs and private review/run reports are intentionally outside
this tree and must not be copied into it. Source descriptions below identify
public-safe provenance categories, not internal paths or collection methods.

| File | Purpose | Source |
|---|---|---|
| `.gitattributes` | Line endings and generated-file markers | Draft tooling policy |
| `.github/ISSUE_TEMPLATE/config.yml` | Contact-only issue configuration | Owner policy: issues off |
| `.github/disabled-issue-templates/bug_report.yml` | Inactive structured bug form | Draft support policy |
| `.github/disabled-issue-templates/feature_request.yml` | Inactive integration request form | Draft support policy |
| `.github/pull_request_template.md` | Safe contribution checklist | Reviewed publication policy |
| `.github/workflows/ci.yml` | Read-only offline tests and staging checks | Draft CI policy; no production inputs |
| `.gitignore` | Local development exclusions | Draft tooling policy; not a publication boundary |
| `CONTRIBUTING.md` | Offline workflow and contribution boundaries | Reviewed contribution template |
| `LICENSE` | MIT grant and scope pointer | Standard MIT text; owner-approved licensing policy |
| `LICENSES/CC-BY-4.0.txt` | Documentation license grant by reference | Official CC BY 4.0 legal-text reference and owner policy |
| `MANIFEST.md` | File-to-purpose-to-source inventory | This reviewed allowlist |
| `NOTICE.md` | License boundaries and independence disclaimer | Reviewed notice template |
| `README.md` | Live developer introduction | Reviewed README template and project configuration |
| `SECURITY.md` | Private reporting contact | Reviewed security template |
| `assets/icon-512-light.png` | Organisation avatar image | Published brand asset; pinned bytes |
| `assets/lockup-600-dark.png` | README logo for dark themes | Published brand asset; pinned bytes |
| `assets/lockup-600-light.png` | README logo for light themes | Published brand asset; pinned bytes |
| `assets/og-1200x630.png` | Repository social preview image | Published brand asset; pinned bytes |
| `clients/js/LICENSE` | MIT code license | Repository code license |
| `clients/js/README.md` | JavaScript and TypeScript client guide | Reviewed client behaviour |
| `clients/js/generated.js` | Generated operation metadata | Public 2.3.1 contract |
| `clients/js/index.d.ts` | Generated response models and method declarations | Public 2.3.1 contract |
| `clients/js/index.js` | Demo-first one-shot fetch client | Reviewed public contract and safety rules |
| `clients/js/package.json` | Private local ESM package and type entry | Zero-dependency client packaging |
| `clients/js/test/client.test.mjs` | Offline client tests | Injected fetch and synthetic responses |
| `clients/python/pyproject.toml` | Local draft package metadata | SDK packaging policy; no registry release |
| `clients/python/src/luxdb_client/__init__.py` | Public client entry point | Maintained SDK wrapper |
| `clients/python/src/luxdb_client/_http_worker.py` | Supervised one-shot HTTP worker | Stdlib I/O; bounded by the parent deadline |
| `clients/python/src/luxdb_client/generated.py` | Typed models and eight methods | Locked public OpenAPI and deterministic generator |
| `clients/python/src/luxdb_client/transport.py` | One-shot JSON HTTPS transport | Maintained stdlib implementation |
| `config/fixed-hashes.json` | Accepted fixed-file content hashes | Explicit review-controlled policy snapshot |
| `config/project.json` | Single project-name variable and public address | Owner naming/contact policy and supplied public server |
| `config/public-demo.json` | Public demo reference-code allowlist | The site's 31 public sample items supplied for review |
| `config/schema-lock.json` | Hash of draft public spec | Customer contract bytes; not semantic approval |
| `config/schema-policy.json` | Typed path-specific draft contract policy | Reviewed public 2.3.1 definitions; publication separately approved |
| `config/sources.json` | Digests of supplied public definition sources | Verified source inputs |
| `docs/api-compatibility.md` | Draft SDK limitations | Public contract and generator capabilities |
| `docs/api-reference.md` | API operations and response field definitions | Canonical contract, excluding example values |
| `docs/data-dictionary.md` | Data-field definitions and units | Public definitions from the current dictionary |
| `docs/houses.md` | House names; auto-generated later marker | Static house metadata snapshot |
| `docs/quickstart.md` | Offline first and explicit paid opt-in | Reviewed quickstart template |
| `examples/demo.mjs` | Offline JavaScript example | Synthetic fixture and client |
| `examples/demo.py` | Offline mocked sandbox example | Synthetic fixture and SDK |
| `examples/paid_item.py` | Explicit opt-in single-item request | Public SDK method; user supplies key/code locally |
| `metadata/fields.json` | Public data-field definitions | Static supplied dictionary snapshot; public names, hidden fields excluded |
| `metadata/houses.json` | Static house-name snapshot only | Approved task context; live export pending |
| `openapi/openapi.json` | Exact canonical customer contract | API-owner 2.3.1 public file copied byte-for-byte |
| `templates/CONTRIBUTING.md.in` | Static contribution template | Publication policy |
| `templates/NOTICE.md.in` | Static scope/disclaimer template | Owner license and independence policy |
| `templates/README.md.in` | Static intro template | Owner decisions and reviewed product copy |
| `templates/SECURITY.md.in` | Static security template | Owner contact decision |
| `templates/quickstart.md.in` | Static usage template | SDK safety policy |
| `tests/fixtures/synthetic-response.json` | Invented empty search response | Hand-authored synthetic fixture; no observed data |
| `tests/test_assets.py` | Pinned image and README logo negative cases | Synthetic probes only |
| `tests/test_canonical.py` | Canonical types and definition-source tests | Verified inputs and synthetic mocks |
| `tests/test_generation.py` | Schema, rendering and draft acceptance tests | Public schema, metadata and deterministic tools |
| `tests/test_javascript_public.py` | JavaScript scanner negative cases | Synthetic attacks only |
| `tests/test_public.py` | Scanner negative and staging tests | Synthetic attack cases; no real secrets or records |
| `tests/test_review_regressions.py` | Codex review bypass and checkout regressions | Fabricated probes; no actual secret or item record |
| `tests/test_sdk.py` | Offline transport/SDK tests | Public contract and synthetic responses |
| `tools/api_reference.py` | Definition-only API reference renderer | Canonical field definitions and types |
| `tools/audit_canonical.py` | Upstream copy and demo membership audit | Canonical copy and public demo allowlist |
| `tools/build_public_spec.py` | Exact canonical-file importer | API-owner contract; no local schema edits |
| `tools/check_public.py` | Pre-upload content/structure scanner | Review-controlled allowlist and public policy |
| `tools/client_compat.py` | Unmodified canonical client view | Canonical API types; no client-only overrides |
| `tools/content_policy.py` | Bounded literal normalisation and decoding | Non-executing content checks |
| `tools/export_dictionary.py` | Public data-definition exporter | Current dictionary; no rows or coverage values |
| `tools/generate_clients.py` | Local deterministic SDK generator | Canonical contract |
| `tools/generate_js.py` | ESM metadata and TypeScript declarations generator | Committed public OpenAPI |
| `tools/inventory.py` | Allowlist and manifest renderer | Accepted draft file layout |
| `tools/javascript_policy.py` | Non-executing JS literal policy | Reviewed fixed-source and content policy |
| `tools/render_public.py` | Single-variable docs renderer | Reviewed templates and metadata |
| `tools/schema_policy.py` | Typed contract and enum policy validator | Review-controlled public schema boundary |
| `tools/stage_public.py` | Clean folder staging, never history | Review-controlled file allowlist |
| `tools/update_reviewed_policy.py` | Explicit draft policy snapshot tool | Maintainer review only; never a CI/autopublish step |
