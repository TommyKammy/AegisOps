#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-sigma-n8n-skeleton-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

create_sigma_and_n8n_skeleton() {
  local target="$1"

  mkdir -p \
    "${target}/sigma/curated/windows-security-and-endpoint" \
    "${target}/sigma/suppressed" \
    "${target}/n8n/workflows/aegisops_alert_ingest" \
    "${target}/n8n/workflows/aegisops_approve" \
    "${target}/n8n/workflows/aegisops_enrich" \
    "${target}/n8n/workflows/aegisops_notify" \
    "${target}/n8n/workflows/aegisops_response" \
    "${target}/docs"

  cat <<'EOF' > "${target}/sigma/curated/README.md"
# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding.

Status: candidate Windows security and endpoint rules for the selected Phase 6 use cases only.

Scope: privileged group membership change, audit log cleared, and new local user created.

These rules stay within the approved single-event Sigma subset and remain review content only.
EOF

  cat <<'EOF' > "${target}/sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml"
title: AegisOps Windows Privileged Group Membership Change
id: 2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81
status: candidate
description: Reviewed candidate rule for the initial Windows Phase 6 use case.
owner: IT Operations, Information Systems Department
purpose: Detect a reviewed Windows event where a user is added to a privileged local or domain group.
expected_behavior: Create a reviewable finding when reviewed Windows telemetry records a membership change into a privileged group.
severity: high
level: high
required_reviewer: Security Engineering reviewer
expiry: 2026-07-01
source_of_truth: sigma
validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#privileged-group-membership-change
rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable.
tags:
  - attack.persistence
  - attack.privilege-escalation
  - attack.t1098
logsource:
  product: windows
  service: security
field_semantics:
  match_required:
    - event.dataset
    - event.code
    - group.name
  triage_required:
    - user.name
    - destination.user.name
  activation_gating:
    - Windows security and endpoint telemetry family remains detection-ready for authoritative actor and target identity under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  confidence_degrading:
    - Missing actor identity degrades attribution confidence and blocks promotion beyond staging review for actor-dependent use.
source_prerequisites:
  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  - Staging translation review is allowed only while the reviewed success-path fixtures preserve event.dataset, event.code, group.name, user.name, and destination.user.name.
false_positive_considerations:
  - Approved administrative group changes by endpoint engineering, identity administrators, or build automation can legitimately match.
detection:
  selection:
    event.dataset: windows.security
    event.code:
      - '4728'
      - '4732'
      - '4756'
    group.name:
      - Administrators
      - Domain Admins
      - Enterprise Admins
  condition: selection
EOF

  cat <<'EOF' > "${target}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"
title: AegisOps Windows Audit Log Cleared
id: 4f5b2a71-91d4-4d75-85a1-c0fc12276fea
status: candidate
description: Reviewed candidate rule for the initial Windows Phase 6 use case.
owner: IT Operations, Information Systems Department
purpose: Detect a reviewed Windows event that records clearing of the Windows audit log.
expected_behavior: Create a reviewable finding when reviewed Windows telemetry records audit-log-cleared activity.
severity: high
level: high
required_reviewer: Security Engineering reviewer
expiry: 2026-07-01
source_of_truth: sigma
validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#audit-log-cleared
rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable.
tags:
  - attack.defense-evasion
  - attack.t1070.001
logsource:
  product: windows
  service: security
field_semantics:
  match_required:
    - event.dataset
    - event.code
    - event.action
  triage_required:
    - host.name
    - user.name
  activation_gating:
    - Windows security and endpoint telemetry family remains detection-ready for authoritative host and actor identity under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  confidence_degrading:
    - Missing actor identity degrades attribution confidence and blocks promotion beyond staging review for actor-dependent use.
source_prerequisites:
  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  - Staging translation review is allowed only while the reviewed success-path fixtures preserve event.dataset, event.code, event.action, host.name, and user.name.
false_positive_considerations:
  - Approved maintenance, forensic review, or controlled break-glass procedures can legitimately clear audit logs.
detection:
  selection:
    event.dataset: windows.security
    event.code: '1102'
    event.action: audit-log-cleared
  condition: selection
EOF

  cat <<'EOF' > "${target}/sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"
title: AegisOps Windows New Local User Created
id: 91c9f67d-76f5-41f1-9ccf-66942a33df4f
status: candidate
description: Reviewed candidate rule for the initial Windows Phase 6 use case.
owner: IT Operations, Information Systems Department
purpose: Detect a reviewed Windows event where a new local user account is created on a managed host.
expected_behavior: Create a reviewable finding when reviewed Windows telemetry records local account creation.
severity: medium
level: medium
required_reviewer: Security Engineering reviewer
expiry: 2026-07-01
source_of_truth: sigma
validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#new-local-user-created
rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable.
tags:
  - attack.persistence
  - attack.t1136.001
logsource:
  product: windows
  service: security
field_semantics:
  match_required:
    - event.dataset
    - event.code
    - event.action
  triage_required:
    - host.name
    - user.name
    - destination.user.name
  activation_gating:
    - Windows security and endpoint telemetry family remains detection-ready for authoritative host, actor, and target identity under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  confidence_degrading:
    - Missing actor identity degrades attribution confidence and blocks promotion beyond staging review for actor-dependent use.
source_prerequisites:
  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  - Staging translation review is allowed only while the reviewed success-path fixtures preserve event.dataset, event.code, event.action, host.name, user.name, and destination.user.name.
false_positive_considerations:
  - Approved help desk provisioning, imaging workflows, or temporary break-glass account creation can legitimately match.
detection:
  selection:
    event.dataset: windows.security
    event.code: '4720'
    event.action: local-user-created
  condition: selection
EOF

  cat <<'EOF' > "${target}/sigma/suppressed/README.md"
# Sigma Suppressed Directory

Purpose: approved home for future Sigma suppression decisions that have been reviewed and documented.

Status: placeholder only; no active Sigma suppression rules, exceptions, or decisions are committed here yet.

This directory reserves the approved location for future documented suppression entries after review.

Any future suppression entry must include documented justification, review, and approval before real content is added.
EOF

  cat <<'EOF' > "${target}/n8n/workflows/README.md"
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

Do not infer broader live runtime behavior, integration coverage, or production-ready response logic beyond the approved Phase 6 read-only workflow assets.

## 4. Control vs Execution Alignment

OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution.

This separation preserves the approved control-versus-execution model: alerts are detected in the analytics plane first, then routed into the orchestration plane for reviewable enrichment, approval, notification, and response handling.

The guidance in this directory does not authorize direct destructive actions from raw inbound alerts, hidden write operations inside read-only workflows, or approval bypass by implementation detail.

## 5. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline beyond the current Phase 6 read-only workflow assets.

Keep future workflow additions within the approved category boundary and preserve explicit approval gates for write or destructive actions.

The approved Phase 6 workflow assets must remain read-only for enrichment and notify-only for analyst routing, without response execution, write-capable connectors, or uncontrolled downstream mutation.

When real workflow assets are introduced in later approved work, they should remain auditable, clearly named, and explicit about whether a step is read-only, notify-only, approval-handling, or response-executing.

## 6. Reference Documents

- `docs/architecture.md`
- `docs/requirements-baseline.md`
- `docs/repository-structure-baseline.md`
EOF

  : > "${target}/n8n/workflows/aegisops_alert_ingest/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_approve/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_enrich/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_notify/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_response/.gitkeep"

  cat <<'EOF' > "${target}/n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json"
{
  "name": "aegisops_enrich_windows_selected_detector_outputs",
  "nodes": [
    {
      "parameters": {},
      "name": "Phase 6 Read-only Boundary",
      "type": "n8n-nodes-base.stickyNote"
    },
    {
      "parameters": {},
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger"
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "selected_detector_outputs",
              "value": "privileged_group_membership_change,audit_log_cleared,new_local_user_created",
              "type": "string"
            },
            {
              "name": "read_only_boundary",
              "value": "true",
              "type": "string"
            },
            {
              "name": "notification_handoff_required",
              "value": "true",
              "type": "string"
            }
          ]
        }
      },
      "name": "Normalize Selected Detector Output",
      "type": "n8n-nodes-base.set"
    },
    {
      "parameters": {
        "rules": {
          "values": [
            {
              "value": "privileged_group_membership_change"
            },
            {
              "value": "audit_log_cleared"
            },
            {
              "value": "new_local_user_created"
            }
          ]
        }
      },
      "name": "Route Selected Detector Output",
      "type": "n8n-nodes-base.switch"
    }
  ],
  "tags": [
    {
      "name": "read_only"
    },
    {
      "name": "phase_6"
    }
  ]
}
EOF

  cat <<'EOF' > "${target}/n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json"
{
  "name": "aegisops_notify_windows_selected_detector_outputs",
  "nodes": [
    {
      "parameters": {},
      "name": "Notify-only Boundary",
      "type": "n8n-nodes-base.stickyNote"
    },
    {
      "parameters": {},
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger"
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "selected_detector_outputs",
              "value": "privileged_group_membership_change,audit_log_cleared,new_local_user_created",
              "type": "string"
            },
            {
              "name": "notify_only_boundary",
              "value": "true",
              "type": "string"
            },
            {
              "name": "downstream_mutation_allowed",
              "value": "false",
              "type": "string"
            }
          ]
        }
      },
      "name": "Format Analyst Notification",
      "type": "n8n-nodes-base.set"
    }
  ],
  "tags": [
    {
      "name": "notify_only"
    },
    {
      "name": "phase_6"
    }
  ]
}
EOF
}

