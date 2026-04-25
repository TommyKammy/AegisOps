# GitHub Audit Repository Admin Membership Change Candidate

Lifecycle state: `candidate`

Candidate scope: GitHub audit repository administrator membership changes.

This candidate covers the reviewed GitHub audit signal where a repository membership or team membership event grants administrator-level repository access. The current fixture-backed example is `member.added` with `data.privilege.scope` set to `repository_admin` and `data.privilege.permission` set to `admin`.

The candidate exists to make one detector activation path reviewable from the existing detection-ready source-family package. It is not a detector catalog, direct GitHub remediation path, GitHub-owned workflow truth, or production activation approval.

## Candidate Rule Review Criteria

Reviewers may consider this candidate only when all of the following are true:

- source family is GitHub audit admitted through the reviewed Wazuh-backed intake boundary;
- `decoder.name` is `github_audit`;
- `rule.id` is `github-audit-privilege-change`;
- `data.source_family` is `github_audit`;
- `data.audit_action` is `member.added`;
- `data.privilege.change_type` is `membership_change`;
- `data.privilege.scope` is `repository_admin`;
- `data.privilege.permission` is `admin`;
- actor identity, target identity, repository context, organization context, request context, Wazuh rule metadata, Wazuh manager identity, location, and timestamp remain present and reviewable; and
- missing, malformed, placeholder, or inferred provenance keeps the candidate blocked rather than treated as detector-ready.

The rule must not infer repository, organization, account, issue, or environment linkage from naming conventions, path shape, comments, or nearby metadata alone. It requires the explicit GitHub audit fields preserved by the reviewed Wazuh fixture and onboarding package.

## Fixture And Parser Evidence

Fixture and parser evidence is anchored to `control-plane/tests/fixtures/wazuh/github-audit-alert.json`.

The reviewed fixture proves that:

- `decoder.name` is `github_audit`;
- `data.audit_action` is `member.added`;
- `data.privilege.permission` is `admin`;
- Wazuh manager identity is `wazuh-manager-github-1`;
- rule identity is `github-audit-privilege-change`;
- repository context is `TommyKammy/AegisOps`;
- organization context is `TommyKammy`;
- actor identity is `octocat`;
- target identity is `security-reviews`; and
- request context is `GH-REQ-0001`.

This evidence is sufficient for candidate review only. Parser changes, rule metadata changes, source field changes, or provenance changes require fixture refresh and renewed review before the candidate can move toward staging.

## Staging Activation Expectations

Staging activation expectations are:

- keep lifecycle state at `candidate` until rule review, rollout review, fixture review, expected-volume review, and false-positive review are recorded;
- validate the candidate against the reviewed GitHub audit fixture and any separately approved staging replay corpus before production activation is considered;
- use staging only to observe candidate behavior in a controlled validation environment or test index;
- record expected alert volume, expected benign administrative cases, reviewer ownership, next-review date, and rollback owner before moving beyond candidate review; and
- keep AegisOps alert, case, approval, action, execution, and reconciliation state authoritative inside the control plane.

This document does not approve active OpenSearch detector deployment, live Wazuh rule rollout, GitHub API credentials, direct GitHub mutation, automated response, or production write-capable behavior.

## False-Positive Review Expectations

False-positive review expectations must cover routine repository administration, approved maintainer activity, access review cleanup, automation identity behavior, scheduled change windows, onboarding or offboarding work, and expected team membership maintenance.

The reviewer must record whether the event is benign, suspicious, deferred, or still ambiguous. A benign conclusion requires explicit linkage to reviewed AegisOps records, an approved change-management path, or read-oriented GitHub audit evidence. Familiar actor, team, repository, workflow, or organization names are not enough to suppress the candidate.

If the false-positive explanation depends on missing parser evidence, missing Wazuh provenance, raw forwarded identity, placeholder credentials, or inferred scope linkage, the candidate remains blocked.

## Rollback Expectations

Rollback expectations are:

- disable or withdraw the candidate activation if staged behavior produces unacceptable false positives, source drift, parser drift, missing provenance, or analyst load outside the reviewed expectation;
- restore the last reviewed fixture, rule metadata, or candidate state when parser or Wazuh rule changes invalidate the evidence package;
- move the lifecycle state back to `candidate` or `draft` until refreshed evidence is reviewed; and
- preserve a reviewable record of the rollback reason, affected fixture evidence, owner, and follow-up.

Rollback is a content and validation reset path. It does not authorize direct GitHub API actioning, repository mutation, destructive response, or undocumented production hotfixes.

## Source Evidence Boundary

GitHub audit remains source evidence only.

This candidate does not authorize direct GitHub API actioning, source-side mutation, GitHub credentials, GitHub-owned case authority, GitHub-owned approval state, GitHub-owned action state, GitHub-owned execution state, GitHub-owned reconciliation truth, or autonomous remediation.

It also does not make GitHub the authority for AegisOps case state, approval state, action state, execution state, or reconciliation outcomes.
