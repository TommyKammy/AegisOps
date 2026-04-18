# Phase 25 Multi-Source Case Review and Osquery Evidence Runbook

## 1. Purpose

This runbook defines the reviewed operator procedure for Phase 25 business-hours operator casework.

It supplements `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, `docs/source-families/github-audit/analyst-triage-runbook.md`, `docs/source-families/entra-id/analyst-triage-runbook.md`, `docs/secops-business-hours-operating-model.md`, and `docs/wazuh-rule-lifecycle-runbook.md`.

The goal is to give operators one consistent procedure for multi-source case review, osquery-backed host evidence review, provenance interpretation, and ambiguity escalation without widening the reviewed authority model.

## 2. Scope and Non-Goals

This runbook applies to the reviewed Phase 25 multi-source case review path for business-hours operator casework.

The approved source set for this runbook is:

- GitHub audit context attached through the reviewed case chain;
- the approved second reviewed source family for this slice, `entra_id`; and
- osquery-backed host evidence attached as reviewed augmentation.

This runbook does not authorize broad entity stitching, substrate-led investigation, external substrate authority promotion, direct GitHub or Entra ID actioning, or free-form host hunting outside the reviewed case chain.

osquery-backed host evidence may add host, process, or local-state context, but it must not become the authority for case identity, actor identity, approval truth, or lifecycle truth on its own.

## 3. Business-Hours Multi-Source Case Review Checklist

The operator starts from the reviewed AegisOps case, not from a substrate console.

The business-hours multi-source case review path is:

1. Open the case detail view and identify the authoritative anchor record before reviewing any attached records.
2. Confirm the reviewed source set remains bounded to the current Phase 25 slice instead of silently widening to unrelated source families or nearby substrate artifacts.
3. Review the `cross_source_timeline` and `provenance_summary` surfaces to see which records are attached, how they were classified, and whether any blocking reason remains active.
4. Treat attached GitHub audit or `entra_id` records as reviewed context only to the extent the reviewed case chain explicitly links them.
5. Treat osquery-backed host evidence as augmenting evidence and confirm it is attached to a host already bound explicitly on the reviewed case chain.
6. If any record remains `unresolved`, preserve that state, record the blocking reason, and escalate for reviewed follow-up instead of inferring success from nearby metadata.

Operators should use the approved read-only inspection surfaces for this review:

- `python3 control-plane/main.py inspect-case-detail --case-id <case-id>`
- `python3 control-plane/main.py inspect-assistant-context --family case --record-id <case-id>`

The case review fails closed when the authoritative anchor record is unclear, the source family is out of scope, the linkage is only implied, or the provenance fields needed to explain the attachment are missing or malformed.

## 4. Osquery-Backed Host Evidence Handling

osquery-backed host evidence is admissible only when the reviewed case already binds the host explicitly through `reviewed_context.asset.host_identifier`.

Operators must not attach osquery evidence to a case by hostname similarity, IP proximity, analyst expectation, or substrate-local hints alone.

When collecting or reviewing osquery-backed host evidence, the operator must confirm that the attachment preserves:

- the explicitly bound host identifier;
- the reviewed `source_id`;
- the reviewed collection path;
- the reviewed analyst attribution;
- the collection timestamp; and
- the result kind and row set needed to explain what was observed.

The approved osquery result kinds for this reviewed path are `host_state`, `process`, `local_user`, and `scheduled_query`.

If the collection is meant to produce a durable operator note, the operator must preserve an explicit observation scope statement rather than relying on an unlabeled attachment.

The operator reviews osquery-backed host evidence as augmenting evidence:

- use it to show host or process context already scoped by the reviewed case chain;
- use it to support a reviewed observation linked back to the evidence record; and
- do not use it to overwrite the authoritative anchor record or to prove `same-entity` on its own.

If the case lacks an explicit host binding, if the provenance fields are incomplete, or if the osquery result would force a stronger identity claim than the reviewed chain supports, the operator must reject the attachment and escalate rather than keep a partial write.

## 5. Provenance and Ambiguity Interpretation

Phase 25 requires operators to read provenance and ambiguity separately.

Each attached record should expose one provenance badge and, when it is not the authoritative anchor, one ambiguity badge.

The reviewed provenance classifications for this runbook are:

- `authoritative-anchor` for the reviewed case-chain record that owns scope;
- `reviewed-direct` for a reviewed record linked directly to that anchor;
- `reviewed-derived` for a reviewed record linked through another durable reviewed record;
- `augmenting-evidence` for osquery-backed host evidence or similar bounded augmentation; and
- `unresolved-linkage` for candidate context that lacks trusted reviewed linkage.

The reviewed ambiguity states for this runbook are:

- `same-entity` only when stable identifiers or an explicit reviewed binding prove the records refer to the same scoped subject;
- `related-entity` when the reviewed chain proves a bounded relationship without proving identity equality; and
- `unresolved` when the reviewed chain does not justify a stronger relation.

The operator must preserve `unresolved` when:

- stable identifiers are missing or conflict;
- provenance is partial, malformed, or unreviewed;
- the only support is alias-style overlap, timing proximity, or nearby metadata;
- osquery-backed host evidence appears relevant but the reviewed chain does not bind it explicitly; or
- the assistant summary would need to collapse ambiguity to sound cleaner than the reviewed records allow.

Operators must not override an `unresolved` case detail state with a stronger assistant-facing interpretation unless a new authoritative reviewed link is recorded first.

## 6. Escalation and Out-of-Scope Boundaries

Escalate instead of continuing routine review when:

- the authoritative anchor record cannot be identified cleanly;
- a source family outside the approved Phase 25 slice appears necessary;
- the desired linkage depends on broad entity stitching rather than explicit reviewed binding;
- the osquery evidence suggests a host relationship that the case chain does not bind explicitly; or
- substrate-local UI or nearby telemetry would need to be treated as the authority to complete the review.

Escalation means recording the blocking reason on the reviewed case path and preserving the unresolved state for the next reviewed decision. It does not mean widening the case silently or treating external substrate summaries as case truth.

This runbook keeps broad entity stitching, substrate-led investigation, and external substrate authority explicitly out of scope for the reviewed Phase 25 path.

## 7. Repository-Local Verification Commands

The repository-local verification commands for this runbook are:

- `bash scripts/verify-phase-25-multi-source-case-review-runbook.sh`
- `python3 -m unittest control-plane.tests.test_phase25_multi_source_case_admission_docs`
- `python3 -m unittest control-plane.tests.test_phase25_osquery_host_context_validation`

Run those checks after updating this runbook so the documentation surface, the Phase 25 operator-doc assertions, and the osquery-backed evidence boundary remain executable as written.
