# ADR-0008: Phase 50.11 Service Residual Extraction Contract

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #1000, #1001
- **Depends On**: #993
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 50.10.6 closed #993 and recorded the accepted residual `service.py` ceiling in `docs/maintainability-hotspot-baseline.txt`.

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule.

ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence.

ADR-0006 remains authoritative for the Phase 50.9 residual facade convergence and projection hotspot guard.

ADR-0007 remains authoritative for the Phase 50.10 facade floor and external-evidence guard.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

Phase 50.11 needs a repo-owned contract before residual DTO/helper extraction starts so later slices do not choose local extraction order, treat the Phase 50.10.6 ceiling as permission for facade growth, or move authority-boundary helper pressure into unchecked modules.

This ADR does not refresh the baseline because Phase 50.11 implementation evidence does not exist yet and follow-on implementation slices remain.

## 2. Decision

Phase 50.11 will reduce the residual `service.py` hotspot by extracting DTO/snapshot shaping and helper clusters in a fixed, behavior-preserving order.

The Phase 50.11 residual extraction clusters are:

- DTO/snapshot extraction cluster
- runtime auth helper cluster
- action-review helper cluster
- assistant linkage helper cluster
- detection/case-linkage helper cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, response semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context.

## 3. Starting Measurements

The Phase 50.10.6 starting ceiling for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines=3003`
- `max_effective_lines=2704`
- `max_facade_methods=167`
- `facade_class=AegisOpsControlPlaneService`
- `phase=50.10.6`
- `issue=#993`

The same values are the Phase 50.11 starting measurements before implementation slices begin:

- `physical_lines=3003`
- `effective_lines=2704`
- `AegisOpsControlPlaneService methods=167`

The Phase 50.11 implementation target for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines <= 2700`
- `max_effective_lines <= 2450`
- `max_facade_methods <= 150`

A Phase 50.11 closeout may record a lower exception only if it names the unresolved residual cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.10.6 ceiling.

Any `service.py` baseline refresh before Phase 50.11 implementation evidence exists is forbidden.

## 4. Extraction Scope

The DTO/snapshot extraction cluster owns internal data shaping for response DTOs, snapshot views, and operator-facing projection assembly that is already anchored to authoritative AegisOps records.

The runtime auth helper cluster owns internal helper code for principal, tenant, scope, and runtime-boundary checks without trusting forwarded headers, client-supplied identity fields, placeholder credentials, or inferred scope.

The action-review helper cluster owns internal helper code that shapes approval, execution, delegation, reconciliation, mismatch, and receipt views while preserving authoritative action-review records as the source of truth.

The assistant linkage helper cluster owns internal helper code that attaches assistant, advisory, recommendation, and citation context only through explicit authoritative links.

The detection/case-linkage helper cluster owns internal helper code that binds detection intake, case linkage, external-evidence linkage, and evidence admission to explicit authoritative records.

No extracted helper may infer tenant, repository, account, issue, case, alert, host, environment, approval, execution, reconciliation, assistant, detection, or evidence linkage from naming conventions, path shape, comments, nearby metadata, sibling records, or operator-facing summaries alone.

## 5. Migration Order

The Phase 50.11 migration order is:

1. DTO/snapshot extraction cluster
2. runtime auth helper cluster
3. action-review helper cluster
4. assistant linkage helper cluster
5. detection/case-linkage helper cluster
6. closeout and hotspot-baseline guard cluster

DTO/snapshot helpers must move before authority-bearing helpers so read-shaping code is separated from enforcement logic before later slices touch auth, action-review, assistant, or detection linkage.

Runtime auth helpers must move before action-review, assistant, and detection/case-linkage helpers so later helper boundaries keep using normalized trusted auth context instead of client-supplied hints.

Action-review helpers must move before assistant linkage helpers so advisory surfaces continue to attach to directly linked authoritative approval, execution, delegation, reconciliation, and receipt records.

Assistant linkage helpers must move before detection/case-linkage helpers so recommendation and citation context cannot broaden evidence or case linkage by sibling or same-parent inference.

Detection/case-linkage helpers must move before closeout so any residual `service.py` baseline decision is based on implementation evidence rather than a desired target.

The Phase 50.11 child issues are not parallelizable by default. A later issue may change the order only through another repo-owned decision that explicitly preserves the authority-boundary, authoritative-record, snapshot-consistency, and measurement rules in this ADR.

## 6. Validation

Run `bash scripts/verify-phase-50-11-service-residual-extraction-contract.sh`.

Run `bash scripts/test-verify-phase-50-11-service-residual-extraction-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `bash scripts/test-verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1001 --config <supervisor-config-path>`.

For the Phase 50.11 Epic, run the same issue-lint command for each Phase 50.11 child issue before allowing implementation slices to proceed.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No DTO, snapshot, runtime auth, action-review, assistant linkage, detection, case-linkage, or external-evidence module split is approved by this ADR.
- No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed.
- No ticket, ML, endpoint, network, browser, optional-evidence, Wazuh, Shuffle, Zammad, deployment, database, migration, credential source, HTTP surface, CLI surface, or operator UI behavior is changed.
- No public service entrypoint, runtime behavior, configuration shape, authority semantics, response semantic, or durable-state side effect is changed.
- No baseline refresh is approved before Phase 50.11 implementation evidence exists.
- No subordinate source, operator-facing projection, summary, badge, counter, snapshot, DTO, recommendation, evidence snippet, reconciliation note, or helper-module output becomes authoritative workflow truth.
- No exception may raise the Phase 50.10.6 ceiling.

## 8. Approval

- **Proposed By**: Codex for Issue #1001
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-30
