# Phase 52.3 Combined Dependency Matrix

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/single-customer-profile.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`
- **Related Issues**: #1063, #1065, #1066

This matrix defines dependency documentation and verifier expectations for the executable first-user stack only. It does not implement an installer, compose generation, Wazuh product-profile runtime behavior, Shuffle product-profile runtime behavior, a full host preflight engine, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The combined dependency matrix gives platform admins one repo-owned place to review expected component versions, host footprint, ports, volumes, certificate requirements, incompatible versions, and the fields a later host preflight contract must consume.

The matrix covers the first-user executable stack shape: AegisOps, Wazuh, Shuffle, PostgreSQL, proxy, Docker, and Docker Compose.

## 2. Authority Boundary

Dependency expectations are setup readiness evidence only. Docker, Docker Compose, Wazuh, Shuffle, PostgreSQL, proxy, port, certificate, volume, host sizing, or version state is not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This matrix cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. Dependency checks must preserve the Phase 51.6 rule that Wazuh, Shuffle, generated config, placeholders, tickets, AI, browser state, UI cache, logs, and downstream receipts cannot become workflow truth or production truth.

## 3. Host Footprint

The first-user stack baseline assumes one SMB single-node host profile before any HA, multi-customer, or managed-service deployment work exists.

| Host tier | CPU | RAM | Disk | Notes |
| --- | --- | --- | --- | --- |
| Minimum rehearsal | 4 vCPU | 16 GB RAM | 250 GB durable disk plus separate backup capacity | Sufficient for disposable rehearsal and verifier-driven setup review only. |
| Recommended first-user | 8 vCPU | 32 GB RAM | 500 GB durable disk plus separate backup capacity | Recommended for one named customer environment with Wazuh intake, PostgreSQL state, proxy ingress, and bounded Shuffle delegation. |
| Out of scope | Cluster sizing | HA memory sizing | Multi-node storage sizing | Enterprise cluster, MSSP, zero-downtime, and vendor-managed HA sizing are later scope. |

## 4. Dependency Matrix

| Component | Version expectation | Host CPU/RAM/disk expectation | Ports | Volumes | Certificate requirements | Known incompatibilities | Host preflight follow-up fields | Authority boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AegisOps | Reviewed repository revision plus Python/runtime dependencies from the repo-owned control-plane package; image tags or source revisions must be release-bound, not floating latest. | Included in recommended 8 vCPU, 32 GB RAM, 500 GB disk host; control-plane logs and evidence must not share mutable database storage. | Proxy-published operator, readiness, runtime inspection, and Wazuh intake routes only; backend port remains internal. | Runtime env reference, evidence directory, log directory, and control-plane migration assets. | Protected-surface reverse-proxy secret, admin bootstrap token, break-glass token, and reviewed identity-provider binding must come from trusted custody. | Floating image tags, placeholder secrets, unsigned identity hints, direct backend exposure, raw forwarded-header trust, or skipped migration bootstrap are incompatible. | `AEGISOPS_PREFLIGHT_AEGISOPS_REVISION`, `AEGISOPS_PREFLIGHT_AEGISOPS_IMAGE_TAG`, `AEGISOPS_PREFLIGHT_CONTROL_PLANE_PORT`, `AEGISOPS_PREFLIGHT_AEGISOPS_EVIDENCE_VOLUME`, `AEGISOPS_PREFLIGHT_AEGISOPS_SECRET_REFS` | AegisOps dependency state is setup readiness evidence only and cannot replace AegisOps-owned workflow records. |
| Wazuh | Reviewed Wazuh 4.x manager profile for the first-user intake path; exact product-profile pin is deferred to the Wazuh profile issue. | Included in recommended host sizing unless deployed as an external reviewed substrate; retention growth must be accounted for separately from PostgreSQL. | Wazuh manager/API ports stay internal or substrate-owned; only the reviewed Wazuh intake route reaches AegisOps through the proxy. | Wazuh manager data, rules, decoder, and log volumes must be separate from AegisOps PostgreSQL state. | Wazuh ingest shared secret and Wazuh ingest reverse-proxy secret must come from trusted custody. | Wazuh 3.x, unreviewed Wazuh 5.x, direct Wazuh-to-automation routing, treating Wazuh alert status as AegisOps case truth, and placeholder ingest secrets are incompatible. | `AEGISOPS_PREFLIGHT_WAZUH_VERSION`, `AEGISOPS_PREFLIGHT_WAZUH_INGEST_ROUTE`, `AEGISOPS_PREFLIGHT_WAZUH_SECRET_REFS`, `AEGISOPS_PREFLIGHT_WAZUH_VOLUME_REFS` | Wazuh detects and provides subordinate upstream signal context; Wazuh state is not AegisOps workflow truth. |
| Shuffle | Reviewed Shuffle deployment profile for delegated low-risk automation; exact product-profile pin is deferred to the Shuffle profile issue. | Included in recommended host sizing only when bounded delegated execution is enabled; workflow execution artifacts must not share authoritative AegisOps state storage. | Shuffle API, webhook, and callback ports stay internal or proxy-mediated through reviewed callback routes. | Shuffle app data and workflow catalog volumes must be separated from PostgreSQL and AegisOps evidence custody. | Shuffle API credential, callback secret, and workflow-catalog custody must come from trusted secret references. | Unreviewed workflow packs, placeholder API keys, direct Wazuh-to-Shuffle execution, and treating Shuffle workflow success as AegisOps reconciliation truth are incompatible. | `AEGISOPS_PREFLIGHT_SHUFFLE_VERSION`, `AEGISOPS_PREFLIGHT_SHUFFLE_API_ROUTE`, `AEGISOPS_PREFLIGHT_SHUFFLE_CALLBACK_ROUTE`, `AEGISOPS_PREFLIGHT_SHUFFLE_SECRET_REFS`, `AEGISOPS_PREFLIGHT_SHUFFLE_VOLUME_REFS` | Shuffle executes reviewed delegated routine work only; Shuffle state is not AegisOps execution or reconciliation truth. |
| PostgreSQL | PostgreSQL 15 or 16 until a later migration compatibility review changes the pin. | Requires durable disk with backup capacity separate from data capacity; database memory pressure must not starve the control-plane process. | Database port remains internal to the Compose or host service boundary and must not be published as a user-facing ingress path. | PostgreSQL data volume and PostgreSQL backup volume must be distinct. | PostgreSQL credential source must come from trusted custody; direct DSNs with secret material are incompatible. | PostgreSQL below 15, unreviewed PostgreSQL 17+, destructive schema recreation, placeholder DSNs, shared data and backup volumes, and external write access outside the control plane are incompatible. | `AEGISOPS_PREFLIGHT_POSTGRES_VERSION`, `AEGISOPS_PREFLIGHT_POSTGRES_PORT`, `AEGISOPS_PREFLIGHT_POSTGRES_DATA_VOLUME`, `AEGISOPS_PREFLIGHT_POSTGRES_BACKUP_VOLUME`, `AEGISOPS_PREFLIGHT_POSTGRES_SECRET_REFS` | PostgreSQL stores AegisOps-owned records, but PostgreSQL process state alone is not workflow truth. |
| Proxy | Reviewed reverse-proxy implementation selected by the deployment package; proxy config revision must be release-bound. | Included in recommended host sizing; TLS material and access logs require bounded storage and rotation. | Public HTTPS port, optional HTTP redirect port, protected-surface routes, readiness route, runtime inspection route, and Wazuh intake route. | Proxy config, TLS certificate chain reference, TLS private-key reference, and bounded access-log storage. | Ingress TLS certificate chain, ingress TLS private key, protected-surface boundary secret, Wazuh reverse-proxy secret, trusted proxy CIDR binding, and reviewed identity-provider binding are required. | Raw `X-Forwarded-*`, `Forwarded`, host, proto, tenant, or user-id trust without normalized proxy boundary; direct backend exposure; placeholder TLS material; and expired certificate custody are incompatible. | `AEGISOPS_PREFLIGHT_PROXY_VERSION`, `AEGISOPS_PREFLIGHT_PROXY_PUBLIC_PORTS`, `AEGISOPS_PREFLIGHT_PROXY_TLS_REFS`, `AEGISOPS_PREFLIGHT_PROXY_TRUSTED_CIDRS`, `AEGISOPS_PREFLIGHT_PROXY_ROUTE_MAP` | The proxy enforces ingress and normalization boundaries; proxy header or port state is not AegisOps workflow truth. |
| Docker | Docker Engine 24 or 25 for first-user stack rehearsal and setup verification until a later runtime support review changes the expectation. | Host must satisfy the recommended first-user CPU, RAM, and disk tier before dependency checks are accepted. | Docker daemon socket or service endpoint must not be exposed as a user-facing AegisOps port. | Docker image cache, named volumes, and logs must preserve separation between AegisOps state, PostgreSQL data, backups, and optional substrate data. | No Docker daemon certificate requirement is approved for the local single-node profile; if remote daemon TLS is introduced later it needs a separate reviewed certificate custody contract. | Docker Engine below 24, rootless or remote-daemon profiles not covered by the deployment package, daemon socket exposure to untrusted users, and floating image pulls are incompatible. | `AEGISOPS_PREFLIGHT_DOCKER_ENGINE_VERSION`, `AEGISOPS_PREFLIGHT_DOCKER_CONTEXT`, `AEGISOPS_PREFLIGHT_DOCKER_ROOTLESS_MODE`, `AEGISOPS_PREFLIGHT_DOCKER_VOLUME_DRIVER`, `AEGISOPS_PREFLIGHT_DOCKER_SOCKET_EXPOSURE` | Docker health or container state is setup readiness evidence only and cannot become AegisOps workflow truth. |
| Docker Compose | Docker Compose plugin v2.24 or newer; legacy standalone `docker-compose` v1 is not an accepted first-user stack interface. | Compose must run on a host that satisfies the recommended first-user CPU, RAM, and disk tier and preserves named-volume separation. | Compose-published ports must match the reviewed proxy and internal-service exposure policy. | Compose project name, named volumes, env-file reference, and bind-mount policy must be explicit and repo-relative or placeholder-backed. | Compose must reference secret and certificate files through trusted secret refs or documented placeholders; inline secret material is incompatible. | Standalone Compose v1, unreviewed Compose v3-only semantics that change health dependency behavior, host absolute path guidance in publishable docs, inline secrets, and published database/backend ports are incompatible. | `AEGISOPS_PREFLIGHT_COMPOSE_VERSION`, `AEGISOPS_PREFLIGHT_COMPOSE_PROJECT_NAME`, `AEGISOPS_PREFLIGHT_COMPOSE_FILE`, `AEGISOPS_PREFLIGHT_COMPOSE_ENV_FILE`, `AEGISOPS_PREFLIGHT_COMPOSE_PUBLISHED_PORTS`, `AEGISOPS_PREFLIGHT_COMPOSE_VOLUME_REFS` | Compose orchestration result is setup readiness evidence only and cannot become AegisOps workflow truth. |

Known incompatible versions must be explicit and must fail host preflight follow-up until reviewed.

## 5. Host Preflight Follow-Up Contract

This issue does not implement the full host preflight engine. A later host preflight issue must consume the `AEGISOPS_PREFLIGHT_*` fields named in this matrix and fail closed when a required field is missing, malformed, placeholder-backed, stale, incompatible, inferred from naming conventions, or only partially trusted.

The existing install preflight remains the current verifier for runtime input, secret custody, storage separation, migration bootstrap, and optional-extension non-blocking behavior. The dependency-matrix follow-up must link back to that contract instead of redefining runtime authority.

Host preflight output may report readiness evidence, incompatibility findings, missing prerequisites, and safe next actions. It must not promote Docker, Compose, Wazuh, Shuffle, port, certificate, or version state into AegisOps workflow truth.

## 6. Validation Rules

Matrix validation must fail closed when:

- any required component row is missing, including AegisOps, Wazuh, Shuffle, PostgreSQL, proxy, Docker, or Docker Compose;
- CPU, RAM, disk, ports, volumes, certificate requirements, known incompatibilities, or preflight follow-up fields are missing;
- known incompatible versions are omitted or described as warnings only;
- substrate version state, port state, certificate state, Docker state, Compose state, Wazuh state, or Shuffle state is described as workflow truth;
- placeholder secrets, sample credentials, TODO values, inline secrets, raw forwarded headers, or unreviewed scope inference are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<compose-file>`, and `<runtime-env-file>`.

