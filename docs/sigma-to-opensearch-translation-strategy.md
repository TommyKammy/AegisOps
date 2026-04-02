# AegisOps Sigma-to-OpenSearch Translation Strategy

## 1. Purpose

This document defines the approved Sigma-to-OpenSearch translation strategy for the AegisOps baseline.

It makes the supported Sigma subset, required metadata, deferred features, and OpenSearch-native fallback path explicit before runtime detector implementation begins.

This strategy defines translation scope and review boundaries only. It does not claim full Sigma parity and does not approve automatic detector generation or production activation.

## 2. Baseline Translation Boundary

AegisOps supports only single-rule, single-event Sigma detections whose logic can be translated into reviewable OpenSearch detector content without changing the rule's meaning.

The translation boundary exists to keep Sigma as the reviewed rule-definition source while OpenSearch remains the runtime system of record for deployed detector materialization.

Straight-through translation is allowed only when all of the following remain true:

- The source telemetry family is at least `schema-reviewed` and the fields used by the rule have documented coverage under `docs/source-onboarding-contract.md`.
- The rule depends on normalized event fields rather than hidden collector behavior, undocumented enrichment, or ad hoc analyst interpretation.
- The translated OpenSearch detector content can preserve the same analytic intent, scope, and operator expectations without adding unstated runtime semantics.

If those conditions are not satisfied, the rule is not eligible for baseline Sigma translation.

## 3. Supported Sigma Subset for the Approved Baseline

AegisOps supports only single-rule, single-event Sigma detections whose logic can be translated into reviewable OpenSearch detector content without changing the rule's meaning.

The approved baseline supports selection-based field matching, boolean condition composition using `and`, `or`, and `not`, and stable comparisons on normalized fields that have documented source coverage.

Supported straight-through translation is intentionally narrow:

| Status | Sigma capability handling |
| ---- | ---- |
| Supported for baseline translation | Simple single-event selections on normalized fields; boolean combinations that preserve straight-through detector meaning |
| Supported with explicit review notes | Equality and membership checks on canonical schema fields when the source-family mapping, value semantics, and false-positive expectations are documented |

For the approved baseline, a supported Sigma rule should generally:

- Describe one event-level detection hypothesis rather than a multi-stage analytic story.
- Use fields that are already mapped into the canonical telemetry schema or are explicitly documented as stable `aegisops.*` extensions.
- Keep condition logic reviewable enough that a human reviewer can compare the Sigma intent to the future OpenSearch detector materialization without inference gaps.

## 4. Required Rule Metadata and Source Prerequisites

Each rule proposed for translation must declare rule identity, owner, severity, purpose, ATT&CK mapping, normalized field dependencies, source-family prerequisites, and known false-positive considerations.

Required metadata and prerequisite mapping for future OpenSearch detector work:

| Sigma-side requirement | Why it is required | Future OpenSearch detector use |
| ---- | ---- | ---- |
| Rule identity (`title`, stable internal identifier, version or review status) | Preserves traceability across review and implementation | Maps to detector title, change tracking, and review evidence |
| Owner | Makes accountability explicit | Maps to detector ownership and future operational review |
| Purpose and analytic intent | States what the rule is trying to detect | Maps to detector description and expected behavior notes |
| Severity | Preserves analyst triage expectations | Maps to alert severity or detector priority metadata |
| ATT&CK mapping | Keeps adversary-technique context reviewable | Maps to detector tags and downstream triage context |
| Normalized field dependencies | Prevents silent field remapping during translation | Maps to detector query fields and validation targets |
| Source-family prerequisites | Confirms which telemetry families may support the rule | Maps to detector index or log source eligibility checks |
| Known false-positive considerations | Makes review tradeoffs explicit before activation | Maps to detector rollout notes and tuning prerequisites |
| Validation evidence reference | Shows that field coverage and rule intent were tested or reviewed | Maps to detector validation artifacts and future staging checks |

