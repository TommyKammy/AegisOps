# AegisOps Phase 25 Reviewed Multi-Source Case Admission and Ambiguity Taxonomy

## 1. Purpose

This document defines the reviewed multi-source case admission contract and the ambiguity taxonomy for bounded cross-source casework.

It supplements `README.md`, `docs/architecture.md`, `docs/control-plane-state-model.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, and `docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md`.

This document defines reviewed multi-source case admission, provenance, and operator-display rules only. It does not authorize automatic entity stitching, substrate-local truth promotion, new execution authority, or broad cross-source correlation beyond the reviewed case chain.

## 2. Scope and Reviewed Source Set

The approved reviewed multi-source case admission slice is intentionally narrow.

It allows reviewed casework to combine evidence from:

- GitHub audit context;
- the approved second reviewed source family for this slice (`entra_id`), which has completed its reviewed onboarding boundary; and
- osquery-backed host evidence attached as reviewed augmentation.

The bounded source set exists to support richer operator review without redefining case truth around whichever substrate currently exposes the most nearby metadata.

osquery-backed host evidence is an augmenter only.

It may contribute reviewed host, process, and local-state evidence, but it must not become the authority for case identity, actor identity, approval truth, or lifecycle truth.

## 3. Case Admission Contract

### 3.1 Admission Preconditions

Reviewed multi-source case admission may occur only when all of the following are true:

- one authoritative anchor record already exists on the reviewed case chain;
- each added source record is explicitly linked to that anchor record or to a directly linked reviewed record;
- the link is supported by stable identifiers, reviewed binding fields, or an explicit reviewed relationship record;
- the attached source record preserves enough provenance to show where it came from, who reviewed it, and which reviewed case-chain record admitted it; and
- the resulting case still preserves unresolved ambiguity instead of hiding it behind a merged summary.

If any prerequisite is missing, malformed, partially trusted, or only implied by nearby metadata, the path must fail closed.

### 3.2 Authoritative Anchor Record

Every reviewed multi-source case must keep one authoritative anchor record.

The authoritative anchor record is the reviewed `Case` or directly linked reviewed control-plane record that already owns the operator-facing scope under review.

Admission works outward from that anchor.

The system must not pick the winning identity, subject, or scope from whichever substrate summary appears newest, loudest, or more operator-friendly.

### 3.3 Allowed Linkage Signals

Admission may rely on:

- reviewed case identifiers;
- stable source-specific identifiers already preserved on reviewed records;
- reviewed evidence linkage fields;
- reviewed context identifiers already accepted on the control-plane chain; and
- explicit reviewed relationship records that say why one source record is attached to another.

Admission must not rely on:

- display-name similarity;
- repository, host, or account naming conventions;
- path shape, ticket text, comments, or analyst free text alone;
- raw forwarded headers or client-supplied identity fields;
- source-local badge text; or
- proximity in time without explicit reviewed linkage.

If a source can only be attached by weak inference, the case must stay `unresolved` for that linkage decision.

## 4. same-entity / related-entity / unresolved Taxonomy

This document defines one reviewed same-entity / related-entity / unresolved taxonomy for reviewed multi-source casework.

The taxonomy must be used consistently across case detail, case timeline, evidence detail, assistant summaries, ambiguity badges, and later validation work.

### 4.1 `same-entity`

`same-entity` may be used only when reviewed records prove that two records refer to the same actor, asset, repository, account, host, process, or other scoped subject.

Required support for `same-entity`:

- either stable identifiers match across the compared records, or one reviewed record explicitly binds the two identifiers as the same subject; and
- provenance remains visible enough for an operator to inspect the supporting reviewed records.

`same-entity` must not be inferred from alias-style similarity, nearby metadata, or operator expectation.

### 4.2 `related-entity`

`related-entity` may be used when reviewed records prove that two records are linked but do not prove they are the same subject.

Examples include:

- the same GitHub issue linked to a host under review;
- a reviewed source record attached to the same case through a shared recommendation or evidence chain; or
- osquery-backed host evidence attached to a case because the reviewed anchor record already scoped that host as relevant.

`related-entity` means "linked for reviewed casework," not "interchangeable identity."

### 4.3 `unresolved`

`unresolved` must be used when reviewed records cannot justify either `same-entity` or `related-entity` with trusted linkage.

`unresolved` is mandatory when:

- stable identifiers are missing;
- stable identifiers conflict;
- provenance is partial or unreviewed;
- one source suggests equality and another does not;
- osquery-backed host evidence appears nearby but the reviewed case chain does not explicitly bind it; or
- an operator or assistant request would require the system to choose a stronger linkage than the reviewed record chain currently supports.

When `unresolved` applies, the system must fail closed and preserve the guard instead of rendering a weak merge.

## 5. Provenance Classification and Evidence Roles

This section defines the Phase 25 reviewed multi-source implementation target.
These requirements are forward-looking design constraints for Phase 25 follow-on implementation work; they do not claim that pre-Phase-25 runtime surfaces already persist this contract today.

Every admitted multi-source record must keep an explicit provenance classification.

For this slice, the authoritative reviewed control-plane storage contract is `record.provenance`.

Pre-Phase-25 compatibility paths may still expose admission provenance through `reviewed_context.provenance` or `admission_provenance`, but those legacy surfaces do not satisfy this reviewed multi-source contract on their own.

Implementations must write and read `record.provenance.classification` as the authoritative provenance-classification field for enforcement and validation.

Implementations must also persist `record.provenance.source_id`, `record.provenance.timestamp`, and `record.provenance.reviewed_by` so operators and validators can trace the reviewed provenance origin, review attribution, and admission accountability without relying on UI-only metadata.

If an implementation also exposes `reviewed_context.provenance_classification` for compatibility with reviewed-context surfaces, that alias is optional and must mirror `record.provenance.classification`.

`reviewed_context` may support display compatibility, but it must not replace `record.provenance.*` as the authoritative storage contract for this reviewed multi-source slice.

Minimum provenance classifications for this slice:

| Classification | Meaning |
| --- | --- |
| `authoritative-anchor` | The reviewed case-chain record that owns scope for the current reviewed casework surface. |
| `reviewed-direct` | A reviewed record directly linked to the authoritative anchor record. |
| `reviewed-derived` | A reviewed record linked through another reviewed case-chain record with an explicit durable relationship. |
| `augmenting-evidence` | Additional reviewed evidence, such as osquery-backed host evidence, that augments the case without becoming case truth. |
| `unresolved-linkage` | A candidate source record that may be relevant but lacks trusted linkage strong enough for `same-entity` or `related-entity`. |

GitHub audit context and the approved `entra_id` reviewed source family for this slice may appear as `reviewed-direct` or `reviewed-derived` depending on how the reviewed case chain links them.

osquery-backed host evidence is expected to appear as `augmenting-evidence` unless a later reviewed record explicitly promotes a narrower relationship for a specific claim.

osquery-backed host evidence must not silently become the authoritative anchor record.

## 6. Operator-Facing Ambiguity Display

This section defines the operator-facing ambiguity display for reviewed multi-source casework.

Operators must be able to see why evidence appears together on one reviewed case without relying on substrate-local UI.

The reviewed case chain must expose, at minimum:

- the authoritative anchor record;
- the taxonomy state for each non-anchor attached record;
- the provenance classification for each attached record;
- the reviewed linkage or missing linkage that justified the current state; and
- the blocking reason when a record remains `unresolved`.

Each attached record must surface exactly one provenance badge.

Each attached record that is not the authoritative anchor must also surface exactly one ambiguity badge.

The provenance badge must identify whether the record is `authoritative-anchor`, `reviewed-direct`, `reviewed-derived`, `augmenting-evidence`, or `unresolved-linkage`.

The ambiguity badge applies only to attached records that are not the authoritative anchor and must identify whether the record is `same-entity`, `related-entity`, or `unresolved`.

Operator-facing ambiguity display must render from reviewed control-plane fields and reviewed linkage records, not from substrate-local UI summaries.

Substrate-local UI may remain useful for drill-down, but it must not be required to understand why the control plane grouped records into one case.

## 7. Fail-Closed Multi-Source Rules

This reviewed multi-source case admission contract must fail closed.

Trust-blocking conditions that must reject stronger linkage or force `unresolved` include:

- required provenance fields are missing;
- the authoritative anchor record is missing or ambiguous;
- the attached source record has no explicit reviewed relationship to the case chain;
- stable identifiers are absent, mismatched, or only partially trusted;
- a stronger linkage would require stitching entities automatically;
- the only support for linkage is alias-style similarity, timing proximity, or nearby metadata;
- the assistant or operator surface would need to collapse ambiguity to produce a cleaner summary; or
- one surface tries to widen a relation beyond the directly linked authoritative record.

The system must fail closed and must not stitch entities automatically.

If a reviewer cannot explain the linkage from reviewed records and stable identifiers, the stronger linkage is not admitted.

## 8. Alignment with Assistant Unresolved Handling

The ambiguity taxonomy in this document must stay aligned with the existing assistant unresolved model.

That means:

- Phase 15 identity-grounded assistant rules still control whether identity ambiguity can be collapsed;
- the Phase 24 trusted output contract remains advisory-only and must force `unresolved` when reviewed grounding is incomplete or conflicting; and
- later assistant, timeline, and case-detail surfaces must reuse this same taxonomy rather than invent a looser multi-source interpretation.

Reviewed multi-source casework must not create one ambiguity model for operator case surfaces and another for assistant summaries.

If a case detail surface classifies linkage as `unresolved`, the assistant must not restate it as `same-entity` or `related-entity` without a new authoritative reviewed link.

## 9. Non-Expansion Rules

This document does not authorize:

- broad source-family onboarding beyond the bounded reviewed source set;
- automatic entity stitching across source families;
- source-local identity truth promotion into the control plane;
- osquery-backed host evidence as case truth;
- broad cross-source search or free-form correlation as a substitute for reviewed linkage; or
- any authority expansion beyond the reviewed case chain and the advisory-only assistant boundary.

Future source expansion, broader correlation, or stronger stitching behavior requires a separate reviewed design decision.
