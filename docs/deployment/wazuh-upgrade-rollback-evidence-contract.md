# Phase 53.7 Wazuh Upgrade And Rollback Evidence Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/wazuh-smb-single-node-profile-contract.md`, `docs/deployment/wazuh-source-health-projection-contract.md`, `docs/deployment/release-handoff-evidence-package.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1135, #1136, #1142

This contract defines release evidence expectations for Wazuh profile version changes in the `smb-single-node` product profile. It records the required before and after version evidence, rollback owner, rollback trigger, evidence references, known limitations, and profile-change handoff without implementing a live Wazuh upgrader.

The required structured artifact is `docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml`.

## 1. Purpose

The Wazuh upgrade and rollback evidence contract gives maintainers a reviewed release-evidence template for future Wazuh profile version changes.

The contract is intentionally evidence custody only. It does not execute upgrades, generate Wazuh configuration, mutate Wazuh manager, indexer, dashboard, agent, or certificate state, or change AegisOps workflow authority.

## 2. Authority Boundary

Wazuh is a subordinate detection substrate. Wazuh version state, upgrade evidence, rollback evidence, manager state, indexer state, dashboard state, agent state, generated config, source-health projection, verifier output, issue-lint output, operator-facing status text, release notes, and setup evidence are not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. A Wazuh profile version change must preserve the rule that Wazuh status, Wazuh version, manager reports, indexer contents, dashboard text, source-health projection, tickets, AI, browser, UI cache, optional evidence, and downstream receipt state cannot close, reconcile, approve, execute, release, gate, or otherwise mutate AegisOps records without explicit AegisOps admission and linkage.

## 3. Required Evidence Fields

| Field | Required content | Fail-closed rule |
| --- | --- | --- |
| `version_before` | The accepted Wazuh profile version before the reviewed change. | Missing, floating, `latest`, beta, RC, or inferred versions fail. |
| `version_after` | The reviewed target Wazuh profile version or explicit placeholder `<reviewed-target-wazuh-version>` before a real change is selected. | Missing or unreviewed target versions fail. |
| `rollback_owner` | Named accountable owner or owner group for rollback decisions. | Missing, placeholder-like, or inferred owner fails. |
| `rollback_trigger` | The reviewed condition that triggers rollback review. | Missing trigger or broad operator discretion without evidence fails. |
| `evidence_references` | AegisOps release-gate, source-health, profile diff, backup or restore, and validation evidence references. | Missing references or Wazuh-only references fail. |
| `known_limitations` | Accepted limitations for the version change, including deferred automation and fleet-scale exclusions. | Missing limitations or commercial-readiness claims fail. |
| `profile_change_handoff` | Handoff target, expected recipient, review state, and next profile-change action. | Missing handoff or inferred ownership fails. |

## 4. Component Coverage

| Component | Version evidence | Rollback evidence | Authority boundary |
| --- | --- | --- | --- |
| manager | Before and after Wazuh manager version or reviewed target placeholder. | Rollback returns to the last reviewed manager profile version and evidence set. | Manager version is substrate context only. |
| indexer | Before and after Wazuh indexer version or reviewed target placeholder. | Rollback returns to the last reviewed indexer profile version and evidence set. | Indexer version and contents are not AegisOps evidence truth. |
| dashboard | Before and after Wazuh dashboard version or reviewed target placeholder. | Rollback returns to the last reviewed dashboard profile version and evidence set. | Dashboard version and UI state are operator context only. |

## 5. Validation Rules

Wazuh upgrade and rollback evidence validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml` is missing;
- the contract document is missing;
- manager, indexer, or dashboard component coverage is missing or lacks component-level `version_before`, `version_after`, or `rollback_target` evidence;
- `version_before` or `version_after` evidence is missing;
- rollback owner or rollback trigger evidence is missing;
- rollback trigger evidence is placeholder-like or leaves rollback to broad operator discretion without a reviewed condition;
- evidence references are missing or only cite Wazuh-owned state;
- known limitations are missing;
- profile-change handoff expectations are missing;
- the artifact claims to implement a full automatic Wazuh upgrader;
- Wazuh version state, upgrade evidence, rollback evidence, source-health projection, dashboard state, manager state, or indexer state is described as AegisOps workflow truth, case truth, evidence truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, or closeout truth; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<runtime-env-file>`, and `<wazuh-profile-path>`.

## 6. Forbidden Claims

- Wazuh version state is AegisOps release truth.
- Wazuh upgrade evidence is AegisOps workflow truth.
- Wazuh rollback evidence closes AegisOps cases.
- Wazuh manager version is AegisOps source truth.
- Wazuh dashboard upgrade status is AegisOps approval truth.
- Wazuh indexer upgrade status is AegisOps evidence truth.
- Phase 53.7 implements a full Wazuh upgrader.
- Phase 53.7 implements Wazuh upgrade automation.
- Phase 53.7 implements fleet-scale Wazuh management.
- Phase 53.7 implements Shuffle product profiles.
- Phase 53.7 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness.

## 7. Validation

Run `bash scripts/verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh`.

Run `bash scripts/test-verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1142 --config <supervisor-config-path>`.

The verifier must fail when the upgrade and rollback evidence contract or artifact is missing, when version before or after evidence is missing, when rollback owner or trigger evidence is missing or placeholder-like, when component-level rollback targets are missing, when evidence references or known limitations are missing, when profile-change handoff expectations are missing, when Wazuh version or rollback state is promoted into AegisOps authority, when full upgrader behavior is claimed, or when publishable guidance uses workstation-local absolute paths.

## 8. Non-Goals

- No live Wazuh upgrader, Wazuh upgrade automation, Wazuh configuration generation, Wazuh certificate generation, fleet-scale Wazuh management, Shuffle product profile work, direct Wazuh-to-Shuffle shortcut, release-candidate behavior, general-availability behavior, commercial readiness, or Wazuh replacement readiness is implemented here.
- No Wazuh manager state, indexer state, dashboard state, agent state, version state, generated Wazuh config, source-health projection, upgrade evidence, rollback evidence, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
