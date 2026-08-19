# ADR 0020: Phase 67 GA-Prerequisite Boundary

- **Status**: Proposed
- **Activation**: Deferred
- **Activated By**: Pending
- **Effective Date**: Pending
- **Date**: 2026-08-12
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`, `docs/auth-baseline.md`, `docs/control-plane-state-model.md`, `docs/retention-evidence-and-replay-readiness-baseline.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `docs/phase-49-production-rbac-auth-hardening-contract.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-58-5-upgrade-rollback-plan-contract.md`, `docs/phase-65-3-release-channel-upgrade-manifest-contract.md`, `docs/phase-66-6-rc-supportability-proof.md`, `docs/phase-66-7-rc-authority-boundary-proof-pack.md`
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
  observed outcome. Each indexed journey must also bind exactly one immutable
  authoritative owner-review record identity and content version. That review
  must bind the pre-reserved journey-run identity rather than a mutually
  recursive full-record digest, the exact observed outcome, family-specific
  criteria and declaration, class, environment observation and interval proof,
  evidence revision, claimed-participant-set identity, accountable journey owner
  and actual reviewer, and its AegisOps-assigned `reviewed_at`, audit sequence,
  explicit disposition, and any follow-up identity. Only `accepted` or a valid
  non-blocking `accepted-with-follow-up` disposition may pass; the latter must
  satisfy the exact limitation-obligation mapping, deadline, and currentness
  rules below. Missing, mutable, unknown, `not-reviewed`, rejected, journey-,
  outcome-, criteria-, class-, environment-, interval-proof-, participant-set-,
  or revision-mismatched, pre-completion, or post-`decision_at` owner review
  blocks the journey. This accountable owner review is subordinate evidence and
  neither grants GA authority nor replaces any required independent GA evidence
  review. It must use the authoritative `review_outcome` lifecycle schema and
  enter the separate complete owner-review aggregate/head closure even when it is
  not independent. It enters the bounded independent-GA-review closure only when
  the decision separately uses that same record as an independent GA evidence
  review, in which case all independence rules apply. The journey must also bind a non-
  empty exact set of the human participants whose use is claimed as real-user or
  design-partner evidence. At least one such participant must be a direct causal producer of
  the family-specific journey action and must bind the same source-authority
  identity and opaque stable source-subject identifier used by that input's
  producer-attribution record to an immutable qualification record. That record
  must identify `real-user` or `design-partner` qualification, an opaque
  organization or engagement and launch-scope identity, the Accepted persona or
  operating responsibility, source and immutable version, issuer and acceptance
  provenance under a separately Accepted qualification-source policy, effective
  interval, and correction or revocation lifecycle. The actual attributable
  issuer and qualification-acceptance actor must each bind a source-authority
  identity, opaque stable source-subject identifier, principal kind, scope-valid
  authority reference, and immutable provenance; a group, role, title, service
  label, or caller-declared actor without an attributable principal cannot
  substitute. Before the journey starts,
  one immutable declaration
  envelope must bind those criteria, the current Accepted deployment-profile and
  environment-criteria identities, the same immutable deployment-class and
  environment-record identities named by the journey, every claimed
  participant's qualification-record identity, and a machine-verifiable
  comparison for the claimed class across every applicable environment
  dimension defined below.
  The envelope must carry its declaration event identity, AegisOps-recorded
  declaration time, and audit sequence. Independent ordering must prove that the
  criteria, environment comparison, and each qualification record existed and
  were accepted before the journey started, and that every claimed participant
  remained qualified for the entire interval from `started_at` through
  `completed_at`. The envelope and journey record must also bind the same exact
  immutable environment-observation, comparison, source-authority and interval-
  proof identities, their AegisOps-recorded times, audit sequences and high-water
  marks, and the exact material-dimension set, count and digest. That proof must
  use exactly one of these forms:

  - an accepted pre-start snapshot and comparison satisfying
    `observation_sequence <= comparison_sequence <= declaration_sequence < journey_started_sequence`,
    plus authoritative environment-change history or start and completion
    bindings proving that no material compared dimension changed through
    `journey_completed_sequence`; or
  - a declaration that binds the source, criteria and reserved attestation
    identity before `started_at`, followed by a source-authoritative immutable
    attestation that binds the same environment and exact dimensions and covers
    `[started_at, completed_at]` without a gap.

  A caller-supplied or backdated time, post-run point observation, producer-only
  assertion, unreserved, late, short or gapped attestation, environment swap, or
  material mid-run change invalidates the journey and requires a new observation,
  declaration and rerun; an invalid source journey cannot support a journey-
  coverage rule. The common environment-interval-proof schema and chronology may
  be reused, but a generic operability equivalence cannot replace this direct
  journey binding. A non-material or post-completion change does not invalidate
  the historical interval when the exact proof remains valid, and this rule does
  not require continuous telemetry or a particular CMDB or host agent. The
  criteria must incorporate the applicable accepted Phase
  51.3 evidence-family and authority rules. An owner label, authenticated role,
  employment or lab assignment, self-attestation, or post-run qualification
  cannot substitute. Internal assistance remains attributable producer evidence
  but counts as real-user use only when a source-authoritative record proves an
  in-scope operating assignment. Only an explicit `passed` result against every
  criterion counts; a failed, partial, abandoned, placeholder-backed,
  incomparable, weakening, class-label-only, qualification-mismatched, or
  after-the-fact record blocks GA. A normal relationship end after completion
  does not rewrite historical evidence, but a correction or revocation that
  invalidates any part of the execution interval blocks that evidence.
  The separately Accepted qualification-source policy must define allowed
  source authorities, issuer scope, acceptance authority, correction and
  revocation semantics, and the exact prohibited-principal role-selection
  predicate and completeness semantics for each qualification kind and scope,
  without allowing the policy, issuer, participant, or evidence producer to
  self-bootstrap qualification. That policy must form an
  AegisOps-owned append-only, non-forking lifecycle aggregate whose current head
  binds the Accepted policy version, authoritative source family and version,
  exact prohibited-role-selection predicate, completeness and currentness
  semantics, effective interval, status, predecessor, sequence, authority
  provenance, and audit high-water mark. Only a current
  `accepted`, effective, unexpired, non-revoked, non-superseded policy head may
  authorize the pre-run declaration and decision. Each qualification must
  expose an AegisOps-owned append-only, non-forking lifecycle current head, or an
  equivalent current snapshot under that policy, binding its immutable source
  version, predecessor, sequence, status, effective interval, correction and
  revocation state, exact issuer and qualification-acceptance actor source
  subjects and authority provenance, issuer authority, exact governing policy
  aggregate, head and version, and audit high-water mark. The decision must bind
  the exact ordered head set, count, and digest for every claimed participant
  plus one complete ordered qualification-actor-separation mapping set, count,
  and digest. Each member must bind its exact qualification and participant,
  issuer and acceptance-actor source subjects, the decision-bound policy head,
  version, effective interval and prohibited-role-selection predicate, and the
  exact prohibited source-subject set, count, digest, role mapping and immutable
  source proof/version mechanically derived from that predicate for that
  qualification. The qualification set and mapping members must reconcile
  bidirectionally one-to-one; missing, extra, duplicate, substituted, or wrong-
  policy members block acceptance. The claimed participant, every actual
  issuer, every qualification-acceptance actor, and every subject in that
  qualification's exact decision-bound prohibited-principal set must enter the
  same decision-scoped identity-resolution closure. The participant must resolve
  canonically distinct from every issuer, acceptance actor, and prohibited
  principal mapped to that qualification; issuer and acceptance actors need not
  be distinct from each other unless the Accepted policy says so. A group- or
  role-label-only, ambiguous, conflicting, or alias-collapsed mapping or mutable
  or incomplete prohibited-subject source proof also blocks acceptance. The
  initial qualification-source
  policy and its acceptance authority must derive from a separately Accepted
  governance decision and immutable approval provenance outside the
  qualification graph; neither a participant, qualification record, nor that
  graph may bootstrap the policy or its authority.

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
  Every rule used by the decision must belong to an AegisOps-owned append-only,
  non-forking lifecycle aggregate. Its current head binds the stable aggregate
  identity, immutable rule version, declaration and accepted-review identities,
  source journey, family, class and environment, covered class-and-environment
  set, profile and criteria identities, effective interval, status, predecessor,
  sequence, review authority, and audit high-water mark. Only a current
  `accepted`, effective, unexpired, non-revoked, non-superseded head may support
  the decision, which binds the complete ordered used-rule aggregate and head
  set, count, and digest. Direct per-class journeys and unused rules do not enter
  that set.
- Inherited RC evidence is complete only when the immutable Phase 66.7 packet
  and an immutable, independently `accepted` Phase 66.8 closeout result both
  resolve at the gate evidence revision. An immutable authoritative AegisOps
  RC-gate result produced under an Accepted successor contract may replace the
  Phase 66.8 path. Missing, rejected, stale, scope-mismatched, or
  revision-mismatched closeout or gate evidence blocks GA. The Phase 66.7 packet
  alone, closeout prose, verifier output, or issue state cannot substitute. A
  Phase 66.8 closeout result remains subordinate RC evidence and cannot accept
  GA.
- The exact selected Phase 66.7 packet must belong to an AegisOps-owned,
  append-only, non-forking `rc_proof_packet` evidence aggregate with an
  authoritative current head, or an equivalent canonical lifecycle defined by
  an Accepted successor contract. The head must bind the stable aggregate
  identity, exact immutable packet content and version, `repository_revision`,
  `journey_run_id`, complete packet-input closure, set, count and digest,
  effective interval and Evidence state, predecessor and sequence, authorized
  correction, withdrawal, revocation and supersession provenance, transition
  authority, and audit high-water mark. Only a current usable `validated` or
  `linked` state that is effective, unwithdrawn, unrevoked and non-superseded may
  support GA. The selected Phase 66.8 closeout or Accepted-successor RC-gate
  result head must bind that exact packet aggregate, decision-time packet head,
  content version and one-revision mapping, and the GA decision must bind both
  heads and their mapping. A stable packet or result aggregate identity may be
  reserved beforehand, but authoritative audit ordering must prove
  `packet_selected_head_commit_sequence < rc_result_review_and_initial_head_commit_sequence < decision_sequence`.
  The selected packet head cannot be reviewed before its immutable content and
  head exist, and it does not bind a future result; the dependency is one-way
  from the later independently reviewed RC result to the already committed
  packet head. A caller-supplied or backdated sequence, an equal or reversed
  packet/result sequence, a result over a reserved but uncommitted future packet
  head, or a packet materialized after its result blocks GA. At every
  `evaluated_at`, AegisOps must resolve the
  complete packet and selected-result chains and current heads in one snapshot.
  Temporary unreadability may recover only when the same complete valid chains
  resolve. A same-aggregate metadata-only successor may pass only when it
  preserves the exact packet content, revision, input closure, selected result,
  and lifecycle semantics. A material correction, withdrawal, revocation,
  invalidating supersession, fork, gap, cached favorable non-head, replacement
  aggregate, or packet-to-result mismatch returns `unavailable` and requires a
  new packet, independent RC-result evaluation, and GA decision rather than
  in-place rebinding. This lifecycle remains subordinate evidence and grants no
  RC or GA authority.
- The selected Phase 66.8 closeout or Accepted-successor RC-gate result and every
  independent GA evidence-review event explicitly required by this ADR whose
  `accepted` or `accepted-with-follow-up` outcome is used by the decision must
  belong to an AegisOps-owned, append-only, non-forking `review_outcome`
  aggregate with an authoritative current head. This bounded set includes an
  explicitly required independent review of an environment-coverage or cross-
  class-backup-reuse rule when that review outcome supports the decision. It
  does not recursively wrap the
  GA decision event; approval metadata for an ADR, source contract, profile,
  criteria, lifecycle policy, root-governance decision, or other governance
  artifact; or requirements-approval, requirements-separation, producer,
  attribution, ownership, membership, or review-control metadata. Those
  dependencies remain governed by their dedicated current-head rules. Each
  review-outcome head must bind the stable aggregate identity, exact
  immutable result or review event and content version, exact reviewed evidence,
  source contract, gate, launch scope, deployment class and family where
  applicable, evidence revision, reviewer source subject and review authority,
  outcome and follow-up identity, effective interval and status, predecessor and
  sequence, correction, retraction, revocation and supersession provenance, and
  audit high-water mark, including the attributable transition authority
  validated under the separately Accepted review-lifecycle policy bound by the
  aggregate. Only a policy-authorized append may advance the head; a comment,
  ticket or unauthorized retraction cannot mutate current review state. At
  `decision_at`, only a current `accepted` or valid
  `accepted-with-follow-up`, effective, unexpired, unrevoked, non-superseded head
  may pass; the latter remains subject to the limitation and due-date rules
  below. The decision must bind a complete ordered decision-used review-outcome
  aggregate and head set, count, and digest. A historical favorable result,
  immutable bytes alone, or a replacement result cannot be selected or rebound.
- Every subordinate owner review for a decision-used journey or one-time indexed
  operability execution must use the same `review_outcome` aggregate and
  authoritative-head schema even when it is not an independent GA review. The
  decision must bind a separate complete ordered owner-review aggregate/head
  closure, set, count and digest, with a bidirectional one-to-one mapping from
  each exact decision-used run to its selected review. If the same review is also
  selected as an independent GA review, the same aggregate and head enters both
  closures and only the independent use adds the reviewer-independence predicate.
  A canonical routine-stream aggregate that already exposes equivalent
  authoritative review lifecycle/current-head semantics may be referenced
  instead of double-wrapping that review. At `decision_at` and every
  `evaluated_at`, each exact selected review's complete chain and current head
  must resolve as current `accepted` or valid `accepted-with-follow-up`, effective,
  unexpired, unrevoked and non-superseded. A correction, retraction, rejection,
  revocation, expiry, invalidating supersession, fork, gap, run/evidence/outcome/
  follow-up mismatch, cached favorable non-head or replacement-review rebinding
  returns `unavailable`; recovery requires a new valid owner review and GA
  decision, while a rerun is required only when the primary run is invalid or no
  longer fresh. This lifecycle adds neither independent review nor a second
  reviewer.
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
- Every decision-used journey and one-time indexed operability execution must
  belong to an AegisOps-owned append-only, non-forking `primary_run_outcome`
  aggregate with an authoritative current head. The stable aggregate and run
  identity must be reserved before start; the post-completion initial head binds
  the exact immutable record version, declaration or target, family, class,
  environment and interval proof, gate revision, criteria, participant set or
  operator, start and completion sequence, observed outcome or result, artifact
  and produced-evidence identities, status, predecessor and sequence, authorized
  correction, withdrawal, revocation and supersession provenance, and audit
  high-water mark. The run head does not bind its later owner review; the
  decision closure links run to review in the one-way order target or declaration
  -> run outcome -> owner review -> decision. The decision must bind separate
  complete ordered journey-run and one-time-execution aggregate/head closures,
  sets, counts and digests, each reconciled bidirectionally one-to-one with the
  exact journey index or operability manifest and owner-review mapping. A
  canonical routine-stream lifecycle that already provides equivalent primary-
  record correction/current-head semantics is not double-wrapped.
  At `decision_at` and every `evaluated_at`, each exact selected aggregate's
  complete chain and current head must resolve. A same-aggregate successor may
  pass only when it preserves every decision-bound run fact. A result, outcome,
  artifact, interval, target, declaration, participant, operator, criteria,
  environment or revision correction; withdrawal, revocation, invalidating
  supersession, fork, gap, cached favorable non-head, set/count/digest/mapping
  mismatch or replacement-run rebinding returns `unavailable` and requires a new
  run, owner review and GA decision. This rule does not make a one-time exercise
  periodic or rewrite the historical run.
- The complete inherited RC packet and every additional GA evidence reference
  must carry an immutable content identity. Repository-owned artifacts must bind
  to their exact Git object or content digest; authoritative AegisOps records
  must bind to an equivalent tamper-evident record version or snapshot identity.
  This applies to the selected RC-proof-packet lifecycle head and the independent
  RC closeout or authoritative RC-gate result,
  real-user or design-partner journey, qualification, and owner-review records,
  journey and operability environment-evidence lifecycle and governing source-
  policy heads, the
  launch-scope definition and class-set closure, the operability manifest and
  its environment, requirements, approval, target, execution, and owner-review
  records, ownership and limitation records, and release-authority records and
  chain snapshots. The
  gate must resolve and verify each input identity when the decision is made. A
  mutable label, path, URL, or record identifier without immutable snapshot
  binding blocks acceptance.
- Every immutable input-evidence-index entry and every addressable material-
  source or transformation node reachable in that entry's complete provenance
  closure must bind one immutable producer-attribution record to its exact
  content or authoritative-record version. Reachable nodes remain provenance
  members rather than additional evidence-index entries, and a node shared by
  multiple roots is deduplicated by its immutable identity. Each record must be
  the immutable version selected by a stable,
  append-only, non-forking `producer_attribution` aggregate with an authoritative
  current head governed by a separately Accepted attribution-source/currentness
  rule. That rule must itself expose a stable append-only, non-forking
  `producer_attribution_policy` aggregate and current head binding its immutable
  Accepted version, permitted source authorities, completeness and causal-
  provenance semantics, transition authority, effective interval, status,
  predecessor, sequence and audit high-water mark. Each attribution head binds
  the exact governing policy aggregate, head and version as well as the exact
  input identity and version, immutable
  attribution version, status, predecessor and sequence, correction, retraction,
  withdrawal and supersession provenance, source-resolved-through and audit
  high-water marks, governing rule identity and source authority. Only current
  `accepted`, effective, unexpired, unrevoked and non-superseded attribution and
  policy heads may be selected. Each record
  carries a non-empty complete ordered set and count of
  human or machine principals that directly authored, generated, executed,
  collected, selected, supplied, or materially transformed that evidence
  instance and, for each principal, the immutable source-authority identity,
  opaque stable source-subject identifier, instance-specific causal action, and
  source-authoritative commit,
  append, audit, execution, acquisition, or record-creation provenance and
  sequence. An email address, display name, or raw customer identifier cannot
  serve as the retained source-subject identifier. Machine-generated evidence must
  include the executing identity and any attributable human initiator,
  delegator, or material-input selector; a proven autonomous scheduled run may
  be machine-only.
- Derived evidence must bind a complete acyclic provenance closure over every
  material source and instance-specific transformation rather than hiding a
  source producer behind the derived artifact. Owner, operator, reviewer,
  custodian, administrator, submitter, display name, service label,
  caller-supplied `produced_by`, or unverified repository-author fields do not
  substitute for causal provenance. Before decision creation, AegisOps must
  deterministically materialize one immutable producer-closure record bound to
  the input-index identity and revision, exact entry set and count, every
  per-entry attribution identity, the complete ordered root-to-reachable-node
  set and edge mapping, reachable-node set, count and digest, every node-to-
  attribution mapping, the complete ordered input-to-attribution-
  aggregate/current-head and attribution-to-policy-aggregate/head/version
  mapping sets, counts and digests, the source-authoritative decision-scoped
  identity-resolution current-head identity and its immutable source snapshot,
  the complete ordered producer source-authority and source-subject set, count,
  and digest, every decision-time canonical mapping result, the canonical
  producer union, set and count digest, and provenance audit high-water mark.
  Missing, empty,
  ambiguous, alias-conflicting, cyclic, incomplete, extra, stale, changed, or
  input-mismatched attribution blocks acceptance. Producer is causal metadata,
  not a role or authority; a passive owner, reviewer, custodian, tool provider,
  or administrator is not a producer unless it directly creates or materially
  changes the exact evidence instance. Per-entry attribution records and the
  closure record are derived decision-control metadata and separately bound
  dependencies, not evidence-set members that would recursively attribute
  themselves.
  At every `evaluated_at`, the evaluator must deterministically derive one
  complete ordered producer-currentness input set as the union of two separately
  bound exact partitions: every immutable decision-bound root input plus its
  complete reachable material-source and transformation-node set, and every
  exact reviewed-evidence root plus its complete reachable node set for the
  currently consumed review set derived below. Shared nodes are deduplicated by
  immutable identity. The partitions, union, root and node sets, root-to-node
  edge mappings, counts and digests, and each member's provenance as decision-
  bound, currently consumed or both must bind the evaluation; future or
  unconsumed evidence and unrelated provenance nodes are excluded. From
  that exact union the evaluator must resolve each attribution aggregate's
  complete non-forking chain, authoritative current head, governing policy
  aggregate, complete chain and current head, and source high-water mark one-to-
  one in the same current-read boundary. It must then derive a separate current
  decision-input producer closure and per-consumed-review producer slices, each
  with its complete source-subject set, causal and provenance edges, set, count
  and digest, canonicalize those exact current sets with the evaluated-at
  identity head, and recompute the acting-approver, requirements-separation and
  decision-bound review-independence predicates from the decision-input
  partition and each consumed review's independence predicate only from that
  review's exact consumed-review partition. A later review's producers do not
  enter the historical GA producer union or a requirements-separation slice
  merely because that review is currently consumed. The historical producer
  closure remains immutable provenance and is not rebound. A same-aggregate successor may pass only when
  the Accepted rule proves that the exact input, complete producer set, causal
  closure, source authority and semantics are unchanged. Missing, extra,
  duplicate, substituted, forked, gapped, stale, retracted, withdrawn,
  invalidatingly corrected or superseded state; an input, head, set, count,
  digest, causal-edge or provenance mismatch; a newly discovered or omitted
  producer; a cached favorable non-head; or replacement attribution returns
  `unavailable`. Temporary unreadability returns `unavailable` only until the
  same complete attribution and policy chains, heads, mappings and high-water
  marks resolve again. A missing, expired, revoked, superseded or replaced policy head,
  or a policy successor that changes the selected source authority,
  completeness, causal-provenance or transition semantics, has the same effect;
  a future-only or otherwise no-weaker same-policy-aggregate successor may pass
  only when the bound version remains accepted for the exact selected evidence
  and source interval and every completeness, causal-provenance, correction and
  transition semantic applicable to it remains unchanged; it cannot rebind the
  historical policy selection. A material attribution change in the decision-
  input partition, including a shared node that affects that partition, always
  requires a new GA decision, but the same eligible acting approver may make it
  when the rederived decision-input producer closure remains disjoint. A
  different approver is required only for acting-approver overlap; new
  requirements approval, target and affected rerun only when that exact tuple
  predicate or target provenance is invalidated; and a new decision-bound
  independent review only when that review's independence predicate is
  invalidated. A change confined to a currently consumed-review partition does
  not alter the historical decision or cohort: if every reviewed-evidence
  binding and per-review independence predicate still passes, AegisOps may
  rebuild the consumed-review control closure and re-evaluate current status; if
  it creates reviewer overlap or invalidates that evidence binding, a new
  applicable review and recomputed control closure are required, not a new GA
  decision. Attribution correction alone does not otherwise require rerun or
  discard still-current evidence and review.
  Attribution aggregate/head, current producer closure, identity mapping and
  other approval or review-control records remain non-evidence decision-control
  metadata, do not attribute themselves, and their recorder is not a producer of
  the original evidence absent authoritative causal provenance. Unrelated audit
  or catalog updates and monotonic high-water advancement that preserve the exact
  selected attribution remain non-blocking.
- The GA gate record preserves the accepted Phase 51.3 metadata: the real-user
  or design-partner record reference, reviewed environment class, operator or
  design-partner owner, evidence date, gate record identifier, accepted
  limitations, support owner, upgrade owner, and follow-up decision. It
  additionally records the evidence revision, immutable evidence index,
  claimed-participant qualification-record-head-set and complete qualification-
  actor-separation-mapping-set identities, support-ownership and
  upgrade-ownership coverage-closure identities, decision-used journey-coverage
  rule-head-set identity, launch-scope-definition and non-empty launch-eligible-
  subset identities, deployment-profile and environment-criteria dependency-
  closure identity, journey and operability environment-evidence lifecycle-
  closure identities, environment-source-policy dependency-closure identity,
  selected RC-proof-packet aggregate/head and packet-to-result mapping
  identities plus packet-before-result audit-order identity,
  GA-approver-ownership coverage-closure identity,
  requirements-separation-closure-set identity, journey-run and one-time-
  execution primary-outcome-head-set identities, owner-review-head-set identity,
  producer-attribution-head-set, attribution-policy-head-set and producer-
  closure identities, reviewed-at
  relationship-head-set, relationship-policy-dependency-closure and review-
  independence-closure identities, and complete
  decision-used review-outcome aggregate-and-head-set identity.
- The gate record must contain an attributable, immutable human GA decision
  event, not merely an assigned approver identity. The event records an explicit
  outcome and justification or attestation and binds the approver identity and
  authority record to the stable canonical gate-definition identity,
  per-decision gate-record identifier, canonical intended launch-scope identity,
  evidence revision, immutable input-evidence index, journey-run and one-time-
  execution primary-outcome-head sets, owner-review-head set, claimed-
  qualification-head set and complete qualification-actor-separation mapping
  set, producer-
  attribution-head and attribution-policy-head sets and immutable producer-
  closure record, reviewed-at
  relationship-head set, relationship-policy dependency closure and review-
  independence closure, complete decision-used
  review-outcome aggregate and head set, selected RC-proof-packet aggregate and
  head plus packet-to-result mapping and packet-before-result audit order,
  decision-used journey-coverage rule-head set,
  deployment-profile and environment-criteria dependency closure, GA-
  approver-ownership coverage closure, journey and operability environment-
  evidence lifecycle closures, environment-source-policy dependency closure,
  requirements-separation closure set, identity-
  resolution current-head and bound source-snapshot identities,
  the approver's source-authority identity and opaque stable source-subject
  identifier, and the complete ordered acting-approver, selected approver-
  coverage-holder, producer, independent-reviewer, reviewed-evidence-owner, and
  credential-custodian, requirements-approval-actor, qualification-participant,
  qualification-issuer, qualification-acceptance-actor, policy-prohibited-
  qualification-principal, selected root-holder,
  attributable root-governance-approval-actor, and assignment-or-delegation
  issuer and grantee source-subject set, count, and digest. Its
  AegisOps-recorded
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
  long as the decision remains current. It must also bind a stable AegisOps-owned,
  append-only, non-forking decision-input integrity-review aggregate and current
  head. That aggregate must bind the current Accepted compatibility-rule-derived
  cadence and currentness-rule identity, coverage start, deterministic immutable
  slot identities, eligibility windows, deadlines and any grace, the complete
  decision-input set and digest, every verification attempt and result, every
  authoritative review-outcome aggregate and current-head exact set and count,
  the bidirectional slot-to-review-outcome mapping, audit high-water mark, and
  next-due boundary. Each satisfying review must use the `review_outcome`
  lifecycle schema above or an equivalent inseparable child lifecycle whose
  correction, retraction, rejection, revocation, expiry, or supersession must
  advance the integrity-review parent head atomically. The initial head binds an
  empty exact outcome mapping when no slot is due or open; a future review head
  is neither fabricated nor reserved in the decision-time cohort. The
  initial aggregate identity may be reserved beforehand, but its initial head
  must be created in the same atomic decision-time cohort, bind
  `coverage_start = decision_at` using the boundary-assigned authoritative time,
  and derive its first slot and `next_due` from the current Accepted cadence. A
  caller-supplied, future, delayed, replacement, or reset coverage start or first-
  slot anchor is invalid, and no successor may advance that anchor. Each
  satisfying verification and review must directly bind one slot and the complete
  decision-input closure, execute inside that slot's eligibility window, and
  succeed and receive accepted review by its deadline. Stable attempt, result,
  review, or parent-successor identities may be reserved, but authoritative time
  and audit order must prove
  `slot_eligibility_start <= verification_started_at <= result_completed_at < reviewed_at <= slot_review_deadline`
  and
  `result_completed_sequence < review_and_initial_outcome_head_commit_sequence < integrity_parent_successor_sequence <= evaluated_at_read_sequence`.
  The initial accepted review-outcome head must bind an already committed exact
  result, and the later integrity-parent successor must bind that exact outcome
  head and slot mapping. A caller-supplied or backdated time, review of a future
  or reserved-only result, equal or reversed result/review/parent sequence, or
  review-outcome change not reflected by a later parent successor is invalid.
  One result may satisfy only one slot unless the exact Accepted cadence rule defines a deterministic no-
  weaker reuse mapping for named slots. At every `evaluated_at`, AegisOps must
  resolve the same aggregate's complete successor chain and current head and
  reconcile every due, overlapping, or open slot even when the head identity has
  not changed. Each selected review-outcome aggregate's complete chain and
  current head must resolve in the same snapshot as current `accepted`,
  effective, unexpired, unrevoked and non-superseded. A future slot is non-
  blocking. Missing, omitted, forked,
  gapped, late, failed, unreviewed, partial, wrong-input, duplicate, cross-slot,
  weaker, corrected, retracted, rejected, revoked, expired, superseded, cached-
  favorable, outcome-mismatched, or replacement state returns `unavailable`. A
  later successful verification or replacement review cannot retroactively cure
  a missed deadline; current acceptance requires a new complete compliant review
  window and new decision. Temporary unreadability may recover only when the
  same complete valid integrity and outcome chains resolve. These slot reviews
  do not enter the independent-GA review-outcome closure or evaluated-at
  consumed-review control merely because they satisfy integrity cadence, and
  they acquire an independence predicate only when the governing Accepted
  cadence rule explicitly requires one. When it does, every such slot's exact
  review-outcome identity must enter the deterministic evaluated-at currently-
  consumed review set and `consumed_review_control` closure for as long as that
  review supports the current projection. The control closure must bind the
  complete exact origin-edge set, count, and digest from each qualifying
  integrity aggregate, immutable slot, and Accepted cadence-rule version to its
  selected review-outcome identity and reconcile those origins bidirectionally
  with the consumed member set. One review identity may be deduplicated when it
  satisfies multiple explicitly permitted origins, but every origin edge must
  remain present. The same snapshot must bind and re-resolve its exact reviewed
  result and complete producer slice,
  authoritative reviewed-at non-empty owner set and membership proofs, governing
  attribution and relationship policies, current reviewer/owner/producer
  identity mappings, and per-review independence result under all common
  consumed-review rules below. This does not add the future slot review to the
  immutable decision-time independent-review closure or make the control closure
  review itself; a missing, extra, duplicate, wrong-slot, wrong-cadence, or
  mismatched origin edge, stale control evidence, or reviewer-owner/producer
  overlap returns `unavailable`. A `pre-cutoff-invalidation`
  mode must
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
- For each canonical intended launch-scope identity, AegisOps must maintain an
  append-only, non-forking `launch_scope_definition` aggregate with an
  authoritative current-state head. The head must bind the exact immutable
  Accepted scope-definition artifact or authorized parameter source, acceptance
  and authority provenance, effective interval and current status, predecessor
  and sequence, audit high-water mark, and a complete non-empty ordered set,
  count of at least one, and digest of canonical deployment-class identities.
  It must also bind a non-empty ordered launch-eligible class subset, count of at
  least one, and digest. Every member of that subset must belong to the complete
  class set and bind a current immutable Accepted profile version that explicitly
  classifies the deployment shape as eligible for customer deployment or small-
  production operation. A Lab, internal-only, exercise, or training profile
  cannot satisfy this existential requirement, and eligibility cannot be inferred
  from a class label, producer or operator assertion, production-like environment,
  or real-user designation. Such profiles may remain additive classes when at
  least one eligible class is present. Each class entry must bind
  the current Accepted deployment-profile and environment-criteria identities
  that define it. Only a current `accepted`, effective, unexpired, non-revoked,
  non-superseded head may define the launch scope; a producer label, discovered
  environment, issue name, caller alias, or historical profile cannot create or
  widen a class.
