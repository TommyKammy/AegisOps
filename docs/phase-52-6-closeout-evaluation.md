# Phase 52.6 Closeout Evaluation

**Status**: Accepted as compatibility shim deprecation and root package reduction; Phase 53 Wazuh product profile work can start after #1112 lands.

**Related Issues**: #1105, #1106, #1107, #1108, #1109, #1110, #1111, #1112

**Authority Boundary**: This closeout is release and planning evidence only. AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth. Compatibility import aliases, root shim inventory, verifier output, issue-lint output, and this document do not change runtime workflow truth.

Phase 52.6 is accepted as the compatibility shim deprecation and root package reduction phase that keeps the public `aegisops_control_plane` package name, the outer `control-plane/` repository directory, retained owners, retained blockers, and existing runtime/product behavior unchanged while retiring approved physical root shim files behind explicit alias registry coverage.

This closeout does not claim that Wazuh product profiles are complete, Shuffle product profiles are complete, AegisOps is GA, RC, Beta, or self-service commercially ready, or that runtime behavior changed during Phase 52.6.

## Child Issue Outcomes

| Issue | Scope | Outcome |
| --- | --- | --- |
| #1105 | Epic: Phase 52.6 Compatibility Shim Deprecation and Root Package Reduction | Open until #1112 lands; accepted when this closeout, verifiers, and issue-lint pass. |
| #1106 | Phase 52.6.1 root shim inventory and deprecation contract | Closed. ADR-0014 records the root shim inventory, Phase 52.5 baseline, root file classifications, deprecation decision rules, and Phase29 boundary. PR #1113. |
| #1107 | Phase 52.6.2 canonical domain import rewiring | Closed. Internal callers use canonical domain owner imports while approved compatibility usage remains bounded to shims, tests, and docs. PR #1114. |
| #1108 | Phase 52.6.3 legacy import alias registry and compatibility tests | Closed. ADR-0015 and `legacy_import_aliases.py` preserve approved legacy import paths without one physical shim per path. PR #1115. |
| #1109 | Phase 52.6.4 remove simple physical root shims covered by alias registry | Closed. Twenty-one simple physical root shims were deleted after registry aliases and focused import regressions proved compatibility. PR #1116. |
| #1110 | Phase 52.6.5 retire Phase29 root filenames safely | Closed. Four Phase29-named root files were retired, with `ml_shadow` owners and a legacy scoring adapter preserving the reviewed compatibility surface. PR #1117. |
| #1111 | Phase 52.6.6 tighten root package guardrails and retained-root owner policy | Closed. The root guardrail baseline is pinned to 37 direct root Python files, retained owners are explicit, Phase29 root filenames are rejected, and `service.py` stays a retained compatibility blocker. PR #1118. |
| #1112 | Phase 52.6.7 Phase 52.6 closeout evaluation | Open until this closeout lands; accepted when this document, focused verifier, all Phase 52.6 verifiers, issue-lint, and path hygiene pass. |

## Root Package Count

| Baseline | Direct root `.py` files under `control-plane/aegisops_control_plane/` |
| --- | ---: |
| Phase 52.5 baseline before Phase 52.6 deletions | 63 |
| Phase 52.6.5 and Phase 52.6.6 accepted baseline after approved shim and Phase29 filename deletion | 37 |

The after count is intentionally bounded to direct root `.py` files. Package-owned files below subdirectories remain governed by ADR-0012 and are outside the root shim count.

## Deleted Shims And Phase29 Files

Phase 52.6.3 deleted `audit_export.py` as the proof-of-pattern physical root shim removal while preserving `aegisops_control_plane.audit_export` through the legacy import alias registry.

Phase 52.6.4 deleted these 21 simple physical root shims after adding explicit registry aliases and focused compatibility tests:

`action_receipt_validation.py`, `action_review_chain.py`, `action_review_coordination.py`, `action_review_index.py`, `action_review_inspection.py`, `action_review_path_health.py`, `action_review_timeline.py`, `action_review_visibility.py`, `assistant_provider.py`, `detection_lifecycle_helpers.py`, `detection_native_context.py`, `entrypoint_support.py`, `execution_coordinator.py`, `execution_coordinator_delegation.py`, `execution_coordinator_reconciliation.py`, `external_evidence_endpoint.py`, `external_evidence_facade.py`, `external_evidence_misp.py`, `external_evidence_osquery.py`, `operations.py`, and `service_snapshots.py`.

Phase 52.6.5 deleted these four Phase29 root filenames after adding explicit registry aliases and focused compatibility tests:

`phase29_shadow_dataset.py`, `phase29_shadow_scoring.py`, `phase29_evidently_drift_visibility.py`, and `phase29_mlflow_shadow_model_registry.py`.

## Retained Owners, Blockers, And Compatibility Status

Retained root owners are exactly `__init__.py`, `config.py`, `models.py`, `operator_inspection.py`, `persistence_lifecycle.py`, `publishable_paths.py`, `record_validation.py`, `reviewed_slice_policy.py`, `service_composition.py`, and `structured_events.py`.

Retained blockers remain physical root files until later accepted ADRs or issue-specific contracts prove caller evidence, replacement paths, deprecation window, focused regression coverage, rollback path, and authority-boundary impact. The retained compatibility blocker is `service.py`; root shim files that current regression tests still inspect directly also remain physical compatibility blockers rather than retained owners.

Phase29 root filename status: no direct root Python filename begins with `phaseNN` or `phaseNN_` after Phase 52.6.6. Legacy `aegisops_control_plane.phase29_*` import paths remain available only through the alias registry and focused compatibility tests, with production owners under `ml_shadow/`.

