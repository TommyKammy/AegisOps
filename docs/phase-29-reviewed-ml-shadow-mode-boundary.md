# AegisOps Phase 29 Reviewed ML Shadow-Mode Boundary

## 1. Purpose

This document defines the reviewed ML shadow-mode boundary for AegisOps before any model implementation, experiment tracking, or scoring pipeline exists.

It supplements `README.md`, `docs/architecture.md`, `docs/control-plane-state-model.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, `docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md`, and `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`.

This document defines reviewed feature, label, provenance, and shadow-output rules only. It does not approve model implementation, live scoring, workflow automation, authority expansion, or hidden policy interpretation.

The reviewed ML shadow-mode boundary must keep ML advisory-only and must remain outside the authority path for alert admission, approval grant or reject, delegation, execution policy, reconciliation truth, and case truth promotion.

## 2. Boundary Statement

The reviewed ML shadow-mode boundary exists to let later implementation work evaluate bounded model outputs without redefining the AegisOps control-plane authority model.

Within this boundary:

- ML may consume reviewed records and reviewed fields that have already been admitted to the authoritative control-plane chain.
- ML may emit shadow-only operator assistance in the shape of `Observation`, `Lead`, or `Recommendation draft` assistance.
- ML output remains advisory-only and must not mutate authoritative lifecycle state on its own.

Outside this boundary:

- ML must remain outside the authority path for alert admission;
- ML must remain outside the authority path for approval grant or reject;
- ML must remain outside the authority path for delegation or execution policy;
- ML must remain outside the authority path for reconciliation truth; and
- ML must remain outside the authority path for case truth promotion.

Scores, rank values, label predictions, or model confidence must not be treated as equivalent to reviewed operator judgment, approval state, case state, or reconciliation outcome.

## 3. Allowed Reviewed Feature Sources

This section defines the allowed reviewed feature sources for the reviewed ML shadow-mode boundary.

Allowed reviewed feature sources are intentionally narrow and must already exist on the reviewed control-plane chain.

Allowed reviewed feature sources:

- `Alert` reviewed fields that preserve admitted source, severity, bounded reviewed context, explicit lifecycle state, and stable identifiers;
- `Case` reviewed fields that preserve scoped ownership, explicit lifecycle state, linked source set, and bounded reviewed context;
- `Evidence` reviewed fields that preserve explicit provenance, evidence type, validation state, and durable linkage to the alert or case chain;
- `Observation` reviewed fields only when the observation is already reviewed and linked to supporting evidence or explicit scoped casework;
- `Lead` reviewed fields only when the lead is already reviewed, bounded, and linked to the reviewed chain as candidate investigative direction;
- `Recommendation` reviewed fields only when the recommendation is already recorded as a reviewed control-plane record rather than prompt-only text;
- `Approval Decision`, `Action Request`, `Action Execution`, and `Reconciliation` reviewed fields only as non-authoritative historical context for later analysis, not as a live policy shortcut; and
- `AI Trace` reviewed fields only when they are explicitly preserved as reviewed control-plane records and are used as lineage context rather than authority.

Feature extraction must not consume:

- raw substrate-local summaries as if they were already reviewed control-plane facts;
- free-form prompt text, comments, or nearby metadata without explicit reviewed linkage;
- raw forwarded headers, client-supplied identity hints, or other untrusted boundary inputs;
- coordination-substrate lifecycle fields as if they were case or approval truth; or
- any field whose current meaning depends on future interpretation instead of a reviewed control-plane definition.

If a candidate feature source is missing, malformed, stale, partially trusted, or only implied by nearby metadata, the feature path must fail closed.

## 4. Allowed Reviewed Labels

This section defines the allowed reviewed labels for the reviewed ML shadow-mode boundary.

Allowed reviewed labels must come from explicit reviewed control-plane records and must preserve the exact record that supplied the label decision.

Allowed reviewed labels:

- reviewed `Observation` outcomes, such as whether an observation remained `confirmed`, `challenged`, `superseded`, or `withdrawn`;
- reviewed `Lead` outcomes, such as whether a lead remained open, was dismissed, or was promoted through an explicitly linked alert or case path;
- reviewed `Recommendation` review outcomes, such as accepted, rejected, superseded, or withdrawn recommendation state when that state is already explicit on the reviewed record;
- reviewed `Approval Decision` outcomes only as historical labels for later analysis of recommendation quality, never as a live approval shortcut;
- reviewed `Reconciliation` outcomes only as historical labels for mismatch-learning analysis, never as live reconciliation truth; and
- explicitly reviewed operator taxonomy states such as `same-entity`, `related-entity`, or `unresolved` only when the reviewed case chain already recorded them authoritatively.

Allowed reviewed labels must not be inferred from:

- unreviewed assistant text;
- ticket-system comments or queue movement;
- execution-surface runtime receipts without the governing reviewed control-plane record;
- missing follow-up records interpreted as implied success; or
- case notes, naming conventions, or lineage-relative records that do not explicitly own the label decision.

The system must not infer a label from silence, absence, partial lineage, or nearby metadata. If no authoritative reviewed label exists, the example remains unlabeled.

## 5. Allowed Shadow-Only Output Surface

The allowed shadow-only output surface is intentionally narrow.

Shadow output may help operators review possible investigative or explanatory material, but it must not write authoritative state by implication.

Allowed shadow-only output surface:

- `Observation` assistance that proposes a candidate observation for reviewer confirmation;
- `Lead` assistance that proposes a candidate investigative direction for reviewer confirmation; and
- `Recommendation draft` assistance that proposes a draft next-step recommendation for reviewer confirmation.

Shadow output must not:

- create or admit an `Alert`;
- promote or close a `Case`;
- create an `Approval Decision`;
- issue or mutate an `Action Request`;
- authorize delegation or execution;
- resolve or overwrite `Reconciliation`; or
- silently mutate evidence custody, reviewed provenance, or lifecycle truth.

The reviewed ML shadow-mode boundary does not approve hidden score-only routing, auto-closure, auto-promotion, or authority-bearing workflow state under another name.

## 6. Provenance Contracts

Every feature, label, model artifact, and shadow output must preserve explicit lineage back to the reviewed control-plane chain.

### 6.0 ML lineage envelope semantics

The identifiers in Sections 6.1 through 6.4 define a separate ML lineage envelope namespace.

They do not rename, replace, or relax the reviewed record-level provenance fields already used on control-plane records such as `provenance.source_family`, `provenance.source_system`, `provenance.source_id`, `provenance.classification`, and `provenance.reviewed_by`.

Implementations must preserve the original reviewed record identity and provenance keys on the source record and must preserve a deterministic mapping from that reviewed record into the ML lineage envelope.

The ML lineage envelope exists so later feature, label, model, and shadow-output work can record extraction-time lineage without redefining the reviewed control-plane record schema.

At minimum, implementations must preserve and validate mappings such as:

- `feature_source_record_family` = the reviewed control-plane record family that supplied the feature, such as `Alert`, `Case`, `Evidence`, `Observation`, `Lead`, `Recommendation`, `Approval Decision`, `Action Request`, `Action Execution`, `Reconciliation`, or `AI Trace`; this is not an alias for `provenance.source_family` or `provenance.source_system`;
- `feature_source_record_id` = the durable identifier of that reviewed control-plane record, such as `alert_id`, `case_id`, `evidence_id`, `observation_id`, `lead_id`, `recommendation_id`, `approval_decision_id`, `action_request_id`, `action_execution_id`, `reconciliation_id`, or `ai_trace_id`; this is not an alias for `provenance.source_id`;
- `feature_source_field_path` = the canonical field path inside the reviewed control-plane record that supplied the extracted value;
- `feature_source_provenance_classification` = the reviewed record's `provenance.classification` value when the source record preserves it;
- `feature_source_reviewed_by` = the reviewed record's `provenance.reviewed_by` value when the source record preserves reviewer attribution;
- `label_record_family` = the reviewed control-plane record family that owns the label decision, rather than a source-substrate family name;
- `label_record_id` = the durable identifier of the exact reviewed control-plane record that owns the label decision, rather than a source-substrate identifier; and
- `label_linked_subject_record_id` = the durable identifier of the reviewed subject record to which the label decision was explicitly linked.

If a reviewed record lacks the identity, provenance, or mapping data needed to populate the ML lineage envelope without ambiguity, the ML path must fail closed instead of inventing aliases or inferred lineage.

### 6.1 Feature provenance contract

The feature provenance contract must preserve, at minimum:

- `feature_source_record_family`;
- `feature_source_record_id`;
- `feature_source_field_path`;
- `feature_extraction_spec_version`;
- `feature_snapshot_timestamp`;
- `feature_reviewed_linkage`;
- `feature_source_provenance_classification`; and
- `feature_source_reviewed_by` when the source record preserves reviewer attribution.

Feature provenance must allow a reviewer to explain which reviewed record supplied the feature, which field was extracted, which extraction spec version applied, and whether the source was direct, derived, augmenting, or unresolved.

### 6.2 Label provenance contract

The label provenance contract must preserve, at minimum:

- `label_record_family`;
- `label_record_id`;
- `label_field_path`;
- `label_decision_basis`;
- `label_decided_at`;
- `label_reviewed_by`; and
- `label_linked_subject_record_id`.

The label provenance contract must preserve the exact reviewed record and field that justified the label instead of collapsing labels into a synthetic training-table assertion.

### 6.3 Model lineage contract

The model lineage contract must preserve, at minimum:

- `model_family`;
- `model_version`;
- `training_data_snapshot_id`;
- `training_spec_version`;
- `feature_schema_version`;
- `label_schema_version`;
- `training_started_at`;
- `training_completed_at`; and
- `lineage_review_note_id` or equivalent reviewed lineage reference.

Model lineage must make it possible to trace which reviewed feature schema and reviewed label schema produced the model artifact without treating the model as a new authority surface.

### 6.4 Shadow output lineage contract

The shadow output lineage contract must preserve, at minimum:

- `shadow_output_id`;
- `shadow_output_type`;
- `model_family`;
- `model_version`;
- `input_snapshot_id`;
- `rendered_at`;
- `subject_record_family`;
- `subject_record_id`;
- `supporting_feature_snapshot_id`; and
- `review_required`.

Shadow output lineage must keep rendered assistance anchored to the exact reviewed subject record and the exact model and feature snapshot that produced it.

## 7. Fail-Closed and Degraded Handling

The reviewed ML shadow-mode boundary must fail closed.

Trust-blocking conditions include:

- missing labels;
- missing reviewed linkage for a feature source;
- source-health degradation that makes feature freshness or completeness unreliable;
- stale features that no longer match the current reviewed subject snapshot;
- partial provenance or malformed lineage fields;
- conflicting authoritative records on lifecycle, scope, or label meaning;
- attempts to widen subject scope from the anchored reviewed record to sibling or nearby records; or
- any situation where a shadow surface would need to guess whether the output still applies.

When those conditions apply:

- the path must fail closed;
- the system must mark the output `unresolved` or `degraded`;
- the system must not silently emit authority-shaped output;
- the system must not infer a label;
- the system must not widen scope; and
- the system must keep the operator-visible guard in place.

`degraded` means the shadow path may still expose bounded diagnostic context about why the output is incomplete, stale, or blocked.

`unresolved` means the system cannot justify a trustworthy shadow output from the currently reviewed lineage and must withhold the candidate result.

## 8. Explicit Authority Prohibitions

The reviewed ML shadow-mode boundary explicitly prohibits using ML scores, classes, or ranking outputs for:

- alert admission;
- alert closure;
- case promotion or case truth promotion;
- approval grant or reject;
- delegation routing authority;
- execution policy;
- reconciliation truth;
- evidence validation truth;
- identity or scope collapse beyond the anchored reviewed record; or
- any operator-facing state mutation that would appear authoritative without separate reviewed confirmation.

Shadow-mode ML may inform reviewer attention. It must not redefine the durable control-plane truth chain.

## 9. Alignment Notes

This boundary stays aligned with `README.md` and `docs/architecture.md` by keeping AegisOps as the authoritative control plane above reviewed detection and automation substrates.

It stays aligned with `docs/control-plane-state-model.md` by treating `Alert`, `Case`, `Evidence`, `Observation`, `Lead`, `Recommendation`, `Approval Decision`, `Action Request`, `AI Trace`, `Action Execution`, and `Reconciliation` as explicit control-plane records with separate lifecycle ownership.

It stays aligned with `docs/phase-15-identity-grounded-analyst-assistant-boundary.md` and `docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md` by keeping ML output advisory-only and by requiring unresolved handling when grounding or citation-quality lineage is incomplete.

It stays aligned with `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md` by requiring one anchored reviewed subject record and by forbidding linkage widening from nearby metadata, sibling lineage, or partial provenance.
