# Phase 54.8 Shuffle Manual Fallback Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-reviewed-workflow-template-contract.md`, `docs/deployment/shuffle-notify-identity-owner-template-import-contract.md`, `docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md`, `docs/deployment/shuffle-read-notify-template-contracts.md`, `docs/phase-52-closeout-evaluation.md`, `docs/phase-52-7-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1154, #1160, #1162

This contract defines the manual fallback and operator-note path for unavailable Shuffle, rejected execution, missing receipt, stale receipt, and mismatched receipt states for every reviewed Phase 54 Shuffle template. It does not launch Shuffle directly, implement live receipt normalization, broaden the workflow catalog, enable Controlled Write or Hard Write by default, introduce live third-party credentials, or claim Beta, RC, GA, commercial readiness, or broad SOAR replacement readiness.

The required structured artifact is `docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml`.

## 1. Purpose

Phase 54.8 adds the reviewed manual fallback contract for the Shuffle product profile. The fallback path gives operators a consistent way to record who owns manual follow-up, what note should be carried forward, which template and action request are affected, what evidence is still expected, and why Shuffle-backed execution cannot be treated as valid execution receipt evidence.

## 2. Authority Boundary

Shuffle is a subordinate routine automation substrate. Manual fallback is subordinate operator guidance and does not create a bypass approval path. Operator notes, fallback owner assignment, expected-evidence hints, blocked reasons, Shuffle workflow status, workflow success, workflow failure, retry state, callback payloads, execution logs, workflow canvas state, generated config, API responses, template metadata, verifier output, issue-lint output, tickets, assistant output, browser state, UI cache, optional evidence, and downstream receipt state are not AegisOps approval, action request, execution receipt, reconciliation, workflow, release, gate, limitation, or closeout truth.

AegisOps control-plane records remain authoritative for approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth. Fallback records explain why the reviewed Shuffle path is blocked or incomplete; they do not convert unavailable, rejected, missing, stale, or mismatched substrate evidence into successful execution.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. Missing owner, note, affected template, affected action, expected evidence, blocked reason, request, approval, receipt, subject, scope, or reviewed template version signals must fail closed instead of being inferred from workflow names, template paths, comments, callback payload shape, issue text, tenant names, account names, or nearby metadata.

## 3. Fallback Record Contract

| Contract area | Required fields | Failure rule |
| --- | --- | --- |
| Fallback owner | `fallback_owner_id` | Missing, blank, placeholder, inferred, or template-derived owner rejects the fallback record. |
| Operator note | `operator_note` | Missing, blank, approval-bypass, reconciliation-truth, or Shuffle-success-as-truth note rejects the fallback record. |
| Affected template/action | `affected_template_id`, `affected_action_type`, `action_request_id` | Missing, blank, mismatched, inferred, or unreviewed template/action linkage rejects the fallback record. |
| Expected evidence | `expected_evidence` | Missing, blank, broad, or authority-promoting evidence expectations reject the fallback record. |
| Blocked/unavailable reason | `blocked_reason`, `fallback_state` | Missing, blank, unsupported, success-like, or inferred reason rejects the fallback record. |

## 4. Covered Failure States

Phase 54.8 manual fallback validation must cover these states:

- `shuffle_unavailable`: Shuffle, a required Shuffle dependency, a reviewed workflow route, or a trusted credential reference is unavailable.
- `execution_rejected`: AegisOps, the reviewed delegation boundary, or the Shuffle-side import contract rejects execution.
- `missing_receipt`: No normalized execution receipt is available for the affected action request.
- `stale_receipt`: The available receipt is older than the authoritative request, approval, or expected receipt window.
- `mismatched_receipt`: The available receipt does not bind to the affected request, approval, template, action type, correlation id, subject, or reviewed template version.

Each state requires explicit owner, note, affected template/action, expected evidence, and blocked reason. None of these states may be reported as successful execution.

## 5. Reviewed Template Coverage

