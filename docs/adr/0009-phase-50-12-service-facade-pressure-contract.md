# ADR-0009: Phase 50.12 Service Facade Pressure Contract

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #1015, #1016
- **Depends On**: #1007
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 50.11.7 closed #1007 and recorded the accepted residual `service.py` ceiling in `docs/maintainability-hotspot-baseline.txt`.

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule.

ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence.

ADR-0006 remains authoritative for the Phase 50.9 residual facade convergence and projection hotspot guard.

ADR-0007 remains authoritative for the Phase 50.10 facade floor and external-evidence guard.

ADR-0008 remains authoritative for the Phase 50.11 residual DTO/helper extraction order and closeout validation.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

Phase 50.12 needs a repo-owned contract before final facade-pressure implementation slices start so the sub-1500 target, unchanged behavior boundaries, and verification commands are fixed before code moves.

This ADR does not refresh the baseline because Phase 50.12 implementation evidence does not exist yet and follow-on implementation slices remain.

## 2. Decision

Phase 50.12 will reduce the residual `service.py` facade pressure by extracting or fencing directly linked service facade helper clusters in a fixed, behavior-preserving order.

The Phase 50.12 residual extraction clusters are:

- constructor/composition wiring cluster
- action request/approval cluster
- casework write delegate cluster
- assistant residual helper cluster
- detection/action residual helper cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, response semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context.

## 3. Starting Measurements

The Phase 50.11.7 starting ceiling for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines=1812`
- `max_effective_lines=1632`
- `max_facade_methods=125`
- `facade_class=AegisOpsControlPlaneService`
- `phase=50.11.7`
- `issue=#1007`

The same values are the Phase 50.12 starting measurements before implementation slices begin:

- `physical_lines=1812`
- `effective_lines=1632`
- `AegisOpsControlPlaneService methods=125`

The Phase 50.12 implementation target for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines <= 1500`
- `max_effective_lines <= 1350`
- `max_facade_methods <= 95`

The sub-1500 target is a pressure-reduction target, not permission to change behavior.

A Phase 50.12 closeout may record a lower exception only if it names the unresolved residual cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.11.7 ceiling.

If the sub-1500 target cannot be reached safely, the fallback is to preserve behavior, keep the public `AegisOpsControlPlaneService` facade, record the blocker cluster explicitly, and require the next contract to lower or fence that exact residual cluster instead of claiming long-term completion.

Any `service.py` baseline refresh before Phase 50.12 implementation evidence exists is forbidden.

## 4. Extraction Scope

The constructor/composition wiring cluster owns internal collaborator construction, dependency binding, and facade composition routing that can move behind explicit internal builders without changing public initialization semantics.

The action request/approval cluster owns internal helper code for action request creation, approval decisions, delegation binding, reconciliation routing, mismatch handling, and receipt linkage while preserving authoritative action-review records as the source of truth.

The casework write delegate cluster owns bounded case mutation delegates for observations, leads, recommendations, handoff, disposition, and linked case lifecycle writes while preserving authoritative case records as workflow truth.

The assistant residual helper cluster owns remaining assistant context, advisory, recommendation, citation, draft, and live-assistant helper code that is directly linked to the anchored service request.

The detection/action residual helper cluster owns remaining detection intake, case linkage, external-evidence admission, action-review inspection, and action lifecycle helper code that still sits in the service facade.

No extracted helper may infer tenant, repository, account, issue, case, alert, host, environment, approval, execution, reconciliation, assistant, detection, action, or evidence linkage from naming conventions, path shape, comments, nearby metadata, sibling records, or operator-facing summaries alone.

## 5. Migration Order

The Phase 50.12 migration order is:

1. constructor/composition wiring cluster
2. action request/approval cluster
3. casework write delegate cluster
4. assistant residual helper cluster
5. detection/action residual helper cluster
6. closeout and hotspot-baseline guard cluster

Constructor/composition wiring must move first so later slices depend on explicit collaborator ownership instead of adding more facade-local construction pressure.

Action request/approval helpers must move before casework write delegates so write-path mutations keep using authoritative approval, delegation, reconciliation, and receipt records.

Casework write delegates must move before assistant residual helpers so advisory surfaces continue to attach to directly linked authoritative case records.

Assistant residual helpers must move before detection/action residual helpers so recommendation and citation context cannot broaden evidence, case, or action linkage by sibling or same-parent inference.

Detection/action residual helpers must move before closeout so any residual `service.py` baseline decision is based on implementation evidence rather than a desired target.

The Phase 50.12 child issues are not parallelizable by default. A later issue may change the order only through another repo-owned decision that explicitly preserves the authority-boundary, authoritative-record, snapshot-consistency, and measurement rules in this ADR.

## 6. Validation

Run `bash scripts/verify-phase-50-12-service-facade-pressure-contract.sh`.

Run `bash scripts/test-verify-phase-50-12-service-facade-pressure-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `bash scripts/test-verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1016 --config <supervisor-config-path>`.

For the Phase 50.12 Epic, run the same issue-lint command for each Phase 50.12 child issue before allowing implementation slices to proceed.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No constructor, composition, action request, approval, casework write, assistant, detection, action, or external-evidence module split is approved by this ADR.
- No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed.
- No ticket, ML, endpoint, network, browser, optional-evidence, Wazuh, Shuffle, Zammad, deployment, database, migration, credential source, HTTP surface, CLI surface, or operator UI behavior is changed.
- No public service entrypoint, runtime behavior, configuration shape, authority semantic, response semantic, or durable-state side effect is changed.
- No baseline refresh is approved before Phase 50.12 implementation evidence exists.
- No subordinate source, operator-facing projection, summary, badge, counter, snapshot, DTO, recommendation, evidence snippet, reconciliation note, or helper-module output becomes authoritative workflow truth.
- No exception may raise the Phase 50.11.7 ceiling.
- No long-term 50-method completion claim is approved unless later child issues prove it safely.

## 8. Approval

- **Proposed By**: Codex for Issue #1016
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-30
