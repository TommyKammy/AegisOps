# Phase 65.1 Release Bundle Inventory

- **Status**: Accepted as the Phase 65 beta/design-partner bundle inventory contract before offline packaging, hosted release metadata, SBOM/signing, licensing, migration, template, RC, GA, and commercial replacement claims.
- **Date**: 2026-06-01
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379
- **Related Baseline**: `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-51-5-competitive-gap-matrix.md`, `docs/phase-64-closeout-evaluation.md`, `docs/deployment/single-customer-release-bundle-inventory.md`

This contract is the versioned release bundle inventory for Phase 65 beta/design-partner artifacts. It defines the bounded artifact classes, owners, version identifiers, evidence references, explicit exclusions, and verifier coverage that later Phase 65 packaging slices must consume.

It is release packaging evidence only. It does not create offline install packaging, release channel behavior, SBOM or signing conclusions, licensing conclusions, migration guides, beta evidence templates, RC gate acceptance, GA readiness, production entitlement enforcement, hosted update service behavior, workflow authority, runtime execution authority, or commercial replacement readiness.

## 1. Version and Ownership Binding

The inventory identifier is `phase-65-release-bundle-inventory-v1`.

Every beta/design-partner release bundle record that consumes this inventory must include:

- inventory identifier `phase-65-release-bundle-inventory-v1`;
- release bundle identifier in the form `aegisops-beta-<repository-revision>`;
- repository revision or reviewed tag;
- artifact-set owner;
- per-artifact owner;
- evidence reference for every required artifact class;
- verifier output reference;
- explicit exclusion review reference; and
- issue or change record that approved the bundle for beta/design-partner packaging review.

The artifact-set owner is AegisOps maintainers. Artifact owners must be named by role or team in the inventory and by accountable person or service owner in the maintained release bundle record.

Release bundle records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<support-bundle.md>`, `<upgrade-plan.md>`, and `<design-partner-evidence.md>`.

## 2. Required Artifact Classes

| Artifact class | Inventory owner | Required evidence reference | Version identifier | Phase 65 consumer |
| --- | --- | --- | --- | --- |
| Install artifact set | Platform maintainers | Install entrypoint, profile selection, runtime env sample, preflight output, and bounded install evidence reference. | `install-artifacts:<repository-revision>` | Phase 65.2 offline install bundle contract. |
| Runtime configuration artifact set | Platform maintainers | Reviewed runtime config keys, secret-source placeholders, proxy boundary, certificate custody, and fail-closed config validation evidence. | `runtime-config:<repository-revision>` | Phase 65.2 and Phase 65.3 packaging and upgrade metadata. |
| Documentation artifact set | IT Operations, Information Systems Department | Default SMB documentation pack index for installation, daily operation, source onboarding, automation catalog, AI usage, backup and restore, support bundle, upgrade, and rollback. | `docs-pack:<repository-revision>` | Phase 65.6 default SMB documentation pack. |
| Supportability evidence artifact set | IT Operations, Information Systems Department | Doctor, backup, restore dry-run, support bundle redaction, support handoff, and safe support-bundle submission evidence references. | `supportability:<repository-revision>` | Phase 65.8 beta known-limitations and design-partner evidence templates. |
| Release notes artifact set | AegisOps maintainers | Release notes reference naming changes, known limitations, operator verification, rollback pointer, and support-bundle pointer. | `release-notes:<repository-revision>` | Phase 65.3 release channel metadata. |
| Upgrade and rollback guidance artifact set | Platform maintainers | Upgrade plan, rollback trigger, migration owner, rollback owner, clean-state validation, and post-rollback smoke evidence references. | `upgrade-rollback:<repository-revision>` | Phase 65.3 release channel and upgrade manifest. |
| Known limitation evidence artifact set | AegisOps maintainers | Phase 64 limitation ownership record references, Phase 66 handoff notes, owner, mitigation posture, blocker, accepted-risk posture, and next review date. | `limitations:<repository-revision>` | Phase 65.8 beta known-limitations template and Phase 66 planning evidence. |
| Verification output artifact set | Platform maintainers | Focused Phase 65 inventory verifier output, publishable path hygiene output, Phase 51.3 gate verifier output, and issue-lint output reference. | `verification:<repository-revision>` | Phase 65.9 closeout evaluation. |

Required artifact classes are inventory obligations only. Artifact presence does not make a workflow, support, readiness, release gate, RC, GA, or commercial replacement claim authoritative.

## 3. Evidence and Authority Boundaries

The inventory preserves the Phase 51.3 gate boundary: Pilot, Beta, RC, and GA evidence must remain distinct, and Phase 66 remains RC while Phase 67 remains GA.

The inventory preserves Phase 64 limitation ownership: known limitation records, mitigation posture, handoff notes, verifier output, issue-lint output, UI text, readiness projections, and AI summaries remain subordinate planning evidence only.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

Wazuh, Shuffle, AI, tickets, reports, support notes, dashboards, exports, browser state, UI cache, downstream receipts, release notes, bundle files, verifier output, issue-lint output, and operator-facing summaries cannot satisfy RC gates, GA gates, workflow truth, limitation truth, release truth, or readiness truth by themselves.

Missing owner, missing version identifier, missing evidence reference, missing required artifact class, missing exclusion review, placeholder credential, production secret material, customer-private data, workstation-local absolute path, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, or issue-lint-as-readiness-truth must block the release bundle record until the prerequisite is corrected.

## 4. Explicit Exclusions

The Phase 65.1 inventory explicitly excludes:

- production secret material;
- customer-private data;
- workstation-local absolute paths;
- hosted update service behavior;
- silent auto-upgrade behavior;
- billing;
- production entitlement enforcement;
- full offline install packaging implementation;
- release channel implementation;
- SBOM generation, checksum generation, or signing implementation;
- OSS licensing conclusion or redistribution approval;
- migration guide implementation;
- beta known-limitations template implementation;
- design-partner evidence template implementation;
- RC gate acceptance;
- GA readiness;
- self-service commercial readiness; and
- broad SIEM/SOAR replacement readiness.

Later Phase 65 slices may define their own bounded contracts, but they must not infer inclusion, readiness, entitlement, billing, hosted-update, RC, GA, or commercial replacement scope from this root inventory.

## 5. Verification

Run the focused inventory verifier:

```sh
bash scripts/verify-phase-65-1-release-bundle-inventory.sh
```

Run the verifier self-test:

```sh
bash scripts/test-verify-phase-65-1-release-bundle-inventory.sh
```

Run the inherited gate and path checks:

```sh
bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
```

Run issue-lint:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint 1379 --config <supervisor-config-path>
```

The verifier must reject missing version identifier, missing artifact owner, missing required artifact class, missing evidence reference, missing exclusion list, workstation-local absolute paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.

## 6. Non-Claims

This inventory does not claim Phase 66 RC readiness, Phase 67 GA readiness, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update service readiness, billing readiness, release-channel readiness, offline install completeness, SBOM completeness, checksum completeness, signing completeness, licensing approval, migration readiness, beta template completeness, or design-partner evidence completeness.

This inventory is a root packaging contract for later Phase 65 work. It is not workflow authority, support authority, runtime execution authority, release gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, UI truth, AI truth, or substitute evidence for the Phase 51.3 gate contract.
