# Phase 54.1 Shuffle SMB Single-Node Profile Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/combined-dependency-matrix.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1154, #1155
- **Upstream Reference**: Shuffle release `v2.2.0` and the reviewed self-hosted compose topology from `https://github.com/Shuffle/Shuffle/releases/tag/v2.2.0` and `https://github.com/Shuffle/Shuffle/blob/v2.2.0/docker-compose.yml`

This contract defines the repo-owned Shuffle `smb-single-node` product-profile contract and version matrix. It does not implement workflow template fields, template imports, delegation binding, receipt normalization, fallback, Wazuh profile work, broad SOAR catalog expansion, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The Shuffle profile gives Phase 54 one product-owned contract for frontend, backend, orborus, worker image, OpenSearch dependency, service topology, ports, volumes, credentials, API URL, callback URL, dependency expectations, and pinned versions.

The required structured artifact is `docs/deployment/profiles/smb-single-node/shuffle/profile.yaml`.

## 2. Authority Boundary

Shuffle is a subordinate routine automation substrate. Shuffle frontend state, backend state, orborus state, worker state, OpenSearch state, workflow success, workflow failure, retry state, workflow payloads, callback payloads, workflow canvas state, generated config, logs, API responses, version state, verifier output, issue-lint output, operator-facing status text, and setup evidence are not alert, case, evidence, approval, action request, execution receipt, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Shuffle profile must preserve the rule that Shuffle workflow success, failure, retry, payload, callback state, API state, generated config, ticket, AI, browser, UI cache, optional evidence, and downstream receipt state cannot close, reconcile, approve, execute, release, gate, or otherwise mutate AegisOps records without explicit AegisOps approval, action intent, receipt, and reconciliation records.

## 3. Component Contract

| Component | Required | Version pin | Image pin | Resource expectation | Ports | Volumes | Credential expectations | Authority boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frontend | Yes | `2.2.0` | `ghcr.io/shuffle/shuffle-frontend:2.2.0` | 1 vCPU, 1 GB RAM, bounded config/log storage. | `80/tcp` and `443/tcp` internal frontend UI through reviewed proxy only. | `shuffle-frontend-config`. | `shuffle-frontend-session-secret-ref`. | Frontend UI and browser state remain operator context only and cannot become AegisOps workflow truth. |
| backend | Yes | `2.2.0` | `ghcr.io/shuffle/shuffle-backend:2.2.0` | 2 vCPU, 4 GB RAM, bounded app/file storage. | `5001/tcp` internal API only through reviewed proxy route. | `shuffle-apps`; `shuffle-files`; `shuffle-docker-socket-proxy`. | `shuffle-api-credential-ref`; `shuffle-callback-secret-ref`; `shuffle-encryption-modifier-ref`. | Backend API and callback payloads remain subordinate delegated-execution context until admitted by AegisOps records. |
| orborus | Yes | `2.2.0` | `ghcr.io/shuffle/shuffle-orborus:2.2.0` | 1 vCPU, 2 GB RAM, bounded worker orchestration capacity. | No direct host ports; outbound worker orchestration only. | `shuffle-docker-socket-proxy`; `shuffle-worker-runtime`. | `shuffle-orborus-auth-ref`; `shuffle-worker-registry-ref`. | Orborus scheduling and retry state cannot become AegisOps execution or reconciliation truth. |
| worker | Yes | `2.2.0` | `ghcr.io/shuffle/shuffle-worker:2.2.0` | Ephemeral worker capacity bounded by reviewed concurrency. | No direct host ports; callback egress returns through reviewed callback route only. | `shuffle-worker-ephemeral`; `shuffle-app-execution-cache`. | `shuffle-worker-runtime-secret-ref`; `shuffle-app-auth-custody-ref`. | Worker output is downstream execution context only until normalized into an AegisOps execution receipt. |
| opensearch | Yes | `3.2.0` | `opensearchproject/opensearch:3.2.0` | 2 vCPU, 6 GB RAM, 120 GB durable substrate storage. | `9200/tcp` internal Shuffle datastore API only. | `shuffle-database`. | `shuffle-opensearch-admin-secret-ref`. | Shuffle datastore contents are substrate state only and cannot become AegisOps release, gate, or reconciliation truth. |

## 4. Version Matrix

