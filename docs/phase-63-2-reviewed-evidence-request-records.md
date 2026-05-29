# AegisOps Phase 63.2 Reviewed Evidence Request Records

## 1. Purpose

Phase 63.2 adds reviewed evidence request records for Evidence Expansion v1.

The records bind requester, scope, target, source, expiry, custody, authorization, and linked case context before an evidence source can be used for a case. The request is AegisOps-owned workflow context. Evidence output, source-native state, freshness projections, AI output, verifier output, issue-lint output, browser state, and UI cache remain subordinate context only.

## 2. Record Contract

Reviewed evidence request records use `reviewed_evidence_request` as the record family and `evidence_request_id` as the durable identifier.

Required fields:

- `evidence_request_id`
- `case_id`
- `requester_identity`
- `requester_role`
- `target`
- `source_id`
- `requested_scope`
- `custody`
- `authorization`
- `linked_case_context`
- `requested_at`
- `expires_at`
- `lifecycle_state`
- `authority_posture`

The authority posture must be `aegisops_owned_workflow_context_subordinate_evidence_output`.

## 3. Reviewed Scope And Compatibility

The first Phase 63.2 source and target pairings are deliberately narrow:

| Source id | Required target class | Required target binding |
| --- | --- | --- |
| `osquery_host_state` | `explicitly_bound_host` | `case_id` and `host_identifier` |
| `malwarebazaar_hash_reputation` | `reviewed_file_hash` | `case_id` and `file_hash` |

The validator rejects missing scope, expired request use, naive injected clocks, unauthorized requester roles, invalid target/source pairing, missing custody, missing case linkage, stale source use, denied source use, and duplicate active request ambiguity.

Source freshness that exceeds the Phase 63.1 registry window is stale, registry degraded or disabled state names stay binding after separator or camel-case normalization, duplicate subject checks compare only target binding fields and apply only to active candidate requests, and evidence request identifiers cannot be reused for a different request subject or changed request binding.

Requested scope, authorization reviewed scope, source status, state, registry_state, and source_state fields cannot claim workflow truth, case truth, approval truth, execution authority, or readiness authority.

## 4. Custody, Authorization, And Case Linkage

Custody must include `reviewed_by`, `custody_owner`, `custody_reference`, and `provenance_chain`.

Authorization must include an affirmative reviewed decision, a `decision_id`, and a `reviewed_scope` that exactly matches the request scope.

Linked case context must include `case_id`, `admitting_evidence_id`, and `reviewed_context_id`. The linked case and target case must match the request case.

## 5. Authority Boundary

Only AegisOps-owned records own workflow truth for admitted alerts, cases, evidence requests, approvals, action requests, execution receipts, reconciliation, audit, release gates, limitations, and closeout state.

Reviewed evidence request records cannot let osquery output, hash-reputation output, evidence output, source-native state, freshness or confidence projections, AI output, verifier output, issue-lint output, browser state, UI cache, or evidence packs approve, execute, reconcile, close, activate detectors, create source truth, gate release, or claim readiness.

The negative-test posture follows `docs/phase-51-6-authority-boundary-negative-test-policy.md` for endpoint evidence, evidence systems, browser state, UI cache, AI output, verifier output, issue-lint output, and source-native state.

## 6. Validation

- Run `bash scripts/verify-phase-63-2-reviewed-evidence-request-records.sh`.
- Run `python3 -m unittest control-plane.tests.test_phase63_2_reviewed_evidence_request_records`.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
- Run `node <codex-supervisor-root>/dist/index.js issue-lint 1333 --config <supervisor-config-path>`.
