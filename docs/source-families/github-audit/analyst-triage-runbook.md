# GitHub Audit Analyst Triage Runbook

## 1. Purpose

This runbook defines the reviewed analyst triage posture for the approved GitHub audit family.

It complements the AegisOps Source Onboarding Contract, the Wazuh Rule Lifecycle and Validation Runbook, `docs/source-families/github-audit/onboarding-package.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-rule-lifecycle-runbook.md`, and `docs/secops-business-hours-operating-model.md`.

The runbook keeps GitHub audit handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit.

## 2. Scope and Non-Goals

This runbook applies to reviewed GitHub audit alerts and cases that enter AegisOps through the Wazuh-backed intake boundary.

It covers read-oriented triage, evidence capture, disposition decisions, and fixture refresh expectations for the reviewed GitHub audit source profile.

Direct GitHub API actioning remains out of scope. This runbook does not authorize repository changes, secret rotation, privilege enforcement, or any unsupported source family.

It also does not replace the source onboarding contract or the Wazuh rule lifecycle runbook. Those documents remain authoritative for onboarding evidence and rule-change validation.

## 3. Reviewed Triage Posture

GitHub audit items are triaged as queue-driven work items rather than as autonomous response triggers.

The analyst first determines whether the item is a reviewed GitHub audit event, a duplicate, an expected administrative change, or a potentially interesting privilege or access change.

If the item is already explained by known repository administration, maintainer activity, a reviewed automation identity, or an approved change window, the analyst records the benign explanation and closes or links the item according to the current case state.

If the item is not clearly benign, the analyst gathers read-oriented evidence, preserves the reviewed source identity, and decides whether the work item should remain an alert, promote to a case, or wait for the next business-hours review cycle.

The control-plane-first analyst workflow remains the decision boundary. GitHub audit output informs triage, but it does not become the source of truth for case state, approval state, or action execution.

## 4. Family Assumptions and False-Positive Expectations

The reviewed GitHub audit family preserves accountable source identity, actor identity, target identity, repository or organization context, and privilege-change metadata.

False-positive expectations are centered on routine repository administration, approved maintainer activity, automation identity activity, and changes that were already reviewed in a change-management path outside the alert.

Expected benign examples include repository setting updates, workflow maintenance, bot-driven changes, access review cleanup, or other reviewed administrative activity that remains within the approved boundary.

Analysts must not assume that every GitHub audit alert indicates malicious activity. The triage posture requires explicit evidence before escalation, especially when the event can be explained by a normal maintenance task or a reviewed automation path.

Unsupported GitHub telemetry families remain out of scope. Direct vendor-local actioning remains out of scope even when a repository event looks urgent.

## 5. Evidence to Collect

The analyst captures read-oriented evidence that answers what changed, who or what changed it, which target object was affected, and why the item is or is not interesting.

At minimum, the analyst records:

- the reviewed GitHub audit event summary;
- the accountable source identity and delivery path;
- the actor identity, including whether it was a human, app, bot, or other automation identity when present;
- the target object, repository, organization, or membership context;
- the privilege or access change context, if any;
- the raw payload or fixture reference used for review; and
- the reason the event is benign, escalated, or deferred.

The reviewer should keep evidence aligned with `docs/source-onboarding-contract.md` and the reviewed GitHub audit onboarding package. If a new reviewed alert shape appears, the corresponding fixture under `control-plane/tests/fixtures/wazuh/github-audit-alert.json` and the related Wazuh rule lifecycle evidence must be refreshed before downstream workflow assumptions change.

## 6. Business-Hours Handling

This runbook follows the Business-hours SecOps daily operating model.

GitHub audit alerts that do not require immediate same-day handling remain queued for the next business-hours review cycle with enough context recorded that the next analyst does not need to reconstruct intent from raw system output.

If an item appears to require escalation, the analyst records the reason, the affected scope, and the review context before requesting any human follow-up.

After-hours handling remains explicit and bounded. The reviewed path does not imply 24x7 analyst watchstanding, and it does not authorize vendor-local actioning or automatic enforcement.

## 7. Validation and Fixture Expectations

The reviewer treats the reviewed GitHub audit fixture as the canonical replay reference for this family.

Any new reviewed GitHub audit rule shape, provenance expectation, or identity branch must be validated against `docs/wazuh-rule-lifecycle-runbook.md` before it is treated as stable for triage.

The analyst triage record should note whether the current fixture set still explains the alert clearly, whether the event remains compatible with the control-plane-first analyst workflow, and whether a new fixture or mapping update is required.

## 8. Baseline Alignment Notes

This runbook remains aligned with `docs/source-onboarding-contract.md`, `docs/wazuh-rule-lifecycle-runbook.md`, and `docs/secops-business-hours-operating-model.md`.

It preserves the Wazuh-backed source boundary, keeps false-positive expectations explicit, and avoids any promise of production expansion beyond the reviewed GitHub audit family.
