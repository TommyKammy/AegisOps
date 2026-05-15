# Phase 61.5 Suppression Proposal Workflow Validation

- Validation status: PASS
- Validation scope: suppression proposal records linked to reviewed detector lifecycle, source catalog, alert/case/evidence context, owner, rationale, citation set, finite expiry, review cadence, and expected signal impact.

## Record Contract

`SuppressionProposalRecord` is a proposal-only AegisOps record. It lets operators review a documented suppression candidate without hiding source signals, mutating raw source history, applying source-native suppression, closing cases, or reconciling outcomes.

Required bindings:

- detector lifecycle record identifier
- reviewed source family and source catalog entry
- at least one alert, case, or evidence context link
- owner
- rationale
- citation references
- finite expiry
- review cadence
- expected signal impact
- bounded suppression scope
- source signal handling that preserves source truth

Supported lifecycle states:

- `proposed`
- `under_review`
- `rejected`
- `withdrawn`
- `expired`
- `superseded`

No lifecycle state represents active or authoritative suppression.

## Authority Boundary

Suppression proposal records may inform detector review and triage. They must not silently delete, hide, or suppress source signals, mutate raw Wazuh history, close cases from labels alone, treat detector/source-native status as AegisOps workflow truth, or claim Beta/RC/GA readiness.

## Verification Commands

Run `python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract`.

Run `bash scripts/verify-phase-61-5-suppression-proposal-workflow.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

## Deviations

- No deviations.
