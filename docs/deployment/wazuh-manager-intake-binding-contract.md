# Phase 53.3 Wazuh Manager Intake Binding Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/wazuh-smb-single-node-profile-contract.md`, `docs/deployment/wazuh-certificate-credential-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1135, #1136, #1137, #1138

This contract defines the Wazuh manager-to-AegisOps intake URL binding, shared-secret custody reference, reviewed proxy binding, required provenance fields, and analytic-signal admission posture for the `smb-single-node` Wazuh product profile.

It does not implement source-health projection, Wazuh upgrade automation, fleet-scale Wazuh management, Shuffle product profiles, release-candidate behavior, general-availability behavior, or runtime behavior beyond the reviewed intake-binding contract surface.

The required structured artifact is `docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml`.

## 1. Purpose

Phase 53.3 makes the Wazuh manager-to-AegisOps intake binding enforceable before later Wazuh profile setup, source-health, or live clean-host work can rely on Wazuh-origin events.

The contract covers the reviewed intake URL, proxy route, manager delivery posture, shared-secret custody reference, required provenance fields, and the rule that Wazuh-origin input remains a candidate analytic signal until AegisOps admission and linkage.

## 2. Authority Boundary

Wazuh is a subordinate detection substrate. Wazuh manager state, Wazuh dashboard state, Wazuh indexer state, Wazuh alert state, Wazuh rule state, Wazuh timestamp state, webhook acknowledgement, generated Wazuh config, verifier output, issue-lint output, operator-facing status text, and setup evidence are not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, source, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The Wazuh intake binding must preserve the rule that Wazuh alert, manager, decoder, rule, status, timestamp, webhook acknowledgement, raw forwarded header, placeholder secret, inferred source linkage, ticket, AI, browser, UI cache, optional evidence, and downstream receipt state cannot become AegisOps truth or mutate AegisOps records without explicit AegisOps admission and linkage.

## 3. Intake Binding Contract

The reviewed AegisOps intake URL is `/intake/wazuh`.

The reviewed proxy route binding is `aegisops-proxy:/intake/wazuh -> aegisops-control-plane:/intake/wazuh`.

The Wazuh manager must send alerts to AegisOps through the reviewed proxy route only.

The shared-secret custody reference must be `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH`.

Raw shared-secret values, placeholder secrets, sample secrets, fake values, TODO values, unsigned tokens, raw forwarded headers, or inferred source linkage must fail validation.

The reviewed binding is a contract for the `smb-single-node` Wazuh product profile. It does not authorize direct Wazuh-to-Shuffle shortcuts, direct Wazuh Active Response as an authority path, Wazuh dashboard status as workflow truth, or Wazuh alert status as case truth.

## 4. Required Provenance Fields

Wazuh-origin events must carry explicit provenance before AegisOps admission can treat them as candidate analytic signals:

- `source_family`
- `source_system`
- `source_component`
- `source_id`
- `event_id`
- `event_timestamp`
- `wazuh_manager_id`
- `wazuh_rule_id`
- `wazuh_rule_level`
- `ingest_channel`
- `admission_channel`
- `secret_custody_reference`
- `proxy_route`
- `reviewed_by`

The required provenance must be explicit. It must not be inferred from hostnames, URL paths, nearby comments, dashboard names, manager names, forwarded headers, tenant hints, or issue text.

## 5. Analytic-Signal Admission

Wazuh-origin input remains a candidate analytic signal until AegisOps admits it and links it to an AegisOps record.

A Wazuh alert, manager status, dashboard status, rule state, timestamp, or webhook acknowledgement must not be treated as case, alert, reconciliation, release, gate, closeout, or source truth before AegisOps admission and linkage.

Admission must fail closed when the intake URL, shared-secret custody reference, reviewed proxy binding, or required provenance fields are missing, malformed, placeholder-backed, unsigned, inferred, forwarded-header-derived, or otherwise untrusted.

Admission may produce or link an AegisOps analytic signal only after the reviewed AegisOps boundary validates the binding and preserves the Wazuh payload as subordinate evidence. Later alert, case, evidence, approval, action, execution, and reconciliation records must still come from AegisOps-owned records.

## 6. Validation Rules

Wazuh intake binding validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml` is missing;
- the contract document is missing;
- the reviewed intake URL is missing or placeholder-backed;
- the reviewed proxy route binding is missing;
- the manager delivery posture is not reviewed-proxy-only;
- the shared-secret custody reference is missing or replaced by a raw secret, placeholder, sample, fake value, TODO value, unsigned token, inline secret, or committed secret-looking value;
- required provenance fields are missing;
- raw forwarded headers or inferred source linkage are treated as trusted input;
- Wazuh-origin input is promoted into AegisOps authority before admission and linkage;
- Wazuh manager, dashboard, indexer, alert, rule, timestamp, webhook, generated-config, verifier, or issue-lint state is described as AegisOps workflow, production, release, gate, closeout, source, approval, execution, or reconciliation truth; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<wazuh-intake-url>`, and `<wazuh-secret-ref>`.

## 7. Forbidden Claims

- Wazuh-origin input is AegisOps case truth before admission.
- Wazuh alert status is AegisOps case truth.
- Wazuh manager state is AegisOps source truth.
- Wazuh dashboard state is AegisOps workflow truth.
- Webhook acknowledgement is AegisOps reconciliation truth.
- Wazuh timestamp is AegisOps release truth.
- Placeholder Wazuh intake secrets are valid credentials.
- Raw forwarded headers are trusted identity.
- Inferred Wazuh source linkage is valid admission.
- Phase 53.3 implements Wazuh source-health projection.
- Phase 53.3 implements Wazuh upgrade automation.
- Phase 53.3 implements Shuffle product profiles.
- Phase 53.3 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness.

## 8. Validation

Run `bash scripts/verify-phase-53-3-wazuh-intake-binding-contract.sh`.

Run `bash scripts/test-verify-phase-53-3-wazuh-intake-binding-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1138 --config <supervisor-config-path>`.

The verifier must fail when the Wazuh intake binding contract or structured artifact is missing, when the intake URL is missing, when the shared-secret custody reference is missing, when required Wazuh provenance fields are missing, when raw secrets or committed secret-looking values appear, when forwarded headers or inferred linkage are trusted, when Wazuh-origin input is promoted into AegisOps authority before admission and linkage, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No source-health projection, upgrade automation, fleet-scale Wazuh management, Shuffle profile work, release-candidate behavior, general-availability behavior, direct Wazuh-to-Shuffle shortcut, Wazuh Active Response authority path, or broad SIEM detector catalog is implemented here.
- No live secret, customer-specific value, private key, bearer token, API key, password, env file, generated config, generated secret, Wazuh manager state, Wazuh indexer state, Wazuh dashboard state, Wazuh alert, Wazuh rule state, Wazuh timestamp, webhook acknowledgement, verifier output, issue-lint output, ticket, AI output, browser state, UI cache, downstream receipt, log text, or operator-facing summary becomes authoritative AegisOps truth.
