# AegisOps Phase 62.1 Reviewed Automation Catalog Contract

- **Status**: Accepted contract
- **Date**: 2026-05-17
- **Owner**: AegisOps maintainers
- **Related Baseline**: `docs/phase-54-closeout-evaluation.md`, `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-reviewed-workflow-template-contract.md`, `docs/deployment/shuffle-read-notify-template-contracts.md`, `docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md`, `docs/phase-56-closeout-evaluation.md`, `docs/phase-57-closeout-evaluation.md`, `docs/phase-61-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1314, #1315

This contract defines the minimum reviewed automation catalog for Phase 62.1. It covers default `smb-single-node` Read, Notify, and Soft Write automation actions only. It does not launch Shuffle directly, broaden SOAR marketplace coverage, enable Controlled Write or Hard Write default actions, grant autonomous remediation, or claim Beta, RC, GA, commercial readiness, or broad SOAR replacement readiness.

## 1. Purpose

Phase 62.1 records the default reviewed automation catalog that later Phase 62 work can consume before expanding SOAR breadth. Each catalog entry must carry action family, owner, substrate mapping need, required approval posture, expected receipt shape, reconciliation expectation, allowed roles, idempotency posture, and explicit limitations.

The catalog consumes the reviewed Phase 54 Shuffle profile, template, delegation, receipt, and fallback posture as a substrate evidence pattern. It does not import new workflow templates, dispatch workflow runs, or let downstream workflow state become AegisOps truth.

## 2. Authority Boundary

Every automation action must route through AegisOps action request, approval when required, execution receipt, and reconciliation records. AegisOps records remain authoritative for case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

Shuffle workflow state, simulator state, ticket state, UI cache, browser state, AI output, source-native state, verifier output, and issue-lint output remain subordinate context. They cannot approve, execute, reconcile, close, gate, or claim readiness by themselves.

Missing owner, action family, substrate mapping, approval posture, receipt expectation, reconciliation expectation, role boundary, idempotency posture, limitation, correlation, action request, approval decision, or reviewed template/version signal must fail closed instead of being inferred from workflow names, template paths, comments, issue text, source names, case names, ticket titles, tenant names, or nearby metadata.

## 3. Approved Default Catalog Entries

| Catalog action | Family | Owner | Substrate mapping need | Required approval posture | Expected receipt shape | Reconciliation expectation | Allowed roles | Idempotency posture | Explicit limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `enrichment_only_lookup` | Read | AegisOps maintainers and IT Operations, Information Systems Department | Must map only to the reviewed Phase 54 Shuffle `enrichment_only_lookup` template contract or an equivalent later reviewed Read substrate mapping. No direct ad-hoc Shuffle launch. | AegisOps action request required. Separate approval is not required by default unless action policy marks the request elevated, but the approval posture must be recorded explicitly as policy-not-required or approved. | AegisOps execution receipt with `action_request_id`, `catalog_action`, `family`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, `started_at`, `finished_at`, `status`, and subordinate lookup evidence reference. | Reconciliation may attach subordinate lookup context to the linked AegisOps record. It cannot close cases, approve actions, mutate protected targets, or replace source/evidence truth. | `analyst` may request within assigned scope; `approver` may approve elevated policy paths; `platform_admin` may administer catalog posture only; `read_only_auditor` may inspect. | Idempotency key must bind action request, subject, reviewed template version, and normalized lookup inputs. Duplicate keys must return or link the existing receipt instead of creating a new authoritative outcome. | Read-only enrichment context. No protected target mutation, credential change, ticket mutation, case closure, detector activation, suppression activation, direct source actioning, or marketplace expansion. |
| `operator_notification` | Notify | AegisOps maintainers and IT Operations, Information Systems Department | Must map only to the reviewed Phase 54 Shuffle `operator_notification` template contract or an equivalent later reviewed Notify substrate mapping. No direct ad-hoc Shuffle launch. | AegisOps action request required. Separate approval is not required by default unless action policy marks the request elevated, but recipient and scope must be explicit. | AegisOps execution receipt with `action_request_id`, `catalog_action`, `family`, `recipient_ref`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, delivery-attempt status, and normalized receipt reference. | Reconciliation may record notification attempted, delivered, failed, or fallback-needed as subordinate context. It cannot approve, execute, reconcile other actions, close tickets, or close cases. | `analyst` may request within assigned scope; `approver` may approve elevated policy paths; `platform_admin` may administer catalog posture only; `read_only_auditor` may inspect. | Idempotency key must bind action request, recipient, subject, message intent, and reviewed template version. Retries must preserve the original action request and receipt lineage. | Notification-only. No authoritative workflow state mutation, ticket closure, case closure, approval decision, reconciliation decision, protected target mutation, broad notification marketplace, or readiness claim. |
| `manual_escalation_request` | Notify | AegisOps maintainers and IT Operations, Information Systems Department | Must map only to the reviewed Phase 54 Shuffle `manual_escalation_request` template contract or an equivalent later reviewed Notify substrate mapping. No direct ad-hoc Shuffle launch. | AegisOps action request required. Escalation owner, subject, reason, and policy posture must be explicit. Approval is required when the escalation request asks for protected-target follow-up. | AegisOps execution receipt with `action_request_id`, `catalog_action`, `family`, `escalation_owner_ref`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, delivery-attempt status, and fallback-needed flag when applicable. | Reconciliation may record that human escalation was requested and whether fallback is needed. It cannot create automatic approval, bypass approval, close cases, close tickets, or mark remediation complete. | `analyst` may request within assigned scope; `approver` may approve protected follow-up paths; `platform_admin` may administer catalog posture only; `read_only_auditor` may inspect. | Idempotency key must bind action request, escalation owner, subject, reason, and reviewed template version. Repeated escalation attempts must keep the original request lineage visible. | Request-only escalation. No automatic approval, autonomous remediation, protected target mutation, case closure, ticket closure, broad escalation marketplace, or support-authority override. |
| `create_tracking_ticket` | Soft Write | AegisOps maintainers and IT Operations, Information Systems Department | Must map only to the reviewed Phase 54 Shuffle `create_tracking_ticket` template import contract or an equivalent later reviewed Soft Write substrate mapping. No direct ad-hoc Shuffle launch. | AegisOps action request and reviewed approval posture required before delegation. The approver must be distinct from the requester on approval-sensitive paths. | AegisOps execution receipt with `action_request_id`, `approval_decision_id`, `catalog_action`, `family`, `ticket_pointer_id`, `ticket_system_id`, `ticket_pointer_custody`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, delivery status, and normalized receipt reference. | Reconciliation may link a non-authoritative ticket pointer and record ticket-coordination outcome. Ticket state cannot become case truth, reconciliation truth, limitation truth, release truth, gate truth, or closeout truth. | `analyst` may request within assigned scope; `approver` may approve when policy requires approval; `platform_admin` may administer catalog posture only; `read_only_auditor` may inspect. | Idempotency key must bind action request, approved scope, ticket system, subject, and reviewed template version. Duplicate requests must reuse or link the existing ticket pointer rather than creating competing durable truth. | Soft Write coordination only. No protected target mutation, ticket-close authority, case-close authority, account disablement, credential rotation, group membership change, suppression activation, autonomous remediation, or marketplace expansion. |

## 4. Catalog Boundedness Rules

- This catalog must stay bounded to the four default entries above for Phase 62.1.
- The default catalog families are exactly Read, Notify, and Soft Write.
- Controlled Write and Hard Write are not default catalog families and must be rejected when marked as default entries.
- Unreviewed integrations, arbitrary SOAR connectors, broad SOAR marketplace language, template marketplace import, and broad Shuffle replacement claims are rejected.
- Each entry must include owner, family, substrate mapping need, approval posture, receipt expectation, reconciliation expectation, allowed roles, idempotency posture, and explicit limitations.
- Each entry must reference the reviewed Shuffle/product-profile posture without using that posture as authority to launch workflows directly.
- Action policy configuration, admin UI state, Shuffle state, ticket state, source-native state, AI output, verifier output, and issue-lint output remain subordinate and cannot become approval, execution, reconciliation, closeout, release, or gate truth.

## 5. Validation Rules

The Phase 62.1 reviewed automation catalog verifier must fail closed when:

- the catalog contract or validation record is missing;
- the catalog does not include at least one Read action, one Notify action, and one Soft Write action;
- an entry is missing owner, family, substrate mapping need, approval posture, expected receipt shape, reconciliation expectation, allowed roles, idempotency posture, or limitation;
- a default entry uses Controlled Write or Hard Write;
- a default entry permits direct ad-hoc Shuffle launch, autonomous approval, autonomous remediation, protected target mutation, case closure, ticket closure, detector activation, suppression activation, approval bypass, or reconciliation bypass;
- a default entry promotes Shuffle workflow state, simulator state, ticket state, UI cache, browser state, AI output, source-native state, verifier output, issue-lint output, or admin configuration to AegisOps truth;
- broad SOAR marketplace, arbitrary connector marketplace, broad Shuffle replacement, Beta, RC, GA, commercial readiness, Phase 63 evidence expansion, Phase 66 RC proof, or standalone replacement claims appear outside explicit rejection or non-goal context;
- placeholder secrets, sample credentials, fake values, TODO values, unsigned tokens, inline secrets, raw forwarded headers, or inferred tenant/source/delegation linkage are treated as valid setup state; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented environment variables, or placeholders such as `<supervisor-config-path>`, `<codex-supervisor-root>`, `<shuffle-template-path>`, and `<aegisops-shuffle-callback-url>`.

## 6. Forbidden Claims

- Controlled Write is a default Phase 62.1 catalog entry.
- Hard Write is a default Phase 62.1 catalog entry.
- Broad SOAR marketplace coverage is implemented.
- Arbitrary SOAR connector marketplace import is approved.
- Direct ad-hoc Shuffle launch is approved.
- Shuffle workflow success is AegisOps reconciliation truth.
- Shuffle callback payload is AegisOps execution receipt truth.
- Shuffle workflow status closes AegisOps cases.
- Ticket status is AegisOps case truth.
- Ticket close is AegisOps reconciliation truth.
- UI cache is AegisOps action policy truth.
- AI output approves automation.
- Source-native status reconciles automation.
- Verifier output gates production readiness.
- Issue-lint output gates production readiness.
- Placeholder Shuffle API keys are valid credentials.
- Raw forwarded headers are trusted callback identity.
- `enrichment_only_lookup` mutates protected target state.
- `operator_notification` changes authoritative workflow state.
- `manual_escalation_request` creates automatic approval.
- `create_tracking_ticket` closes cases or tickets.
- Phase 62.1 implements Phase 63 evidence expansion.
- Phase 62.1 implements Phase 66 RC proof.
- Phase 62.1 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement.

## 7. Validation

Run `bash scripts/verify-phase-62-1-reviewed-automation-catalog-contract.sh`.

Run `bash scripts/test-verify-phase-62-1-reviewed-automation-catalog-contract.sh`.

Run `python3 -m unittest control-plane.tests.test_phase62_reviewed_automation_catalog_contract`.

Run `bash scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1314 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1315 --config <supervisor-config-path>`.

## 8. Non-Goals

- No Controlled Write or Hard Write default enablement, autonomous remediation, destructive response, protected-target mutation, approval bypass, reconciliation bypass, direct workflow launch, arbitrary SOAR marketplace, template marketplace import, production secret material, customer-private data, Phase 63 evidence expansion, Phase 66 RC proof, Beta readiness, RC readiness, GA readiness, commercial replacement readiness, or broad SOAR replacement readiness is implemented here.
- No Shuffle workflow success, workflow failure, workflow status, simulator state, callback payload, execution log, workflow canvas, generated config, API response, template metadata, ticket state, UI cache, browser state, AI output, source-native status, verifier output, issue-lint output, admin configuration, downstream receipt, or operator-facing summary becomes authoritative AegisOps truth.
