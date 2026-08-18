# ADR 0020: Phase 67 GA-Prerequisite Boundary

- **Status**: Proposed
- **Date**: 2026-08-12
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`, `docs/auth-baseline.md`, `docs/retention-evidence-and-replay-readiness-baseline.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-66-6-rc-supportability-proof.md`, `docs/phase-66-7-rc-authority-boundary-proof-pack.md`
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
approver for GA acceptance, define a GA release-authority root, or establish the
additional immutable-reference and decision-event controls proposed here.

The implemented Phase 67 Epic has a narrower boundary. It describes a bounded,
single-host, non-production real-integration trial and explicitly excludes GA
acceptance, production rollout, design-partner success, HA, scale, and disaster
recovery. A closed issue, merged pull request, passing verifier, or successful
lab component trial therefore cannot supply the evidence required by the
accepted GA gate.

The accepted Phase 51.3 contract remains the current baseline while this ADR is
Proposed. What remains undecided is whether Phase 67 should be renamed and
governed as GA-prerequisite validation, whether GA acceptance should move to a
separate gate decision, and whether that gate should introduce an authorized
human decision independent of evidence production. The authority root,
authority-chain validation, immutable evidence binding, and explicit GA decision
event would be new release-governance controls proposed by this ADR. Deferring
these decisions leaves the roadmap label and the actual trial boundary in
conflict and makes GA overclaim difficult to audit.

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
- The real-user or design-partner evidence must demonstrate attributable use of
  every accepted Phase 51.3 GA journey family across that scope: install or
  upgrade, Wazuh signal admission, Shuffle delegated execution, AI advisory
  trace review, report export, restore dry-run, upgrade-plan rehearsal,
  support-bundle generation, and accepted limitations ownership. Inherited RC
  or lab evidence and generic operability evidence cannot substitute for an
  attributable real-user or design-partner exercise of any family.
- The Phase 66.7 packet's `repository_revision` and every additional GA evidence
  item must bind to the one immutable evidence revision recorded by the GA gate.
  If the inherited packet names another revision, it must be regenerated and
  revalidated at the gate revision. Combining it with current-revision GA
  evidence is mixed-snapshot evidence and blocks acceptance.
- The complete inherited RC packet and every additional GA evidence reference
  must carry an immutable content identity. Repository-owned artifacts must bind
  to their exact Git object or content digest; authoritative AegisOps records
  must bind to an equivalent tamper-evident record version or snapshot identity.
  This applies to real-user or design-partner journey records, the operability
  manifest and its environment, target, and execution records, ownership and
  limitation records, and release-authority records and chain snapshots. The
  gate must resolve and verify each input identity when the decision is made. A
  mutable label, path, URL, or record identifier without immutable snapshot
  binding blocks acceptance.
- The GA gate record preserves the accepted Phase 51.3 metadata: the real-user
  or design-partner record reference, reviewed environment class, operator or
  design-partner owner, evidence date, gate record identifier, accepted
  limitations, support owner, upgrade owner, and follow-up decision. It
  additionally records the evidence revision and immutable evidence index.
- The gate record must contain an attributable, immutable human GA decision
  event, not merely an assigned approver identity. The event records an explicit
  outcome, decision timestamp, and justification or attestation, and binds the
  approver identity and authority record to the gate identifier, intended launch
  scope, evidence revision, and immutable input-evidence index. The completed
  decision event receives its own immutable AegisOps record identity or version
  as part of its atomic creation; it is not an input to the index that it binds.
  Only an explicit `accepted` outcome satisfies GA. A missing, pending,
  rejected, expired, superseded, or mismatched decision blocks acceptance.
- The human GA approver is eligible only when the gate record references an
  AegisOps-owned, auditable role-assignment or explicit-delegation record that
  binds the attributable identity to GA release authority for the recorded
  intended launch scope and is effective and unrevoked when the decision is
  made. The existing action-approver role, platform-administration access, an
  evidence-owner, product-owner, or release-owner label, or a human disposition
  does not confer that authority by itself. The authorized approver must remain
  distinct from every evidence producer.
- Each role-assignment or delegation record must also name its issuer, issuance
  time, immutable record identity, granted scope, and the accepted AegisOps
  governance record or prior delegation that authorized the issuer to grant
  equal-or-narrower GA release authority. At decision time the gate must resolve
  an effective, unrevoked chain to an authority root established outside the
  delegation chain by a separately accepted AegisOps governance decision. That
  root decision must name the root holder and scope, be approved by an
  attributable competent release-governance authority of the AegisOps-owning
  organization that is distinct from the designated root, and retain immutable
  approval provenance. It must bind that approving authority to an immutable,
  resolvable organizational appointment, charter, or equivalent governance
  reference that authorizes designation of the root; a title or competence
  assertion alone does not. Repository write, merge, or administration access,
  ADR authorship, and approval of this ADR alone do not establish or approve the
  root. Missing links, cycles, scope widening, an issuer who equals the grantee,
  and self-issued or otherwise unauthorized grants block acceptance. This ADR
  does not designate that initial authority root or grant GA release authority.
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

Each indexed execution record must name its run identifier, deployment-class
identifier, immutable environment-record reference, execution start and
completion times, operator, observed result, artifact digest, owner, and owner
review time. It must also reference an immutable target record with its content
identity, declaration time, and AegisOps append-only audit-sequence reference or
equivalent independently timestamped external attestation. That independent
record must establish the target before the execution's authoritative start
time. A caller-supplied timestamp, Git author or committer date, or assertion
created only in post-run output does not prove predeclaration. A plan, dry run,
service-health result, CI result, or verifier result cannot by itself satisfy an
executed evidence reference.

The exercises must run in at least one production-like environment for every
materially distinct deployment class in the intended launch scope. Each
environment record must bind the supported operating system and architecture,
deployment profile and topology, release image and configuration digests,
proxy, TLS, and secret boundary, persistent and backup-separated storage,
resource floor, and in-scope Wazuh and Shuffle routes. Every difference from the
declared launch class requires an owned blocking or non-blocking disposition.
For each declared class, the manifest must contain the complete mandatory
exercise set, and an execution counts only for the class and environment record
to which it is immutably bound.

Exercises must use synthetic or reviewed-redacted inputs. Retained GA evidence
must not contain production secrets, credentials, authorization material,
certificate or key material, raw customer-private data, ticket-private content,
customer identifiers, email addresses, or workstation-local paths. A redaction
assertion does not permit retaining the forbidden value beside it. Direct
production access is neither required nor accepted as a substitute for
production-like evidence.

The operability packet passes only when every mandatory exercise exists, is
non-placeholder, is bound to the gate evidence revision directly or through a
revalidation result that is itself produced at and bound to that revision, meets
its target declared before execution, preserves AegisOps record-chain and
authority invariants, retains failed-path and clean-state evidence, and leaves
no unresolved blocking operability limitation. Missing, mixed-revision, stale,
post-hoc-targeted, failed, or subordinate-authority evidence blocks GA.

Every owner or accountable review in the GA packet must bind an attributable
reviewer who is distinct from the evidence producer and owner to the exact
immutable evidence identity reviewed, and record `accepted` or
`accepted-with-follow-up`. The latter is allowed only for a non-blocking
follow-up with impact, owner, and due date. A missing, self-reviewed, rejected, or
mismatched review blocks acceptance.

### GA Evidence Freshness

All age and ordering checks use the immutable GA decision event's
AegisOps-recorded `decision_at`; a caller-supplied decision time cannot establish
freshness. For every target-bound execution, independent records must prove
`target_declared_at < started_at <= completed_at <= owner_review_at <= decision_at`.
Every other reviewed evidence record must prove
`observed_at <= owner_review_at <= decision_at`. These orderings require
AegisOps append-only audit sequencing or an equivalent independently timestamped
attestation. The decision timestamp must not be more than five minutes in the
future when verified.

The following maximum ages are measured backward from `decision_at`:

| Evidence family                                                                                                                                                          | Maximum age                                                                                                                                                      | Required action after expiry                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Inherited Phase 66.7 RC packet                                                                                                                                           | Its regeneration and focused revalidation must complete within 24 hours.                                                                                         | Regenerate and revalidate the whole packet at the gate evidence revision; its native observation, review, and decision freshness rules must pass.                                                          |
| Real-user or design-partner GA journey records                                                                                                                           | Each required journey completion and owner review must be no more than 720 hours old.                                                                            | Repeat each expired journey family with attributable real-user or design-partner use at the gate evidence revision and reviewed environment class; a desk review or owner reattestation cannot refresh it. |
| Capacity, component-interruption and recovery, clean-target restore, exact-version upgrade and rollback, and any claimed HA, disaster-recovery, or fleet-scale execution | Each execution completion and owner review must be no more than 720 hours old.                                                                                   | Rerun each expired family for every bound deployment class at the gate evidence revision; a verifier rerun or owner reattestation alone cannot refresh it.                                                 |
| Monitoring, diagnostic, support-bundle, and redaction execution                                                                                                          | Each execution completion and owner review must be no more than 24 hours old.                                                                                    | Regenerate the artifacts and rerun the affected checks for every bound deployment class.                                                                                                                   |
| Environment equivalence, support and upgrade ownership, limitation disposition, and release-authority state                                                              | An immutable state snapshot and accountable review must be no more than 24 hours old, and every authority link must be effective and unrevoked at `decision_at`. | Re-resolve the authoritative state and renew its accountable review or disposition; copying the prior snapshot cannot refresh it.                                                                          |

A material version, topology, configuration, route, environment, target, owner,
limitation, or authority change invalidates the affected evidence even inside
its maximum-age window.

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
- keep gate decisions revision-bound, content-bound, and auditable,
- introduce explicit authorized-human accountability, a verifiable authority
  chain, and separation of duties for GA acceptance,
- make incomplete real-user journey coverage, operability evidence, support,
  upgrade, and limitation ownership explicit,
- align roadmap terminology with the Phase 67 trial that actually exists, and
- fail closed when documentation or automation could imply broader readiness.

## 4. Options Considered

### Option A: Retain the accepted Phase 67-to-GA mapping

This preserves the current contract and requires no migration. It leaves the
roadmap label broader than the implemented trial and risks treating issue or CI
completion as evidence that the GA gate itself was accepted.

### Option B: Make Phase 67 prerequisite validation and separate GA acceptance

This is the proposed option. It aligns the phase boundary with the bounded trial
and makes the missing launch-scope evidence and proposed authorized-human
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
Resolving every reference to immutable content and requiring an explicit
decision event prevents a mutable artifact or assigned identity from being
mistaken for acceptance. The 720-hour journey and heavy-exercise window aligns
with the reviewed monthly restore and maintenance cadence, while the 24-hour
packet, diagnostic, and decision-state window retains the stricter Phase 66.6
and 66.7 precedent for rapidly changing evidence. Fixed windows and explicit
expiry actions prevent each implementation from choosing its own definition of
stale evidence.

## 6. Consequences

### Positive Consequences

If approved and implemented:

- Phase 67 results remain bounded and non-production,
- missing GA evidence remains visible as owned prerequisite blockers,
- a later GA decision preserves every accepted Phase 51.3 GA journey and
  metadata requirement and additionally binds immutable evidence identities, an
  explicit human outcome, and a verified authority chain, and
- documentation and verifiers reject claims that Phase 67 itself accepts GA.

### Negative Consequences

If approved and implemented:

- the existing Phase 51, Phase 65, and Phase 66 contract surfaces require a
  coordinated migration,
- every materially distinct launch class requires a fresh mandatory-operability
  exercise set within the fixed family-specific decision windows,
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
and adversarial-test pairs for the GA journey-family index, immutable evidence
index, explicit human decision event, inherited-evidence revalidation,
release-authority chain, and per-deployment-class GA operability manifest. It
must enforce pre-run target identity, bound owner-review outcomes, freshness,
and retained-evidence secret hygiene without storing forbidden source values.

## 8. Security Impact

This proposal changes no runtime privileges, credentials, network exposure, or
runtime attack surface. If approved, it would tighten release-evidence handling
by requiring synthetic or reviewed-redacted inputs and prohibiting retained
secret, authorization, customer-private, and workstation-local material. It
would also introduce an authorized and independent human approval boundary
specifically for GA acceptance. That is a new release-governance policy,
distinct from the accepted baseline's human-approval requirements for
controlled write or destructive action execution. This proposal neither grants
that authority nor designates its root. The intended security benefit is to
prevent subordinate systems, mutable evidence, unauthorized grants, or a named
but inactive approver from conferring GA acceptance.

## 9. Rollback / Exit Strategy

Before approval, the proposal can be marked Rejected with no implementation
rollback because it does not alter the accepted baseline.

After approval and implementation, rollback or supersession is triggered if the
separate-gate model cannot preserve every required Phase 51.3 GA record field,
cannot bind each GA decision to an immutable evidence revision and content,
cannot resolve an authorized release-authority chain, or cannot prevent Phase 67
prerequisite evidence from conferring GA acceptance. A later accepted ADR or
requirements-baseline change that assigns GA acceptance to a different phase or
authority is also a trigger.

When a post-implementation trigger above applies, replacing this decision
requires a new ADR that records why the boundary is changing and supersedes ADR 0020. The related implementation changes would then be reverted or migrated in
a separate pull request. There are no irreversible runtime or data changes in
this decision.

## 10. Validation

Review of this proposal must confirm:

- consistency with the accepted Phase 51.3 gate contract and ADR 0011,
- explicit separation of prerequisite evidence from GA acceptance,
- attributable real-user or design-partner exercise coverage for every accepted
  Phase 51.3 GA journey family and preservation of every accepted GA metadata
  field,
- one-revision binding across the inherited RC packet and every additional GA
  evidence item, including fail-closed mixed-snapshot rejection and
  revalidation,
- resolution of every GA reference to immutable content or authoritative-record
  state rather than a mutable label, path, URL, or bare identifier,
- an explicit immutable human decision event with attributable outcome, time,
  justification, gate, launch-scope, revision, evidence, and authority bindings,
- proof that the approver held effective, unrevoked GA release authority for the
  recorded launch scope, remained distinct from every evidence producer, and
  inherited that authority through a non-cyclic, non-self-issued,
  non-scope-widening chain to a separately accepted root authorized by the
  AegisOps-owning organization's competent release-governance authority,
- complete mandatory exercise coverage per deployment class, immutable pre-run
  target declaration with independently recorded chronology, accepted
  non-self-review bound to each immutable evidence identity, the fixed
  family-specific freshness and invalidation rules, retained-data hygiene, and
  testable HA, scale, and disaster-recovery dispositions,
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
- This proposal does not designate an initial GA authority root or grant GA
  release authority.
- This proposal does not require direct production access or customer data;
  retained evidence remains restricted by Section 2.
- This proposal does not establish a public SLA, 24x7 support commitment,
  enterprise HA or multi-site disaster-recovery scope, fleet-scale
  certification, or multi-tenant readiness.

## 12. Approval

- **Proposed By**: Codex for PR #1424
- **Reviewed By**: Pending
- **Approved By**: Pending
- **Approval Date**: Pending
