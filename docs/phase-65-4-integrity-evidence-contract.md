# Phase 65.4 Integrity Evidence Contract

- **Status**: Accepted as the Phase 65 SBOM, checksum, and signing evidence contract for beta/design-partner packaging review only.
- **Date**: 2026-06-05
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1383
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-65-2-offline-install-bundle-contract.md`, `docs/phase-65-3-release-channel-upgrade-manifest-contract.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`

This contract defines the repo-owned SBOM, checksum, and signing evidence required before Phase 65 beta/design-partner artifacts can be treated as having reviewed integrity evidence.

Integrity evidence is subordinate packaging evidence only. It does not generate production SBOMs, create production signing infrastructure, approve external distribution, enforce entitlement, satisfy Beta, RC, or GA gates, prove release truth, or create commercial replacement readiness.

## 1. Contract And Inventory Binding

The contract identifier is `phase-65-integrity-evidence-contract-v1`.

The required structured artifact is `docs/deployment/release/phase-65-4-integrity-evidence.yaml`.

Every Phase 65.4 integrity evidence record must include:

- contract identifier `phase-65-integrity-evidence-contract-v1`;
- Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`;
- release bundle identifier in the form `aegisops-beta-<repository-revision>`;
- repository revision or reviewed tag;
- integrity evidence owner;
- artifact identity fields for every required artifact;
- SBOM evidence fields for every required artifact;
- checksum evidence fields for every required artifact;
- signing evidence fields for every required artifact;
- verifier output reference for `bash scripts/verify-phase-65-4-integrity-evidence-contract.sh`;
- explicit non-claims for Beta readiness, RC readiness, GA readiness, production signing infrastructure, external distribution approval, entitlement enforcement, and commercial replacement readiness; and
- issue or change record that approved the integrity evidence contract for beta/design-partner packaging review.

Integrity evidence records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<sbom-path>`, `<checksum-manifest-path>`, `<signature-path>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.

## 2. Required Artifact Identity And Integrity Fields

Every integrity artifact entry must include these fields:

| Field | Required content | Fail-closed rule |
| --- | --- | --- |
| `artifact_name` | Exact bundle artifact name from the Phase 65.1 inventory consumer set. | Missing, placeholder, floating, mismatched, inferred, path-only, or sibling-derived names fail. |
| `artifact_class` | One of the required Phase 65.1 artifact classes consumed by beta/design-partner packaging. | Missing, unrecognized, or inferred classes fail. |
| `inventory_reference` | Repo-relative reference to `docs/phase-65-1-release-bundle-inventory.md`. | Missing or inferred inventory linkage fails. |
| `artifact_path` | Repo-relative or bundle-relative artifact path using reviewed placeholders. | Missing, workstation-local, external-only, traversal, or customer-private paths fail. |
| `sbom_reference` | Repo-relative or bundle-relative SBOM evidence path for the same artifact name. | Missing, placeholder-only, external-only, artifact-name mismatch, or sibling SBOM reuse fails. |
| `sbom_format` | Reviewed format such as `CycloneDX JSON` or `SPDX JSON`. | Missing, TODO, sample, guessed, or unsupported formats fail. |
| `sbom_scope` | Explicit scope for the same artifact and repository revision. | Missing, vague, broader-than-artifact, RC, GA, or commercial scope fails. |
| `checksum_algorithm` | Reviewed digest algorithm `sha256`. | Missing, weak, placeholder, or inferred algorithms fail. |
| `checksum_reference` | Repo-relative or bundle-relative checksum manifest path for the same artifact name. | Missing, placeholder-only, external-only, artifact-name mismatch, or sibling checksum reuse fails. |
| `checksum_value` | Retained SHA-256 digest value or placeholder `<sha256:<artifact-name>>` before real bundle generation. | Missing, fake secret, TODO, latest, or wrong artifact binding fails. |
| `signature_reference` | Repo-relative or bundle-relative signature evidence path for the same artifact name. | Missing, placeholder-only, external-only, artifact-name mismatch, or sibling signature reuse fails. |
| `signing_posture` | `beta-attestation-placeholder` for Phase 65 beta/design-partner packaging review. | Missing, production-signing, unsigned-as-valid, TODO, or inferred postures fail. |
| `signing_identity` | Reviewed placeholder identity such as `<beta-signing-identity>` until trusted production signing exists. | Missing, private key material, sample secret, TODO, or production secret values fail. |

