# LuxDB contribution guide

This is the public developer repository draft. Code, tests and tooling are MIT; original docs are
CC BY 4.0. By submitting a contribution you agree to the applicable scoped license.

Use Python 3.10 or later and Node 18 or later. No live service, account key or third-party runtime library
is needed for the checks in README. Please include a synthetic reproducer for a bug.
Do not add real product observations, house-owned prose, images, response recordings,
customer information, infrastructure details or secrets anywhere in a contribution.

Do not hand-edit generated clients or rendered docs. Change the reviewed templates,
metadata or approved public contract, regenerate and run all offline checks. The
committed schema follows the supplied public API contract. Do not invent a separate
field subset.

The importer copies the supplied canonical file byte-for-byte. Check its expected
digest before generation. If the file contains unsuitable copy or examples outside
the public demo, keep it unchanged, report JSON pointers and request an upstream
fix. Publication stays blocked; never fix the canonical prose or fields locally.
For a new API-owner-supplied local file, maintainers can prepare a draft:

```sh
python3 -B tools/build_public_spec.py /path/to/reviewed-contract.json --canonical
python3 -B tools/generate_clients.py
python3 -B tools/render_public.py
python3 -B tools/inventory.py
```

Review the full diff, including path-specific keywords/enums and all original prose.
Then `tools/update_reviewed_policy.py --reviewed-draft` records proposed schema and
fixed-file hash policies for **independent review**. Never run it in CI or data-sync
jobs, or treat changing a lock/SDK/policy as approval to publish. The accepted tooling
must be supplied separately from the candidate; no candidate tool is executed by
scan or stage. The known synthetic negative-test source exception requires exact
reviewed content hashes; changed test source loses that exception.

Changes to scanner policy, manifests, templates, exports, CI and source-lock hashes
need maintainer review. Passing a scanner modified by the same contributor is not
an independent publication approval. The publisher must run the accepted scanner
and compare policy changes in a clean workspace **before** any upload.

Issues are off at launch. Contact support@luxdb.net privately for support and security.
Use respectful, concise reports; do not post vulnerabilities publicly. Do not send
keys or paid response bodies in email unless a maintainer arranges a safe process.
Maintainers make no response-time or bounty commitment.

The publish folder must have fresh history, never an inherited source tree. No
registry release or publication automation is enabled by this draft. Templates for
issues are included only for a possible later activation by the owner; disabling
blank issues in their YAML is not the GitHub repository's issues setting.

A semantic scan does not replace human review of the full diff on every rebaseline.
New hashes record accepted bytes; they do not approve their meaning or publication.
