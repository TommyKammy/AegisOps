# Phase 52.2 SMB Single-Node Profile Model

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/phase-52-1-cli-command-contract.md`
- **Related Issues**: #1063, #1064, #1065

This contract defines the repo-owned `smb-single-node` profile model only. It does not implement full profile generation, compose generation, Wazuh product profiles, Shuffle product profiles, installer UX, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The `smb-single-node` profile is the first executable-stack model for a first-user SMB deployment shape. It names the required setup inputs, generated configuration expectations, validation rules, and mode labels that later profile-generation issues must preserve.

The approved profile identifier is `smb-single-node`.

## 2. Authority Boundary

Profile config is setup input only. Profile config is not alert, case, evidence, approval, execution, reconciliation, source, workflow, gate, release, production, or closeout truth.

Generated config is operator setup output and readiness evidence only. Generated config is not production truth and must not become AegisOps workflow truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

This profile model cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The profile must preserve the Phase 51.6 rule that Wazuh, Shuffle, demo data, generated config, placeholders, tickets, AI, browser state, UI cache, and downstream receipts cannot become workflow truth or production truth.

## 3. Mode Labels

The profile model uses the following mode labels:

| Mode label | Purpose | Production meaning |
| --- | --- | --- |
| `required` | The section is required for a valid `smb-single-node` profile contract. | Missing required sections fail validation. |
| `deferred` | The section is named and bounded now, but full product-profile generation is owned by a later issue. | Deferred sections remain explicit `skipped` or `mocked` setup surfaces until reviewed implementation exists. |
| `demo-only` | The section may seed reviewed demonstration fixtures for first-user evaluation. | Demo-only data is not production truth and must not satisfy production credential, source, approval, execution, or reconciliation requirements. |

## 4. Required Profile Sections

Every valid `smb-single-node` profile must include these sections:

| Section | Mode label | Required fields | Generated config expectations | Validation rules |
| --- | --- | --- | --- | --- |
| AegisOps | `required` | `service_name`, `control_plane_url`, `operator_url`, `runtime_env_file`, `admin_bootstrap_secret_ref`, `evidence_dir`, `profile_id` | Control-plane runtime env placeholders, operator access URL, readiness evidence path, and profile binding metadata. | `profile_id` must equal `smb-single-node`; URLs must use the reviewed proxy access path; secret refs must point to trusted custody instead of inline or placeholder secrets. |
| PostgreSQL | `required` | `service_name`, `database_name`, `credential_ref`, `data_volume`, `backup_volume`, `migration_mode` | Database connection placeholders, persistent data volume, backup volume, and migration mode for the control-plane store. | Credential source must be explicit; data and backup volumes must be distinct; placeholder passwords, sample DSNs, or TODO credentials are invalid. |
| Proxy | `required` | `service_name`, `public_base_url`, `protected_routes`, `wazuh_ingest_route`, `tls_mode`, `trusted_proxy_cidrs`, `boundary_secret_ref` | Reverse-proxy route map for operator, readiness, runtime inspection, and Wazuh-facing intake admission. | The proxy is the only reviewed user-facing ingress; forwarded headers, host, proto, tenant, or user hints are untrusted unless already normalized by the trusted boundary. |
| Wazuh | `deferred` | `service_name`, `manager_url`, `ingest_route`, `ingest_secret_ref`, `alert_contract`, `source_binding` | Wazuh-facing intake placeholders and binding metadata for later reviewed Wazuh product-profile generation. | Missing Wazuh section fails validation; Wazuh status, rule, manager, decoder, alert, or timestamp state must not become AegisOps source, workflow, release, or gate truth without explicit AegisOps admission and linkage. |
| Shuffle | `deferred` | `service_name`, `api_url`, `credential_ref`, `workflow_catalog_ref`, `callback_route`, `delegation_scope` | Shuffle delegation placeholders and callback binding metadata for later reviewed Shuffle product-profile generation. | Missing Shuffle section fails validation; Shuffle workflow success, failure, retry, payload, or callback state must not become AegisOps execution, reconciliation, release, gate, or closeout truth without AegisOps approval, action intent, receipt, and reconciliation records. |
| Demo source | `demo-only` | `fixture_bundle`, `demo_mode_flag`, `source_family`, `seed_scope`, `credential_policy`, `cleanup_policy` | Demo fixture references, explicit demo-mode flag, and cleanup guidance for first-user evaluation. | Demo mode must be explicit; demo data, fake secrets, sample credentials, TODO values, or placeholder credentials must not satisfy production readiness or credential validation. |

## 5. Shared Required Fields

Each profile section must define:

- `section_id`: stable section key from the required profile sections table.
- `mode_label`: one of `required`, `deferred`, or `demo-only`.
- `required_fields`: the section-specific input fields that must be present.
- `generated_config_expectations`: the config files, placeholders, routes, or evidence references later generators may create.
- `validation_rules`: fail-closed validation requirements for missing, malformed, placeholder-backed, ambiguous, inferred, or untrusted fields.
- `authority_boundary`: the explicit statement that the section remains setup input or subordinate context and cannot become authoritative AegisOps truth.

## 6. Validation Rules

Profile validation must fail closed when:

- the profile identifier is missing or is not `smb-single-node`;
- any required profile section is missing, including Wazuh or Shuffle;
- a required field is missing, empty, malformed, placeholder-backed, inferred from naming conventions, or only partially trusted;
- generated config is described as production truth or workflow truth;
- placeholder secrets, fake secrets, sample credentials, TODO values, or inline credentials are treated as valid values;
- Wazuh, Shuffle, demo data, browser state, UI cache, tickets, AI, generated config, downstream receipts, or logs are treated as AegisOps workflow truth or production truth;
- proxy boundary checks depend on raw `X-Forwarded-*`, `Forwarded`, host, proto, tenant, or user-id hints without a trusted normalized boundary; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<runtime-env-file>`, `<profile-name>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.

Validation may produce readiness evidence, but readiness evidence remains derived evidence only and must not overwrite or redefine authoritative AegisOps records.

## 7. Forbidden Claims

- Generated config is production truth.
- Generated config is workflow truth.
- Profile config is authoritative for AegisOps records.
- Wazuh profile status is AegisOps source truth.
- Shuffle workflow success is AegisOps reconciliation truth.
- Demo data is production truth.
- Placeholder secrets are valid credentials.
- Raw forwarded headers are trusted identity.
- Phase 52.2 implements Wazuh product profiles.
- Phase 52.2 implements Shuffle product profiles.

## 8. Validation

Run `bash scripts/verify-phase-52-2-smb-single-node-profile-model.sh`.

Run `bash scripts/test-verify-phase-52-2-smb-single-node-profile-model.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1065 --config <supervisor-config-path>`.

The verifier must fail when the contract is missing, when AegisOps, PostgreSQL, proxy, Wazuh, Shuffle, or demo source coverage is missing, when required fields or mode labels are missing, when generated config is treated as production truth or workflow truth, when placeholder secrets are accepted as valid credentials, when the Phase 51.6 policy citation is missing, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No runtime profile generation is implemented here.
- No compose generation, installer UX, Wazuh product profile, Shuffle product profile, RC behavior, GA behavior, or production deployment behavior is implemented here.
- No profile config, generated config, Wazuh state, Shuffle state, demo data, placeholder, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
