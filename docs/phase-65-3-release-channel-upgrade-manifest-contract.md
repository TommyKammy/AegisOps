# Phase 65.3 Release Channel And Upgrade Manifest Contract

- **Status**: Accepted as the Phase 65 release-channel and upgrade-manifest contract for beta/design-partner packaging review only.
- **Date**: 2026-06-03
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1380
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-65-2-offline-install-bundle-contract.md`, `docs/phase-58-5-upgrade-rollback-plan-contract.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`

This contract defines the repo-owned release-channel metadata and upgrade manifest evidence required before Phase 65 beta/design-partner packages can describe what version they contain, what prior versions they can be reviewed from, what checks are required, and where rollback evidence is represented.

Release-channel metadata and upgrade manifests are packaging and planning evidence only. They do not implement silent auto-upgrade, hosted update-service behavior, production rollout, automatic rollback, RC gate acceptance, GA gate acceptance, release truth, upgrade truth, readiness truth, workflow authority, runtime execution authority, or commercial replacement readiness.

## 1. Contract And Artifact Binding

The contract identifier is `phase-65-release-channel-upgrade-manifest-contract-v1`.

The required structured artifact is `docs/deployment/release/phase-65-3-upgrade-manifest.yaml`.

Every Phase 65.3 release-channel and upgrade manifest record must include:

- contract identifier `phase-65-release-channel-upgrade-manifest-contract-v1`;
- Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`;
- Phase 65.2 offline bundle contract identifier `phase-65-offline-install-bundle-contract-v1`;
- release channel `beta-design-partner`;
- release bundle identifier in the form `aegisops-beta-<repository-revision>`;
- repository revision or reviewed tag;
- source version;
- target version;
- compatibility posture;
- rollback expectation;
- rollback evidence reference;
- required checks;
- known limitation references;
- upgrade-plan evidence reference;
- rollback evidence reference;
- verifier output reference for `bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh`;
- explicit non-claims for silent auto-upgrade, hosted update service, RC readiness, GA readiness, and commercial replacement readiness; and
- issue or change record that approved the metadata for beta/design-partner packaging review.

Release-channel and upgrade manifest records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<upgrade-plan.md>`, `<rollback-evidence.md>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.

## 2. Release Channel Metadata Fields

| Field | Required content | Fail-closed rule |
| --- | --- | --- |
| `release_channel` | Reviewed channel name `beta-design-partner`. | Missing, GA, RC, production, hosted, or inferred channel names fail. |
| `channel_scope` | Bounded beta/design-partner packaging review scope. | Missing scope or production rollout, entitlement, billing, support, RC, GA, or commercial claims fail. |
| `release_bundle_identifier` | Bundle identifier in the form `aegisops-beta-<repository-revision>`. | Missing, floating, latest, branch-only, placeholder, or unbound identifiers fail. |
| `repository_revision` | Reviewed immutable commit or reviewed tag represented by the bundle. | Missing, floating, latest, branch-only, placeholder, or unresolved revisions fail. |
| `release_notes_reference` | Repo-relative release notes evidence reference consumed from the Phase 65.1 release notes artifact set. | Missing, external-only, ticket-only, placeholder, or readiness-claim references fail. |
| `inventory_reference` | Repo-relative reference to `docs/phase-65-1-release-bundle-inventory.md`. | Missing or inferred inventory linkage fails. |
| `offline_bundle_reference` | Repo-relative reference to `docs/phase-65-2-offline-install-bundle-contract.md`. | Missing or inferred offline bundle linkage fails. |
| `authority_boundary` | Explicit statement that metadata is subordinate packaging evidence only. | Missing boundary or metadata-as-release-truth claims fail. |

## 3. Upgrade Manifest Fields