write_validation_doc() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/sigma-n8n-skeleton-validation.md"
# Sigma and n8n Skeleton Asset Validation

- Validation date: 2026-04-03
- Baseline references: `docs/requirements-baseline.md`, `docs/repository-structure-baseline.md`, `sigma/README.md`, `n8n/workflows/README.md`
- Verification commands: `bash scripts/verify-sigma-guidance-doc.sh`, `bash scripts/verify-sigma-curated-skeleton.sh`, `bash scripts/verify-sigma-suppressed-skeleton.sh`, `bash scripts/verify-n8n-workflow-category-guidance.sh`, `bash scripts/verify-n8n-workflow-skeleton.sh`, `bash scripts/verify-sigma-n8n-skeleton-validation.sh`
- Validation status: PASS

## Reviewed Artifacts

- `sigma/README.md`
- `sigma/curated/README.md`
- `sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml`
- `sigma/curated/windows-security-and-endpoint/new-local-user-created.yml`
- `sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml`
- `sigma/suppressed/README.md`
- `n8n/workflows/README.md`
- `n8n/workflows/aegisops_alert_ingest/.gitkeep`
- `n8n/workflows/aegisops_approve/.gitkeep`
- `n8n/workflows/aegisops_enrich/.gitkeep`
- `n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json`
- `n8n/workflows/aegisops_notify/.gitkeep`
- `n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json`
- `n8n/workflows/aegisops_response/.gitkeep`

