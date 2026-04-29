# ADR-0004: Phase 50 Maintainability Hotspot Map and Migration Order

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #946, #947
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 49.0 completed the behavior-preserving `AegisOpsControlPlaneService` decomposition sequence governed by ADR-0003.

ADR-0003 remains authoritative for the Phase 49.0 facade-preservation contract and for the closeout ceiling recorded in `docs/maintainability-hotspot-baseline.txt`.

Phase 50 is a follow-on maintainability backlog. It must lower or fence the remaining hotspots after the ADR-0003 closeout ceiling instead of treating the ceiling as permission for new responsibility growth.

The current ambiguity is not whether Phase 50 should preserve behavior. That constraint is already fixed by AegisOps control-plane authority rules. The ambiguity is which hotspots come first, which dependencies block later slices, and which validation commands must remain attached before implementation work starts.

The first Phase 50 implementation issue must not start before this ADR is merged.

This decision cannot be deferred because Phase 50 implementation issues need a repo-owned hotspot map, dependency order, and validation contract before they touch production code.

## 2. Decision

We will run Phase 50 as ordered, behavior-preserving hotspot reduction after the ADR-0003 closeout.

The Phase 50 target hotspots are:

- `control-plane/aegisops_control_plane/service.py`
- restore validation
- HTTP surface
- assistant, detection, and operator inspection second-hotspot risk
- operator-ui route tests

The migration order is:

1. #947 Phase 50 maintainability ADR and verifier gate
2. `service.py` facade ceiling reduction or fencing
3. restore validation boundary extraction and snapshot-consistency proof
4. HTTP surface routing and auth-boundary review split
5. assistant, detection, and operator inspection second-hotspot risk reduction
6. operator-ui route test decomposition
7. hotspot baseline refresh and Phase 50 validation closeout

The child issues are not parallelizable unless a later accepted ADR or issue update explicitly changes the dependency order. Each implementation slice may depend on this ADR and earlier completed Phase 50 slices, but it must not depend on behavior planned for a later slice.

The Phase 50 baseline refresh may only happen after the implementation slices prove the hotspots have actually been lowered or fenced. Until then, `docs/maintainability-hotspot-baseline.txt` and `docs/maintainability-decomposition-thresholds.md` remain governing checks.

## 3. Decision Drivers

- maintainability
- behavior preservation
- authority-boundary preservation
- snapshot consistency
- reviewable sequencing
- focused regression scope
- rollback safety

## 4. Options Considered

### Option A: Ordered post-Phase 49 hotspot reduction

#### Description
Reduce or fence the remaining hotspots in a fixed order while preserving public behavior and AegisOps authority boundaries.

#### Pros
- Keeps Phase 50 implementation work tied to a reviewed hotspot map.
- Lets each child issue prove one boundary before the next slice depends on it.
- Preserves the ADR-0003 closeout contract until concrete lower ceilings can be verified.
- Prevents UI route-test decomposition from masking backend authority or restore-validation changes.

#### Cons
- Requires strict sequencing.
- Keeps some known hotspots visible until their ordered slice lands.

### Option B: Refresh the hotspot baseline before extraction

#### Description
Update `docs/maintainability-hotspot-baseline.txt` up front to describe the intended Phase 50 end state.

#### Pros
- Makes the target state visible early.
- Reduces immediate verifier pressure on paper.

#### Cons
- Redefines truth around a desired projection instead of verified repository state.
- Could hide facade re-growth or second-hotspot drift behind a premature baseline update.
- Undercuts ADR-0003 by treating its closeout ceiling as a normal operating limit.

### Option C: Let each child issue choose its own hotspot order

#### Description
Allow implementation issues to pick local extraction order without a shared Phase 50 decision contract.

#### Pros
- Maximizes short-term scheduling flexibility.
- Avoids maintaining a separate decision document.

#### Cons
- Recreates the ambiguity this ADR is meant to remove.
- Makes it harder to reject production code changes that skip prerequisite boundaries.
- Increases the chance that assistant, detection, restore, HTTP, or operator UI work broadens authority semantics by convenience.

## 5. Rationale

Option A is selected because it follows `docs/maintainability-decomposition-thresholds.md` while respecting the ADR-0003 closeout state.

Phase 50 should lower or fence hotspots after Phase 49.0, not silently supersede the accepted Phase 49.0 facade-preservation contract. The ordered sequence keeps the remaining `service.py` ceiling, restore validation, HTTP surface, second-hotspot risks, and operator-ui route tests reviewable as separate responsibilities.

