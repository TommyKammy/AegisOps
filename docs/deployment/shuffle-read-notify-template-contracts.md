# Phase 54.5 Read/Notify Shuffle Template Contracts

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-reviewed-workflow-template-contract.md`, `docs/deployment/shuffle-notify-identity-owner-template-import-contract.md`, `docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md`, `docs/phase-52-closeout-evaluation.md`, `docs/phase-52-7-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1154, #1156, #1159

This contract defines repo-owned `enrichment_only_lookup`, `operator_notification`, and `manual_escalation_request` Shuffle template contracts for the Phase 54 `smb-single-node` product profile. It does not launch Shuffle directly, implement delegation binding, normalize receipts, broaden the enrichment marketplace, mutate protected target state, bypass AegisOps approval, enable Controlled Write or Hard Write by default, introduce live third-party credentials, or claim Beta, RC, GA, commercial readiness, or broad SOAR replacement readiness.

The required structured artifacts are:

- `docs/deployment/profiles/smb-single-node/shuffle/templates/enrichment_only_lookup-import-contract.yaml`
- `docs/deployment/profiles/smb-single-node/shuffle/templates/operator_notification-import-contract.yaml`
- `docs/deployment/profiles/smb-single-node/shuffle/templates/manual_escalation_request-import-contract.yaml`

## 1. Purpose

Phase 54.5 extends the reviewed Shuffle product profile with Read/Notify-only template contracts. These templates give operators bounded enrichment, operator notification, and manual escalation request paths without granting Shuffle authority over AegisOps approval, action request, execution receipt, reconciliation, workflow state, or protected target state.

## 2. Authority Boundary

Shuffle is a subordinate routine automation substrate. Lookup results, notification delivery state, escalation request delivery state, Shuffle workflow status, workflow success, workflow failure, retry state, callback payloads, execution logs, workflow canvas state, generated config, API responses, template metadata, verifier output, issue-lint output, tickets, assistant output, browser state, UI cache, optional evidence, and downstream receipt state are not AegisOps approval, action request, execution receipt, reconciliation, workflow, release, gate, limitation, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth. Shuffle may execute these Read/Notify templates only after AegisOps records the action request and approval posture required by policy.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. Missing request, approval, correlation, receipt, subject, recipient, escalation owner, scope, or reviewed template version signals must fail closed instead of being inferred from workflow names, template paths, comments, callback payload shape, issue text, tenant names, account names, or nearby metadata.

## 3. Template Contract Metadata

| Template | Required action type | Required scope | Allowed target effect | Protected boundary |
| --- | --- | --- | --- | --- |
| `enrichment_only_lookup` | `enrichment_only_lookup` | `read-only-enrichment-lookup` | Read subordinate context and return lookup evidence only. | No protected target state mutation, account change, credential rotation, group membership change, ticket closure, case closure, or workflow state change. |
| `operator_notification` | `operator_notification` | `operator-notification-only` | Notify a reviewed operator recipient only. | No authoritative workflow state mutation, case closure, ticket closure, approval decision, reconciliation decision, or protected target state mutation. |
| `manual_escalation_request` | `manual_escalation_request` | `manual-escalation-request-only` | Request human escalation through an AegisOps-approved path only. | No AegisOps approval bypass, automatic escalation approval, case closure, ticket closure, or protected target state mutation. |

## 4. Required Binding Contract

| Contract area | Required fields | Failure rule |
| --- | --- | --- |
| Request | `action_request_id` | Missing, blank, mismatched, or inferred request id rejects the template contract. |
| Approval | `approval_decision_id` | Missing, blank, mismatched, or inferred approval id rejects the template contract. |
| Correlation | `correlation_id` | Missing, blank, or one-sided correlation rejects the template contract. |
| Receipt | `execution_receipt_id`, `normalized_receipt_ref` | Missing or blank receipt fields reject the template contract. |
| Subject | Template-specific subject id | Missing, blank, or inferred lookup, recipient, or escalation subject rejects the template contract. |
| Scope | Template-specific Read/Notify scope | Missing, blank, broad, write-capable, or protected-target-mutating scope rejects the template contract. |
| Version | `reviewed_template_version` | Missing or mismatched reviewed template version rejects the template contract. |

## 5. Entry Rules