## 7. Forbidden Claims

- Substrate version state is AegisOps workflow truth.
- Docker status is AegisOps workflow truth.
- Docker Compose status is AegisOps workflow truth.
- Wazuh alert status is AegisOps case truth.
- Shuffle workflow success is AegisOps reconciliation truth.
- Placeholder secrets are valid credentials.
- Raw forwarded headers are trusted identity.
- This matrix implements the host preflight engine.
- This matrix implements Wazuh product-profile runtime behavior.
- This matrix implements Shuffle product-profile runtime behavior.

## 8. Validation

Run `bash scripts/verify-phase-52-3-combined-dependency-matrix.sh`.

Run `bash scripts/test-verify-phase-52-3-combined-dependency-matrix.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1066 --config <supervisor-config-path>`.

The verifier must fail when the matrix is missing, when AegisOps, Wazuh, Shuffle, PostgreSQL, proxy, Docker, or Docker Compose coverage is missing, when CPU, RAM, disk, ports, volumes, certificate requirements, known incompatibilities, or preflight follow-up fields are missing, when dependency state is treated as workflow truth, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No installer, compose generation, profile generation, host probing, or runtime behavior is implemented here.
- No Wazuh product-profile runtime behavior or Shuffle product-profile runtime behavior is implemented here.
- No Docker, Docker Compose, Wazuh, Shuffle, PostgreSQL, proxy, port, certificate, volume, host sizing, preflight, setup, generated-config, placeholder, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
