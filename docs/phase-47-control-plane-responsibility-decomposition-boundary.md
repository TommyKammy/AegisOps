# AegisOps Phase 47 Control-Plane Responsibility Decomposition Boundary

## 1. Purpose

This document defines the reviewed Phase 47 control-plane responsibility decomposition boundary.

It retroactively closes the Phase 47 contract around behavior-preserving coordinator extractions, readiness contract isolation, external evidence coordination, assistant advisory coordination, and the maintainability hotspot verifier.

It supplements `docs/control-plane-service-internal-boundaries.md`, `docs/maintainability-decomposition-thresholds.md`, `docs/maintainability-hotspot-baseline.txt`, `docs/control-plane-runtime-service-boundary.md`, `docs/response-action-safety-model.md`, `docs/control-plane-state-model.md`, and `docs/architecture.md`.

This document describes the closed Phase 47 decomposition contract only. It does not change runtime behavior, authority posture, action behavior, evidence authority, assistant authority, readiness behavior, public facade signatures, or deployment posture.

## 2. In Scope

Phase 47 closes one narrow control-plane maintainability contract:

- action lifecycle write routing stays delegated through `control-plane/aegisops_control_plane/action_lifecycle_write_coordinator.py`;
- readiness runtime status coordination keeps shared readiness DTO and status-resolution ownership in `control-plane/aegisops_control_plane/readiness_contracts.py`;
- external evidence coordination stays delegated through `control-plane/aegisops_control_plane/external_evidence_boundary.py`;
- assistant advisory coordination stays delegated through `control-plane/aegisops_control_plane/assistant_advisory.py` and the existing assistant context assembler;
- focused coordinator and boundary tests remain the executable proof that public `AegisOpsControlPlaneService` entrypoints preserve the reviewed behavior; and
- the maintainability hotspot verifier remains the guard that records `control-plane/aegisops_control_plane/service.py` as a known reviewed hotspot instead of pretending the hotspot is solved.

Phase 47 is a behavior-preserving decomposition closure. It records that selected responsibilities moved behind narrower collaborators while AegisOps control-plane records remain authoritative and the public facade remains stable for reviewed callers.

## 3. Out of Scope

Phase 47 does not authorize:

- Phase 49.0 service decomposition;
- new coordinator extraction beyond the implementation already landed before this documentation closure;
- new runtime behavior, HTTP routes, CLI commands, action types, evidence sources, assistant capabilities, approval paths, execution paths, reconciliation outcomes, readiness states, or deployment paths;
- treating assistants, optional evidence, external tickets, downstream receipts, browser state, source substrates, forwarded headers, placeholder credentials, or operator-facing projections as authority;
- changing maintainability thresholds or hotspot baselines without an explicit verifier-backed rationale; or
- claiming commercial readiness, completed third-stage service decomposition, or elimination of `service.py` responsibility concentration.

`service.py` remains a reviewed maintainability hotspot. Further concentration reduction belongs to Phase 49.0, not to this Phase 47 documentation closure.

## 4. Action Lifecycle Write Routing

Action lifecycle write routing is anchored in `control-plane/aegisops_control_plane/action_lifecycle_write_coordinator.py`.

`AegisOpsControlPlaneService` remains the public facade for action lifecycle writes, but the write routing behind these facade entrypoints is owned by the coordinator. The reviewed delegation covers action request creation from assistant advisory context, tracking-ticket action requests, approval decision recording, delegation binding, and reconciliation write coordination.

The coordinator extraction must preserve the existing fail-closed authority model:

- action requests remain bound to explicit AegisOps record identifiers, reviewed payloads, approval scope, and expiry constraints;
- approval decisions do not become execution or reconciliation truth;
- execution receipts do not become reconciliation truth;
- downstream tickets, comments, receipts, assistant summaries, or substrate status do not replace AegisOps action records; and
- missing, malformed, placeholder-like, stale, or mismatched approval, execution, provenance, payload, or scope signals keep the write path blocked or unresolved.

