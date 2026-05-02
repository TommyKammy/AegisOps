# Phase 53.5 Wazuh First Agent Enrollment Helper Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/wazuh-smb-single-node-profile-contract.md`, `docs/deployment/wazuh-certificate-credential-contract.md`, `docs/deployment/wazuh-manager-intake-binding-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1135, #1136, #1140

This contract defines the bounded first Wazuh agent enrollment helper posture for one endpoint only.

It does not implement fleet-scale Wazuh agent management, Wazuh upgrade automation, Shuffle product profiles, release-candidate behavior, general-availability behavior, or runtime behavior beyond the reviewed enrollment-helper contract surface.

The required structured artifact is `docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml`.

## 1. Purpose

Phase 53.5 makes the first endpoint enrollment helper reviewable before later clean-host or source-health work can assume that a Wazuh endpoint agent can be enrolled safely.

The enrollment helper covers one reviewed endpoint only. It records prerequisites, one-endpoint enrollment steps, rollback and removal notes, safety warnings, and the rule that Wazuh enrollment state remains subordinate substrate context.

## 2. Authority Boundary

Wazuh is a subordinate detection substrate. Wazuh agent state, Wazuh manager enrollment state, Wazuh dashboard state, generated Wazuh config, setup commands, verifier output, issue-lint output, operator-facing status text, and setup evidence are not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, source, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Wazuh agent enrollment helper must preserve the rule that Wazuh agent state, manager state, dashboard state, placeholder secrets, sample credentials, fake values, TODO values, setup text, ticket state, AI output, browser state, UI cache, optional evidence, and downstream receipt state cannot become AegisOps truth or mutate AegisOps records without explicit AegisOps admission and linkage.

## 3. Enrollment Helper Contract

The helper is a contract for the `smb-single-node` Wazuh product profile and a single reviewed endpoint.

Fleet-scale Wazuh agent management remains out of scope.

Enrollment must use a reviewed Wazuh manager address placeholder such as `<wazuh-manager-host>` and a reviewed agent enrollment token or password custody reference.

The helper must not require committed secrets, inline credentials, customer-specific values, or workstation-local absolute paths.

The helper must not enable Wazuh Active Response as an AegisOps authority path, route directly from Wazuh to Shuffle, or treat Wazuh agent presence as source admission.

## 4. Prerequisites

The first endpoint enrollment helper requires:

- the accepted `smb-single-node` Wazuh profile contract;
- the reviewed Wazuh manager enrollment port and address placeholder;
- the reviewed enrollment secret custody reference;
- explicit operator approval for one endpoint;
- an identified rollback owner before enrollment starts; and
- a reviewed AegisOps intake binding if post-enrollment signal testing is performed.

Missing prerequisites block the helper. The helper must not infer endpoint, tenant, source, or customer linkage from hostnames, path shape, comments, dashboard labels, nearby metadata, or issue text.

## 5. First Endpoint Enrollment Steps

The bounded enrollment flow is:

1. Confirm the reviewed manager address placeholder and enrollment port for `<wazuh-manager-host>`.
2. Confirm the enrollment credential custody reference without exposing the credential value.
3. Install the Wazuh agent on one reviewed endpoint.
4. Enroll the agent to the reviewed Wazuh manager by using the custody-backed enrollment value.
5. Verify the endpoint appears only as a subordinate Wazuh signal source.

Post-enrollment signal review still depends on AegisOps admission and linkage. Wazuh agent status, manager status, dashboard presence, or setup output is not AegisOps source truth.

## 6. Rollback And Removal

Rollback must remove or disable the enrolled endpoint agent, revoke or rotate the enrollment credential when used, and preserve AegisOps-owned records as the workflow truth.

Removal must also delete or disable the agent registration from the Wazuh manager when appropriate and record an AegisOps-owned follow-up only when reviewed signal custody or source admission assumptions changed.

Rollback evidence is setup context only. It cannot close, reconcile, release, gate, or mutate AegisOps records without the AegisOps-owned record chain.

## 7. Safety Warnings

Safety warnings are mandatory:

- Do not commit Wazuh enrollment secrets, tokens, passwords, API keys, private keys, customer-specific values, generated secret files, or copied credentials.
- Do not treat placeholder credentials, sample secrets, fake values, TODO values, unsigned tokens, or default Wazuh credentials as valid.
- Do not enroll a fleet, bulk endpoint set, endpoint group, tenant-wide source, or unmanaged endpoint collection under this helper.
- Do not use Wazuh agent state, manager enrollment state, dashboard state, setup output, or optional endpoint evidence as AegisOps workflow truth.
- Do not enable Wazuh Active Response as an AegisOps authority path.
- Do not use workstation-local absolute paths in publishable guidance.

## 8. Validation Rules

Wazuh agent enrollment helper validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml` is missing;
- the contract document is missing;
- prerequisites, enrollment steps, rollback steps, or safety warnings are missing;
- the helper is not limited to one reviewed endpoint;
- enrollment secret custody is missing or replaced by a raw secret, placeholder, sample, fake value, TODO value, unsigned token, inline secret, or committed secret-looking value;
- committed customer-specific values or workstation-local absolute paths appear;
- the helper claims fleet-scale Wazuh agent management, Wazuh upgrade automation, Shuffle product profile work, release-candidate behavior, general-availability behavior, or commercial readiness;
- Wazuh agent state, manager state, dashboard state, generated config, setup output, verifier, or issue-lint state is described as AegisOps workflow, production, release, gate, closeout, source, approval, execution, evidence, or reconciliation truth; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<wazuh-manager-host>`, and `<first-endpoint-agent-name>`.

## 9. Forbidden Claims

- Wazuh agent state is AegisOps source truth.
- Wazuh agent enrollment is AegisOps workflow truth.
- Wazuh manager agent status is AegisOps evidence truth.
- Wazuh Active Response is an AegisOps authority path.
- Placeholder Wazuh enrollment secrets are valid credentials.
- Committed Wazuh enrollment secrets are acceptable.
- Phase 53.5 implements fleet-scale Wazuh agent management.
- Phase 53.5 implements Wazuh upgrade automation.
- Phase 53.5 implements Shuffle product profiles.
- Phase 53.5 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness.

## 10. Validation

Run `bash scripts/verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh`.

Run `bash scripts/test-verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1140 --config <supervisor-config-path>`.

The verifier must fail when the Wazuh enrollment helper contract or structured artifact is missing, when prerequisites, enrollment steps, rollback steps, or safety warnings are missing, when the helper permits fleet management, when raw secrets or committed secret-looking values appear, when Wazuh enrollment state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 11. Non-Goals

- No fleet-scale Wazuh agent management, Wazuh upgrade automation, Shuffle profile work, release-candidate behavior, general-availability behavior, Wazuh Active Response authority path, direct Wazuh-to-Shuffle shortcut, broad SIEM detector catalog, source-health projection, or runtime behavior is implemented here.
- No live secret, customer-specific value, private key, bearer token, API key, password, env file, generated config, generated secret, Wazuh agent state, Wazuh manager state, Wazuh dashboard state, Wazuh alert, Wazuh rule state, Wazuh timestamp, setup output, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
