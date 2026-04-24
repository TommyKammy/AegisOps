# Entra ID Analyst Triage Runbook

## 1. Purpose

This runbook defines the reviewed analyst triage posture for the approved Entra ID family.

It complements the AegisOps Source Onboarding Contract, the Wazuh Rule Lifecycle and Validation Runbook, `docs/source-families/entra-id/onboarding-package.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-rule-lifecycle-runbook.md`, and `docs/secops-business-hours-operating-model.md`.

The runbook keeps Entra ID handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit.

## 2. Scope and Non-Goals

This runbook applies to reviewed Entra ID alerts and cases that enter AegisOps through the Wazuh-backed intake boundary.

It covers read-oriented triage, evidence capture, disposition decisions, and fixture refresh expectations for the reviewed Entra ID source profile.

Direct Entra ID actioning remains out of scope. This runbook does not authorize directory changes, credential changes, source-side credentials, detector activation, Entra ID-owned case authority, or any unsupported source family.

It also does not replace the source onboarding contract or the Wazuh rule lifecycle runbook. Those documents remain authoritative for onboarding evidence and rule-change validation.

## 3. Reviewed Triage Posture

Entra ID items are triaged as queue-driven work items rather than as autonomous response triggers.

The analyst first determines whether the item is a reviewed Entra ID audit event, a duplicate, an expected administrative change, or a potentially interesting privilege, directory, or authentication change.

If the item is already explained by known directory administration, approved identity operations, a reviewed service identity, or an approved change window, the analyst records the benign explanation and closes or links the item according to the current case state.

If the item is not clearly benign, the analyst gathers read-oriented evidence, preserves the reviewed source identity, and decides whether the work item should remain an alert, promote to a case, or wait for the next business-hours review cycle.

The control-plane-first analyst workflow remains the decision boundary. Entra ID output informs triage, but it does not become the source of truth for case state, approval state, or action execution.

## 4. Family Assumptions and False-Positive Expectations

The reviewed Entra ID family preserves tenant context, actor identity, target identity, authentication context, privilege-change metadata, and directory provenance.

The directory boundary stays explicit so the reviewed triage path does not collapse into a generic identity provider assumption.

False-positive expectations are centered on routine directory administration, approved identity operations, reviewed service identity activity, role assignment maintenance, and changes that were already reviewed in a separate change-management path.

Expected benign examples include role assignment updates, group membership maintenance, app registration changes, credential lifecycle work, or other reviewed administrative activity that remains within the approved boundary.

Analysts must not assume that every Entra ID alert indicates malicious activity. The triage posture requires explicit evidence before escalation, especially when the event can be explained by a normal maintenance task or a reviewed automation path.

Unsupported Entra ID telemetry families remain out of scope. Direct vendor-local actioning remains out of scope even when a directory event looks urgent.

## 5. Detector-use handling

Entra ID may support detector review only within the approved detection-ready scope in the onboarding package.

Future detector-use review must confirm that the event is a reviewed Entra ID audit signal entering through the Wazuh-backed intake boundary and that the detector depends only on reviewed field coverage, parser evidence, timestamp quality, and Wazuh provenance.

Analysts must treat Entra ID as source evidence for AegisOps review, not as Entra ID-owned workflow truth or direct action authority.

Detector-ready handling remains blocked when the event depends on direct Entra ID actioning, non-audit Entra ID telemetry, tenant or directory-object naming conventions alone, untrusted forwarded identity, placeholder credentials, missing parser evidence, or missing provenance.

Detector activation still requires separate detector review, rollout review, and Wazuh rule lifecycle validation. The runbook does not let a detection-ready source-family package bypass rule QA, staging, expected-volume review, false-positive review, or production activation approval.

## 6. Family-specific false-positive review

Family-specific false-positive review must remain visible in each triage record and each future detector review that depends on Entra ID.

