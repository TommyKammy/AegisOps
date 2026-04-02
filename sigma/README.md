# AegisOps Sigma Content Guidance

## Purpose

This document records the approved governance model for Sigma content tracked under `sigma/` and supplements the Sigma baseline in `docs/requirements-baseline.md`.

It explains how AegisOps distinguishes reviewed curated content from documented suppressed content so future contributors preserve the approved onboarding and review model.

## Directory Roles

### `curated/`

`sigma/curated/` is reserved for reviewed Sigma rules that are approved for future AegisOps onboarding.

A rule belongs in `curated/` when it has passed content review and is retained as an approved candidate for future platform onboarding.

Placeholder-only status in this directory must remain explicit until real Sigma content is admitted through review and approval.

### `suppressed/`

`sigma/suppressed/` is reserved for documented suppression decisions for Sigma content that should remain excluded from onboarding.

An entry belongs in `suppressed/` when the decision to exclude or defer Sigma content must be preserved with documented rationale, review, and approval context.

This directory is for governance records about exclusion or deferral, not for quietly disabling detections through undocumented repository changes.

## Review Expectations

Any future addition under either directory must remain reviewable, attributable, and explicitly approved before placeholder-only status is removed.

Changes should preserve clear authorship, decision context, and rationale so reviewers can distinguish approved onboarding candidates from approved exclusion decisions.

If a contribution changes the intended governance model for Sigma content, that change must be reviewed against `docs/requirements-baseline.md` and handled through the normal baseline review path.

## Validation Expectations

Contributors must validate that directory purpose, review state, and supporting documentation remain clear before merging changes.

Validation for Sigma repository content should confirm:

- the directory purpose still matches the approved distinction between curated and suppressed content
- placeholder markers or future entries remain internally consistent with their stated review status
- review and approval language remains explicit enough for future onboarding and audit work

## Scope Boundary

This document defines repository content governance only. It does not activate detections, create suppression behavior, or change runtime execution in OpenSearch, Sigma tooling, or n8n.