- Every deployment-profile or environment-criteria version actually referenced
  by the selected launch scope, journey evidence or coverage rule, operability
  environment, cadence, capacity boundary, approver coverage, or credential-
  custody rule must belong to an AegisOps-owned, append-only, non-forking
  lifecycle aggregate with an authoritative current head. Each head binds the
  exact immutable Accepted version, profile or criteria kind, class and
  environment scope, effective interval and status, predecessor and sequence,
  acceptance, revocation, and supersession provenance, and audit high-water
  mark. The decision must bind one complete ordered profile-and-criteria
  dependency closure containing the exact aggregate, head, version, and usage
  mapping set, count, and digest for only those referenced inputs. At target
  declaration and `decision_at`, every selected head must be current `accepted`,
  effective, unexpired, unrevoked, and non-superseded. An unselected catalog
  profile, unrelated environment instance, or document revision that does not
  change a referenced lifecycle head does not enter this closure.
- At target declaration and decision creation, AegisOps must derive one
  immutable expected pair closure from that exact class set and the canonical
  launch-scope identity. The active `launch_operability_requirements` heads must
  reconcile one-to-one to that expected `(launch scope, deployment class)` set,
  count, and digest. The pair closure must be non-empty, and its count must equal
  the deployment-class count. The journey index must likewise reconcile every required
  family to every class, and the operability manifest and its class streams must
  reconcile exactly to the same class set. Missing, duplicate, extra,
  wrong-scope, alias-split, historical-only, or superseded active pairs or class
  mappings block GA; inactive historical records may remain retained without
  entering the closure. Every pre-run journey envelope and operability target
  must bind the current scope-definition head, class-set and non-empty launch-
  eligible-subset identities, and expected pair-closure identity. A head,
  eligibility, or membership change through `decision_at`
  invalidates the affected targets and requires new declarations and affected
  reruns rather than post-hoc rebinding. This exact set is the declared launch
  scope only; it does not automatically enumerate every catalog profile,
  environment instance, host, tenant, customer, or fleet.
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
  that presents such a current claim, must run in explicit `current` mode. The
  same snapshot, fence, or authoritative total-order boundary that linearizes
  that status read must assign its `evaluated_at`, read sequence, and resolved-
  through audit high-water marks inside that boundary. They cannot be caller-
  supplied, overridden, backdated, future-dated, or reused from an earlier
  evaluation. If the boundary cannot assign authoritative time and sequence or
  cannot prove that every mutation effective at or before that linearization
  point is included, the result is `unavailable`. At that boundary the
  evaluation must start from the canonical gate-and-launch-scope head and resolve
  one snapshot-consistent selected decision aggregate containing its event,
  complete transition chain, current head, and authoritative audit high-water
  mark through `evaluated_at`, plus the current lifecycle and expiry-policy
  heads. The scope head and selected decision identity must match, and only a
  unique current `accepted` and unexpired decision head governed by current valid
  policy heads passes. A missing, multiple-current,
  pending, rejected, expired, canceled, superseded, forked, gapped, mismatched,
  stale-predecessor, not resolved through `evaluated_at`, or later-invalidated
  scope, decision, or policy state fails closed. The current-status evaluation
  and projection must share that boundary, and its result must bind
  `mode=current`, the boundary-assigned time and sequence, fence or linearization
  identity, every resolved-through high-water mark, and the resulting status for
  that response only. A caller-selected `as_of` is permitted solely in a
  separately typed `historical` mode whose output is labeled non-current and
  cannot authorize a GA claim, release, or rollout; it never changes the
  historical decision event.
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
  policy. A static artifact may cite an immutable decision event or an explicitly
  historical `as_of` result as historical evidence only and must not present it
  as current GA status. A historical accepted event, earlier snapshot, cached
  current-mode result, or reused `evaluated_at` cannot substitute for a new
  current evaluation; an arbitrary favorable non-head aggregate cannot be
  selected, and a superseded event can be evaluated only through its separately
  identified successor.
- The same current evaluation must resolve the immutable input-evidence index,
  journey-run and one-time-execution primary-outcome aggregate/head closures,
  separate owner-review aggregate/head closure, every producer-attribution
  aggregate/current head, every selected attribution-policy chain/current head,
  the exact producer-currentness input union, and the historical and evaluated-
  at producer-closure records, every reviewed-at ownership and membership relationship-proof chain
  and current head, the exact relationship-policy dependency closure and every
  selected policy chain/current head, review-independence closure, the selected
  RC-proof-packet aggregate's complete chain and current head and exact packet-
  to-selected-result mapping, complete decision-bound review-outcome aggregate
  and head set, and any evaluated-at consumed-review
  control closure required below; the decision-scoped
  source-authoritative identity-resolution head for the exact decision-bound
  acting approver, selected approver-coverage holders, producers, independent
  reviewers, reviewed-evidence owners, credential custodians, requirements
  approval actors, qualification participants, qualification issuers,
  qualification-acceptance actors, and every qualification-scoped exact
  decision-bound policy-prohibited qualification principal,
  selected root holder, attributable root-governance approval
  actor, and every selected assignment-or-delegation issuer and grantee's source-
  authority and opaque source-subject set, count, and digest; and,
  separately, the source-authoritative current identity-resolution head and
  immutable source snapshot used at `evaluated_at` to re-canonicalize that exact
  fixed decision-bound subject set, the current attribution-derived producer
  subject sets for the decision-input and currently consumed-review partitions,
  and every current-successor credential custodian; every
  required reviewed and redacted artifact or authoritative-record
  version in that input index, the exact decision-bound
  `launch_scope_definition` head and deployment-class set, the complete
  decision-bound deployment-profile and environment-criteria dependency closure
  and every selected lifecycle head, the separate complete decision-bound
  journey and operability environment-evidence lifecycle closures and every
  selected evidence aggregate's complete chain and source-authoritative current
  head, and the exact governing environment-source-policy dependency closure and
  every selected policy aggregate's complete chain and current head, the complete
  decision-bound scope-class requirements pair closure and every selected
  `launch_operability_requirements` aggregate, current head, required-component
  set, applicability matrix, claimed-capacity-boundary, material-environment-
  boundary and referenced conservative-equivalence-rule, environment-coverage-
  rule, cross-class-backup-reuse-rule and sequence-equivalence-rule child sets,
  supported-upgrade-path set, and
  credential-family-definition set, every decision-bound requirements-
  separation control closure, every decision-bound routine-
  backup and operator-health stable
  aggregate and current head and, for backup, the independent material-
  configuration-history and reviewed-change-registry heads, derived
  configuration-backup-obligation closure, and restore-rehearsal schedule and
  currentness rule, every claimed
  participant qualification-lifecycle head and its governing
  qualification-source policy head, the complete decision-used journey-coverage
  rule aggregate and head set, every claimed capability
  scope-authority head, every decision-bound credential-lifecycle aggregate and
  its current head,
  the exact profile-derived GA-approver-ownership coverage closure and selected
  holder authority heads, the exact decision-bound root-governance aggregate and
  current head, immutable root-provenance identity, and complete assignment and
  delegation-chain aggregate and head set,
  the exact support-ownership and upgrade-ownership coverage closures and heads
  bound by the selected decision, the exact authoritative limitation-registry
  current head and bound disposition/currentness-rule head, and one AegisOps-
  owned evidence-retention and resolvability head plus, in current-lifetime mode,
  the decision-input integrity-review aggregate and current head. The immutable
  decision-bound primary-run, owner-review, producer-attribution and review-
  relationship closures remain historical provenance. The evaluation record
  must separately bind the exact producer-currentness input union and its
  decision-bound/currently-consumed provenance, set, count and digest; their
  exact evaluated-at aggregate-to-current-head and attribution-to-policy-head
  and relationship-to-policy-head mappings; complete predecessor-chain identities; governing currentness-rule
  heads; each complete per-qualification actor-separation mapping member, bound
  policy predicate, prohibited-subject source proof and current comparison; the
  selected RC-proof-packet chain, current head, source high-water mark, packet-
  to-result mapping and historical packet/result audit order; the two producer input partitions and union;
  their sets, counts, digests
  and source high-water marks; the rederived current decision-input producer
  closure and per-consumed-review producer slices; and the resulting run, review
  and independence comparisons.
  It cannot overwrite a decision-bound head with a successor. The immutable
  decision-scoped
  historical identity-resolution head and source snapshot must remain exactly
  retrievable as audit provenance and cannot be rebound. At every `evaluated_at`,
  the source-authoritative current identity-resolution head must atomically
  re-canonicalize the complete fixed decision-bound subject set and, as separate
  exact partitions, the current attribution-derived decision-input producer set,
  each currently consumed review's producer set, and every current-successor
  custodian set. The evaluation record must bind that current head, immutable
  source snapshot, audit high-water mark, each partition's origin tags, and
  separate exact source-subject sets, counts, digests, and mapping results for
  the fixed, attribution-derived, consumed-review, and current-successor
  populations.

  Current-head advancement alone is not a failure. However, an unavailable or
  missing historical reference or current head; a missing, extra, or substituted
  fixed subject; ambiguous or conflicting resolution; fixed-set mapping drift or
  alias collapse; alias-equivalent qualification participant overlap with that
  qualification's issuer, acceptance actor, or policy-prohibited principal;
  alias-equivalent approver-producer overlap; or a per-review
  reviewer overlap with that review's exact authoritative owner set or complete
  reviewed-evidence producer set returns `unavailable` and requires the
  applicable new review or decision. A no-weaker successor in the same
  credential-lifecycle aggregate may use a changed current custodian population
  only when the current mapping is complete, unambiguous, non-stale,
  non-duplicate, non-alias-collapsed, and satisfies the applicable profile
  cardinality. The evaluated-at current mapping neither rebinds the historical
  head or immutable decision event nor replaces its fixed mappings.
  The immutable decision-bound requirements-separation closure set must still
  reconcile bidirectionally and one-to-one with the complete selected
  requirements, approval, target, and execution tuple set, including the exact
  tuple and closure member identities, counts, digests and mappings. Each member
  closure must still match its exact tuple and role-labeled producer slices. A
  requirements approval actor who resolves equal to any member of that tuple's
  requirements-author, target-author, or exercise-producer set, or any missing,
  extra, substituted, stale, or mismatched role slice, returns `unavailable` and
  requires a new requirements approval and head, target, affected rerun, and GA
  decision. Creation of the approval event or control closure itself remains
  outside that per-tuple producer predicate. The evaluation record must bind the
  complete per-tuple current separation-result set, count, digest, identity-head
  mapping results and audit high-water mark without replacing the immutable
  decision-bound tuple or closure set. A missing, extra, duplicated,
  substituted, unreferenced or tuple-mismatched closure, or a tuple-set,
  closure-set, count, digest or mapping mismatch, returns `unavailable`.
  Each review-independence closure must still match its
  decision-bound review and evidence set, per-review evidence-producer set and,
  for derived evidence, its content-bound complete acyclic producer-closure
  slice, authoritative ownership snapshot and exact owner set, reviewer and
  owner subjects, and reviewed-at membership results. A retroactive identity,
  ownership, or membership
  correction, revocation, ambiguity, or newly discovered overlap returns
  `unavailable` and requires a new independent review and decision. A normal
  post-review group join or leave does not invalidate the historical review when
  the authoritative result effective at `reviewed_at` remains unchanged.

  When a later routine successor review is consumed by current evaluation,
  AegisOps must first derive the complete exact currently consumed review set
  from every decision-bound routine aggregate's completely resolved post-
  decision successor chain and every obligation due or open at `evaluated_at`,
  including each current-lifetime integrity-review slot whose governing cadence
  rule explicitly requires independent review:
  the set contains every `review_outcome` identity that those chains or
  obligations reference or require to support the current projection, and no
  other identity. The evaluation must materialize a non-evidence-member
  `consumed_review_control` closure bound to that set; each
  review-outcome aggregate and current head; the exact reviewed evidence and its
  exact root-and-reachable-node producer-currentness partition, root-to-node
  edges, set, count and digest; each node's current producer-attribution
  aggregate/head and governing attribution-policy head mapping; and, for derived
  evidence, its content-bound complete current
  producer-closure slice; the authoritative reviewed-at owner snapshot, exact
  owner set and membership proofs; their exact relationship-policy dependency
  closure, current policy heads and relationship-to-policy mappings; the source-
  authoritative current identity-
  resolution head and mapping results; each per-review independence result; and
  the set, count, digest and audit high-water mark. The derived set and closure
  members must reconcile bidirectionally one-to-one. The same per-review
  reviewer-owner and reviewer-producer predicates must be rederived from the
  exact producer-currentness input union and pass inside the same evaluated-at
  snapshot. A missing, extra, duplicate, omitted, relabeled-as-
  unconsumed, set, count or digest-mismatched, stale, ambiguous, unavailable or
  overlapping evidence, attribution, ownership, membership, identity mapping or
  independence state returns `unavailable`. This evaluated-at decision-control
  metadata does not modify the immutable decision-time cohort or require its own
  review. An accountable routine source review that the governing Accepted
  profile or currentness rule does not classify as an independent GA evidence
  review does not thereby create an independent-review `review_outcome` or
  control-closure member. A review outcome already required by the integrity-
  review lifecycle remains in that lifecycle, but enters
  `consumed_review_control` only when its cadence rule explicitly requires
  independence.

  The selected RC-proof-packet aggregate must resolve its complete non-forking
  chain and authoritative current head through `evaluated_at` in the same
  snapshot as the selected RC-result chain and preserve the exact packet
  content, repository revision, journey run, packet-input closure and packet-to-
  result mapping plus the decision-bound strict packet-head/result-head/decision
  audit order. Temporary unreadability returns `unavailable` until the same
  complete valid chains resolve. A correction, withdrawal, revocation,
  invalidating supersession, fork, gap, cached favorable non-head, replacement,
  or mapping mismatch returns `unavailable` and requires a new packet,
  independently accepted RC result and GA decision; metadata-only
  same-aggregate advancement may pass only when every bound fact remains exact.

  Each
  decision-bound review-outcome aggregate must resolve its complete non-forking
  chain and authoritative current head through `evaluated_at` and reconcile
  exactly to the decision-bound set, count, and digest. A same-aggregate head
  advance may pass only when it preserves the exact immutable review or RC
  result, reviewed evidence, reviewer and authority, outcome, follow-up semantics,
  scope, revision, and effective posture. Temporary unreadability returns
  `unavailable` until the same valid chain resolves. A missing, forked, gapped,
  corrected, retracted, rejected, revoked, expired, superseded, mismatched, or
  replacement result returns `unavailable`; a favorable historical or non-head
  outcome cannot substitute, and restoring acceptance requires a new applicable
  review or RC result, review-independence closure, and GA decision rather than
  in-place rebinding. When a permitted same-aggregate routine successor is first
  consumed by a later current evaluation, that evaluation must separately bind
  the complete exact consumed-review control closure defined above and apply the
  same currentness rules; future review heads are not added to the immutable
  decision-time cohort. Each decision-used journey-coverage aggregate must
  resolve its
  complete non-forking
  chain and current head through `evaluated_at`. Temporary unreadability returns
  `unavailable` until the same valid head resolves. A future-only same-aggregate
  successor may pass only when it preserves the executed interval and every
  source, covered-set, profile, criteria, comparison, and review-authority
  binding; a missing, forked, gapped, corrected, revoked, expired,
  interval-invalidating supersession, mismatch, or replacement rule requires a
  predeclared valid rule, affected journey coverage, and a new decision rather
  than in-place rebinding. Direct per-class journeys require no rule head. The
  GA-approver-ownership closure must still satisfy each decision-bound profile
  minimum with canonically distinct current human holders and the acting
  approver must remain in every applicable set. A below-minimum, alias-collapsed,
  missing, forked, gapped, expired, revoked, superseded, wrong-scope, or
  replacement holder or authority head returns `unavailable`; a substitute
  holder cannot be rebound to the existing decision. The decision-bound root-
  governance aggregate and every assignment or delegation aggregate in the
  complete authority chain must likewise resolve their complete non-forking
  successor chains and current heads through `evaluated_at`, with exact root
  provenance, issuer, grantee, scope, effective, expiry, revocation and
  supersession state, set, count, digest and audit high-water mark. The evaluated-
  at current identity head must re-canonicalize the exact decision-bound root
  holder, root approval actor, and every issuer and grantee and re-prove their
  required distinctness and acyclic chain. Temporary unreadability returns
  `unavailable` until the same valid chain and mappings resolve. A
  missing, forked, gapped, expired, revoked, superseded, scope-widened, root,
  issuer, grantee or provenance-mismatched, mapping-missing, ambiguous, alias-
  collapsed, canonical-cycle, or replacement root or chain returns `unavailable`
  and cannot be rebound; restoring acceptance requires a new
  complete authority evaluation and GA decision. Each ownership closure
  must still map the complete authoritative
  deployment-class set exactly once for its family to the decision-bound selected
  heads. Each selected head must match its decision-bound identity, ownership
  family, scope, and covered class set and remain current, effective, unrevoked,
  non-retired, and independently reviewed through `evaluated_at`. A missing or temporarily
  unreadable unchanged head returns `unavailable` until that exact head can be
  resolved again. Removal, expiry, retirement, reassignment, supersession,
  scope change, or replacement-head mismatch also returns `unavailable`; a
  replacement cannot be rebound to the existing decision, and restoring an
  accepted claim requires a new aggregate and complete gate-input and
  human-authority evaluation. The launch-scope-definition head must still match
  the decision-bound identity, exact class set, count, digest, non-empty launch-
  eligible subset, subset count and digest, profile and criteria bindings, and
  audit high-water mark. Every eligible subset member must still resolve to an
  Accepted customer-deployment or small-production-eligible profile. A temporary
  read failure returns
  `unavailable` until that exact head resolves; an add, removal, rename, alias,
  scope, lifecycle, profile, criteria, or head change cannot be rebound and
  requires a new decision and complete evaluation. Every selected deployment-
  profile and environment-criteria aggregate must resolve its complete non-
  forking chain and authoritative current head through `evaluated_at` and still
  reconcile exactly to the decision-bound dependency closure. A temporary read
  failure returns `unavailable` until valid state resolves. A same-aggregate head
  advance may pass only when it preserves the exact bound Accepted version,
  class and environment scope, effective semantics, usage mapping, and every
  derived cadence, capacity, approver-coverage, custody, comparison, and other
  obligation. A missing, forked, gapped, expired, revoked, superseded, narrowed,
  replacement, different-version, or semantically changed head returns
  `unavailable`; it cannot be rebound, and restoring acceptance requires new
  declarations, targets, affected reruns, and a new complete decision. Every
  requirements aggregate
  and child exact set must still match the decision-bound scope-class pair,
  identity, count, digest, approval provenance, lifecycle, and audit high-water
  mark, including the exact cross-class source/target-applicability-to-rule and
  sequence-hop-edge-to-rule mappings, and remain current, accepted, unexpired,
  unrevoked, and non-superseded
  through `evaluated_at`. Temporary unreadability returns `unavailable` until
  the same exact state resolves. A missing, forked, gapped, changed, historical,
  revoked, superseded, or replacement requirements head or component, matrix,
  capacity-boundary, referenced conservative-equivalence-rule, environment-
  coverage-rule, cross-class-backup-reuse-rule, sequence-equivalence-rule,
  upgrade-path, or credential-family-definition set returns `unavailable`; it
  cannot be rebound, and restoring acceptance requires a new target, every
  affected rerun, and a new complete decision. Separately, every concrete cross-
  class restore-target mapping in the immutable decision input and manifest must
  still reconcile bidirectionally to the target's exact current rule head,
  accepted review-outcome current head, source backup and manifest and to one
  requirements-bound applicability tuple. Missing, extra, duplicate,
  substituted, stale, target-
  mismatched or in-place-rebound concrete mapping returns `unavailable`; it does
  not mutate the historical requirements head. The evaluation must also reprove
  the immutable rule-content/review-head/accepted-parent/target/execution and
  backup/integrity/review/target/execution audit orders; a reserved-only, future,
  equal, reversed, backdated, or post-target materialization returns
  `unavailable`. The limitation head must
  likewise match the exact decision-bound gate, scope, applicability predicate,
  record set, count, authoritative record-state and disposition identities, and
  audit high-water mark through `evaluated_at`. Its bound disposition/currentness
  rule head and immutable version must remain current `accepted`, effective,
  unexpired, unrevoked, and non-superseded. The evaluation must derive each
  member's effective review and disposition posture at `evaluated_at` from its
  bound currentness rule, cadence or due date, accepted-risk and follow-up state,
  and next invalidation boundary, and must recompute every GA review follow-up's
  maximum permitted due boundary from its immutable origin and bound policy
  parameters. An over-maximum, extended, reset, overdue, expired, or effectively
  blocking posture or a missing, duplicate, or mismatched decision-bound review-
  follow-up mapping returns `unavailable` even when the head identity has not
  changed. A
  temporarily unreadable
  unchanged head returns `unavailable` until it resolves again. An in-scope
  create, update, reopen, close, deletion, severity, disposition, owner, scope,
  applicability, lifecycle, fork, gap, or head change returns `unavailable`;
  the replacement head cannot be rebound to the existing decision and accepted
  status requires a new aggregate and complete evaluation. An out-of-scope
  registry mutation does not alter the decision-scoped head. Each decision-bound
  qualification aggregate and governing policy aggregate must resolve its
  complete non-forking lifecycle and authoritative current head through
  `evaluated_at` and preserve the bound source, exact issuer and qualification-
  acceptance actor subjects and authority, the exact decision-bound policy
  version and prohibited-role predicate, per-qualification exact prohibited-
  subject set, count, digest, role/source-proof mapping, scope, and qualification
  for every journey execution interval. That historical mapping set must still
  reconcile bidirectionally one-to-one with the qualification set. The current
  identity head must re-canonicalize the exact historical participant, issuer,
  acceptance-actor and qualification-scoped prohibited-principal sets and
  preserve the required per-qualification separation; it must not rederive or
  rebind the historical set from a newer policy version. An unavailable,
  missing, extra, duplicate, wrong-policy or wrong-qualification slice, forked,
  gapped, authority- or source-proof-mismatched, mapping-mismatched, alias-
  collapsed, self-issued, or retroactively corrected or revoked interval or
  applicable predicate returns `unavailable` and requires new journey evidence
  and a new decision. A later head is permitted only when it is a valid successor
  in the same aggregate and leaves that interval's prohibited-role predicate,
  completeness semantics, historical actor mapping, canonical separation,
  source and issuer authority unchanged; a normal relationship end after
  `completed_at` or a future-only policy successor that does not retroactively
  change those facts therefore does not invalidate the historical journey. A
  different participant, qualification, source, or policy-authority aggregate
  cannot be rebound to the old decision. Each decision-bound routine-
  backup and operator-health aggregate must resolve the same stable aggregate's
  complete non-forking successor chain and current head through `evaluated_at`.
  The evaluation must reconcile every slot, attempt, review, finding,
  escalation, and follow-up whose Accepted deadline is at or before that instant
  or whose lifecycle remains open, including time-derived obligations when the
  head identity has not changed. An on-time, accepted, no-weaker routine
  successor in the same aggregate may pass and a future obligation not yet due
  is not blocking. Temporary unreadability returns `unavailable` until the same
  valid chain resolves. A missing, forked, gapped, omitted, late, overdue,
  rejected, unreviewed, hidden-failure, unresolved-blocker, weaker, or
  replacement aggregate returns `unavailable`. Late evidence cannot cure the
  old miss; restoration requires a new complete gap-free window, its required
  review, and a new decision, while a governing requirements change also
  requires the affected new target and rerun. For the backup aggregate, the same
  evaluation must also resolve the independent material-configuration-history
  and reviewed-change-registry successor chains and source high-water marks,
  regenerate every change-triggered backup obligation, and reconcile every
  profile-derived restore-rehearsal slot due or open at `evaluated_at`. A future
  restore slot is nonblocking, and an on-time successful reviewed same-aggregate
  successor may pass. An unregistered or hidden configuration transition,
  missing change-triggered backup, or missing, late, failed, unreviewed, wrong-
  source, wrong-revision, or wrong-target restore returns `unavailable`; late
  evidence cannot cure the miss. A target-bound material configuration change
  still requires a new target, affected rerun, and new decision even when its
  backup succeeds. Each credential-lifecycle
  aggregate must resolve its complete non-forking successor chain and current
  head through `evaluated_at`, preserve the bound family-definition set and
  governing obligations, and prove every due or triggered event completed on
  time with accepted review, no weaker ownership, scope, or custody, a complete
  current custodian set freshly mapped to canonically distinct humans at the
  profile-required cardinality, and closed break-glass state. The evaluation
  must also re-resolve the decision-bound historical custodian mappings so a
  retroactive alias collapse or correction fails closed. A routine successful
  successor with a distinct no-weaker custodian replacement may pass without
  rebinding the event, but an unavailable,
  missing, forked, gapped, omitted, overdue, failed, open, unreviewed, weaker, or
  replacement aggregate returns `unavailable`; a replacement or definition
  change requires a new decision rather than rebinding. The retention head
  must bind the complete ordered
  decision-input evidence-identifier set and count, producer-closure record and
  complete producer set and entry counts, content or record identities,
  storage-class and location version, custody, provenance, review, applicable
  retention or legal-hold posture, most recent integrity result, and audit
  high-water mark. For no-automatic-expiry it must additionally
  bind the selected mode and current compatibility-rule head. It must bind either
  the current-lifetime integrity-review aggregate identity and decision-time
  head, authoritative `coverage_start = decision_at`, first-slot anchor,
  Accepted cadence and currentness rule, complete decision-input set and digest,
  due-slot and attempt/review exact sets, next-due boundary and audit high-water
  mark, or the exact or deterministic retention cutoff, first expiry-
  eligibility and effective invalidation
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

  In `current-lifetime` mode, that evaluation must also resolve the complete non-
  forking successor chain and current integrity-review head, regenerate every
  slot from the immutable decision-time coverage and first-slot anchors through
  `evaluated_at`, and exactly reconcile every due, overlapping, or open slot
  and its verification attempts, results, and exact review-outcome aggregate/
  current-head mappings against the complete immutable decision-input closure.
  Every selected outcome chain and current head must resolve in the same
  snapshot, and any equivalent child-outcome mutation must have advanced the
  integrity-review head. The evaluation record must bind the authoritative
  verification-result completion, review-and-initial-head commit, integrity-
  parent successor and evaluated-at read sequence and prove the strict order
  defined above for every satisfying slot. For every slot whose cadence rule
  requires independence, the same evaluation must derive that review into the
  exact currently consumed review set and pass its complete
  `consumed_review_control` producer, owner, membership, identity and per-review
  independence predicates in this snapshot. A future slot is non-blocking and an on-time
  successful reviewed no-weaker successor in the same aggregate may pass.
  Missing, omitted, forked, gapped, late, failed, unreviewed, partial, wrong-
  input, duplicate, cross-slot, weaker, corrected, retracted, rejected, revoked,
  expired, superseded, cached-favorable, outcome-mismatched, or replacement
  state returns `unavailable`; a later verification or review cannot cure a
  missed deadline, and the historical most-recent result or immutable favorable
  review bytes cannot substitute for the due-slot exact set. Temporary
  unreadability may recover only when the same complete valid integrity and
  outcome chains resolve.

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
  distinct from every evidence producer. Inside the same atomic decision
  boundary, the authority check must prove one-to-one reconciliation with the
  input index and bind the exact producer-closure record, complete canonical
  producer union, complete acting-approver, selected approver-coverage-holder,
  producer, independent-reviewer, reviewed-evidence-owner, credential-custodian,
  requirements-approval-actor, qualification-participant, qualification-issuer,
  qualification-acceptance-actor, policy-prohibited-qualification-principal,
  selected root-holder, attributable root-
  governance-approval-actor, and every selected assignment-or-delegation issuer
  and grantee source-subject set identity, count and digest, every mapping
  result, the exact selected requirements tuple-set and requirements-separation
  closure-set identities, members, counts, digests and bidirectional mappings,
  and provenance audit high-water mark. The exact decision-bound
  source-authority and opaque source-subject set, without missing, extra, or
  substituted members, must be normalized by the same
  source-authoritative decision-scoped identity-resolution current head and its
  immutable source snapshot bound by the decision; self-asserted aliases,
  display names, email addresses, or Git author strings do not establish
  identity. The approver's canonical identity and every alias-equivalent
  identity must be absent from every direct producer set and from the union,
  including when the approver initiated automation that produced an indexed
  input. Root-approver versus root-holder and every issuer-versus-grantee
  distinctness check, plus chain-cycle detection, must likewise use resolved
  canonical principals rather than raw record or source identifiers. Each
  requirements approval actor must likewise resolve distinct from the complete
  exact requirements-author, target-author, and exercise-producer slices for the
  tuple it approved. Each qualification participant must likewise resolve
  distinct from that qualification's exact issuer, acceptance actor, and
  decision-bound policy-prohibited principal set derived by its exact actor-
  separation mapping member. Missing
  attribution, ambiguous or conflicting identities, alias collapse, or any input,
  attribution, closure, or mutable identity-head change leaves the attempt
  pending; recording a different owner, reviewer, root, issuer or grantee does
  not establish separation of duties.