The public facade may forward to the coordinator, but it must not infer successful action lifecycle state from naming conventions, path shape, nearby metadata, external ticket state, or subordinate context.

## 5. Readiness Runtime Status Coordination

Readiness runtime status coordination is anchored in `control-plane/aegisops_control_plane/readiness_contracts.py`.

The readiness contract extraction keeps shared readiness aggregate DTOs and runtime status resolution in one explicit module so runtime surfaces and readiness collaborators do not reach through persistence adapter internals for status semantics.

Readiness status remains derived from AegisOps-owned runtime, readiness, backup, restore, restore-drill, and lifecycle facts. Operator-facing readiness text, HTTP response shape, dashboard display, or optional substrate health is a projection over those facts, not an independent source of truth.

If readiness inputs are missing, malformed, mixed across snapshots, stale, or contradictory, the reviewed posture is degraded, blocked, unavailable, or explicit follow-up. Phase 47 does not allow readiness success to be inferred from summary text, a successful HTTP render, optional extension availability, or a downstream substrate response.

## 6. External Evidence Coordination

External evidence coordination is anchored in `control-plane/aegisops_control_plane/external_evidence_boundary.py`.

The extraction keeps MISP, osquery, and endpoint evidence request handling behind a boundary that preserves AegisOps evidence authority. External evidence may enrich a reviewed record only when the AegisOps record chain explicitly binds the evidence subject, source, provenance, and linked case or alert context.

External evidence remains subordinate context. Optional evidence, enrichment payloads, endpoint artifacts, ticket references, source-substrate metadata, and downstream receipts do not become alert, case, approval, execution, reconciliation, readiness, or audit truth.

When evidence provenance, source identity, subject linkage, tenant or repository binding, credential custody, or record linkage is absent or only partially trusted, the boundary must fail closed by rejecting the write, keeping the evidence unresolved, or surfacing a follow-up instead of accepting guessed context.

## 7. Assistant Advisory Coordination

Assistant advisory coordination is anchored in `control-plane/aegisops_control_plane/assistant_advisory.py` and the existing `AssistantContextAssembler`.

The coordinator exposes advisory-only operations for inspected advisory output, recommendation draft rendering, and assistant advisory draft attachment. It must not expose approval, execution, reconciliation, case closure, readiness, credential, or production write authority.

Assistant output remains subordinate to reviewed AegisOps records and linked evidence. The coordinator may assemble citation-grounded context and advisory drafts, but it must preserve unresolved status when identity, provenance, citation, scope, or subject-linkage signals are missing or ambiguous.

An assistant advisory draft attached to one record must not be generalized to a neighboring recommendation, case, action, lineage-relative surface, or same-parent record unless an explicit authoritative link says it applies there.

## 8. Maintainability Hotspot Verifier

The maintainability hotspot verifier is `scripts/verify-maintainability-hotspots.sh`.

The verifier reads `docs/maintainability-decomposition-thresholds.md` and `docs/maintainability-hotspot-baseline.txt` to distinguish known reviewed hotspots from new responsibility growth.

The current reviewed baseline intentionally includes:

- `control-plane/aegisops_control_plane/service.py`

This baseline entry is not an exemption for additional responsibility growth. It is an explicit reminder that `AegisOpsControlPlaneService` still concentrates multiple reviewed concerns even after Phase 47 reduced selected routing and coordination responsibilities.

If the verifier reports a new hotspot, maintainers should apply the threshold guidance and open a focused decomposition backlog rather than extend the file by default. If the verifier reports that the baseline entry is stale, maintainers should update the baseline only after confirming the hotspot no longer crosses the responsibility-growth threshold.

## 9. Remaining Service Decomposition Debt

Phase 47 reduced concentration but did not complete third-stage service decomposition.

`control-plane/aegisops_control_plane/service.py` and `AegisOpsControlPlaneService` still remain a known responsibility concentration point for runtime and auth boundaries, detection intake, analyst workflow facade routing, assistant and advisory facade routing, action governance facade routing, readiness and restore facade routing, and Phase 19 slice policy boundaries.

