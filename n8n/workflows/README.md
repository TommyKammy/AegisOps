# AegisOps n8n Workflow Category Guidance

This document explains the approved purpose and current boundaries of the tracked n8n workflow categories in AegisOps.

## 1. Purpose

This directory exists to document the approved workflow-category boundaries for AegisOps n8n assets.

The approved workflow categories are alert ingest, enrich, approve, notify, and response.

## 2. Approved Workflow Categories

- `aegisops_alert_ingest` reserves the category for workflows that receive validated findings or alerts into the SOAR layer after detection has already occurred elsewhere.
- `aegisops_enrich` reserves the category for read-oriented context gathering, lookup, and triage support steps that help analysts evaluate an alert.
- `aegisops_approve` reserves the category for explicit approval handling before approval-required actions continue.
- `aegisops_notify` reserves the category for notification, escalation, and operator-routing steps that communicate approved workflow state.
- `aegisops_response` reserves the category for controlled downstream execution after validation and required approvals are complete.

## 3. Placeholder Boundary

Placeholder directories and marker files under `n8n/workflows/` remain non-production placeholders for categories that do not yet contain an explicitly approved exported workflow asset.

The approved Phase 6 exception is limited to `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json`.

Those two exported workflow assets are limited to the selected Windows detector outputs for privileged group membership change, audit log cleared, and new local user created.

Do not infer broader live runtime behavior, integration coverage, or production-ready response logic beyond the approved Phase 6 read-only workflow assets.

## 4. Control vs Execution Alignment

OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution.

This separation preserves the approved control-versus-execution model: alerts are detected in the analytics plane first, then routed into the orchestration plane for reviewable enrichment, approval, notification, and response handling.

The guidance in this directory does not authorize direct destructive actions from raw inbound alerts, hidden write operations inside read-only workflows, or approval bypass by implementation detail.

The approved Phase 6 workflow assets must remain read-only for enrichment and notify-only for analyst routing, without response execution, write-capable connectors, or uncontrolled downstream mutation.

## 5. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline beyond the current Phase 6 read-only workflow assets.

Keep future workflow additions within the approved category boundary and preserve explicit approval gates for write or destructive actions.

When real workflow assets are introduced in later approved work, they should remain auditable, clearly named, and explicit about whether a step is read-only, notify-only, approval-handling, or response-executing.

## 6. Reference Documents

- `docs/architecture.md`
- `docs/requirements-baseline.md`
- `docs/repository-structure-baseline.md`
