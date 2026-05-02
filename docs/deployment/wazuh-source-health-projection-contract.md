# Phase 53.6 Wazuh Source-Health Projection Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/wazuh-smb-single-node-profile-contract.md`, `docs/deployment/wazuh-manager-intake-binding-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1135, #1138, #1141

This contract defines the Wazuh source-health projection for the `smb-single-node` product profile. It turns Wazuh substrate availability, signal freshness, parser, volume, and credential posture into subordinate AegisOps health context only. It does not implement Wazuh Active Response authority, case closure, workflow mutation, Shuffle product profiles, release-candidate behavior, general-availability behavior, or commercial readiness.

The required structured artifact is `docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml`.

## 1. Purpose

The source-health projection gives operators one reviewed view of whether the Wazuh manager, dashboard, indexer, intake, signal freshness, parser, event volume, and credential posture look usable for subordinate signal intake.

The projection is advisory context for source reliability and triage confidence. It is not the authoritative lifecycle source for AegisOps alerts, cases, evidence, approvals, actions, executions, reconciliations, release gates, or closeout decisions.

## 2. Authority Boundary

Wazuh is a subordinate detection substrate. Wazuh manager state, dashboard state, indexer state, intake status, signal freshness, parser failures, volume anomalies, credential-degraded posture, unavailable posture, mismatched posture, source-health projection, verifier output, issue-lint output, operator-facing status text, and setup evidence are not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Wazuh source-health projection must preserve the rule that substrate status, dashboard text, manager reports, indexer search results, parser diagnostics, volume counters, credential status, tickets, AI, browser, UI cache, optional evidence, and downstream receipt state cannot close, reconcile, approve, execute, release, gate, or otherwise mutate AegisOps records without explicit AegisOps admission and linkage.

## 3. Projection Inputs

| Component | Input surface | Required projection coverage | Authority boundary |
| --- | --- | --- | --- |
| manager | Wazuh manager service/API reachability and reviewed profile identity. | `available`, `degraded`, `unavailable`, `mismatched`. | Manager health remains subordinate signal-source context. |
| dashboard | Wazuh dashboard reachability through the reviewed proxy path. | `available`, `degraded`, `unavailable`, `mismatched`. | Dashboard status is operator-facing substrate context only. |
| indexer | Wazuh indexer availability and reviewed profile identity. | `available`, `degraded`, `unavailable`, `mismatched`. | Indexer contents and search status are not AegisOps evidence truth. |
| intake | Reviewed AegisOps Wazuh intake route and secret custody reference. | `available`, `credential_degraded`, `unavailable`, `mismatched`. | Intake acknowledgements remain pre-admission transport evidence until AegisOps links a record. |
| signal_freshness | Last accepted Wazuh analytic signal timestamp recorded by AegisOps. | `available`, `stale_source`, `unavailable`. | Freshness informs source reliability only and cannot close or reopen records. |
| parser | Reviewed parser and mapping result for accepted Wazuh payloads. | `available`, `degraded`, `parser_failure`. | Parser failures block reliable projection but do not rewrite case truth. |
| volume | Reviewed signal volume expectation for the `smb-single-node` Wazuh profile. | `available`, `degraded`, `volume_anomaly`. | Volume anomaly is an operator signal, not an AegisOps lifecycle transition. |
| credential | Secret custody, rotation compatibility, and redacted credential posture. | `available`, `credential_degraded`, `unavailable`, `mismatched`. | Credential posture must never expose secret material or validate placeholders. |

## 4. Projection States

| State | Meaning | Required handling |
| --- | --- | --- |
| available | Required Wazuh component signal is present, reviewed, and aligned with the accepted profile. | Surface as healthy subordinate context only. |
| degraded | Required Wazuh component signal is present but incomplete, lagging, or operationally weak. | Surface as degraded context and preserve AegisOps authority. |
| stale_source | The last accepted Wazuh signal is older than the reviewed freshness expectation. | Surface as stale source context without changing alert or case lifecycle truth. |
| parser_failure | Accepted Wazuh payloads cannot be parsed or mapped to the reviewed contract. | Surface parser failure, block false healthy projection, and keep durable records unchanged unless AegisOps admission already happened. |
| volume_anomaly | Reviewed Wazuh signal volume is unexpectedly silent, spiking, or outside bounded expectations. | Surface volume anomaly context without treating Wazuh volume as incident truth. |
| credential_degraded | Credential custody, rotation state, or proxy-secret posture is missing, stale, mismatched, placeholder-like, or otherwise not trusted. | Surface redacted credential degradation and do not expose secret material. |
| unavailable | Required Wazuh component or required AegisOps intake observation is absent. | Surface unavailable context and fail closed on source-health completeness. |
| mismatched | Component identity, profile version, route, custody reference, or source linkage does not match the accepted profile. | Surface mismatch context and do not infer authoritative linkage from naming or path shape. |

