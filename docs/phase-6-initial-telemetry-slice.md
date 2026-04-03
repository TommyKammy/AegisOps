# AegisOps Phase 6 Initial Telemetry Slice

## 1. Purpose

This document selects the single initial telemetry family and first detection use cases for the Phase 6 validated slice.

It supplements `docs/canonical-telemetry-schema-baseline.md`, `docs/source-onboarding-contract.md`, `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/secops-business-hours-operating-model.md`, `docs/retention-evidence-and-replay-readiness-baseline.md`, and `docs/sigma-to-opensearch-translation-strategy.md` by narrowing the first end-to-end validation target to one family and a small set of reviewable detections.

This document selects scope only. It does not approve live onboarding, production detector activation, new response automation, or a broader Phase 6 implementation plan.

## 2. Selected Initial Telemetry Family

The selected initial telemetry family for the Phase 6 slice is Windows security and endpoint telemetry.

Phase 6 starts with one telemetry family only.

This family is the best initial fit for the first validated slice because the existing baseline already expects Windows telemetry to preserve event classification, timestamp semantics, source provenance, host identity, and actor or target identity when present.

Those semantics are sufficient to validate the first end-to-end path from normalized event review, through single-event detection expression, into finding or alert handling without adding cross-family normalization ambiguity.

## 3. Selected Initial Detection Use Cases

The initial use cases below are intentionally limited to single-event detections that can be reviewed during business hours and exercised through replay.

The Phase 6 slice is limited to these three initial detection use cases:

1. Privileged group membership change
   Detect a Windows event that records a user being added to a privileged local or domain group.
   This is a high-signal administrative change with clear actor, target, and host context and does not require thresholding or multi-event correlation to be meaningful.
2. Audit log cleared
   Detect a Windows event that records clearing of the Windows audit log.
   This is a direct single-event security signal that exercises provenance and timestamp handling while remaining reviewable as a standalone analyst work item.
3. New local user created
   Detect a Windows event that records creation of a new local account on a managed endpoint or server.
   This is narrow enough for replay validation, often preserves actor and target identity, and fits business-hours triage as a review-first use case rather than an automatic action trigger.

Each selected use case can be exercised with replayable Windows event samples and handled through read-only analyst workflow steps before any approval-bound response exists.

The initial slice deliberately avoids detections that depend on threshold accumulation, sequence logic, cross-host correlation, or unresolved enrichment dependencies.

## 4. Selection Rationale

Windows telemetry is the best first proof of the Phase 5 contracts because it exercises actor identity, host identity, provenance, timestamp semantics, and Sigma-compatible single-event detection patterns in one family.

The selected use cases are also small enough to validate the current contracts end to end:

- They fit the source onboarding contract because representative Windows event samples can document raw payload shape, mapping assumptions, replay corpus needs, and parser provenance without having to solve multiple source families at once.
- They fit the Sigma translation strategy because each use case can be expressed as a reviewable, single-rule, single-event hypothesis rather than a correlation story or a threshold rule.
- They fit the detection lifecycle and rule QA framework because replay evidence, field coverage review, and expected-volume review can be evaluated for a narrow set of discrete administrative-security events.
- They fit the business-hours operating model because they are plausible queue-driven review items that can be investigated through read-oriented evidence collection before any approval-bound response exists.
- They fit the retention and replay baseline because normalized Windows event samples are a credible replay substrate for repeated detector validation and analyst workflow review.

Windows is preferred over the other approved telemetry families for the first slice because the alternatives would broaden scope too early:

Network telemetry is deferred because volume, directionality, and product variance would broaden parser and tuning scope too early.

Linux telemetry is deferred because initial source heterogeneity would widen normalization and replay coverage before the first vertical slice is proven.

SaaS audit telemetry is deferred because provider-specific action semantics would force early cross-provider narrowing inside a family that is still too broad for the first validated slice.

## 5. Scope Guardrails

No additional telemetry families, correlation logic, threshold-based analytics, response automation, or after-hours operating promises are included in this slice.

The first Phase 6 validation target is limited to proving that one reviewed family can support:

- replayable sample selection;
- schema and provenance review for the required fields the chosen detections rely on;
- up to three single-event detection definitions;
- finding or alert handling that remains compatible with the current business-hours operating model; and
- read-only investigation steps that do not assume write-capable response execution.

If a proposed addition requires a second telemetry family, sequence or threshold analytics, cross-provider SaaS normalization, after-hours workflow guarantees, or automatic response behavior, it is outside this initial Phase 6 slice and should be handled by a later scoped issue.
