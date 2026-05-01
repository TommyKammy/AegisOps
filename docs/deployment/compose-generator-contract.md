# Phase 52.4 Compose Generator Contract

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/combined-dependency-matrix.md`, `docs/network-exposure-and-access-path-policy.md`
- **Related Issues**: #1063, #1065, #1066, #1067

This contract defines generated Docker Compose shape and snapshot-test expectations for the executable first-user stack only. It does not implement the installer, compose generator runtime, Wazuh product profile, Shuffle product profile, production hardening, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The compose generator contract gives later setup issues one stable output shape for the `smb-single-node` first-user stack. The generator may produce a Compose file from reviewed profile input, but the generated file is setup/runtime posture evidence only.

Manual editing of generated Compose output is not the product path. Operators may supply reviewed profile input, env files, secret references, and documented overrides through later installer or profile surfaces, but hand-edited Compose files must not become the supported configuration workflow.

## 2. Authority Boundary

Generated compose state is setup/runtime posture evidence only. Generated compose state is not alert, case, evidence, approval, execution, reconciliation, source, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The generator must preserve the Phase 51.6 rule that Wazuh, Shuffle, generated config, placeholders, tickets, AI, browser state, UI cache, logs, and downstream receipts cannot become workflow truth or production truth.

## 3. Generated Compose Shape

The generated `smb-single-node` Compose output must include these service keys and boundaries:

| Service | Mode label | Generated shape | Boundary requirement |
| --- | --- | --- | --- |
| AegisOps | `required` | Control-plane service built from a release-bound image or repository revision, joined only to internal and proxy networks, with env-file and secret-reference placeholders. | Backend port remains internal; no direct host `ports` publication is allowed. |
| PostgreSQL | `required` | PostgreSQL 15 or 16 service with named data and backup volumes, explicit credential reference, and healthcheck dependency for AegisOps startup. | Database port remains internal; state backs AegisOps records but process state alone is not workflow truth. |
| Proxy | `required` | Reviewed reverse-proxy service with the only host-published user-facing ports, route map for operator, readiness, runtime inspection, and Wazuh intake paths, and trusted boundary secret references. | Proxy is the only approved ingress boundary; raw forwarded headers and direct backend access are not trusted. |
| Wazuh | `deferred` | Deferred product-profile placeholder service or external-substrate binding with explicit intake route, source binding, and secret-reference placeholders. | Wazuh status, alerts, timestamps, and rule state remain subordinate signal context, not AegisOps workflow truth. |
| Shuffle | `deferred` | Deferred product-profile placeholder service or external-substrate binding with callback route, workflow catalog reference, and credential-reference placeholders. | Shuffle workflow success, failure, retry, payload, and callback state remain subordinate execution context until admitted through AegisOps records. |
| Demo source | `demo-only` | Demo fixture source with explicit demo mode, reviewed fixture bundle reference, seed scope, and cleanup policy. | Demo data, fake secrets, and sample credentials are not production truth and must not satisfy production readiness. |

Generated Compose output must use named volumes, repo-relative references, documented environment variables, or placeholders such as `<runtime-env-file>`, `<compose-output-path>`, `<profile-name>`, `<supervisor-config-path>`, and `<codex-supervisor-root>` in publishable guidance.

## 4. Snapshot Expectations

The required snapshot fixture is `docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml`.

Snapshot tests must verify:

- service keys for AegisOps, PostgreSQL, proxy, Wazuh, Shuffle, and demo source are present;
- the proxy service is the only service with host-published `ports`;
- AegisOps, PostgreSQL, Wazuh, Shuffle, and demo source do not publish direct host ports;
- AegisOps and PostgreSQL share an internal network, and AegisOps reaches users only through the proxy network;
- PostgreSQL data and backup volumes are separate named volumes;
- Wazuh, Shuffle, and demo source are explicit deferred or demo-only surfaces instead of hidden product-profile completion claims;
- secret, certificate, and credential values are represented as trusted references or placeholders, not inline secrets; and
- the snapshot carries an authority-boundary note that generated Compose output is setup/runtime posture evidence only.

## 5. Validation Rules

Compose generator contract validation must fail closed when:

- the contract document is missing;
- any required service row is missing, including AegisOps, PostgreSQL, proxy, Wazuh, Shuffle, or demo source;
- the generated snapshot fixture is missing;
- the generated snapshot omits any required service;
- any non-proxy service publishes host ports directly;
- the proxy boundary is missing or is not the only approved ingress;
- manual Compose editing is described as the product path;
- generated compose state is described as AegisOps workflow truth, production truth, release truth, gate truth, or closeout truth;
- placeholder secrets, sample credentials, TODO values, inline secrets, raw forwarded headers, or unreviewed scope inference are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders.

## 6. Forbidden Claims

- Compose state is AegisOps workflow truth.
- Generated compose state is production truth.
- Generated compose state is release truth.
- Generated compose state is closeout truth.
- Manual Compose editing is the product path.
- Direct backend exposure is approved.
- Proxy boundary is optional.
- Placeholder secrets are valid credentials.
- Raw forwarded headers are trusted identity.
- Phase 52.4 implements the compose generator runtime.
- Phase 52.4 implements Wazuh product profiles.
- Phase 52.4 implements Shuffle product profiles.

## 7. Validation

Run `bash scripts/verify-phase-52-4-compose-generator-contract.sh`.

Run `bash scripts/test-verify-phase-52-4-compose-generator-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1067 --config <supervisor-config-path>`.

The verifier must fail when the contract is missing, when the snapshot is missing, when any expected service is absent, when a non-proxy service exposes backend ports directly, when the proxy boundary is missing, when manual Compose editing is treated as the product path, when generated compose state is treated as workflow truth, or when publishable guidance uses workstation-local absolute paths.

## 8. Non-Goals

- No compose generator implementation is approved by this contract.
- No installer, Wazuh product profile, Shuffle product profile, production hardening, release-candidate behavior, general-availability behavior, or runtime behavior is implemented here.
- No generated compose output, generated config, Wazuh state, Shuffle state, demo data, placeholder, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
