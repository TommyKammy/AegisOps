# ADR-0006: Phase 50.9 Residual Facade Convergence and Projection Hotspot Guard

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #974, #975
- **Depends On**: #967
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 50.8.6 closed #967 and recorded the current residual `service.py` ceiling in `docs/maintainability-hotspot-baseline.txt`.

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule.

ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

Phase 50.9 needs a repo-owned contract before the next implementation sequence starts so later slices do not choose local extraction order, treat the final Phase 50.8 ceiling as permission for facade growth, or move action-review projection pressure into another unchecked hotspot.

This ADR does not refresh the baseline because Phase 50.9 implementation evidence does not exist yet.

## 2. Decision

Phase 50.9 will continue residual facade convergence in a fixed, behavior-preserving order and will guard the action-review projection split from becoming a new accepted hotspot by accident.

The residual Phase 50.9 target clusters are:

- external evidence helper cluster
- persistence and record-shaping helper cluster
- internal-only delegate cluster
- action-review projection split cluster
- closeout and hotspot-baseline guard cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, projection response semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, and projections remain subordinate context.

## 3. Residual Facade Targets

The current Phase 50.8.6 ceiling remains:

- `max_lines=3505`
- `max_effective_lines=3182`
- `max_facade_methods=185`

The Phase 50.9 implementation target for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines <= 3000`
- `max_effective_lines <= 2750`
- `max_facade_methods <= 160`

A Phase 50.9 closeout may record a lower exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.8.6 ceiling.

Any `service.py` baseline refresh before Phase 50.9 implementation evidence exists is forbidden.

## 4. Projection Hotspot Guard

The action-review projection split target is `control-plane/aegisops_control_plane/action_review_projection.py`.

The projection split must preserve directly linked authoritative action-review records as the anchor for approval, execution, reconciliation, mismatch inspection, path health, coordination outcome, and runtime visibility surfaces.

The projection split must not widen advisory context, recommendation lineage, evidence anchors, reconciliation subject linkage, or operator-facing detail surfaces beyond directly linked authoritative records.

No `action_review_projection.py` hotspot baseline may be recorded before implementation evidence exists.

An `action_review_projection.py` baseline may be recorded only at Phase 50.9 closeout when all of these criteria are true:

- the projection split has already moved directly linked helper ownership out of `service.py`;
- the closeout records measured `action_review_projection.py` line and effective-line counts after the split;
- the closeout names the unresolved projection responsibility cluster;
- the recorded projection ceiling is lower than the pre-Phase 50.9 projection measurement of `max_lines=2034` and `max_effective_lines=1911`;
- the baseline entry names a Phase 50.9 closeout phase and issue;
- the closeout explicitly states why another split would be riskier than accepting the temporary projection hotspot.

If those criteria are not all true, the correct result is a follow-up decomposition issue, not a silent projection hotspot exception.

## 5. Migration Order

The Phase 50.9 migration order is:

1. external evidence helper cluster
2. persistence and record-shaping helper cluster
3. internal-only delegate cluster
4. action-review projection split cluster
5. closeout and hotspot-baseline guard cluster

External evidence helpers must move before persistence and record-shaping helpers so evidence admission stays subordinate to AegisOps-owned records.

Persistence and record-shaping helpers must move before internal-only delegates so delegate boundaries do not infer alert, case, action, lifecycle, or evidence linkage from names, paths, comments, or neighboring records.

Internal-only delegates must move before the projection split so projection surfaces continue to read from explicit authoritative records instead of convenience summaries.

The projection split must move before closeout so any `action_review_projection.py` hotspot baseline decision is based on implementation evidence rather than a desired target.

The Phase 50.9 child issues are not parallelizable by default. A later issue may change the order only through another repo-owned decision that explicitly preserves the authority-boundary, projection, and measurement rules in this ADR.

## 6. Validation

Run `bash scripts/verify-phase-50-9-residual-facade-convergence-contract.sh`.

Run `bash scripts/test-verify-phase-50-9-residual-facade-convergence-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 975 --config <supervisor-config-path>`.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No projection module split is approved by this ADR.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, detection, external-evidence, or operator authority behavior is changed.
- No deployment, database, migration, credential source, external substrate, HTTP surface, CLI surface, or operator UI behavior is changed.
- No public service entrypoint, runtime behavior, configuration shape, authority semantic, projection response semantic, or durable-state side effect is changed.
- No baseline refresh is approved before Phase 50.9 implementation evidence exists.
- No subordinate source, operator-facing projection, summary, badge, counter, recommendation, evidence snippet, or reconciliation note becomes authoritative workflow truth.
- No exception may raise the Phase 50.8.6 ceiling.

## 8. Approval

- **Proposed By**: Codex for Issue #975
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-29