Source readiness constraints for translation:

- A Sigma rule must not be treated as translation-ready unless the dependent telemetry family documents the relevant field coverage, timestamp semantics, provenance, and identity or asset linkage limits.
- Rules that depend on fields marked unavailable, intentionally deferred, or unstable in source onboarding evidence must remain untranslated until that gap is resolved through approved work.
- Rule metadata must state whether the Sigma rule is the intended source of truth for future detector materialization or whether the detection remains OpenSearch-native by design.

## 5. Unsupported and Deferred Sigma Feature Matrix

The baseline does not support Sigma correlation, aggregations, temporal counting semantics, cross-index joins, multi-source dependencies, or field logic that depends on unsupported modifiers without a separate approved design.

Unsupported and deferred handling for the approved baseline:

| Status | Sigma capability handling | Baseline handling |
| ---- | ---- | ---- |
| Deferred pending separate design | Correlation blocks; aggregation or threshold semantics; temporal sequences; multi-source joins | Do not translate straight through. Require separate design for detector, alert grouping, and validation semantics before implementation. |
| Deferred pending field-model decision | Rules that rely on unsupported field modifiers, backend-specific pipelines, or schema features that are not yet modeled canonically | Keep out of baseline translation until canonical field semantics and reviewer guidance exist. |
| Forbidden for straight-through translation | Content that requires hidden enrichment assumptions, undocumented field remapping, or runtime behavior outside approved OpenSearch detector responsibilities | Reject as Sigma translation input for the baseline. If needed, redesign as documented OpenSearch-native content or raise an ADR. |
| Forbidden for parity claims | Any wording that implies AegisOps already implements the full Sigma specification or full Sigma correlation behavior | Do not use in documentation, review, or future detector promotion language. |

Interpretation notes:

- Correlation and aggregation features are deferred because they change state, timing, grouping, or counting semantics in ways that cannot be represented safely as baseline single-event translation.
- Multi-source logic is deferred because it depends on source onboarding maturity, event-linkage semantics, and analytic state that are outside the approved baseline scope.
- Unsupported modifiers or backend-specific assumptions must not be smuggled into the translation path as if they were equivalent to canonical normalized-field logic.

## 6. OpenSearch-Native Fallback Path

When a detection requirement cannot be translated safely from the approved Sigma subset, the detection must remain OpenSearch-native and carry explicit documentation that Sigma is not the source of truth for that rule.

OpenSearch-native fallback content must still preserve owner, purpose, source prerequisites, field dependencies, validation evidence, and false-positive notes so review standards remain consistent.

Fallback rules:

- The OpenSearch-native detector must record why Sigma is not used, such as aggregation semantics, multi-source correlation, unsupported modifiers, or OpenSearch-specific analytic features.
- The detector review package must identify the exact telemetry families, normalized fields, and runtime assumptions it depends on.
- OpenSearch-native content must not be described as auto-generated from Sigma or as equivalent to a Sigma rule unless a future approved design makes that relationship explicit.
- Review and validation expectations remain the same as for Sigma-derived content: documented ownership, traceable purpose, staging or test evidence, and explicit false-positive considerations.

This fallback path keeps the baseline honest: Sigma is preferred where the supported subset is sufficient, but OpenSearch-native detections remain the correct path when straight-through translation would overstate portability or hide runtime-specific behavior.

## 7. Baseline Alignment Notes

This strategy remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, and `docs/secops-domain-model.md`.

It also remains aligned with `sigma/README.md` and `opensearch/detectors/README.md` by preserving the distinction between reviewed rule-definition sources, detector metadata scaffolding, and future runtime activation work.

Future implementation may add Sigma translation tooling, detector generation helpers, or richer rule-validation procedures, but those changes must keep Sigma authoring separate from OpenSearch execution responsibilities and must not weaken the supported/deferred/forbidden boundary defined here.
