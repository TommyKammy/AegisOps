# SMB Footprint and Deployment-Profile Baseline

## 1. Purpose

This baseline publishes the reviewed SMB deployment profiles that future footprint, reliability, and operator-experience work must target.

Use this baseline to replace intuition-only sizing discussions with a concrete, reviewable deployment floor and ceiling for the approved Phase 27 operating model.

This document is a planning and review artifact. It does not authorize new runtime dependencies, high-availability topology changes, or live deployment commands.

## 2. Scope and Decision Rule

Use this baseline to judge whether AegisOps remains operable for the approved small-team deployment target before later work adds substrate, reliability, or ergonomics scope.

A profile is acceptable only if it preserves the positive SMB value proposition and remains realistic for a small business-hours SecOps team to operate.

The decision rule is practical: if a proposed change requires materially more infrastructure, more frequent operator touch, or more recovery complexity than the reviewed profiles below can tolerate, that change needs explicit re-review before it becomes part of the baseline.

## 3. Reviewed Deployment Profiles

### 3.1 Lab Profile

The lab profile is the minimum reviewable footprint for first-boot exercises, restore rehearsal, and operator training.

It is intended for a single internal environment where reviewers can validate startup, backup, restore, and daily-path ergonomics without assuming full production telemetry breadth or nonstop staffing.

### 3.2 Single-Customer Profile

The single-customer profile is the default reviewed deployment shape for one customer environment with explicit operator ownership and no implied multi-tenant fleet posture.

This profile assumes the environment is still narrow, business-hours oriented, and governed by explicit approvals, but it must tolerate a steadier daily operational rhythm than the lab profile.

### 3.3 Small-Production SMB Operation Profile

The small-production SMB operation profile is the maximum reviewed baseline for Phase 27 roadmap decisions.

It represents a serious SMB deployment with enough scale to justify disciplined backup, restore, and operator workflows, while still staying inside the approved narrow-team and narrow-footprint product thesis.

## 4. Baseline Expectations by Profile

The table below is the reviewed planning baseline for whole-environment sizing. It is deliberately conservative enough to keep recovery and operator load honest, but narrow enough to avoid drifting into enterprise-cluster assumptions.

| Profile | Managed endpoints | vCPU | Memory | Primary storage | Backup expectation | Restore expectation | Upgrade and rollback expectation | Health and operator cadence | Identity and secret-management expectation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lab | 250 to 500 | 8 to 10 | 24 to 32 GB | 400 to 600 GB usable persistent storage | Daily PostgreSQL-aware backup, configuration backup after reviewed changes, and a named operator responsible for verifying the backup job outcome | At least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery | Reviewed upgrades fit one business-hours maintenance window and rollback returns to the prior known-good backup without extra platform staff or high-availability failover machinery | Startup, queue, backup, and reverse-proxy health reviewed at least three times per week during business hours, with one operator capturing the readiness result | One named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list are sufficient for the lab path |
| Single-customer | 500 to 1,000 | 12 to 16 | 40 to 56 GB | 0.8 to 1.5 TB usable persistent storage | Daily PostgreSQL-aware backup, weekly backup review, and reviewed configuration backup before platform changes that affect customer operations | Monthly restore rehearsal against a reviewed single-customer recovery target, including validation that customer-scoped workflow truth and linked evidence return cleanly | Reviewed upgrades fit one planned maintenance window per month and rollback remains operator-led without cluster failover tooling or multi-customer coordination assumptions | Daily queue and health review on business days plus weekly platform hygiene review for certificates, storage growth, and backup drift | Named customer-scoped approver ownership, a reviewed secret rotation checklist, and explicit break-glass custody for customer credentials are required |
| Small-production SMB operation | 1,000 to 1,500 | 16 to 24 | 56 to 96 GB | 1.5 to 3 TB usable persistent storage | Daily PostgreSQL-aware backup, weekly backup review, and pre-change configuration backup with documented custody | Monthly restore rehearsal with documented recovery timing, clean-state validation, and reconciliation checks before normal operations resume | Reviewed upgrades require a documented change plan, same-day rollback readiness, and no dependence on enterprise-only deployment tooling, dedicated database teams, or multi-region failover | Daily queue and platform health review on business days plus weekly drift, storage-growth, and capacity review by the named operator team | Two-person ownership coverage for approver and secret custody, scheduled rotation checkpoints, and documented break-glass audit follow-up are required |

CPU and memory expectations must be read as whole-environment planning guidance for the approved control-plane footprint, not as per-container reservations.

Primary storage assumptions include PostgreSQL state, approved configuration artifacts, logs required for the reviewed control-plane path, and reasonable growth headroom for replay and audit readiness. They do not authorize large analytics clusters or indefinite retention expansion.

Backup expectations must include PostgreSQL-aware backups, configuration backup, and a restore rehearsal expectation rather than relying on hypervisor snapshots alone.

Restore expectations assume operators are recovering a narrow, reviewed control-plane environment and validating that the approval, evidence, execution, and reconciliation record chain is intact before normal operations resume.

## 5. Capacity Budget Guardrails

Each reviewed profile must publish explicit budget assumptions for backup, restore, upgrade, rollback, health review, identity administration, and secret management rather than leaving Phase 27 day-2 hardening work to infer them later.

Upgrade and rollback expectations must stay narrow enough that one small business-hours operator team can complete a reviewed platform change and, if needed, return to the prior known-good state without enterprise-only tooling.

Health expectations must state the minimum operator review cadence that later readiness, drift, and alert-handling work can assume.

Identity and secret-management expectations must keep named approver ownership, secret rotation touch points, and break-glass handling inside the reviewed SMB operating posture.

## 6. Operational Burden Baseline

Operator-overhead expectations are part of the footprint baseline because a deployment that fits on paper but requires enterprise-style staffing is out of scope.

The approved small-team operating assumption remains 2 to 6 business-hours SecOps operators with 1 to 3 designated approvers or escalation owners.

For this baseline, operator overhead includes:

- daily queue and alert review for the approved control-plane path;
- explicit approval handling for reviewed write-capable actions;
- backup review and restore-readiness checks;
- narrow platform hygiene work such as cert rotation, reviewed configuration updates, and health validation; and
- after-hours escalation coordination rather than continuous overnight staffing.

Any future design that assumes a dedicated database team, a full-time platform SRE rotation, or 24x7 analyst staffing is no longer targeting the reviewed SMB footprint.

## 7. Alignment to Phase 27 Day-2 Hardening

Phase 27 day-2 hardening work must stay inside these reviewed profiles unless a later ADR approves a new target footprint.

Later upgrade, rollback, health, identity, and secret-management work must target one of these reviewed profiles rather than inventing a broader operating posture by implication.

This baseline supports the product thesis that AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

It keeps later reliability and substrate decisions anchored to the same question: does this change make the reviewed daily path more trustworthy for a small team, or does it quietly convert AegisOps into an enterprise-overbuilt platform that no longer matches the intended audience.

The baseline therefore favors:

- reliable backup and restore over HA overbuild;
- operator-visible recovery and reconciliation over opaque automation complexity;
- incremental hardening for one reviewed deployment target over broad market repositioning; and
- clear business-hours operational expectations over implied 24x7 staffing.

## 8. Explicitly Out of Scope

High-availability overbuild, large-cluster sizing, and generic enterprise capacity planning are explicitly out of scope for this baseline.

Also out of scope are multi-tenant packaging assumptions, MSSP fleet-wide aggregation sizing, unlimited telemetry-retention planning, and environment-specific benchmark claims that are not yet backed by reviewed runtime measurements.
