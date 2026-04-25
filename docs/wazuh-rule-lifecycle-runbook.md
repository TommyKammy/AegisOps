# Wazuh Rule Lifecycle and Validation Runbook

## 1. Purpose

This runbook defines the reviewed lifecycle for Wazuh rules that AegisOps relies on during the current Phase 12 design and implementation slice.

It supplements `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/secops-business-hours-operating-model.md`.

The goal is to give Phase 12 implementers one durable reference for how a reviewed Wazuh rule moves from proposal through validation, fixture-backed onboarding, controlled rollout, and rollback without relying on tribal knowledge.

## 2. Scope and Non-Goals

This runbook governs documentation, validation, and review expectations for Wazuh custom rules whose alerts are intended to cross the AegisOps ingest boundary.

It covers rule introduction, custom-rule onboarding expectations, `wazuh-logtest`-based validation, fixture refresh requirements, rollout notes, and rollback posture.

This runbook does not authorize live Wazuh automation changes, broad source-family rollout, or destructive response actions.

It also does not replace the generic detection lifecycle framework or the Wazuh ingest contract. Those documents remain authoritative for lifecycle state definitions and admitted alert-shape requirements.

## 3. Rule Lifecycle Within AegisOps

A Wazuh rule change must not be treated as an isolated substrate tweak.

For AegisOps, a Wazuh rule is acceptable only when the rule logic, emitted alert shape, and downstream control-plane assumptions remain reviewable together.

Use the baseline lifecycle from `docs/detection-lifecycle-and-rule-qa-framework.md` with the following Wazuh-specific interpretation:

| Lifecycle state | Wazuh-specific expectation |
| ---- | ---- |
| `draft` | The rule idea, parser dependency, or source assumptions are still changing. No downstream fixture or workflow dependency is allowed. |
| `candidate` | The rule intent is stable enough for review, expected source family and fields are named, and `wazuh-logtest` input examples have been identified. |
| `staging` | `wazuh-logtest` output, fixture updates, and adapter or persistence tests are reviewable, but no production activation assumption is implied. |
| `active` | A separate activation decision has accepted the rule for production use with explicit reviewer sign-off, follow-up, and rollback notes. |
| `deprecated` | The rule remains documented temporarily while replacement, removal, or source drift review is coordinated. |
| `retired` | The rule is removed from active use and preserved only for audit or historical reference. |

Progression is blocked when the rule no longer preserves the reviewed Wazuh alert shape, accountable source identity, or provenance assumptions that AegisOps depends on.

## 4. Custom-Rule Onboarding Path for Phase 12

For AegisOps, a custom-rule change is admissible only when the resulting Wazuh alert shape still satisfies the reviewed Wazuh ingest contract, especially `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and full raw payload preservation.

Phase 12 implementers must review the rule change against all of the following before calling the rule onboarding-ready:

| Onboarding checkpoint | Required evidence |
| ---- | ---- |
| Source-family readiness | The upstream source family remains within the reviewed onboarding scope from `docs/source-onboarding-contract.md`. |
| Ingest-contract fit | The emitted Wazuh alert still satisfies the required and optional field handling in `docs/wazuh-alert-ingest-contract.md`. |
| Fixture refresh | Reviewed alert examples exist under `control-plane/tests/fixtures/wazuh/` for each new or changed alert shape that AegisOps intends to admit. |
| Adapter behavior | The adapter and service tests still prove namespacing, accountable source identity handling, and analytic-signal admission behavior. |
| Workflow boundary | Any analyst or workflow assumptions remain aligned with the business-hours operating model and do not infer autonomous action. |

Phase 12 implementers must update or add fixture coverage under `control-plane/tests/fixtures/wazuh/` whenever a custom rule introduces a new reviewed alert shape, source-identity branch, or provenance expectation.

At minimum, the fixture-backed review path must keep `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, and `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py` aligned with the reviewed rule behavior before downstream workflow logic can rely on it.

If a rule change alters `rule.id`, `rule.description`, source-identity handling, or correlation-relevant fields such as manager-versus-agent provenance, the affected fixtures and tests must be refreshed in the same review slice.

Downstream analyst workflow behavior must remain derived from AegisOps-owned alert or case state, not from the Wazuh rule lifecycle alone.

That means a Wazuh custom rule may influence what analytic signal is admitted, but it must not silently redefine alert ownership, case creation semantics, approval requirements, or destructive action posture.

## 5. `wazuh-logtest` Validation Runbook

Use `wazuh-logtest` before staging or downstream workflow review so rule authors can confirm that the candidate event produces the expected Wazuh rule metadata and alert shape.

The local validation sequence is: prepare representative input logs, run `wazuh-logtest`, compare the resulting alert fields against `docs/wazuh-alert-ingest-contract.md`, then refresh Phase 12 fixtures and adapter tests before treating the rule as onboarding-ready.

Recommended validation flow:

1. Prepare representative source events that exercise the intended match path and at least one expected non-match or edge path.
2. Run `wazuh-logtest` in a non-production validation environment that uses the candidate rule set.
3. Capture the resulting rule match details, including `rule.id`, `rule.level`, `rule.description`, source identity, and any relevant `decoder`, `location`, `rule.groups`, or `data.*` fields.
4. Compare that output with the reviewed AegisOps ingest expectations to confirm the alert still carries the required contract fields and preserves optional provenance when present.
5. Convert the reviewed alert examples into refreshed fixtures under `control-plane/tests/fixtures/wazuh/` and rerun the adapter and persistence tests before relying on the change downstream.

The validation record should answer these questions explicitly:

