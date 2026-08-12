# ADR 0020: Phase 67 GA-Prerequisite Boundary

- **Status**: Proposed
- **Date**: 2026-08-12
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`
- **Product**: AegisOps
- **Related Issues**: #1414, #1418
- **Related ADRs**: `docs/adr/0011-phase-51-1-replacement-boundary.md`
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

The accepted Phase 51.3 gate contract currently maps Phase 67 directly to GA.
It requires real-user or design-partner evidence, supportability, known
limitation ownership, named owners, and a recorded follow-up decision before
that GA mapping may be materialized. It does not require an independent human
approver for GA acceptance.

The implemented Phase 67 Epic has a narrower boundary. It describes a bounded,
single-host, non-production real-integration trial and explicitly excludes GA
acceptance, production rollout, design-partner success, HA, scale, and disaster
recovery. A closed issue, merged pull request, passing verifier, or successful
lab component trial therefore cannot supply the evidence required by the
accepted GA gate.

The accepted Phase 51.3 contract remains the current baseline while this ADR is
Proposed. What remains undecided is whether Phase 67 should be renamed and
governed as GA-prerequisite validation, whether GA acceptance should move to a
separate gate decision, and whether that gate should introduce a human approver
independent of evidence production. That independent-human-approval requirement
would be a new release-governance control proposed by this ADR. Deferring these
decisions leaves the roadmap label and the actual trial boundary in conflict
and makes GA overclaim difficult to audit.

## 2. Proposed Decision

If approved, this ADR would establish the following decision:

- Phase 66 remains the bounded RC evidence phase.
- Phase 67 performs bounded GA-prerequisite validation. It may collect real
  Wazuh and Shuffle interoperability evidence and publish owned blockers, but it
  does not accept GA, authorize production rollout, or establish customer
  success.
- GA acceptance is a separate gate decision. It requires all RC evidence plus
  revision-bound real-user or design-partner evidence across the intended
  launch scope, production-operability evidence, support and upgrade ownership,
  explicit disposition of every blocking limitation, and a human approver who
  is independent of evidence production.
- A result such as `integration_trial_passed_with_owned_limitations` remains
  prerequisite evidence only. Issue closure, pull-request merge, CI success,
  external-service health, or a subordinate Wazuh or Shuffle result cannot
  convert it into GA acceptance.

This proposal does not change the accepted baseline or its verifiers. If this
ADR is approved, the status and real approval metadata must be updated together
before a separate implementation pull request applies the decision.

## 3. Decision Drivers

- prevent bounded lab evidence from being overstated as GA acceptance,
- keep gate decisions revision-bound and auditable,
- introduce human accountability and separation of duties for GA acceptance,
- make missing real-user, operability, support, upgrade, and limitation evidence
  explicit,
- align roadmap terminology with the Phase 67 trial that actually exists, and
- fail closed when documentation or automation could imply broader readiness.

## 4. Options Considered

### Option A: Retain the accepted Phase 67-to-GA mapping

This preserves the current contract and requires no migration. It leaves the
roadmap label broader than the implemented trial and risks treating issue or CI
completion as evidence that the GA gate itself was accepted.

### Option B: Make Phase 67 prerequisite validation and separate GA acceptance

This is the proposed option. It aligns the phase boundary with the bounded trial
and makes the missing launch-scope evidence and proposed independent-human
decision explicit. It also requires an approved baseline change and a separate,
reviewed implementation pull request.

### Option C: Interpret Phase 67 case by case without changing the baseline

This avoids an immediate baseline decision. It produces ambiguous and
non-reproducible gate semantics across issues, documents, and verifiers and is
not sufficiently auditable.

## 5. Rationale

Option B best matches the evidence the repository can currently produce while
retaining an explicit path to GA. Option A can make bounded component success
appear equivalent to launch acceptance. Option C moves the decision into
informal interpretation and cannot provide a stable contract for reviewers or
automation. Requiring a human GA approver who did not produce the evidence would
introduce separation of duties between evidence production and release
acceptance, making the accountable decision and its inputs independently
reviewable.

## 6. Consequences

### Positive Consequences

If approved and implemented:

- Phase 67 results remain bounded and non-production,
- missing GA evidence remains visible as owned prerequisite blockers,
- a later GA decision names its evidence revision, environment, operator,
  support owner, upgrade owner, accepted limitations, independent approver, and
  decision, and
- documentation and verifiers reject claims that Phase 67 itself accepts GA.

### Negative Consequences

If approved and implemented:

- the existing Phase 51, Phase 65, and Phase 66 contract surfaces require a
  coordinated migration,
- Phase 67 completion alone cannot close the GA decision, and
- reviewers must distinguish prerequisite evidence from release acceptance.

### Neutral / Follow-up Consequences

- While this ADR is Proposed, the accepted Phase 51.3 contract remains
  authoritative and no implementation may rely on this proposal.
- After approval, documentation, verifiers, and adversarial tests must be
  updated in a separate implementation pull request.
- Issue #1418 remains open until its own current-revision evidence and operator
  approval requirements are satisfied.

## 7. Implementation Impact

This proposal has no runtime, configuration, schema, deployment, or credential
impact.

If approved, a separate implementation pull request would update the affected
Phase 51 gate, persona, competitive-gap, authority-boundary, and closeout
documents; Phase 65 packaging and upgrade contracts; Phase 66 supportability and
closeout documents; README positioning; and their focused verifier and
adversarial self-test pairs. That implementation must not be merged before this
ADR records approval.

## 8. Security Impact

This proposal changes no privileges, secret handling, network exposure, or
runtime attack surface. If approved, it would introduce an independent human
approval boundary specifically for GA acceptance. That is a new
release-governance policy, distinct from the accepted baseline's human-approval
requirements for controlled write or destructive action execution. It would
also prevent subordinate systems, CI, issue state, or generated evidence from
gaining release authority. The intended security benefit is stronger
auditability of who accepted GA and which evidence revision supported the
decision.

## 9. Rollback / Exit Strategy

Before approval, the proposal can be marked Rejected with no implementation
rollback because it does not alter the accepted baseline.

After approval and implementation, replacing this decision requires a new ADR
that records why the boundary is changing and supersedes ADR 0020. The related
implementation changes would then be reverted or migrated in a separate pull
request. There are no irreversible runtime or data changes in this decision.

## 10. Validation

Review of this proposal must confirm:

- consistency with the accepted Phase 51.3 gate contract and ADR 0011,
- explicit separation of prerequisite evidence from GA acceptance,
- current-revision evidence requirements,
- identification and justification of independent human GA approval as a new
  release-governance control,
- complete approval metadata when the status changes, and
- no claim that this proposal itself accepts GA or production readiness.

After approval, the implementation pull request must run the affected canonical
verifiers and adversarial self-tests. Claim scanners must compare rendered
Markdown text rather than raw delimiters and cover plain text, emphasis, code
spans, links, and table cells, while retaining negative and prerequisite-only
statements. The repository-wide phase-contract verifier and shell-test gates and
`git diff --check` must also pass.

## 11. Non-Goals

- This proposal does not accept the GA gate.
- This proposal does not prove production readiness or customer success.
- This proposal does not complete issue #1418.
- This proposal does not change the currently accepted Phase 51.3 baseline.
- This proposal does not implement or enforce its proposed boundary.

## 12. Approval

- **Proposed By**: Codex for PR #1424
- **Reviewed By**: Pending
- **Approved By**: Pending
- **Approval Date**: Pending
