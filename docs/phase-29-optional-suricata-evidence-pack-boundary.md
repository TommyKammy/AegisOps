# AegisOps Phase 29 Optional Suricata Evidence-Pack Boundary

## 1. Purpose

This document defines the reviewed optional Suricata evidence-pack boundary for Phase 29.

It supplements `README.md`, `docs/architecture.md`, `docs/canonical-telemetry-schema-baseline.md`, `docs/phase-28-optional-endpoint-evidence-pack-boundary.md`, and `docs/phase-29-reviewed-ml-shadow-mode-boundary.md` by defining the only approved role for Suricata-derived material in the current reviewed design.

This document defines reviewed design scope only. It does not approve network-first product repositioning, mandatory IDS rollout, detection-authority reassignment, case-truth reassignment, approval-surface expansion, execution-surface expansion, or any promotion of network telemetry into the AegisOps mainline authority path.

## 2. Reviewed Optional Suricata Role

Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.

Suricata is approved only as a subordinate evidence-pack and shadow-correlation substrate for this reviewed slice.

Suricata-derived output is optional augmentation, not a mandatory platform dependency or case-truth authority surface.

The reviewed role of this boundary is to let operators preserve bounded network-derived context only when an existing reviewed case chain, evidence gap, or reviewed shadow-mode comparison already justifies collecting it.

Suricata-derived material must remain subordinate to the AegisOps-owned case chain.

Suricata-derived output must not replace AegisOps-owned alert truth, case truth, evidence truth, approval truth, execution truth, or reconciliation truth.

## 3. Enablement Conditions

A reviewed Suricata evidence pack may be used only when an existing operating need or explicit evidence gap is already present on the reviewed case chain.

Suricata collection or parsing must start from an existing AegisOps-owned case, evidence record, or reviewed follow-up decision rather than from free-form network hunting or substrate-first alerting.

Approved triggering conditions for this reviewed path are intentionally narrow:

- a reviewed case already has an explicit host, service, detector, or evidence binding and needs bounded network context to resolve a documented evidence gap;
- a reviewed evidence record already anchors the specific flow, transaction, alert, or protocol artifact for which Suricata-derived context is being requested; or
- a reviewed Phase 29 shadow-mode comparison needs bounded non-authoritative correlation context tied to an already-reviewed subject record.

The path must fail closed when the anchor case or evidence record is missing, the network scope is only implied, the requested flow or observer binding is inferred from weak hints, or the requested intake would widen into general network-first detection coverage.

## 4. Approved Artifact Classes

The approved artifact classes for this boundary are:

- `collection_manifest` for the reviewed description of which bounded Suricata source, observer, time window, and case or evidence anchor were requested;
- `alert_sample` for the explicitly scoped Suricata alert or event material collected under the reviewed anchor;
- `flow_excerpt` for the bounded flow, transaction, or protocol excerpt tied to the reviewed anchor rather than a broad sensor dump;
- `shadow_correlation_note` for subordinate correlation context that may inform Phase 29 shadow-only comparison work without becoming workflow truth; and
- `tool_output_receipt` for the subordinate receipt that records which reviewed Suricata source, parser, or import step produced which artifact and when.

These artifact classes are evidence-pack artifacts only.

They are subordinate evidence that may support reviewed observations, reviewed operator notes, or shadow-only diagnostic context, but they do not become authoritative control-plane lifecycle records on their own.

## 5. Provenance and Citation Requirements

Every Suricata-derived artifact must preserve provenance that identifies the reviewed observer or sensor binding, source family, source event or flow identifier when available, bounded time window, reviewed operator or reviewed automation attribution, and the AegisOps evidence record that admitted it.

Minimum reviewed provenance for this boundary includes:

- the explicitly bound observer, sensor, or reviewed source binding;
- the reviewed case identifier and admitting evidence identifier;
- the reviewed Suricata source, rule, parser, or import tool identity and version when available;
- the collection, parse, or extraction timestamp;
- the reviewed operator or reviewed automation attribution that initiated the step; and
- the reviewed event, flow, transaction, or time-window description needed to explain what was collected.

Suricata-derived artifacts and shadow correlation notes must be cited as subordinate evidence linked to an AegisOps-owned evidence record.

Citation must preserve whether the cited material is raw collected output, a bounded derivative, or an operator-authored interpretation.

The case chain must not cite Suricata-derived output as if it decided case scope, actor identity, approval state, execution state, or reconciliation success.

## 6. Boundary Notes for Phase 29 Shadow Mode

Suricata-derived material may inform Phase 29 only as reviewed subordinate context or evidence-pack material consistent with the reviewed ML shadow-mode contract.

Any Suricata-derived feature, note, or correlation signal must preserve explicit provenance and remain advisory-only.

Suricata-derived output must not widen feature scope beyond the anchored reviewed record, must not become an authoritative label source, and must not silently promote network telemetry into mainline workflow truth.

If a reviewed Phase 29 path cannot preserve explicit linkage from the anchored reviewed record to the Suricata-derived artifact, the Suricata path must remain blocked.

## 7. Non-Goals and Fail-Closed Rules

This boundary does not approve network-first mainline detection, broad IDS-led workflow redesign, mandatory Suricata deployment, or substrate authority expansion.

This boundary also does not approve:

- making Suricata a required mainline dependency for first boot, routine case handling, or reviewed ML shadow-mode operation;
- treating Suricata alert streams, flow logs, signatures, classifications, or metadata as authoritative alert, case, approval, execution, or reconciliation truth;
- widening from a reviewed anchor into broad sensor sweeps, generalized threat hunting, or passive backlog mining;
- allowing Suricata rule names, signatures, classifications, or parser convenience fields to become workflow truth by convenience; or
- using subordinate network telemetry to bypass reviewed evidence linkage, approval controls, or explicit reconciliation checks.

The path must fail closed when provenance is partial, the observer or subject scope is only inferred, the requested artifact class falls outside this reviewed slice, the boundary is enabled without an explicit reviewed need, or a citation would overstate what the subordinate network telemetry actually proved.

## 8. Repository-Local Verification Commands

The repository-local verification commands for this boundary are:

- `python3 -m unittest control-plane.tests.test_phase29_suricata_evidence_pack_boundary_validation`
- `bash scripts/verify-phase-29-suricata-evidence-pack-boundary.sh`
