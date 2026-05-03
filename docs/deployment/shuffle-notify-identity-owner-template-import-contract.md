# Phase 54.3 notify_identity_owner Shuffle Template Import Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-reviewed-workflow-template-contract.md`, `docs/phase-52-closeout-evaluation.md`, `docs/phase-52-7-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1154, #1156, #1157

This contract defines the repo-owned `notify_identity_owner` Shuffle workflow template import contract for the Phase 54 `smb-single-node` product profile. It does not launch Shuffle directly, implement delegation binding, normalize receipts, broaden the notification catalog, mutate protected target state, enable Controlled Write or Hard Write by default, or claim Beta, RC, GA, commercial readiness, or broad SOAR replacement readiness.

The required structured artifact is `docs/deployment/profiles/smb-single-node/shuffle/templates/notify_identity_owner-import-contract.yaml`.

## 1. Purpose

The `notify_identity_owner` template import contract makes the first reviewed low-risk notification workflow enforceable before template import work enters the product mainline. The contract binds request identity, approval identity, correlation identity, receipt identity, recipient identity owner, message scope, and reviewed template version without treating Shuffle state as authoritative AegisOps truth.

## 2. Authority Boundary

Shuffle is a subordinate routine automation substrate. Shuffle workflow status, workflow success, workflow failure, retry state, callback payloads, execution logs, workflow canvas state, generated config, API responses, template metadata, verifier output, issue-lint output, tickets, assistant output, browser state, UI cache, optional evidence, and downstream receipt state are not AegisOps approval, action request, execution receipt, reconciliation, workflow, release, gate, limitation, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth. Shuffle executes delegated notification work only after AegisOps records the action request and approval posture required by policy.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. Missing request, approval, correlation, receipt, recipient identity owner, message scope, or reviewed template version signals must fail closed instead of being inferred from workflow names, template paths, comments, callback payload shape, or nearby metadata.

## 3. Template Import Metadata

| Field | Required | Expected value or binding | Authority boundary |
| --- | --- | --- | --- |
| `template_id` | Yes | `notify_identity_owner`. | Template identity is import eligibility metadata only. |
| `reviewed_template_version` | Yes | `notify_identity_owner-v1-reviewed-2026-05-03`. | Version state cannot become release or gate truth. |
| `owner` | Yes | AegisOps maintainer or named owning team. | Owner metadata is accountability context only. |
| `review_status` | Yes | `reviewed` only. | Unreviewed, draft, deprecated, sample, or TODO status cannot enter the product mainline. |
| `action_type` | Yes | `notify_identity_owner`. | Action type binding does not authorize execution by itself. |
| `message_scope` | Yes | `identity-owner-low-risk-notification-only`. | Message scope cannot mutate protected target state. |
| `authority_boundary` | Yes | Explicit statement that Shuffle remains subordinate. | Boundary text cannot override AegisOps control-plane records. |

## 4. Required Binding Contract

| Contract area | Required fields | Failure rule |
| --- | --- | --- |
| Request | `action_request_id` | Missing, blank, mismatched, or inferred request id rejects the template import. |
| Approval | `approval_decision_id` | Missing, blank, mismatched, or inferred approval id rejects the template import. |
| Correlation | `correlation_id` | Missing, blank, or one-sided correlation rejects the template import. |
| Receipt | `execution_receipt_id`, `normalized_receipt_ref` | Missing or blank receipt fields reject the template import. |
| Recipient | `recipient_identity_owner_id` | Missing, blank, or inferred recipient owner rejects the template import. |
| Message scope | `message_scope` | Missing, blank, broad, write-capable, or protected-target-mutating scope rejects the template import. |
| Version | `reviewed_template_version` | Missing or mismatched reviewed template version rejects the template import. |

## 5. Import Entry Rules