| Validation question | Reason it matters |
| ---- | ---- |
| Did the candidate event trigger the intended Wazuh rule and no unintended reviewed rule? | Confirms the rule behavior is stable enough for lifecycle review. |
| Does the emitted alert preserve the required ingest fields? | Confirms the rule remains admissible at the AegisOps boundary. |
| Is accountable source identity still reviewable as `agent:*` or manager-local provenance when agent identity is absent? | Confirms downstream correlation and reconciliation assumptions remain valid. |
| Do the resulting fixtures still support `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, and `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py`? | Confirms the review is backed by executable Phase 12 evidence instead of prose alone. |
| Are any downstream workflow expectations changed? | Forces review before analyst routing or automation assumptions drift. |

If `wazuh-logtest` output does not preserve the reviewed rule metadata or accountable source identity needed by AegisOps, the rule must return to `draft` or `candidate` rather than moving forward on analyst workflow assumptions.

If the rule only validates with ad hoc field rewrites, undocumented parser assumptions, or missing provenance, onboarding is not complete.

## 6. Phase 40 Detector Activation Gate

Phase 40 detector activation must remain a reviewed AegisOps release-gate decision, not a Wazuh-owned workflow transition.

Staging activation is allowed only after rule review, fixture review, expected-volume review, false-positive review, rollback owner, disable owner, and next-review date are recorded.

Staging activation is a controlled observation step for candidate detector behavior. It may use reviewed replay data, a controlled validation environment, or a test index, but it must not be treated as production activation, AegisOps workflow authority, or a live executor wiring approval.

Before a candidate moves from staging to activation review, the reviewer must confirm:

- the Wazuh rule identity, source family, parser assumptions, and reviewed fixture set are explicit;
- the candidate has a named reviewer, activation owner, disable owner, rollback owner, and next-review date;
- expected alert volume, expected benign cases, false-positive review notes, and analyst load expectations are recorded;
- the detector evidence handoff path names the AegisOps-owned alert, case, reconciliation, and release-gate evidence records that will carry the operational truth; and
- rollback can restore the last reviewed rule revision and fixture set without relying on Wazuh as the authority for downstream workflow state.

Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record.

The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred.

## 7. Rollout, Disable, and Rollback

Controlled rollout review must happen only after the `wazuh-logtest` result, fixture updates, and local tests all agree on the intended alert behavior.

Before any separate activation decision, reviewers should confirm:

- the candidate rule has explicit owner, reviewer, and next-review or expiry notes;
- the corresponding fixtures describe the approved alert shape that Phase 12 code expects;
- local tests still prove analytic-signal admission behavior for the reviewed alert examples; and
- downstream workflow consumers are still reading AegisOps-owned alert and case state rather than substrate-only assumptions.

Rollback means disabling or reverting the custom rule, restoring the last reviewed rule revision, and withdrawing any dependent fixture or workflow assumptions until validation is rerun.

Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review.

Rollback evidence must identify the last reviewed rule revision, restored fixture set, rollback owner, rollback reason, validation rerun result, and AegisOps release-gate evidence record.

If rollback is required, reviewers should also record whether the previous fixture set must be restored, whether any adapter logic depends on the reverted rule shape, and whether analyst-facing expectations need to move back to `staging` or `candidate`.

Rollback must remain non-destructive and reviewable. It is a documentation, rule-set, fixture, and validation reset path rather than an approval for live destructive response or undocumented hotfixes.

## 8. False-Positive Handling

False-positive handling must keep benign, suspicious, deferred, and ambiguous outcomes tied to AegisOps-owned alert, case, approval, action, execution, or reconciliation records.

The false-positive review must record the specific benign explanation, reviewed evidence source, affected rule or candidate, reviewer, follow-up owner, and whether the candidate remains in staging, moves toward activation review, returns to `candidate`, or is disabled.

A benign conclusion requires explicit linkage to an AegisOps-owned record, approved change-management path, or reviewed read-only source evidence. Familiar actor names, hostnames, repository names, tenant names, Wazuh manager labels, expected-looking groups, comments, or nearby metadata are not enough to suppress a candidate or declare the signal safe.

If false-positive review depends on missing parser evidence, missing Wazuh provenance, raw forwarded identity, placeholder credentials, sample secrets, unsigned tokens, TODO values, or inferred tenant, repository, account, issue, or environment linkage, the candidate remains blocked until the prerequisite is supplied.

## 9. Detector Evidence Handoff

Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete.

The handoff package must name:

- the Wazuh candidate rule and source-family package;
- the reviewed fixture set and validation command result;
- the AegisOps alert, case, or reconciliation record identifiers that received detector evidence;
- the reviewer, activation owner, disable owner, rollback owner, and next-review date;
- the false-positive review disposition and expected alert volume; and
- the release-gate evidence record that binds activation, disable, and rollback evidence to the current repository revision.

The handoff is evidence custody only. It does not let Wazuh decide case truth, approval truth, execution truth, reconciliation truth, or release readiness.

## 10. Authority Boundary

Wazuh remains detection substrate only and is not the authority for AegisOps alert lifecycle, case state, approval state, action state, execution state, reconciliation outcome, or release-gate truth.

Wazuh may provide analytic signal evidence, rule metadata, parser output, and source provenance for AegisOps review. AegisOps-owned records remain authoritative for workflow state, analyst disposition, approval decisions, action delegation, execution reconciliation, release-gate acceptance, disable decisions, and rollback completion.

Operators must not infer activation success, disable completion, rollback completion, case closure, approval state, or reconciliation outcome from Wazuh rule state, alert count, source names, manager labels, or detector status alone.

When Wazuh substrate evidence and AegisOps-owned records disagree, repair the derived substrate-facing projection or block the gate for review. Do not redefine AegisOps workflow truth around Wazuh status.