Required artifact entries for Phase 65.4 are:

| Artifact name | Artifact class | Required integrity evidence |
| --- | --- | --- |
| `offline-install-bundle` | Install artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to the offline install artifact set from Phase 65.2. |
| `release-channel-upgrade-manifest` | Upgrade and rollback guidance artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to `docs/deployment/release/phase-65-3-upgrade-manifest.yaml`. |
| `release-notes` | Release notes artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to `docs/release/phase-65-beta-release-notes.md`. |
| `verification-output` | Verification output artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to retained verifier output references. |

The artifact name carried in `artifact_name`, `sbom_reference`, `checksum_reference`, `signature_reference`, and `checksum_value` must match. Integrity evidence must not be borrowed from a neighboring artifact, same-parent artifact, release notes summary, or operator-facing projection.

## 3. Accepted Beta Signing And Integrity Posture

Phase 65.4 accepts only a beta/design-partner integrity posture:

- SBOM evidence is required as explicit artifact-bound evidence, but SBOM generation may remain a retained placeholder until the bundle build produces real SBOM files.
- Checksum evidence is required as explicit artifact-bound SHA-256 evidence, but checksum values may use `<sha256:<artifact-name>>` placeholders until real bundle generation records immutable digests.
- Signing evidence is required as explicit artifact-bound beta attestation placeholder evidence, but production signing infrastructure, production key custody, external distribution approval, and customer trust-root publication remain future work.

The beta signing posture is `beta-attestation-placeholder`. It means the artifact has a reviewed evidence slot and fail-closed validation contract. It does not mean the artifact is production signed, externally distributable, entitlement-approved, RC-ready, GA-ready, or commercially ready.

## 4. Authority Boundary

SBOM files, checksum manifests, signature files, signing attestations, release notes, bundle manifests, verifier output, issue-lint output, and operator-facing summaries are integrity evidence only.

AegisOps control-plane records and explicit gate records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, workflow, and closeout truth.

Integrity evidence cannot approve release readiness, satisfy Pilot, Beta, RC, or GA gates, prove release truth, prove install truth, prove upgrade truth, approve external distribution, enforce entitlement, approve production signing, close workflows, reconcile actions, or replace Phase 51.3 gate evidence.

When artifact identity, inventory binding, SBOM reference, checksum reference, signature reference, signing posture, signing identity, verifier boundary, or non-claim signals are missing, malformed, placeholder credentials, production secrets, customer-private data, inferred, sibling-derived, or only partially trusted, validation fails closed.

## 5. Forbidden Material And Claims

The verifier must reject:

- missing SBOM evidence;
- missing checksum evidence;
- missing signature evidence;
- artifact-name mismatch;
- missing inventory binding;
- workstation-local absolute paths;
- production secret material;
- customer-private data;
- placeholder credentials treated as valid auth;
- production signing infrastructure claims;
- external distribution approval claims;
- production entitlement enforcement claims;
- inferred Beta pass;
- inferred RC pass;
- inferred GA pass;
- verifier-as-readiness-truth claims;
- issue-lint-as-readiness-truth claims; and
- commercial replacement readiness claims.

## 6. Verification

Run the focused contract and manifest verifier:

```sh
bash scripts/verify-phase-65-4-integrity-evidence-contract.sh
```

Run the verifier self-test:

```sh
bash scripts/test-verify-phase-65-4-integrity-evidence-contract.sh
```

Run inherited checks:

```sh
bash scripts/verify-publishable-path-hygiene.sh
```

Run issue-lint:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint 1383 --config <supervisor-config-path>
```

The verifier must reject missing SBOM, missing checksum, missing signature, artifact-name mismatch, workstation-local paths, production secrets, verifier-as-readiness-truth, inferred RC pass, and inferred GA pass.

## 7. Non-Claims

This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, external distribution approval, hosted update-service readiness, production signing infrastructure, production key custody, production trust-root publication, licensing approval, migration readiness, support readiness, or design-partner evidence completeness.

This contract is SBOM, checksum, and signing evidence for beta/design-partner packaging review only. It is not workflow authority, support authority, runtime execution authority, release gate authority, Beta gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, SBOM truth, checksum truth, signature truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
