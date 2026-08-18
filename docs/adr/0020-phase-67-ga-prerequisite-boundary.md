# ADR 0020: Phase 67 GA-Prerequisite Boundary

- **Status**: Proposed
- **Date**: 2026-08-12
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`, `docs/auth-baseline.md`, `docs/retention-evidence-and-replay-readiness-baseline.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-58-5-upgrade-rollback-plan-contract.md`, `docs/phase-65-3-release-channel-upgrade-manifest-contract.md`, `docs/phase-66-6-rc-supportability-proof.md`, `docs/phase-66-7-rc-authority-boundary-proof-pack.md`
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
- The immutable GA evidence index must map every required journey family to
  every materially distinct deployment class in the intended launch scope.
  Each journey record must bind an attributable real-user or design-partner
  owner, immutable deployment-class and environment-record identities, the gate
  evidence revision, immutable family-specific pass criteria, criteria
  declaration, journey-start and completion audit-sequence references, and the
  observed outcome. Before the journey starts, one immutable declaration
  envelope must bind those criteria, the current Accepted deployment-profile and
  environment-criteria identities, the same immutable deployment-class and
  environment-record identities named by the journey, and a machine-verifiable
  comparison for the claimed class across every applicable environment dimension
  defined below.
  The envelope must carry its declaration event identity, AegisOps-recorded
  declaration time, and audit sequence. Independent ordering must prove that the
  criteria and environment comparison were established before the journey
  started. The criteria must incorporate the applicable accepted Phase 51.3
  evidence-family and authority rules. Only an explicit `passed` result against
  every criterion counts; a failed, partial, abandoned, placeholder-backed,
  incomparable, weakening, class-label-only, or after-the-fact record blocks GA.
- A journey record may cover another deployment class or a non-identical
  environment only through a predeclared, immutable, independently reviewed
  journey-coverage rule that
  binds a reserved source-journey identity, family, source class and environment,
  every covered class and environment, the current Accepted profile and
  environment-criteria identities for the source and every covered environment,
  and a journey-specific comparison and rationale for every differing dimension.
  The rule must have its own immutable declaration event identity,
  AegisOps-recorded `rule_declared_at`, declaration audit sequence, attributable
  independent reviewer, `accepted` outcome, `accepted_review_at`, and review
  audit sequence. Independent ordering must prove
  `rule_declared_at <= accepted_review_at < source_journey.started_at`; a caller
  timestamp, post-run acceptance, stale or mismatched criteria, or later
  rebinding cannot prove predeclaration. A generic
  operability environment-equivalence assertion or producer label cannot
  substitute for that journey-level rule, and an unmapped or weaker class or
  family blocks GA.
- Inherited RC evidence is complete only when the immutable Phase 66.7 packet
  and an immutable, independently `accepted` Phase 66.8 closeout result both
  resolve at the gate evidence revision. An immutable authoritative AegisOps
  RC-gate result produced under an Accepted successor contract may replace the
  Phase 66.8 path. Missing, rejected, stale, scope-mismatched, or
  revision-mismatched closeout or gate evidence blocks GA. The Phase 66.7 packet
  alone, closeout prose, verifier output, or issue state cannot substitute. A
  Phase 66.8 closeout result remains subordinate RC evidence and cannot accept
  GA.
- The Phase 66.7 packet's `repository_revision`, the independent RC closeout or
  authoritative RC-gate result, and every additional GA evidence item must bind
  to the one immutable evidence revision recorded by the GA gate. If any
  inherited item names another revision, the affected packet or result must be
  regenerated or independently re-evaluated and revalidated at the gate
  revision. Combining it with current-revision GA evidence is mixed-snapshot
  evidence and blocks acceptance.
- Every real-user or design-partner journey and every operability execution must
  run directly against the release artifacts and configuration mapped to the
  gate evidence revision. An execution from another revision cannot be rebound
  by a verifier rerun, artifact check, owner reattestation,
  environment-equivalence review, or generic revalidation, even while it remains
  inside its freshness window. It must be re-executed with new target, execution,
  and review records. Revalidation is permitted only for non-execution state or
  reference evidence whose accepted source contract expressly defines that path
  and which is resolved as an immutable snapshot at the gate revision.
- The complete inherited RC packet and every additional GA evidence reference
  must carry an immutable content identity. Repository-owned artifacts must bind
  to their exact Git object or content digest; authoritative AegisOps records
  must bind to an equivalent tamper-evident record version or snapshot identity.
  This applies to the independent RC closeout or authoritative RC-gate result,
  real-user or design-partner journey records, the operability manifest and its
  environment, requirements, target, and execution records, ownership and
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
  outcome and justification or attestation and binds the approver identity and
  authority record to the stable canonical gate-definition identity,
  per-decision gate-record identifier, canonical intended launch-scope identity,
  evidence revision, and immutable input-evidence index. Its AegisOps-recorded
  `decision_at` and audit sequence must be assigned by the same authoritative
  transaction, fence, or total-order boundary that atomically creates the event;
  they cannot be caller-supplied, backdated, or future-dated relative to that
  commit. The completed decision event receives its own immutable AegisOps
  record identity or version as part of that atomic creation; it is not an input
  to the index that it binds. If the boundary cannot assign authoritative time
  and sequence at commit, or a future decision time is requested, the attempt
  remains pending and must re-resolve every decision input and mutable-state head
  at a later atomic attempt. Only an explicit `accepted` outcome satisfies GA. A
  missing, pending, rejected, expired, superseded, or mismatched decision blocks
  acceptance.
- The immutable decision event is historical evidence, not current GA status by
  itself. AegisOps must maintain a GA-decision aggregate keyed by that immutable
  decision identity, with an append-only, non-forking lifecycle-transition chain
  and an authoritative current-state head. Atomic creation writes the event and
  an initial head matching its explicit outcome together. Every initial
  `accepted` state must bind the current GA-decision expiry-policy head. In
  `finite` mode the policy must define a machine-verifiable `maximum_lifetime`
  and the commit must prove
  `decision_at < expires_at <= decision_at + maximum_lifetime`. Only an explicit
  `no-automatic-expiry` mode may omit `expires_at`; an approver-supplied distant
  timestamp cannot substitute for that mode. That mode is valid only when the
  current expiry-policy head also binds a separately Accepted evidence-retention
  compatibility-rule current head and the selected retention mode. A
  `current-lifetime` mode must preserve deterministic resolvability and bind the
  periodic integrity-review cadence for the complete decision-input set for as
  long as the decision remains current. A `pre-cutoff-invalidation` mode must
  bind an exact or deterministically computed `retention_cutoff_at`, its immutable
  parameter identities, the first evidence-expiry-eligibility boundary, the
  deterministically derived `retention_invalidation_boundary_at` that is no later
  than either, the required invalidating transition kind and authority, and a
  deletion or expiry fence. The transition and canonical scope-head advance must
  commit before that invalidation boundary, and the current retention head must
  then bind their immutable commit identities and audit sequences. Required
  evidence cannot expire or be deleted until that commit succeeds. At or after
  the invalidation boundary, a missing, late, or failed transition makes current
  status `unavailable` even when the bytes remain. If neither mode can be
  guaranteed, no-automatic-expiry is unavailable. This ADR does not itself
  authorize unbounded retention. Each later transition must carry
  an immutable identity and sequence, predecessor head, from-state and to-state,
  `effective_at`, attributable actor and authority reference, current lifecycle
  policy-head identity, rationale, and a successor decision identity when it
  supersedes the decision.
- The retention compatibility rule must form an append-only, non-forking
  aggregate with an authoritative current head, or be an inseparable child of the
  expiry-policy aggregate with equivalent semantics. Only a current `accepted`,
  effective, unexpired, non-revoked, non-superseded head may support decision
  creation or current evaluation. The decision-time cohort and every
  `evaluated_at` snapshot must resolve it atomically with the expiry-policy and
  evidence-retention heads. A missing or changed head fails closed and cannot
  rebind an existing decision; accepted status requires a new aggregate and
  complete evaluation under the new rule.
- AegisOps must also maintain one authoritative GA-scope aggregate keyed by the
  immutable canonical tuple of an AegisOps-owned stable GA gate-definition
  identity and an AegisOps-owned canonical intended launch-scope identity. A
  per-decision gate-record identifier, decision or evidence identifier, evidence
  revision, attempt identifier, caller-minted scope identifier, or alias is not
  part of that key. Canonical resolution of both identities must be bound inside
  the same compare-and-append boundary; missing, ambiguous, or conflicting
  resolution leaves the attempt pending. The aggregate's append-only,
  non-forking current head must bind sequence and predecessor, the selected
  decision identity and effective state, and the authoritative audit high-water
  mark. Atomic creation of an `accepted` decision must compare the expected
  scope-head predecessor and commit the decision event, its initial per-decision
  head, the decision-time cohort, and the resulting scope head in one
  transaction, fence, or total order. Replacing a current accepted decision must
  also append its authorized superseding transition inside that boundary. A
  concurrent or stale-predecessor attempt cannot commit `accepted`; it remains
  pending and must repeat the complete gate-input and human-authority evaluation.
  At most one decision for the canonical gate and launch scope may be current
  and `accepted`; pending, rejected, superseded, and other historical aggregates
  remain retained evidence. Every later transition that changes the selected
  decision's effective status or successor must advance the scope head inside
  the same authorized transition boundary; a missing or mismatched advance makes
  current status `unavailable` rather than leaving an older acceptance
  selectable.
- GA-decision lifecycle-policy and expiry-policy records must each form an
  append-only, non-forking
  aggregate with an authoritative current-state head. Each head must bind the
  exact immutable separately Accepted policy artifact and version, policy kind
  and scope, effective interval and current status, predecessor and head
  sequence, acceptance and supersession provenance, and audit high-water mark.
  Only a current `accepted`, effective, unexpired, non-revoked, non-superseded,
  non-forked head passes; Accepted metadata on a historical artifact cannot
  substitute.
  Policy-head acceptance, revocation, and supersession must follow a separately
  Accepted repository-governance or ADR-supersession path with attributable
  authority external to the policy being changed. A policy cannot authorize its
  own current-state mutation, and authorship, merge, or administration access is
  insufficient.
- The current GA-decision lifecycle-policy head must define every allowed
  from-state and to-state transition and its required authority. Atomic decision
  creation must bind that current head and the current expiry-policy head. Each
  non-time-driven transition must resolve and bind the current lifecycle-policy
  head and the actor's immutable authority reference at commit and prove both
  effective, unrevoked, and scope-valid inside the same serialization, fencing,
  or total-order boundary used for the transition. Missing, unauthorized,
  self-issued, stale, revoked, superseded, or scope-mismatched policy or authority
  and an illegal transition invalidate the aggregate and block a current claim.
  A policy version valid for an older transition remains historical provenance
  but cannot authorize a new one.
  A later transition cannot enter or return to `accepted`; re-acceptance requires
  complete gate-input and human-authority evaluation in a new immutable
  GA-decision aggregate. Reaching `expires_at` may create the policy-defined
  time-driven invalidating state without inventing a human actor.
- Every authoritative evaluation that decides whether the gate currently
  permits a GA claim, and every API, UI, or generated release-status projection
  that presents such a current claim, must at its own AegisOps-recorded
  `evaluated_at` start from the canonical gate-and-launch-scope head and resolve
  one snapshot-consistent selected decision aggregate containing its event,
  complete transition chain, current head, and authoritative audit high-water
  mark through `evaluated_at`, plus the current lifecycle and expiry-policy
  heads. The scope head and selected decision identity must match, and only a
  unique current `accepted` and unexpired decision head governed by current valid
  policy heads passes. A missing, multiple-current,
  pending, rejected, expired, canceled, superseded, forked, gapped, mismatched,
  stale-predecessor, not resolved through `evaluated_at`, or later-invalidated
  scope, decision, or policy state fails closed. The current-status evaluation
  and projection must share a snapshot, fencing boundary, or authoritative total
  order.
- If an authoritative decision or policy head or audit high-water mark cannot be
  resolved, the evaluation must return an explicit non-accepted `unavailable`
  result and every current-status projection must preserve it; cached accepted
  state and subordinate surfaces cannot substitute or authorize release or
  rollout. A later policy change does not rewrite historical decisions or
  transitions, but until an authorized invalidating or superseding lifecycle
  transition is appended, the obsolete bound policy cannot support current
  status. Restoring an `accepted` current status after that transition requires
  a new decision aggregate and complete gate-input and human-authority
  evaluation; a migration cannot rebind an existing decision to a different
  policy. A static artifact may cite an immutable decision event and its
  `evaluated_at` as historical evidence only and must not present that event as
  current GA status.
  A historical accepted event or earlier snapshot cannot substitute for a
  current evaluation, an arbitrary favorable non-head aggregate cannot be
  selected, and a superseded event can be evaluated only through its separately
  identified successor.
- The same current evaluation must resolve the immutable input-evidence index,
  every required reviewed and redacted artifact or authoritative-record version
  in that index, every claimed capability scope-authority head, and one
  AegisOps-owned evidence-retention and resolvability head. That head must bind
  the complete ordered decision-input evidence-identifier set and count, content
  or record identities, storage-class and location version, custody, provenance,
  review, applicable retention or legal-hold posture, most recent integrity
  result, and audit high-water mark. For no-automatic-expiry it must additionally
  bind the selected mode and current compatibility-rule head. It must bind either
  the current-lifetime integrity-review cadence or the exact or deterministic
  retention cutoff, first expiry-eligibility and effective invalidation
  boundaries, invalidating transition kind and required authority, deletion
  fence, and, once committed, the transition, canonical scope-head advance, and
  audit-sequence identities. The retention head is a separately bound dependency
  rather than a member of the evidence set it enumerates. The evaluation must
  retrieve and verify the exact bytes
  or authoritative versions and their digests inside the same snapshot, fence,
  or total order through `evaluated_at`. Missing, unreadable, corrupt, partial,
  mismatched, expired-without-authority, or unresolved evidence returns
  `unavailable`; a hash, mutable URL, cache, or subordinate surface cannot stand
  in for retrievable evidence. Archived evidence is allowed, but current status
  remains `unavailable` while retrieval or verification is incomplete. Recovery
  of the exact evidence permits a new current evaluation when every other head
  remains valid; it does not rewrite the historical decision.
- In `pre-cutoff-invalidation` mode, an evaluation before
  `retention_invalidation_boundary_at` may pass without a completed invalidating
  transition only when the current compatibility head, bound cutoff, first
  expiry-eligibility boundary, required transition authority, active deletion
  fence, and exact evidence resolvability all pass. At or after the invalidation
  boundary, the evaluation must prove that the required invalidating transition
  and canonical scope-head advance committed before that boundary and before any
  evidence expiry or deletion audit sequence. Absent, late, failed,
  authority-mismatched, or scope-head-mismatched commit evidence returns
  `unavailable` even if every byte is still retrievable. A transition committed
  early makes the selected decision non-current according to its new lifecycle
  and scope heads; it cannot leave an accepted projection active. Before that
  commit, the deletion fence must reject expiry or deletion. A revoked,
  superseded, mode-mismatched, or cutoff-mismatched compatibility-rule head also
  fails closed.
- Only exact reviewed-redacted, repository-owned, or AegisOps-owned evidence in
  the decision index must remain deterministically retrievable while that
  decision is current. This requirement does not retain forbidden source values,
  require hot storage, create an automatic legal hold, or establish indefinite
  retention. After the decision is no longer current, the separately Accepted
  retention and legal-hold policy governs disposition while preserving required
  historical traceability.
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
- The immutable organizational appointment, charter, or equivalent reference is
  provenance for the separately accepted AegisOps root decision; its source
  bytes are not required to participate in an AegisOps database transaction.
  The reference must be content- or version-bound and resolvable, and its
  effective, revoked, and superseded posture must be represented by an
  AegisOps-owned root-governance state head before a GA decision is attempted.
- An `accepted` GA decision event may be created only when the mutable
  root-governance state, assignment and delegation chain, current scope, expiry,
  revocation, and supersession heads share the AegisOps serialization, fencing,
  or authoritative total-order boundary through atomic decision creation. The
  event must bind the immutable root-provenance identity, root-governance head,
  resolved authority-chain identity, and monotonic audit high-water mark. If the
  external provenance cannot be immutably versioned, its status cannot be
  reconciled into that AegisOps authority state through `decision_at`, or no
  authority change effective at or before `decision_at` can be excluded, the
  gate remains pending; a post-hoc check cannot retroactively validate an
  accepted event. Any detected change requires a new chain snapshot, resolution,
  and decision attempt. A later revocation remains historical state and affects
  current GA status only through a separately authorized GA lifecycle
  transition.
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
- routine cadence-driven PostgreSQL-aware backup and required
  configuration-backup evidence for every materially distinct deployment class,
  including completed creation and integrity results, logically separate
  custody and retention ownership, and accountable review at the applicable
  Accepted deployment-profile cadence,
- a profile-cadence operator-health and platform-hygiene review stream for every
  class, including every applicable readiness, queue, degraded-state,
  certificate, storage-growth, backup-drift, restore-readiness, and capacity
  obligation,
- controlled component-interruption, application-aware clean-target restore of
  an integrity-passed backup from that routine path, and recovery evidence with
  declared recovery targets,
- the current immutable supported-upgrade-path exact set and exact-version
  upgrade and rollback rehearsal evidence for every compatible path claimed by
  the launch scope, with post-operation smoke and authoritative-record-chain
  checks,
- monitoring, diagnostic, support-bundle, and redaction evidence,
- a current credential-lifecycle and custody snapshot reconciling every in-scope
  credential family, due or triggered rotation, and break-glass event without
  retaining secret values, and
- a current immutable, snapshot-consistent inventory of the authoritative
  AegisOps `known_limitation_ownership` record set, or an Accepted successor,
  plus reconciliation of every operability limitation with its impact, owner,
  disposition, decision date, and follow-up date.

The routine-backup, operator-health, and credential-lifecycle streams use a
two-stage review boundary. Before the GA decision attempt, each stream must
materialize an immutable AegisOps-recorded `evidence_cutoff_at`, audit high-water
mark and cutoff audit sequence, and complete snapshot through that cutoff. It
must then receive an immutable, detached, independent `accepted` aggregate-review
attestation that directly binds the exact snapshot identity, cutoff, high-water
mark, and ordered set and count, and carries its own AegisOps-assigned review time
and audit sequence. Chronology must prove both
`evidence_cutoff_at <= aggregate_reviewed_at <= decision_at` and
`cutoff_high_water < aggregate_review_sequence < decision_sequence`; a
caller-supplied time or same-time wrong sequence cannot substitute.

The detached attestation is stored outside the operational evidence aggregates
and cannot change a finding, disposition, obligation, or source record. Its exact
identity and the exact immutable decision-attempt bookkeeping identity bound to
the cohort are the only expected post-cutoff records excluded from zero-delta
comparison. During atomic decision creation, the authoritative operational
evidence heads and generated-obligation sets must prove that no other in-scope
record, newly due obligation, pre-existing open obligation whose deadline or
grace became due, or state transition was omitted in
`(evidence_cutoff_at, decision_at]`. A review that changes an operational record
is not an allowed attestation-only delta. Any unexpected delta leaves the attempt
pending and requires a new cutoff, snapshot, reconciliation, and human review
outside the transaction or fence; the commit boundary must not wait for a human.
The reviewed window and that zero-delta proof together make coverage current
through `decision_at`.

For each deployment class, routine-backup coverage must be current and gap-free:
one contiguous reviewed window ending at `evidence_cutoff_at` and spanning at
least one complete applicable Accepted profile review interval. When the profile
uses discrete calendar or business intervals, the window must include the
immediately preceding completed interval plus the current partial interval
through that cutoff, or the current interval when the cutoff is its closing
boundary. An operator-selected older interval combined with recent evidence
cannot satisfy the gate, and the zero-delta reconciliation above must bridge the
cutoff to `decision_at`.

The evidence must bind the immutable class and environment records, the
supported backup-path identity, and the complete non-forking schedule and
cadence lifecycle across the coverage window. That lifecycle must identify every
immutable Accepted schedule version, its status and effective subinterval,
transition boundary, predecessor, and approval or supersession provenance, plus
the current `accepted`, effective, unexpired, non-revoked, non-superseded head at
`decision_at`. Due slots and review deadlines must be generated under the
version effective for each subinterval; a schedule change cannot reset the
coverage start or hide an earlier miss. A missing, overlapping, gapped,
retroactive, or unaccepted schedule interval blocks GA.

Each cadence version must establish the time zone or business calendar,
interval boundaries and cutoff inclusion, due-slot generation, any allowed
lateness or grace, review deadline, and configuration-change trigger and
ordering; an implementation or operator cannot invent a boundary or grace that
closes a gap.

Each cadence version must also bind the immutable governing Accepted deployment
profile and parameter identities effective for the same subinterval and emit a
machine-verifiable no-weaker comparison. Across that subinterval, every
profile-required backup slot, review, and configuration-change trigger must map
to a schedule obligation with no later final deadline, including grace, and no
narrower protected-state, integrity, custody, retention, or review obligation.
Grace is permitted only up to a maximum explicitly authorized by the governing
profile. Missing, ambiguous, incomparable, omitted, later, less-frequent, or
otherwise weaker obligations block GA; generic schedule approval cannot waive
the profile. Any weakening requires an immutable separately Accepted ADR, or a
requirements-baseline revision approved through that ADR process, that identifies
the exact deviation, deployment class and launch scope, effective interval, and
replacement profile identity. Such a deviation cannot apply retroactively,
excuse an earlier miss, or widen the launch scope.

The evidence must include a snapshot-consistent inventory of the authoritative
backup-attempt, reviewed-configuration-change, and accountable-review records
continuously from `coverage_start` through `evidence_cutoff_at`, with its as-of
boundary, ordered record-identifier sets and counts, and audit high-water mark.
The manifest set must equal every scheduled slot, relevant configuration change,
review, and every attempt regardless of lifecycle state whose authoritative
trigger or effective time falls in that window, whose lifecycle, deadline, or
grace overlaps it, or that remains open at the cutoff, including pending,
in-progress, completed, failed, canceled, abandoned, unknown, and unscheduled
attempts.
Unscheduled attempts remain visible but do not satisfy a due slot. A due slot is
satisfied only when its supported-path attempt completes by the slot deadline,
passes integrity, and satisfies the required accountable accepted review by the
applicable Accepted review deadline.
Each slot must carry an immutable slot identity and Accepted eligibility window,
and the satisfying attempt must directly bind that identity and have its
authoritative trigger within that window. One attempt can satisfy only one slot
unless the exact Accepted cadence version defines a deterministic reuse rule for
the named slots that does not weaken backup frequency, protected-state coverage,
integrity, custody, or review requirements.

Each backup entry must bind its immutable backup and manifest identities,
trigger and completion times, PostgreSQL-aware or configuration state set,
creation and integrity outcomes, source revision and configuration identity,
separate backup target, custody and retention owner, and accountable review
outcome. The latest successful backup and review must remain inside the Accepted
profile's own cadence at `decision_at`.

Every due slot and required review whose applicable Accepted deadline, including
any Accepted grace, is at or before `decision_at` must satisfy the completion,
integrity, and review rule above. An unsatisfied or late slot or review blocks GA;
completion, integrity success, or review acceptance after its deadline cannot
retroactively satisfy it or be rebound to a later slot. Every pending,
in-progress, failed, canceled, abandoned, unknown, and retried attempt remains in
the exact set and failed-path evidence. A non-completing attempt does not by
itself block GA when an eligible retry bound to the same immutable slot completes,
passes integrity, and receives its accepted review within the original deadline
and grace, and the failed path has an accepted cleanup and disposition with no
unresolved blocker or non-clean state. An unsatisfied slot, late or cross-slot
retry, concealed failure, unresolved failure disposition, or incomplete cleanup
blocks GA. Custody or retention mismatch, a required configuration change
without its backup, a missed or rejected review, discontinuous high-water
progression or coverage, or incomplete inventory or exact-set reconciliation
also blocks GA. The clean-target restore must consume the exact integrity-passed
backup produced and retained by that class's compliant routine stream. A
manually prepared or one-off backup, historical-window and recent-success splice,
hypervisor snapshot, manifest alone, ad-hoc review, or backup from another class
cannot substitute. Backup-specific cross-class reuse is allowed only when a
separately Accepted rule covers the backup mechanism, protected state set,
storage and custody boundary, and configuration; generic environment equivalence
is insufficient. These records remain subordinate operability evidence and do
not establish a public recovery objective, infinite history, or an enterprise
scheduling requirement.

For every deployment class, routine operator-health and platform-hygiene
coverage must use a current, gap-free reviewed window ending at
`evidence_cutoff_at` and spanning at least the longest applicable Accepted
profile review interval. A discrete cadence must include the immediately
preceding completed interval and the current partial interval through that
cutoff, or the current interval when the cutoff is at its closing boundary. The
zero-delta reconciliation above must bridge the cutoff to `decision_at`. The
stream must bind the complete non-forking
review-schedule lifecycle. Every schedule version must bind the governing
Accepted profile and parameter identities effective for the same subinterval and
must emit a machine-verifiable no-weaker obligation-set comparison using the same
boundary, grace, change-control, and separately Accepted deviation rules as the
backup stream. A mid-window profile or schedule change cannot reset coverage or
hide an earlier duty.

The manifest must reconcile a snapshot-consistent exact set of every generated
due-review slot, review attempt, finding, escalation, limitation, and follow-up
whose trigger or effective time falls in that window, whose lifecycle overlaps
the window, or that remains open at `evidence_cutoff_at`. Each review must bind its
immutable slot, class and environment, applicable readiness and queue state,
degraded-state markers, and the profile-required certificate, storage-growth,
backup-drift, restore-readiness, capacity, and other platform-hygiene dimensions,
plus observed result, accountable operator, outcome, and review time. Applicable
obligations come only from the governing Accepted health, profile, and runbook
parameters; the operability exercise matrix cannot waive a profile-required
health duty. A backup-drift review must reference the routine-backup stream but
cannot replace it.

Every due slot is satisfied only by `accepted` or `accepted-with-follow-up` review
by its Accepted deadline. A rejected or incomplete attempt remains in the exact
set but does not by itself block GA when an eligible re-review bound to the same
slot is accepted within the original deadline and every finding has an accepted
disposition with no unresolved blocker. The complete window and exact set must
receive one independent `accepted` aggregate review bound to their immutable
identities; this does not require a second operator for each routine review. A
missing or late slot, late or cross-slot re-review, weaker or one-off-only review,
carried-open escalation or blocker, missing owned follow-up, or incomplete
exact-set reconciliation blocks GA. One fresh monitoring or diagnostic execution
cannot substitute for the continuous profile-cadence stream. These records are
subordinate operability evidence and do not create a new cadence, scheduler
product, public SLA, or 24x7 staffing commitment.

For every deployment class, the current launch-operability requirements head
must bind a complete, ordered, immutable `supported_upgrade_path` exact set for
the intended launch scope. Each claimed compatible direct path must have its own
immutable path identity and bind the exact source and gate-target release,
bundle, artifact, and configuration identities; release channel, deployment
profile, and class; compatibility posture; migration or schema identity;
required preflight and post-operation checks; backup and rollback mechanism; and
exact rollback target and immutable required rollback-evidence schema and
success-criteria identities, including routine-stream eligibility, integrity,
accepted review, custody, and retention criteria for the rollback checkpoint.
The set must record its count and approval provenance. Phase 65.3 packaging
manifests may supply subordinate structure and input, but cannot establish the
supported set or confer GA authority.

Each claimed compatible sequence must bind one immutable sequence identity and
an ordered list of immutable hop identities in the pre-run requirements set.
Every hop definition must bind its exact source and target releases, artifacts,
configurations, migration or schema identity, required success-criteria and
evidence-schema identities, and required rollback checkpoint, exact target,
routine-stream eligibility, integrity, accepted review, custody, and retention
criteria. The first source and final target must equal the sequence endpoints,
and the final target must equal the gate target.

The post-run manifest and immutable decision input index must bind each hop's
observed input and resulting state, configuration, and schema digests and its
produced upgrade, checkpoint, and rollback outcome evidence identities. They
must prove that every prior target and observed output exactly match the next
source and observed input and that every required checkpoint and rollback target
succeeded across one continuous environment and state lineage. A separately
Accepted sequence-equivalence rule may substitute only when it binds the exact
predecessor output and successor input identities and does not weaken path,
class, state, or configuration coverage. Skipped, reordered, independently
executed, reset, reinstalled, state-discontinuous, or wrong-rollback-target hops
cannot satisfy a sequence.

The manifest's claimed compatible path identifiers must exactly equal that
supported set and map to successful exact-version upgrade and rollback
executions bound to the same path-specific pre-run target, continuous run
lineage, class, environment, gate revision, and predeclared criteria. Missing,
extra, floating, arbitrary, stale, superseded, incompatible, mismatched, failed,
partial, or unexecuted claimed paths block GA.
The post-run manifest and immutable decision input index, not the pre-run
requirements head, must bind the produced upgrade and rollback outcome evidence
identities.
Incompatible or unsupported cases remain explicit owned limitations and need
not be executed, and no unclaimed historical version pair or Cartesian product
is required. This evidence does not establish silent or automatic upgrade,
automatic rollback, zero-downtime behavior, a public SLA, or a fleet-wide
upgrade capability.

The limitation snapshot must bind the gate identifier and intended launch scope,
its as-of audit or transaction boundary, the scope and applicability predicate,
an immutable content or state identity, the complete ordered record-identifier
set, and its count. The manifest limitation identifiers must exactly equal every
in-scope, non-closed record in that snapshot. Every limitation surfaced by an
indexed journey, execution, failed path, owner review, or environment-difference
disposition must be registered in and reconcile to the same snapshot before the
decision. A missing, extra, unregistered, scope-ambiguous, mismatched, or
post-snapshot item blocks acceptance.

When that reconciled snapshot contains no blocking record, the manifest must
carry an attributable independent result
`reviewed-no-known-blocking-limitation` bound to the gate identifier, intended
launch scope, evidence revision, immutable snapshot identity, and its own
`reviewed_at`. The immutable decision input index must bind that review identity,
and chronology must prove `snapshot_as_of <= reviewed_at <= decision_at`.

At decision time, either the snapshot transaction or read boundary must remain
held through atomic decision creation, or authoritative registry audit or
high-water-mark reconciliation must prove that no in-scope create, update, or
lifecycle transition occurred from `snapshot_as_of` through `decision_at`. Any
such change requires a new snapshot, exact-set reconciliation, and independent
review before a decision. An empty list, omitted review, or caller assertion is
`not-reviewed` and blocks acceptance. This completeness claim is limited to the
declared launch scope and authoritative record family; it does not claim
knowledge of unknown limitations outside those bounds.

Each indexed execution record must name its run identifier, deployment-class
identifier, immutable environment-record reference, execution start and
completion times, operator, observed result, artifact digest, owner, and owner
review time. It must also reference an immutable target record with its content
identity, declaration time, applicable immutable launch-operability-requirements
identity, and AegisOps append-only audit-sequence reference or equivalent
independently timestamped external attestation. That independent record must
establish the target before the execution's authoritative start time. A
caller-supplied timestamp, Git author or committer date, or assertion created
only in post-run output does not prove predeclaration. A plan, dry run,
service-health result, CI result, or verifier result cannot by itself satisfy an
executed evidence reference.

Before a direct path or sequence begins, one immutable path-target envelope must
bind the current supported-upgrade-path exact-set and selected path identities,
the gate revision, deployment class and environment, exact source and gate
target, migration or schema, success-criteria and evidence-schema identities,
and every predeclared rollback checkpoint and exact target. For a sequence it
must also bind the immutable ordered hop list. Independent audit ordering must
prove that this envelope existed before the direct-path execution or first hop
started. It contains no produced outcome or checkpoint identity.

Before a direct-path execution or each sequence hop starts, a separate immutable
execution-target record must bind that path-target envelope, the selected path
and hop where applicable, and an exact eligible backup and manifest from the
same class's compliant routine stream or profile-required pre-change
configuration-backup path. The bound backup must already have completed, passed
integrity, received an accepted review, and identify its protected state,
custody, and retention. At `execution_target_declared_at` it must be the latest
eligible reviewed success inside the applicable Accepted cadence, or the exact
profile-required pre-change checkpoint produced after the last material source
change. Its immutable source revision, configuration, state, and schema digests
must match the path or hop's observed source, and its protected-state set must be
equal to or stronger than every mutable database, configuration, and schema
element the path can change. A later sequence checkpoint may be produced by the
prior hop, but its immutable identity, protected state, and source digests must
match that hop's observed output and must receive the same integrity, review,
custody, and retention results before the next hop's target is declared and the
next hop starts. A material source change after checkpoint selection invalidates
that target. Every selected checkpoint must remain retained, resolvable, and
custody-valid through `decision_at`; it need not remain the latest routine backup
after the rehearsal.

Every claimed path requires its own path-target envelope and continuous run
lineage. Each sequence hop has its own execution-target record while sharing the
same envelope, path, class, environment, gate revision, and continuous lineage.
A run, hop, result, manually prepared or one-off snapshot, uncustodied or
unreviewed backup, or another class's checkpoint cannot be assigned after
execution, rebound to another path, imported from another revision, or reused
across paths even when endpoint versions match. Produced outcome identities
remain post-run evidence and are not part of the path-target envelope or any
earlier execution target.

For every deployment class, the gate must resolve before target declaration an
immutable, independently accepted `launch_operability_requirements` record. It
must be either a separately Accepted ADR or a version-controlled parameter
record produced under an Accepted launch-requirements contract. The record must
bind the intended launch scope, deployment class, gate revision, and applicable
Accepted deployment profile or requirements-baseline envelope. It must also
bind an attributable `accepted` approval event and immutable authority
provenance that the source contract authorizes for that scope and class; the
approver must be distinct from the requirements author, target author, and
exercise producer.

The requirements records for each launch-scope and deployment-class pair must
form an append-only, non-forking lifecycle aggregate with an authoritative
current-state head. At `target_declared_at`, the target must bind the current
`accepted`, unexpired, non-revoked, non-superseded head identity and audit
high-water mark. A missing, forked, gapped, stale, historical-only, or otherwise
non-current head blocks target declaration. Any head change through
`decision_at` invalidates the target and execution and requires a new target and
rerun; a historical threshold or post-hoc rebinding cannot substitute.

The current requirements head must also bind a complete, ordered immutable
required-component exact set and count derived from the Accepted launch scope
and deployment profile. Each entry identifies the canonical component, its
in-scope and enabled posture, required-or-optional classification, state and
persistence posture, every applicable interruption, recovery, and restore
family, and the immutable
procedure and criteria identities. The manifest must reconcile its exercise and
result identifiers exactly to every applicable in-scope required or enabled
entry. One execution may cover multiple components only when it records each
component's state and result separately. An in-scope persistent component that
is required or enabled cannot lose its restore
procedure or required restore exercise through disposition; only a genuine
family-level non-applicability under an Accepted rule may be excluded. A missing
component, cherry-picked subset, unregistered persistent state, failed or
unimplemented exercise labeled not applicable, or component-set change after
target declaration blocks GA and requires a new target and affected rerun.
Components such as Wazuh or Shuffle are required only when the Accepted launch
scope includes them.

The same head must bind a complete immutable applicability matrix for that
deployment class across every mandatory exercise family, applicable component,
upgrade path or claimed capability, and target dimension. Every cell is either
`required` with immutable criteria, units, direction, and threshold, or
`not_applicable` with an immutable family-specific rationale and provenance
accepted as part of that current matrix head. An external exception is allowed
only when the cell binds that separately Accepted rule identity. A dimension is
required until such a rationale exists. A missing cell, producer- or
operator-selected `not_applicable`, incomparable value, or post-hoc matrix change
blocks GA. Each target must cite the exact matrix and cells used.

The requirements record must define machine-comparable minimum validation
workload, duration, concurrency or data volume, throughput, and resource
headroom and maximum latency, error rate, and recovery time, with units and
comparison direction. A `not_applicable` cell is permitted when the Accepted
family-specific matrix proves that the dimension has no meaning for that exact
exercise family, component, path, or capability, or when it is genuinely outside
an optional capability in a narrowed launch scope. The matrix head's attributable
approval provenance governs those cells; a producer assertion or separate
post-hoc exemption does not. A `not_applicable` cell cannot
remove the accepted workload envelope, duration, concurrency or data-volume,
throughput, latency, error-rate, or resource-headroom comparisons from mandatory
capacity validation. It cannot remove a finite maximum recovery-time threshold,
record-chain and clean-state criteria, or an applicable Accepted recovery-point
or data-loss criterion from recovery or restore of required components. Nor can
it waive the path-specific upgrade and rollback criteria or any other mandatory
family's predeclared pass criteria merely because a numeric dimension is
inapplicable. The matrix prevents fabricated measurements for genuinely
irrelevant dimensions without weakening a mandatory exercise family.

Each execution target must cite the exact requirements, component-set, and
applicability-matrix identities and be equal to or stricter than every required
threshold. A missing or unauthorized
requirement or approval provenance, unsupported exemption, omitted applicable
dimension, incomparable unit, caller-selected benchmark without that binding,
or weaker or vacuous target blocks GA. A stricter target may provide stronger
evidence but cannot widen the authorized launch scope. These are internal GA
acceptance thresholds; they do not establish a public SLA, enterprise-sizing
promise, or 24x7 support commitment. If an applicable threshold has not yet been
separately accepted, GA remains blocked rather than allowing the exercise
producer to invent it.

The exercises must run in at least one production-like environment for every
materially distinct deployment class in the intended launch scope. Each
environment record must bind the current immutable Accepted deployment-profile
and environment-criteria identities and compare the supported operating system
and architecture, deployment profile and topology, release image and
configuration digests, proxy, TLS, and secret boundary, persistent and
backup-separated storage, resource envelope, and in-scope Wazuh and Shuffle
routes. Each dimension must record the criterion, expected predicate or value,
observed value or digest, accepted exact, set, minimum, maximum, or tolerance
comparison mode, and result.

A missing, unmeasured, incomparable, out-of-tolerance, or weakening result
blocks the class. A difference is non-blocking only when its exact Accepted
criterion permits it and the comparison proves that it does not weaken security
or authority, mask minimum-resource capacity, add an unclaimed dependency or
capability, or change required journey coverage. A producer disposition alone
cannot establish equivalence, and equivalence cannot widen launch scope. For
each declared class, the manifest must contain the complete mandatory exercise
set, and an execution counts only for the class and environment record to which
it is immutably bound.

For every deployment class, credential-lifecycle evidence must use a current,
gap-free reviewed window with an immutable `coverage_start`, ending at
`evidence_cutoff_at`, and spanning at least the applicable Accepted
credential-lifecycle review interval. Its complete
non-forking policy and cadence lifecycle must bind every immutable Accepted
version, status, effective subinterval, predecessor, and approval or supersession
provenance, plus the current `accepted`, effective, unexpired, non-revoked,
non-superseded head at `decision_at`. Each version must bind the authentication
and deployment-profile criteria effective for the same subinterval and prove a
machine-verifiable no-weaker comparison of ownership, bounded consumer and
access scope, delivery, custody, cadence, and triggers. A policy change cannot
reset the coverage start, retroactively excuse a miss, or hide an earlier event;
the common zero-delta reconciliation must bridge the cutoff to `decision_at`.

The current launch-operability requirements head and manifest must bind a
complete, ordered immutable credential-family exact set and count derived from
the Accepted launch scope, authentication baseline, and deployment profile. Each
family entry must identify its accountable owner, bounded consumers and scope,
delivery and custody references, governing current Accepted rotation policy and
cadence, scheduled, emergency, ownership-change, and scope-change triggers, the
complete ordered event set, count, and outcomes of every rotation whose trigger
or effective time falls in the coverage window, whose lifecycle, deadline, or
grace overlaps it, or that remains open at `evidence_cutoff_at`, the next due
boundary, and the authoritative as-of audit high-water mark. When the governing
criteria require primary and backup or two-person custody, the attributable
custodian identities must be distinct. The manifest must reconcile an
AegisOps-owned current lifecycle and custody head for every family; a raw
credential, secret, certificate key, or authorization value must never enter the
evidence index.

The snapshot must also reconcile the ordered break-glass event set and count for
every event triggered in the window, overlapping it, or still open at
`evidence_cutoff_at`, including an explicit reviewed zero-event result when none
occurred. Every used break-glass credential must bind its trigger, bounded use window, affected
credential families and scope, primary and backup custodians where required,
its invalidation or rotation, required reload or restart, readiness and refusal
checks, follow-up owner, independently accepted review, and return-to-normal
closeout. A due or triggered rotation with no successful
reviewed outcome, missing owner or custody, stale or widened consumer scope,
unclosed break-glass use, or hidden event blocks GA. A future rotation not yet
due under the Accepted policy is not required merely because GA is evaluated;
this proposal does not require universal pre-GA rotation, a vault product,
automatic rotation, or 24x7 staffing.

Exercises must use synthetic or reviewed-redacted inputs. Retained GA evidence
must not contain production secrets, credentials, authorization material,
certificate or key material, raw customer-private data, ticket-private content,
customer identifiers, email addresses, or workstation-local paths. A redaction
assertion does not permit retaining the forbidden value beside it. Direct
production access is neither required nor accepted as a substitute for
production-like evidence.

The operability packet passes only when every mandatory exercise exists, is
non-placeholder, was executed at and is bound directly to the gate evidence
revision, meets its target declared before execution, preserves AegisOps
record-chain and authority invariants, retains failed-path and clean-state
evidence, and leaves no unresolved blocking operability limitation. Missing,
mixed-revision, stale, post-hoc-targeted, failed, or subordinate-authority
evidence blocks GA.

Every review used as an independent GA acceptance review must bind an
attributable reviewer who is distinct from the evidence producer and owner to
the exact immutable evidence identity reviewed, and record `accepted` or
`accepted-with-follow-up`. The latter is allowed only for a non-blocking
follow-up with impact, owner, and due date. Routine source reviews may use the
accountable operator only when the governing Accepted profile permits it; they
remain in the exact set and cannot substitute for the required independent
aggregate or GA review. A missing or rejected independent review, a purported
independent review by the producer or owner, or a mismatched review blocks
acceptance.

### Decision-Time Mutable-State Cohort

GA-scope selection predecessor state; GA-decision lifecycle and expiry-policy
state; journey and operability environment-profile, criteria, equivalence, and
coverage-rule review state; launch-operability requirements with its
required-component exact set, applicability matrix, and supported-upgrade-path
exact set; routine-backup profile or deviation, schedule, path, attempt, change,
custody, retention, evidence-cutoff, and reviewed exact-set state; routine
operator-health schedule, cutoff, review, finding, and follow-up state;
credential-family, lifecycle, rotation, custody, cutoff, and break-glass state;
support and upgrade ownership; the authoritative limitation
registry and dispositions; every claimed capability-scope-authority head; the
evidence-retention and resolvability head; and release-authority root and chain
state form one decision-time mutable-state cohort. Each family must expose an
AegisOps-owned current-state head or immutable snapshot bound to the stable
canonical gate-definition and intended launch-scope identities, the per-decision
gate-record identity where applicable, evidence revision, effective status or
interval, predecessor and current lifecycle identities, review identity and
time, and authoritative audit high-water mark. The decision event must bind one
immutable cohort identity, the expected scope-head predecessor, and the current
policy-head identities; the resulting scope head binds the decision identity.
For no-automatic-expiry, the cohort must also bind the retention compatibility
rule head, selected mode, and integrity-review cadence or deterministic cutoff,
first expiry-eligibility and effective invalidation boundaries, required
transition kind and authority, and deletion fence. A later
pre-cutoff-invalidation transition must atomically bind those original values,
its commit identity and sequence, and the advanced canonical scope head; it
cannot change the mode or cutoff of the existing decision.
The specialized journey chronology, backup and upgrade-path exact sets,
required-component and applicability-matrix reconciliation, limitation exact
set, policy governance, evidence durability, capability-scope authority, and
release-authority-chain requirements remain additive.

Each support and upgrade ownership head must identify the attributable current
owner, covered class and support or upgrade scope, assignment provenance,
effective interval, immutable head identity, and audit sequence, and must be
effective, unrevoked, non-retired, and independently reviewed. A plan, bundle,
ticket, or owner label is subordinate evidence and cannot establish current
ownership. A missing, removed, expired, or superseded owner blocks GA until a
replacement head and independent review enter a new decision attempt.

An `accepted` event may be created only when every cohort head and the event
share one serialization, fencing, or authoritative total-order boundary through
atomic creation. That boundary assigns `decision_at` and its audit sequence at
commit, so the decision cutoff and the mutation order are the same authoritative
boundary. It must prove that no in-scope create, update,
reassignment, removal, expiry, revocation, or supersession effective at or
before `decision_at` was omitted. Any change requires re-resolving the affected
head, renewing its independent review, rebuilding the cohort, and retrying the
decision after the serialization boundary is released; no transaction, fence,
or remote wait may remain open for human review. Unavailable or externally mutable state that cannot first be
reconciled into an AegisOps-owned current head leaves the gate pending; post-hoc
reconciliation cannot validate an accepted event. The maximum-age windows below
are freshness caps, not commit-time grace periods. A later state change does not
rewrite the historical event or its acceptance. A missing, revoked, superseded,
expired, narrowed, or unresolvable current dependency that this ADR requires at
`evaluated_at` immediately makes the current projection `unavailable`; that
fail-closed evaluation does not mutate the decision aggregate. A durable
`expired`, `canceled`, `rejected`, or `superseded` decision-state change must be
recorded through the separately Accepted GA lifecycle policy and an authorized
transition. Recovery of temporarily unavailable exact evidence permits a new
evaluation, but withdrawn policy or capability authority cannot be rebound to
restore an existing decision; accepted status requires the new aggregate and
complete re-evaluation defined above.

### GA Evidence Freshness

All age and ordering checks use the immutable GA decision event's
boundary-assigned `decision_at` and audit sequence. That timestamp is the
authoritative atomic-commit time and cannot be caller-supplied, backdated, or
future-dated. For every target-bound execution, independent records must prove
`target_declared_at < started_at <= completed_at <= owner_review_at <= decision_at`.
Every other reviewed evidence record must prove
`observed_at <= owner_review_at <= decision_at`. These orderings require
AegisOps append-only audit sequencing or an equivalent independently timestamped
attestation. Any source contract's clock-skew tolerance applies only while
verifying its subordinate observation or review evidence; it cannot move
`decision_at`, permit evidence after the decision, or replace commit-time cohort
reconciliation.

The following maximum ages are measured backward from `decision_at`. A maximum
age never overrides a revision mismatch; the required action applies after
either expiry or a mismatch:

| Evidence family                                                                                                                                                          | Maximum age                                                                                                                                                                                                                                                                                                             | Required action after expiry or revision mismatch                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Inherited Phase 66 RC evidence set: Phase 66.7 packet plus Phase 66.8 closeout result or authoritative RC-gate result                                                    | Packet regeneration and independent closeout or gate-result evaluation and focused revalidation must complete within 24 hours.                                                                                                                                                                                          | Regenerate the packet and independently re-evaluate and revalidate the closeout or authoritative gate result at the gate evidence revision; every native observation, review, and decision rule must pass.                                                                                                           |
| Real-user or design-partner GA journey records                                                                                                                           | Each required journey completion and owner review must be no more than 720 hours old.                                                                                                                                                                                                                                   | Repeat each affected journey family for every mapped deployment class at the gate evidence revision with a pre-run declaration envelope, or predeclare and independently accept a new journey-coverage rule before its source journey; review alone cannot refresh it.                                               |
| Routine cadence-driven backup stream                                                                                                                                     | One reviewed gap-free window must end at `evidence_cutoff_at`, span at least one full Accepted profile review interval, and reconcile every due or overlapping item and attempt; zero-delta commit reconciliation must bridge the cutoff to `decision_at`, where the latest success and review remain inside cadence.   | Re-establish and independently review a new complete cutoff window at the gate evidence revision for each affected class; any record or newly due obligation before commit forces a new cutoff. An older-window splice, weaker schedule, one-off backup, verifier rerun, or reattestation cannot refresh the stream. |
| Routine operator-health and platform-hygiene stream                                                                                                                      | One reviewed gap-free window must end at `evidence_cutoff_at`, span the longest applicable Accepted profile review interval, and reconcile every due or overlapping review, finding, escalation, and follow-up; zero-delta commit reconciliation must bridge it to `decision_at`.                                       | Re-establish and independently review the complete cutoff window and resolve every due slot and carried-open finding for the affected class; any delta before commit requires a new cutoff. One fresh diagnostic, verifier rerun, or reattestation cannot refresh a missed interval.                                 |
| Capacity, component-interruption and recovery, clean-target restore, exact-version upgrade and rollback, and any claimed HA, disaster-recovery, or fleet-scale execution | Each execution completion and owner review must be no more than 720 hours old.                                                                                                                                                                                                                                          | Rerun each affected family for every bound deployment class and every affected claimed compatible upgrade path at the gate evidence revision; a verifier rerun or owner reattestation alone cannot refresh it.                                                                                                       |
| Monitoring, diagnostic, support-bundle, and redaction execution                                                                                                          | Each execution completion and owner review must be no more than 24 hours old.                                                                                                                                                                                                                                           | Regenerate the artifacts and rerun the affected checks at the gate evidence revision for every bound deployment class.                                                                                                                                                                                               |
| GA lifecycle and expiry-policy current heads                                                                                                                             | Their current-head snapshots must be no more than 24 hours old and be resolved inside each decision or transition commit cohort; the original accepted approval may be older.                                                                                                                                           | Re-resolve every applicable current head and rebuild the cohort. A mismatch, revocation, expiry, or supersession blocks the decision or transition; an older Accepted policy cannot authorize it.                                                                                                                    |
| Launch-operability requirements, required-component set, applicability matrix, and supported-upgrade-path current head                                                   | Its current-head snapshot and bound child exact sets must be no more than 24 hours old at target declaration and be resolved again inside the decision-time cohort; the original accepted approval may be older.                                                                                                        | Re-resolve the current head and every child set. Any requirement, component, matrix, path, compatibility, migration, or rollback mismatch or lifecycle change requires a new target and affected reruns; older versions cannot rebind execution.                                                                     |
| Credential lifecycle, rotation, custody, and break-glass state                                                                                                           | A reviewed gap-free policy-versioned window must end at `evidence_cutoff_at`; current family-set and custody heads must be no more than 24 hours old, and zero-delta reconciliation must bridge the cutoff to `decision_at`. Rotations remain due under Accepted cadence or triggers rather than a universal GA window. | Re-resolve the complete policy lifecycle, every family and overlapping or open event exact set, and independently review a new cutoff. A policy reset, current-state refresh, or new version cannot excuse a missed event, and a delta before commit forces another review.                                          |
| Journey and operability environment criteria, support and upgrade ownership, limitation disposition, and release-authority state                                         | An immutable state snapshot and accountable review must be no more than 24 hours old, and every authority link must be effective and unrevoked at `decision_at`.                                                                                                                                                        | Re-resolve the authoritative state as an immutable gate-revision snapshot and renew its accountable review or disposition; copying the prior snapshot cannot refresh it.                                                                                                                                             |
| Claimed HA, disaster-recovery, or fleet-scale capability-scope-authority heads                                                                                           | Each current head must be resolved at target declaration, inside the decision-time cohort, and again for current-status evaluation; the underlying approval may be older.                                                                                                                                               | A missing, narrowed, expired, revoked, superseded, or mismatched head invalidates the target and current claim; restoration requires a new decision, not rebinding.                                                                                                                                                  |
| Evidence-retention, resolvability, and retention-compatibility current heads plus immutable decision-input closure                                                       | No cached age is accepted. All current heads and exact evidence must resolve at `decision_at` and every authoritative `evaluated_at`; a no-automatic-expiry decision must retain its compatible current-lifetime or pre-cutoff invalidation posture.                                                                    | Return `unavailable` until the exact reviewed evidence, current rule head, and posture are verified. A historical rule, hash, URL, cache, partial set, post-deletion substitute, or unapproved unbounded-retention assertion cannot refresh or replace them.                                                         |

A material version, topology, configuration, route, environment, journey rule or
criterion, GA-scope head, GA lifecycle or expiry-policy head, accepted profile,
backup or operator-health cadence or deviation, equivalence criterion,
launch-operability requirements, required-component set, applicability matrix,
supported-upgrade-path head, compatibility, migration, rollback target,
credential policy, scope, custody or break-glass state, claimed-capability
scope-authority head, evidence-retention or resolvability state, owner,
limitation, or release-authority change invalidates the affected evidence even
inside its maximum-age window.

The decision-time cohort maximum ages do not replace its serialization boundary
through atomic decision creation. Authoritative current-status evaluations and
projections also have no cache-based grace period: each must re-resolve the
canonical scope and selected-decision heads, lifecycle and expiry-policy heads,
claimed-capability heads, immutable input closure, evidence-retention head, and
their audit high-water marks at its own `evaluated_at`.

Capacity within the declared supported envelope, controlled recovery of
required in-scope components, application-aware restore, and upgrade and
rollback rehearsal are mandatory. Multi-node HA or failover, multi-site
disaster recovery, or fleet-scale capability may enter the intended launch scope
only when a separately Accepted ADR, or requirements-baseline revision approved
through that ADR process, explicitly authorizes the capability and its bounded
supported scope.

For every such claimed capability and canonical launch scope, AegisOps must
maintain an append-only, non-forking capability-scope-authority aggregate with an
authoritative current head. The head must bind the exact current Accepted ADR or
approved baseline version, capability and bounded scope, effective interval and
status, predecessor and sequence, acceptance and supersession provenance, and
audit high-water mark. At target declaration and `decision_at`, only a current
`accepted`, effective, unexpired, non-revoked, non-superseded head passes. The
head is a current representation of the separately Accepted authority source;
it cannot grant scope by itself.

The corresponding exercise is mandatory for every capability authorized and
claimed by the launch scope. Without its current scope-authority head, the
capability remains explicitly unsupported even if an exercise succeeds, with
customer or operator impact, owner, decision date, and follow-up date recorded.
A successful exercise is evidence for an already authorized capability; it
cannot authorize or widen launch scope. A failed or merely unimplemented
exercise cannot be labeled not applicable, and GA claims must remain inside the
resulting authorized launch boundary. A withdrawn, expired, superseded, narrowed,
or scope-mismatched head invalidates the affected target and current claim. It
cannot be rebound to an existing decision; restoration requires a new aggregate
and complete current gate-input and human-authority evaluation. Unclaimed
capabilities require no authority head.

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
packet, diagnostic, and input-state window retains the stricter Phase 66.6 and
66.7 precedent for rapidly changing evidence. Authoritative current GA status is
instead re-resolved for each evaluation or projection without a cache-based
grace period.
Fixed windows and explicit expiry actions prevent each implementation from
choosing its own definition of stale evidence. Requiring an accepted
scope-authority reference also keeps successful technical exercises from
silently expanding the product boundary.
Binding each exercise target to independently accepted launch requirements
prevents a producer from satisfying the gate with a vacuous benchmark. Resolving
both the authority state through decision commit and the decision lifecycle at
each later use closes the corresponding time-of-check gaps without rewriting
historical events. Requiring a compliant routine backup stream prevents a
one-off restore source from standing in for daily operability, while the shared
decision-time mutable-state cohort applies the same commit-boundary rule to
policy, environment, requirements, backup, ownership, limitation, and authority
changes. Assigning `decision_at` inside that boundary and serializing accepted
selection through one canonical gate-and-launch-scope head prevent future-dated
or concurrent favorable decisions from escaping the same reconciliation.
Comparing every backup schedule to its governing profile prevents approval of a
weaker cadence by indirection, and binding every claimed supported upgrade path
to its exact compatibility record and successful rehearsal prevents an
arbitrary version pair from standing in for launch-scope coverage. Predeclared
journey comparisons, complete component and applicability sets, and continuous
health and credential-lifecycle streams prevent class labels, cherry-picked
components, meaningless metrics, or a last-minute check from standing in for
launch operability. A reviewed evidence cutoff plus commit-time zero-delta check
keeps those streams current without holding a transaction open for human review.
Current capability-authority and evidence-resolvability heads prevent superseded
scope or deleted proof from continuing to support a current claim, while the
expiry policy constrains both finite and explicitly non-expiring decisions
without inventing a lifetime in this ADR. Requiring a compatible retention rule
for the latter prevents a nominally permanent decision from depending on
evidence scheduled to disappear.

## 6. Consequences

### Positive Consequences

If approved and implemented:

- Phase 67 results remain bounded and non-production,
- missing GA evidence remains visible as owned prerequisite blockers,
- a later GA decision preserves every accepted Phase 51.3 GA journey and
  metadata requirement and additionally binds immutable evidence identities, an
  explicit current human outcome, a verified authority chain, and meaningful
  launch-operability requirements, and
- documentation and verifiers reject claims that Phase 67 itself accepts GA.

### Negative Consequences

If approved and implemented:

- the existing Phase 51, Phase 65, and Phase 66 contract surfaces require a
  coordinated migration,
- every materially distinct launch class requires a fresh mandatory-operability
  exercise set, compliant routine backup and health intervals, complete
  credential-lifecycle reconciliation, and successful user-journey coverage
  within the fixed family-specific decision windows,
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

This proposal-only pull request changes no runtime, configuration, schema,
deployment, credential, privilege, or persistent state. If this ADR is
Accepted, implementation will add authoritative GA-decision, lifecycle,
gate-and-launch-scope selection, release-authority, evidence-index,
expiry-policy, launch-requirements, required-component, applicability-matrix,
supported-upgrade-path, credential-lifecycle, capability-scope-authority,
limitation-snapshot, evidence-retention, and operability-manifest schemas;
backend authorization and current-status read and write paths; persistent
migrations; and atomic or fenced audit ordering. It must not widen the existing
action-approver or platform-administration roles.

If approved, a separate implementation pull request would update the affected
Phase 51 gate, persona, competitive-gap, authority-boundary, and closeout
documents; Phase 58 upgrade and rollback plans; Phase 65 packaging and upgrade
contracts; Phase 66 supportability and closeout documents; README positioning;
and their focused verifier and adversarial self-test pairs. That implementation
must not be merged before this ADR records approval.

That implementation must also define structured schemas and focused verifier
and adversarial-test pairs for the per-class GA journey-family index and
pre-run declaration envelope, successful criteria, journey-level coverage rule,
and class-environment comparator; immutable evidence index and retention head;
complete inherited RC set; explicit human decision event and lifecycle
aggregate; canonical gate-and-launch-scope aggregate and compare-and-append
selection head; release-authority chain and decision-time serialization
boundary; independently accepted launch-operability requirements with complete
required-component, applicability-matrix, and supported-upgrade-path child sets;
and a per-deployment-class GA operability manifest with routine-backup and
operator-health streams, no-weaker profile-cadence comparators, Accepted
environment criteria, reviewed evidence-cutoff snapshots, detached aggregate
review attestations with strict audit-sequence ordering, and commit-time
operational zero-delta reconciliation, plus credential policy-lifecycle,
rotation, custody, and break-glass snapshots. It must enforce direct
gate-revision execution,
current-requirements-bound pre-run target identity and comparison, distinct
path-target and per-hop execution-target records, one-path run lineage, reviewed
rollback-backup custody, upgrade and rollback outcomes, bound owner-review
outcomes, authoritative limitation-registry snapshot and exact-set
reconciliation, current support and upgrade ownership heads, claimed-capability
scope-authority heads, and the shared mutable-state cohort through the atomic
decision boundary, freshness, scope-first current-head re-evaluation, and
retained-evidence secret hygiene without storing forbidden source values.

The later implementation must also encode the separately Accepted GA-decision
lifecycle and expiry-policy current-head schemas, including finite maximum
lifetime and explicit no-automatic-expiry modes, transition policy and required
transition authorities, serialize each authorized mutation, reject unauthorized
or illegal transitions and accepted-state resurrection, and test a missing or
arbitrarily distant expiry, mode or maximum mismatch, no-automatic-expiry with
neither current-lifetime retention authorization nor pre-retention invalidation,
loss of its periodic integrity review, a missing, late, failed, unauthorized, or
scope-head-mismatched pre-cutoff transition, evidence expiry or deletion before
that commit, bytes-only accepted evaluation at or after the invalidation
boundary, mode or boundary mismatch, and policy or compatibility-rule
revocation, expiry, or supersession between snapshot and decision or transition
commit and at a later `evaluated_at`. Positive coverage must accept a current
decision before the invalidation boundary while its transition is not yet
committed, exact evidence resolves, and the deletion fence remains active; an
early transition must instead produce the resulting non-current state. It
must also test authority revocation between snapshot and commit, later decision
expiry, rejection, cancellation, supersession, transition-chain forks or gaps,
presentation of an older accepted event or policy, attempted migration or
in-place rebinding of an existing decision to a replacement policy head, and a
replacement accepted aggregate that reuses rather than completely re-evaluates
current gate inputs and human authority. It must reject a caller-supplied,
backdated, or future-dated `decision_at`, mutation before a requested future
decision time, concurrent accepted creation or replacement for the same
canonical gate and scope, key-splitting through per-decision gate-record,
evidence, attempt, caller-minted scope, or alias identifiers, ambiguous canonical
identity resolution, stale scope-head predecessors, and selection of a favorable
non-head decision aggregate.

The later implementation must test a post-run journey-coverage declaration or
review acceptance, caller-timestamped ordering, comparison-to-execution
environment swaps, stale or wrong covered-profile criteria, class-label spoof,
missing or weakening journey environment comparison, and post-hoc journey
equivalence. It must test
historical or discontinuous backup windows; missing, omitted, pending,
in-progress, abandoned, unknown, deadline-incomplete, late-completing, or
late-reviewed attempts; pre-slot, duplicate cross-slot, and late-evidence
rebinding; a slot, attempt, or review whose lifecycle, deadline, or grace crosses
`coverage_start`; a new record or newly due pre-existing obligation between
`evidence_cutoff_at` and atomic commit; and both a visible failed attempt followed
by an on-time clean retry and a concealed, late, cross-slot, or incompletely
cleaned failure. It must test
unregistered configuration changes; sparse due slots, shifted boundaries,
oversized grace, delayed review, post-change configuration backup, weaker state
or custody coverage, unapproved or mismatched profile deviations, integrity or
custody failures, one-off restore and rollback sources, and missed routine-backup
or operator-health intervals. Health-stream tests must also cover a mid-window
profile change, a finding opened before the window but still unresolved, an
exercise-matrix attempt to waive a profile duty, and a rejected attempt followed
by an eligible on-time accepted re-review. The decision path must abort and
release its transaction or fence before requesting any renewed human review.
Positive coverage must prove that the exact detached aggregate-review
attestation and decision-attempt records do not invalidate an otherwise
zero-operational-delta commit. Negative coverage must reject a caller time,
same-time wrong audit order, review attestation that does not bind the cutoff
snapshot and high-water mark, any extra post-cutoff review or operational record,
and a review that mutates a finding or disposition without a new cutoff.

The later implementation must additionally reject producer-declared or weakening
environment equivalence; historical launch-requirements heads; component
inventory cherry-picking, enabled in-scope omission, or missing
persistent-component restore; a missing, post-hoc, or producer-selected
applicability cell, an irrelevant numeric dimension forced onto a family, or a
core capacity or recovery dimension marked not applicable; missing, extra, floating,
incompatible, failed, or mismatched supported upgrade paths; missing, skipped,
reordered, disconnected, independently executed, reset, reinstalled,
state-discontinuous, hop-target-mismatched, or wrong-rollback-target sequence
hops; same-endpoint path swaps, cross-path run reuse, post-hoc sequence
assignment, or older-revision hop import; an uncustodied, unreviewed, one-off, or
post-hoc rollback checkpoint, a checkpoint stale at execution start or selected
before a later material source change, a source-digest mismatch, or insufficient
protected-state coverage; missing due rotation, hidden trigger, one-person or
otherwise weaker-than-profile custody, weaker cadence, missing primary or backup
custodian, stale custody, or break-glass use without return-to-normal closeout;
credential-policy replacement that resets coverage or hides a boundary-crossing
or carried-open event; withdrawn or narrowed
capability authority; and missing, deleted, unreadable, corrupt, partial, or
archive-unavailable decision evidence. Snapshot-to-commit tests must mutate each
backup, health, environment, requirements, component, matrix, upgrade-path,
credential, capability-authority, evidence-retention, ownership, limitation, and
release-authority head and prove that no accepted decision is written.

## 8. Security Impact

This proposal-only pull request changes no current runtime privileges,
credentials, network exposure, or runtime attack surface. If approved, it would
tighten release-evidence handling by requiring synthetic or reviewed-redacted
inputs and prohibiting retained secret, authorization, customer-private, and
workstation-local material. Implementation would add a separately governed GA
release-authority permission without granting it to any existing role. It would
also introduce an authorized and independent human approval boundary
specifically for GA acceptance. That is a new release-governance policy,
distinct from the accepted baseline's human-approval requirements for
controlled write or destructive action execution. This proposal neither grants
that authority nor designates its root. The intended security benefit is to
prevent subordinate systems, mutable evidence, unauthorized grants, or a named
but inactive approver from conferring GA acceptance. Credential-lifecycle
evidence would record identities, scope, custody, triggers, outcomes, and
break-glass closeout without retaining raw credentials or expanding access.

## 9. Rollback / Exit Strategy

Before approval, the proposal can be marked Rejected with no implementation
rollback because it does not alter the accepted baseline.

After approval and implementation, rollback or supersession is triggered if the
separate-gate model cannot preserve every required Phase 51.3 GA record field,
cannot bind each GA decision to an immutable evidence revision and content,
cannot serialize one authoritative current accepted decision per canonical gate
and launch scope, cannot resolve an authorized release-authority chain, or cannot
prevent Phase 67 prerequisite evidence from conferring GA acceptance. A later
accepted ADR or requirements-baseline change that assigns GA acceptance to a
different phase or authority is also a trigger.

When a post-implementation trigger above applies, replacing this decision
requires a new ADR that records why the boundary is changing and supersedes ADR 0020. The related implementation changes would then be reverted or migrated in
a separate pull request.

The proposal-only change has no runtime or data rollback. After implementation,
immutable decision events, scope-selection and lifecycle transitions, authority,
capability-scope, component, matrix, upgrade-path, credential, cadence,
retention, and evidence snapshots, and audit high-water records are irreversible
historical evidence. Rollback must stop new GA decisions and current-status
publication, append a policy-authorized invalidating or superseding transition
and advance the canonical scope head where applicable, and retain or
schema-migrate those records; it must not delete, rewrite, or rebind them. A
transient archive outage may make current status `unavailable` without erasing
history; permanent evidence loss cannot be repaired by substituting a new
artifact into the old decision.

## 10. Validation

Review of this proposal must confirm:

- consistency with the accepted Phase 51.3 gate contract and ADR 0011,
- explicit separation of prerequisite evidence from GA acceptance,
- attributable real-user or design-partner exercise coverage for every accepted
  Phase 51.3 GA journey family in every mapped deployment class, with immutable
  pre-run criteria and class-environment declaration events proven by independent
  audit ordering, explicit successful outcomes, predeclared independently
  reviewed journey-level coverage rules whose source and covered criteria and
  accepted review all predate the source journey, direct binding between the
  compared and executed environment identities, and preservation of every
  accepted GA metadata field,
- a complete inherited RC set containing the Phase 66.7 packet and independent
  Phase 66.8 closeout result or Accepted-successor authoritative RC-gate result,
  with one-revision binding across that set and every additional GA evidence
  item, fail-closed mixed-snapshot rejection, direct gate-revision execution,
  and rejection of cross-revision execution rebinding,
- resolution of every GA reference to immutable content or authoritative-record
  state rather than a mutable label, path, URL, or bare identifier,
- an explicit immutable human decision event with attributable outcome, time,
  justification, gate, launch-scope, revision, evidence, and authority bindings,
  with `decision_at` assigned at atomic commit rather than supplied or
  future-dated, plus a non-forking per-decision lifecycle aggregate, one
  canonical non-forking gate-and-launch-scope selection head keyed only by stable
  AegisOps-owned gate-definition and launch-scope identities, at most one current
  accepted decision for that key, explicit expiry posture, and
  snapshot-consistent scope-first current-head evaluation for every authoritative
  current-status decision or projection, explicit fail-closed `unavailable`
  behavior, historical-only static references, current effective lifecycle and
  expiry-policy heads governed outside themselves, finite expiry bounded by the
  current policy's maximum lifetime or explicit no-automatic-expiry mode, that
  mode permitted only when a current `accepted`, effective, unrevoked, and
  non-superseded retention-compatibility head preserves the complete inputs for
  the current lifetime or binds an exact or deterministic retention cutoff,
  first expiry-eligibility and effective invalidation boundaries, transition kind
  and authority, and deletion fence requiring the invalidating transition and
  scope-head advance before either source boundary, only separately Accepted and
  authority-validated lifecycle transitions, and no accepted-state resurrection
  or favorable non-head selection,
- re-resolution at every authoritative current-status evaluation of the exact
  immutable decision-input closure and its AegisOps-owned retention and
  resolvability head, with bytes or record versions, custody, provenance, review,
  retention or legal-hold posture, integrity, complete set and count, and audit
  high-water mark verified rather than replaced by a hash, URL, cache, or
  subordinate surface, including atomic re-resolution of the current
  retention-compatibility head, periodic integrity review or pre-retention
  invalidation for a no-automatic-expiry decision, accepted evaluation before
  the invalidation boundary while the fence and evidence remain valid, missing
  or late transition evidence at or after the boundary returning `unavailable`
  even while bytes remain, early transition producing non-current state, and
  deletion forbidden until the transition and scope-head commit,
- proof that the approver held effective, unrevoked GA release authority for the
  recorded launch scope, remained distinct from every evidence producer, and
  inherited that authority through a non-cyclic, non-self-issued,
  non-scope-widening chain to a separately accepted root authorized by the
  AegisOps-owning organization's competent release-governance authority, with
  immutable external provenance separated from AegisOps-owned mutable authority
  state and serialized revocation, scope, expiry, and supersession reconciliation
  through atomic decision creation,
- complete mandatory exercise coverage per deployment class, immutable pre-run
  target declaration with independently recorded chronology, independently
  accepted launch-operability requirements and machine-comparable no-weaker
  target validation, a complete required-component exact set and family-specific
  applicability matrix with Accepted non-applicability provenance, no omission
  of an enabled in-scope component, no fabricated irrelevant metric, and no
  exemption from mandatory family criteria, accepted
  non-self-review bound to each immutable evidence identity, and a complete
  current supported-upgrade-path exact set with every claimed
  compatible direct or sequence path bound to successful exact-source,
  gate-target, migration, and predeclared rollback-schema and success-criteria
  identities through a pre-run path-target envelope and per-hop execution
  targets, each rollback target bound to an eligible reviewed backup and custody
  identity that is current at target declaration, matches the observed source
  digests, and covers every mutable state element, and a continuous gate-revision
  run lineage that cannot be reassigned or reused, including predeclared ordered
  sequence-hop and checkpoint
  definitions plus separately produced immutable per-hop input and output
  digests and upgrade, rollback, checkpoint, and post-operation outcome evidence,
  fixed family-specific freshness and invalidation rules, retained-data hygiene,
  and testable HA, scale, and disaster-recovery dispositions,
- a complete cadence-driven PostgreSQL-aware and configuration-backup stream for
  every deployment class, with authoritative schedule, attempt, and
  configuration-change exact-set reconciliation across a current gap-free window
  ending at a reviewed `evidence_cutoff_at`, including every boundary-crossing or
  open item and a commit-time zero-delta bridge through `decision_at`,
  machine-verifiable comparison proving that every schedule, deadline, grace,
  review, change trigger, state set, and custody obligation is no weaker than its
  governing Accepted profile, integrity, separate custody and retention,
  profile-cadence review, and clean-target restore bound to a backup from that
  stream rather than a historical splice, one-off, or manually prepared source,
  while preserving failed attempts and allowing only an eligible on-time clean
  retry for the same slot,
- a current gap-free operator-health and platform-hygiene stream for every class,
  with each schedule subinterval bound to its governing profile, no-weaker
  cadence, exact due-review and carried-open finding, escalation, and follow-up
  reconciliation through a reviewed cutoff plus zero-delta commit bridge, one
  independent aggregate review, eligible same-slot on-time re-review, and no
  matrix waiver or substitution by one fresh diagnostic,
- machine-verifiable journey and operability environment comparison against
  current immutable Accepted profile criteria, with producer dispositions and
  class labels unable to waive missing, incomparable, out-of-tolerance, or
  weakening dimensions,
- a complete credential-family exact set with current owner, bounded consumer
  scope, delivery and custody proven no weaker than current Accepted
  authentication and profile criteria for every effective policy subinterval,
  distinct custodians where required, a non-forking Accepted rotation-policy
  lifecycle that cannot reset coverage, every due, boundary-crossing, or open
  rotation outcome through the reviewed cutoff and commit bridge, next due
  boundary, and exact break-glass set, bounded use, and return-to-normal closeout,
  without retaining raw secret values,
- a current non-forking launch-requirements head and complete
  required-component, applicability-matrix, and supported-upgrade-path exact sets
  at target declaration and decision, with any lifecycle, component, matrix,
  compatibility, migration, or rollback change requiring a new target and
  affected execution,
- an immutable authoritative limitation-registry snapshot, exact reconciliation
  of every in-scope non-closed and newly surfaced limitation, and independently
  reviewed evidence when no blocking limitation is known, with transaction or
  audit high-water-mark reconciliation through the atomic decision boundary,
- one immutable decision-time mutable-state cohort covering the expected
  canonical scope-head predecessor, lifecycle and expiry policy, journey and
  operability environment state, requirements child sets, backup and health
  cadence, credential lifecycle and custody, support and upgrade ownership,
  limitations, claimed-capability authority, evidence retention and
  compatibility, and release authority, with every current head reconciled
  through atomic decision creation
  and concurrent mutation failing closed, plus reviewed cadence-stream cutoffs
  whose detached aggregate-review identity and strict
  `cutoff < review < decision` audit ordering are bound explicitly, whose
  operational zero-delta comparison excludes only that attestation and exact
  decision-attempt bookkeeping, and whose mismatch aborts and releases the
  boundary before any renewed human review,
- a current append-only, non-forking capability-scope-authority head for every
  claimed HA, multi-site disaster-recovery, or fleet-scale capability, bound to
  an immutable separately Accepted authority source at target declaration,
  decision, and current evaluation, with exercise success prohibited from
  authorizing or widening launch scope and obsolete authority unable to rebind an
  existing decision,
- complete approval metadata when the status changes, and
- no claim that this proposal itself accepts GA or production readiness.

After approval, the implementation pull request must run the affected canonical
verifiers and adversarial self-tests, including the Phase 58.5 upgrade and
rollback verifier and self-test and the Phase 65.3 release-channel and upgrade
manifest verifier and self-test. Claim scanners must compare rendered Markdown
text rather than raw delimiters and cover plain text, emphasis, code spans,
links, and table cells, while retaining negative and prerequisite-only
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