- Each Phase 54.5 template contract must be represented by its structured artifact before import work starts.
- The reviewed template version must be explicit; unreviewed, draft, sample, placeholder, TODO, deprecated, floating, or latest template versions cannot enter the product mainline.
- Request id, approval id, correlation id, receipt id, subject id, owner, scope, and reviewed template version must be explicit fields, not inferred from names, paths, comments, issue text, callback payload shape, tenant names, account names, or sibling metadata.
- `enrichment_only_lookup` is enrichment-only and read-only. It may return subordinate lookup evidence but cannot mutate protected target state.
- `operator_notification` is notification-only. It cannot change authoritative workflow state, close cases, close tickets, approve actions, reconcile actions, or mutate protected target state.
- `manual_escalation_request` is a request-only path. It cannot bypass AegisOps approval, create automatic escalation approval, close cases, close tickets, or mutate protected target state.
- Callback URLs must use the placeholder `<aegisops-shuffle-callback-url>` until a later AegisOps-owned route binding is implemented.
- Callback secrets, enrichment API credentials, notification credentials, escalation credentials, and Shuffle API credentials must be trusted secret references only. Placeholder, sample, fake, TODO, unsigned, inline, or default secret values are invalid.

## 6. Validation Rules

Phase 54.5 Read/Notify template validation must fail closed when:

- `docs/deployment/shuffle-read-notify-template-contracts.md` is missing;
- any required structured artifact is missing;
- required request id, approval id, correlation id, receipt id, subject id, scope, reviewed template version, owner, review status, import eligibility, callback, or authority-boundary fields are missing or blank;
- `review_status` is not exactly `reviewed`;
- any `action_type` does not exactly match its template id;
- any Read/Notify scope is broad, write-capable, authority-mutating, truth-promoting, or protected-target-mutating;
- enrichment-only behavior permits write behavior;
- operator notification changes authoritative workflow state;
- manual escalation request bypasses AegisOps approval or records automatic approval;
- request, approval, correlation, receipt, subject, owner, version, or review status is inferred from naming conventions, path shape, comments, sibling metadata, callback payloads, account names, tenant names, or issue text;
- placeholder secrets, sample credentials, fake values, TODO values, unsigned tokens, inline secrets, raw forwarded headers, or inferred tenant/source/delegation linkage are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<shuffle-template-path>`, and `<aegisops-shuffle-callback-url>`.

## 7. Forbidden Claims

- Shuffle workflow success is AegisOps reconciliation truth.
- Shuffle callback payload is AegisOps execution receipt truth.
- Shuffle workflow status closes AegisOps cases.
- Shuffle execution logs are AegisOps audit truth.
- enrichment_only_lookup mutates protected target state.
- enrichment_only_lookup disables accounts.
- enrichment_only_lookup rotates credentials.
- enrichment_only_lookup changes group membership.
- operator_notification changes authoritative workflow state.
- operator_notification closes cases.
- operator_notification closes tickets.
- manual_escalation_request bypasses AegisOps approval.
- manual_escalation_request creates automatic approval.
- manual_escalation_request closes cases.
- Template names imply approval decision binding.
- Template paths imply action request binding.
- Lookup, recipient, escalation owner, tenant, account, case, ticket, or source linkage can be inferred from a name, domain, path, comment, issue text, or sibling metadata.
- Placeholder Shuffle API keys are valid credentials.
- Raw forwarded headers are trusted callback identity.
- Phase 54.5 implements broad enrichment marketplace expansion.
- Phase 54.5 implements write-capable Shuffle actions.
- Phase 54.5 enables Controlled Write by default.
- Phase 54.5 enables Hard Write by default.
- Phase 54.5 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement.

## 8. Validation

Run `bash scripts/verify-phase-54-5-read-notify-template-contracts.sh`.

Run `bash scripts/test-verify-phase-54-5-read-notify-template-contracts.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1159 --config <supervisor-config-path>`.

The verifier must fail when any Phase 54.5 Read/Notify contract or structured artifact is missing, when required request id, approval id, correlation id, receipt id, subject id, scope, reviewed template version, owner, review status, import eligibility, or callback fields are missing, when enrichment-only behavior becomes write-capable, when operator notification mutates authoritative workflow state, when manual escalation bypasses AegisOps approval, when Shuffle substrate state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No live Shuffle import, delegation binding, receipt normalization, fallback behavior, direct Shuffle launch, broad notification catalog, broad enrichment marketplace, broad SOAR action catalog, Wazuh profile work, release-candidate behavior, general-availability behavior, Controlled Write default enablement, Hard Write default enablement, or runtime behavior is implemented here.
- No lookup result, notification delivery state, escalation request delivery state, Shuffle workflow success, workflow failure, workflow status, retry state, callback payload, execution log, workflow canvas, generated config, API response, template metadata, verifier output, issue-lint output, ticket, assistant output, browser state, UI cache, optional evidence, downstream receipt, or operator-facing summary becomes authoritative AegisOps truth.
