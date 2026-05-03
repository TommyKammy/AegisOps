# Phase 54.2 Shuffle Reviewed Workflow Template Contract

- **Status**: Accepted contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/phase-52-closeout-evaluation.md`, `docs/phase-52-7-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1154, #1155, #1156

This contract defines the repo-owned reviewed Shuffle workflow template contract for the Phase 54 `smb-single-node` product profile. It does not import workflow templates, implement delegation binding, normalize receipts, launch Shuffle directly, broaden the automation catalog, enable Controlled Write or Hard Write by default, or claim Beta, RC, GA, commercial readiness, or broad SOAR replacement readiness.

The required structured artifact is `docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml`.

## 1. Purpose

Every reviewed Shuffle workflow template must expose the minimum fields AegisOps needs before the template can enter the product mainline. The contract covers template identity, owner, review status, input fields, output fields, correlation fields, action request fields, approval decision fields, execution receipt fields, version fields, and validation posture.

## 2. Authority Boundary

Shuffle is a subordinate routine automation substrate. Shuffle workflow status, workflow success, workflow failure, retry state, callback payloads, execution logs, workflow canvas state, generated config, API responses, template metadata, verifier output, issue-lint output, tickets, assistant output, browser state, UI cache, optional evidence, and downstream receipt state are not AegisOps approval, action request, execution receipt, reconciliation, workflow, release, gate, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth. Shuffle executes delegated work only after AegisOps records the action request and approval posture required by policy.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. Missing correlation, action request, approval decision, execution receipt, version, owner, or reviewed-status signals must fail closed instead of being inferred from workflow names, template paths, comments, callback payload shape, or nearby metadata.

## 3. Reviewed Template Metadata

| Field | Required | Expected value or binding | Authority boundary |
| --- | --- | --- | --- |
| `template_id` | Yes | Stable repo-owned template identifier. | Template identity is import eligibility metadata only. |
| `template_version_id` | Yes | Stable reviewed contract version identifier. | Version state cannot become release or gate truth. |
| `owner` | Yes | AegisOps maintainer or named owning team. | Owner metadata is accountability context only. |
| `review_status` | Yes | `reviewed` only. | Unreviewed, draft, deprecated, sample, or TODO status cannot enter the product mainline. |
| `product_profile` | Yes | `shuffle` with `profile_id` `smb-single-node`. | Product-profile binding does not authorize execution by itself. |
| `authority_boundary` | Yes | Explicit statement that Shuffle remains subordinate. | Boundary text cannot override AegisOps control-plane records. |

## 4. Required Field Contract

| Contract area | Required fields | Failure rule |
| --- | --- | --- |
| Inputs | `correlation_id`, `action_request_id`, `approval_decision_id`, `template_version_id`, `delegation_subject_id`, `requested_by`, `callback_url`, `callback_secret_ref` | Missing or blank input fields reject the template. |
| Outputs | `correlation_id`, `action_request_id`, `approval_decision_id`, `execution_receipt_id`, `template_version_id`, `execution_status`, `execution_started_at`, `execution_finished_at`, `normalized_receipt_ref` | Missing or blank output fields reject the template. |
| Correlation | `correlation_id` in both inputs and outputs | Missing, blank, or one-sided correlation rejects the template. |
| Action request | `action_request_id` in both inputs and outputs | Missing, blank, or inferred action-request linkage rejects the template. |
| Approval decision | `approval_decision_id` in both inputs and outputs | Missing, blank, or inferred approval linkage rejects the template. |
| Execution receipt | `execution_receipt_id` and `normalized_receipt_ref` in outputs | Missing or blank receipt fields reject the template. |
| Version | `template_version_id` in metadata, inputs, and outputs | Missing or mismatched version linkage rejects the template. |
| Review | `owner` and `review_status: reviewed` in metadata | Missing owner or non-reviewed status rejects the template. |

## 5. Product Mainline Entry Rules

- A reviewed template must be represented by the structured artifact before import work starts.
- The reviewed status must be explicit; unreviewed, draft, sample, placeholder, TODO, or deprecated templates cannot enter the product mainline.
- Correlation, action request, approval decision, execution receipt, version, owner, and review status must be explicit authoritative fields, not inferred from names, paths, comments, issue text, callback payload shape, or sibling metadata.
- Callback URLs must use the placeholder `<aegisops-shuffle-callback-url>` until a later AegisOps-owned route binding is implemented.
- Callback secrets and API credentials must be trusted secret references only. Placeholder, sample, fake, TODO, unsigned, inline, or default secret values are invalid.
- Shuffle workflow success, failure, status, callback payload, logs, generated config, ticket state, assistant output, browser state, UI cache, or optional evidence cannot close, approve, execute, reconcile, release, gate, or mutate AegisOps records without explicit AegisOps approval, action request, execution receipt, and reconciliation records.

## 6. Validation Rules

Reviewed workflow template validation must fail closed when:

- `docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml` is missing;
- the contract document is missing;
- required metadata, input, output, correlation, action request, approval decision, execution receipt, version, owner, review status, or authority-boundary fields are missing or blank;
- `review_status` is not exactly `reviewed`;
- unreviewed, draft, sample, placeholder, TODO, or deprecated template status is described as eligible for the product mainline;
- correlation, action request, approval decision, execution receipt, owner, version, or review status is inferred from naming conventions, path shape, comments, sibling metadata, callback payloads, or issue text;
- placeholder secrets, sample credentials, fake values, TODO values, unsigned tokens, inline secrets, raw forwarded headers, or inferred tenant/source/delegation linkage are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<shuffle-profile-path>`, and `<aegisops-shuffle-callback-url>`.

## 7. Forbidden Claims

- Shuffle workflow success is AegisOps reconciliation truth.
- Shuffle callback payload is AegisOps execution receipt truth.
- Shuffle workflow status closes AegisOps cases.
- Shuffle execution logs are AegisOps audit truth.
- Unreviewed Shuffle templates may enter the product mainline.
- Draft Shuffle templates may enter the product mainline.
- Placeholder Shuffle API keys are valid credentials.
- Raw forwarded headers are trusted callback identity.
- Template names imply approval decision binding.
- Template paths imply action request binding.
- Phase 54.2 implements template imports.
- Phase 54.2 implements delegation binding.
- Phase 54.2 implements receipt normalization.
- Phase 54.2 implements broad SOAR catalog expansion.
- Phase 54.2 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement.

## 8. Validation

Run `bash scripts/verify-phase-54-2-reviewed-workflow-template-contract.sh`.

Run `bash scripts/test-verify-phase-54-2-reviewed-workflow-template-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1156 --config <supervisor-config-path>`.

The verifier must fail when the reviewed workflow template contract or structured artifact is missing, when required correlation, action request, approval decision, execution receipt, version, owner, review status, input, or output fields are missing, when an unreviewed template is allowed into the product mainline, when Shuffle substrate state is promoted into AegisOps authority, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No workflow template import, delegation binding, receipt normalization, fallback behavior, direct Shuffle launch, broad SOAR action catalog, marketplace work, Wazuh profile work, release-candidate behavior, general-availability behavior, Controlled Write default enablement, Hard Write default enablement, or runtime behavior is implemented here.
- No Shuffle workflow success, workflow failure, workflow status, retry state, callback payload, execution log, workflow canvas, generated config, API response, template metadata, verifier output, issue-lint output, ticket, assistant output, browser state, UI cache, optional evidence, downstream receipt, or operator-facing summary becomes authoritative AegisOps truth.
