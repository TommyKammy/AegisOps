# AegisOps Detection Lifecycle and Rule QA Framework

## 1. Purpose

This document defines the baseline lifecycle states and minimum quality-assurance evidence required before AegisOps detection content can move from proposal to activation, deprecation, and retirement.

It applies to Sigma detection rules, OpenSearch detector artifacts, supporting validation notes, and future detection metadata that govern whether reviewed content is ready for activation decisions.

This framework defines review and readiness expectations only. It does not authorize live detector activation, bypass staging, or approve production rollout without separate implementation work.

## 2. Scope and Non-Goals

The lifecycle must distinguish at least `draft`, `candidate`, `staging`, `active`, `deprecated`, and `retired` detection content states.

This framework is content-focused. It governs reviewed detection logic, detector metadata, activation evidence, and follow-up obligations rather than runtime automation, action execution, or case-management behavior.

This framework does not replace the source onboarding contract, Sigma translation strategy, or future operator procedures. Those artifacts remain authoritative for telemetry admission, translation boundaries, and implementation-specific handling.

## 3. Lifecycle States

| State | Expectation |
| ---- | ---- |
| `draft` | Initial proposal or substantial rewrite that is not yet eligible for activation review. |
| `candidate` | Reviewable detection content with assigned ownership and documented intent, but not yet approved for staging activation. |
| `staging` | Content approved for controlled validation in a staging environment or test index only. |
| `active` | Content approved for production activation with documented evidence and follow-up obligations. |
| `deprecated` | Content that remains deployed or historically referenced temporarily while replacement or removal is coordinated. |
| `retired` | Content removed from active use and preserved only for audit, history, or reference. |

`draft` content may capture emerging ideas, analytic hypotheses, or major rewrites, but it must not be treated as reviewed content ready for staging or production consideration.

`candidate` content is the first state where reviewers should expect stable rule intent, ownership, metadata completeness, and a scoped validation plan.

`staging` remains a controlled readiness state only. It exists to prove evidence, not to silently approximate production rollout.

`active` is the only state that permits approved production activation, and it still carries explicit follow-up, expiry, and rollback expectations.

`deprecated` and `retired` ensure that removal work is governed as deliberately as activation work so historical rationale and rollback context remain reviewable.

## 4. State Transition Expectations

Detection content must not move to `staging` until source prerequisites, field coverage expectations, replay data, and review ownership are explicitly documented.

Detection content must not move to `active` until replay or staged validation evidence, expected-volume review, and false-positive review are recorded and reviewable.

Staging readiness is sufficient for controlled translation and validation only when source prerequisites and activation-gating field dependencies are explicit and reviewable.

Production activation requires detection-ready source evidence for activation-gating dependencies and must not rely on schema-reviewed coverage alone.

Expected transitions are:

| From | To | Minimum expectation |
| ---- | ---- | ---- |
| `draft` | `candidate` | Rule purpose, ownership, source prerequisites, and intended detection behavior are stable enough for review. |
| `candidate` | `staging` | QA evidence package is complete enough to justify controlled validation only. |
| `staging` | `active` | Activation evidence, reviewer sign-off, expiry, and rollback notes are complete. |
| `active` | `deprecated` | Replacement, unacceptable behavior, source drift, or strategic retirement need is documented. |
| `deprecated` | `retired` | Runtime use is removed and historical references are preserved for audit and future review. |

Content may move backward when validation fails, source readiness regresses, or post-deploy review identifies unacceptable behavior. Re-entry into a later state requires refreshed evidence rather than implicit carry-forward.

No transition may be used to bypass staging, replay validation, or ownership review simply because similar logic was previously approved elsewhere.

## 5. Minimum QA Evidence Before Activation

Activation readiness requires evidence for source prerequisite checks, canonical field coverage checks, replay or staged tests, expected alert volume review, and false-positive review.

Source prerequisite checks must confirm that the required source family is admitted under the source onboarding contract, that required indices or datasets exist, and that the rule does not depend on undeclared telemetry.

