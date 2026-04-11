# AegisOps Phase 19 Thin Operator Surface and First Daily Analyst Workflow

## 1. Purpose

This document defines the approved Phase 19 thin operator surface and first daily analyst workflow for the first live Wazuh-backed operator slice.

It supplements `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md`, and `docs/architecture.md`.

This document defines the approved operator-facing surface shape and workflow scope only. It does not approve broader dashboarding, full interactive assistant behavior, broad source-family coverage, or medium-risk or high-risk live action wiring.

## 2. Approved Phase 19 Thin Operator Surface

The approved operator surface is thin, review-oriented, and anchored to the completed Phase 18 live ingest path.

AegisOps remains the primary daily work surface for the approved first live slice.

The approved surface is limited to the first Wazuh-backed and GitHub audit-backed review path inside AegisOps rather than a broad SOC dashboard.

The approved surface must preserve AegisOps as the authority for alert, case, evidence, recommendation, approval, action intent, and reconciliation truth.

### 2.1 Approved Operator Reads

The analyst may read:

- daily queue review data from the read-only analyst queue view for the reviewed `analyst_review` queue and `business_hours_triage` selection;
- alert, case, and reconciliation detail linked to the selected queue item;
- read-only evidence access through linked evidence identifiers, evidence records, native rule context, source identity, and reviewed context; and
- cited advisory review through the approved assistant-context path that renders from reviewed control-plane records and linked evidence.

The approved read path is intentionally narrow and must stay grounded in reviewed control-plane records created from the reviewed Phase 18 live Wazuh-backed intake boundary.

The approved read path must not depend on OpenSearch runtime enrichment, external dashboard pivots, or direct substrate-console truth to complete the first daily workflow.

### 2.2 Approved Bounded Analyst Actions

The approved Phase 19 bounded analyst actions are:

- select a queue item from the reviewed analyst queue;
- inspect alert, case, reconciliation, and evidence detail inside AegisOps;
- promote an alert to a case when review requires tracked casework;
- enter or update AegisOps-owned casework entry as reviewed notes, observations, findings, or recommendation drafts that stay cited to reviewed records and evidence; and
- request a cited advisory review from the approved read-only assistant-context snapshot path.

Bounded analyst actions must stay inside AegisOps-owned control-plane records and must remain reviewable, attributable, and reversible through normal record history.

Bounded analyst actions must not mutate upstream Wazuh records, call direct GitHub APIs, trigger broad automation, or bypass approval and reconciliation controls.

## 3. First Daily Analyst Workflow

The approved first daily workflow is:

`daily queue review -> alert inspection -> casework entry -> evidence review -> cited advisory review`

This workflow is the minimum daily analyst path that keeps AegisOps as the primary reviewed operator surface for the first live slice without reopening broader UI or runtime scope.

### 3.1 Daily Queue Review

Daily queue review begins in the read-only analyst queue populated by the reviewed Phase 18 live Wazuh-backed intake path.

The queue record must show enough context for a first decision without leaving AegisOps, including alert identifier, case linkage, review state, source family, accountable source identity, correlation key, native rule summary, and first-seen and last-seen timing.

The approved queue path is review-only. It is not a broad dashboarding surface and does not authorize arbitrary queue management or substrate-side state mutation.

### 3.2 Alert Inspection

Alert inspection means the analyst can open the selected queue item and review the linked alert truth, reconciliation state, reviewed context, and source lineage that explain why the record is on the queue.

For the first live slice, alert inspection is limited to Wazuh-backed GitHub audit records admitted through the reviewed reverse-proxy path and stored as AegisOps-owned records.

The operator may inspect repeat sightings, deduplicated or restated lineage, case linkage, and reconciliation metadata without treating Wazuh, OpenSearch, or GitHub as the authority for the operational record.

### 3.3 Casework Entry

Casework entry begins only after the analyst has inspected the queue item and decided the work should be tracked as a case inside AegisOps.

The approved Phase 19 casework entry scope is bounded to AegisOps-owned case state, cited notes, observations, finding updates, and recommendation drafts that preserve links back to the reviewed alert, case, reconciliation, and evidence set.

Casework entry must stay narrow enough that an analyst can record reviewed work progress and decision support inside AegisOps without needing a broader collaborative workspace or automation surface.

### 3.4 Evidence Review

Evidence review means the analyst can inspect linked evidence records, preserved raw Wazuh payload context, accountable source identity, native rule provenance, and any cited record linkage already attached to the alert or case.

Read-only evidence access must preserve provenance and must not permit destructive evidence editing, silent evidence replacement, or substrate-local overwrite of the reviewed control-plane record set.

Evidence review must keep cited lineage visible enough that the analyst can explain why a claim or casework entry is supported without leaving the approved first live slice.

### 3.5 Cited Advisory Review

Cited advisory review is the only approved assistant-facing path in Phase 19.

The approved cited advisory review path is a bounded read-only review of assistant-context snapshots, cited summaries, case summaries, and recommendation drafts that are anchored to reviewed control-plane records and linked evidence.

Phase 19 cited advisory review must stay citation-first, uncertainty-preserving, and advisory-only as already required by the Phase 15 assistant boundary and operating guidance.

Phase 19 does not approve free-form operator chat, autonomous assistant behavior, or any assistant path that can create approval, execution, or reconciliation authority.

## 4. Deferred Beyond Phase 19

The following remain deferred beyond Phase 19:

- broader dashboarding or general SOC workspace expansion;
- full interactive assistant behavior or free-form assistant chat surfaces;
- broader automation breadth beyond cited recommendation review;
- direct substrate-side mutation from the operator surface;
- low-risk live response execution from the daily analyst surface;
- medium-risk or high-risk live action wiring;
- broader source-family rollout beyond the approved Phase 18 GitHub audit first live family; and
- UI polish or broader visual design work that is not required to keep the thin operator path explicit.

## 5. Alignment and Non-Expansion Rules

This Phase 19 surface is aligned to Phase 18 by assuming the approved Wazuh-backed GitHub audit live path already exists and by not reopening live ingest, topology, or source-admission scope.

`docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md` remains the normative source for the approved live-path topology, GitHub audit first live family, and fail-closed intake contract.

`docs/phase-17-runtime-config-contract-and-boot-command-expectations.md` and `docs/phase-16-release-state-and-first-boot-scope.md` remain the normative source for the narrow first-boot runtime floor that this thin operator surface must not broaden.

`docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md` remains the normative source for how cited advisory review stays advisory-only, citation-first, and grounded in reviewed control-plane records and linked evidence.

`docs/architecture.md` remains the normative source for the rule that AegisOps owns the policy-sensitive workflow truth and that detection or automation substrates must not become the operator authority surface.
