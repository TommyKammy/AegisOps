# Phase 53.2 Wazuh Certificate And Credential Handling Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/wazuh-smb-single-node-profile-contract.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1135, #1136, #1137

This contract defines Wazuh certificate generation-wrapper posture, credential custody expectations, default-credential rejection, rotation guidance, and fail-closed secret validation for the `smb-single-node` Wazuh product profile.

It does not implement live certificate generation, secret backend integration, production credential provisioning, Wazuh intake binding, source-health projection, upgrade automation, fleet-scale Wazuh management, Shuffle profile work, release-candidate behavior, general-availability behavior, or runtime behavior.

The required structured artifact is `docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml`.

## 1. Purpose

Phase 53.2 makes the Wazuh product-profile certificate and credential posture enforceable before later setup or source-health work can rely on it.

The contract covers Wazuh manager API TLS, indexer TLS, indexer admin client certificate, dashboard TLS, dashboard indexer client certificate, Wazuh ingest shared secret custody, Wazuh API credential custody, Wazuh indexer admin credential custody, and Wazuh dashboard credential custody.

## 2. Authority Boundary

Wazuh is a subordinate detection substrate. Wazuh certificate state, Wazuh credential state, Wazuh manager state, Wazuh indexer state, Wazuh dashboard state, generated Wazuh config, Wazuh alerts, Wazuh rule state, verifier output, issue-lint output, operator-facing status text, and setup evidence are not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Wazuh certificate and credential contract must preserve the rule that placeholders, sample credentials, fake secrets, TODO values, generated demo certificates, Wazuh status, Wazuh certificate state, Wazuh credential state, ticket state, AI output, browser state, UI cache, optional evidence, and downstream receipt state cannot become AegisOps production truth or mutate AegisOps records.

## 3. Certificate Handling Contract

The Wazuh certificate generation wrapper may generate demo or local rehearsal material only when demo mode is explicit.

Generated demo certificate material must be written to ignored or untracked certificate custody paths, must be labeled demo-only, and must not satisfy production TLS custody.

TLS-ready Wazuh profile validation must require certificate path references for:

- `wazuh-manager-api-tls-chain-ref`
- `wazuh-manager-api-tls-private-key-ref`
- `wazuh-indexer-tls-chain-ref`
- `wazuh-indexer-tls-private-key-ref`
- `wazuh-indexer-admin-client-cert-ref`
- `wazuh-dashboard-tls-chain-ref`
- `wazuh-dashboard-tls-private-key-ref`
- `wazuh-dashboard-indexer-client-cert-ref`

Certificate path references must be documented env vars, reviewed file bindings, reviewed OpenBao bindings, or explicit placeholders such as `<wazuh-cert-chain-ref>`, `<wazuh-private-key-ref>`, and `<wazuh-client-cert-ref>`. Certificate path existence, generated demo certificate presence, self-signed local material, or Wazuh dashboard status is not production truth.

## 4. Credential Handling Contract

Wazuh credentials must be supplied through reviewed file bindings or reviewed OpenBao bindings. Inline secrets, committed values, copied comments, generated examples, default credentials, sample credentials, placeholder values, fake values, TODO values, unsigned tokens, guessed scope, raw forwarded headers, or inferred tenant/source linkage are invalid.

Default Wazuh credentials must fail validation. The blocked default credential class includes `admin:admin`, `wazuh:wazuh`, `wazuh:wazuh123`, `wazuh:SecretPassword`, and any documented upstream default reused as trusted setup state.

Placeholder credentials must fail validation. The blocked placeholder class includes `changeme`, `change-me`, `password`, `Password123`, `secret`, `sample`, `example`, `fake`, `dummy`, `todo`, and `set-trusted-secret-ref` when treated as a resolved value instead of a required placeholder guard.

Committed live secret-looking values must fail validation. Tracked Wazuh profile artifacts may contain secret reference names, env var names, file-binding names, OpenBao binding names, and placeholder-safe `<...>` references only; they must not contain resolved passwords, bearer tokens, API keys, private keys, certificate private-key material, or customer-specific credential values.

## 5. Rotation Guidance

Rotation must replace Wazuh API, indexer admin, dashboard, and ingest shared-secret custody references without committing the old or new secret value.

Rotation evidence must identify the rotated custody reference, reviewer, rotation window, rollback owner, reload or restart evidence, and AegisOps handoff record when applicable. The evidence may cite references and hashes approved for disclosure, but must not include raw secret values or private-key material.

Rotation must not treat Wazuh dashboard state, Wazuh manager state, Wazuh indexer state, generated config, verifier output, or issue-lint output as AegisOps production truth, release truth, gate truth, workflow truth, reconciliation truth, approval truth, execution truth, or closeout truth.

## 6. Validation Rules

Wazuh certificate and credential validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml` is missing;
- the contract document is missing;
- certificate generation-wrapper posture is missing;
- TLS-ready certificate path references are missing;
- Wazuh API, indexer admin, dashboard, or ingest shared-secret custody references are missing;
- default Wazuh credentials are accepted;
- placeholder, sample, fake, TODO, unsigned, inline, or committed secret-looking values are accepted;
- private-key material appears in tracked Wazuh profile contract artifacts;
- rotation guidance is missing;
- Wazuh certificate or credential state is described as AegisOps workflow truth, production truth, release truth, gate truth, closeout truth, approval truth, execution truth, or reconciliation truth; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<wazuh-cert-chain-ref>`, and `<wazuh-secret-ref>`.

## 7. Forbidden Claims

- Wazuh credential state is AegisOps production truth.
- Wazuh certificate state is AegisOps gate truth.
- Generated Wazuh certificates are production truth.
- Default Wazuh credentials are valid credentials.
- Placeholder Wazuh secrets are valid credentials.
- Committed Wazuh secret-looking values are acceptable.
- Raw forwarded headers are trusted identity.
- Phase 53.2 implements live certificate generation.
- Phase 53.2 implements secret backend integration.
- Phase 53.2 implements Wazuh source-health projection.
- Phase 53.2 implements Wazuh intake binding.
- Phase 53.2 implements Shuffle product profiles.
- Phase 53.2 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness.

## 8. Validation

Run `bash scripts/verify-phase-53-2-wazuh-cert-credential-contract.sh`.

Run `bash scripts/test-verify-phase-53-2-wazuh-cert-credential-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1137 --config <supervisor-config-path>`.

The verifier must fail when the Wazuh certificate and credential contract or structured artifact is missing, when TLS-ready certificate path references are missing, when default credentials are present, when placeholder credentials are present, when committed secret-looking values or private-key material appear, when rotation guidance is missing, when Wazuh substrate state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No live certificate generation, secret backend integration, production credential provisioning, Wazuh intake binding, source-health projection, upgrade automation, fleet-scale Wazuh management, Shuffle profile work, release-candidate behavior, general-availability behavior, or runtime behavior is implemented here.
- No live secret, customer-specific value, private key, certificate material, bearer token, API key, password, env file, generated config, generated certificate, generated secret, Wazuh manager state, Wazuh indexer state, Wazuh dashboard state, Wazuh alert, Wazuh credential state, Wazuh certificate state, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