| Template | Action type | Scope | Manual fallback requirement |
| --- | --- | --- | --- |
| `notify_identity_owner` | `notify_identity_owner` | `identity-owner-low-risk-notification-only` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |
| `create_tracking_ticket` | `create_tracking_ticket` | `ticket-coordination-context-only` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |
| `enrichment_only_lookup` | `enrichment_only_lookup` | `read-only-enrichment-lookup` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |
| `operator_notification` | `operator_notification` | `operator-notification-only` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |
| `manual_escalation_request` | `manual_escalation_request` | `manual-escalation-request-only` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |

## 6. Validation Rules

Phase 54.8 manual fallback validation must fail closed when:

- `docs/deployment/shuffle-manual-fallback-contract.md` is missing;
- `docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml` is missing;
- any reviewed Phase 54 template artifact is missing;
- fallback owner, operator note, affected template, affected action type, action request id, expected evidence, blocked reason, or fallback state is missing or blank;
- fallback owner, affected template, affected action type, action request id, expected evidence, blocked reason, or fallback state is inferred from naming conventions, path shape, comments, sibling metadata, callback payloads, account names, tenant names, or issue text;
- `fallback_state` is outside `shuffle_unavailable`, `execution_rejected`, `missing_receipt`, `stale_receipt`, or `mismatched_receipt`;
- an unavailable Shuffle path is reported as successful execution;
- a rejected execution path is reported as successful execution;
- a missing receipt path is reported as successful execution;
- a stale receipt path is reported as successful execution;
- a mismatched receipt path is reported as successful execution;
- an operator note is treated as AegisOps reconciliation truth;
- a fallback note creates, changes, or bypasses AegisOps approval;
- expected evidence promotes Shuffle workflow status, success, callback payload, execution log, ticket state, assistant output, browser state, UI cache, or optional evidence into AegisOps authority; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<shuffle-template-path>`, and `<aegisops-shuffle-callback-url>`.

## 7. Forbidden Claims

- Manual fallback bypasses AegisOps approval.
- Manual fallback note is AegisOps reconciliation truth.
- Unavailable Shuffle is reported as successful execution.
- Rejected execution is reported as successful execution.
- Missing receipt is treated as successful execution.
- Stale receipt is treated as successful execution.
- Mismatched receipt is treated as successful execution.
- Shuffle workflow success is AegisOps reconciliation truth.
- Shuffle callback payload is AegisOps execution receipt truth.
- Operator note closes AegisOps cases.
- Operator note changes AegisOps approval decisions.
- Fallback owner can be inferred from template name, path, issue text, tenant name, account name, or nearby metadata.
- Phase 54.8 implements broad SOAR action catalog expansion.
- Phase 54.8 enables Controlled Write by default.
- Phase 54.8 enables Hard Write by default.
- Phase 54.8 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement.

## 8. Validation

Run `bash scripts/verify-phase-54-8-manual-fallback-contract.sh`.

Run `bash scripts/test-verify-phase-54-8-manual-fallback-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1162 --config <supervisor-config-path>`.

The verifier must fail when the manual fallback contract or structured artifact is missing, when fallback owner or operator note is missing, when affected template/action, expected evidence, or blocked reason is missing, when any unavailable, rejected, missing receipt, stale receipt, or mismatched receipt path is reported as success, when manual notes are promoted into AegisOps reconciliation truth, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No live Shuffle launch, delegation binding, receipt normalization, broad SOAR action catalog, Wazuh profile work, ticket close behavior, case close behavior, release-candidate behavior, general-availability behavior, Controlled Write default enablement, Hard Write default enablement, or runtime behavior is implemented here.
- No fallback owner, operator note, expected evidence, blocked reason, Shuffle workflow success, workflow failure, workflow status, retry state, callback payload, execution log, workflow canvas, generated config, API response, template metadata, verifier output, issue-lint output, ticket, assistant output, browser state, UI cache, optional evidence, downstream receipt, or operator-facing summary becomes authoritative AegisOps truth.