- The decision must also bind one immutable, profile-derived
  `GA-approver-ownership` coverage closure. It is derived from the authoritative
  deployment-class set and each class's current Accepted deployment-profile
  head and binds, per class, the required minimum, exact ordered selected-holder
  set, count and digest, and each holder's source-authority and opaque
  source-subject identity, scope-valid assignment or delegation, validated
  authority-chain identity, and current head. The acting approver must be a
  member of every applicable class coverage set. For a small-production SMB
  class, at least two canonically distinct human principals must hold current GA
  release authority for that scope; aliases, duplicate grants to one person,
  unresolved group or role labels, or an issuer, root designator, or
  administrator without their own scope-valid grant cannot increase the count.
  The closure proves coverage and grants no authority. It requires neither two
  signatures, two roots, nor two issuers: one eligible acting approver still
  creates the decision event.
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
  root. Every selected root holder, actual attributable human root-governance
  approval actor, and issuer and grantee in the selected assignment or delegation
  chain must bind a source-authority identity and opaque stable source-subject
  identifier and enter the same exact decision-scoped identity-resolution
  closure. A group, role or title cannot replace the actual approval actor. Root-
  approval-actor versus root-holder distinctness, every issuer-versus-grantee
  distinctness check, and cycle detection must compare source-authoritatively
  resolved canonical principals. Missing, ambiguous, conflicting, alias-
  collapsed, self-asserted or substituted mapping; missing links; canonical
  cycles; scope widening; an alias-equivalent issuer and grantee; and self-issued
  or otherwise unauthorized grants block acceptance. This identity closure
  proves identity only and grants no authority. It is limited to the selected
  decision-bound root and chain and does not require an enterprise directory,
  second root, second issuer or second signature. This ADR does not designate
  that initial authority root or grant GA release authority.
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
  and decision attempt. A later revocation does not rewrite the historical
  decision event. It makes the current projection immediately `unavailable` when
  the root-governance or complete authority-chain dependency is re-resolved,
  independent of whether profile-derived holder coverage has changed; a durable
  GA-decision lifecycle-state mutation still requires a separately authorized
  transition. Restoring current acceptance after an authority-semantic change
  requires a new complete authority evaluation and decision rather than rebinding
  the old event.
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
  declared recovery targets, plus the profile-derived restore-rehearsal schedule,
  next due boundary, current due-slot reconciliation, and the complete exact
  selected cross-class-backup-reuse-rule set, count, digest, and bidirectional
  restore-target-to-rule-review-and-source-backup mapping mechanically derived
  from every cross-class restore target and reconciled to the requirements-bound
  source/target applicability tuple,
- the current immutable supported-upgrade-path exact set and exact-version
  upgrade and rollback rehearsal evidence for every compatible path claimed by
  the launch scope, including the complete exact referenced sequence-
  equivalence-rule set, count, digest, and path-edge mapping, with post-operation
  smoke and authoritative-record-chain checks,
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
must bind every pre-cutoff input's exact producer-attribution identity, current
attribution-policy head, and the exact current ownership-source and group-
resolution policy heads that will govern the reviewed-at proofs, then reserve
the exact identities for the detached review attestation, that
attestation's inseparable initial review-outcome head, attribution record and
producer-attribution head,
every derived reviewed-at ownership-snapshot and owner-group-membership proof
record and its relationship-proof head for the reserved review, the
deterministic relationship-policy-dependency-closure record, the
deterministic producer-closure record, the
review-independence-closure and decision-used review-outcome-closure records, and
decision-attempt bookkeeping. It must then receive an immutable, detached,
independent `accepted` aggregate-review
attestation that directly binds the exact snapshot identity, cutoff, high-water
mark, and ordered set and count, and carries its own AegisOps-assigned review time
and audit sequence. Chronology must prove both
`evidence_cutoff_at <= aggregate_reviewed_at <= decision_at` and
`cutoff_high_water < aggregate_review_and_initial_outcome_head_sequence < review_attribution_and_initial_head_sequence < every_review_relationship_proof_and_initial_head_sequence < relationship_policy_dependency_closure_sequence < producer_closure_sequence < review_independence_closure_sequence < review_outcome_closure_sequence < decision_sequence`; a
caller-supplied time or same-time wrong sequence cannot substitute.

The detached attestation is stored outside the operational evidence aggregates
and cannot change a finding, disposition, obligation, or source record. Its exact
reserved identity and inseparable initial review-outcome-head identity, its exact
per-entry attribution and inseparable initial producer-attribution-head
identities, the deterministic relationship-policy-dependency-closure and
producer-closure identities, the
exact reserved reviewed-at ownership-snapshot and owner-group-membership proof
and inseparable initial relationship-proof-head identities, the reserved review-
independence and review-outcome-closure
identities, the required decision-control audit or head advances, and the exact
immutable decision-attempt bookkeeping identity bound to the cohort are the only
expected post-cutoff records excluded from zero-delta comparison. Each proof may
only bind the reserved review and an immutable source-authoritative ownership or
membership version and as-of relationship; it cannot create, update, or otherwise
mutate operational owner or group state. Each allowed record must bind the
reviewed cutoff snapshot, reserved identity and exact governing current policy
heads; an unreserved, extra, self-member, wrong-source, wrong-policy, wrong-order,
differently bound, or operationally mutating record is an unexpected delta.
During atomic decision creation, the authoritative operational evidence heads,
including the independent material-configuration history head, the selected
attribution, ownership-source and group-resolution policy heads, and generated-
obligation sets must prove that no other in-scope record, newly
due obligation, pre-existing open obligation whose deadline or grace became
due, or state transition was omitted in
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

The backup evidence must also bind an independently observed, immutable or
tamper-evident material-configuration history for every class and environment.
Its complete configuration-surface set and version lifecycle are derived from
the governing Accepted launch profile and requirements effective for each
coverage subinterval and are limited to repository or runtime
configuration, deployment or topology, proxy, TLS and secret boundaries,
persistent-storage topology, protected-state definitions, schema or migration
configuration, and backup-path state that can affect the declared launch,
recovery, security, or authority boundary. Ordinary authoritative alert, case,
evidence, approval, action, or reconciliation record-content changes are not
configuration transitions unless they alter one of those schema, retention,
authority, storage, topology, or configuration boundaries; their data remains
covered by the existing record-chain and routine-backup requirements. The
history must preserve the
opening and closing state identities and one non-forking predecessor chain from
`coverage_start` through `evidence_cutoff_at`, with every transition's immutable
before and after identities, effective time and audit sequence, class and
environment, source or actor provenance, complete ordered set and count, and
audit high-water mark. It must not be derived solely from the reviewed-change
registry or operability manifest, and it must not retain configuration values or
secret material.

Every independently observed material transition must reconcile
deterministically to an applied reviewed-configuration-change record and to the
profile-required change-triggered backup with the required before or after
ordering. An Accepted, predeclared batch rule may map an exact transition set,
but every applied registry record must still map back to its observed transition
or transitions. Planned, rejected, or canceled records remain visible but
cannot assert a change or backup that did not occur. An unregistered, missing,
extra-applied, ambiguous, forked, gapped, altered-then-reverted-but-omitted,
class- or digest-mismatched, or wrongly ordered transition blocks GA. This
independently observed history is configuration evidence only; it does not
become gate or approval truth.

The evidence must include a snapshot-consistent inventory of the authoritative
backup-attempt, independently observed configuration-transition,
reviewed-configuration-change, and accountable-review records continuously from
`coverage_start` through `evidence_cutoff_at`, with its as-of boundary, ordered
record-identifier sets and counts, and audit high-water mark. The manifest set
must equal every scheduled slot, independently observed material transition,
applied reviewed configuration change, review, and every attempt regardless of
lifecycle state whose authoritative
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
predeclared, independently Accepted rule covers the exact source and target
classes, profile versions and environments, backup mechanism, protected state,
schema and configuration, storage, custody, retention, freshness, cadence and
source eligibility and proves a machine-verifiable no-weaker comparison for the
target class; generic environment equivalence is insufficient. The immutable
rule content and version must be committed before its independent review, and
that review event and initial `review_outcome` head must bind the exact committed
content; a reserved identity or future rule/review head is not evidence. Every
selected reuse rule must then be an inseparable accepted lifecycle child of the target class's
`launch_operability_requirements` aggregate and bind its immutable Accepted
version, exact independent review-outcome aggregate, immutable accepted review
event and head-at-acceptance, effective interval and status, predecessor,
sequence, accepted-child/parent commit sequence and audit high-water mark. The parent head binds the complete exact selected reuse-
rule applicability set, count and digest and a bidirectional
`(source class, profile version, environment, target class, profile version,
environment) -> rule head/version` mapping that can be fixed before any concrete
restore target or backup is selected. The cross-class restore target must
directly bind the exact current rule head, accepted review-outcome current head,
source backup and manifest; a same-class target needs no rule member. The operability manifest and
decision-input index must mechanically derive from every concrete cross-class
target one complete exact target-to-rule-review-and-source-backup mapping set,
count and digest, reconcile it bidirectionally to those targets, and prove every
selected rule against the requirements-bound applicability tuple. That concrete
mapping is not a requirements child and cannot introduce a future target or
reserved backup into the parent head. Independent authoritative ordering must prove
`rule_content_commit_sequence < rule_review_and_initial_outcome_head_commit_sequence < accepted_rule_child_and_requirements_parent_commit_sequence < restore_target_declared_sequence < restore_execution_started_sequence`
and,
separately,
`backup_completed_sequence < integrity_pass_sequence < backup_accepted_review_sequence < restore_target_declared_sequence < restore_execution_started_sequence`;
the rule review and backup review need no mutual ordering before that target.
The rule and review outcome must remain current `accepted`, effective,
unexpired, unrevoked and non-superseded at target declaration, `decision_at`, and
every `evaluated_at`. Any child creation or lifecycle change, or an invalidating
selected review-outcome transition, must atomically advance the parent head and
child-set digest. A semantics-preserving same-aggregate review-outcome successor
may pass without parent advancement only when it preserves the exact accepted
event, rule and target bindings. A missing, extra,
duplicate, wrong-source, class, profile,
environment or revision mapping, post-target acceptance, corrected, revoked,
expired, superseded, forked, gapped, cached-non-head, replacement or weakening
rule; a corrected, retracted, rejected, revoked, expired, superseded, forked,
gapped or cached-non-head selected review outcome; an unadvanced parent; or in-
place target rebinding blocks GA. A review over reserved or uncommitted future
rule content or head, or an equal, reversed, or backdated content/review/parent/
target sequence, has the same effect. Recovery requires a new target, restore
execution, review and decision.

For each deployment class, the stable routine-backup aggregate must also carry a
profile-derived restore-rehearsal schedule and currentness rule, deterministic
slot, eligibility window, deadline and next-due boundary, and the exact pre-run
target, compliant routine-backup source, execution and result, and accountable
accepted owner-review identities for every restore slot. Every schedule version
must bind its governing Accepted profile or parameter identity
and a machine-verifiable comparison proving that its frequency, eligibility
window, deadline, grace, target, result, and review obligations are no weaker.
Each restore slot must have an immutable identity. Its target, execution, result,
and review must directly bind that same slot identity; the target declaration,
authoritative trigger, and execution start must fall inside the Accepted
eligibility window, and completion and accepted review must occur by their
Accepted deadlines. One execution may satisfy only one restore slot unless the
exact Accepted cadence version defines a deterministic reuse rule for named
slots that proves no weakening of cadence, source-backup eligibility, target,
result, or review obligations. At every
`evaluated_at`, the same aggregate's complete non-forking successor chain and
current head must regenerate and exactly reconcile every restore slot whose
deadline is then due, whose lifecycle overlaps the interval, or that remains
open. A future slot is not blocking before its Accepted profile deadline, and an
on-time, successful, reviewed, no-weaker successor in the same aggregate may
pass without a new GA decision. A missing, forked, gapped, omitted, late, failed,
unreviewed, wrong-revision, wrong-target, or noncompliant-backup restore returns
`unavailable`. Late evidence cannot retroactively cure a missed slot; restoration
requires a new current compliant window, successful reviewed rehearsal, and new
decision. The 720-hour admission cap remains separate from this profile-derived
continuing cadence: this rule does not turn every heavy exercise into a periodic
stream, change a quarterly profile to monthly, or create a public recovery
objective or enterprise scheduler requirement.

These records remain subordinate operability evidence and do
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

For each canonical launch scope, deployment class, and routine-stream family,
the backup and operator-health evidence must belong to one AegisOps-owned,
append-only, non-forking aggregate with a stable identity. The decision binds
that aggregate identity, its governing Accepted cadence and currentness-rule
identities, its independently reviewed cutoff head, audit high-water mark, and
deterministic next due boundary. After `decision_at`, an on-time, accepted,
no-weaker successor in the same aggregate may extend the stream without a new
target or GA decision. Each authoritative `evaluated_at` must resolve the
complete successor chain and current head and reconcile every deadline then due
and every overlapping or open slot, attempt, review, finding, escalation, and
follow-up. A future obligation is not blocking before its Accepted deadline,
and this rule does not require an independent aggregate review for each routine
successor when the governing profile has not made one due. A missing, forked,
gapped, omitted, late, overdue, rejected, unreviewed, hidden-failure,
unresolved-blocker, weaker, or replacement aggregate returns `unavailable`.
Temporary unreadability may recover only by resolving the same valid chain. A
late record cannot retroactively cure a missed obligation; restoring current
acceptance requires a new complete gap-free window, its due independent review,
and a new decision. A governing requirements, profile, cadence, deviation, or
currentness-rule change cannot be rebound and additionally follows the existing
new-target and affected-rerun rule where it changes target-bound obligations.

Each routine-backup aggregate must bind, per class and environment, the stable
identity and decision-time head of the independent material-configuration
history, the reviewed-configuration-change registry, and the derived
configuration-backup-obligation closure. At every `evaluated_at`, the evaluation
must resolve their complete non-forking successor chains, authoritative current
heads, and independent source high-water marks in the same snapshot, fence, or
total order as the routine-backup head. From the decision-bound material surface
through that instant, every independently observed transition must reconcile in
both directions to the applied reviewed-change set and regenerate the exact
profile-required before- or after-change backup obligations, which must then
reconcile to the backup attempts and reviews. This derivation applies even when
the prior backup head has not advanced.

A missing, unregistered, registry-only, omitted, reverted-but-hidden, forked,
gapped, wrong-order, open, or due-but-unsatisfied transition or obligation
returns `unavailable`; a temporary read failure may recover only when the same
complete valid chains and high-water marks resolve. An on-time no-weaker routine
successor may pass only when it does not change a target-bound release,
configuration, environment, profile, criteria, or requirements identity. Any
such target-bound material change remains subject to the existing new-target,
affected-rerun, and new-decision rule even when its required backup succeeds.
Ordinary alert, case, evidence, approval, action, or reconciliation content
changes and other out-of-scope non-material observations do not create a
configuration-backup obligation.

For every deployment class, the current launch-operability requirements head
must bind a complete, non-empty, ordered, immutable `supported_upgrade_path`
exact set with count of at least one for the intended launch scope. Each claimed
compatible direct path must have its own
immutable path identity and bind the exact source and gate-target release,
bundle, artifact, and configuration identities; release channel, deployment
profile, and class; compatibility posture; migration or schema identity;
required preflight and post-operation checks; backup and rollback mechanism; and
exact rollback target and immutable required rollback-evidence schema and
success-criteria identities, including routine-stream eligibility, integrity,
accepted review, custody, and retention criteria for the rollback checkpoint.
The set must record its count, digest, and approval provenance. Phase 65.3 packaging
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
Accepted sequence-equivalence rule may substitute only when it is predeclared
before the path-target envelope, binds the exact predecessor and successor hop
identities plus their reserved output and input record identities, and defines a
machine-verifiable comparison that does not weaken path, class, environment,
gate revision, state, configuration, schema, or rollback coverage. The actual
post-run output and input digests must then satisfy that predeclared predicate;
produced values cannot be embedded into or used to backdate the rule. Every
referenced rule must be an inseparable lifecycle child of the same target
class's `launch_operability_requirements` aggregate. Its current head must bind
the immutable Accepted rule version, exact path and adjacent-hop edge,
comparison dimensions, assumptions and no-weaker proof, approval authority,
effective interval and status, predecessor, sequence and audit high-water mark.
The parent requirements head must bind one complete ordered referenced-rule
set, count and digest plus a bidirectional one-to-one
`(path, predecessor hop, successor hop) -> rule head/version` mapping; an
exactly identical adjacency needs no rule and contributes no member. Every
selected rule must be current `accepted`, effective, unexpired, unrevoked and
non-superseded at target declaration, `decision_at`, and every `evaluated_at`.
A child creation or lifecycle change must atomically advance the parent
requirements head and child-set digest. Missing, extra, duplicate, wrong-edge,
post-hoc, corrected, revoked, expired, superseded, forked, gapped, cached-non-
head, replacement or weakening rule state or an unadvanced parent blocks GA and
requires a new target, affected sequence rerun and new decision. Skipped,
reordered, independently executed, reset, reinstalled, state-discontinuous, or
wrong-rollback-target hops cannot satisfy a sequence.

The manifest's claimed compatible path identifiers must exactly equal that
supported set and map to successful exact-version upgrade and rollback
executions bound to the same path-specific pre-run target, continuous run
lineage, class, environment, gate revision, and predeclared criteria. Missing,
empty, zero-count, extra, floating, arbitrary, stale, superseded, incompatible,
mismatched, failed, partial, or unexecuted claimed paths block GA.
The post-run manifest and immutable decision input index, not the pre-run
requirements head, must bind the produced upgrade and rollback outcome evidence
identities.
Incompatible or unsupported cases remain explicit owned limitations and need
not be executed, and no unclaimed historical version pair or Cartesian product
is required. This evidence does not establish silent or automatic upgrade,
automatic rollback, zero-downtime behavior, a public SLA, or a fleet-wide
upgrade capability.

The authoritative AegisOps limitation registry must expose an append-only,
non-forking current head scoped to the stable canonical gate definition,
canonical intended launch scope, authoritative record family, and applicability
predicate. That head must bind its predecessor and sequence, audit high-water
mark, and the complete ordered set, count, and digest of every in-scope
non-closed record identity together with each authoritative content, lifecycle,
severity, ownership, disposition, current review state, review cadence or due
date, accepted-risk and follow-up identity. It must also bind the Accepted
currentness and disposition-rule aggregate, current head and immutable version,
including its severity-, impact-, class-, and family-applicable machine-
verifiable maximum follow-up lifetime or cadence and calculation rule, plus the
deterministically derived next invalidation boundary for every member. That rule
head must be current `accepted`, effective, unexpired, unrevoked, and non-
superseded, or be an inseparable child with equivalent lifecycle semantics; any
rule lifecycle or parameter change must advance the limitation-registry head.
The head and snapshot must bind the
complete ordered decision-bound GA review follow-up obligation set, count, and
digest and the exact source-review, evidence, and limitation-record mapping for
every obligation. An open non-blocking obligation passes only before its bound
`due_at`; an unresolved obligation at or after that boundary is effectively
blocking even if the head identity has not changed. The limitation snapshot must
bind that exact current-head identity, the gate identifier and intended launch scope,
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
review time. It must bind exactly one immutable authoritative owner-review
record identity and content version directly to that exact run, observed result
and artifact digest, target, family, class, environment, evidence revision and
accountable execution owner and actual reviewer. The review record must bind its
AegisOps-assigned `reviewed_at` and audit sequence, explicit disposition and any
follow-up identity. The accountable owner and actual reviewer may resolve to the
same person or group unless a separately Accepted source contract requires
separation; an owner field, artifact, service identity or verifier result without
an attributable actual reviewer is not a review.
Only `accepted` or a valid non-blocking `accepted-with-follow-up` disposition may
pass; the latter must satisfy the exact limitation-obligation mapping, deadline
and currentness rules below. Missing, mutable, unknown, `not-reviewed`, rejected,
result-, target-, class-, environment-, family- or revision-mismatched, pre-
completion, or post-`decision_at` owner review blocks the execution. This
accountable owner review is subordinate evidence and does not grant GA authority
or replace any required independent GA acceptance review. It must use the
authoritative `review_outcome` lifecycle schema and enter the separate complete
owner-review aggregate/head closure even when it is not independent. It enters
the bounded independent-GA-review closure only when the decision separately uses
that same record as an independent GA evidence review, in which case all
independence rules apply. The execution record must also reference an immutable target record with its content
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
must also bind the immutable ordered hop list and the exact referenced sequence-
equivalence-rule set, count, digest, and path-edge-to-rule-head mapping current
at declaration. Independent audit ordering must prove that this envelope existed
before the direct-path execution or first hop started. It contains no produced
outcome or checkpoint identity.

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
exercise producer. The approval event must bind every attributable approval
actor's source-authority identity and opaque stable source-subject identifier.
AegisOps must deterministically materialize the complete ordered selected
requirements tuple set, identity, member identities, count and digest from every
exact requirements version and head, approval event, target and execution used
by the decision. For each member tuple, AegisOps must derive the complete role-
labeled requirements-author, target-author, and exercise-producer source-subject
sets from the exact input producer attributions already required above. One non-
evidence-member
`requirements_separation` control closure must bind that tuple, the approval-
actor set, each of those three producer slices, every set, count, digest and
canonical mapping result, the shared decision-scoped identity-resolution head
and source snapshot, and the provenance audit high-water mark. Every approval
actor must be canonically distinct from every member of all three reviewed
content, target, and execution slices. The latter three sets may overlap with
one another; this rule neither requires four people nor treats creation of the
approval event or derived separation metadata as production of the content
being approved. Missing, extra, substituted, ambiguous, stale, self-asserted,
or alias-conflicting role mapping blocks the requirements approval, target,
and execution. Before decision creation, AegisOps must materialize one immutable
requirements-separation closure-set record bound to the selected tuple-set
identity, exact ordered tuple and closure member identities, their counts and
digests, and a bidirectional one-to-one tuple-to-closure mapping. Missing, extra,
duplicate, substituted, unreferenced or tuple-mismatched closure members, or a
set, count, digest or mapping mismatch, block acceptance. The closure-set record
is decision-control metadata rather than an evidence-index member and does not
create another requirements approval obligation.

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

For each deployment class, the current requirements head must also bind a
non-empty exact claimed-capacity-boundary set derived from the current Accepted
profile and environment criteria. Each member binds the exact claimed workload
or managed-endpoint boundary, every capacity-relevant resource floor, storage
and data-volume posture, criteria identities, set count and digest, and the
comparison directions needed to prove the supported envelope. Each capacity
target and manifest must reconcile every member exactly once and either execute
with resources no more favorable and workload no less demanding than that
member, or bind an immutable conservative-equivalence rule that was independently
Accepted before target declaration. Every referenced rule must be an inseparable
child of the same `launch_operability_requirements` aggregate and its exact child
set and digest. It must identify the tested and claimed tuples, dimension
directions, assumptions, thresholds, scope, effective interval, lifecycle, and
machine-verifiable no-weaker proof and remain current `accepted`, effective,
unexpired, unrevoked, and non-superseded at target declaration, `decision_at`, and
every `evaluated_at`. Creating, changing, revoking, expiring, or superseding a
rule must advance the parent requirements head and child-set digest, thereby
invalidating the target and affected execution; a historical child cannot be
selected independently. A producer label or post-run argument cannot establish
equivalence. When an Accepted source defines ranges
without their supported correlation tuples, the gate must remain blocked or
narrow the declared minimum resource scope to the tested tuple rather than
inventing a Cartesian product. A top-of-range resource run cannot by itself
support a lower-resource claim. This rule does not require every intermediate
point or an unclaimed resource combination and does not create a public capacity
SLA.

For each deployment class, the current requirements head must also bind a non-
empty complete ordered `material_environment_boundary` exact set, count, and
digest derived from the current Accepted profile and environment criteria. Each
member is one canonical correlated tuple of the material operating-system and
version, architecture, topology, release and configuration compatibility,
proxy, TLS and secret boundary, persistent and backup-custody storage, resource
envelope, and in-scope route dimensions that those Accepted inputs declare
supported. The gate must not infer a Cartesian product from independently listed
dimension ranges; if the Accepted inputs do not define the supported correlation,
the launch scope must be narrowed to a known tuple or remain blocked.

For each mandatory operability family whose Accepted criteria make a boundary
member material, the pre-run targets and manifest must map that member exactly
once either to an execution directly bound to the exact tuple or to an immutable
conservative environment-coverage rule independently Accepted before target
declaration. Every such rule must be an inseparable child of the same
`launch_operability_requirements` aggregate and exact child-set digest and bind
the tested and covered tuple identities, family, every differing dimension,
assumptions, thresholds and comparison directions, scope, effective interval,
lifecycle, and machine-verifiable no-weaker proof. It must remain current
`accepted`, effective, unexpired, unrevoked and non-superseded at target
declaration, `decision_at`, and every `evaluated_at`; any rule creation, change,
revocation, expiry or supersession must advance the parent requirements head and
invalidate affected targets and executions. A missing, duplicate, extra, post-
hoc, producer-selected, historical, mismatched or weaker mapping blocks GA. A
class label, generic environment or journey equivalence, or successful execution
on the easiest allowed variant cannot substitute. This exact set covers only
material correlated variants actually claimed by the declared scope; it does not
enumerate every host, tenant, customer, patch, optional variant, intermediate
range point, or unclaimed multi-architecture or HA combination.

The exercises must run in at least one production-like environment for every
material-environment boundary member of every materially distinct deployment
class in the intended launch scope, subject only to the predeclared conservative
coverage rule above. Each target and execution must bind the exact boundary-
member and direct environment-record identities. Each environment record must
bind the current immutable Accepted deployment-profile
and environment-criteria identities and compare the supported operating system
and architecture, deployment profile and topology, release image and
configuration digests, proxy, TLS, and secret boundary, persistent and
backup-separated storage, resource envelope, and in-scope Wazuh and Shuffle
routes. Each dimension must record the criterion, expected predicate or value,
observed value or digest, accepted exact, set, minimum, maximum, or tolerance
comparison mode, and result.

Each operability environment comparison must also bind an immutable observation
identity, source authority, AegisOps-recorded observation and comparison times,
audit sequence and high-water mark, exact profile and criteria versions, exact
compared-dimension set, count, and digest, and its effective coverage. The pre-run
target and execution record must bind that same exact environment observation
and comparison identity. Valid chronology requires either:

- an accepted snapshot and comparison bound by the target with
  `observation_sequence <= comparison_sequence <= target_declaration_sequence < started_sequence`,
  plus authoritative environment-change history or start and completion bindings
  proving that no material compared dimension changed through
  `completed_sequence`; or
- a target that predeclares the source, criteria, and reserved attestation
  identity before `started_at`, followed by a source-authoritative immutable
  interval attestation that covers `[started_at, completed_at]` without a gap and
  binds every compared dimension and the same environment identity.

A caller-supplied or backdated time, post-run point snapshot, producer-only
assertion, unreserved interval attestation, target-to-execution environment swap,
or material mid-run change without a full valid interval proof invalidates the
execution and requires a new observation, target, and rerun. This rule does not
require continuous telemetry, a particular CMDB or host agent, or observation of
non-material dimensions.

Every decision-used journey or operability environment observation, comparison,
change-history proof, and interval attestation must also belong to an AegisOps-
owned append-only, non-forking lifecycle aggregate, or an equivalent current
representation governed by an Accepted source policy. Its current head must bind
the stable aggregate identity, exact immutable evidence kind and source version,
source authority, journey or target and execution identity, environment, class,
executed interval, profile and criteria, material-dimension set, count and digest,
observed results and coverage, status, predecessor and sequence, correction,
challenge, withdrawal, revocation and supersession provenance, and source audit
high-water mark. Every governing Accepted source policy used by a selected
environment-evidence aggregate must itself belong to a stable append-only,
non-forking lifecycle aggregate with a current head that binds its exact version,
source authority, scope, effective interval, status, predecessor and sequence,
permitted lifecycle-transition semantics, and audit high-water mark. The
decision must bind separate complete ordered journey and operability
environment-evidence aggregate and current-head closures with their sets, counts
and digests, plus the exact governing source-policy aggregate, head and version
set, count, digest and one-to-one evidence-to-policy mapping. Every selected
evidence and policy head must be current, valid, effective, unexpired,
unchallenged, unwithdrawn, unrevoked, and non-superseded inside the decision
cohort.

