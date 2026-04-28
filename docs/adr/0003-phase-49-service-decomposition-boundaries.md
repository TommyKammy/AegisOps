# ADR-0003: Phase 49 Service Decomposition Boundaries and Migration Order

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #918, #919, #920, #921, #922, #923, #924, #925
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 49.0 is a behavior-preserving maintainability refactor backlog for the remaining `AegisOpsControlPlaneService` responsibility concentration.

The repository already records the governing hotspot contract in `docs/maintainability-decomposition-thresholds.md`, and that contract keeps `docs/maintainability-hotspot-baseline.txt` as the reviewed hotspot baseline until extraction work proves the baseline can be safely refreshed.

AegisOpsControlPlaneService remains the public facade for Phase 49.0 behavior-preserving decomposition work.

The ambiguity before this ADR is not whether the service should be decomposed. The ambiguity is which internal ownership boundaries are fixed, which child issue may move first, and which behaviors must remain unchanged while the extraction proceeds.

The first implementation issue must not start before this ADR is merged.

This decision cannot be deferred because implementation issues #920 through #925 need a stable repo-owned ordering and boundary contract before they touch production code.

## 2. Decision

We will preserve the existing public facade while extracting internal collaborators.

The target service boundaries are:

- Intake and triage boundary
- Case mutation and evidence linkage boundary
- Advisory and AI trace lifecycle boundary
- Action and reconciliation orchestration boundary
- Runtime, restore, and readiness diagnostics boundary

The migration order is:

1. #919 ADR and verification gate
2. #920 intake and triage extraction
3. #921 case mutation and evidence linkage extraction
4. #922 advisory and AI trace lifecycle extraction
5. #923 action and reconciliation orchestration extraction
6. #924 runtime, restore, and readiness diagnostics extraction
7. #925 hotspot baseline refresh and validation closeout

The child issues are not parallelizable unless a later accepted ADR or issue update explicitly changes the dependency order. Each extraction may depend on the facade and the collaborators extracted before it, but it must not depend on behavior planned for a later child issue.

The hotspot baseline remains governed by `docs/maintainability-decomposition-thresholds.md` until #925 verifies that the extracted modules and focused tests make a baseline refresh accurate.

## 3. Decision Drivers

- maintainability
- auditability
- behavior preservation
- authority-boundary preservation
- focused regression scope
- rollback safety
- reviewable child-issue sequencing

## 4. Options Considered

### Option A: Ordered behavior-preserving decomposition behind the existing facade

#### Description
Extract one internal boundary at a time while `AegisOpsControlPlaneService` remains the public facade for existing callers and tests.

#### Pros
- Keeps runtime behavior stable while implementation ownership becomes easier to review.
- Lets each child issue add focused regression coverage at the boundary it extracts.
- Preserves the current authority posture because external callers still cross the same facade.
- Gives #925 a concrete basis for refreshing the hotspot baseline only after extraction evidence exists.

#### Cons
- Requires strict sequencing across child issues.
- Leaves the hotspot baseline unchanged until the end of the extraction sequence.

### Option B: Rewrite the service boundary in one issue

#### Description
Replace the facade and all internal collaborators in one broad refactor.

#### Pros
- Completes the visible decomposition faster on paper.
- Avoids temporary adapter code between the facade and newly extracted collaborators.

#### Cons
- Broadens regression risk across intake, mutation, advisory, action, reconciliation, runtime, restore, and readiness behavior at once.
- Makes it harder to prove that the public behavior and authority posture remained unchanged.
- Undercuts the focused child-issue structure already materialized for Phase 49.0.

### Option C: Continue extending the hotspot in place

#### Description
Leave the service concentration untouched and continue adding behavior to the existing facade class.

#### Pros
- Avoids immediate extraction work.
- Preserves the current implementation layout.

#### Cons
- Ignores the governing hotspot contract.
- Keeps unrelated review surfaces coupled together.
- Makes later Phase 49 work more likely to mix authority-bearing paths by convenience.

## 5. Rationale

Option A is selected because it follows `docs/maintainability-decomposition-thresholds.md` while preserving runtime behavior.

The current service concentration is already a known hotspot, but Phase 49.0 is explicitly refactor work, not a product expansion. A facade-preserving extraction sequence is the narrowest path that reduces the hotspot without reopening approval, execution, reconciliation, assistant, ticket, evidence, or readiness semantics.

Option B was rejected because broad replacement would make regression failures harder to localize and could hide authority-boundary changes inside structural churn.

Option C was rejected because the repository has already crossed the decomposition threshold and the Phase 49.0 backlog exists to stop further responsibility growth in the hotspot.

The accepted trade-off is that short-lived internal adapter code may remain during the sequence. That is preferable to changing public service behavior or refreshing the hotspot baseline before the extraction evidence exists.