Option B was rejected because AegisOps authoritative state rules require the repository to repair projections from real lifecycle facts. A desired future hotspot map is not a verified baseline.

Option C was rejected because unordered implementation would let dependency and authority assumptions move into PR text, comments, or issue-local judgment instead of a durable repo-owned decision.

The accepted trade-off is that Phase 50 may expose uncomfortable known hotspots for longer. That is preferable to refreshing the baseline before the repository proves the lower or fenced state.

## 6. Consequences

### Positive Consequences

- Phase 50 has a fixed hotspot map before production code changes land.
- Reviewers can reject implementation work that skips the ADR gate, changes migration order, or refreshes the baseline prematurely.
- Each child issue can attach focused tests to the boundary it lowers or fences.
- Authority-boundary and behavior-preservation non-goals stay visible during maintainability work.

### Negative Consequences

- Phase 50 cannot safely parallelize its implementation slices by default.
- The hotspot baseline may continue to report known pressure until closeout.
- Some intermediate fences may be temporary until later slices lower the underlying hotspot.

### Neutral / Follow-up Consequences

- Later ADRs may change this order only if they explicitly supersede this ADR or record the changed dependency contract.
- Phase 50 closeout owns the final hotspot baseline refresh.
- Operator UI route-test decomposition remains validation-surface work, not approval or execution behavior expansion.

## 7. Implementation Impact

Issue #947 owns this ADR and its focused verifier only.

Later Phase 50 implementation slices must preserve production behavior, public service entrypoints, runtime configuration, and authority semantics unless a separate accepted ADR and scoped issue explicitly allow a change.

The `service.py` slice must reduce or fence the post-ADR-0003 facade ceiling without treating the closeout ceiling as approval for new responsibility growth.

The restore validation slice must prove snapshot-consistent reads or explicit rejection of mixed-snapshot results, and failed paths must leave no orphan record, partial durable write, or half-restored state.

The HTTP surface slice must preserve trusted-boundary behavior and must not trust raw forwarded headers, host, proto, tenant, user-id, or client-supplied identity hints unless a trusted proxy or boundary has authenticated and normalized them.

The assistant, detection, and operator inspection slice must keep advisory output, detection evidence, and inspection projections subordinate to directly linked authoritative control-plane records.

The operator-ui route test slice must reduce test hotspot pressure without introducing new operator capability, approval behavior, execution behavior, or routing authority.

No deployment manifest, runtime configuration, database migration, credential source, endpoint exposure, network behavior, browser behavior, optional-evidence source, or commercial readiness workflow changes through this ADR.

## 8. Security Impact

This ADR does not change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, secrets, restore, readiness, or write-capable authority.

Privileges do not expand. Secrets handling does not change. Network exposure does not change. Approval requirements do not change. No production write-action is introduced.

The security benefit is fail-closed reviewability: Phase 50 implementation must prove authority, provenance, snapshot, and scope boundaries at the real enforcement boundary instead of relying on issue text, comments, placeholder credentials, forwarded headers, inferred names, or neighboring metadata.

## 9. Rollback / Exit Strategy

Rollback removes this ADR and its verifier wiring before Phase 50 implementation starts.

If implementation has already started, rollback must happen through the child issue that introduced the production change. The child issue must preserve the existing public behavior or explicitly restore the previous implementation path.

If Phase 50 closeout cannot honestly refresh the hotspot baseline, the rollback path is to keep the existing baseline and open a follow-up maintainability issue rather than redefining the threshold around the desired result.

No data migration rollback is involved because this ADR does not approve schema or runtime data changes.

## 10. Validation

Run `bash scripts/verify-phase-50-maintainability-adr.sh`.

Run `bash scripts/test-verify-phase-50-maintainability-adr.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 947 --config <supervisor-config-path>`.

Before later Phase 50 implementation starts, repository review must confirm that this ADR is merged and that the child issue preserves the fixed migration order, behavior-preservation constraints, and authority-boundary non-goals.

## 11. Non-Goals

- No production code extraction is approved by this ADR.
- No commercial readiness capability is added.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, or operator UI behavior is expanded.
- No deployment, database, migration, credential, or external substrate behavior is changed.
- No hotspot baseline refresh is approved before Phase 50 validates the lower or fenced hotspot state.
- Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context and do not become workflow truth.

## 12. Approval

- **Proposed By**: Codex for Issue #947
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-29
