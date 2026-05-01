# Phase 52.5 Env, Secrets, and Cert Generation Contract

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/combined-dependency-matrix.md`, `docs/deployment/compose-generator-contract.md`, `control-plane/deployment/first-boot/bootstrap.env.sample`
- **Related Issues**: #1063, #1065, #1066, #1067, #1068

This contract defines generated runtime env config, secret-reference, and certificate-generation expectations for the executable first-user stack only. It does not implement full secret backend integration, Wazuh product-profile generation, Shuffle product-profile generation, installer UX, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The first-user stack needs one reviewed contract for the files and references that later setup commands may generate before `up`, `doctor`, or rehearsal smoke checks run.

Generated runtime config is a setup prerequisite. It may prove that required inputs are present, named, ignored, and bound to reviewed custody, but it is not a source of AegisOps workflow authority.

## 2. Authority Boundary

Env files, generated secret files, generated demo tokens, generated certificates, certificate paths, OpenBao bindings, and custody checklists are setup/security prerequisites only. Their presence, freshness, generated status, file ownership, or validation status cannot become AegisOps workflow truth, approval truth, execution truth, reconciliation truth, source truth, gate truth, release truth, production truth, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Phase 52.5 verifier must preserve the Phase 51.6 rule that generated config, placeholders, demo data, tickets, AI, browser state, UI cache, downstream receipts, logs, Wazuh state, and Shuffle state cannot become workflow truth or production truth.

## 3. Generated Runtime Config

Later setup commands may generate an untracked runtime env file from `control-plane/deployment/first-boot/bootstrap.env.sample`.

The reviewed runtime env contract uses these setup bindings:

| Binding | Expected form | Production posture | Validation rule |
| --- | --- | --- | --- |
| `AEGISOPS_RUNTIME_ENV_FILE` | Path to an untracked env file such as `<runtime-env-file>`. | Required setup input; not committed evidence or workflow truth. | Must not point at `.env.sample`, a tracked file, or a workstation-local publishable path. |
| `AEGISOPS_GENERATED_CONFIG_DIR` | Untracked generated config directory such as `control-plane/deployment/first-boot/generated/`. | Generated setup output only. | Directory must be ignored or outside Git-tracked paths before writing generated files. |
| `AEGISOPS_SECRETS_DIR` | Mounted secret-file directory such as `control-plane/deployment/first-boot/secrets/` for local rehearsal or `/run/aegisops-secrets` in containers. | Secret custody source or mount point, never product truth. | Missing, empty, placeholder, sample, fake, TODO, unsigned, inline, guessed, or committed secret-looking values fail validation. |
| `AEGISOPS_CERTS_DIR` | Generated certificate directory such as `control-plane/deployment/first-boot/certs/` for local rehearsal. | Certificate custody source or mount point, never production truth by itself. | Demo certificates must be explicitly marked demo-only and cannot satisfy production TLS custody. |
| `AEGISOPS_DEMO_TOKEN_FILE` | File reference for a generated demo token when demo mode is explicitly enabled. | Demo-only setup convenience. | Must not satisfy admin bootstrap, break-glass, Wazuh ingest, proxy boundary, OpenBao, or production credential checks. |
| `AEGISOPS_DEMO_TLS_CERT_FILE` | File reference for a generated demo certificate when demo mode is explicitly enabled. | Demo-only local rehearsal certificate. | Must not satisfy production ingress TLS certificate-chain custody, private-key custody, expiry review, or reload evidence. |

Generated config must use repo-relative paths, documented env vars, or placeholders such as `<runtime-env-file>`, `<generated-config-dir>`, `<secrets-dir>`, `<certs-dir>`, `<evidence-dir>`, `<supervisor-config-path>`, and `<codex-supervisor-root>` in publishable guidance.

## 4. Secret File Custody

Secret values must be supplied through reviewed file bindings or reviewed OpenBao bindings. Inline secrets, sample credentials, placeholder values, fake values, TODO values, unsigned tokens, guessed scope, and values copied from comments are invalid.

The required secret custody classes are:

| Secret class | Accepted reference forms | Demo posture | Rejection rule |
| --- | --- | --- | --- |
| PostgreSQL DSN | `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE` or `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH`. | Demo DSNs are not production readiness. | Inline DSNs in committed docs or fixtures are rejected unless they are placeholder-safe samples in `.sample` files. |
| Wazuh ingest shared secret | `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH`. | Demo token files must be separate and demo-labeled. | Placeholder, sample, fake, TODO, unsigned, or committed bearer values are rejected. |
| Wazuh reverse-proxy secret | `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH`. | Demo proxy tokens cannot become trusted boundary secrets. | Missing trusted proxy boundary custody fails closed. |
| Protected-surface proxy secret | `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH`. | Demo values cannot satisfy protected-surface custody. | Raw forwarded headers, host, proto, tenant, or user-id hints are not trusted identity. |
| Admin bootstrap token | `AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE` or `AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH`. | Demo tokens are separate from bootstrap tokens. | Placeholder or demo token files must not unlock admin bootstrap. |
| Break-glass token | `AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE` or `AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH`. | Demo tokens are separate from break-glass tokens. | Missing custody owner, trigger, and follow-up rotation evidence fails closed. |
| OpenBao token | `AEGISOPS_OPENBAO_TOKEN_FILE` or a runtime-injected `AEGISOPS_OPENBAO_TOKEN`. | Demo-only OpenBao tokens are invalid. | Committed OpenBao tokens, TODO values, and sample tokens are rejected. |

## 5. Certificate Generation

Later setup commands may generate demo TLS material only when demo mode is explicit. Generated demo certificate material must be written to an ignored or untracked certificate directory and labeled as demo-only.

Production posture requires reviewed certificate-chain custody, private-key custody, expiry review horizon, reload evidence, approved proxy artifact revision, and trusted-header normalization. The existing first-boot sample names these production custody fields through `AEGISOPS_INGRESS_TLS_CERT_CHAIN_FILE`, `AEGISOPS_INGRESS_TLS_PRIVATE_KEY_FILE`, `AEGISOPS_INGRESS_TLS_CERT_CUSTODY_OWNER`, `AEGISOPS_INGRESS_TLS_PRIVATE_KEY_CUSTODIAN`, `AEGISOPS_INGRESS_TLS_EXPIRY_REVIEW_HORIZON`, `AEGISOPS_INGRESS_TLS_RELOAD_EVIDENCE_REF`, `AEGISOPS_INGRESS_APPROVED_PROXY_ARTIFACT_REVISION`, and `AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION`.

Demo certificates, self-signed local certificates, generated key pairs, or certificate path existence are not production truth and must not satisfy production ingress TLS custody.

## 6. Ignored Generated Paths

Generated runtime config, generated secret files, and generated certificates must be untracked or explicitly ignored before setup commands write them.

The repository ignore contract includes:

| Ignored path | Purpose | Tracking rule |
| --- | --- | --- |
| `control-plane/deployment/first-boot/generated/` | Generated compose/env/profile output for first-user setup. | Must remain ignored. |
| `control-plane/deployment/first-boot/runtime/` | Local runtime env files and generated runtime state. | Must remain ignored. |
| `control-plane/deployment/first-boot/secrets/` | Local rehearsal secret-file bindings. | Must remain ignored. |
| `control-plane/deployment/first-boot/certs/` | Local rehearsal certificate material. | Must remain ignored. |

Tracked `.sample` files may document names and placeholder-safe structure only. Real env files, live DSNs, live tokens, private keys, certificate material, and customer-private credentials must not be committed.

## 7. Validation Rules

Env, secrets, and cert contract validation must fail closed when:

- the contract document is missing;
- runtime env, generated config, secret, demo token, or cert binding coverage is missing;
- generated secret or certificate paths are not ignored;
- demo token or demo certificate posture is not separated from production posture;
- a placeholder, TODO, sample, fake, guessed, unsigned, inline, or committed secret-looking value is accepted as valid;
- generated env, secret, certificate, demo token, or certificate path state is described as AegisOps workflow truth, production truth, gate truth, release truth, approval truth, execution truth, reconciliation truth, or closeout truth;
- raw forwarded headers, host, proto, tenant, or user-id hints are trusted as identity without the reviewed proxy boundary; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders.

## 8. Forbidden Claims

- Placeholder secrets are valid credentials.
- Committed secret-looking values are acceptable.
- Demo token is production truth.
- Demo certificate is production truth.
- Generated certificate path is production truth.
- Env config is AegisOps workflow truth.
- Secret file presence is AegisOps approval truth.
- Certificate freshness is AegisOps release truth.
- Raw forwarded headers are trusted identity.
- Phase 52.5 implements secret backend integration.
- Phase 52.5 implements production certificate automation.
- Phase 52.5 implements Wazuh product profiles.
- Phase 52.5 implements Shuffle product profiles.

## 9. Validation

Run `bash scripts/verify-phase-52-5-env-secrets-certs-contract.sh`.

Run `bash scripts/test-verify-phase-52-5-env-secrets-certs-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1068 --config <supervisor-config-path>`.

The verifier must fail when the contract is missing, when generated runtime paths are not ignored, when placeholder secrets are accepted as valid, when committed secret-looking values appear outside approved placeholder-safe sample context, when demo token or demo certificate posture is treated as production truth, when the Phase 51.6 policy citation is missing, or when publishable guidance uses workstation-local absolute paths.

## 10. Non-Goals

- No secret backend integration is implemented here.
- No Wazuh product profile generation, Shuffle product profile generation, installer UX, release-candidate behavior, general-availability behavior, or runtime behavior is implemented here.
- No env file, generated config, generated secret, generated certificate, demo token, certificate path, OpenBao binding, custody checklist, Wazuh state, Shuffle state, placeholder, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