## Sigma Review Result

The Sigma curated and suppressed directories preserve the approved distinction between reviewed onboarding candidates and documented future suppression decisions.

The curated slice is limited to privileged group membership change, audit log cleared, and new local user created, and the suppressed directory remains placeholder-only without live suppression entries.

## n8n Workflow Category Review Result

The tracked n8n workflow structure keeps the approved alert ingest, enrich, approve, notify, and response categories while limiting exported workflow assets to the selected Phase 6 read-only slice.

Alert ingest, approve, and response remain placeholder-only with `.gitkeep` markers, while enrich and notify contain only the approved selected-detector workflow exports.

## Live Behavior Review Result

No reviewed Sigma asset introduces runnable detection behavior, and the reviewed n8n assets remain read-only workflow exports without approval-exempt write or response execution steps.

The current tracked Sigma assets remain reviewed content only, and the n8n workflow assets are limited to enrichment, routing, and notification payload preparation for the selected Windows detector outputs.

## Deviations

No deviations found.
EOF
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
create_sigma_and_n8n_skeleton "${valid_repo}"
mkdir -p "${valid_repo}/sigma"
cat <<'EOF' > "${valid_repo}/sigma/README.md"
# AegisOps Sigma Content Guidance

## Purpose

This document records the approved governance model for Sigma content tracked under `sigma/` and supplements the Sigma baseline in `docs/requirements-baseline.md`.

It explains how AegisOps distinguishes reviewed curated content from documented suppressed content so future contributors preserve the approved onboarding and review model.

## Directory Roles

### `curated/`

`sigma/curated/` is reserved for reviewed Sigma rules that are approved for future AegisOps onboarding.

A rule belongs in `curated/` when it has passed content review and is retained as an approved candidate for future platform onboarding.

### `suppressed/`

`sigma/suppressed/` is reserved for documented suppression decisions for Sigma content that should remain excluded from onboarding.

An entry belongs in `suppressed/` when the decision to exclude or defer Sigma content must be preserved with documented rationale, review, and approval context.

## Review Expectations

Any future addition under either directory must remain reviewable, attributable, and explicitly approved before placeholder-only status is removed.

## Validation Expectations

Contributors must validate that directory purpose, review state, and supporting documentation remain clear before merging changes.

## Scope Boundary

This document defines repository content governance only. It does not activate detections, create suppression behavior, or change runtime execution in OpenSearch, Sigma tooling, or n8n.
EOF
write_validation_doc "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
create_sigma_and_n8n_skeleton "${missing_report_repo}"
mkdir -p "${missing_report_repo}/sigma"
cp "${valid_repo}/sigma/README.md" "${missing_report_repo}/sigma/README.md"
assert_fails_with \
  "${missing_report_repo}" \
  "Missing Sigma and n8n skeleton validation result document"

bad_report_repo="${workdir}/bad-report"
create_repo "${bad_report_repo}"
create_sigma_and_n8n_skeleton "${bad_report_repo}"
mkdir -p "${bad_report_repo}/sigma"
cp "${valid_repo}/sigma/README.md" "${bad_report_repo}/sigma/README.md"
write_validation_doc "${bad_report_repo}"
python3 - <<'PY' "${bad_report_repo}/docs/sigma-n8n-skeleton-validation.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
path.write_text(text.replace("No deviations found.", "Pending review."))
PY
assert_fails_with \
  "${bad_report_repo}" \
  "Missing validation statement in"

echo "verify-sigma-n8n-skeleton-validation tests passed"
