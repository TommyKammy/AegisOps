# AegisOps ADR Review Path

This document defines the ADR lifecycle for AegisOps design changes.

It applies to proposal, review, approval, and supersession of ADR-governed changes.

This process defines governance only and does not require tool-specific automation.

## 1. Purpose

The purpose of this document is to make the design-change review path explicit before implementation issues introduce architecture drift.

It supplements `docs/requirements-baseline.md` and the ADR template at `docs/adr/0000-template.md` by defining who does what and in which order.

## 2. When an ADR Is Required

An ADR is required before implementation when a change affects architecture, boundaries, naming, security posture, storage layout, or the operating model.

Design-change issues and implementation issues must remain separate.

If implementation work reveals that the approved baseline is incomplete or flawed, that gap must be handled through ADR review rather than being hidden inside an implementation-only change.

## 3. Proposal Path

An ADR proposal must be created as a dedicated issue or document update before implementation begins.

The proposer must:

- open or update the design-change issue that scopes the decision,
- draft the ADR from `docs/adr/0000-template.md`,
- state the context, decision, options, rationale, and validation approach, and
- identify the baseline clauses or accepted ADRs that the proposal depends on or would change.

The proposal should stay focused on one design decision so review can be explicit and testable.

## 4. Review Path

Review must confirm alignment with the current AegisOps requirements baseline and any already accepted ADRs.

Review must also confirm:

- the decision is actually architectural rather than an implementation detail,
- the problem statement and decision language are specific enough to govern later implementation,
- the consequences, rollback path, and validation expectations are documented, and
- the proposal does not silently redefine approval, security, storage, or operating-model constraints without stating that impact.

Review is complete only when another engineer, reviewer, or owning team has examined the ADR content and the ADR records that review in its approval section.

## 5. Approval Path

Approval must be explicit and recorded in the ADR document.

The approver must ensure the ADR status and approval metadata are updated together, including the `Reviewed By`, `Approved By`, and `Approval Date` fields defined by the ADR template.

An ADR may guide implementation only after approval is recorded. Until then, the ADR remains proposed and must not be treated as an accepted baseline change.

If approval is denied, the ADR should be marked rejected rather than left ambiguous.

## 6. Supersession Path

Superseding an accepted ADR requires a new ADR that names the older ADR in the supersedes field.

When a newer ADR replaces an older decision, the new ADR must explain why the prior decision is no longer sufficient, and the older ADR should be updated to reference the replacing ADR in its superseded-by field.

Supersession must preserve traceability:

- the older ADR remains in the repository as historical record,
- the newer ADR becomes the governing decision only after review and approval, and
- implementation work must reference the currently accepted ADR, not an outdated one.

Supersession does not retroactively authorize runtime changes. Any implementation issue still needs its own scoped validation and review before merge.
