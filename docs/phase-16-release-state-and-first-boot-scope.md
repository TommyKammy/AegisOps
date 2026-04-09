# AegisOps Phase 16 Release-State and First-Boot Scope

## 1. Purpose

This document defines the approved Phase 16 release-state and first-boot scope for bootable AegisOps.

It supplements `docs/control-plane-runtime-service-boundary.md`, `docs/architecture.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `README.md` by narrowing Phase 16 to the minimum runtime shape that is allowed to count as the first bootable AegisOps release-state before Phase 17 runtime bring-up expands implementation detail.

This document defines release-state and review scope only. It does not approve concrete containerization, live Wazuh integration wiring, analyst UI implementation, or broad runtime expansion beyond the first-boot boundary described here.

## 2. Approved Phase 16 Release-State

The approved Phase 16 release-state is a repository baseline that is ready to enter Phase 17 runtime bring-up with one narrow bootability target.

That target is a bootable first-boot runtime composed of:

- the AegisOps control-plane service as the authoritative runtime boundary;
- PostgreSQL as the AegisOps-owned persistence dependency for control-plane state;
- the approved reverse proxy access boundary for controlled ingress; and
- reviewed Wazuh-facing runtime expectations for upstream analytic-signal intake.

Phase 16 release-state means those components are the required bootability floor.

It does not mean every adjacent substrate tracked in the repository must boot on day one, and it does not redefine optional repository assets as mandatory first-boot dependencies.

## 3. First-Boot In-Scope Runtime Components

The first bootable AegisOps runtime includes the following in-scope components:

- a live AegisOps control-plane service rooted under `control-plane/`;
- the reviewed PostgreSQL boundary for AegisOps-owned control-plane records;
- the approved reverse proxy path for controlled user-facing ingress and administrative exposure control; and
- reviewed runtime expectations that the control-plane service can accept Wazuh-originated analytic-signal inputs without requiring Wazuh to become the authority for downstream alert, case, approval, or reconciliation truth.

The first-boot scope is intentionally narrow.

It is limited to the minimum runtime needed to prove that AegisOps can boot around its own control-plane authority boundary instead of around optional analytics, optional orchestration, or future user-interface surfaces.

## 4. First-Boot Explicitly Out of Scope

The following items are explicitly out of scope for the Phase 16 first-boot release-state:

- optional OpenSearch extension runtime or OpenSearch-dependent first-boot success criteria;
- n8n as a required first-boot dependency or orchestration prerequisite;
- the full interactive analyst-assistant surface;
- the high-risk executor path or write-capable response execution; and
- broad source coverage beyond the narrow Wazuh-facing runtime expectation required for first boot.

These areas may remain repository-tracked, designed, or deferred, but they must not silently become blockers for the first bootable runtime target.

## 5. Phase 16 Definition of Done

Phase 16 is done when the repository baseline unambiguously states that:

- first boot requires the AegisOps control-plane service, PostgreSQL, and the approved reverse proxy boundary;
- Wazuh-facing runtime expectations are limited to reviewed upstream analytic-signal intake expectations rather than live end-to-end substrate wiring;
- OpenSearch, n8n, the full analyst-assistant surface, the high-risk executor, and broad source expansion remain optional, deferred, or non-blocking for first boot; and
- later phases can use this document as the bootability target for Phase 17 runtime bring-up without reopening what counts as the minimum first-boot runtime.

Phase 16 therefore ends with an approved bootability target, not with a claim that the full platform is feature-complete.

## 6. Boundary and Alignment Notes

`docs/control-plane-runtime-service-boundary.md` remains the normative source for the live control-plane ownership split and repository placement.

`docs/architecture.md` remains the normative source for the separation between detection, control, automation, and execution.

`docs/network-exposure-and-access-path-policy.md` remains the normative source for the reverse proxy and internal exposure rules that first boot must preserve.

`docs/storage-layout-and-mount-policy.md` remains the normative source for persistent storage separation, including the distinction between PostgreSQL-owned state and optional substrate-local data.

`README.md` remains aligned with this Phase 16 release-state by keeping OpenSearch and n8n optional and by keeping the control-plane runtime as the product authority boundary.