At every `evaluated_at`, the historical decision-bound closures remain immutable
audit provenance while the evaluator resolves each exact selected evidence and
governing source-policy aggregate's complete successor chain,
source-authoritative current head and high-water mark inside the current-read
boundary. A same-aggregate evidence successor may pass only when it preserves
the exact historical interval facts, source, environment, profile, criteria,
dimension set, results, coverage and validity. A same-policy-aggregate successor
may pass only when it preserves the exact bound policy version, scope, source
authority and transition semantics under which that evidence remains valid.
Temporary unreadability returns `unavailable` until the same valid chains
resolve. A policy expiry, revocation, supersession, source-authority or
transition-semantic change, or an evidence correction,
challenge, withdrawal, revocation, invalidating supersession, fork, gap, source-
version or interval mismatch, cached favorable non-head, self-asserted AegisOps
mirror, or replacement-evidence rebinding returns `unavailable` and requires a
new observation, declaration or target, affected rerun, and GA decision. An
unrelated or future observation and a post-completion environment change that
does not alter the exact historical interval proof remain outside the selected
closure and do not create periodic review, continuous monitoring, or catalog-
wide observation duties. The evaluation record must bind the immutable
historical closure identities and, separately for journey and operability, the
exact evaluated-at aggregate-to-current-head mapping set, count and digest,
complete predecessor-chain identities, governing policy mapping and current-head
set, policy and source high-water marks and comparison results; it cannot
overwrite a decision-bound head with its successor.

A missing, unmeasured, incomparable, out-of-tolerance, or weakening result
blocks the class. A difference is non-blocking only when its exact Accepted
criterion permits it and the comparison proves that it does not weaken security
or authority, bypass the claimed-capacity-boundary or material-environment-
boundary exact set, mask minimum-resource capacity, add an unclaimed dependency
or capability, or change required journey coverage. A producer disposition alone
cannot establish equivalence, and equivalence cannot widen launch scope. For
each declared class, the manifest must contain the complete mandatory exercise
and material-environment-boundary mapping sets, and an execution counts only for
the boundary member, class and environment record to which it is immutably
bound.

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

The current launch-operability requirements head must bind a complete, ordered
immutable credential-family definition exact set and count derived from the
Accepted launch scope, authentication baseline, and deployment profile. Each
definition identifies the canonical family, required owner-assignment, bounded
consumer and scope, delivery and custody predicates, Accepted policy, cadence,
and scheduled, emergency, ownership-change, and scope-change trigger
obligations, required event and result schema, and no-weaker comparison rules.
It must not bind observed rotation or break-glass event identities, counts,
outcomes, current assignment identities, or audit high-water marks.

The manifest and AegisOps-owned current credential-lifecycle snapshot must
reconcile exactly to that immutable family-definition set. Each current family
entry must bind its attributable owner, bounded consumers and scope, delivery
and custody references, governing current Accepted policy and cadence heads,
the complete ordered event set, count, and outcomes of every rotation whose
trigger or effective time falls in the coverage window, whose lifecycle,
deadline, or grace overlaps it, or that remains open at `evidence_cutoff_at`,
the next due boundary, and the authoritative as-of audit high-water mark. Every
selected custodian must bind a source-authority identity, opaque stable source-
subject identity, and source-authoritatively resolved canonical human principal;
the snapshot binds the exact custodian set, count, digest, and mapping results.
When the governing criteria require primary and backup or two-person custody,
the selected set must meet that profile-derived cardinality with canonically
distinct current humans. Alias splitting or collision, duplicate subjects,
unresolved or stale mappings, and group, role, service, or display labels without
the actual current human custodians fail closed. A raw credential, secret,
certificate key, or authorization value must never enter the evidence index.
An event after target declaration and at or before `evidence_cutoff_at` updates
this snapshot without changing the requirements head or invalidating an
otherwise matching target. An event after the cutoff is an operational delta
that aborts the decision attempt and requires a new cutoff, snapshot, and
independent review; it does not require a new target or rerun while the family
definition, policy, cadence, and trigger obligations remain unchanged. A change
to any such governing obligation still invalidates the target and affected
execution under the requirements-head rule.

For each canonical launch scope and deployment class, the current credential
snapshot must belong to one AegisOps-owned append-only, non-forking
credential-lifecycle aggregate with a stable identity. The decision binds that
aggregate identity, the immutable family-definition set, the Accepted
currentness and transition-rule identity, and its cutoff head and audit
high-water mark. Every authoritative `evaluated_at` must resolve the same
aggregate's complete successor chain and current head through that instant. A
successor may preserve current acceptance only when the bound family-definition
set and governing obligations remain unchanged, every due or triggered event is
complete, on time, reviewed and accepted, owner, consumer scope and custody
remain no weaker, the current custodian set is freshly canonicalized and still
satisfies the applicable profile minimum, and every break-glass use is closed
with its required return-to-normal evidence. The historical decision-bound
custodian subjects must also be re-resolved under the evaluated-at current
identity head to detect a retroactive alias merge or correction; the current
successor set is evaluation state and does not rebind the immutable decision
event. The evaluation state must bind the current identity-resolution head,
immutable source snapshot, audit high-water mark, and separate exact sets,
counts, digests, and mapping results for the decision-bound custodians and
current successor custodians. That head may advance after the decision, but only
an unchanged valid mapping of every decision-bound subject and an unambiguous
current mapping that preserves the applicable profile cardinality pass. An
unavailable, missing, forked, gapped, omitted,
overdue, failed, open, unreviewed, weaker, or replacement aggregate or a changed
family definition or governing obligation returns `unavailable`. A routine
successful successor does not require a new GA decision. A replacement
aggregate cannot be rebound and requires a new decision with complete gate-input
and human-authority evaluation; matching targets and executions that remain
within their freshness windows may be reused. A family-definition or governing-
obligation change requires a new target, affected rerun, and decision.

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
raw or directly identifying customer identifiers, email addresses, or
workstation-local paths. The privacy-minimized opaque source-subject,
organization, and engagement identifiers required by this decision are allowed
when they contain no directly identifying value and remain bound to their
source-authoritative relationship and version; they do not permit retaining the
underlying raw identity. A redaction assertion does not permit retaining the
forbidden value beside it. Direct
production access is neither required nor accepted as a substitute for
production-like evidence.

The operability packet passes only when every mandatory exercise exists, is
non-placeholder, was executed at and is bound directly to the gate evidence
revision, meets its target declared before execution, preserves AegisOps
record-chain and authority invariants, binds its exact immutable owner-review
record with an accepted or valid non-blocking accepted-with-follow-up disposition,
retains failed-path and clean-state evidence, and leaves no unresolved blocking
operability limitation. Missing, mutable, mismatched, unknown, not-reviewed,
rejected, pre-completion, post-decision, mixed-revision, stale, post-hoc-targeted,
failed, or subordinate-authority evidence blocks GA.

Every review used as an independent GA acceptance review must bind an
attributable reviewer who is distinct from the evidence producer and owner to
the exact immutable evidence identity reviewed, and record `accepted` or
`accepted-with-follow-up`. Its `review_outcome` aggregate and current-head
identity must enter the complete decision-used review-outcome closure defined
above; the selected Phase 66.8 or successor RC result is included even when it
uses a different subordinate source contract. The review record must bind the reviewer's
source-authority, opaque source-subject, and canonical human-principal identities
and the complete non-empty reviewed-at-time owner set, count of at least one, and
digest plus, for each owner, its `person` or `group` kind, source-authority, and
opaque source-subject identity. That set must equal the non-empty exact owner set
in an immutable authoritative
ownership assignment or snapshot for the reviewed evidence that was effective
at `reviewed_at` and binds its source version, effective interval, predecessor
or audit high-water mark, set, count, and digest. A reviewer-supplied owner set,
mutable label, or missing, extra, substituted, stale, or mismatched owner cannot
prove completeness, and a group label cannot replace the actual human reviewer.
Canonical or alias equivalence with any person owner blocks independence. For
every group owner, an immutable
source-authoritative membership result effective at `reviewed_at` must prove
that the reviewer was not a direct or transitive member under the Accepted
group-resolution policy bound by the decision-scoped identity-resolution head.
A true, unknown, unavailable, stale,
ambiguous, or self-asserted membership result blocks the review. An
authoritative ownership assignment/snapshot and every direct, transitive or
dependency membership proof used by a decision-bound or evaluated-at consumed
review must each belong to a stable append-only, non-forking relationship-proof
aggregate with a source-authoritative current head, or an equivalent current
representation under the Accepted ownership and group-resolution policies.
Each governing ownership-source and group-resolution policy must itself expose a
stable append-only, non-forking lifecycle aggregate and current head binding its
exact Accepted version, scope and source authority, owner-set completeness and
direct or transitive membership semantics, correction and transition authority,
effective interval, status, predecessor, sequence and audit high-water mark. Its
selected relationship head binds the exact governing policy aggregate, head and
version, stable relationship identity, reviewed evidence, owner group and
reviewer opaque subjects as applicable, exact owner set or membership result,
effective interval including `reviewed_at`, source version and authority,
predecessor and sequence, correction, revocation and supersession provenance,
and audit high-water mark. The review-independence closure and any evaluated-at
consumed-review control closure must bind the complete ordered selected
relationship aggregate/head set, count, digest and exact per-review mapping,
plus an exact relationship-policy dependency closure containing every selected
policy aggregate, head and version, set, count, digest and relationship-to-policy
mapping. Every `evaluated_at` must resolve each selected relationship and policy
aggregate's complete chain, source-authoritative current head and high-water mark
in the same current-read boundary and compare the current as-of-`reviewed_at`
owner set and membership result with the immutable review-time proof. Only
current `accepted`, effective, unexpired, unrevoked and non-superseded policy and
relationship heads may pass. A correction that changes the owner
set or direct/transitive membership at `reviewed_at`, missing, extra,
substituted, unknown or ambiguous relationship state, fork, gap, cached non-head
or replacement returns `unavailable`. Temporary unreadability returns
`unavailable` only until the same complete relationship and policy chains,
heads and high-water marks resolve again. An authoritative missing, expired,
revoked, superseded, forked, gapped or replacement policy, or a policy successor that
changes source authority, owner-set completeness, membership, correction or
transition semantics, has the same effect. A decision-bound review then requires a
new independent review and decision; a later consumed review requires the new
applicable review and recomputed control closure. A same-aggregate relationship
or policy successor, or ordinary owner/group join or leave effective only after
`reviewed_at`, may pass only when the bound policy version remains accepted for
the reviewed interval and its source, completeness, membership, correction and
transition semantics and all reviewed-at facts remain unchanged; it cannot
rebind the historical policy selection. Only the selected
relationships are resolved; no raw roster or relationship catalog is retained
or monitored. An
`accepted-with-follow-up` outcome is allowed only for a non-blocking follow-up
with impact, owner, and due date. Every such GA review must bind an
immutable follow-up obligation identity, the source review and reviewed-evidence
identities, gate, launch scope, deployment class and family, impact, owner,
immutable origin time and audit sequence from the source review's `reviewed_at`
or AegisOps-assigned obligation creation, `due_at`, initial non-blocking
disposition, the current Accepted disposition/currentness-rule aggregate, head
and version, applicable maximum lifetime or cadence parameters, and the
deterministically calculated `maximum_follow_up_due_at`. That obligation must
reconcile
exactly once to an in-scope non-closed member of the authoritative
`known_limitation_ownership` current head, or an Accepted successor record
family, and the decision must prove
`decision_at < due_at <= maximum_follow_up_due_at` under the rule effective at
the immutable origin. A missing, historical, expired, revoked, superseded,
wrong-scope, ambiguous, or incomparable rule; a caller-selected deadline beyond
that maximum; or an in-place extension, anchor reset, or new-decision reset of
the original obligation does not count. A record may carry a
complete ordered obligation set rather than requiring one physical record per
obligation, but missing, duplicate, ticket-only, prose-only, owner-label-only, or
review, evidence, scope, class, family, owner, due-date, or disposition-mismatched
mapping does not count. A plain `accepted` review creates no obligation. Every
GA review must finish before the limitation snapshot and its independent review
are finalized; a later follow-up requires a new snapshot, exact reconciliation,
and review before the decision attempt can continue. Before decision creation,
AegisOps must materialize one immutable review-independence closure bound to the
exact independent-review set and count, the complete decision-used review-
outcome aggregate and head set, count and digest, and, for each review, the exact
reviewed-evidence identity and complete canonical producer set; for direct non-derived
evidence, its exact producer-attribution identity; for derived evidence, its
content-bound complete acyclic slice of the global producer closure containing
every direct and upstream material-source and transformation producer; the
authoritative reviewed-at ownership snapshot and exact owner set; the reviewer
and reviewed-at membership identities; the complete selected relationship-
proof aggregate/head set, count, digest and per-review mapping; the exact
relationship-policy dependency closure, policy aggregate/head/version set,
count, digest and relationship-to-policy mapping; the decision-scoped identity-
resolution head; and the complete ordered reviewer-
and-owner source-subject set, mapping results, count, digest, and audit high-water
mark.
This closure is separately bound
decision-control metadata, not an evidence-index member, and reviewer or owner
subjects enter the producer union only when their causal actions separately make
them producers. Independence is evaluated per review: the reviewer must be
absent from the producer set for that review's exact reviewed evidence. The
reviewer's authorship of the review attestation itself and production of derived
decision-control metadata are outside that predicate, while production of the
reviewed evidence is not. Routine source reviews may use the accountable operator only
when the governing Accepted profile permits it; they
remain in the exact set and cannot substitute for the required independent
aggregate or GA review. A missing or rejected independent review, a purported
independent review by the producer or owner, or a mismatched review blocks
acceptance.

### Decision-Time Mutable-State Cohort

GA-scope selection predecessor state; the current launch-scope-definition head,
deployment-class exact set, non-empty launch-eligible class subset, and expected
scope-class pair closure; GA-decision
lifecycle and expiry-policy state; journey-participant qualification lifecycle
and qualification-source policy plus the complete per-qualification actor-
separation mapping set: exact participant, issuer and acceptance-actor subjects,
the decision-bound policy version, applicable prohibited-role predicate, exact
prohibited-subject set/count/digest and source-proof/role mapping, and canonical
subject separation; the selected RC-proof-packet
aggregate/current head, packet-to-selected-result mapping, and packet-head/
result-review-and-initial-head authoritative sequence identities; journey-run
and one-time-execution primary-
outcome heads and exact closures; the separate owner-review aggregate/head
closure; every producer-attribution aggregate/head, governing attribution-
policy head and producer closure; every
reviewed-at ownership/membership relationship-proof head and review-independence
closure plus the exact selected relationship-policy dependency closure and
current policy heads; the exact deployment-profile and environment-
criteria dependency closure and selected current heads, journey environment-
observation, comparison, interval-proof and audit-high-water state and its exact
environment-evidence lifecycle aggregate/head closure, operability environment
observation, comparison, interval proof, equivalence and audit-high-water state
and its separate exact environment-evidence lifecycle aggregate/head closure,
plus the exact governing environment-source-policy dependency closure and
selected current policy heads;
and decision-used coverage-rule lifecycle and review state;
launch-operability requirements with its
required-component, applicability-matrix, claimed-capacity-boundary, material-
environment-boundary, referenced conservative-equivalence-rule, environment-
coverage-rule, cross-class-backup-reuse-rule and sequence-equivalence-rule,
supported-upgrade-path, and immutable credential-family-definition exact sets
and their exact source/target-applicability and path-edge mappings plus the
complete selected requirements tuple set and bidirectionally
reconciled requirements-separation closure set;
routine-
backup stable aggregate,
current head, profile or deviation, schedule, path, attempt,
material-configuration surface and independent history, reviewed-change
registry reconciliation, derived configuration-backup obligations, restore-
rehearsal schedule and currentness, custody, retention, evidence-cutoff, and
reviewed exact-set state, plus the separate concrete cross-class restore-target-
to-rule-review-and-source-backup mapping set mechanically derived by the
manifest and decision-input index and both strict rule/review/parent/target/run
and backup/integrity/review/target/run audit-order identities; routine operator-health stable aggregate, current head,
schedule, cutoff, review, finding, and follow-up state;
current credential policy lifecycle, assignment, rotation, custody, event,
cutoff, and break-glass state;
support and upgrade ownership heads and coverage closures; the authoritative
limitation-registry current head, dispositions, and current
disposition/currentness-rule head; every claimed
capability-scope-authority head; the
evidence-retention and resolvability head and, in current-lifetime mode, the
decision-input integrity-review aggregate and current head; the source-authoritative
decision-scoped identity-resolution head used for producer, approver,
selected approver-coverage-holder, independent-reviewer, reviewed-evidence-
owner, decision-time credential-custodian, requirements-approval-actor,
qualification-participant, qualification-issuer, qualification-acceptance-actor,
policy-prohibited-qualification-principal, selected
root-holder, root-governance-approval-actor, and assignment-or-delegation issuer and grantee
canonicalization; the
review-independence closure and complete decision-used review-outcome aggregate
and current-head closure; the profile-derived GA-approver-ownership coverage
closure and selected holder authority heads; and release-authority root and
chain state form one decision-time mutable-state
cohort. Each family must expose an
AegisOps-owned current-state head or immutable snapshot bound to the stable
canonical gate-definition and intended launch-scope identities, the per-decision
gate-record identity where applicable, evidence revision, effective status or
interval, predecessor and current lifecycle identities, review identity and
time, and authoritative audit high-water mark. The decision event must bind one
immutable cohort identity, the expected scope-head predecessor, current
launch-scope-definition, class-set and launch-eligible-subset identities,
expected pair-closure
identity, deployment-profile and environment-criteria dependency-closure
identity, journey and operability environment-evidence lifecycle-closure
identities, environment-source-policy dependency-closure identity and selected
current policy-head identities, journey-run and one-time-execution primary-
outcome-head-set identities, owner-review-head-set identity, producer-
attribution-head-set and producer-closure identities, reviewed-at relationship-
head-set and review-independence identities, selected RC-proof-packet aggregate/
head, packet-to-result mapping and packet-before-result audit-order identities,
review-outcome-closure identity,
decision-used journey-
coverage rule-head-set identity, GA-approver-ownership coverage-closure identity,
requirements-separation tuple-set and closure-set identities, identity-resolution current head, and
its bound source snapshot; the resulting scope head binds the decision identity.
For no-automatic-expiry, the cohort must also bind the retention compatibility
rule head, selected mode, and current-lifetime integrity-review aggregate, head,
authoritative decision-time coverage and first-slot anchors, cadence, due-slot
and attempt/result/review-outcome aggregate/current-head exact sets and slot
mappings, next-due boundary, or the
deterministic cutoff, first expiry-eligibility and effective invalidation
boundaries, required
transition kind and authority, and deletion fence. A later
pre-cutoff-invalidation transition must atomically bind those original values,
its commit identity and sequence, and the advanced canonical scope head; it
cannot change the mode or cutoff of the existing decision.
The specialized launch-scope class and pair closures, journey qualification and
chronology, backup and upgrade-path exact sets, required-component, material-
environment-boundary and applicability-matrix reconciliation, limitation exact
set and review-follow-up
current-head requirements, immutable credential definitions and mutable
event-stream separation, review-outcome, review-independence and journey-rule lifecycle
closures, support and upgrade ownership coverage closures, profile-derived
approver coverage, policy governance,
evidence durability, capability-scope authority, and release-authority root-and-chain
requirements remain additive.

Each support and upgrade ownership head must identify the attributable current
owner, ownership family, covered class set and support or upgrade scope,
assignment provenance, effective interval, immutable head identity, and audit
sequence, and must be effective, unrevoked, non-retired, and independently
reviewed. A class-specific head must name its exact class. A family-specific
scope-wide head must bind the canonical launch-scope identity and exact
deployment-class set identity, count, and digest. A plan, bundle, ticket, or
owner label is subordinate evidence and cannot establish current ownership. A
missing, removed, expired, or superseded owner blocks GA until a replacement
head and independent review enter a new decision attempt.

At decision time, AegisOps must derive separate immutable support-ownership and
upgrade-ownership coverage closures from the authoritative deployment-class
set. Each `(ownership family, deployment class)` cell must map to exactly one
selected current head. A class-specific head may satisfy only its named class;
one scope-wide head may satisfy every cell for its family only when its exact
class-set binding matches. A scope-wide selection cannot overlap a selected
class-specific head. Each closure binds the complete cell set, count, and
digest, the unique selected-head set, count, and digest, and the exact mapping.
Missing, duplicate, overlapping, extra, wrong-family, wrong-class, wrong-scope,
alias-split, stale, revoked, retired, superseded, or unreviewed coverage blocks
GA. The same accountable person or team may cover multiple classes or both
families, and the number of selected heads need not equal the class count, but
support and upgrade coverage must each be complete.

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
For every journey, independent records must likewise prove
`declaration_at < journey_started_at <= journey_completed_at <= journey_owner_reviewed_at <= decision_at`.
Every other decision-bound reviewed evidence record must prove
`observed_at <= owner_review_at <= decision_at`. These orderings require
AegisOps append-only audit sequencing or an equivalent independently timestamped
attestation. Any source contract's clock-skew tolerance applies only while
verifying its subordinate observation or review evidence; it cannot move
`decision_at`, permit evidence after the decision, or replace commit-time cohort
reconciliation.

The following maximum ages are measured backward from `decision_at`. A maximum
age never overrides a revision mismatch; the required action applies after
either expiry or a mismatch:

