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
- GA acceptance is a separate gate decision. It requires the complete inherited
  RC proof packet plus real-user or design-partner evidence across the intended
  launch scope, production-operability evidence, support and upgrade ownership,
  and explicit disposition of every blocking limitation.
- The Phase 66.7 packet's `repository_revision` and every additional GA evidence
  item must bind to the one immutable evidence revision recorded by the GA gate.
  If the inherited packet names another revision, it must be regenerated and
  revalidated at the gate revision. Combining it with current-revision GA
  evidence is mixed-snapshot evidence and blocks acceptance.
- The GA gate record preserves the accepted Phase 51.3 metadata: the real-user
  or design-partner record reference, reviewed environment class, operator or
  design-partner owner, evidence date, gate record identifier, accepted
  limitations, support owner, upgrade owner, and follow-up decision. It
  additionally records the evidence revision and a human approver who is
  independent of evidence production.
- The human GA approver is eligible only when the gate record references an
  AegisOps-owned, auditable role-assignment or explicit-delegation record that
  binds the attributable identity to GA release authority for the recorded
  intended launch scope and is effective and unrevoked when the decision is
  made. The existing action-approver role, platform-administration access, an
  evidence-owner, product-owner, or release-owner label, or a human disposition
  does not confer that authority by itself. The authorized approver must remain
  distinct from every evidence producer.
- A result such as `integration_trial_passed_with_owned_limitations` remains
  prerequisite evidence only. Issue closure, pull-request merge, CI success,
  external-service health, or a subordinate Wazuh or Shuffle result cannot
  convert it into GA acceptance.

### Production-Operability Evidence

For this proposal, production-operability evidence means one machine-verifiable
GA operability manifest bound to the GA gate record identifier and evidence
revision. The manifest must directly index:

- the declared launch scope and environment-equivalence record,
- executed capacity evidence with a predeclared workload, duration, concurrency
  or data-volume envelope and throughput, latency, error-rate, and
  resource-headroom targets,
- controlled component-interruption, application-aware clean-target restore,
  and recovery evidence with declared recovery targets,
- exact-version upgrade and rollback rehearsal evidence with post-operation
  smoke and authoritative-record-chain checks,
- monitoring, diagnostic, support-bundle, and redaction evidence, and
- every operability limitation with its impact, owner, disposition, decision
  date, and follow-up date.

Each indexed execution record must name its run identifier, execution time,
operator, target declared before execution, observed result, artifact digest,
and owner. A plan, dry run, service-health result, CI result, or verifier result
cannot by itself satisfy an executed evidence reference.

The exercises must run in at least one production-like environment for every
materially distinct deployment class in the intended launch scope. Each
environment record must bind the supported operating system and architecture,
deployment profile and topology, release image and configuration digests,
proxy, TLS, and secret boundary, persistent and backup-separated storage,
resource floor, and in-scope Wazuh and Shuffle routes. Every difference from the
declared launch class requires an owned blocking or non-blocking disposition.
Production credentials, customer data, and direct production access are not
required.

The operability packet passes only when every mandatory exercise exists, is
non-placeholder, is bound to the gate evidence revision directly or through a
revalidation result that is itself produced at and bound to that revision, meets
its target declared before execution, preserves AegisOps record-chain and
authority invariants, retains failed-path and clean-state evidence, and leaves
no unresolved blocking operability limitation. Missing, mixed-revision, stale,
post-hoc-targeted, failed, or subordinate-authority evidence blocks GA.

Capacity within the declared supported envelope, controlled recovery of
required in-scope components, application-aware restore, and upgrade and
rollback rehearsal are mandatory. Multi-node HA or failover, multi-site
disaster recovery, and fleet-scale exercises are mandatory only when the
intended launch scope claims those capabilities. Otherwise they may be recorded
only as explicitly unsupported launch capabilities with customer or operator
impact, owner, decision date, and follow-up date. Failed or merely unimplemented
exercises cannot be labeled not applicable, and GA claims must remain inside the
resulting launch boundary.

This proposal does not change the accepted baseline or its verifiers. If this
ADR is approved, the status and real approval metadata must be updated together
before a separate implementation pull request applies the decision.

## 3. Decision Drivers

- prevent bounded lab evidence from being overstated as GA acceptance,
- keep gate decisions revision-bound and auditable,
- introduce authorized human accountability and separation of duties for GA
  acceptance,
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
reviewable. Requiring an effective, scope-bound release-authority record also
prevents an unrelated human or an action-approval role from accepting GA.

## 6. Consequences

### Positive Consequences

If approved and implemented:

- Phase 67 results remain bounded and non-production,
- missing GA evidence remains visible as owned prerequisite blockers,
- a later GA decision preserves every accepted Phase 51.3 GA evidence metadata
  field and additionally names its evidence revision and authorized, independent
  approver, and
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

That implementation must also define structured schemas and focused verifier
and adversarial-test pairs for the GA gate record, inherited-evidence
revalidation, release-authority record, and GA operability manifest.

## 8. Security Impact

This proposal changes no privileges, secret handling, network exposure, or
runtime attack surface. If approved, it would introduce an authorized and
independent human approval boundary specifically for GA acceptance. That is a
new release-governance policy, distinct from the accepted baseline's
human-approval requirements for controlled write or destructive action
execution. It would also prevent subordinate systems, CI, issue state, or
generated evidence from gaining release authority. The intended security
benefit is stronger auditability of who accepted GA and which evidence revision
supported the decision.

## 9. Rollback / Exit Strategy

Before approval, the proposal can be marked Rejected with no implementation
rollback because it does not alter the accepted baseline.

After approval and implementation, rollback or supersession is triggered if the
separate-gate model cannot preserve every required Phase 51.3 GA record field,
cannot bind each GA decision to an auditable evidence revision, or cannot
prevent Phase 67 prerequisite evidence from conferring GA acceptance. A later
accepted ADR or requirements-baseline change that assigns GA acceptance to a
different phase or authority is also a trigger.

When a post-implementation trigger above applies, replacing this decision
requires a new ADR that records why the boundary is changing and supersedes ADR 0020. The related implementation changes would then be reverted or migrated in
a separate pull request. There are no irreversible runtime or data changes in
this decision.

## 10. Validation

Review of this proposal must confirm:

- consistency with the accepted Phase 51.3 gate contract and ADR 0011,
- explicit separation of prerequisite evidence from GA acceptance,
- preservation of every accepted Phase 51.3 GA evidence metadata field,
- one-revision binding across the inherited RC packet and every additional GA
  evidence item, including fail-closed mixed-snapshot rejection and
  revalidation,
- identification and justification of authorized, independent human GA approval
  as a new release-governance control, including proof that the named approver
  held effective, unrevoked GA release authority for the recorded launch scope
  and remained distinct from every evidence producer,
- testable artifact, production-like-environment, pass-criteria, and HA, scale,
  and disaster-recovery disposition requirements for production-operability
  evidence,
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
- This proposal does not require production credentials, customer data, or
  direct production access to produce operability evidence.
- This proposal does not establish a public SLA, 24x7 support commitment,
  enterprise HA or multi-site disaster-recovery scope, fleet-scale
  certification, or multi-tenant readiness.

## 12. Approval

- **Proposed By**: Codex for PR #1424
- **Reviewed By**: Pending
- **Approved By**: Pending
- **Approval Date**: Pending
