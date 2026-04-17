# Revised Phase 23-20 Epic Roadmap

## 1. Purpose

This roadmap revision anchors the next hardening and ergonomics work to the approved AegisOps control-plane thesis and deployment target.

It exists to keep Phase 23 planning aligned with the reviewed SMB operating model rather than drifting toward broad enterprise repositioning, generic SIEM replacement language, or multi-tenant packaging.

## 2. Product Thesis

AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

It sits above reviewed detection and automation substrates so analysts and approvers can preserve authoritative workflow truth without asking those substrates to become the durable authority for approvals, evidence custody, or reconciliation outcomes.

The positive value proposition is not broad source breadth or broad autonomous response. The value proposition is trustworthy governance over the narrow set of actions, records, and handoffs that a small SecOps team must actually review.

## 3. Primary Deployment Target Profile

The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners.

The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC.

The intended deployment shape remains a narrow on-premise control-plane environment where later footprint, reliability, and ergonomics decisions can be judged against one concrete operator model instead of vague enterprise aspirations.

## 4. Roadmap Guardrails

Phase 23 hardening and ergonomics work must be evaluated against this deployment target before scope expands.

That means later work should prefer:

- stronger approval handling, evidence quality, and reconciliation visibility for the reviewed daily path;
- clearer operator ergonomics for small business-hours teams;
- reliability and recovery work sized for the approved SMB footprint; and
- narrow source and action growth that preserves the reviewed authority boundary.

That means later work should avoid:

- broad enterprise-market repositioning;
- generic SIEM replacement claims;
- multi-tenant packaging; and
- scope growth that assumes 24x7 staffed operations by default.

## 5. Alignment Notes

`README.md` should describe AegisOps positively as the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

`docs/architecture.md` should carry the same product thesis and deployment target so component-boundary decisions stay anchored to the same audience and operating assumptions.

`docs/smb-footprint-and-deployment-profile-baseline.md` should publish the concrete reviewed footprint, backup, restore, and operator-burden expectations that keep later hardening and ergonomics work honest for the approved SMB target.

Future roadmap slices should treat this document as the control statement for who AegisOps is for before they add new hardening, ergonomics, or source-expansion work.