| Evidence family                                                                                                                                                                                                                                                  | Maximum age                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Required action after expiry or revision mismatch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Inherited Phase 66 RC evidence set: Phase 66.7 packet plus Phase 66.8 closeout result or authoritative RC-gate result                                                                                                                                            | Packet regeneration and independent closeout or gate-result evaluation and focused revalidation must complete within 24 hours. The selected result's decision-bound review-outcome aggregate and complete current chain must also resolve without cached age at every `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Regenerate the packet and independently re-evaluate and revalidate the closeout or authoritative gate result at the gate evidence revision; every native observation, review, and decision rule must pass. A corrected, retracted, rejected, revoked, expired, superseded, forked, gapped, mismatched, historical or replacement selected result returns `unavailable` and requires a new independently accepted RC result and GA decision.                                                                                                                                                                                                                                                                                                                                                                                                 |
| Real-user or design-partner GA journey records                                                                                                                                                                                                                   | Each required journey completion and its exact immutable `accepted` or valid non-blocking `accepted-with-follow-up` owner review must be no more than 720 hours old; each claimed participant's qualification record and the exact journey-environment observation and comparison must have been accepted before start, with qualification and an authoritative no-material-change or gap-free interval proof covering the same environment through completion.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Repeat each affected journey family for every mapped deployment class at the gate evidence revision with a pre-run declaration envelope, valid participant qualification, exact accepted owner review and full environment-interval proof, or predeclare and independently accept a new journey-coverage rule before its valid source journey. A missing, mismatched, unknown, not-reviewed or rejected owner review, post-run point observation, gap, environment swap or material mid-run change requires a new observation, declaration, journey, and review; owner relabeling or post-run qualification cannot refresh it.                                                                                                                                                                                                              |
| Routine cadence-driven backup stream                                                                                                                                                                                                                             | One reviewed gap-free window must end at `evidence_cutoff_at`, span at least one full Accepted profile review interval, and reconcile every due or overlapping item and attempt; zero-delta commit reconciliation must bridge the cutoff to `decision_at`. At every `evaluated_at`, the same stable backup aggregate, independent material-configuration history, reviewed-change registry, derived configuration-backup obligations, and their complete successor chains and high-water marks must resolve without cached age.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | An on-time, accepted, no-weaker same-aggregate successor may pass. Missing, forked, gapped, omitted, late, overdue, failed, hidden, unresolved, weaker, unregistered or reverted transition, wrong-order change backup, or replacement state returns `unavailable`. Re-establish and review a new complete gap-free window and make a new decision; late evidence, an older-window splice, one-off backup, verifier rerun, or reattestation cannot cure the miss.                                                                                                                                                                                                                                                                                                                                                                           |
| Routine operator-health and platform-hygiene stream                                                                                                                                                                                                              | One reviewed gap-free window must end at `evidence_cutoff_at`, span the longest applicable Accepted profile review interval, and reconcile every due or overlapping review, finding, escalation, and follow-up; zero-delta commit reconciliation must bridge it to `decision_at`. The same stable aggregate and complete successor chain, including every time-derived due or open obligation, must resolve without cached age at every `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | An on-time, accepted, no-weaker same-aggregate successor may pass. Missing, forked, gapped, omitted, late, overdue, rejected, unreviewed, carried-open, unresolved, weaker, or replacement state returns `unavailable`. Re-establish and independently review a new complete gap-free window and make a new decision; one fresh diagnostic, verifier rerun, or reattestation cannot cure a missed interval.                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Capacity, component-interruption and recovery, clean-target restore, exact-version upgrade and rollback, and any claimed HA, disaster-recovery, or fleet-scale execution                                                                                         | Each execution completion and its exact immutable accepted or valid non-blocking accepted-with-follow-up owner review must be no more than 720 hours old for admission, and each deployment class must retain at least one exact compatible supported upgrade path with successful upgrade and rollback evidence. In addition, each class's clean-target restore schedule, currentness rule, complete successor chain, and every due or open slot must be reconciled against the Accepted profile without cached age at every `evaluated_at`; this does not add cadence to the other heavy families.                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Rerun each affected family for every bound class and affected compatible upgrade path at the gate revision when the admission cap expires. An empty or zero-count supported set blocks. For restore, an on-time successful reviewed same-aggregate successor may pass and a future slot is nonblocking; a missing, late, failed, unreviewed, wrong-source, wrong-revision, or wrong-target due slot returns `unavailable` and requires a new compliant restore window, rehearsal, review, and decision. A verifier rerun or reattestation cannot cure it.                                                                                                                                                                                                                                                                                   |
| Monitoring, diagnostic, support-bundle, and redaction execution                                                                                                                                                                                                  | Each execution completion and its exact immutable accepted or valid non-blocking accepted-with-follow-up owner review must be no more than 24 hours old.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Regenerate the artifacts and rerun the affected checks at the gate evidence revision for every bound deployment class; a missing, mismatched, not-reviewed, unknown or rejected owner review cannot be refreshed by time alone.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Decision-used journey and one-time execution primary-run and subordinate owner-review lifecycle                                                                                                                                                                  | The exact primary-run and owner-review aggregate/head closures must resolve at `decision_at` and without cached age at every `evaluated_at`, with bidirectional index/manifest/run/review mappings and complete chains, sets, counts and digests. Existing canonical routine-stream lifecycle heads are reused rather than double-wrapped.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | A semantics-preserving same-aggregate successor may pass. A corrected, withdrawn, revoked, expired, rejected, superseded, forked, gapped, mismatched, cached favorable non-head or replacement run or review returns `unavailable`; invalid primary facts require a new run, owner review and decision, while a review-only invalidation requires a new review and decision unless freshness independently requires rerun.                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Producer-attribution and reviewed-at ownership/membership relationship currentness                                                                                                                                                                               | Every exact root and reachable provenance node in the decision-input and currently consumed-review partitions must reconcile to its attribution aggregate/head and governing attribution-policy head; every selected review-relationship aggregate/head and governing ownership-source or group-resolution policy head must also resolve with complete chains and source high-water marks at `decision_at` where decision-bound and every `evaluated_at`. The exact partitions and union, current decision-input producer closure, per-consumed-review producer slices, reviewed-at owner/membership posture and their separate current identity mappings must be rederived in the same current-read boundary.                                                                                                                                                                                                                                                                                                                                                                | Missing, extra, duplicate, forked, gapped, stale, corrected, retracted, withdrawn, expired, revoked, superseded, mismatched or replacement attribution, relationship or policy state, a newly discovered or omitted producer, changed reviewed-at owner set or membership, governing-policy semantic change, or affected separation predicate returns `unavailable` and requires the applicable approval, review or decision. Semantics-preserving same-aggregate successors, future-only relationship changes and unrelated monotonic high-water advancement may pass when the exact source, causal, policy and reviewed-at facts remain unchanged; future, unconsumed and unrelated provenance remains outside the partitions.                                                                                                            |
| GA lifecycle and expiry-policy current heads                                                                                                                                                                                                                     | Their current-head snapshots must be no more than 24 hours old and be resolved inside each decision or transition commit cohort; the original accepted approval may be older.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Re-resolve every applicable current head and rebuild the cohort. A mismatch, revocation, expiry, or supersession blocks the decision or transition; an older Accepted policy cannot authorize it.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Launch-scope and launch-operability current heads                                                                                                                                                                                                                | The scope-definition and requirements current-head snapshots and bound non-empty class set, non-empty customer-deployment or small-production-eligible subset, pair closure, and child exact sets, including every claimed-capacity and material-environment boundary, referenced conservative-equivalence and environment-coverage rule, cross-class-backup-reuse applicability tuple-to-rule mapping, sequence-equivalence path-edge mapping, and non-empty supported-upgrade-path set, must be no more than 24 hours old at target declaration and be resolved again inside the decision-time cohort. The separate concrete restore-target-to-rule-review-and-source-backup mapping derived by the manifest and decision-input index must be complete at decision and resolve without cached age with the exact decision-bound requirements heads and sets at every `evaluated_at`.                                                                                                                                                                                        | Re-resolve the scope-definition head, exact class, eligible-subset and pair closures, requirements heads, child rule sets and applicability/path-edge mappings, and the separate concrete restore-target mapping. A Lab-only, empty eligible subset, empty material-variant or supported-path set, missing, extra, duplicate, post-hoc, unavailable, scope, class, applicability tuple, concrete target, source backup, hop-edge, requirement, component, matrix, capacity or environment boundary, equivalence, coverage or reuse rule, path, compatibility, migration, rollback, lifecycle, parent-head or replacement mismatch returns `unavailable` and requires new declarations, targets, affected reruns, and a new decision; only temporary recovery of the same exact state may pass.                                              |
| Credential lifecycle, rotation, custody, and break-glass state                                                                                                                                                                                                   | A reviewed gap-free policy-versioned window must end at `evidence_cutoff_at`; the immutable requirements family-definition set and current manifest family set must match, current assignment and custody heads must be no more than 24 hours old, and zero-delta reconciliation must bridge the cutoff to `decision_at`. The same stable lifecycle aggregate and complete successor chain must resolve without cached age at every `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Re-resolve the complete policy lifecycle and every event exact set. A post-target event updates only the current snapshot; a post-cutoff delta forces a new snapshot and review. A later routine successful successor may support current status, but missing, forked, gapped, omitted, overdue, failed, open, unreviewed, weaker, or replacement state returns `unavailable`; only a definition or governing-obligation change requires a new target and affected rerun.                                                                                                                                                                                                                                                                                                                                                                   |
| Deployment-profile and environment-criteria lifecycle plus journey and operability environment-evidence and governing source-policy lifecycle                                                                                                                    | The exact decision-used profile and criteria dependency closure and heads plus each immutable environment snapshot, material-variant mapping, accountable review, separate journey and operability environment-evidence aggregate/head closure, and governing source-policy dependency closure and heads must be no more than 24 hours old at declaration or target and `decision_at`. Every selected profile, criteria, observation, comparison, change-history proof, interval-attestation and governing policy aggregate's complete chain, source-authoritative current head, and source or policy high-water mark must resolve without cached age at every `evaluated_at`. Each journey and operability execution must prove its applicable pre-start comparison plus no material change through completion or a predeclared authoritative attestation covering its full interval.                                                                                                                                                                                        | Re-resolve every selected profile, criteria, environment-evidence and governing source-policy current head, material-environment boundary and mapping, coverage rule, and authoritative environment state. Temporary unavailability or a semantics-preserving same-aggregate successor may recover; a policy expiry, revocation, supersession, source-authority or transition-semantic change, or evidence correction, challenge, withdrawal, revocation, invalidating supersession, fork, gap, cached favorable non-head, replacement, source-version or interval mismatch requires a new observation, declaration or target, affected rerun, review, and decision. Unrelated or post-completion observations and monotonic source high-water advancement that preserve the selected chain and historical interval do not block.           |
| Journey qualification lifecycle and source-policy heads                                                                                                                                                                                                          | Each qualification must cover its journey interval at `decision_at`; the same decision-bound qualification and policy aggregates and their complete current lifecycles must resolve without cached age at every authoritative `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Return `unavailable` for an unavailable, missing, forked, gapped, authority-mismatched, self-issued, or retroactively invalidated interval until new journey evidence and a new decision exist. Recovery or a valid same-aggregate successor is allowed only when it preserves the executed interval; a normal post-completion relationship end or future-only policy successor does not expire the evidence.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Decision-used journey-coverage rule lifecycle heads                                                                                                                                                                                                              | The exact used-rule aggregate and head set must resolve in the decision cohort and without cached age at every authoritative `evaluated_at`; direct per-class journeys and unused rules are excluded.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | A temporary read failure returns `unavailable` until the same valid head resolves. A future-only same-aggregate successor may pass only when every executed-interval and decision binding remains unchanged; correction, revocation, expiry, invalidating supersession, fork, gap, mismatch, or replacement requires a valid predeclared rule, affected journey coverage, and new decision.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Decision-used review-outcome lifecycle heads and evaluated-at consumed-review control closures                                                                                                                                                                   | The complete decision-bound aggregate and head set, including the selected inherited RC acceptance result, must resolve in the decision cohort and without cached age at every authoritative `evaluated_at`; a later routine successor's consumed-review control closure must separately and one-to-one resolve the exact outcome set mechanically derived from all resolved post-decision successor chains and due or open obligations, plus reviewed-evidence producer closure, reviewed-at owner and membership proofs, current identity mappings and per-review independence result, only when that successor is consumed.                                                                                                                                                                                                                                                                                                                                                                                                                                                | A temporary read failure returns `unavailable` until the same valid chain and control closure resolve. A missing, extra, duplicate, omitted or relabeled review, set, count or digest mismatch, missing or overlapping independence evidence, or correction, retraction, rejection, revocation, expiry, supersession, fork, gap, mismatch, favorable non-head selection or replacement requires a new applicable review or RC result, review-independence closure and decision rather than in-place rebinding; an Accepted rule that requires no independent review creates no member.                                                                                                                                                                                                                                                      |
| Authoritative limitation-registry current head                                                                                                                                                                                                                   | The decision-bound snapshot and review must be no more than 24 hours old at `decision_at`; every GA review follow-up must map exactly once into it and bind an immutable origin plus current Accepted disposition/currentness-rule head proving `decision_at < due_at <= maximum_follow_up_due_at`; and the exact heads plus time-derived review, maximum-deadline and disposition posture must be re-resolved without cached age at every authoritative `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | A temporary read failure returns `unavailable` until the same valid heads resolve. A missing, historical or mismatched rule or review obligation, over-maximum or reset deadline, in-scope record or head change, or an unchanged head crossing its cadence, due-date, or next-invalidation boundary into an overdue, expired, or blocking posture requires a new decision and complete evaluation; cached or replacement state cannot be rebound.                                                                                                                                                                                                                                                                                                                                                                                          |
| Acting-approver, approver-coverage-holder, requirements-approval-actor, producer, reviewer, owner, credential-custodian, root-holder, root-approval-actor, issuer, and grantee identity resolution plus requirements-separation and review-independence closures | The exact decision-scoped historical head and snapshot must remain retrievable. At every authoritative `evaluated_at`, the source-authoritative current head must re-canonicalize the complete fixed decision-bound subject set, the exact current attribution-derived producer sets for the decision-input and each currently consumed-review partition, and each current-successor custodian set, and bind its snapshot, high-water mark, origin-tagged separate exact sets, counts, digests, and mappings; the complete requirements tuple set must reconcile bidirectionally one-to-one with its closure set, and per-tuple requirements-author, target-author and exercise-producer slices and per-review producer, owner, and reviewed-at membership proofs remain additive.                                                                                                                                                                                                                                                                                            | A temporary read failure returns `unavailable` until valid state resolves. A tuple/closure missing, extra, duplicate, substitution, count, digest or mapping mismatch; fixed or current-producer subject omission, substitution, remap or alias conflict; requirements approval actor overlap with its decision-input requirements-author, target-author or exercise-producer slice; approver-producer, root-approver/root-holder, issuer/grantee or canonical-cycle conflict; or per-review independence violation within that review's exact producer partition requires a new applicable approval, target, rerun, review or decision and cannot be rebound. Current-head advancement alone may pass, and it may map a no-weaker same-aggregate custodian successor only when all fixed and current sets remain complete and valid.       |
| Profile-derived GA-approver-ownership coverage closure and holder authority heads                                                                                                                                                                                | The exact closure must satisfy each decision-bound profile minimum at `decision_at`, and its holder subjects, authority chains, and heads must resolve without cached age at every authoritative `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Below-minimum coverage, alias collapse, acting-approver non-membership, or missing, revoked, expired, superseded, wrong-scope, forked, gapped, or replacement holder state returns `unavailable` and requires a new decision; it cannot be repaired by a second signature or in-place substitution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Release-authority root-governance and complete assignment/delegation chain                                                                                                                                                                                       | The exact decision-bound root provenance, root-governance aggregate/current head, complete authority-chain aggregate/head set, count, digest and high-water mark, and current canonical mappings of the selected root holder, root approval actor, issuers and grantees must resolve without cached age at every authoritative `evaluated_at`; external charter bytes remain version-bound provenance rather than a live database participant.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Temporary unreadability returns `unavailable` until the same valid chain and mappings resolve. Missing, forked, gapped, expired, revoked, superseded, scope-widened, root, issuer, grantee or provenance-mismatched, alias-collapsed, canonical-cycle, cached, or replacement state returns `unavailable` and requires a new complete authority and identity evaluation and GA decision; durable decision-state mutation still uses its authorized lifecycle transition.                                                                                                                                                                                                                                                                                                                                                                    |
| Support and upgrade ownership coverage closures and current heads                                                                                                                                                                                                | Each family closure must cover every authoritative deployment class exactly once at `decision_at`; every selected head must be no more than 24 hours old and the closure and heads must be re-resolved without cached age at every authoritative `evaluated_at`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | A temporary read failure returns `unavailable` until the same complete mapping resolves. Missing, duplicate, overlapping, extra, wrong-family, class, or scope coverage, or removal, expiry, retirement, reassignment, supersession, review, or replacement-head mismatch requires a new decision and complete evaluation; it cannot be rebound in place.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Claimed HA, disaster-recovery, or fleet-scale capability-scope-authority heads                                                                                                                                                                                   | Each current head must be resolved at target declaration, inside the decision-time cohort, and again for current-status evaluation; the underlying approval may be older.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | A missing, narrowed, expired, revoked, superseded, or mismatched head invalidates the target and current claim; restoration requires a new decision, not rebinding.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Evidence-retention, resolvability, and retention-compatibility current heads plus immutable decision-input closure                                                                                                                                               | No cached age is accepted. All current heads and exact evidence must resolve at `decision_at` and every authoritative `evaluated_at`; current-lifetime mode must create its initial integrity-review head in the decision cohort with `coverage_start = decision_at`, derive its first slot and next due from the Accepted cadence, and resolve that aggregate's complete successor chain, every due or open slot, attempt, result and authoritative review-outcome aggregate/current head against the complete input closure, while pre-cutoff mode retains its invalidation posture. Each post-decision slot must prove result completion before the accepted review-outcome initial head, that head before the integrity-parent successor, and the parent successor by the evaluated-at read boundary. A cadence-designated independent slot review must also enter the exact currently consumed set with its complete slot/cadence origin-edge set, count and digest and pass complete producer/owner/membership/current-identity independence control in that same read. | Return `unavailable` for a future, delayed, replaced, or reset coverage or first-slot anchor, missing, extra, wrong-origin or stale required consumed-review control, reviewer-owner/producer overlap, pre-result or wrong-order review, unadvanced parent, or an omitted, late, failed, unreviewed, partial, wrong-input, duplicate, cross-slot, weaker, corrected, retracted, rejected, revoked, expired, superseded, cached-favorable, outcome-mismatched, or replacement integrity-review state, or until the exact reviewed evidence, review-outcome and current rule heads and posture are verified. A late verification or review, historical most-recent result, favorable review bytes, rule, hash, URL, cache, partial set, post-deletion substitute, or unapproved unbounded-retention assertion cannot refresh or replace them. |
| Selected Phase 66.7 RC-proof-packet evidence lifecycle and packet-to-result mapping                                                                                                                                                                              | Packet regeneration, independent closeout or gate-result evaluation and focused revalidation must complete within 24 hours. The exact selected packet aggregate/current head, packet-input closure, source high-water mark, selected-result head and packet-to-result mapping must resolve in the decision cohort and without cached age at every `evaluated_at`, with authoritative `packet selected-head commit < independent RC-result review-and-initial-head commit < GA decision` ordering.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Temporary unreadability returns `unavailable` until the same complete valid packet and result chains resolve. A review over a future or reserved-only packet head, equal/reversed/backdated packet-result order, material correction, withdrawal, revocation, invalidating supersession, fork, gap, cached favorable non-head, replacement, or packet-to-result mismatch requires a new packet, independently accepted RC result and GA decision; a metadata-only same-aggregate successor may pass only when every packet, revision, input and result binding remains exact.                                                                                                                                                                                                                                                               |
| Qualification issuer, acceptance-actor and prohibited-principal identity and separation                                                                                                                                                                          | Every claimed qualification must bind exact attributable issuer and acceptance-actor subjects and one complete per-qualification actor-separation mapping member containing the decision-bound policy version and applicable prohibited-role predicate, exact prohibited source-subject set/count/digest and source-proof/role mapping. The decision-time and evaluated-at current identity heads must canonicalize that immutable historical exact set without cached age; a future-only policy successor may pass only when it does not retroactively change the applicable predicate, completeness semantics, or mapping.                                                                                                                                                                                                                                                                                                                                                                                                                                                  | A missing, extra, duplicate, wrong-policy or wrong-qualification slice, role- or group-label-only, ambiguous, substituted, stale, remapped or alias-collapsed actor, mutable/incomplete source proof, or participant overlap with its mapped issuer, acceptance actor or prohibited principal returns `unavailable` and requires new valid journey evidence and a new decision. Historical sets cannot be rederived from a newer policy head; issuer and acceptance actor need not be mutually distinct unless the decision-bound Accepted policy requires it.                                                                                                                                                                                                                                                                              |

Cross-class backup-reuse freshness also requires the bound authoritative audit
order `rule content < independent review and initial outcome head < accepted
rule child and requirements parent < restore target < execution` and the
separate order `backup completion < integrity pass < accepted backup review <
restore target < execution`. A reserved-only or future review or backup, equal,
reversed, same-sequence, backdated, or post-target materialization is
a mismatch rather than fresh evidence.

A material version, topology, configuration, route, selected environment-source-
policy authority or transition-semantic change, or execution-interval
environment-evidence correction, challenge, withdrawal or invalidating
supersession, journey or one-time execution primary-run outcome, artifact or
head, subordinate owner-review identity, head or disposition, producer-
attribution set, causal closure, head or governing policy, reviewed-at ownership/
membership relationship proof, head or governing ownership-source or group-
resolution policy, journey rule,
criterion, participant qualification, qualification issuer/acceptance-actor
mapping, decision-bound prohibited-role predicate, prohibited-subject source
proof/set/count/digest or canonical separation, or qualification-source policy, GA-scope
head, launch-scope-definition head, deployment-class membership or launch-
eligibility posture, GA lifecycle
or expiry-policy head,
accepted deployment-profile or environment-criteria lifecycle head or semantics,
backup or operator-health cadence or deviation, conservative, environment,
cross-class-backup-reuse or sequence-equivalence criterion or child mapping,
launch-operability requirements, required-component set, applicability matrix,
claimed-capacity or material-environment boundary, conservative-equivalence or
environment-coverage rule, supported-upgrade-
path head, compatibility, migration, rollback target,
requirements tuple set, separation closure set or requirements-approval-actor
mapping,
credential policy, scope, custody or break-glass state, claimed-capability
scope-authority head, decision-used journey-coverage rule lifecycle,
selected RC-proof-packet lifecycle or packet-to-result mapping, decision-used
review-outcome lifecycle or currently consumed review-control closure, profile-derived
approver coverage, decision-bound reviewer, owner, custodian, or
group-membership identity resolution,
evidence-retention, resolvability, current-lifetime integrity-review state or
slot-bound review-outcome head/mapping,
owner, limitation-registry or disposition/currentness-rule head or disposition,
or
release-authority root-governance or assignment/delegation-chain change invalidates the affected evidence even inside its
maximum-age window.

For credential evidence, an observed rotation, break-glass, assignment,
custody, or event-lifecycle delta invalidates the current snapshot, cutoff, and
review but does not by itself invalidate an otherwise matching pre-run target or
execution. A change to the immutable credential-family definition or governing
policy, cadence, trigger obligation, or required result schema is a requirements
change and does invalidate the affected target and execution.

The decision-time cohort maximum ages do not replace its serialization boundary
through atomic decision creation. Authoritative current-status evaluations and
projections also have no cache-based grace period: each must re-resolve the
canonical scope and selected-decision heads, lifecycle and expiry-policy heads,
the exact decision-bound launch-scope-definition, deployment-profile and
environment-criteria dependency closure, non-empty launch-eligible subset and
selected lifecycle heads, the separate exact journey and operability environment-
evidence lifecycle closures, complete successor chains, source-authoritative
current heads and high-water marks, and the exact governing environment-source-
policy dependency closure, selected policy chains and current heads,
journey-run and one-time-execution primary-outcome closures, subordinate owner-
review closure, both exact root-and-reachable-node producer-currentness
partitions and their union, every selected producer-attribution and governing
attribution-policy current head, the rederived current decision-input producer
closure and per-consumed-review producer slices, and every selected reviewed-at
ownership/membership relationship-proof and governing relationship-policy
current head,
scope-class requirements pair closure, every launch-operability requirements
head and child exact set, including selected cross-class-backup-reuse and
sequence-equivalence rules and exact source/target-applicability and path-edge
mappings, plus the separate concrete restore-target-to-rule-review-and-source-
backup mapping from the manifest and decision-input index, selected requirements tuple set and bidirectionally
reconciled requirements-separation closure set,
limitation-registry and disposition/currentness-rule
heads, every decision-bound routine-
backup and operator-health stable aggregate and current successor head, every
backup-bound independent material-configuration-history and reviewed-change-
registry head, derived change-backup obligation closure, and restore-rehearsal
schedule and currentness rule,
participant qualification-lifecycle and governing source-policy heads plus the
complete per-qualification issuer/acceptance-actor, decision-bound policy-
predicate and exact prohibited-subject source-proof/role mapping sets, counts,
digests and canonical separation predicates, the selected RC-proof-packet chain/
current head, packet-to-result mapping and decision-bound audit order,
decision-used journey-coverage rule and review-outcome lifecycle heads plus any
currently consumed successor-review control closure,
claimed-capability heads, each decision-bound credential-lifecycle aggregate
and current head, the exact decision-scoped historical identity-resolution head,
the current identity-resolution head used to re-canonicalize its exact fixed
subject set, including qualification issuers, acceptance actors and prohibited
principals, both attribution-derived current producer partitions, and any
current-successor credential-custodian set, producer and
review-independence closures, the profile-derived
approver-coverage closure
and holder authority heads, the root-governance head and complete assignment and
delegation-chain heads, exact decision-bound support and upgrade ownership heads,
their coverage closures, immutable input closure, evidence-retention head, and
the current-lifetime integrity-review aggregate, successor head, and exact slot-
bound review-outcome aggregate/current-head mappings and result/review/parent/
evaluated-at audit order plus, where cadence requires independence, exact slot/
cadence-version origin edges into the currently consumed set and complete
`consumed_review_control` where
applicable, and their audit high-water marks at its own `evaluated_at`.
That `evaluated_at`, read sequence, fence or linearization identity, and the
resolved-through high-water marks must be assigned and bound by the same current-
read boundary; a caller time, historical `as_of`, or cached result has no current
authority.

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

This proposal does not change the accepted baseline or its verifiers. Human
approval authorizes the separately scoped implementation work but does not by
itself activate the Phase 67 mapping or release semantics in this decision. The
ADR's Activation must remain `Deferred` and its Activated By and Effective Date
metadata must remain pending, and the accepted
Phase 51.3 baseline remains the sole governing mapping, until one coordinated
implementation revision atomically updates that baseline and its verifiers and
changes this ADR's Activation to `Active` with attributable activation metadata.
The first default-branch revision whose final tree contains all of those changes
is the activation identity. A repository state with this ADR marked `Active` but
either baseline, focused verifier, or authoritative consumer still enforcing the
prior mapping, or with the new mapping present while Activation remains
`Deferred`, is invalid and must fail release review. The ADR status and real
approval metadata must still be updated together under the review path before
that separate implementation pull request may be accepted.

## 3. Decision Drivers

- prevent bounded lab evidence from being overstated as GA acceptance,
- keep gate decisions revision-bound, content-bound, and auditable,
- introduce explicit authorized-human accountability, a verifiable authority
  chain, and separation of duties for GA acceptance,
- make unqualified or incomplete real-user journey and deployment-class
  coverage, operability evidence, support, upgrade, and current limitation state
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
reviewable. Binding every exact input to a source-authoritative, complete causal
producer closure prevents owner, reviewer, or alias labels from manufacturing
that separation. Per-review canonical reviewer-to-authoritative-owner and
owner-group-membership checks preserve the same independence for evidence
review. Profile-derived approver coverage
preserves small-production staffing redundancy without turning one accountable
GA decision into dual approval. Requiring an effective, scope-bound
release-authority record also prevents an unrelated human or an action-approval
role from accepting GA.
Resolving every reference to immutable content and requiring an explicit
decision event prevents a mutable artifact or assigned identity from being
mistaken for acceptance. The 720-hour journey and heavy-exercise window aligns
with the reviewed monthly restore and maintenance cadence, while the 24-hour
packet, diagnostic, and input-state window retains the stricter Phase 66.6 and
66.7 precedent for rapidly changing evidence. Authoritative current GA status is
instead re-resolved for each evaluation or projection without a cache-based
grace period. Assigning `evaluated_at` at that current read's own linearization
boundary prevents a caller-selected historical instant from omitting a later
revocation, expiry, or newly due obligation while presenting the result as
current.
Fixed windows and explicit expiry actions prevent each implementation from
choosing its own definition of stale evidence. Requiring an accepted
scope-authority reference also keeps successful technical exercises from
silently expanding the product boundary.
Binding each exercise target to independently accepted launch requirements
prevents a producer from satisfying the gate with a vacuous benchmark.
Canonical per-tuple requirements separation prevents an approval actor from
self-approving requirements, targets, or exercise evidence through aliases
without requiring four different people. Resolving
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
to its exact compatibility record and successful rehearsal, with at least one
such path per class, prevents an arbitrary or empty version set from standing in
for launch-scope coverage. Predeclared
journey comparisons, complete component and applicability sets, and continuous
health and credential-lifecycle streams prevent class labels, cherry-picked
components, meaningless metrics, or a last-minute check from standing in for
launch operability. Binding each claimed participant to a pre-existing
source-authoritative qualification record prevents an owner, employee, or lab
label from standing in for real-user or design-partner use. Canonicalizing the
attributable issuer and qualification-acceptance actor against the participant
prevents a second source alias from self-issuing that qualification without
inventing a two-person or two-signature rule. Binding the exact policy predicate
and prohibited-subject source proof per qualification prevents omission or
cross-policy over-application without retroactively applying a future-only policy
change. Binding the same
journey environment observation and comparison through completion prevents a
pre-start compliant snapshot from hiding a material mid-run departure. Deriving every
family and operability pair from one authoritative launch-scope class set
prevents a supplied subset from defining its own completeness, while requiring a
non-empty customer-deployment or small-production-eligible subset prevents an
internal Lab-only exercise scope from accepting GA. Re-resolving the
exact launch-scope and limitation-registry heads for every current projection
prevents later class or limitation changes from being hidden behind the
decision-time snapshot. Complete ownership closures prevent an uncovered class
from inheriting an unrelated owner label, and mapping review follow-ups into the
same limitation currentness rules and their accepted maximum deadlines prevents
an overdue or arbitrarily distant promise from remaining silently non-blocking.
Re-resolving the exact requirements children and stable
backup and health streams prevents a long-lived decision from surviving a
revoked launch envelope or later cadence gap. Exact claimed-capacity boundaries
prevent a top-of-range environment from proving an untested resource floor;
making every referenced equivalence rule an inseparable requirements child
prevents a revoked rule from surviving through a historical reference.
The material-environment boundary prevents the easiest allowed OS, architecture,
or topology tuple from silently proving every materially different supported
variant without inventing an unapproved Cartesian product.
Re-resolving only the selected profile and criteria lifecycle heads prevents an
obsolete launch envelope from governing current capacity, cadence, approver, or
custody claims without monitoring the entire profile catalog. Binding an
operability comparison to the target and full execution interval prevents a
post-run compliant snapshot from describing an earlier noncompliant run, while
re-resolving only the exact selected environment-evidence and governing source-
policy chains exposes later correction, withdrawal or policy-authority change
without monitoring an environment or policy catalog. Binding each
journey and execution's accepted owner-review disposition prevents a passing
machine result from overriding its accountable owner's rejection, while
re-resolving the primary-run and subordinate-review heads prevents a later
authorized correction or retraction from being hidden behind immutable favorable
bytes. Re-deriving producer attribution and reviewed-at relationship proofs from
their exact current heads exposes omitted producers, co-owners or retroactive
group-membership corrections without monitoring unrelated audit or directory
catalogs.
Continuing the profile-derived restore schedule and independent configuration-
history reconciliation prevents a no-automatic-expiry decision from surviving a
missed restore or hidden material change while leaving other heavy exercises and
ordinary workflow records outside that cadence. Predeclaring and lifecycle-
binding only the exact cross-class backup-reuse mappings prevents a successful
restore from being qualified after the fact without imposing a rule on same-
class restores or unused class pairs. Likewise, lifecycle-binding only the
sequence edges that need an equivalence predicate prevents corrected or revoked
hop assumptions from outliving their requirements head without requiring rules
for exact adjacency.
Separating the immutable historical identity snapshot from the current identity
head that re-canonicalizes both its fixed subjects and later credential
successors detects retroactive alias collapse while permitting legitimate
custodian turnover, and canonical custodian identities preserve profile-required
secret-custody staffing without creating dual approval. Separating immutable
credential obligations from observed
events preserves target validity while the reviewed cutoff still captures every
routine event. A reviewed evidence cutoff plus commit-time zero-delta check
keeps those streams current without holding a transaction open for human review.
Current review-outcome, inherited-RC, root-governance, and complete authority-
chain resolution prevents immutable but later withdrawn acceptance or authority
from remaining a favorable current projection. Giving the exact selected Phase
66.7 packet its own current Evidence lifecycle also prevents a corrected or
withdrawn packet from surviving behind an otherwise unchanged RC result.
Canonicalizing the exact root
holder, root approval actor, issuer and grantee principals prevents alias-based
self-designation, self-delegation and canonical cycles without adding another
root or signature.
Current capability-authority and evidence-resolvability heads prevent superseded
scope or deleted proof from continuing to support a current claim, while the
expiry policy constrains both finite and explicitly non-expiring decisions
without inventing a lifetime in this ADR. Requiring a compatible retention rule
for the latter prevents a nominally permanent decision from depending on
evidence scheduled to disappear. Exact current-lifetime integrity-review slots
anchored to authoritative `decision_at` prevent a delayed first due date or one
recent successful read from concealing a missed periodic review, while resolving
each slot's authoritative review-outcome head prevents a later retraction from
leaving the slot falsely satisfied. When the Accepted cadence additionally
requires independence, deriving the slot review into the evaluated-at consumed-
review control prevents stale owner, producer, membership, or identity facts
from turning self-review into a current pass without adding that future review
to the historical decision cohort.
Deferring activation until one coordinated default-branch revision aligns this
ADR, Phase 51.3, its verifier, and authoritative consumers avoids an accepted
but contradictory transition state while still allowing approved design work to
guide implementation.

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
- After approval, the ADR may guide implementation but Activation remains
  `Deferred`; the accepted Phase 51.3 contract remains the sole release mapping
  until the coordinated implementation revision atomically activates this ADR,
  its baseline changes, focused verifiers, and authoritative consumers.
- A denied proposal may be `Rejected` only before approval. Once Accepted,
  withdrawal in either Deferred or Active posture requires a new Accepted ADR
  and Superseded metadata; it cannot rewrite the original approval or activation
  history.
- Documentation, verifiers, and adversarial tests must be updated in that
  separate implementation pull request.
- Issue #1418 remains open until its own current-revision evidence and operator
  approval requirements are satisfied.

## 7. Implementation Impact

This proposal-only pull request changes no runtime, configuration, schema,
deployment, credential, privilege, or persistent state. If this ADR is
Accepted, implementation will add authoritative GA-decision, lifecycle,
gate-and-launch-scope selection, launch-scope-definition and deployment-class
and launch-eligible-subset closure, deployment-profile and environment-criteria lifecycle and dependency
closure, journey and operability environment-evidence lifecycle and dependency
closures plus governing environment-source-policy lifecycle and dependency
closure, journey and one-time-execution primary-run-outcome lifecycle and head
closures, subordinate owner-review head closure, release-authority, identity-
resolution, requirements-separation tuple-set and closure-set records,
evidence-index, producer-attribution lifecycle/current-head and evaluated-at
root/node producer-currentness partitions and producer closures, attribution-
policy dependency set, reviewed-at ownership/membership relationship-proof and
governing ownership-source/group-resolution policy lifecycles and dependency
closure,
real-user and design-partner qualification plus attributable issuer/acceptance-
actor identity and complete per-qualification policy-prohibited-subject source-
proof, role, set/count/digest and separation mappings,
journey-coverage-rule, bounded decision-used review-outcome lifecycle, and
evaluated-at consumed-review control closure, review-independence,
selected RC-proof-packet evidence lifecycle and packet-to-result mapping,
GA-approver-ownership coverage,
expiry-policy, launch-requirements, required-component, applicability-matrix,
claimed-capacity and material-environment boundary, conservative-equivalence and
environment-coverage, cross-class-backup-reuse and sequence-equivalence-rule
child sets with source/target-applicability and path-edge mappings, plus the
separate manifest and decision-input concrete cross-class restore-target-to-
rule-review-and-source-backup mapping,
supported-upgrade-path, routine-backup and operator-health stable lifecycle,
restore-rehearsal schedule and currentness, credential-lifecycle, capability-
scope-authority, material-configuration-history and reviewed-change current-head,
derived configuration-backup-obligation, support and upgrade ownership-head,
ownership-coverage-closure,
limitation-registry current-head, disposition/currentness-policy head and
snapshot, evidence-retention and decision-input integrity-review lifecycle, and
slot-bound integrity review-outcome lifecycle/current-head mappings and cadence-
dependent consumed-review-control origin mappings,
operability-manifest schemas;
backend authorization and current-status read and write paths; persistent
migrations; and atomic or fenced audit ordering. It must not widen the existing
action-approver or platform-administration roles.

If approved, a separate implementation pull request would update the affected
Phase 51 gate, persona, competitive-gap, authority-boundary, and closeout
documents; Phase 58 upgrade and rollback plans; Phase 65 packaging and upgrade
contracts; Phase 66 supportability and closeout documents; README positioning;
and their focused verifier and adversarial self-test pairs. That implementation
must not be merged before this ADR records approval. Its first accepted default-
branch tree must update the Phase 51.3 mapping, focused verifier and every
authoritative consumer together with this ADR's Activation, Activated By, and
Effective Date metadata; partial or metadata-only activation must fail closed.

That implementation must also define structured schemas and focused verifier
and adversarial-test pairs for the per-class GA journey-family index and
pre-run declaration envelope, successful criteria, journey-level coverage rule
and current lifecycle head, used-rule exact-set closure,
class-environment comparator with immutable observation, audit chronology and
journey declaration-and-record binding to either a pre-start snapshot plus
authoritative no-material-change proof through completion or a predeclared gap-
free full-interval attestation, separate journey environment-evidence lifecycle
aggregate/current-head closure, exactly one immutable authoritative journey
owner-review identity, content version, accepted or valid non-blocking accepted-
with-follow-up disposition, accountable journey owner, attributable actual
reviewer, reviewed-at and audit sequence, separate complete journey primary-run-
outcome and owner-review aggregate/head closures with index/run/review mappings,
participant exact set, and immutable
source-authoritative real-user or design-partner qualification record, lifecycle
current head, attributable issuer and qualification-acceptance actor source
subjects and authority provenance, decision-bound qualification-source-policy
version and prohibited-role predicate, exact per-qualification prohibited-
subject set/count/digest and source-proof/role mapping, complete actor-
separation mapping-set reconciliation, and canonical participant-separation
closure; immutable
evidence index, per-entry producer-attribution stable aggregate/current-head
records for every root and reachable material provenance node, governing
attribution-source/currentness policy aggregates and heads, root-to-node and
node-to-attribution mappings with shared-node deduplication, and decision-time
and evaluated-at acyclic producer-closure records with exact input/head/policy
mappings and separate decision-input and currently consumed-review partitions, a source-authoritative
decision-scoped identity-resolution head and immutable source-snapshot record for
historical provenance plus evaluated-at current-head records that bind separate
fixed-subject, attribution-derived decision-input, per-consumed-review and
current-successor mapping closures, independent-review direct-
producer attribution or complete derived-evidence producer-closure slices,
authoritative review-outcome lifecycle heads, decision-used head closures, and
evaluated-at consumed-review control closures binding exact producer,
ownership, membership, identity, and per-review independence state, plus direct
routine-record or slot-to-review-outcome bindings and deterministic expected-set
derivation with bidirectional reconciliation, reviewed-at ownership-
snapshot and owner-group-membership proof stable aggregates/current heads,
selected relationship-head closures and per-review mappings, exact ownership-
source and group-resolution policy dependency closures and current heads,
review-independence closure,
credential-custodian source-subject and canonical-human mappings for both the
decision-bound and current successor sets, retention head, and current-lifetime
decision-input integrity-review aggregate with its decision-time coverage and
first-slot anchors, slots, attempts, results, authoritative review-outcome
aggregate/current-head exact set and bidirectional slot mapping, plus boundary-
assigned result-completion, accepted-review-head and parent-successor sequence
fields and verifier-enforced strict ordering and, when cadence requires
independence, slot/cadence-version origin edges into the evaluated-at consumed-
review exact set and complete control closure;
complete inherited RC set with a selected RC-proof-packet evidence aggregate/
current head, packet-input closure and packet-to-result mapping plus an
authoritative selected-result review-outcome aggregate and current head, with
packet-head, result-review/head and GA-decision audit sequences proving their
strict one-way order;
explicit human decision event and lifecycle
aggregate; canonical gate-and-launch-scope aggregate and compare-and-append
selection head, plus the current launch-scope-definition head, canonical
deployment-class exact set, non-empty profile-derived launch-eligible subset,
deterministic scope-class pair closure, and exact
decision-used deployment-profile and environment-criteria lifecycle dependency
closure plus separate decision-used journey and operability environment-evidence
lifecycle closures and a governing environment-source-policy dependency closure
binding every selected policy aggregate, head, version, source authority,
transition semantics, set, count, digest and evidence-to-policy mapping;
release-authority root-governance head and complete assignment/delegation chain,
source-authority and opaque source-subject bindings and current canonical mapping
closure for every selected root holder, actual root approval actor, issuer and
grantee, profile-derived approver-ownership coverage closure and selected holder
heads, and decision-time serialization boundary; independently
accepted launch-operability requirements with complete
required-component, applicability-matrix, claimed-capacity and material-
environment boundaries, referenced conservative-equivalence and environment-
coverage rules, selected cross-class-backup-reuse and sequence-equivalence rules
with exact source/target-applicability and path-edge mappings, and non-empty
supported-upgrade-path child sets,
plus per-tuple
requirements-separation closures over canonical requirements approval actors and
the exact requirements-author, target-author and exercise-producer slices, and
one complete selected tuple-set and bidirectionally reconciled closure-set record;
and a per-deployment-class GA operability manifest with routine-backup and
operator-health stable aggregates, current heads and successor chains,
profile-derived restore-rehearsal schedule, slots and currentness, no-weaker
profile-cadence comparators, Accepted environment criteria, immutable target-
and-execution binding to the same environment observation and interval proof,
and cross-class restore-target direct binding to its predeclared current reuse-
rule head, accepted review-outcome aggregate/current head and exact eligible
source backup/manifest, plus authoritative rule-content, rule-review-and-initial-
head, accepted-child/requirements-parent, restore-target and execution sequence
fields and the separate backup-completion, integrity-pass and accepted-review
sequence fields,
plus exactly one immutable authoritative owner-review identity, content version,
explicit accepted or valid accepted-with-follow-up disposition, exact execution,
result, target and revision binding, accountable execution owner, attributable
actual reviewer, reviewed-at and audit sequence per indexed execution, and
separate complete one-time-execution primary-run-outcome and owner-review
aggregate/head closures with manifest/run/review mappings; a
complete Accepted-profile-derived material-configuration surface and independent
transition-history aggregate reconciled exactly to the reviewed-change registry
and derived configuration-backup obligations at decision and every later
evaluation; reviewed evidence-cutoff snapshots; detached
aggregate review attestations with pre-reserved reviewed-at relationship-proof
identities and strict audit-sequence ordering, and
commit-time operational zero-delta reconciliation, plus immutable credential
family-definition obligations separated from current policy-lifecycle,
assignment, rotation, custody, event, and break-glass snapshots in stable
non-forking lifecycle aggregates with Accepted currentness rules. It must enforce direct
gate-revision execution,
current-requirements-bound pre-run target identity, claimed-capacity and material-
environment-boundary exact-set reconciliation, minimum-resource comparison and
per-family direct-or-conservative variant coverage, accepted owner-review
outcomes for every indexed journey and execution without treating them as
independent GA approval unless separately selected for that purpose, distinct
path-target and per-hop execution-target records, one-path run lineage, reviewed
rollback-backup custody, upgrade and rollback outcomes, bound owner-review
outcomes, authoritative limitation-registry current head, snapshot, exact-set,
bound currentness rule and next invalidation boundary, and
every-`evaluated_at` time-derived posture reconciliation, including the current
Accepted disposition/currentness-rule head and machine-verifiable maximum
follow-up lifetime, immutable obligation origin, maximum-due calculation, exact
GA-review follow-up obligation and source-review mapping, one-to-one producer
attribution for every immutable input root and reachable material provenance
node, exact root/node and policy mapping, and
the complete producer-union independence check, current support and upgrade
ownership heads and per-family deployment-class coverage closures,
claimed-capability
scope-authority heads, and the shared mutable-state cohort through the atomic
decision boundary, freshness, scope-first current-head re-evaluation including
the exact decision-bound launch-scope-definition, profile-and-criteria dependency
closure and selected lifecycle heads, separate journey and one-time-execution
primary-run-outcome closures, subordinate owner-review closure, every input-to-
producer-attribution current head, governing attribution-policy current head,
root-and-reachable-node partition mapping and rederived current decision-input
producer closure and per-consumed-review producer slices, every selected
reviewed-at relationship-proof and governing relationship-policy current head,
separate journey and operability
environment-evidence closures and every selected aggregate's complete chain,
source-authoritative current head and high-water mark, governing environment-
source-policy dependency closure and every selected policy chain and current
head, scope-class requirements
pair closure, launch-operability requirements heads, every child exact set and
requirements-separation tuple and closure sets, limitation-
registry and disposition/currentness-rule heads, routine-backup and operator-
health stable aggregates and successor
heads, backup-bound material-configuration-history and reviewed-change heads,
derived configuration-backup obligations and restore-rehearsal schedule and
currentness,
participant qualification-lifecycle and source-policy heads, the exact
per-qualification participant/issuer/acceptance-actor and decision-bound policy-
prohibited-subject source-proof/role mapping set, counts, digests and canonical
separation,
the selected RC-proof-packet chain/current head and exact packet-to-result
mapping,
decision-bound credential-lifecycle aggregates and their current successor
heads, the exact decision-used journey-coverage rule and review-outcome heads,
any currently consumed successor-review control closure with its exact
evidence-producer, owner, membership, identity-mapping, and per-review
independence dependencies and derived expected-set equality, the exact
decision-scoped approver, producer, independent-reviewer, owner, decision-bound
custodian, requirements-approval-actor, qualification-participant,
qualification-issuer, qualification-acceptance-actor, policy-prohibited-
qualification-principal, root-holder, root-approval-actor, issuer and grantee identity-
resolution head, fresh canonicalization of each current fixed decision-bound
subject set, current attribution-derived decision-input producer set, each
currently consumed review's producer set, and current-successor custodian set with the
evaluated-at current identity head, immutable source snapshot, high-water mark,
separate exact sets and mappings, and review-independence closure, the profile-
derived approver-ownership coverage closure and holder authority heads, the
root-governance head and complete assignment/delegation-chain heads, and exact
decision-bound support and upgrade ownership closures and heads at every
`evaluated_at`, and retained-evidence secret hygiene without storing forbidden
source values.

The current-status read schema and path must expose distinct `current` and
`historical` modes. A current evaluation record binds the read-boundary-assigned
`evaluated_at`, read sequence, fence or linearization identity, every resolved-
through audit high-water mark, and status from one snapshot-consistent read; it
must reject caller-supplied, backdated, future-dated, overridden or reused times
and cached-current relabeling. A historical query may accept an explicit `as_of`
only while returning a non-current, non-authoritative projection. Neither path
holds a transaction through UI rendering or external human review.

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
early transition must instead produce the resulting non-current state. Current-
lifetime integrity-review tests must accept a future-not-due slot and an on-time
successful review whose authoritative outcome aggregate/current head is
accepted and bound one-to-one to the slot and complete input closure in the same
non-forking aggregate whose initial head was created in the decision cohort with
`coverage_start = decision_at` and first due slot derived from the Accepted
cadence. The positive case must prove boundary-assigned result completion before
the accepted review-outcome initial head, that head before the integrity-parent
successor, and the parent successor by the evaluated-at read boundary. They must
reject a caller-supplied, future, delayed, replacement, or
reset coverage start, a shifted first-slot or next-due boundary, and any omitted,
pre-window, late, failed, unreviewed, partial, wrong-input, duplicate, cross-slot,
weaker, forked, gapped, or replacement result or review mapping. A review over a
reserved or future result, pre-result, equal, reversed or backdated result/review/
parent sequence, or accepted review head omitted from a later parent successor
must also fail. They must also
correct, retract, reject, revoke, expire, supersede, fork, gap, cache, replace or
mismatch a previously accepted slot review outcome and reject the stale
favorable review and parent head; an inseparable child mutation that does not
advance the parent must fail. A later successful verification, replacement
review, or most-recent-result update must not cure an earlier miss, and a
temporary read outage may recover only when the same complete valid integrity
and outcome chains resolve. For a slot whose exact Accepted cadence version
requires independence, tests must reject omission from, injection into, or
duplicate membership in the currently consumed set; a missing, extra, wrong-
slot, wrong-cadence, or mismatched origin edge; a stale attribution, owner,
membership, relationship-policy, identity mapping, or review-outcome head;
and a reviewer canonically equal to the exact result's owner or producer.
Positive coverage must accept a canonically distinct reviewer with the
complete slot-and-cadence-origin mapping and control closure, deduplicate one
review identity used by multiple explicitly permitted origins without losing
an origin edge, exclude future slots, and leave the immutable decision-time
cohort unchanged. It must also prove that a routine slot review does not enter
the independent-GA or consumed-review closure unless its Accepted cadence rule
explicitly requires independence. A retroactive overlap correction requires
a new applicable independent review, but a replacement after the slot deadline
cannot cure the missed slot. It
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

Current-read chronology tests must reject a caller-supplied, overridden,
backdated, future-dated, or reused `evaluated_at`; a revocation, expiry, or newly
due obligation effective after a requested old time but at or before the actual
read boundary; omission of the boundary's sequence, fence identity, or resolved-
through high-water marks; and relabeling a cached or historical result as
current. Positive coverage must assign current-mode time and sequence at the same
snapshot-consistent linearization point that resolves all dependencies, while an
explicit caller-selected `as_of` may produce only a labeled historical result
with no GA, release, or rollout authority.

Producer-separation tests must reject a missing or empty direct producer set,
missing, extra, or duplicate entry, input, revision, set, or count mismatch,
missing, extra, substituted, raw-identifier, or canonical-only source-authority
or source-subject binding, source-subject set, count, or digest mismatch,
owner, reviewer, custodian, submitter, display-name, self-declared, unverified
repository-author, or service-label substitution, canonical-identity alias
splitting or collision, an approver who authored or materially produced any one
input, approver-initiated automation, derived-source omission or cycle, and
input, attribution, identity-head, or closure mutation between snapshot and
decision commit. Post-acceptance currentness tests must correct an attribution to
add an omitted acting-approver, requirements-author/target/execution overlap, or
reviewed-evidence producer; add an omitted upstream material producer to
decision-bound derived evidence; retract or withdraw an attribution; expire,
revoke, supersede, fork, gap,
replace or semantically weaken its governing attribution-policy head; fork or
gap the attribution aggregate; serve a cached favorable head; omit, duplicate or substitute an
input-to-head mapping; and change a causal or provenance edge, and must reject
the stale historical closure after rederiving every affected separation
predicate. Positive coverage must reconcile every input entry exactly once;
recover from a temporary read outage only when the same complete attribution and
policy chains resolve; accept a metadata-only same-aggregate successor and
unrelated monotonic source high-water advancement only when the exact producer and causal closure remain
unchanged; accept a future-only no-weaker attribution-policy successor that
preserves the bound version and every semantic applicable to the selected
evidence; deduplicate one immutable upstream node shared by multiple evidence
roots while retaining every root-to-node edge; keep attribution/current-closure/
control records non-recursive; and permit the historical acting approver or a
requirements actor to produce later routine evidence without extending the old
decision-input predicate, while still applying per-review independence to that
evidence's currently consumed review. A harmless newly disclosed decision-input
producer must still invalidate the old projection but allow a complete new
decision by the same eligible approver when every rederived separation predicate
remains satisfied, without an unrelated rerun or re-review. Positive coverage
must also cover manual
production, human-triggered automation, and a proven
autonomous scheduled machine-only producer; and reuse legacy evidence only when
complete producer provenance can be rebuilt from immutable authoritative audit,
repository, acquisition, or execution records rather than owner or reviewer
attestation.

Requirements-separation tests must reject a requirements approval actor who is
alias-equivalent to any requirements author, target author, or exercise producer
for the exact approved tuple; missing, extra, substituted, stale, ambiguous, or
set, count, digest, tuple, role-slice, identity-head, or mapping mismatch; and a
snapshot-to-commit or post-acceptance alias merge. They must also reject a
missing, extra, duplicated, substituted, unreferenced or tuple-mismatched closure
member, a tuple-set or closure-set count, digest or mapping mismatch, and a multi-
tuple decision whose closure set omits any one tuple. Positive coverage must
accept one canonically distinct approval actor while allowing the requirements
author, target author, and exercise producer to overlap with one another, accept
a complete multi-tuple one-to-one closure set, and must not treat creation of the
approval event or derived control closure as production of the approved content.

Review-independence tests must reject an owner who reviews through another
alias, a reviewer who produced that review's exact reviewed evidence, a
reviewer who produced an upstream material source or transformation of derived
reviewed evidence, a
group-only reviewer label,
direct or transitive membership in the named owner group at `reviewed_at`, an
unknown, stale, unavailable, ambiguous, self-asserted, missing, extra,
substituted, count-mismatched, or digest-mismatched reviewer, evidence-producer
set, authoritative ownership snapshot, owner set, or membership result, a
zero-owner snapshot or count, a review-declared set that omits a co-owner, and a
retroactive identity, ownership, or membership correction that invalidates the
review. Currentness tests must add or remove a co-owner effective at
`reviewed_at`, correct direct or transitive owner-group membership at that time,
fork or gap a selected relationship aggregate, serve a cached favorable head,
substitute or omit a per-review relationship mapping, and reject the stale
independence result after exact current-head re-resolution. They must also
expire, revoke, supersede, fork, gap, replace or weaken a selected ownership-
source or group-resolution policy, including changing owner-completeness,
transitive-membership, correction, source-authority or transition semantics, and
reject the unchanged favorable relationship proof, a missing or extra policy-
closure member, and a relationship-to-policy set, count, digest or mapping
mismatch. Positive coverage must
accept a reviewer as the producer of their own review record or derived
decision-control metadata, a producer of evidence A reviewing unrelated evidence
B when they did not produce B, an owner of evidence A reviewing unrelated evidence
B when they neither own nor produced B, canonically distinct person owners and
reviewers, an authoritative non-member reviewer for a named owner group, and ordinary later
group joins or leaves that do not change the
relationship effective at `reviewed_at`, a semantics-preserving same-aggregate
relationship or policy successor, and an unrelated relationship or policy
catalog change, including a future-only policy successor that preserves every
reviewed-at source and semantic, plus temporary unreadability followed by recovery of the same
complete relationship and policy chains; same-organization, department, or role
membership alone must not create an owner-group conflict.

RC-proof-packet lifecycle tests must correct, withdraw, revoke, supersede, fork,
gap, replace, or serve a cached favorable non-head packet after GA acceptance
while leaving the selected RC result unchanged, and must reject a packet-input,
repository-revision, journey-run, content-version or packet-to-result mapping,
set, count or digest mismatch. They must also mutate the packet head between the
decision snapshot and commit and reject an RC result over a reserved-only or
not-yet-committed packet head, a packet materialized after review, or an equal,
reversed, caller-supplied or backdated packet/result/decision sequence. Positive
coverage must bind the already committed packet head one-way into a later
independently reviewed result and then into the later GA decision, recover after temporary
unreadability when the same complete packet and result chains resolve and may
accept only a metadata-only same-aggregate successor that preserves every exact
packet, input, revision, result and lifecycle binding. A material packet change
must require a new packet, independent RC-result evaluation and GA decision, but
the packet lifecycle must remain subordinate and grant no RC or GA authority.

Review-outcome lifecycle tests must retract, reject, revoke, expire, supersede,
correct, fork, gap, or replace a decision-used review after acceptance,
including the selected Phase 66.8 closeout or successor RC-gate result, and must
reject a cached favorable historical or non-head outcome and in-place
replacement rebinding. They must also reject a result, evidence, reviewer,
authority, scope, revision, outcome, or follow-up mismatch and a lifecycle
mutation between snapshot and decision commit, while proving that an
unauthorized comment, ticket, or purported retraction cannot advance the head.
Scope tests must reject recursively adding the GA decision, ADR, source-contract,
profile, criteria, lifecycle-policy, root-governance, other governance-approval,
requirements-approval or separation-control, or review-control metadata to
either the decision-used review-outcome set or an
evaluated-at consumed-review control closure, while proving that each excluded
dependency's dedicated current-head rule resolves normally without such a
member.
Positive coverage must recover
after temporary unavailability when the same complete valid chain resolves and
may accept only a same-aggregate successor that preserves the exact immutable
review or RC result and every decision binding. A permitted routine successor
review consumed later must enter a separate evaluated-at consumed-review control
closure; retracting it must make that projection `unavailable` without adding its
future head to the historical decision cohort. Current-status tests for that
later review must reject omission or relabeling of a referenced review as
unconsumed; injection of an unrelated or future-not-due review; duplicate,
substituted, set, count or digest-mismatched members, including a multi-review
successor with an incomplete set; a reviewer who is an alias of an authoritative
owner, a direct or upstream producer of the exact reviewed evidence, or a self-
reviewer of that evidence; a later producer-attribution correction or governing-
policy change that creates reviewer overlap or invalidates the exact reviewed-
evidence binding or applicable semantics; and a missing, stale, mismatched, unavailable, or
incomplete owner, membership, producer, identity-mapping, or per-review
independence proof. A consumed-only attribution correction that preserves the
reviewed-evidence binding and all independence predicates must permit a rebuilt
control closure and current re-evaluation without a new GA decision; a correction
that creates reviewer overlap must require a new applicable review and closure,
also without rewriting or replacing the historical decision. Positive coverage must accept a canonically distinct
independent reviewer with a complete evaluated-at consumed-review control
closure, exclude a future-not-due review, and leave the historical decision
cohort unchanged.

Profile-derived approver-coverage tests must reject a small-production class
with one holder, alias or duplicate-grant double counting, an unresolved group
or role label, wrong class, scope, profile, or authority chain, an acting
approver outside the selected set, an issuer or root designator counted without
their own scope-valid grant, and holder revocation or replacement between
snapshot and commit or acceptance and `evaluated_at`. Positive coverage must
accept two canonically distinct current holders with only one acting approver,
and apply the exact minimum from each Accepted lab or single-customer profile
without inventing dual signatures, roots, or issuers.

Release-authority currentness tests must revoke or supersede the root-governance
head or an upstream issuer or delegation after acceptance while leaving the leaf
holder and staffing closure unchanged, and must reject cached old roots, missing,
forked or gapped chains, scope widening, root, issuer, grantee or provenance
mismatch, a root approval actor alias-equivalent to the root holder, an issuer
alias-equivalent to its grantee through another source subject, a multi-hop
canonical cycle, missing or ambiguous root/chain-principal mapping, post-
acceptance alias merge, and in-place replacement rebinding. A snapshot-to-commit
identity change affecting any selected root or chain principal must abort.
Temporary read failure must return `unavailable`, while the same complete still-
valid chain and canonically distinct principals may recover. The
historical decision event must remain unchanged, and a durable lifecycle mutation
must still use the separately authorized transition path.

Current-status tests must add, remove, rename, alias, or supersede a deployment
class or remove or change the decision-bound launch-eligible subset or a member's
eligibility in the launch-scope-definition head; add, update, reopen,
close, delete, reclassify, or redispose an in-scope limitation; and remove,
expire, retire, reassign, supersede, or narrow each decision-bound support and
upgrade ownership head between acceptance and `evaluated_at`. They must also
revoke, expire, supersede, fork, gap, or replace a decision-bound launch-
requirements head or its component, matrix, capacity-boundary, referenced
conservative-equivalence-rule, material-environment boundary, environment-
coverage-rule, cross-class-backup-reuse-rule, sequence-equivalence-rule,
upgrade-path, or credential-family child set and
reject recovery through a historical or
replacement head. They must reject
stale class or limitation sets, count or digest mismatches, forked or gapped
heads, cached historical heads, and in-place replacement binding. Profile-and-
criteria currentness tests must keep the launch-scope head unchanged while
revoking, expiring, superseding, narrowing, forking, gapping, or replacing each
selected deployment-profile or environment-criteria head and must reject a
cached version, semantic obligation change, or in-place rebinding at
`evaluated_at`. Positive coverage must recover after temporary unavailability,
accept a same-aggregate successor only when it preserves the exact bound version,
scope, usage mapping, and all derived obligations, and ignore mutations outside
the decision-used dependency closure. Environment-evidence currentness tests
must, after acceptance, correct an observation or comparison, reveal a material
change-and-revert through revised change history, withdraw or revoke an interval
attestation, fork or gap a selected chain, serve a stale, rolled-back or selected-
chain-mismatched source high-water mark, expire, revoke or supersede its governing
source-policy head, change that policy's source authority or transition
semantics, serve a cached favorable evidence or policy non-head, or attempt
replacement-evidence or policy rebinding and must return `unavailable`. Positive
coverage must recover the same valid chains, accept a same-aggregate evidence or
policy successor only when it preserves every historical interval fact,
governing policy binding and decision binding, and permit monotonic source high-
water advancement caused only by an unrelated, future, or post-completion
observation that leaves the selected chain and exact executed interval valid.
Ownership
coverage tests must reject a missing class in either family, duplicate,
overlapping, extra, wrong-family, wrong-class, wrong-scope, alias-split, stale,
retired, revoked, superseded, or unreviewed mapping and must accept both complete
class-specific mappings and one exact family-specific scope-wide head without
requiring distinct owners. They must also
cross a limitation review-cadence, due-date, or deterministic invalidation
boundary without changing the head and reject the resulting overdue, expired,
or blocking posture. Review-follow-up tests must reject a missing, duplicate,
ticket-only, wrong-review, evidence, scope, class, family, owner, due-date, or
disposition mapping; a missing, historical, revoked, superseded, or wrong-scope
disposition/currentness-rule head; an arbitrary distant, maximum-plus-epsilon,
incomparable, extended, or origin-reset deadline; a follow-up already due at
`decision_at`; a follow-up added after the finalized snapshot; and late
completion or in-place rebinding. They must accept a plain `accepted` review with
no obligation and a mapped open non-blocking obligation at or before its exact
policy maximum and before its due boundary, then return `unavailable` at that
boundary when it remains unresolved. A new decision must not reset the original
obligation anchor. A temporary read outage must return `unavailable`, while
recovery of each exact unchanged and still-valid head may permit a new
evaluation; a changed or time-invalid head requires a new decision.
An out-of-scope limitation mutation and an inactive historical scope-class pair
must not create a false mismatch.
Routine-stream currentness tests must accept complete, on-time, no-weaker backup
and health successors in the same stable aggregate and a future obligation before
its deadline without requiring a new decision. They must return `unavailable`
for a post-decision missing, forked, gapped, omitted, late, overdue, failed,
rejected, unreviewed, hidden-failure, carried-open, unresolved, weaker, or
replacement stream; an unchanged head crossing a due boundary must fail as well.
Late evidence must not cure the miss, and recovery must require a new complete
gap-free window, its due review, and a new decision rather than cached evidence.
Backup-stream tests must also advance the independent configuration-history or
reviewed-change source after acceptance while leaving the prior backup head
unchanged. They must reject an unregistered, registry-only, omitted, reverted,
forked, gapped, wrong-order, open, or due-but-unsatisfied post-decision change and
its generated backup obligation, including a source high-water mutation between
the current-evaluation snapshot and commit. A registered transition with its
correct backup may extend the routine stream only when no target-bound identity
changes; an ordinary non-material workflow-record update must remain
nonblocking, while a target-bound change must require a new target, affected
rerun, and decision even after a successful backup. Restore-currentness tests
must cross a profile-derived restore deadline without changing unrelated heads
and return `unavailable` for a missing, late, failed, unreviewed, wrong-source,
wrong-revision, or wrong-target slot. They must accept a future-not-due slot and
an on-time successful reviewed same-aggregate successor without making the lab
profile monthly or any other heavy family periodic; late rehearsal evidence
cannot cure the old miss. They must also reject a pre-window target, trigger, or
execution, a target or result bound to the wrong slot, duplicate or cross-slot
execution reuse without an exact Accepted deterministic no-weaker rule, a late
completion or review, and a cadence version that weakens the governing monthly
or quarterly profile. Positive coverage must accept the correct quarterly Lab
and monthly Single-customer and Small-production schedules without inventing a
stricter cadence. Cross-class restore tests must reject a missing, extra,
duplicate, wrong-source, wrong-class, wrong-profile, wrong-environment, wrong-
revision, post-target, corrected, revoked, expired, superseded, forked, gapped,
cached-non-head, replacement, weakened, or in-place-rebound reuse rule or a rule
transition whose requirements parent did not advance; they must also correct,
retract, reject, revoke, expire, supersede, fork, gap, or serve a cached non-head
for its selected review outcome and reject the stale favorable review. They must separately
reject a missing, extra, duplicate, wrong-tuple, count, digest, or mapping
mismatch in the requirements-bound source/target applicability closure and a
missing, extra, duplicate, unreferenced, or bidirectionally mismatched concrete
target mapping in the manifest or decision-input index. A future or
unmaterialized target or reserved-only backup in the requirements parent must
fail. They must reject a target that omits or substitutes its exact rule head,
accepted review-outcome current head, source backup, or manifest; a rule review-
and-initial-head commit over reserved or uncommitted future rule content, before
the content commit, or at or after the accepted child/requirements-parent commit;
an accepted child/parent commit at or after target declaration; any equal,
reversed, or backdated content/review/parent/target sequence; a backup whose
completion is not strictly before its integrity pass, whose integrity pass is
not strictly before its accepted review, or whose accepted review is not before
the target; and an execution that does not start after the target. Positive coverage must accept a
same-class restore with no reuse rule and a cross-class restore whose
independently accepted rule and eligible reviewed source backup each predate the
exact bound target, without imposing an order between the rule review and backup
review. It must prove the complete rule-content, review-head, accepted-parent,
target and execution order and the separate backup-completion, integrity-pass,
backup-review, target and execution order. A same-class restore and an unused applicability tuple must not create a
concrete target-mapping member. Temporary unreadability may recover only the same complete valid rule
chain and mapping; a material rule change requires a new target, restore,
review, and decision.
Qualification-currentness tests must retroactively correct or revoke a bound
participant's execution interval, fork or gap the lifecycle, remove the source
policy or issuer authority, omit or substitute the actual issuer or acceptance-
actor source subject, use only a group/role/service label, collapse a participant
alias onto either actor or another policy-prohibited principal, mismatch the
per-qualification mapping, omit, add, duplicate, substitute, or attach to the
wrong qualification or policy a prohibited subject or role, mutate its source
proof, or rederive the historical subject set from a later policy version, and
reject cached or in-place replacement state at `evaluated_at`. They must also
abort when an actor mapping, bound prohibited-role predicate, applicable policy
head, prohibited-subject source proof, or mapping set/count/digest changes
between the decision snapshot and commit and return `unavailable` when a later
current identity head exposes self-issuance, self-acceptance, or a mapped
prohibited-principal overlap. They must reject initial source-policy or actor
authority whose acceptance provenance derives from the participant,
qualification record, or qualification graph. Positive coverage
must bind canonically distinct attributable participant and actor principals
plus the exact policy-derived per-qualification prohibited-subject closure and
separately governed source-policy approval provenance, permit one issuer to be
the acceptance actor when the Accepted policy allows it, keep distinct
qualifications' policy slices isolated, and retain validity after a temporary outage
when the same aggregates and complete valid lifecycles resolve again, a normal
relationship end after `completed_at`, or a future-only policy successor that
leaves the executed interval's predicate and completeness semantics, exact
historical actor mapping, canonical separation, source proof and issuer authority
valid.

Identity-currentness tests must use a later source-authoritative current head to
merge or correct aliases after acceptance so that a fixed decision-bound
approver resolves to a producer, an independent reviewer resolves to the reviewed
evidence's person owner or reviewed-at owner-group member, or two decision-time
custodians collapse to one human, or a qualification participant resolves to its
issuer, acceptance actor, or policy-prohibited principal. They must also remove
or conflict a fixed
source subject; omit, add, substitute or mis-tag a subject in the fixed,
attribution-derived decision-input, per-consumed-review or current-successor
partition; introduce a newly disclosed producer subject that cannot be
canonicalized; drift a reviewed-at membership result; make the historical
provenance unavailable; and reject any partition set, count, digest or mapping
mismatch, cached snapshot, or in-place historical-head rebinding. A
credential-custodian test must reject two aliases or source-system subjects for
one human, a duplicate, raw or canonical-only identifier, group, role, service,
or display label, unknown or stale mapping, snapshot-to-commit drift, a post-
decision alias merge that collapses the profile minimum, and an uncanonicalized
successor set. Positive coverage must accept canonically distinct humans at the
exact profile-derived minimum and a freshly canonicalized, no-weaker custodian
replacement in the same credential aggregate under a later current identity head
without imposing two-person custody on a profile that does not require it. It
must also accept an otherwise valid later routine record produced by the
historical acting approver or requirements actor when that actor is distinct
from the current review's reviewer and the record is not inserted into a
decision-input predicate. The evaluation must bind that later head, source
snapshot, audit high-water mark, separate exact fixed, current decision-input-
producer, per-consumed-review-producer and current-successor-custodian sets and
all mapping closures while retaining
the exact immutable decision-bound historical head and snapshot as provenance.
A temporary identity-head read outage must return `unavailable`; recovery of the
historical reference plus valid current mappings may permit a new evaluation.
Historical-reference drift, fixed-set remapping, mapping ambiguity, alias
collapse, or cardinality failure still requires a new review or decision and
complete producer and authority evaluation; unrelated current-head advancement
alone does not.

The later implementation must test a post-run journey-coverage declaration or
review acceptance, caller-timestamped ordering, comparison-to-execution
environment swaps, stale or wrong covered-profile criteria, class-label spoof,
missing or weakening journey environment comparison, and post-hoc journey
equivalence. Journey-specific interval tests must reject a material mutation and
revert between start and completion, gapped change history, a late, short,
unreserved or producer-only interval attestation, a declaration-to-journey
environment swap, and reuse of that invalid source journey through a coverage
rule. Positive journey coverage must prove the same exact environment by either
the accepted pre-start observation plus authoritative no-material-change history
through completion or the predeclared source-authoritative gap-free full-interval
attestation, while allowing a non-material or post-completion change that leaves
the exact historical proof valid. Generic operability tests must reject a post-run or backdated point
comparison, caller time, target-to-execution environment swap, wrong profile or
criteria, unreserved or producer-only interval attestation, gapped coverage, an
attestation starting after execution or ending before completion, and a material
mid-run environment change. Positive coverage must bind the same environment
observation to target and execution and prove either the pre-start audit ordering
plus authoritative no-change through completion or a predeclared source-
authoritative attestation enclosing the entire execution interval. Owner-review
tests must reject a missing, mutable, duplicate-selected, unknown, not-reviewed,
or rejected disposition; a review created before completion or after
`decision_at`; a journey review with the wrong run, outcome, criteria,
declaration, class, environment, interval proof, participant set, owner or
revision; a journey or execution review without an attributable actual reviewer,
or with only an artifact, service identity or verifier result in the reviewer
field; an execution review with the wrong execution, result, artifact, target,
family, class, environment, owner or revision; and accepted-with-follow-up
without the exact current limitation obligation and due-date mapping.
Positive coverage must accept a directly bound immutable `accepted` journey
owner review, an `accepted` execution owner review whose accountable owner also
acts as the attributable actual reviewer when no separate Accepted rule requires
independence, and valid non-blocking `accepted-with-follow-up` cases without
treating an accountable owner review as GA authority, an independent review or
a second-person approval. Owner-review lifecycle tests must, after acceptance,
correct, retract, reject, revoke, expire or supersede a selected journey or one-
time execution review; fork or gap its aggregate; serve a cached favorable head;
omit, duplicate, substitute or mismatch a run-to-review mapping; and attempt
replacement-review rebinding. They must return `unavailable` and require a new
valid review and decision without an unconditional rerun when the primary run
remains valid and fresh. When the same review is separately used as independent
GA review, the same head must appear in both exact closures and satisfy the
additional independence predicate. Primary-run currentness tests must correct a
selected outcome/result, artifact, interval, target/declaration, criteria,
participant/operator, environment or revision; withdraw or revoke the run; fork
or gap its aggregate; serve a cached favorable head; omit, duplicate, substitute
or mismatch an index/manifest-to-run mapping; or attempt replacement-run
rebinding, and must require a new run, owner review and decision. Positive
coverage must accept only a same-aggregate run or review successor preserving
every exact decision-bound fact and must reuse, rather than double-wrap, an
equivalent canonical routine-stream lifecycle. It must reject
a class with two Accepted material environment variants when only the easier
variant is executed; an empty, missing, duplicate, extra, label-spoofed or wrong-
class tuple; an invented Cartesian product; and a post-hoc, producer-selected,
revoked, superseded, mismatched or weaker environment-coverage rule. Positive
coverage must accept the current singleton Accepted environment boundary, direct
execution of every member, and direct execution plus an independently Accepted
predeclared no-weaker coverage rule without expanding journey coverage or
unclaimed variants. It must also
correct, revoke, expire, supersede, fork, gap, or make
unavailable a decision-used rule after acceptance and reject cached historical
heads, wrong source, covered-set, profile, criteria, comparison, or authority
bindings, and replacement-rule rebinding. Positive coverage must recover the
same valid head and accept a future-only same-aggregate successor that preserves
every executed-interval and decision binding, without requiring rule heads for
direct per-class journeys. It must also reject an owner-only, authenticated employee or lab
actor, wrong or alias-mismatched source subject, self-issued or mutable
qualification, post-run or backdated qualification, mid-journey expiry, and a
qualification correction or revocation that invalidates the executed interval.
Positive coverage must include a qualified real-user operating assignment, a
qualified design-partner engagement, a qualified participant assisted by an
attributable non-qualifying producer, and a normal engagement end after journey
completion. Retained qualification evidence must use opaque identifiers and
must reject a name, email address, raw customer identifier, HR or contract body,
private interview note, or co-retained raw-to-opaque lookup material. Positive
coverage must retain the required privacy-minimized opaque source-subject and
organization or engagement identifiers without a directly identifying value.
It must test
historical or discontinuous backup windows; missing, omitted, pending,
in-progress, abandoned, unknown, deadline-incomplete, late-completing, or
late-reviewed attempts; pre-slot, duplicate cross-slot, and late-evidence
rebinding; a slot, attempt, or review whose lifecycle, deadline, or grace crosses
`coverage_start`; a new record or newly due pre-existing obligation between
`evidence_cutoff_at` and atomic commit; and both a visible failed attempt followed
by an on-time clean retry and a concealed, late, cross-slot, or incompletely
cleaned failure. It must test an independently observed but unregistered
configuration change, a registry-only applied change with no observed
transition, an omitted, forked, or gapped transition history, a hidden
change-then-revert, wrong class, digest, or profile-required backup ordering,
self-derived registry history, and a post-cutoff transition that does not abort
the decision attempt. Positive coverage must include a correctly registered
transition with its required before or after backup and an Accepted predeclared
batch mapping without turning an out-of-scope or non-material observation into a
new obligation, including an ordinary workflow-record content mutation that
does not change schema, retention, authority, storage, topology, or configuration
boundaries. It must also test sparse due slots, shifted boundaries,
oversized grace, delayed review, post-change configuration backup, weaker state
or custody coverage, unapproved or mismatched profile deviations, integrity or
custody failures, one-off restore and rollback sources, and missed routine-backup
or operator-health intervals. Health-stream tests must also cover a mid-window
profile change, a finding opened before the window but still unresolved, an
exercise-matrix attempt to waive a profile duty, and a rejected attempt followed
by an eligible on-time accepted re-review. The decision path must abort and
release its transaction or fence before requesting any renewed human review.
Positive coverage must prove that the exact detached aggregate-review
attestation and inseparable initial review-outcome head, its exact attribution
record, deterministic producer closure,
reserved reviewed-at ownership-snapshot and owner-group-membership proofs,
reserved review-independence and decision-used review-outcome closures, required
decision-control head advances, and decision-attempt bookkeeping do not invalidate an otherwise
zero-operational-delta commit. Negative coverage must
reject a caller time, same-time or wrong audit order, review attestation or
initial outcome head, attribution, ownership-snapshot proof, membership proof,
review-independence or review-outcome closure that does not
bind the reserved identity, cutoff snapshot, authoritative source version, and
high-water mark, self-membership of producer metadata, an unreserved, extra,
wrong-order, wrong-source, or operationally mutating relationship proof, any
extra post-cutoff review, producer-control, or operational record, and a review
or producer record that mutates a finding or disposition without a new cutoff.

The later implementation must additionally reject producer-declared or weakening
environment equivalence; an empty launch-scope class set or pair closure, a non-
empty but Lab-, internal-, exercise-, or training-only scope, an empty, missing,
duplicate, label-spoofed, post-target, revoked, or superseded launch-eligible
subset or eligibility binding, a launch scope with classes A and B whose journey,
operability, or active
requirements closure supplies only A, an extra or duplicate class, alias-split
or wrong-scope pair, count or digest mismatch, stale or superseded
scope-definition head, or a class-set or eligibility mutation between target
declaration and decision. Positive coverage must accept a complete Single-
customer- or Small-production-eligible single-class set and a complete Lab-plus-
eligible A-and-B set while ignoring inactive historical pairs and without
treating the Lab member as the qualifying class. It must reject
historical launch-requirements heads; component
inventory cherry-picking, enabled in-scope omission, or missing
persistent-component restore; a missing, post-hoc, or producer-selected
applicability cell, an irrelevant numeric dimension forced onto a family, or a
core capacity or recovery dimension marked not applicable; an empty or missing
claimed-capacity-boundary set, a top-of-range resource run used to claim an
untested lower-resource floor, a post-hoc or producer-accepted conservative-
equivalence rule, a rule omitted from the parent requirements child set, a rule
revoked or superseded between target, decision, and `evaluated_at`, a parent head
that fails to advance on rule lifecycle change, a tested-to-claimed tuple or
direction mismatch, or an invented Cartesian range combination. Positive
capacity coverage must execute each exact
Accepted boundary at resources no more favorable and workload no less demanding,
accept an independently predeclared no-weaker equivalence rule, or explicitly
narrow the claimed minimum resource scope to the tested tuple without requiring
every intermediate or unclaimed combination. Environment-boundary coverage must
also reject missing, duplicate, extra or unexecuted material tuples, a generic
environment or journey-equivalence substitute, and a requirements head that
fails to advance when a referenced coverage rule changes. It must accept a
complete direct-or-predeclared no-weaker mapping for every applicable family
without enumerating unclaimed hosts, patches or Cartesian tuples. It must also
reject an empty or zero-count supported-upgrade-path set and missing, extra, floating,
incompatible, failed, or mismatched supported upgrade paths; missing, skipped,
reordered, disconnected, independently executed, reset, reinstalled,
state-discontinuous, hop-target-mismatched, or wrong-rollback-target sequence
hops; same-endpoint path swaps, cross-path run reuse, post-hoc sequence
assignment, or older-revision hop import; an uncustodied, unreviewed, one-off, or
post-hoc rollback checkpoint, a checkpoint stale at execution start or selected
before a later material source change, a source-digest mismatch, or insufficient
protected-state coverage. Sequence-equivalence tests must reject an omitted,
extra, duplicate, wrong-path or wrong-edge rule; a post-hoc rule or one bound to
produced rather than reserved output/input identities; a corrected, revoked,
expired, superseded, forked, gapped, cached-non-head, replacement, or weakened
rule between target, decision, and `evaluated_at`; a set, count, digest, edge-
mapping mismatch; or a rule lifecycle transition whose parent requirements head
and child digest did not advance. Positive coverage must accept a directly exact
adjacent hop with an empty referenced-rule set, a predeclared current no-weaker
rule whose predicate matches the later actual adjacent output/input digests, and
temporary recovery of the same complete valid chain. Any material rule
transition requires a new target, affected sequence rerun, and decision rather
than in-place rebinding. The tests must not require rules for direct paths,
exact adjacency, or unreferenced catalog entries. They must also reject missing
due rotation, hidden trigger, one-person or
otherwise weaker-than-profile custody, weaker cadence, missing primary or backup
custodian, two aliases or source-system identities for one custodian, duplicate,
unknown, stale, group-label-only, or canonically collapsed custody, or break-
glass use without return-to-normal closeout;
credential-policy replacement that resets coverage or hides a boundary-crossing
or carried-open event. Credential temporal tests must reject an observed event
identity, outcome, or high-water mark embedded in the immutable requirements
head and must keep the requirements head and matching target valid when a
rotation or break-glass event occurs after target declaration and is captured by
the current snapshot at or before the cutoff. They must reject an omitted event,
require a new snapshot and review for a post-cutoff delta without rerunning an
otherwise matching target, and invalidate the target when a family definition,
policy, cadence, trigger obligation, or required result schema changes. They
must also accept a post-decision routine rotation as a continuous same-aggregate
successor only when it is complete, on time, accepted, and no weaker. At a later
`evaluated_at`, a missing, forked, gapped, omitted, overdue, failed, open,
unreviewed, weaker, or replacement aggregate and an unclosed break-glass event
must return `unavailable`; a family-definition or governing-obligation change
must require a new target and decision rather than rebinding. They
must also reject withdrawn or narrowed
capability authority; and missing, deleted, unreadable, corrupt, partial, or
archive-unavailable decision evidence. Snapshot-to-commit tests must mutate each
backup, health, selected deployment-profile or environment-criteria lifecycle,
journey or operability environment observation, comparison, interval-attestation
or lifecycle head, selected governing environment-source-policy head or source
audit-high-water between snapshot and commit, journey or one-time-execution
primary-run-outcome aggregate/head or closure, subordinate owner-review
aggregate/head, identity, content or closure, producer-attribution aggregate/
head, governing attribution-policy aggregate/head or producer closure, or
reviewed-at ownership/membership relationship-proof aggregate/head, governing
ownership-source or group-resolution policy aggregate/head, policy-dependency
closure or mapping,
participant-qualification lifecycle,
qualification-source-policy head, applicable prohibited-role predicate,
issuer/acceptance-actor identity, per-qualification prohibited-subject source
proof or actor-separation mapping set/count/digest, selected RC-proof-packet
aggregate/head or packet-to-
result mapping, journey-coverage-rule lifecycle,
review-outcome, review-independence or owner-membership state, launch-scope-definition,
launch-eligible subset or profile eligibility,
requirements, component, matrix, claimed-capacity or material-environment
boundary, conservative-equivalence or environment-coverage rule, cross-class-
backup-reuse applicability child set or source/target tuple mapping, sequence-
equivalence child set or path-edge mapping, separate concrete restore-target-to-
rule-review-and-source-backup mapping, upgrade-path,
requirements tuple or separation closure-set membership, count, digest, mapping,
or requirements-approval-actor identity mapping,
routine-backup or operator-health aggregate,
material-configuration-history or reviewed-change head, derived configuration-
backup obligations, restore-rehearsal schedule or currentness,
credential-definition, credential-state or custodian-identity mapping,
root-holder, root-approval-actor, issuer or grantee identity mapping,
capability-authority,
evidence-retention, current-lifetime integrity-review aggregate or slot-bound
review-outcome head/mapping, or, when its cadence requires independence, the
slot/cadence origin-edge set or consumed-review control closure,
GA-approver-ownership coverage or selected-holder authority,
support or upgrade ownership coverage, ownership-head, limitation or
disposition/currentness-rule head, and
release-authority root-governance or any assignment/delegation-chain state and
prove that no accepted decision is written. The
qualification cases must include correction or revocation, source-policy change
or expiry, and issuer-authority revocation or scope change after snapshot but
before commit.

Cross-document activation tests must accept this proposal as `Proposed` and,
after real human approval, as `Accepted` with Activation still `Deferred` while
the current Phase 51.3 mapping remains authoritative. They must accept
Activation `Active` only in the first accepted default-branch tree that also
contains the aligned Phase 51.3 contract, focused verifier, authoritative
consumers, Activated By and Effective Date metadata, and passing canonical
gates. `Active` with an old contract or verifier, `Deferred` with the new mapping,
metadata-only activation, or any partial or contradictory state must fail
closed. Before approval, `Rejected` is valid only for a denied proposal. After
approval, tests must reject an `Accepted` or `Deferred` ADR changed directly to
`Rejected` and accept withdrawal only through a new Accepted superseding ADR
with atomic Status and Superseded By updates. After activation, tests must accept
deactivation only when one accepted default-branch tree contains that new ADR,
this ADR's Status and Superseded By update, attributable deactivation metadata,
and aligned Phase 51.3 contract, verifier, and consumers while preserving the
original Activated By and Effective Date history; resetting Activation to
`Deferred` or partially applying those changes must fail closed.

## 8. Security Impact

This proposal-only pull request changes no current runtime privileges,
credentials, network exposure, or runtime attack surface. If approved, it would
tighten release-evidence handling by requiring synthetic or reviewed-redacted
inputs and prohibiting retained secret, authorization, customer-private, and
workstation-local material. Real-user and design-partner qualification evidence
would retain only opaque source-authority, subject, organization or engagement,
scope, interval, and version provenance rather than names, email addresses, raw
or directly identifying customer identifiers, raw-to-opaque lookup material, HR
or contract bodies, or private interview notes. Those opaque identifiers remain
sensitive metadata subject to the evidence retention and access boundary; this
ADR does not require a particular tokenization or hashing scheme.
Implementation would add a separately governed GA
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
Approver coverage and review-independence checks would retain opaque source
subjects and reviewed-at membership predicates rather than names, email
addresses, or group rosters, and would grant no new authority or access.

## 9. Rollback / Exit Strategy

Before approval, the proposal can be marked Rejected with no implementation
rollback because it does not alter the accepted baseline.

After approval while Activation is `Deferred`, this ADR cannot be changed to
`Rejected`; withdrawal requires a new Accepted ADR that supersedes it and updates
this ADR's Status and Superseded By metadata in the same accepted default-branch
revision. The original Activation remains `Deferred`, and its pending activation
metadata remains historical because the Phase 51.3 mapping never changed. After
Activation becomes `Active`, any deactivation, rollback, or supersession requires
a new Accepted ADR and one accepted default-branch revision that updates this
ADR's Status and Superseded By metadata, records attributable deactivation
metadata, and aligns the Phase 51.3 contract, focused verifier, and authoritative
consumers. The original Activated By and Effective Date values remain immutable
history and must not be erased or reset to `Deferred`; a partial rollback is
invalid.

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
root-governance and delegation, RC-proof-packet, review-outcome, integrity-
review-outcome, qualification-actor mapping, capability-scope, component,
matrix, material-environment boundary, upgrade-path, credential, cadence,
retention, and evidence snapshots and audit high-water records are irreversible
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
  participant exact sets, direct causal use by at least one participant whose
  source-authority and opaque source-subject identity binds to a pre-existing
  Accepted real-user or design-partner qualification effective throughout the
  execution interval, exact attributable issuer and qualification-acceptance
  actor source subjects, authority provenance and a complete per-qualification
  actor-separation mapping member that binds the decision-bound policy version,
  applicable prohibited-role predicate, exact prohibited-subject set/count/
  digest and immutable source-proof/role mapping, canonical participant
  separation from those mapped actors, and a non-recursive separately governed source-policy
  bootstrap, pre-run criteria and class-environment declaration events
  proven by independent audit ordering, explicit successful outcomes and exactly
  one immutable authoritative owner-review identity and content version per
  journey bound to the run, outcome, criteria, declaration, class, environment,
  interval proof, participant set, accountable owner, attributable actual
  reviewer and revision, with completion-before-review-before-decision
  chronology and only `accepted` or valid mapped non-
  blocking `accepted-with-follow-up` passing as subordinate evidence,
  predeclared independently reviewed journey-level coverage rules whose source
  and covered criteria and accepted review all predate the source journey,
  a complete decision-used rule aggregate and head set with atomic
  every-`evaluated_at` lifecycle re-resolution, unchanged-head recovery, and
  fail-closed correction, revocation, expiry, invalidating supersession, fork,
  gap, mismatch, or replacement behavior,
  direct binding between the same journey environment observation, comparison,
  interval proof and executed environment identities, with either pre-start
  comparison plus authoritative no-material-change evidence through completion
  or a predeclared source-authoritative gap-free attestation for the full
  execution interval, and fail-closed post-run point, backdated, gapped, swapped,
  producer-only or material mid-run-change evidence, plus separate complete
  decision-used journey environment-evidence lifecycle closures whose selected
  chains, exact governing source-policy dependency closure, and evidence and
  policy source-authoritative current heads are re-resolved at every
  `evaluated_at` and fail closed on policy expiry, revocation, supersession,
  source-authority or transition-semantic change, evidence correction,
  challenge, withdrawal, invalidating supersession, fork, gap, stale or rolled-
  back selected-chain HWM, cached non-head or replacement, while unrelated
  monotonic HWM advancement that preserves the selected interval remains valid,
  rejection of owner, role, employment, lab, self-issued, post-run, PII-bearing,
  or interval-invalid qualification substitutes, and preservation of every
  accepted GA metadata field,
- a complete inherited RC set containing the Phase 66.7 packet and independent
  Phase 66.8 closeout result or Accepted-successor authoritative RC-gate result,
  with one-revision binding across that set and every additional GA evidence
  item, fail-closed mixed-snapshot rejection, direct gate-revision execution,
  rejection of cross-revision execution rebinding, a selected RC-proof-packet
  evidence aggregate/current head and exact packet-to-result mapping, inclusion
  of the selected result in the decision-used review-outcome aggregate and head
  closure, authoritative one-way
  `packet selected-head commit < independent result review-and-initial-head commit < GA decision`
  audit ordering that rejects future/reserved packet review and equal, reversed
  or backdated sequence, and atomic complete-chain/current-head re-resolution of
  both packet and result at `decision_at` and every `evaluated_at`, with correction,
  withdrawal, revocation, invalidating supersession, fork, gap, cached non-head,
  replacement or mapping mismatch returning `unavailable`,
- separate complete journey and one-time indexed-execution
  `primary_run_outcome` aggregate/head closures and a separate subordinate
  owner-review aggregate/head closure, with exact bidirectional one-to-one
  index-or-manifest-to-run and run-to-review mappings, one-way declaration or
  target to run to review to decision binding, and atomic complete-chain and
  current-head re-resolution at every `evaluated_at`; preserving historical
  records and allowing only semantics-preserving same-aggregate successors, but
  returning `unavailable` for a corrected, withdrawn, revoked, superseded,
  rejected, expired, forked, gapped, mismatched, cached non-head or replacement
  run or owner-review state, requiring a new owner review and decision, and
  requiring a rerun only when the primary run itself is no longer valid, while
  reusing rather than double-wrapping any equivalent canonical routine-stream
  lifecycle,
- resolution of every GA reference to immutable content or authoritative-record
  state rather than a mutable label, path, URL, or bare identifier,
- one-to-one immutable producer attribution for every indexed evidence root and
  every addressable material-source or transformation node in its complete
  acyclic provenance closure, with shared nodes deduplicated by immutable
  identity; a non-empty direct producer set, immutable source-authority and
  opaque stable source-subject identities and causal provenance on each
  attribution record; exact root-to-node edges and node-to-attribution-
  aggregate/current-head mappings; and one exact attribution-policy dependency
  set binding every governing aggregate, head, Accepted version, source,
  completeness and causal semantics, transition authority and lifecycle. The
  decision-time producer closure and identity-resolution snapshot must bind the
  complete ordered source-subject set, canonical mappings, producer union, set,
  count, digest and high-water mark while rejecting owner, reviewer, custodian,
  root, approval actor, issuer, grantee, submitter, display-name, service-label,
  self-declared or alias substitution. At every `evaluated_at`, the complete
  decision-input root/node partition and the mechanically derived currently
  consumed-review root/node partition, their deduplicated union, origin tags,
  edges, sets, counts and digests must resolve every attribution and governing-
  policy complete chain/current head and source high-water mark; the current
  identity head must bind separate mappings for the fixed subjects, current
  decision-input producers, each consumed review's producers and current-
  successor custodians. Acting-approver, requirements-separation and decision-
  bound review predicates use only the decision-input slices, and each consumed
  review uses only its exact evidence slice. Missing, extra, omitted, newly
  disclosed, retracted, withdrawn, expired, revoked, invalidatingly corrected,
  forked, gapped, stale, substituted, semantically weakened, cached or
  replacement attribution or policy state must fail closed, while semantics-
  preserving same-aggregate successors, unrelated monotonic high-water
  advancement and shared-node deduplication remain valid. A decision-input
  change requires a new decision with only the predicates it actually affects
  repeated; a consumed-review-only change may rebuild its control closure when
  independence remains valid or requires a new applicable review when it does
  not, without changing the historical decision. Attribution,
  lifecycle, mapping and current-closure records remain non-member decision-
  control metadata rather than recursive evidence or producers,
- one complete ordered selected requirements tuple set and an immutable
  requirements-separation closure set with one non-evidence-member closure for
  every selected requirements, approval, target, and execution tuple, exact
  member identities, counts, digests and bidirectional one-to-one mappings, with
  the exact canonical
  requirements approval actor set and complete requirements-author, target-
  author, and exercise-producer slices derived from existing input attribution;
  role-labeled sets, counts, digests, mappings and provenance high-water marks;
  every approval actor absent from all three reviewed-content slices; current-
  identity re-canonicalization at every `evaluated_at`; and missing, extra,
  substituted, stale, ambiguous, alias-conflicting, tuple-mismatched, omitted,
  duplicated, unreferenced, closure-set-mismatched, or later-collapsed mapping
  requiring new approval, target, affected rerun, and decision,
  without requiring the latter three sets to be mutually distinct or treating
  approval/control metadata creation as reviewed-content production,
- one immutable review-independence closure over the complete independent-review
  set and, per review, exact reviewed-evidence identity and canonical producer
  set, using the exact direct producer attribution for non-derived evidence and
  a content-bound complete acyclic global-producer-closure slice containing every
  upstream material-source and transformation producer for derived evidence;
  authoritative ownership snapshot and non-empty exact owner set with count of
  at least one; exact reviewer and
  person-or-group owner source subjects; canonical human reviewer mappings; and
  source-authoritative owner-group membership results effective at `reviewed_at`;
  with per-review reviewer equivalence or membership in that review's exact
  authoritative owner set, or overlap with that review's complete evidence-
  producer set, failing closed, but authorship of the
  review record itself, unrelated evidence, or derived decision-control metadata
  excluded from that per-review producer predicate; and with missing co-owners,
  unknown or stale membership, and retroactive identity, ownership, or
  membership correction failing closed while ordinary later group changes that
  preserve the reviewed-at relationship remain historical; plus exact selected
  ownership-snapshot and direct or transitive group-membership relationship-
  proof aggregate/current-head sets, counts, digests and per-review mappings,
  plus one exact ownership-source and group-resolution policy dependency closure
  with policy aggregate/head/version, source authority, owner completeness,
  direct/transitive membership and transition semantics, set, count, digest and
  relationship-to-policy mappings; whose complete relationship and policy chains
  and source high-water marks are re-resolved in the same current-read boundary
  and compared with the immutable reviewed-at proof, rejecting corrected co-
  owner or membership facts, missing, extra, substituted, unknown, ambiguous,
  expired, revoked, superseded, semantically weakened, forked, gapped, cached
  non-head or replacement relationship or policy state while allowing only
  semantics-preserving same-aggregate successors and without monitoring
  unrelated owner, directory or policy catalogs,
- one complete decision-used `review_outcome` aggregate and current-head closure,
  limited to the selected RC result and every independent GA evidence-review
  event explicitly required by this ADR and used by the decision, without
  recursively wrapping the GA decision, governance approvals, requirements-
  approval or separation-control metadata, or review-control metadata,
  with exact event, evidence, reviewer, authority, outcome, follow-up, scope,
  revision, lifecycle, separately Accepted transition-policy authority and audit
  binding; atomic complete-chain re-resolution at
  every `evaluated_at`; temporary same-chain recovery and only semantics-
  preserving same-aggregate successors allowed; and correction, retraction,
  rejection, revocation, expiry, supersession, fork, gap, favorable non-head
  selection, mismatch or replacement returning `unavailable` and requiring a new
  applicable review or RC result, review-independence closure and GA decision,
  while a later routine successor review is bound only in its evaluated-at
  consumed-review control closure with the exact outcome head, reviewed-evidence
  root-and-reachable-node partition, current producer-attribution and governing-
  policy heads, current producer slice, authoritative owner and membership
  proofs and governing relationship-policy heads, current identity mappings,
  per-review independence result, set, count, digest and audit high-water mark
  resolved in the same current-evaluation
  snapshot, with that member set deterministically derived from and reconciled
  bidirectionally one-to-one to every independent review outcome referenced or
  required by the complete resolved routine successor chains and due or open
  obligations, excluding unrelated and future-not-due reviews and ordinary
  accountable source reviews for which no independent GA review is required,
- an explicit immutable human decision event with attributable outcome, time,
  justification, gate, launch-scope, revision, evidence, and authority bindings,
  with `decision_at` assigned at atomic commit rather than supplied or
  future-dated, plus a non-forking per-decision lifecycle aggregate, one
  canonical non-forking gate-and-launch-scope selection head keyed only by stable
  AegisOps-owned gate-definition and launch-scope identities, at most one current
  accepted decision for that key, explicit expiry posture, and
  snapshot-consistent scope-first current-head evaluation for every authoritative
  current-status decision or projection whose `current`-mode `evaluated_at`, read
  sequence, fence identity and resolved-through high-water marks are assigned and
  bound inside that same linearization boundary rather than caller-supplied,
  backdated, future-dated, or reused; explicit fail-closed `unavailable`
  behavior; separately typed caller-selected historical `as_of` results with no
  current authority; historical-only static references; current effective lifecycle and
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
- one current `accepted` launch-scope-definition head for the canonical scope,
  binding its exact non-empty ordered deployment-class set, count of at least
  one, digest, a non-empty exact customer-deployment or small-production-eligible
  subset with count of at least one and digest, profile and environment-criteria
  identities, explicit profile-version eligibility, and authority provenance;
  Lab-, internal-, exercise-, or training-only classes may be additive but cannot
  satisfy that existential minimum; deterministic
  one-to-one reconciliation of that set to the family-by-class journey index,
  operability class streams, and a non-empty active scope-class requirements
  pair closure whose count equals the class count;
  target and decision-time binding; and atomic every-`evaluated_at`
  re-resolution that rejects missing, extra, duplicate, alias-split,
  wrong-scope, Lab-only, empty or changed eligibility, stale, superseded, or in-
  place-rebound class membership while ignoring inactive historical pairs,
- one exact decision-used deployment-profile and environment-criteria dependency
  closure with aggregate, head, version, usage mapping, set, count, and digest;
  atomic current-head re-resolution at every `evaluated_at` that permits
  temporary recovery or a same-aggregate successor only when the exact Accepted
  version, scope, semantics, and all derived obligations remain unchanged, but
  returns `unavailable` for a missing, forked, gapped, expired, revoked,
  superseded, narrowed, replacement, different-version, or semantically changed
  selected head without monitoring unselected catalog entries,
- separate complete decision-used journey and operability environment-evidence
  aggregate/head closures and one exact governing environment-source-policy
  dependency closure with policy aggregate, head, version, source authority,
  transition semantics, set, count, digest and one-to-one evidence mapping;
  atomic re-resolution of every selected evidence and policy chain/current head
  at each `evaluated_at`, rejecting stale, rolled-back or selected-chain-
  mismatched high-water state, policy expiry, revocation, supersession, authority
  or transition-semantic change, evidence correction, challenge, withdrawal,
  invalidating supersession, fork, gap, cached favorable non-head or replacement,
  while permitting same-chain recovery, semantics-preserving successors and
  unrelated monotonic high-water advancement that leaves the exact historical
  interval and selected chain valid,
- atomic re-resolution at every `evaluated_at` of the exact decision-bound
  scope-class requirements pair closure, every selected stable requirements
  aggregate and current accepted head, and its required-component,
  applicability-matrix, claimed-capacity and material-environment boundaries,
  referenced conservative-equivalence, environment-coverage, cross-class-
  backup-reuse and sequence-equivalence rules, their exact source/target-
  applicability-to-rule and path-edge-to-rule mappings,
  supported-upgrade-path, and credential-family-definition
  child exact sets plus the complete decision-bound requirements tuple and
  requirements-separation closure sets, bidirectional one-to-one mappings,
  approval-actor sets and role-labeled author/producer slices, with temporary same-head
  recovery permitted but missing, forked, gapped, changed, historical, revoked,
  superseded, replacement, missing, extra, duplicate, unreferenced, tuple-
  mismatched, set/count/digest/mapping mismatch or canonical self-approval state
  returning `unavailable` and requiring a new requirements approval, target,
  affected rerun, and new decision rather than in-place rebinding; plus separate
  bidirectional reconciliation of the immutable manifest and decision-input
  concrete restore-target-to-rule-review-and-source-backup mapping against those
  requirements applicability tuples without placing future targets or backups
  in the requirements parent,
- re-resolution at every authoritative current-status evaluation of the exact
  immutable decision-input closure and its AegisOps-owned retention and
  resolvability head, with bytes or record versions, custody, provenance, review,
  retention or legal-hold posture, integrity, complete set and count, and audit
  high-water mark verified rather than replaced by a hash, URL, cache, or
  subordinate surface, including atomic re-resolution of the current
  retention-compatibility head; in current-lifetime mode, the same non-forking
  integrity-review aggregate whose initial head is created in the decision
  cohort with `coverage_start = decision_at` and first slot and next due derived
  from the Accepted cadence, complete input closure, every due or open slot,
  attempt, result and authoritative review-outcome aggregate/current head with
  bidirectional direct slot binding, complete-chain resolution, window and
  deadline compliance and authoritative
  `result completion < accepted review-outcome initial head < integrity-parent successor <= evaluated-at read`
  audit ordering, no future, reserved-only, pre-result, equal, reversed or
  backdated review or unadvanced parent, no delayed, replacement, or reset anchor, no
  stale favorable review after correction, retraction, rejection, revocation,
  expiry or supersession, and no late cure; when the exact cadence version
  requires independence, deterministic inclusion in the evaluated-at consumed-
  review set with the complete slot/cadence origin-edge set, count, digest,
  current producer, owner, membership, policy and identity mappings, per-review
  independence result, and preservation of every origin when one review identity
  is deduplicated; ordinary non-independent slot reviews and future slots remain
  outside that control; or pre-retention invalidation for a no-
  automatic-expiry decision; accepted evaluation before
  the invalidation boundary while the fence and evidence remain valid, missing
  or late transition evidence at or after the boundary returning `unavailable`
  even while bytes remain, early transition producing non-current state, and
  deletion forbidden until the transition and scope-head commit,
- exact retrieval at every `evaluated_at` of the immutable decision-scoped
  identity-resolution head and source snapshot as historical provenance, plus
  use of the source-authoritative current identity head to re-canonicalize both
  the complete fixed decision-bound acting-approver, selected approver-coverage-
  holder, requirements-approval-actor, producer, independent-reviewer, reviewed-
  evidence-owner, custodian, qualification-participant, qualification-issuer,
  qualification-acceptance-actor, each qualification-scoped exact decision-bound
  policy-prohibited-qualification-principal,
  selected root-holder, root-governance-approval-
  actor, and assignment-or-delegation issuer and grantee source-subject set and
  the current credential-successor custodian set; the
  evaluation binds the current head, snapshot, high-water mark, and separate
  exact sets, counts, digests, and mappings, with temporary recovery permitted
  but any missing or substituted fixed subject, fixed-set remap or alias conflict,
  requirements-approval-actor overlap with its exact requirements-author,
  target-author or exercise-producer slice, approver-producer overlap, reviewer-
  owner or evidence-producer conflict,
  custodian alias collapse, qualification participant overlap with its issuer,
  acceptance actor or policy-prohibited principal, root-approval-actor/root-holder or issuer/grantee
  alias collapse, canonical authority-chain cycle, or profile-cardinality failure requiring
  `unavailable` and a new review or decision rather than cached acceptance or
  in-place rebinding; unrelated current-head advancement and a no-weaker current-
  custodian replacement may pass only when all fixed and current mappings remain
  complete and unambiguous,
- atomic re-resolution at every `evaluated_at` of every decision-bound
  participant qualification and governing qualification-source policy aggregate,
  including their complete current lifecycles and heads, exact attributable
  issuer and acceptance-actor source subjects and authority provenance, per-
  qualification policy version and prohibited-role predicate, exact prohibited-
  subject set/count/digest and source-proof/role mappings, one-to-one mapping-set
  reconciliation, and canonical separation from the participant, while
  preserving source and issuer authority and qualification over the complete
  journey interval without rederiving the historical set from a future policy;
  same-aggregate recovery or a valid successor and ordinary post-completion
  relationship end are permitted only when that interval remains valid, but an
  unavailable, missing, forked, gapped, actor- or mapping-mismatched, alias-
  collapsed, self-issued, authority-mismatched, or
  retroactively corrected or revoked interval requires `unavailable`, new
  journey evidence, and a new decision rather than cached acceptance or
  replacement rebinding,
- atomic re-resolution at every `evaluated_at` of the exact support-ownership
  and upgrade-ownership coverage closures and selected heads bound by the
  decision, with each family covering the authoritative deployment-class set
  exactly once through class-specific or an exact scope-wide head, unchanged
  complete mapping recovery after temporary unavailability permitted, but any
  missing, duplicate, overlap, extra, wrong-family, class, scope, alias,
  removal, expiry, retirement, reassignment, supersession, review, or
  replacement mismatch requiring `unavailable` and a new decision rather than
  cached acceptance or in-place rebinding,
- atomic re-resolution at every `evaluated_at` of the exact authoritative
  limitation-registry current head bound by the decision, including scope and
  applicability predicate, complete in-scope non-closed set, count, every
  authoritative state and disposition identity, and audit high-water mark, with
  its current Accepted disposition/currentness-rule head and maximum follow-up
  lifetime or cadence, and each member's currentness rule, review cadence or due
  date, accepted risk, follow-up state, next invalidation boundary, and exact
  decision-bound GA review follow-up obligation origin, policy binding,
  `decision_at < due_at <= maximum_follow_up_due_at`, set and source mapping
  evaluated at that instant;
  unchanged-head recovery after temporary unavailability is permitted only
  while every mapping, maximum-deadline calculation and time-derived posture
  remains valid, but any missing, historical or mismatched policy, duplicate,
  over-maximum, extended, reset, overdue, expired, or blocking follow-up posture or
  in-scope create, update, reopen, close, delete, severity,
  owner, disposition, scope, lifecycle, fork, gap, set, or head change requires
  `unavailable` and a new decision rather than cached acceptance or
  replacement-head rebinding, while an out-of-scope mutation remains isolated,
- proof that the approver held effective, unrevoked GA release authority for the
  recorded launch scope, remained absent from every direct producer set and the
  complete decision-bound canonical producer union, including automation the
  approver initiated, and
  belonged to an immutable profile-derived GA-approver-ownership coverage
  closure that satisfies every deployment class's Accepted minimum, including
  at least two canonically distinct current scope-authorized human holders for a
  small-production SMB class without requiring two signatures, roots, or
  issuers; with the exact holder set, authority heads, and acting membership
  reconciled atomically at decision and every `evaluated_at`; and
  inherited that authority through a non-cyclic, non-self-issued,
  non-scope-widening chain to a separately accepted root authorized by the
  AegisOps-owning organization's competent release-governance authority, with
  immutable external provenance separated from AegisOps-owned mutable authority
  state and serialized revocation, scope, expiry, and supersession reconciliation
  through atomic decision creation, plus atomic re-resolution at every
  `evaluated_at` of the decision-bound root-governance current head and every
  assignment and delegation chain head, with temporary same-chain recovery but
  missing, forked, gapped, expired, revoked, superseded, widened, mismatched,
  cached, or replacement root or chain state immediately returning `unavailable`
  without rewriting the historical event or bypassing the separately authorized
  durable lifecycle transition,
- complete mandatory exercise coverage per deployment class, immutable pre-run
  target declaration with independently recorded chronology, independently
  accepted launch-operability requirements and machine-comparable no-weaker
  target validation, exactly one immutable authoritative owner-review identity
  and content version per indexed execution bound directly to the execution,
  observed result, artifact, target, family, class, environment, accountable
  owner, attributable actual reviewer and revision, with completion-before-
  review-before-decision chronology and only `accepted`
  or valid mapped non-blocking `accepted-with-follow-up` passing, while preserving
  that accountable review as subordinate rather than independent GA authority,
  and with the exact execution's `primary_run_outcome` and subordinate owner-
  review aggregate/current heads present in their respective complete decision-
  bound closures and current at every `evaluated_at`,
  a complete required-component exact set, family-specific
  applicability matrix with Accepted non-applicability provenance, and non-empty
  claimed-capacity-boundary exact set covering every Accepted minimum-resource
  claim through an execution at no-more-favorable resources and no-less-demanding
  workload or a predeclared independently Accepted conservative-equivalence rule
  included as an inseparable current child of the requirements head so any rule
  lifecycle change advances that head and invalidates the target,
  plus a non-empty complete material-environment-boundary exact set of the
  Accepted correlated supported tuples, with every applicable family and member
  covered by a direct bound execution or independently predeclared Accepted no-
  weaker environment-coverage rule that is an inseparable current requirements
  child; without invented Cartesian range or environment combinations; no omission
  of an enabled in-scope component, no fabricated irrelevant metric, and no
  exemption from mandatory family criteria, accepted
  non-self-review bound to each immutable evidence identity, and a complete
  current non-empty supported-upgrade-path exact set with count of at least one
  and every claimed
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
  with every non-identical adjacent-hop substitution using an exact predeclared
  current Accepted sequence-equivalence-rule child and one-to-one path-edge
  mapping whose later actual digests satisfy its no-weaker predicate, while exact
  adjacency has an empty rule member and any rule lifecycle change advances the
  parent requirements head and requires a new target, affected rerun, and decision,
  fixed family-specific freshness and invalidation rules, retained-data hygiene,
  and testable HA, scale, and disaster-recovery dispositions,
- a complete cadence-driven PostgreSQL-aware and configuration-backup stream for
  every deployment class, with authoritative schedule and attempt evidence plus
  an Accepted-scope-derived material-configuration surface, independent
  non-forking transition history, and exact reconciliation to applied
  reviewed-change records and required before or after backups across a current
  gap-free window ending at a reviewed `evidence_cutoff_at`, including every
  boundary-crossing, reverted, or open item and a commit-time zero-delta bridge
  through `decision_at`,
  machine-verifiable comparison proving that every schedule, deadline, grace,
  review, change trigger, state set, and custody obligation is no weaker than its
  governing Accepted profile, integrity, separate custody and retention,
  profile-cadence review, and clean-target restore bound to a backup from that
  stream rather than a historical splice, one-off, or manually prepared source,
  with every cross-class source additionally bound by its exact restore target to
  a predeclared current independently Accepted reuse-rule child, exact accepted
  review-outcome aggregate/current head, eligible source backup and manifest;
  the decision-used review-outcome closure must re-resolve that selected review
  at every `evaluated_at`, and independent audit order must prove immutable rule-
  content commit before review-event-and-initial-head commit, before accepted
  child/requirements-parent commit, before target, before execution; separately,
  backup completion before integrity pass, before accepted backup review, before
  target, before execution; without
  ordering the two reviews against each other or requiring a rule for same-class
  restore,
  while preserving failed attempts and allowing only an eligible on-time clean
  retry for the same slot; plus a stable aggregate identity and complete
  every-`evaluated_at` successor-chain, due-slot, open-item, and time-derived
  currentness reconciliation that allows on-time no-weaker routine successors
  but fails closed on a later gap, miss, unresolved failure, or replacement;
  plus every-`evaluated_at` resolution of the independent configuration-history
  and reviewed-change-registry successor chains and source high-water marks,
  bidirectional transition mapping, regenerated configuration-backup obligations,
  and profile-derived restore-rehearsal schedule, next-due boundary and due or
  open slots, with direct target, execution, result and review binding to one
  immutable slot, execution inside its Accepted eligibility window, deadline-
  bounded completion and review, and one execution per slot unless an exact
  Accepted deterministic no-weaker rule applies; allowing a future restore slot
  and an on-time reviewed successor but rejecting an unregistered, hidden,
  reverted, wrong-order, or unbacked material change and a pre-window, cross-
  slot, duplicated, missing, late, failed, unreviewed, wrong-source, wrong-
  revision, wrong-target, or profile-weaker restore without turning other heavy
  exercises into periodic streams,
- a current gap-free operator-health and platform-hygiene stream for every class,
  with each schedule subinterval bound to its governing profile, no-weaker
  cadence, exact due-review and carried-open finding, escalation, and follow-up
  reconciliation through a reviewed cutoff plus zero-delta commit bridge, one
  independent aggregate review, eligible same-slot on-time re-review, and no
  matrix waiver or substitution by one fresh diagnostic; plus a stable aggregate
  identity and complete every-`evaluated_at` successor-chain, due-slot, open-
  finding, and time-derived currentness reconciliation that allows on-time no-
  weaker routine successors but fails closed on a later gap, overdue review,
  unresolved blocker, or replacement,
- machine-verifiable journey and operability environment comparison against
  current immutable Accepted profile criteria, with producer dispositions and
  class labels unable to waive missing, incomparable, out-of-tolerance, or
  weakening dimensions; a complete per-class material correlated-variant set,
  count, digest and family-by-member direct-or-conservative coverage mapping that
  rejects one-variant shortcuts, post-hoc or historical rules and unapproved
  Cartesian products without enumerating unclaimed variants; each operability
  target and execution binds the same
  immutable observation and comparison identity and proves either pre-start
  audit ordering plus no material compared-dimension change through completion,
  or a predeclared source-authoritative attestation enclosing the full execution
  interval, with post-run points, backdating, swaps, gaps, and mid-run material
  changes rejected; separate complete journey and operability environment-
  evidence aggregate/head closures fixed as historical decision provenance and
  every selected aggregate's complete current chain, source head and high-water
  mark re-resolved at each `evaluated_at`, with same-valid-chain recovery and
  semantics-preserving successors allowed but corrections, challenges,
  withdrawals, revocations, invalidating supersessions, forks, gaps, cached
  favorable non-heads, or replacement rebinding returning `unavailable`,
- a complete immutable credential-family definition exact set in the
  requirements head, containing only governing owner, consumer, scope,
  delivery, custody, policy, cadence, trigger, event-schema, and no-weaker
  obligations, plus an exactly reconciled current manifest snapshot with actual
  owner and custody heads, a non-forking Accepted policy lifecycle that cannot
  reset coverage, every due, boundary-crossing, or open rotation outcome through
  the reviewed cutoff and commit bridge, next due boundary, and exact
  break-glass set, bounded use, and return-to-normal closeout, without retaining
  raw secret values or invalidating targets for ordinary observed events, plus
  every-`evaluated_at` resolution of the same stable aggregate's complete
  successor chain, allowing only complete on-time accepted and no-weaker routine
  successors while failing closed on unavailable, missing, forked, gapped,
  omitted, overdue, failed, open, unreviewed, weaker, or replacement state, and
  binding every custodian to source-authority and opaque source-subject identity
  with decision-time and current-successor canonical-human mapping, exact set,
  count and digest, and profile-derived two-person cardinality without alias
  double counting or imposing that minimum on other profiles,
- a current non-forking launch-scope-definition head with a canonical
  deployment-class exact set, deterministic scope-class pair closure, and exact
  decision-used profile-and-criteria lifecycle dependency closure, plus current
  launch-requirements heads and complete required-component,
  applicability-matrix, claimed-capacity-boundary, referenced conservative-
  equivalence-rule, and supported-upgrade-path exact sets at target declaration,
  decision, and every `evaluated_at`, with any scope, class, lifecycle, component,
  matrix, capacity-boundary, equivalence-rule, compatibility, migration, or
  rollback change requiring `unavailable`, new declarations,
  targets, affected execution, and a new decision,
- an immutable authoritative limitation-registry current head and snapshot,
  exact reconciliation of every in-scope non-closed and newly surfaced
  limitation, and independently reviewed evidence when no blocking limitation
  is known, with transaction or audit high-water-mark reconciliation through
  the atomic decision boundary and exact-head re-resolution at every later
  `evaluated_at`,
- one immutable decision-time mutable-state cohort covering the expected
  canonical scope-head predecessor, launch-scope-definition, class and non-empty
  launch-eligible-subset closures,
  exact profile-and-criteria dependency closure and current-at-decision heads,
  lifecycle and expiry policy, journey qualification, exact attributable issuer/
  acceptance-actor mapping and canonical separation, and its exact environment-
  observation, comparison, interval-proof and audit-high-water state and separate
  environment-evidence lifecycle aggregate/head closure, exact governing
  environment-source-policy dependency closure and selected current policy heads,
  operability environment observation, comparison, interval proof and audit
  high-water and separate environment-evidence lifecycle aggregate/head closure,
  requirements child sets including claimed-capacity and material-
  environment boundaries, conservative-equivalence and environment-coverage
  rules plus the complete requirements tuple set, requirements-separation closure
  set and bidirectional tuple mapping, and every approval-actor mapping,
  backup and health stable aggregates, current
  heads and cadence, material-configuration surface, independent history,
  reviewed-change and derived backup-obligation reconciliation, restore-
  rehearsal schedule and currentness, immutable credential definitions and separate
  current lifecycle, event, and custody state, support and upgrade ownership
  heads and coverage closures, decision-used journey-rule lifecycles,
  selected RC-proof-packet aggregate/head and packet-to-result mapping,
  decision-used review-outcome lifecycles and closure, separate subordinate
  owner-review lifecycles and closure, journey and one-time execution primary-
  run-outcome lifecycles and closures, exact producer-attribution aggregate/
  current-head and root/node mappings, governing attribution-policy heads and
  immutable producer closure, reviewed-at ownership and membership relationship-
  proof aggregate/current-head sets, exact governing relationship-policy
  dependency closure and review-independence state, profile-derived
  approver-ownership coverage and selected-holder authority, limitations and
  disposition/currentness policy, claimed-capability authority, evidence
  retention and compatibility plus current-lifetime integrity-review state and
  exact slot-bound review-outcome aggregate/head mappings,
  source-authoritative decision-bound historical identity resolution including
  every requirements approval actor, qualification participant, qualification
  issuer, qualification acceptance actor, policy-prohibited qualification
  principal, selected root holder, root approval actor,
  issuer and grantee, and
  release-authority root-governance and complete assignment/delegation chain with
  canonical distinctness and cycle predicates,
  with every decision-time current head reconciled
  through atomic decision creation
  and concurrent mutation failing closed, plus reviewed cadence-stream cutoffs
  whose detached aggregate-review identity and strict
  `cutoff < review and initial outcome head < review attribution < reviewed-at
