# ADR-0005: Phase 50.8 Residual Service Hotspot Migration Contract

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #961, #962
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 50.7 closed the first Phase 50 maintainability sequence, but it intentionally left `control-plane/aegisops_control_plane/service.py` as the one accepted residual hotspot.

ADR-0004 remains authoritative for the Phase 50 hotspot ordering decision.

ADR-0003 remains authoritative for the public facade-preservation exception.

Phase 50.7 recorded the current residual service ceiling in `docs/maintainability-hotspot-baseline.txt`.

This ADR does not refresh the baseline because implementation evidence does not exist yet.

The next Phase 50.8 implementation slices need a repo-owned residual map before production code extraction starts. Without this contract, later child issues could choose local helper order, refresh the baseline from a desired projection, or treat the Phase 50.7 ceiling as approval for further growth.

## 2. Decision

Phase 50.8 will migrate the remaining `service.py` helper pressure in a fixed, behavior-preserving order.

The residual Phase 50.8 `service.py` helper clusters are:

- readiness helper cluster
- action-review helper cluster
- intake/lifecycle helper cluster
- action-policy helper cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context.

## 3. Residual Hotspot Map

The residual hotspot map is limited to helper migration inside `AegisOpsControlPlaneService`.

The readiness helper cluster covers readiness review health, readiness source health, automation-substrate health, optional extension operability, assistant provider operability, endpoint evidence operability, dominant-reason selection, affected-review counts, and readiness aggregate shaping.

The action-review helper cluster covers action-review record indexing, review-chain snapshots, path health, runtime visibility, after-hours handoff visibility, manual fallback visibility, escalation visibility, timeline shaping, mismatch inspection, coordination-ticket outcomes, downstream binding, and terminal issue detection.

The intake/lifecycle helper cluster covers lifecycle transition creation, lifecycle transition identifiers, latest lifecycle selection, transition attribution, alert/case lifecycle linkage, analytic-signal linkage, alert evidence listing, detection reconciliation linkage, and reviewed intake admission helpers that bind alerts, cases, evidence, and lifecycle records.

The action-policy helper cluster covers action-policy basis normalization, policy determination, policy evaluation overrides, review-bound action-request checks, approved payload binding, approver policy checks, and action request state decisions.

These clusters describe extraction ownership only. They do not create a new runtime service, new endpoint, new approval path, new action catalog, new evidence source, new ticket authority, or new operator workflow.

## 4. Migration Order

The Phase 50.8 migration order is:

1. readiness helper cluster
2. action-review helper cluster
3. intake/lifecycle helper cluster
4. action-policy helper cluster

Readiness helpers must move before action-review helpers that consume readiness projections.

Action-review helpers must move before action-policy helpers so review-state projections stay anchored to authoritative action records.

Intake/lifecycle helpers must move before action-policy helpers so action policy does not infer case, alert, lifecycle, or evidence linkage from names, paths, comments, or neighboring records.

The child issues are not parallelizable by default. A later issue may change the order only through another repo-owned decision that explicitly preserves the authority-boundary and measurement rules in this ADR.

## 5. Measurement Guard

The current Phase 50.7 ceiling remains:

- `max_lines=5660`
- `max_effective_lines=5250`
- `max_facade_methods=203`

The Phase 50.8 implementation target is:

- `max_lines <= 5200`
- `max_effective_lines <= 4850`
- `max_facade_methods <= 175`

A Phase 50.8 closeout may record an exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.7 ceiling.

Any baseline refresh before implementation evidence exists is forbidden.

If a child issue cannot meet the target, the correct closeout is a documented lower exception plus a follow-up backlog, not a silent threshold redefinition. The exception must still prove that the facade did not grow beyond the accepted Phase 50.7 ceiling.

## 6. Validation

Run `bash scripts/verify-phase-50-8-residual-service-hotspot-contract.sh`.

Run `bash scripts/test-verify-phase-50-8-residual-service-hotspot-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 962 --config <supervisor-config-path>`.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, or operator authority behavior is changed.
- No deployment, database, migration, credential source, external substrate, HTTP surface, CLI surface, or operator UI behavior is changed.
- No baseline refresh is approved before Phase 50.8 implementation evidence exists.
- No subordinate source becomes authoritative workflow truth.
- No exception may raise the Phase 50.7 ceiling.

## 8. Approval

- **Proposed By**: Codex for Issue #962
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-29