| Component | Accepted version | Pin type | Known incompatible versions | Upgrade note |
| --- | --- | --- | --- | --- |
| frontend | `2.2.0` | exact | Shuffle 1.x; unreviewed Shuffle 2.3.x; `latest`; RC; beta. | UI changes require later guided first-user journey and delegation-surface review. |
| backend | `2.2.0` | exact | Shuffle 1.x; unreviewed Shuffle 2.3.x; `latest`; RC; beta. | API changes require later callback/API boundary and receipt-normalization evidence. |
| orborus | `2.2.0` | exact | Shuffle 1.x; unreviewed Shuffle 2.3.x; `latest`; RC; beta. | Orchestration changes require later delegation-binding and fallback evidence. |
| worker | `2.2.0` | exact | Shuffle 1.x; unreviewed Shuffle 2.3.x; `latest`; RC; beta. | Worker image changes require later workflow-catalog and delegation-binding evidence. |
| opensearch | `3.2.0` | exact | OpenSearch 1.x; unreviewed OpenSearch 4.x; `latest`; RC; beta. | Datastore changes require later backup, restore, and volume-custody evidence. |

## 5. Profile Expectations

The Shuffle profile must preserve these expectations:

- Service topology: frontend, backend, orborus, worker image, and OpenSearch are explicitly represented; optional monitoring, direct Docker socket exposure, and unreviewed workflow packs are not approved by this contract.
- API URL: the reviewed internal API URL is `http://shuffle-backend:5001`; external access must be proxy-mediated and cannot imply direct backend exposure.
- Callback URL: the reviewed AegisOps callback URL placeholder is `<aegisops-shuffle-callback-url>` and must bind to an AegisOps-owned callback route before runtime use.
- Ports: Shuffle UI, API, worker, and datastore ports are internal or proxy-mediated; direct host exposure is not approved by this contract.
- Volumes: Shuffle app, file, worker, and datastore volumes are separated from PostgreSQL and AegisOps evidence custody.
- Credentials: Shuffle API credentials, callback secrets, encryption modifiers, worker auth, app auth custody, and OpenSearch admin secrets are trusted secret references only; placeholder, sample, fake, TODO, unsigned, inline, or default secret values are invalid.
- Dependency expectations: Shuffle depends on reviewed Docker/Compose posture, proxy custody, trusted secret references, AegisOps approval/action-request records, and later workflow-catalog custody before delegated execution can run.

## 6. Validation Rules

Shuffle profile validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/shuffle/profile.yaml` is missing;
- the contract document is missing;
- frontend, backend, orborus, worker, or OpenSearch coverage is missing;
- frontend, backend, orborus, worker, or OpenSearch version pins are missing, floating, RC, beta, `latest`, or otherwise not exact;
- service topology, resource expectations, ports, volumes, credential expectations, API URL, callback URL, dependency expectations, known incompatible versions, or authority-boundary text are missing;
- Shuffle workflow success, failure, retry, payload, callback state, API state, version state, generated config, verifier output, or datastore state is described as AegisOps workflow truth, production truth, release truth, gate truth, closeout truth, approval truth, execution truth, or reconciliation truth;
- placeholder secrets, sample credentials, fake values, TODO values, unsigned tokens, inline secrets, raw forwarded headers, or inferred tenant/source/delegation linkage are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<runtime-env-file>`, `<shuffle-profile-path>`, and `<aegisops-shuffle-callback-url>`.

## 7. Forbidden Claims

- Shuffle workflow success is AegisOps reconciliation truth.
- Shuffle workflow failure is AegisOps execution truth.
- Shuffle callback payload is AegisOps execution receipt truth.
- Shuffle backend state is AegisOps approval truth.
- Shuffle frontend state is AegisOps workflow truth.
- Shuffle worker state is AegisOps closeout truth.
- Shuffle OpenSearch state is AegisOps release truth.
- Placeholder Shuffle API keys are valid credentials.
- Raw forwarded headers are trusted callback identity.
- Phase 54.1 implements workflow template imports.
- Phase 54.1 implements delegation binding.
- Phase 54.1 implements receipt normalization.
- Phase 54.1 implements Shuffle fallback behavior.
- Phase 54.1 implements Wazuh product profiles.
- Phase 54.1 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement.

## 8. Validation

Run `bash scripts/verify-phase-54-1-shuffle-profile-contract.sh`.

Run `bash scripts/test-verify-phase-54-1-shuffle-profile-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1155 --config <supervisor-config-path>`.

The verifier must fail when the Shuffle profile or contract is missing, when frontend, backend, orborus, worker, or OpenSearch rows are missing, when Shuffle or OpenSearch versions are unpinned or floating, when service, API, callback, port, volume, credential, dependency, incompatible-version, or authority-boundary expectations are missing, when Shuffle substrate state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No workflow template fields, template imports, delegation binding, receipt normalization, fallback, broad SOAR action catalog, marketplace work, Wazuh profile work, release-candidate behavior, general-availability behavior, Controlled Write default enablement, Hard Write default enablement, or runtime behavior is implemented here.
- No Shuffle frontend state, backend state, orborus state, worker state, OpenSearch state, workflow success, workflow failure, retry state, payload, callback payload, API response, version, generated config, workflow canvas, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
