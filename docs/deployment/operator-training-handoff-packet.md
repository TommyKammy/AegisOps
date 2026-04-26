# Operator Training and Handoff Packet

## 1. Purpose and Audience

This packet trains a single-customer pilot operator on the daily AegisOps path from queue review through case handling, action review, evidence handoff, and next-owner handoff.

The packet is role-readable operator guidance, not generic SOC training, a broad SIEM or SOAR course, or assistant prompt engineering training.

Use it before pilot handoff, during operator shadowing, and when a daily owner needs to explain what AegisOps owns versus what external detection, coordination, automation, or assistant surfaces can only support.

Verify the packet with `scripts/verify-operator-training-handoff-packet.sh`.

## 2. Daily Queue, Case, and Action-Review Path

Daily work starts from the AegisOps queue, not from Wazuh, OpenSearch, Zammad, Shuffle, n8n, or assistant output.

The normal operator path is `queue item -> alert or case detail -> evidence review -> casework update -> action-review read -> approval decision -> execution receipt -> reconciliation outcome -> evidence handoff`.

The operator may move from queue to case only through the AegisOps-owned alert, case, evidence, and reconciliation records linked to the queue item.

Queue review answers what work is currently assigned for review. Case detail answers what investigation record owns the work. Evidence review answers which reviewed artifacts and provenance support the case. Casework update records operator notes, observations, and recommendation drafts inside the AegisOps record chain.

Action review is the reviewed family that keeps the action request, approval decision, execution receipt, and reconciliation outcome visible without collapsing them into one status badge.

## 3. Reviewed Record Chain

The reviewed record chain is the authoritative sequence of AegisOps-owned records that explains why work entered the queue, what case owns it, what evidence supports it, what action was requested, who approved or rejected it, what execution surface reported, and how reconciliation closed or escalated the outcome.

Operators must follow explicit record identifiers such as `alert_id`, `case_id`, `evidence_id`, `action_request_id`, `approval_decision_id`, `action_execution_id`, and `reconciliation_id` instead of inferring linkage from names, ticket titles, dashboard order, or nearby notes.

Use the chain in this order when explaining a handoff:

| Chain segment | Operator question | Authority rule |
| --- | --- | --- |
| Queue item | Why is this work in front of me today? | The queue points to AegisOps records; it does not make external status authoritative. |
| Alert or case | Which reviewed work item owns the investigation? | AegisOps alert and case records own analyst work state. |
| Evidence | What supports the operator claim or next step? | Evidence must remain linked and provenance-preserving. |
| Action request | What response intent was requested for the reviewed scope? | Requested intent stays in the AegisOps action request. |
| Approval decision | Was this exact request approved, rejected, expired, canceled, or superseded? | Approval is a separate AegisOps decision record. |
| Action execution | What did the approved execution surface attempt or refuse? | Execution receipts are correlated evidence, not reconciliation truth by themselves. |
| Reconciliation | Did reviewed AegisOps comparison accept, reject, or escalate the outcome? | Reconciliation remains the control-plane outcome for mismatch or closure. |

If any segment is missing, stale, mixed across release identifiers, or only implied by external metadata, the operator keeps the handoff unresolved until the prerequisite is repaired or the unresolved state is preserved as the reviewed outcome.

## 4. Approval, Execution, and Reconciliation Split

Approval answers whether a specific AegisOps action request is allowed for the reviewed scope.

Execution answers what the approved execution surface actually attempted or refused and which receipt or correlation identifier came back.

Reconciliation answers whether authoritative AegisOps review accepted, rejected, or escalated the observed execution against the approved intent.

Execution success is not reconciliation success, and a ticket closure is neither execution success nor reconciliation success.

When explaining this split to the next operator, use three separate sentences: who approved what, what surface attempted or refused it, and what reconciliation decided or still needs. Do not summarize the three surfaces as one green, done, or closed state unless the reviewed reconciliation record itself supports that terminal outcome.

## 5. External Ticket Non-Authority

External tickets are coordination references only; they may carry ticket identifiers, URLs, comments, or assignee context, but they do not own AegisOps case, approval, execution, or reconciliation truth.

If an external ticket disagrees with the AegisOps reviewed record chain, operators keep the AegisOps record authoritative and preserve the disagreement for review.

Ticket fields may help a human find a coordination thread, but they must not close a case, approve an action, prove execution, prove reconciliation, infer tenant or repository linkage, or replace missing AegisOps evidence.

## 6. Assistant Advisory-Only Posture

Assistant output is advisory-only and must remain grounded in reviewed AegisOps records and linked evidence.

The assistant must not approve, execute, reconcile, close a case, widen pilot scope, or replace missing evidence with generated text.

Use assistant summaries only as cited decision support. If citations are missing, identity context is ambiguous, optional enrichment conflicts with reviewed records, or the output asserts authority it does not have, keep the item unresolved and return to the reviewed record chain.

## 7. Evidence Handoff Walkthrough

A handoff starts by naming the reviewed event, operator, release or repository revision when runtime state changed, customer-scoped reference without secrets, and the directly linked AegisOps record identifiers.

The handoff must include the release handoff record, runtime smoke manifest when relevant, detector activation handoff when relevant, external coordination reference when present, assistant limitation statement when assistant output was used, known-limitations review, handoff owner, and next health review or queue owner.

For failed, rejected, forbidden, rollback, restore, or no-go paths, the handoff must preserve the refusal reason and clean-state evidence instead of overwriting the failed attempt with a later success summary.

Operator rehearsal:

1. Open the current queue item and name the linked alert or case record.
2. Read the evidence and reconciliation references before using external ticket or assistant context.
3. If an action exists, explain the action request, approval decision, execution receipt, and reconciliation outcome separately.
4. Attach only directly linked evidence and coordination references to the handoff.
5. Record the next owner, next health review, unresolved gaps, and clean-state evidence for any rejected or failed path.

Use repo-relative commands and placeholders in handoff notes, such as `scripts/verify-operator-training-handoff-packet.sh`, `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`, `<release-handoff-manifest.md>`, and `<evidence-dir>`.

## 8. Training Checklist

- Can the operator explain the queue item, case detail, action-review detail, approval, execution, reconciliation, and handoff path without using external ticket status as authority?
- Can the operator point to the exact reviewed record identifiers that make up the record chain?
- Can the operator explain why approval, execution, and reconciliation are separate decisions?
- Can the operator state that external tickets and assistant output are non-authoritative?
- Can the operator assemble the evidence handoff with repo-relative commands, placeholders, and no workstation-local absolute paths?

## 9. Out of Scope

Generic SOC curriculum, broad SIEM or SOAR administration, assistant prompt engineering, multi-customer operating model, compliance certification, and ticket-system workflow ownership are out of scope.

This packet does not approve direct backend access, customer-private secret exposure, optional-extension launch gates, assistant-owned workflow decisions, ticket-owned case state, or bypassing the reviewed approval, execution, and reconciliation split.