Compatibility import status: approved legacy import paths deleted from the physical root remain registered aliases to explicit owner modules. The Phase29 scoring legacy path resolves to `ml_shadow/legacy_scoring_adapter.py` to preserve old wrapper fields while canonical scoring remains owned by `ml_shadow/scoring.py`.

## Verifier Evidence

Focused Phase 52.6 verifiers passed:

- `bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`: root shim inventory records the Phase 52.5 root file baseline, accepted deletion sets, retained blockers, and root count baseline.
- `bash scripts/test-verify-phase-52-6-1-root-shim-inventory-contract.sh`: root inventory negative and valid fixtures passed.
- `bash scripts/verify-phase-52-6-2-canonical-domain-imports.sh`: internal callers use canonical domain imports; approved legacy compatibility usage remains bounded.
- `bash scripts/test-verify-phase-52-6-2-canonical-domain-imports.sh`: canonical import negative and valid fixtures passed.
- `bash scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh`: approved aliases preserve module identity or compatibility behavior, target owner metadata, and retained blockers.
- `bash scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh`: alias registry negative and valid fixtures passed.
- `python3 -m unittest control-plane/tests/test_phase52_6_4_root_shim_alias_removal.py`: deleted simple root shims are registry aliases and retained physical blockers remain present.
- `bash scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh`: Phase29 root filenames are retired, `ml_shadow` remains the owner, and legacy import compatibility is explicitly registered.
- `bash scripts/test-verify-phase-52-6-5-retire-phase29-root-filenames.sh`: Phase29 retirement negative and valid fixtures passed.
- `python3 -m unittest control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py`: Phase29 legacy imports resolve through registered aliases and preserve the required compatibility surface.
- `bash scripts/verify-phase-52-6-6-root-package-guardrails.sh`: 37 root Python files remain, retained-owner set is pinned, phase-numbered root filenames are rejected, and `service.py` stays under retained compatibility-blocker policy.
- `bash scripts/test-verify-phase-52-6-6-root-package-guardrails.sh`: root count, retained-owner, phase-numbered filename, and blocker negative fixtures passed.
- `bash scripts/verify-phase-52-5-2-import-compatibility.sh`: stable legacy imports and target imports remain preserved for moved modules and the service/model baseline.
- `bash scripts/verify-phase-52-5-2-layout-guardrail.sh`: current classified baseline passes and new unclassified or phase-numbered production modules are rejected.
- `bash scripts/verify-phase-52-5-9-service-facade-freeze.sh`: `service.py` remains at 1393 lines, 1241 effective lines, and 95 `AegisOpsControlPlaneService` methods; domain package internals avoid legacy compatibility shims.
- `bash scripts/verify-publishable-path-hygiene.sh`: publishable tracked content does not contain workstation-local absolute paths.
- `bash scripts/verify-phase-52-6-closeout-evaluation.sh`: this closeout records child outcomes, root file-count before/after, deleted shims, retained owners, retained blockers, Phase29 filename status, compatibility status, verifier evidence, issue-lint summary, accepted limitations, and bounded Phase 53 recommendation.
- `bash scripts/test-verify-phase-52-6-closeout-evaluation.sh`: closeout negative fixtures reject Wazuh/Shuffle completion overclaims, missing retained compatibility blockers, missing Phase29 root filename status, and workstation-local absolute paths.

Broad control-plane test evidence:

- `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`: 939 broad control-plane tests passed after the import-alias and root package guardrail changes.

Issue-lint evidence for #1105 through #1112:

- `node <codex-supervisor-root>/dist/index.js issue-lint 1105 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1106 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1107 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1108 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1109 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1110 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1111 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.
- `node <codex-supervisor-root>/dist/index.js issue-lint 1112 --config <supervisor-config-path>`: `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, `high_risk_blocking_ambiguity=none`.

## Accepted Limitations And Retained Blockers

- The public package name remains `aegisops_control_plane`; a rename requires a later accepted ADR, caller evidence, operator migration plan, focused regression tests, and rollback path.
- The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.
- `service.py` remains a retained compatibility blocker under ADR-0003 and ADR-0010; Phase 52.6 does not complete all future facade decomposition.
- Retained root owners remain physical files until a later owner-move issue proves identical behavior, caller compatibility, rollback path, and authority-boundary impact.
- Root shim files still inspected by current regression tests remain physical compatibility blockers until those tests and callers are migrated deliberately.
- Legacy import aliases are compatibility mechanisms only. They do not make compatibility state, summary text, module identity, Wazuh state, Shuffle state, tickets, assistant output, generated config, CLI status, or operator-facing text authoritative workflow truth.
- Phase 52.6 does not implement Wazuh product profiles, Shuffle product profiles, public package rename, outer directory rename, product behavior changes, deployment behavior changes, authorization changes, provenance changes, snapshot semantics changes, backup/restore changes, export changes, readiness changes, assistant behavior changes, evidence behavior changes, action-execution behavior changes, HTTP behavior changes, CLI behavior changes, or durable-state changes.

## Phase 53 Recommendation

Phase 53 can start after #1112 lands and all Phase 52.6 verifiers remain green. No additional shim cleanup is required before starting the bounded Wazuh product profile implementation.

The recommendation is bounded to Wazuh product profile materialization. Phase 53 should consume the reduced root package surface, keep retained owners and retained blockers intact, and avoid public package rename, outer directory rename, Shuffle profile work, or additional shim deletion unless a later accepted ADR explicitly changes that boundary.

Do not treat this recommendation as a claim that the Wazuh product profile is complete, Shuffle product profile work is complete, or Phase 52.6 changed runtime product behavior.