## 5. Projection Rules

| Rule | Required behavior | Authority boundary |
| --- | --- | --- |
| all-required-components-available | All required components must be represented before the aggregate projection can be `available`. | Aggregate health remains subordinate context only. |
| stale-last-accepted-signal | `stale_source` must be derived from the last accepted Wazuh signal recorded by AegisOps, not from dashboard freshness text alone. | Dashboard freshness text cannot become AegisOps lifecycle truth. |
| parser-failure-visible | `parser_failure` must stay visible and must prevent a false healthy aggregate projection. | Parser diagnostics cannot rewrite case truth. |
| volume-anomaly-visible | `volume_anomaly` must stay visible and must not become incident, case, or evidence truth by itself. | Volume counters are source-health context only. |
| credential-degraded-redacted | `credential_degraded` must use redacted state only and must reject placeholder, sample, fake, TODO, unsigned, inline, or committed credential material. | Credential posture must not expose secret material or validate placeholders. |
| manager-dashboard-indexer-unavailable-visible | Unavailable manager, dashboard, indexer, intake, or credential posture must stay visible as subordinate health context. | Component availability cannot close, approve, execute, reconcile, release, gate, or mutate AegisOps records. |
| component-mismatch-visible | Mismatched profile, route, component identity, custody reference, or source linkage must fail closed instead of inferring success. | Linkage must come from explicit AegisOps admission and binding. |
| no-authority-mutation | No source-health state may close, approve, execute, reconcile, release, gate, or mutate authoritative AegisOps records. | AegisOps control-plane records remain authoritative. |

## 6. Validation Rules

Wazuh source-health projection validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml` is missing;
- the contract document is missing;
- manager, dashboard, indexer, intake, signal freshness, parser, volume, or credential coverage is missing;
- `available`, `degraded`, `stale_source`, `parser_failure`, `volume_anomaly`, `credential_degraded`, `unavailable`, or `mismatched` coverage is missing;
- stale source, parser failure, volume anomaly, credential degradation, unavailable, or mismatched handling is missing;
- a credential-degraded state exposes secret material, accepts placeholder credentials, or validates committed credentials;
- Wazuh source-health state is described as AegisOps workflow truth, case truth, evidence truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, or closeout truth; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<runtime-env-file>`, and `<wazuh-profile-path>`.

## 7. Forbidden Claims

- Wazuh health status is AegisOps workflow truth.
- Wazuh source health closes AegisOps cases.
- Wazuh manager health is AegisOps source truth.
- Wazuh dashboard health is AegisOps workflow truth.
- Wazuh indexer health is AegisOps evidence truth.
- Credential-degraded state may expose secret material.
- Placeholder Wazuh health credentials are valid credentials.
- Source-health projection is AegisOps closeout truth.
- Phase 53.6 implements Wazuh Active Response authority.
- Phase 53.6 implements Shuffle product profiles.
- Phase 53.6 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness.

## 8. Validation

Run `bash scripts/verify-phase-53-6-wazuh-source-health-projection.sh`.

Run `bash scripts/test-verify-phase-53-6-wazuh-source-health-projection.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1141 --config <supervisor-config-path>`.

The verifier must fail when the source-health projection contract or artifact is missing, when component or state coverage is missing, when degraded/unavailable/parser/volume/credential/mismatched handling is missing, when Wazuh health is promoted into AegisOps authority, when credential-degraded state leaks secret material, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No Wazuh Active Response authority, Shuffle profile work, direct Wazuh-to-Shuffle shortcut, fleet-scale Wazuh management, broad SIEM detector catalog, release-candidate behavior, general-availability behavior, commercial readiness, or Wazuh replacement readiness is implemented here.
- No Wazuh manager state, dashboard state, indexer state, intake state, signal freshness, parser state, volume state, credential state, source-health projection, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
