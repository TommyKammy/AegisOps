# Phase 50 Maintainability Closeout

Phase 50.12.7 records the accepted final `service.py` residual closeout after the Phase 50.11.7 ordered DTO/helper extraction sequence and the Phase 50.12.2/50.12.3/50.12.4/50.12.5/50.12.6 facade-pressure reductions governed by ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0008, and ADR-0009.

This closeout is validation and documentation only. It does not change runtime behavior, public APIs, approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, or operator authority.

ADR-0004 governs the Phase 50 migration order and closeout validation. ADR-0005 governs the Phase 50.8 residual service migration contract. ADR-0006 governs the Phase 50.9 residual facade convergence and projection guard. ADR-0007 governs the Phase 50.10 facade floor and external-evidence guard. ADR-0008 governs the Phase 50.11 residual DTO/helper extraction order. ADR-0003 remains the facade-preservation exception authority for the remaining `service.py` baseline entry.

## Accepted Verifier State

The maintainability verifier still reports one remaining accepted hotspot:

- `control-plane/aegisops_control_plane/service.py`

That result is expected because `AegisOpsControlPlaneService` remains the public facade after the Phase 50.11 DTO/snapshot, runtime-event, action-review inspection, assistant-advisory, and detection/case-linkage helper extraction work accepted in #1007. Phase 50.12.2 for #1017 further extracted constructor composition assignment pressure, Phase 50.12.3 for #1018 moved reviewed action approval policy helper pressure into the action-review write surface, Phase 50.12.4 for #1019 fenced casework write compatibility delegates behind the case workflow facade, Phase 50.12.5 for #1020 moved assistant residual lifecycle helper delegates out of the service facade and onto the extracted AI trace lifecycle boundary, and Phase 50.12.6 for #1021 moved reviewed action visibility persistence helpers into the action-review write surface while retaining public detection intake and action reconciliation facade delegates. Phase 50.13.3 for #1033 moved the remaining owned case-detail, alert-projection, and reviewed action-request binding guards into `control-plane/aegisops_control_plane/operator_inspection.py` and `control-plane/aegisops_control_plane/execution_coordinator_action_requests.py`. The accepted residual ceiling is:

- `max_lines=1393`
- `max_effective_lines=1241`
- `max_facade_methods=95`
- `facade_class=AegisOpsControlPlaneService`
- `adr_exception=ADR-0003`
- `phase=50.13.3`
- `issue=#1033`

The measured Phase 50.13.3 closeout state is:

- `physical_lines=1393`
- `effective_lines=1241`
- `AegisOpsControlPlaneService methods=95`

The baseline is lower than the Phase 50.11.7 ceiling of `max_lines=1812`, `max_effective_lines=1632`, and `max_facade_methods=125`. It also reached the ADR-0009 Phase 50.12 physical-line, effective-line, and method-count targets of `max_lines <= 1500`, `max_effective_lines <= 1350`, and `max_facade_methods <= 95`. The retained `95` facade methods are accepted only as an ADR-0003 facade-preservation exception because the remaining public compatibility entrypoints continue to protect existing callers while delegating into extracted boundaries.

No additional baseline entry is recorded for restore validation, HTTP surface, assistant, detection, operator inspection, operator UI route tests, `control-plane/aegisops_control_plane/action_review_projection.py`, or `control-plane/aegisops_control_plane/external_evidence_boundary.py` because the verifier does not report those areas as current responsibility-growth candidates. The earlier Phase 50.9 projection measurement was `projection lines=105` and `projection effective_lines=103`, so the projection split does not require a baseline entry. The earlier Phase 50.10 external-evidence measurement was `external_evidence_boundary.py lines=216` and `external_evidence_boundary.py effective_lines=195`, so the external-evidence split does not require a baseline entry.

The remaining accepted hotspot is not a general extension target. The residual helper pressure is concentrated in facade dispatch, compatibility entrypoints, runtime-boundary guards, and lifecycle/write-path delegates that still sit behind the public facade. Those helpers remain review-visible because they protect action review state, detection intake linkage, external-evidence linkage, authoritative restore validation, and fail-closed authoritative-state reads at the service boundary.

## Phase 50.11 Extraction Evidence

The final Phase 50.11 extraction sequence moved the following directly linked helper clusters out of `service.py`:

- service snapshot DTO shaping into `control-plane/aegisops_control_plane/service_snapshots.py`;
- structured runtime-event sanitization into `control-plane/aegisops_control_plane/structured_events.py`;
- action-review inspection assembly into `control-plane/aegisops_control_plane/action_review_inspection.py`;
- assistant advisory facade helpers into `control-plane/aegisops_control_plane/assistant_advisory.py` and `control-plane/aegisops_control_plane/live_assistant_workflow.py`;
- detection/case-linkage helpers into `control-plane/aegisops_control_plane/case_workflow.py`, `control-plane/aegisops_control_plane/detection_lifecycle.py`, and `control-plane/aegisops_control_plane/detection_lifecycle_helpers.py`.

Phase 50.12.3 then moved the reviewed action approval policy helpers out of `service.py` and into `control-plane/aegisops_control_plane/action_review_write_surface.py`, preserving the public facade entrypoints for action request creation and approval decision recording.

Phase 50.12.4 then moved the casework write compatibility delegates out of `AegisOpsControlPlaneService` and into `control-plane/aegisops_control_plane/case_workflow.py`, preserving the public facade entrypoints for observation, lead, recommendation, handoff, and disposition writes.

Phase 50.12.5 then removed the remaining assistant residual lifecycle helper delegates from `AegisOpsControlPlaneService` and routed direct consumers through `control-plane/aegisops_control_plane/ai_trace_lifecycle.py`, preserving assistant context, advisory output, recommendation draft, live assistant workflow, readiness, and action-review linkage behavior.

Phase 50.12.6 then moved the remaining reviewed action visibility persistence helpers out of `AegisOpsControlPlaneService` and into `control-plane/aegisops_control_plane/action_review_write_surface.py`, preserving manual fallback, escalation-note, approval-decision, detection intake, and action execution reconciliation behavior. `ingest_finding_alert` and `reconcile_action_execution` remain public facade delegates because callers rely on those compatibility entrypoints; their implementation bodies remain single-hop delegates to the extracted detection intake and action lifecycle boundaries.

Phase 50.13.3 then moved owned private guard helpers out of `AegisOpsControlPlaneService`: `_observations_for_case`, `_leads_for_case`, and `_alert_review_state` now live with `OperatorInspectionReadSurface`; `_require_single_linked_case_id` and `_require_single_recommendation_binding` now live with `ReviewedActionRequestCoordinator`. This lowers the previous #1022 Phase 50.12.7 ceiling without changing public facade behavior. The relocation preserves exception text and keeps shared facade-boundary guards such as identifier allocation and reviewed-slice policy checks on the service until their direct caller evidence supports a narrower owner.

Those extractions preserve the public service facade. AegisOps control-plane records remain authoritative workflow truth. Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context.

## Follow-Up Trigger

The service facade is below the long-term 1,500-line target, but it remains above the long-term 50-method target. The retained method-count ceiling is therefore an accepted exception, not a success target.

Any silent re-growth beyond the recorded ceiling must fail the verifier. The expected response is another decomposition decision or maintainability backlog before unrelated feature expansion lands in the facade.

If a later extraction lowers the facade below the verifier threshold, maintainers should remove or lower the baseline only after confirming that the file no longer crosses the responsibility-growth threshold.

If future work needs to add another action-review surface, intake pathway, authoritative restore/read guard, external-evidence linkage path, runtime-boundary guard, assistant linkage path, detection/case linkage path, or cross-record projection helper to `service.py`, that is the follow-up trigger for another maintainability issue. The follow-up should extract or fence the directly linked helper cluster instead of using this exception as approval for new facade responsibility. If `action_review_projection.py` grows back toward the Phase 50.9 pre-split measurement of `max_lines=2034` or `max_effective_lines=1911`, the follow-up should split that directly linked projection cluster instead of silently recording a new projection hotspot exception. If `external_evidence_boundary.py` grows back toward the pre-Phase 50.10 measurement of `max_lines=1083` or `max_effective_lines=1033`, the follow-up should split the directly linked MISP, osquery, or endpoint-evidence helper cluster instead of recording a silent external-evidence hotspot exception.

## Verification Evidence

Run:

- `bash scripts/verify-maintainability-hotspots.sh`
- `bash scripts/test-verify-maintainability-hotspots.sh`
- `bash scripts/verify-phase-50-12-service-facade-pressure-contract.sh`
- `bash scripts/test-verify-phase-50-12-service-facade-pressure-contract.sh`
- `python3 -m unittest control-plane/tests/test_phase50_maintainability_closeout.py`

The focused negative verifier coverage remains in `scripts/test-verify-maintainability-hotspots.sh` through the `regrowth_repo`, `phase50_11_regrowth_repo`, and `phase50_12_final_regrowth_repo` fixtures, which verify that line-count, effective-line, and facade-method growth beyond the recorded ceiling still fails closed.