The correct handoff is Phase 49.0:

- continue decomposing the remaining `service.py` responsibility clusters under the existing `docs/control-plane-service-internal-boundaries.md` target shape;
- preserve public facade entrypoints unless an explicit follow-up changes the reviewed API;
- keep authority-bearing validation and transaction boundaries anchored to the real enforcement point;
- add focused regression coverage for each extracted cluster; and
- avoid combining service decomposition with new feature scope or commercial readiness claims.

Phase 47 must not be cited as proof that AegisOps is commercially ready or that `AegisOpsControlPlaneService` is no longer a maintainability concern.

## 10. Fail-Closed Conditions

Phase 47 must fail closed when any prerequisite provenance, scope, auth context, subject linkage, transaction boundary, snapshot, readiness, evidence, assistant, approval, execution, or reconciliation signal is missing, malformed, stale, mixed, placeholder-like, or only partially trusted.

Blocking conditions include:

- action lifecycle writes lack explicit AegisOps request, approval, payload, scope, expiry, execution, or reconciliation binding;
- assistant output, optional evidence, downstream receipts, external tickets, browser state, source-substrate status, operator-facing summaries, or convenience projections are treated as authority;
- external evidence lacks reviewed provenance, source identity, subject linkage, credential custody, or direct AegisOps record binding;
- readiness status is inferred from summary text, HTTP rendering, optional substrate health, or mixed-snapshot reads instead of authoritative readiness facts;
- raw forwarded headers, host, proto, tenant, user identity hints, or client-supplied scope fields are trusted without a reviewed authenticated boundary;
- placeholder, sample, fake, TODO, unsigned, empty, stale, or unreviewed credentials are accepted as live custody;
- a coordinator extraction changes public behavior, widens authority, collapses approval, execution, and reconciliation, or hides an unresolved state;
- one logical write persists partial durable state after a rejected, forbidden, failed, or restore-failure path; or
- documentation, validation commands, fixtures, prompts, or operator notes introduce workstation-local absolute paths, hidden manual steps, live secrets, or production write behavior.

When one of these conditions appears, the correct result is rejection, blocked execution, explicit unresolved or degraded status, unavailable posture, rollback, or a documented follow-up. The system must not infer success from names, path shape, nearby metadata, ticket state, assistant text, receipt wording, or display order.

## 11. Authority Boundary Notes

AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, approval, action intent, execution receipt, reconciliation, lifecycle, readiness, release, pilot entry, and audit truth.

The public `AegisOpsControlPlaneService` facade remains the reviewed entrypoint surface for existing callers. Phase 47 coordinator modules are internal decomposition boundaries, not new authority-bearing product surfaces.

Action lifecycle, readiness, evidence, and assistant surfaces remain subordinate to the authoritative AegisOps record chain unless the backend record explicitly binds the context.

Assistant output, optional evidence, downstream receipts, external tickets, browser state, forwarded headers, source substrates, operator-facing summaries, badges, counters, and projections remain subordinate context only.

## 12. Validation Expectations

Validation must remain documentation and boundary focused.

At minimum, validation should prove:

- the Phase 47 boundary and validation docs exist;
- the docs name in-scope, out-of-scope, fail-closed conditions, verifier references, and authority boundary notes;
- action lifecycle write routing stays delegated through the coordinator without changing action lifecycle authority;
- readiness runtime status coordination stays anchored to shared readiness contracts and authoritative readiness facts;
- external evidence coordination stays subordinate to explicit AegisOps evidence linkage;
- assistant advisory coordination remains advisory-only and does not gain authority-bearing methods;
- the maintainability hotspot verifier still records `service.py` as a known reviewed hotspot;
- Phase 49.0 owns the remaining `service.py` and `AegisOpsControlPlaneService` responsibility concentration follow-up; and
- no runtime behavior, authority posture, commercial readiness claim, or completed service decomposition claim is introduced.
