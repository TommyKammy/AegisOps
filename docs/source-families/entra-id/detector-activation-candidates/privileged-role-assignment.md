# Entra ID Privileged Role Assignment Candidate

Lifecycle state: `candidate`

Candidate scope: Entra ID privileged directory role assignments.

This candidate covers the reviewed Entra ID signal where an audit record shows a privileged directory role assignment. The current fixture-backed example is `Add member to role` with `data.privilege.scope` set to `directory_role` and `data.privilege.permission` set to `Global Administrator`.

The candidate exists to make one detector activation path reviewable from the existing detection-ready Entra ID source-family package. It is not a detector catalog, direct Entra ID remediation path, Entra ID-owned workflow truth, Microsoft 365 audit uplift, or production activation approval.

## Candidate Rule Review Criteria

Reviewers may consider this candidate only when all of the following are true:

- source family is Entra ID admitted through the reviewed Wazuh-backed intake boundary;
- `decoder.name` is `entra_id`;
- `rule.id` is `entra-id-role-assignment`;
- `data.source_family` is `entra_id`;
- `data.audit_action` is `Add member to role`;
- `data.operation` is `Add member to role`;
- `data.record_type` is `Entra ID audit`;
- `data.privilege.change_type` is `role_assignment`;
- `data.privilege.scope` is `directory_role`;
- `data.privilege.permission` is `Global Administrator`;
- tenant context, actor identity, target role identity, app or service-principal context, authentication context, request context, Wazuh rule metadata, Wazuh manager identity, location, and timestamp remain present and reviewable; and
- missing, malformed, placeholder, or inferred provenance keeps the candidate blocked rather than treated as detector-ready.

The rule must not infer tenant, directory role, actor, target, account, issue, or environment linkage from naming conventions, path shape, comments, or nearby metadata alone. It requires the explicit Entra ID audit fields preserved by the reviewed Wazuh fixture and onboarding package.

## Fixture And Parser Evidence

Fixture and parser evidence is anchored to `control-plane/tests/fixtures/wazuh/entra-id-alert.json`.

The reviewed fixture proves that:

- `decoder.name` is `entra_id`;
- `data.audit_action` is `Add member to role`;
- `data.operation` is `Add member to role`;
- `data.record_type` is `Entra ID audit`;
- `data.privilege.scope` is `directory_role`;
- `data.privilege.permission` is `Global Administrator`;
- Wazuh manager identity is `wazuh-manager-entra-1`;
- rule identity is `entra-id-role-assignment`;
- tenant identity is `tenant-001`;
- actor identity is `spn-operations`;
- target role identity is `role-global-admin`;
- correlation context is `entra-corr-0001`; and
- request context is `ENTRA-REQ-0001`.

This evidence is sufficient for candidate review only. Parser changes, rule metadata changes, source field changes, tenant or directory-object mapping changes, timestamp changes, or provenance changes require fixture refresh and renewed review before the candidate can move toward staging.

## Staging Activation Expectations

Staging activation expectations are:

- keep lifecycle state at `candidate` until rule review, rollout review, fixture review, expected-volume review, and false-positive review are recorded;
- validate the candidate against the reviewed Entra ID fixture and any separately approved staging replay corpus before production activation is considered;
- use staging only to observe candidate behavior in a controlled validation environment or test index;
- record expected alert volume, expected benign administrative cases, reviewer ownership, next-review date, rollback owner, and disable owner before moving beyond candidate review; and
- keep AegisOps alert, case, approval, action, execution, and reconciliation state authoritative inside the control plane.

This document does not approve active OpenSearch detector deployment, live Wazuh rule rollout, Entra ID API credentials, direct directory mutation, automated response, Microsoft 365 audit detector activation, or production write-capable behavior.

## False-Positive Review Expectations

False-positive review expectations must cover routine directory administration, approved identity operations, reviewed service identity behavior, privileged role assignment maintenance, scheduled change windows, emergency access procedure review, and expected automation-path maintenance.

The reviewer must record whether the event is benign, suspicious, deferred, or still ambiguous. A benign conclusion requires explicit linkage to reviewed AegisOps records, an approved change-management path, or read-oriented Entra ID audit evidence. Familiar actor, tenant, role, app, service principal, or target names are not enough to suppress the candidate.

If the false-positive explanation depends on missing parser evidence, missing Wazuh provenance, raw forwarded identity, placeholder credentials, sample secrets, unsigned tokens, or inferred scope linkage, the candidate remains blocked.

## Rollback And Disable Procedure

Rollback and disable expectations are:

- disable or withdraw the candidate activation if staged behavior produces unacceptable false positives, source drift, parser drift, missing provenance, missing tenant context, or analyst load outside the reviewed expectation;
- restore the last reviewed fixture, rule metadata, or candidate state when parser or Wazuh rule changes invalidate the evidence package;
- move the lifecycle state back to `candidate` or `draft` until refreshed evidence is reviewed;
- keep the Entra ID onboarding package as source-family evidence only unless a separate review approves a new detector candidate; and
- preserve a reviewable record of the disable reason, rollback reason, affected fixture evidence, owner, and follow-up.

Rollback is a content and validation reset path. It does not authorize direct Entra ID actioning, directory mutation, credential reset, destructive response, or undocumented production hotfixes.

## Source Evidence Boundary

Entra ID remains source evidence only.

This candidate does not authorize direct Entra ID actioning, directory mutation, source-side credentials, credential changes, Entra ID-owned case authority, Entra ID-owned approval state, Entra ID-owned action state, Entra ID-owned execution state, Entra ID-owned reconciliation truth, Microsoft 365 audit silent uplift, or autonomous remediation.

It also does not make Entra ID the authority for AegisOps case state, approval state, action state, execution state, or reconciliation outcomes.