Field coverage checks must identify the match-required fields, triage-required fields, activation-gating fields, confidence-degrading gaps, and whether each missing field blocks staging or active use.

Replay or staged test evidence must show that the detection logic was exercised against representative data before activation decisions are made.

Expected-volume review must document whether the projected finding or alert volume is acceptable for the initial operating model and what assumptions were used.

False-positive review must record known benign triggers, planned tuning or suppression constraints, and whether analyst review load is acceptable.

The minimum QA evidence package for a proposed activation decision is:

| Evidence area | Required baseline content |
| ---- | ---- |
| Source prerequisite check | Source family status, index or dataset dependency, provenance boundary, and any blocked dependencies. |
| Field coverage check | Match-required fields, triage-required fields, activation-gating fields, confidence-degrading gaps, and impact of each gap on staging or production readiness. |
| Replay or staged test | Test corpus or staged dataset reference, success and failure examples, expected matches, and reviewer-visible results. |
| Expected-volume review | Estimated finding or alert rate, assumptions behind the estimate, and whether the projected analyst load is acceptable in the current operating model. |
| False-positive review | Known benign scenarios, tuning plan, suppression boundaries, and residual analyst burden. |

If any required evidence area is missing or ambiguous, the detection content must remain in `candidate` or return to `draft` until the gap is resolved.

## 6. Ownership, Review, and Expiry Expectations

Each detection change must declare an owner, a required reviewer, an expiry or next-review date, and the rollback expectation for disabling or reverting the change if post-deploy behavior is unacceptable.

At minimum, reviewed detection content should record:

| Metadata field | Expectation |
| ---- | ---- |
| Owner | Team or maintainer accountable for lifecycle decisions, tuning follow-up, and retirement planning. |
| Required reviewer | Named review authority for the activation decision, distinct from anonymous approval by convention alone. |
| Expiry or next-review date | Date that forces reassessment of continued usefulness, source validity, or tuning assumptions. |
| Validation evidence reference | Stable pointer to replay notes, staged test results, or review package used for activation consideration. |
| Rollback expectation | How the change will be disabled, reverted, or replaced if post-deploy review shows unacceptable behavior. |

Ownership must remain explicit through deprecation and retirement. A detection item without an accountable owner may be preserved for history, but it must not progress toward activation.

Expiry is a control against stale detections. If the next-review date passes without reassessment, the content should be considered for deprecation or temporary rollback until review is refreshed.

## 7. Post-Deploy Review and Rollback Expectations

Post-deploy review must verify observed behavior after activation, compare actual volume against the staged expectation, and confirm whether tuning, suppression, deprecation, or retirement is required.

Rollback expectations must preserve the ability to disable or revert a detection change without implying autonomous response or staging bypass.

The first post-deploy review should confirm:

| Review question | Expectation |
| ---- | ---- |
| Did actual finding or alert volume match the staged estimate? | Differences are explained and either accepted or treated as a tuning concern. |
| Did the rule trigger on expected scenarios only? | Unexpected triggers are documented as false-positive or scope-drift findings. |
| Are source fields and telemetry assumptions still valid? | Source drift or schema loss is treated as a readiness regression. |
| Is suppression or refinement required? | Any new tuning work is explicitly tracked rather than silently applied. |
| Should the rule remain `active`, move to `deprecated`, or be rolled back? | Lifecycle status remains an explicit decision. |

Rollback may mean disabling the activation, reverting the translated detector artifact, restoring a previous approved version, or moving the content back to `staging` or `candidate` for further validation. It must not imply live destructive response, autonomous rollback actions, or undocumented production hotfixes.

## 8. Baseline Alignment Notes

This framework remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, `docs/sigma-to-opensearch-translation-strategy.md`, and `docs/secops-domain-model.md`.

It preserves the baseline requirement that source readiness and staging or test evidence exist before production activation decisions are made.

It also preserves the separation between detection content lifecycle, finding generation, alert routing, approval decisions, and action execution defined elsewhere in the baseline.
