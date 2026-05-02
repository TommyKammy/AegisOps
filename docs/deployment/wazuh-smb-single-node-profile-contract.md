# Phase 53.1 Wazuh SMB Single-Node Profile Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/combined-dependency-matrix.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1135, #1136

This contract defines the repo-owned Wazuh `smb-single-node` product-profile contract and version matrix. It does not implement certificate generation, Wazuh intake binding, sample detection fixtures, source-health projection, upgrade automation, fleet-scale Wazuh management, Shuffle product profiles, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The Wazuh profile gives Phase 53 one product-owned contract for manager, indexer, dashboard, resource needs, ports, volumes, certificates, and pinned versions.

The required structured artifact is `docs/deployment/profiles/smb-single-node/wazuh/profile.yaml`.

## 2. Authority Boundary

Wazuh is a subordinate detection substrate. Wazuh manager state, Wazuh indexer state, Wazuh dashboard state, generated Wazuh config, Wazuh alerts, Wazuh rule state, Wazuh certificate state, Wazuh version state, source-health projection, verifier output, issue-lint output, operator-facing status text, and setup evidence are not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Wazuh profile must preserve the rule that Wazuh status, alert, rule, manager, decoder, dashboard, indexer, generated-config, ticket, AI, browser, UI cache, optional evidence, and downstream receipt state cannot close, reconcile, approve, execute, release, gate, or otherwise mutate AegisOps records without explicit AegisOps admission and linkage.

## 3. Component Contract

| Component | Required | Version pin | Image pin | Resource expectation | Ports | Volumes | Certificate expectations | Authority boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| manager | Yes | `4.12.0` | `wazuh/wazuh-manager:4.12.0` | 2 vCPU, 6 GB RAM, 120 GB durable substrate storage. | `1514/tcp` internal agent event intake; `1514/udp` internal agent event intake; `1515/tcp` internal agent enrollment; `55000/tcp` internal manager API. | `wazuh-manager-data`; `wazuh-manager-rules`; `wazuh-manager-logs`. | `wazuh-manager-api-tls`; `wazuh-ingest-shared-secret-ref`. | Manager status and alert state remain subordinate signal context until admitted and linked by AegisOps. |
| indexer | Yes | `4.12.0` | `wazuh/wazuh-indexer:4.12.0` | 2 vCPU, 12 GB RAM, 250 GB durable substrate storage plus backup capacity. | `9200/tcp` internal indexer API; `9300/tcp` internal cluster transport. | `wazuh-indexer-data`; `wazuh-indexer-backup`. | `wazuh-indexer-tls`; `wazuh-indexer-admin-client-cert`. | Indexer contents and search status are detection substrate evidence only, not AegisOps source or workflow truth. |
| dashboard | Yes | `4.12.0` | `wazuh/wazuh-dashboard:4.12.0` | 1 vCPU, 2 GB RAM, bounded config/log storage. | `5601/tcp` internal dashboard UI through reviewed proxy only. | `wazuh-dashboard-config`. | `wazuh-dashboard-tls`; `wazuh-dashboard-indexer-client-cert`. | Dashboard state is operator-facing substrate context only and cannot become AegisOps workflow truth. |

## 4. Version Matrix

| Component | Accepted version | Pin type | Known incompatible versions | Upgrade note |
| --- | --- | --- | --- | --- |
| manager | `4.12.0` | exact | Wazuh 3.x; unreviewed Wazuh 5.x; `latest`; RC; beta. | Upgrade evidence is deferred to a later Phase 53 child issue. |
| indexer | `4.12.0` | exact | Wazuh 3.x; unreviewed Wazuh 5.x; `latest`; RC; beta. | Upgrade evidence is deferred to a later Phase 53 child issue. |
| dashboard | `4.12.0` | exact | Wazuh 3.x; unreviewed Wazuh 5.x; `latest`; RC; beta. | Upgrade evidence is deferred to a later Phase 53 child issue. |

## 5. Profile Expectations

The Wazuh profile must preserve these expectations:

- Resource floor: the recommended first-user host remains 8 vCPU, 32 GB RAM, and 500 GB durable disk, with Wazuh growth accounted for separately from PostgreSQL.
- Ports: Wazuh manager, indexer, and dashboard ports are internal or substrate-owned; AegisOps receives Wazuh signals only through the reviewed proxy intake route.
- Volumes: Wazuh manager, indexer, dashboard, logs, rules, certificates, and backups are separate from AegisOps PostgreSQL state and AegisOps evidence custody.
- Certificates: certificate and secret references are trusted custody references only; placeholder, sample, fake, TODO, unsigned, or inline secret values are invalid.
- Source health: source-health projection is deferred and cannot use Wazuh dashboard or manager state as authoritative workflow truth.

## 6. Validation Rules

Wazuh profile validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/wazuh/profile.yaml` is missing;
- the contract document is missing;
- manager, indexer, or dashboard coverage is missing;
- manager, indexer, or dashboard version pins are missing, floating, RC, beta, `latest`, or otherwise not exact;
- resource expectations, ports, volumes, certificate expectations, known incompatible versions, or authority-boundary text are missing;
- Wazuh status, version state, dashboard state, manager state, indexer state, generated config, verifier output, or source-health projection is described as AegisOps workflow truth, production truth, release truth, gate truth, closeout truth, approval truth, execution truth, or reconciliation truth;
- placeholder secrets, sample credentials, fake values, TODO values, unsigned tokens, inline secrets, raw forwarded headers, or inferred tenant/source linkage are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<runtime-env-file>`, and `<wazuh-profile-path>`.

## 7. Forbidden Claims

- Wazuh status is AegisOps workflow truth.
- Wazuh alert status is AegisOps case truth.
- Wazuh manager state is AegisOps source truth.
- Wazuh dashboard state is AegisOps approval truth.
- Wazuh indexer state is AegisOps evidence truth.
- Wazuh version state is AegisOps release truth.
- Source-health projection is AegisOps closeout truth.
- Placeholder secrets are valid credentials.
- Raw forwarded headers are trusted identity.
- Phase 53.1 implements Wazuh intake binding.
- Phase 53.1 implements Wazuh certificate generation.
- Phase 53.1 implements Wazuh source-health projection.
- Phase 53.1 implements Wazuh upgrade automation.
- Phase 53.1 implements Shuffle product profiles.
- Phase 53.1 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness.

## 8. Validation

Run `bash scripts/verify-phase-53-1-wazuh-profile-contract.sh`.

Run `bash scripts/test-verify-phase-53-1-wazuh-profile-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1136 --config <supervisor-config-path>`.

The verifier must fail when the Wazuh profile or contract is missing, when manager, indexer, or dashboard rows are missing, when Wazuh versions are unpinned or floating, when resource, port, volume, certificate, incompatible-version, or authority-boundary expectations are missing, when Wazuh substrate state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No certificate generation, Wazuh intake binding, sample detection fixture, source-health projection, upgrade automation, fleet-scale Wazuh management, Shuffle profile work, release-candidate behavior, general-availability behavior, or runtime behavior is implemented here.
- No Wazuh manager state, Wazuh indexer state, Wazuh dashboard state, Wazuh alert, Wazuh version, Wazuh certificate, generated Wazuh config, source-health projection, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
