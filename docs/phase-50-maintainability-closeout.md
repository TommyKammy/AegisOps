# Phase 50 Maintainability Closeout

Phase 50.9.6 closes the ordered maintainability hotspot reduction sequence governed by ADR-0004, ADR-0005, and ADR-0006.

This closeout is validation and documentation only. It does not change runtime behavior, public APIs, approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, or operator authority.

ADR-0004 governs the Phase 50 migration order and closeout validation. ADR-0005 governs the Phase 50.8 residual service migration contract. ADR-0006 governs the Phase 50.9 residual facade convergence and projection guard. ADR-0003 remains the facade-preservation exception authority for the remaining `service.py` baseline entry.

## Accepted Verifier State

The maintainability verifier still reports one remaining accepted hotspot:

- `control-plane/aegisops_control_plane/service.py`

That result is expected because `AegisOpsControlPlaneService` remains the public facade after the Phase 50.9 extraction and fencing work. The final Phase 50.9.6 closeout for #980 records the accepted residual ceiling as:

- `max_lines=3158`
- `max_effective_lines=2853`
- `max_facade_methods=173`
- `facade_class=AegisOpsControlPlaneService`
- `adr_exception=ADR-0003`
- `phase=50.9.6`

No additional baseline entry is recorded for restore validation, HTTP surface, assistant, detection, operator inspection, operator UI route tests, or `control-plane/aegisops_control_plane/action_review_projection.py` because the verifier does not report those areas as current responsibility-growth candidates. The Phase 50.9.6 projection measurement is `projection lines=105` and `projection effective_lines=103`, so the projection split does not require a baseline entry.

The remaining accepted hotspot is not a general extension target. The residual helper pressure is concentrated in facade dispatch and authority-boundary guard helpers that still sit behind the public facade. Those helpers remain review-visible because they protect action review state, detection intake linkage, and fail-closed authoritative-state reads at the service boundary.

## Follow-Up Trigger

The service facade remains above the long-term 1,500-line and 50-method targets. It is therefore an accepted exception, not a success target.

Any silent re-growth beyond the recorded ceiling must fail the verifier. The expected response is another decomposition decision or maintainability backlog before unrelated feature expansion lands in the facade.

If a later extraction lowers the facade below the verifier threshold, maintainers should remove or lower the baseline only after confirming that the file no longer crosses the responsibility-growth threshold.

If future work needs to add another action-review surface, intake pathway, authoritative restore/read guard, or cross-record projection helper to `service.py`, that is the follow-up trigger for another maintainability issue. The follow-up should extract or fence the directly linked helper cluster instead of using this exception as approval for new facade responsibility. If `action_review_projection.py` grows back toward the Phase 50.9 pre-split measurement of `max_lines=2034` or `max_effective_lines=1911`, the follow-up should split that directly linked projection cluster instead of silently recording a new projection hotspot exception.

## Verification Evidence

Run:

- `bash scripts/verify-maintainability-hotspots.sh`
- `bash scripts/test-verify-maintainability-hotspots.sh`
- `python3 -m unittest control-plane/tests/test_phase50_maintainability_closeout.py`

The focused negative verifier coverage remains in `scripts/test-verify-maintainability-hotspots.sh` through the `regrowth_repo` fixture, which verifies that line-count, effective-line, and facade-method growth beyond the recorded ceiling still fails closed.
