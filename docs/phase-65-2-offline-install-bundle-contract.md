# Phase 65.2 Offline Install Bundle Contract

- **Status**: Accepted as the Phase 65 offline install bundle contract for beta/design-partner packaging review only.
- **Date**: 2026-06-02
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1384
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/deployment/first-user-stack.md`, `docs/deployment/host-preflight-contract.md`, `docs/deployment/clean-host-smoke-skeleton.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/runbook.md`

This contract defines the repo-owned offline install bundle shape for Phase 65 beta/design-partner packaging review. It consumes the Phase 65.1 release bundle inventory and narrows the install artifact set into a bounded, inspectable, offline artifact set.

The offline install bundle is packaging evidence only. It does not implement a production installer, hosted update service, silent auto-upgrade, entitlement enforcement, billing, release-channel behavior, RC proof, GA proof, workflow authority, runtime execution authority, or commercial replacement readiness.

## 1. Bundle Identifier And Metadata

The contract identifier is `phase-65-offline-install-bundle-contract-v1`.

Every offline install bundle record must include:

- contract identifier `phase-65-offline-install-bundle-contract-v1`;
- Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`;
- release bundle identifier in the form `aegisops-beta-<repository-revision>`;
- repository revision or reviewed tag;
- bundle owner;
- per-artifact owner;
- bundle creation timestamp;
- reviewed environment assumption `offline-beta-design-partner`;
- required artifact manifest path `BUNDLE-MANIFEST.md`;
- verifier output reference for `bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>`;
- explicit exclusion review reference; and
- issue or change record that approved the offline bundle for beta/design-partner packaging review.

Offline bundle records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<runtime-env-file>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.

## 2. Required Offline Bundle Files

The offline install bundle must contain these required files:

| Bundle path | Owner | Required content | Failure when missing |
| --- | --- | --- | --- |
| `BUNDLE-MANIFEST.md` | AegisOps maintainers | Contract identifier, inventory identifier, release bundle identifier, repository revision, owner, creation timestamp, environment assumption, exclusion review, and verifier output reference. | Reject the bundle before beta/design-partner handoff. |
| `install/README.md` | Platform maintainers | Reviewed offline install entry command, selected profile, dependency assumptions, and manual prerequisites. | Reject the bundle because install entrypoint evidence is absent. |
| `config/runtime.env.sample` | Platform maintainers | Placeholder-only runtime configuration keys and secret-source instructions that cite `docs/deployment/env-secrets-certs-contract.md`. | Reject the bundle because runtime configuration custody is not inspectable. |
| `evidence/install-preflight-output.txt` | Platform maintainers | Retained host preflight output reference for the same release bundle identifier and repository revision. | Reject the bundle because install completeness evidence is absent. |
| `docs/phase-65-2-offline-install-bundle-contract.md` | AegisOps maintainers | This contract, copied from the reviewed repository revision. | Reject the bundle because the offline contract is not carried with the artifact set. |
| `docs/phase-65-1-release-bundle-inventory.md` | AegisOps maintainers | Phase 65 inventory consumed by this contract. | Reject the bundle because the Phase 65 inventory reference is absent. |
| `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md` | AegisOps maintainers | Pilot, Beta, RC, and GA gate boundary. | Reject the bundle because release-gate non-claims are not carried with the artifact set. |
| `docs/deployment/first-user-stack.md` | Platform maintainers | Reviewed first-user install and operating guidance. | Reject the bundle because install guidance is absent. |
| `docs/deployment/host-preflight-contract.md` | Platform maintainers | Reviewed host preflight expectations. | Reject the bundle because host assumptions are not inspectable. |
| `docs/deployment/clean-host-smoke-skeleton.md` | Platform maintainers | Reviewed clean-host smoke skeleton and false-success rejection posture. | Reject the bundle because clean-host smoke expectations are absent. |
| `docs/runbook.md` | IT Operations, Information Systems Department | Startup, shutdown, evidence capture, and operator handoff guidance. | Reject the bundle because operator runbook guidance is absent. |

These files define bundle completeness only. Their presence does not prove install success, clean-host success, Beta readiness, RC readiness, GA readiness, release truth, gate truth, workflow truth, or commercial replacement readiness.

## 3. Offline Environment Assumptions

The bundle may assume:

- operator-controlled transfer of the reviewed artifact set into a beta/design-partner environment;
- Docker and Compose prerequisites reviewed by `docs/deployment/host-preflight-contract.md`;
- runtime configuration produced from placeholder samples and trusted local secret custody;
- manual certificate and credential custody reviewed before use; and
- retained local evidence paths under `<evidence-dir>`.

The bundle must not assume hidden hosted downloads, network update services, silent auto-upgrade, background entitlement checks, production billing, customer-private data, production secrets, or workstation-local absolute paths.

## 4. Forbidden Material And Claims

The verifier must reject:

- missing bundle metadata;
- missing required artifact;
- workstation-local absolute paths;
- production secret material;
- placeholder credentials treated as valid auth;
- customer-private data;
- hidden hosted dependency claim;
- hosted update service claim;
- silent update or silent auto-upgrade claim;
- production installer claim;
- production entitlement enforcement claim;
- inferred Beta pass;
- inferred RC pass;
- inferred GA pass;
- verifier-as-readiness-truth claim; and
- issue-lint-as-readiness-truth claim.

The offline install bundle contract preserves the Phase 51.3 gate boundary: Pilot, Beta, RC, and GA evidence must remain distinct, Phase 66 remains RC, and Phase 67 remains GA.

Bundle files, manifest entries, install output, smoke output, verifier output, issue-lint output, docs, release notes, operator-facing summaries, and downstream receipts cannot satisfy Beta gates, RC gates, GA gates, workflow truth, release truth, gate truth, limitation truth, or readiness truth by themselves.

## 5. Manual Or Unsupported For Beta Use

The Phase 65.2 offline install bundle leaves these items manual or unsupported:

- live production installer behavior;
- hosted update services;
- silent auto-upgrade;
- production entitlement enforcement;
- commercial billing;
- SBOM generation, checksum generation, signing evidence, and licensing conclusions;
- migration guide implementation;
- customer-specific secret provisioning;
- customer-private data packaging;
- automatic support-bundle submission; and
- RC or GA gate acceptance.

## 6. Verification

Run the focused contract verifier:

```sh
bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh
```

Run the offline bundle smoke validation against a bundle directory:

```sh
bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>
```

Run the verifier self-test:

```sh
bash scripts/test-verify-phase-65-2-offline-install-bundle-contract.sh
```

Run inherited path hygiene:

```sh
bash scripts/verify-publishable-path-hygiene.sh
```

Run issue-lint:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint 1384 --config <supervisor-config-path>
```

The verifier must reject missing bundle metadata, missing required artifact, workstation-local absolute paths, production secrets, customer-private data, hidden hosted dependency, silent update claim, inferred RC pass, and inferred GA pass.

## 7. Non-Claims

This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update service readiness, release-channel readiness, production installer completeness, SBOM completeness, checksum completeness, signing completeness, licensing approval, migration readiness, support readiness, or design-partner evidence completeness.

This contract is an offline packaging contract for beta/design-partner review only. It is not workflow authority, support authority, runtime execution authority, release gate authority, Beta gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, install truth, smoke truth, or substitute evidence for the Phase 51.3 gate contract.
