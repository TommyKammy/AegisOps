# AegisOps Phase 28 Optional Endpoint Evidence-Pack Boundary

## 1. Purpose

This document defines the reviewed optional endpoint evidence-pack boundary for Phase 28.

It supplements `docs/requirements-baseline.md`, `docs/architecture.md`, `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, and `docs/phase-25-multi-source-case-review-and-osquery-evidence-runbook.md` by defining when endpoint-collected artifacts may augment case evidence without turning endpoint tooling into mainline case truth, approval authority, or mandatory infrastructure.

This document defines reviewed design scope only. It does not approve mandatory endpoint-agent rollout, broad endpoint-first product positioning, autonomous collection, free-form hunting, or any expansion of endpoint-tool authority beyond a subordinate evidence-pack role.

## 2. Reviewed Optional Endpoint Evidence-Pack Role

Endpoint evidence packs are optional augmentation, not a mandatory platform dependency or case-truth authority surface.

Velociraptor is approved only as a subordinate read and evidence-collection substrate for this slice.

YARA and capa are approved only as subordinate evidence-pack analysis tools for collected files or binaries inside this same boundary.

The reviewed role of this boundary is to let operators collect bounded endpoint artifacts when an existing case already needs additional host, file, or binary context that upstream analytic signals and already-admitted evidence do not provide.

Endpoint evidence tooling must remain subordinate to the AegisOps-owned case chain.

Endpoint evidence packs must not replace AegisOps-owned case truth, actor truth, approval truth, or reconciliation truth.

## 3. Enablement Conditions

A reviewed endpoint evidence pack may be used only when an existing operating need or explicit evidence gap is already present on the reviewed case chain.

Endpoint evidence collection must start from an existing AegisOps-owned case, evidence record, or reviewed follow-up decision rather than from free-form endpoint hunting.

Approved triggering conditions for this reviewed path are intentionally narrow:

- a case already has an explicit host binding and needs additional endpoint-local state to resolve an evidence gap;
- a reviewed file, process, or binary artifact already on the case chain requires bounded collection for preservation or deeper inspection; or
- a reviewed operator decision records why upstream analytic signals or already-admitted augmenting evidence are insufficient for the next case-review step.

The path must fail closed when the host binding is missing, the evidence gap is only implied, the collection target is inferred from weak hints, or the requested collection would widen beyond the reviewed case scope.

## 4. Approved Artifact Classes

The approved artifact classes for this boundary are:

- `collection_manifest` for the reviewed description of what was requested, from which explicitly bound host, by which reviewed operator, and under which case or evidence anchor;
- `triage_bundle` for bounded read-only host-state output such as reviewed process, service, autorun, user, scheduled-task, or network-observation snapshots tied to the scoped host;
- `file_sample` for a reviewed collected file or bounded file subset taken from the scoped host or evidence path;
- `binary_analysis` for derived YARA or capa findings over a reviewed collected file or binary sample; and
- `tool_output_receipt` for the subordinate receipt that records which reviewed collector or analysis tool produced which artifact and when.

These artifact classes are evidence-pack artifacts only.

They are subordinate evidence that may support reviewed observations, operator notes, or later recommendations, but they do not become authoritative control-plane lifecycle records on their own.

## 5. Provenance and Citation Requirements

Every collected or derived artifact must preserve provenance that identifies the source host binding, collector or tool identity, collection or analysis time, reviewed operator attribution, and the AegisOps evidence record that admitted it.

Minimum reviewed provenance for this boundary includes:

- the explicitly bound host identifier or reviewed binary source reference;
- the reviewed case identifier and admitting evidence identifier;
- the reviewed collection or analysis tool name and version when available;
- the collection or analysis timestamp;
- the reviewed operator or reviewed automation attribution that initiated the step; and
- the reviewed path or query description needed to explain what was collected or analyzed.

Collected endpoint artifacts and derived YARA or capa outputs must be cited as subordinate evidence linked to an AegisOps-owned evidence record.

Citation must preserve whether the cited material is raw collected output, a bounded derivative, or an operator-authored interpretation.

The case chain must not cite Velociraptor, YARA, or capa output as if those tools decided case scope, actor identity, approval state, or remediation success.

## 6. Tool-Specific Boundary Notes

Velociraptor remains a read and evidence substrate only for this reviewed slice.

Its reviewed role is bounded collection and preservation of subordinate endpoint evidence packs tied to an already-scoped case or evidence anchor.

Velociraptor is not approved here as a case-led investigation console, fleet-wide hunting authority, approval surface, or workflow owner.

YARA and capa remain subordinate evidence-analysis tools rather than authority surfaces.

They may analyze a reviewed collected file or binary sample and produce derivative findings that stay attached to the admitting evidence record.

YARA or capa findings may support a reviewed observation or operator explanation, but they must not silently promote a file, host, or actor into stronger case truth without an explicit reviewed control-plane link.

## 7. Non-Goals and Fail-Closed Rules

This boundary does not approve mandatory agent rollout, endpoint-first product repositioning, background fleet sweeps, autonomous collection, or endpoint-tool authority expansion.

This boundary also does not approve:

- making Velociraptor, YARA, or capa a required mainline dependency for first boot or routine case handling;
- treating endpoint evidence packs as a substitute for upstream analytic-signal intake or reviewed case admission;
- broad collection from hosts that are not already bound explicitly on the reviewed case chain;
- allowing endpoint-tool UI state, tags, labels, or collection history to become case truth by convenience; or
- using derived endpoint findings to bypass approval, execution, or reconciliation controls.

The path must fail closed when provenance is partial, the host or binary scope is only inferred, a requested artifact class falls outside this reviewed slice, or a citation would overstate what the subordinate tool output actually proved.

## 8. Repository-Local Verification Commands

The repository-local verification commands for this boundary are:

- `python3 -m unittest control-plane.tests.test_phase28_endpoint_evidence_pack_boundary_docs`
- `bash scripts/verify-phase-28-endpoint-evidence-pack-boundary.sh`