Reviewers should compare the event against routine directory administration, approved identity operations, reviewed service identity behavior, role assignment maintenance, app registration maintenance, credential lifecycle work, scheduled change windows, and business-hours operating expectations before escalating.

False-positive notes must state why the event is benign, suspicious, deferred, or still ambiguous. They must also state whether the explanation comes from reviewed AegisOps records, an approved change-management path, or read-oriented Entra ID audit evidence.

Analysts must not suppress or downgrade an event solely because the actor, tenant, group, role, app, or target object name looks familiar. The benign explanation needs an explicit reviewed linkage to the authoritative scope record or the item remains queued for review.

## 7. Provenance handling

Provenance handling starts from the reviewed Wazuh boundary and the Entra ID onboarding package, not from directory-authored text as independent authority.

The analyst preserves Wazuh manager identity, decoder identity, rule identity, rule severity, rule description, source location, event timestamp, source family, Entra ID audit action, actor, target, tenant, app or service-principal context, authentication context, privilege context, correlation id, and request context when present.

If accountable source identity, actor identity, target identity, tenant context, timestamp quality, parser evidence, or Wazuh provenance is missing or malformed, the analyst keeps the item out of detector-ready handling until the prerequisite is repaired or a documented exception path applies.

Missing or malformed provenance is not treated as a reason to infer success from tenant names, directory object names, comments, nearby metadata, or raw vendor-authored prose. The analyst records the gap and keeps the AegisOps control-plane guard in place.

## 8. Evidence to Collect

The analyst captures read-oriented evidence that answers what changed, who or what changed it, which target object was affected, and why the item is or is not interesting.

At minimum, the analyst records:

- the reviewed Entra ID event summary;
- the accountable source identity and delivery path;
- Wazuh manager, decoder, rule, location, timestamp, and parser evidence used for detector-ready handling;
- the actor identity, including whether it was a human, service principal, managed identity, or other automation identity when present;
- the target object, user, group, role assignment, app registration, credential object, or policy context;
- the tenant, directory, authentication, and correlation context;
- the privilege or access change context, if any;
- the family-specific false-positive review outcome;
- the raw payload or fixture reference used for review; and
- the reason the event is benign, escalated, or deferred.

The reviewer should keep evidence aligned with `docs/source-onboarding-contract.md` and the reviewed Entra ID onboarding package. If a new reviewed alert shape appears, the corresponding fixture under `control-plane/tests/fixtures/wazuh/entra-id-alert.json` and the related Wazuh rule lifecycle evidence must be refreshed before downstream workflow assumptions change.

## 9. Business-Hours Handling

This runbook follows the Business-hours SecOps daily operating model.

Entra ID alerts that do not require immediate same-day handling remain queued for the next business-hours review cycle with enough context recorded that the next analyst does not need to reconstruct intent from raw system output.

If an item appears to require escalation, the analyst records the reason, the affected scope, and the review context before requesting any human follow-up.

After-hours handling remains explicit and bounded. The reviewed path does not imply 24x7 analyst watchstanding, and it does not authorize vendor-local actioning or automatic enforcement.

## 10. Validation and Fixture Expectations

The reviewer treats the reviewed Entra ID fixture as the canonical replay reference for this family.

Any new reviewed Entra ID rule shape, provenance expectation, or identity branch must be validated against `docs/wazuh-rule-lifecycle-runbook.md` before it is treated as stable for triage.

The analyst triage record should note whether the current fixture set still explains the alert clearly, whether the event remains compatible with the control-plane-first analyst workflow, and whether a new fixture or mapping update is required.

## 11. Baseline Alignment Notes

This runbook remains aligned with `docs/source-onboarding-contract.md`, `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/wazuh-rule-lifecycle-runbook.md`, and `docs/secops-business-hours-operating-model.md`.

It preserves the Wazuh-backed source boundary, keeps false-positive expectations explicit, keeps detector-use approval separate from detector activation, and avoids any promise of production expansion beyond the reviewed Entra ID family.
