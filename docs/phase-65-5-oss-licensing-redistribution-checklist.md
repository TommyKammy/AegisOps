# Phase 65.5 OSS Licensing And Redistribution Review Checklist

- **Status**: Accepted as the Phase 65 OSS licensing and redistribution review checklist for beta/design-partner packaging review only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1382
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-51-5-competitive-gap-matrix.md`, `docs/deployment/wazuh-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-smb-single-node-profile-contract.md`

This checklist records the Phase 65 licensing and redistribution review fields that must be present before beta/design-partner release bundle evidence can be treated as complete.

The checklist is release planning evidence only. It is not legal advice, production distribution approval, external distribution approval, upstream license modification, entitlement enforcement, RC proof, GA proof, release truth, gate truth, workflow truth, or commercial replacement readiness.

## 1. Checklist And Inventory Binding

The checklist identifier is `phase-65-oss-licensing-redistribution-checklist-v1`.

The required structured checklist record is `docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml`.

Every Phase 65.5 licensing and redistribution review record must include:

- checklist identifier `phase-65-oss-licensing-redistribution-checklist-v1`;
- Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`;
- release bundle identifier in the form `aegisops-beta-<repository-revision>`;
- repository revision or reviewed tag;
- review owner;
- reviewed date;
- artifact scope for every reviewed class;
- redistribution posture for every reviewed class;
- Wazuh packaging boundary notes;
- Shuffle packaging boundary notes;
- blocker disposition;
- conclusion;
- verifier output reference for `bash scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh`;
- explicit non-claims for legal advice, production distribution approval, external distribution approval, RC readiness, GA readiness, entitlement enforcement, and commercial replacement readiness; and
- issue or change record that approved the checklist for beta/design-partner packaging review.

Checklist records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<codex-supervisor-root>`, and `<supervisor-config-path>`.

## 2. Required Artifact Scope

The structured checklist must cover these artifact classes:

| Artifact class | Required owner | Required posture | Required boundary note |
| --- | --- | --- | --- |
| `aegisops-code-docs` | AegisOps maintainers | Repo-owned code and docs may be packaged only with retained license, notice, and attribution review evidence. | AegisOps-owned material is packaging evidence and does not grant legal advice or production distribution approval. |
| `wazuh-profile-package` | Platform maintainers | Wazuh profile files, version pins, and setup references may be included as AegisOps-authored configuration evidence only; upstream Wazuh images, binaries, dashboards, rules, and license text require separate reviewed upstream redistribution approval before inclusion. | Wazuh remains a subordinate detection substrate and does not become AegisOps release, gate, workflow, or readiness truth. |
| `shuffle-profile-package` | Platform maintainers | Shuffle profile files, workflow template contracts, and setup references may be included as AegisOps-authored configuration evidence only; upstream Shuffle images, app bundles, workflow exports, dependencies, and license text require separate reviewed upstream redistribution approval before inclusion. | Shuffle remains a subordinate routine automation substrate and does not become AegisOps release, gate, execution, reconciliation, or readiness truth. |
| `workflow-templates` | IT Operations, Information Systems Department | Reviewed workflow template contracts may be packaged as contract evidence only; generated or upstream template exports require retained license and attribution review before inclusion. | Workflow templates cannot approve, execute, reconcile, close, release, gate, or claim readiness by themselves. |
| `generated-artifacts` | Platform maintainers | Generated SBOM, checksum, signing, install, release note, verifier, and support outputs require source, owner, license posture, and retained-generation evidence before packaging. | Generated artifacts are subordinate packaging evidence and cannot prove install, release, RC, GA, or commercial readiness by themselves. |
| `third-party-dependencies` | Platform maintainers | Third-party dependency lists, image references, and package references require retained license, notice, source, and redistribution posture before any artifact is embedded in a bundle. | Dependency metadata is review evidence only and cannot approve upstream redistribution. |
| `support-bundle-examples` | IT Operations, Information Systems Department | Support examples may be packaged only when demo-only, redacted, license-reviewed, and free of customer-private data and production secrets. | Support examples remain operator-support evidence only and do not become support authority, release truth, gate truth, or workflow truth. |

Missing owner, reviewed date, artifact scope, redistribution posture, Wazuh posture, Shuffle posture, blocker disposition, conclusion, verifier output reference, or non-claim signal must block the checklist record.

## 3. Wazuh And Shuffle Packaging Boundaries

Wazuh packaging boundary:

- AegisOps may package repo-owned Wazuh profile contracts, version pins, intake references, source-health references, upgrade/rollback references, and authority-boundary notes as AegisOps-authored configuration evidence.
- AegisOps must not embed, mirror, sublicense, or imply redistribution approval for upstream Wazuh images, binaries, dashboards, rules, generated configs, or license text without a separate reviewed upstream redistribution record.
- Wazuh manager, indexer, dashboard, alert, rule, certificate, version, source-health, verifier output, issue-lint output, and operator-facing summaries remain subordinate detection substrate context.

Shuffle packaging boundary:

- AegisOps may package repo-owned Shuffle profile contracts, workflow template contracts, manual fallback contracts, callback expectations, and authority-boundary notes as AegisOps-authored configuration evidence.
- AegisOps must not embed, mirror, sublicense, or imply redistribution approval for upstream Shuffle images, app bundles, workflow exports, dependencies, generated configs, or license text without a separate reviewed upstream redistribution record.
- Shuffle frontend, backend, worker, orborus, OpenSearch datastore, workflow state, callback payload, execution output, verifier output, issue-lint output, and operator-facing summaries remain subordinate automation substrate context.

## 4. Blocker And Conclusion Requirements

The checklist record must include a blocker disposition even when no open checklist blocker exists.

Allowed checklist conclusions are limited to beta/design-partner packaging-review conclusions. A valid conclusion may state that the checklist is complete as planning evidence, but it must not state or imply legal advice, production distribution approval, external distribution approval, RC readiness, GA readiness, entitlement enforcement, or commercial replacement readiness.

If a future bundle embeds upstream Wazuh material, upstream Shuffle material, third-party binaries, customer-private data, production secrets, generated artifacts without provenance, or license text without retained attribution review, the checklist must be reopened or superseded before packaging evidence can be accepted.

## 5. Verification

Run the focused checklist verifier:

```sh
bash scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh
```

Run the verifier self-test:

```sh
bash scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh
```

Run inherited path hygiene:

```sh
bash scripts/verify-publishable-path-hygiene.sh
```

Run issue-lint:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint 1382 --config <supervisor-config-path>
```

The verifier must reject missing owner, missing reviewed date, missing Wazuh posture, missing Shuffle posture, missing conclusion, missing blocker disposition, legal-advice claims, production distribution approval claims, external distribution approval claims, inferred RC pass, inferred GA pass, verifier-as-readiness-truth claims, and issue-lint-as-readiness-truth claims.

## 6. Non-Claims

This checklist does not claim legal advice, production distribution approval, external distribution approval, upstream redistribution approval, upstream license modification, production entitlement enforcement, billing readiness, Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production signing approval, production support readiness, or design-partner evidence completeness.

This checklist is OSS licensing and redistribution review evidence for beta/design-partner packaging review only. It is not workflow authority, support authority, runtime execution authority, release gate authority, Beta gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, legal truth, license truth, redistribution truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