| Field | Required content | Fail-closed rule |
| --- | --- | --- |
| `source_version` | Reviewed source package, profile, or repository version before upgrade review. | Missing, floating, latest, TODO, sample, beta-only, RC, GA, or inferred versions fail. |
| `target_version` | Reviewed target package, profile, or repository version represented by the bundle. | Missing, floating, latest, TODO, sample, beta-only, RC, GA, or inferred versions fail. |
| `compatibility_posture` | One of `compatible` or `incompatible`. | Missing, placeholder, inferred, ambiguous, or convenience-summary posture fails. |
| `compatibility_reason` | Explicit reason for the posture, tied to the reviewed source and target versions. | Missing, vague, placeholder, or sibling-record-derived reasons fail. |
| `upgrade_action` | Reviewed operator action for the posture: `manual-upgrade-review` for compatible, `blocked-pending-reviewed-migration` for incompatible. | Missing action, silent auto-upgrade, hosted update, or automatic migration behavior fails. |
| `rollback_expectation` | Reviewed rollback owner, trigger, and target expectation. | Missing, placeholder, automatic rollback, broad operator discretion, or embedded evidence reference fails. |
| `rollback_evidence_reference` | Repo-relative Phase 58.5 rollback evidence reference. | Missing, placeholder, external-only, ticket-only, or inferred evidence references fail. |
| `required_checks` | Focused checks that must be retained before upgrade evidence is consumed. | Missing, placeholder, issue-lint-only, verifier-as-truth, or readiness-overclaim checks fail. |
| `known_limitation_references` | Repo-relative known limitation references that remain subordinate to AegisOps records. | Missing, external-only, inferred, or commercial-readiness claims fail. |
| `phase58_upgrade_plan_reference` | Repo-relative Phase 58.5 upgrade/rollback plan evidence reference. | Missing, placeholder, Wazuh-only, ticket-only, or inferred plan references fail. |
| `phase51_gate_boundary_reference` | Repo-relative Phase 51.3 gate contract reference. | Missing or manifest-as-gate-truth claims fail. |

The manifest must include at least one compatible version case and at least one incompatible version case. Compatible posture may allow only manual upgrade review with required checks. Incompatible posture must block upgrade consumption until a reviewed migration or follow-up contract exists.

## 4. Authority Boundary

Release-channel metadata and upgrade manifests are subordinate packaging and planning evidence. AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, restore, workflow, and closeout truth.

The manifest cannot approve release readiness, satisfy Pilot, Beta, RC, or GA gates, prove live upgrade success, prove rollback success, approve substrate mutation, close workflows, reconcile actions, or replace Phase 51.3 gate evidence.

When provenance, source version, target version, compatibility posture, rollback expectation, required checks, known limitation references, or authority-boundary signals are missing, malformed, placeholder-like, or only partially trusted, validation fails closed.

## 5. Forbidden Material And Claims

The verifier must reject:

- missing release-channel metadata;
- missing upgrade manifest artifact;
- missing source version;
- missing target version;
- missing compatibility posture;
- missing rollback expectation;
- missing required checks;
- missing known limitation references;
- silent auto-upgrade claims;
- hosted update-service claims;
- automatic migration claims;
- automatic rollback claims;
- inferred RC pass;
- inferred GA pass;
- metadata-as-release-truth claims;
- manifest-as-upgrade-truth claims;
- verifier-as-readiness-truth claims;
- issue-lint-as-readiness-truth claims;
- production entitlement enforcement claims;
- billing claims;
- commercial replacement readiness claims;
- production secret material;
- customer-private data; and
- workstation-local absolute paths.

## 6. Verification

Run the focused contract and manifest verifier:

```sh
bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh
```

Run the verifier self-test:

```sh
bash scripts/test-verify-phase-65-3-release-channel-upgrade-manifest.sh
```

Run inherited checks:

```sh
bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
```

Run issue-lint:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint 1380 --config <supervisor-config-path>
```

The verifier must reject missing source version, missing target version, missing compatibility posture, missing rollback expectation, silent auto-upgrade claims, hosted update-service claims, inferred RC pass, inferred GA pass, and workstation-local absolute path guidance.

## 7. Non-Claims

This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update-service readiness, silent auto-upgrade readiness, automatic rollback readiness, production rollout readiness, migration readiness, support readiness, billing readiness, or design-partner evidence completeness.

This contract is release-channel metadata and upgrade-manifest evidence for beta/design-partner packaging review only. It is not workflow authority, support authority, runtime execution authority, release gate authority, Beta gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, install truth, upgrade truth, rollback truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