owner and membership proofs < producer closure < review independence closure <
review-outcome closure < decision` audit ordering is
  bound explicitly, whose operational
  zero-delta comparison excludes only the reserved exact attestation, its
  inseparable initial outcome head and attribution, reviewed-at owner and
  membership proofs, the deterministic producer, review-independence and review-
  outcome closures, required decision-control head
  advances, and decision-attempt
  bookkeeping, and whose mismatch aborts and releases the boundary before any
  renewed human review,
- a current append-only, non-forking capability-scope-authority head for every
  claimed HA, multi-site disaster-recovery, or fleet-scale capability, bound to
  an immutable separately Accepted authority source at target declaration,
  decision, and current evaluation, with exercise success prohibited from
  authorizing or widening launch scope and obsolete authority unable to rebind an
  existing decision,
- complete approval metadata when the status changes, with human approval
  leaving Activation `Deferred`, Phase 51.3 authoritative, and Activated By and
  Effective Date pending until one accepted default-branch revision atomically
  changes Activation to `Active`, records its metadata, aligns the Phase 51.3
  contract, focused verifier, and authoritative consumers, and passes the
  canonical gates; every partial or contradictory cross-document state fails
  closed, and
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
- Human approval alone does not activate this decision or supersede Phase 51.3;
  activation remains deferred until the coordinated implementation revision.
- This proposal does not implement or enforce its proposed boundary.
- This proposal does not designate an initial GA authority root or grant GA
  release authority.
- This proposal does not require two GA signatures, authority roots, or issuers;
  profile-derived approver ownership is staffing coverage, and one eligible
  acting approver remains accountable for each decision.
- This proposal does not require direct production access or customer data;
  retained evidence remains restricted by Section 2.
- This proposal does not prohibit the privacy-minimized opaque source-subject,
  organization, or engagement identifiers required by Section 2, but it does
  prohibit co-retained raw identities or lookup material.
- This proposal does not require a specific HR, CRM, IdP, contract, or
  engagement system, retain its raw records, or restrict qualifying real users
  to external personnel; it requires only the accepted, privacy-minimized,
  source-authoritative qualification boundary defined in Section 2.
- This proposal does not require qualification issuance and acceptance to use
  two people, two signatures, or an external person when the Accepted source
  policy permits one canonically distinct actor to perform both; it resolves
  only each exact claimed qualification's participant, issuer, acceptance actor
  and decision-bound policy-derived prohibited-principal set and does not
  synchronize an enterprise directory or apply one qualification's policy slice
  to another.
- This proposal does not place every catalog profile, environment instance,
  host, tenant, customer, or historical scope-class pair into the declared
  launch scope.
- This proposal does not require every launch class to be production eligible or
  authorize live rollout merely because one class is customer-deployment or
  small-production eligible; it only prevents a Lab-only GA scope.
- This proposal does not monitor unselected profile or criteria catalog entries;
  current-head resolution is limited to the exact decision-used dependency
  closure.
- This proposal does not require capacity execution at every intermediate range
  point or an invented Cartesian product of resource ranges; it requires only
  exact coverage of the Accepted claimed boundary tuples.
- This proposal does not enumerate every host, patch, optional variant, or
  Cartesian environment combination or create multi-architecture, HA, or public
  compatibility support; it covers only material correlated tuples claimed by
  the current Accepted profile and criteria.
- This proposal does not require every historical or incompatible version pair,
  but under the current Accepted lineage it does not invent a first-release or
  no-predecessor exception to the non-empty supported-path requirement.
- This proposal does not require a cross-class backup-reuse rule for a same-
  class restore or any unused class pair, and a selected rule cannot expand the
  launch scope, source eligibility, or restore cadence by itself. Only the
  explicitly selected rule's independent review uses the bounded review-outcome
  lifecycle; this does not recursively review its control metadata or create a
  review for a same-class restore.
- This proposal does not require a sequence-equivalence rule for a direct path,
  an exactly identical adjacent-hop output and input, or an unreferenced rule
  catalog, and it does not add silent, automatic, or zero-downtime upgrade
  support or a public compatibility commitment.
- This proposal does not require a different support or upgrade owner for every
  class or family, separate support and upgrade teams, external support, 24x7
  staffing, or per-host, tenant, or customer ownership; one accountable person
  or team may cover multiple cells when each family closure remains complete.
- This proposal does not mandate a CMDB, host-write monitoring agent, or vendor
  configuration service, continuous or per-second environment telemetry, and
  does not retain raw configuration or secret values; environment-evidence
  currentness resolves only the exact decision-used claim aggregates.
- This proposal does not make capacity, interruption, upgrade, rollback, or
  other heavy exercises periodic; continuing restore rehearsal follows only the
  cadence, calendar, deadline, and grace already defined by the applicable
  Accepted profile.
- This proposal does not invent a fixed integrity-review or follow-up duration,
  require hot storage or an enterprise scheduler, or create a public response
  commitment; those machine-verifiable bounds come only from their separately
  Accepted retention or limitation policies.
- This proposal does not create a producer role, require enterprise-wide
  directory synchronization, or classify passive tool, library, vendor, owner,
  reviewer, or custodian identities as producers without direct causal evidence.
- This proposal does not make producer-attribution or reviewed-at relationship-
  proof lifecycle records, their current closures, identity mappings, or other
  decision-control metadata recursive evidence members or producers of the
  evidence whose currentness they verify, and it does not monitor unrelated
  source, directory, ownership, membership, policy, or audit catalogs. A future-
  only no-weaker governing-policy successor does not invalidate historical
  evidence or review facts whose bound version and applicable semantics remain
  accepted and unchanged.
- This proposal does not create periodic re-review or monitor unrelated review
  catalogs; review-outcome currentness applies only to reviews or RC results
  consumed by the decision or a current evaluation.
- This proposal does not automatically make a periodic integrity review an
  independent GA review or a consumed-review-control member; its authoritative
  outcome lifecycle is slot state, and independence applies only when the
  governing Accepted cadence rule explicitly requires it. That conditional
  check does not create a blanket second reviewer, add future slots to the
  immutable decision cohort, or monitor unrelated reviews.
- This proposal does not monitor every Phase 66 packet or repository artifact,
  promote a proof packet into RC or GA authority, or rerun Phase 66.1-66.6 for a
  temporary read outage or metadata-only same-packet successor; currentness is
  limited to the exact selected packet and its exact selected-result mapping.
- This proposal does not make a journey or one-time operability exercise
  periodic merely because its primary-run and subordinate owner-review outcomes
  have current lifecycle heads; only an invalidated primary run requires a new
  execution, while a review-only invalidation requires a new applicable review
  and GA decision.
- This proposal does not turn an accountable journey or execution owner review into GA
  release authority, an independent review, or a second-person approval unless
  that same record is separately selected under the independent-review rules.
  The accountable owner may also be the attributable actual reviewer unless a
  separately Accepted source contract requires distinct principals.
- This proposal does not require the requirements author, target author, and
  exercise producer to be mutually distinct or create four-person approval; only
  the attributable requirements approval actor must remain canonically distinct
  from those exact reviewed-content producer slices.
- This proposal does not remove historical `as_of` audit queries or require a
  status-read transaction to remain open through UI rendering; a historical
  result simply has no current GA, release, or rollout authority.
- This proposal does not place external charter bytes in every database
  transaction or require repeated root designation; current evaluation resolves
  only the AegisOps-owned root-governance and authority-chain state that binds
  that immutable provenance.
- This proposal does not require dual signatures, simultaneous two-person secret
  handling, or two-person custody for a profile that does not require it; it
  canonicalizes the humans counted by each applicable profile minimum.
- This proposal does not treat shared organization, department, or role
  membership as an owner conflict or retain group rosters or personal identity
  fields; only privacy-minimized source subjects and the relationship to the
  named evidence owner at review time are evaluated.
- This proposal does not establish a public SLA, 24x7 support commitment,
  enterprise HA or multi-site disaster-recovery scope, fleet-scale
  certification, or multi-tenant readiness.

## 12. Approval

- **Proposed By**: Codex for PR #1424
- **Reviewed By**: Pending
- **Approved By**: Pending
- **Approval Date**: Pending
- **Activation**: Deferred
- **Activated By**: Pending
- **Effective Date**: Pending