- The `notify_identity_owner` import contract must be represented by the structured artifact before import work starts.
- The reviewed template version must be explicit; unreviewed, draft, sample, placeholder, TODO, deprecated, floating, or latest template versions cannot enter the product mainline.
- Request id, approval id, correlation id, receipt id, recipient identity owner, message scope, owner, and reviewed template version must be explicit fields, not inferred from names, paths, comments, issue text, callback payload shape, or sibling metadata.
- The only accepted message scope is `identity-owner-low-risk-notification-only`.
- The only accepted target effect is outbound notification to the recipient identity owner.
- Protected target state mutation is forbidden.
- Callback URLs must use the placeholder `<aegisops-shuffle-callback-url>` until a later AegisOps-owned route binding is implemented.
- Callback secrets and API credentials must be trusted secret references only. Placeholder, sample, fake, TODO, unsigned, inline, or default secret values are invalid.

## 6. Validation Rules

`notify_identity_owner` template import validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/shuffle/templates/notify_identity_owner-import-contract.yaml` is missing;
- the contract document is missing;
- required request id, approval id, correlation id, receipt id, recipient identity owner, message scope, reviewed template version, owner, review status, import eligibility, callback, or authority-boundary fields are missing or blank;
- `review_status` is not exactly `reviewed`;
- `action_type` is not exactly `notify_identity_owner`;
- `message_scope` is not exactly `identity-owner-low-risk-notification-only`;
- protected target mutation, account disablement, credential rotation, group membership change, ticket closure, case closure, or direct Wazuh-to-Shuffle shortcut behavior is allowed;
- request, approval, correlation, receipt, recipient owner, owner, version, or review status is inferred from naming conventions, path shape, comments, sibling metadata, callback payloads, or issue text;
- placeholder secrets, sample credentials, fake values, TODO values, unsigned tokens, inline secrets, raw forwarded headers, or inferred tenant/source/delegation linkage are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<shuffle-template-path>`, and `<aegisops-shuffle-callback-url>`.

## 7. Forbidden Claims

- Shuffle workflow success is AegisOps reconciliation truth.
- Shuffle callback payload is AegisOps execution receipt truth.
- Shuffle workflow status closes AegisOps cases.
- Shuffle execution logs are AegisOps audit truth.
- notify_identity_owner mutates protected target state.
- notify_identity_owner disables accounts.
- notify_identity_owner rotates credentials.
- notify_identity_owner changes group membership.
- notify_identity_owner closes cases.
- Template names imply approval decision binding.
- Template paths imply action request binding.
- Recipient owner can be inferred from a username, email domain, tenant name, path, comment, or sibling metadata.
- Placeholder Shuffle API keys are valid credentials.
- Raw forwarded headers are trusted callback identity.
- Phase 54.3 implements broad notification catalog expansion.
- Phase 54.3 implements write-capable Shuffle actions.
- Phase 54.3 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement.

## 8. Validation

Run `bash scripts/verify-phase-54-3-notify-identity-owner-template-import-contract.sh`.

Run `bash scripts/test-verify-phase-54-3-notify-identity-owner-template-import-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1157 --config <supervisor-config-path>`.

The verifier must fail when the `notify_identity_owner` template import contract or structured artifact is missing, when required request id, approval id, correlation id, receipt id, recipient identity owner, message scope, reviewed template version, owner, review status, import eligibility, or callback fields are missing, when a template lacks a reviewed version pin, when a template mutates protected target state, when Shuffle substrate state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No live Shuffle import, delegation binding, receipt normalization, fallback behavior, direct Shuffle launch, broad notification catalog, broad SOAR action catalog, marketplace work, Wazuh profile work, release-candidate behavior, general-availability behavior, Controlled Write default enablement, Hard Write default enablement, or runtime behavior is implemented here.
- No Shuffle workflow success, workflow failure, workflow status, retry state, callback payload, execution log, workflow canvas, generated config, API response, template metadata, verifier output, issue-lint output, ticket, assistant output, browser state, UI cache, optional evidence, downstream receipt, or operator-facing summary becomes authoritative AegisOps truth.