## 6. Consequences

### Positive Consequences

- Child issues have fixed ownership boundaries.
- Reviewers can reject production extraction work that skips the ADR gate or changes the migration order without an explicit update.
- Focused tests can be attached to the specific boundary under extraction.
- The facade-preservation contract keeps runtime callers isolated from internal file movement.

### Negative Consequences

- The sequence cannot be parallelized safely.
- The hotspot baseline intentionally remains stale-looking until #925 confirms the extraction closeout.
- Some temporary delegation paths may exist while the facade remains stable.

### Neutral / Follow-up Consequences

- `docs/maintainability-hotspot-baseline.txt` is refreshed only after extraction lands.
- Later ADRs may redefine service boundaries only if they preserve AegisOps control-plane authority or explicitly supersede this ADR.
- #925 owns the final validation closeout and maintainability-baseline update rather than #919.

## 7. Implementation Impact

Every extraction slice must keep the facade behavior-preserving and add focused regression coverage for its boundary.

\#920 owns intake and triage extraction. Its tests must prove that source admission, triage classification, and queue-facing state preserve existing authoritative record behavior.

\#921 owns case mutation and evidence linkage extraction. Its tests must prove that case lifecycle mutation, evidence attachment, and linkage rules still bind to explicit authoritative records rather than inferred names, paths, comments, or neighboring metadata.

\#922 owns advisory and AI trace lifecycle extraction. Its tests must prove that advisory output, AI traces, recommendations, and cited context stay subordinate to reviewed control-plane records and fail closed when citations, identity, scope, or authority signals are missing.

\#923 owns action and reconciliation orchestration extraction. Its tests must prove that action intent, approval state, execution delegation, receipts, and reconciliation remain explicitly bound and do not trust placeholder credentials, forwarded headers, ticket hints, assistant text, or substrate-local summaries as authority.

\#924 owns runtime, restore, and readiness diagnostics extraction. Its tests must prove that readiness, backup, restore, export, and diagnostic surfaces use snapshot-consistent reads or explicit rejection when mixed state is detected, and that failed paths leave no orphan or partial durable state behind.

\#925 owns hotspot baseline refresh and validation closeout. It must run the maintainability hotspot verifier, refresh the baseline only after extraction is real, and preserve the public facade contract unless a later accepted decision changes it.

The #925 closeout keeps one ADR-approved exception because the accepted child issues decomposed internal ownership while preserving the public facade. At closeout, `control-plane/aegisops_control_plane/service.py` remains above the long-term 1,500-line target and `AegisOpsControlPlaneService` remains above the long-term 50-method target. The refreshed baseline must therefore record the current closeout ceilings and fail on any silent facade re-growth rather than claiming the hotspot has been eliminated.

No deployment manifest, runtime configuration, database migration, credential source, endpoint exposure, browser behavior, operator UI capability, or commercial readiness workflow changes through this ADR.

## 8. Security Impact

This ADR does not change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, secrets, or write-capable authority.

Privileges do not expand. Secrets handling does not change. Network exposure does not change. Approval requirements do not change. No production write-action is introduced.

The security benefit is reviewability: each extraction boundary has to preserve the existing AegisOps authority model instead of using refactor mechanics to widen trust in tickets, assistant output, ML results, endpoint evidence, network evidence, browser state, receipts, optional extension health, names, paths, comments, forwarded headers, placeholder credentials, or other subordinate context.

## 9. Rollback / Exit Strategy

Rollback removes this ADR and its verifier wiring before implementation extraction starts.

If extraction has already started, rollback must happen through the child issue that introduced the implementation change. The facade-preservation contract means a child issue rollback should remove the extracted collaborator and route calls back through the previous in-facade implementation without changing externally visible behavior.

If #925 finds that the hotspot baseline cannot be refreshed honestly, the rollback path is to keep the old baseline and open a follow-up maintainability issue rather than redefining the threshold around the desired result.

No data migration rollback is involved because this ADR does not approve schema or runtime data changes.

## 10. Validation

Run `bash scripts/verify-phase-49-service-decomposition-adr.sh`.

Run `bash scripts/test-verify-phase-49-service-decomposition-adr.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 919 --config <supervisor-config-path>`.

Before #920 starts, repository review must confirm that this ADR is merged and that the child issue still preserves the facade and authority-boundary constraints.

## 11. Non-Goals

- No production code extraction is approved by this ADR.
- No commercial readiness capability is added.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, or operator UI behavior is expanded.
- No deployment, database, migration, credential, or external substrate behavior is changed.
- No hotspot baseline refresh is approved before #925 validates the extraction closeout.
- Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context and do not become workflow truth.

## 12. Approval

- **Proposed By**: Codex for Issue #919
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-29
