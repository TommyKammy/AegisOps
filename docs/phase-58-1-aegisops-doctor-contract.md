# Phase 58.1 AegisOps Doctor Contract

## Purpose

`aegisops doctor` is a read-only supportability surface for explaining common
operator states before broader Phase 58 support bundle, backup, restore,
upgrade, rollback, and UI work expands.

The doctor output is subordinate context. It can explain state and recommend
safe next steps, but it cannot approve, execute, reconcile, close, restore,
upgrade, roll back, release, gate, or mutate authoritative AegisOps records.

## Runtime Surfaces

- CLI: `python3 control-plane/main.py doctor`
- HTTP: `GET /diagnostics/doctor`

Both surfaces render the same JSON contract and are non-mutating.

## Posture Semantics

- `available`: the checked supportability signal is present and usable as
  explanatory context.
- `degraded`: the signal exists but is stale, mismatched, partial, or explicitly
  degraded.
- `unavailable`: the signal is missing, malformed, blocked by a missing
  prerequisite, or unsafe to infer.
- `not_applicable`: the family has no current record or runtime activity that
  needs diagnosis.

## State Families

The contract always names these state families:

- `control_plane`
- `wazuh`
- `shuffle`
- `database`
- `proxy`
- `stale_source`
- `ai_enablement`
- `evidence_availability`
- `workflow_template`
- `execution_receipt`

## Explanation Outputs

Each state family includes human-readable advisory guidance:

- `explanation`: a short operator-facing description of the observed state.
- `safe_next_steps`: bounded support steps that preserve the current posture,
  fail closed on missing prerequisites, and avoid automatic repair claims.
- `support_link`: a repo-relative documentation pointer for the relevant
  support boundary.

Recommended next-step entries repeat the same safe next steps and support link
for every `degraded` or `unavailable` family so CLI and HTTP clients can render
the support guidance without treating it as workflow truth.

The guidance must not expose secrets, workstation-local paths, customer-private
payloads, raw forwarded identity hints, or support text that claims doctor can
repair, approve, execute, reconcile, restore, release, gate, or close work.

## Negative Authority

Doctor output must not be treated as:

- automatic repair authority
- workflow truth
- release truth
- restore truth
- gate truth
- authority to mutate control-plane records

Missing provenance, malformed readiness payloads, missing Wazuh prerequisites,
missing execution receipts, and degraded AI or source-health signals fail closed
to `unavailable` or `degraded`; they do not infer success.
