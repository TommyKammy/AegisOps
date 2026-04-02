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
    "${target}/sigma/curated" \
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

Status: placeholder only; no active Sigma detection rules are committed here yet.

This directory reserves the approved location for future curated Sigma content after review.

Rule onboarding requires future review and explicit approval before any real rule content is added.
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

Placeholder directories and marker files under `n8n/workflows/` are not production workflows.

They reserve approved homes for future workflow assets without claiming that exported workflows, credentials, triggers, or integrations are already implemented here.

Do not infer live runtime behavior, integration coverage, or production-ready response logic from the current placeholders.

## 4. Control vs Execution Alignment

OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution.

This separation preserves the approved control-versus-execution model: alerts are detected in the analytics plane first, then routed into the orchestration plane for reviewable enrichment, approval, notification, and response handling.

The guidance in this directory does not authorize direct destructive actions from raw inbound alerts, hidden write operations inside read-only workflows, or approval bypass by implementation detail.

## 5. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

Keep future workflow additions within the approved category boundary and preserve explicit approval gates for write or destructive actions.

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
}

write_validation_doc() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/sigma-n8n-skeleton-validation.md"
# Sigma and n8n Skeleton Asset Validation

- Validation date: 2026-04-02
- Baseline references: `docs/requirements-baseline.md`, `docs/repository-structure-baseline.md`, `sigma/README.md`, `n8n/workflows/README.md`
- Verification commands: `bash scripts/verify-sigma-guidance-doc.sh`, `bash scripts/verify-sigma-curated-skeleton.sh`, `bash scripts/verify-sigma-suppressed-skeleton.sh`, `bash scripts/verify-n8n-workflow-category-guidance.sh`, `bash scripts/verify-n8n-workflow-skeleton.sh`, `bash scripts/verify-sigma-n8n-skeleton-validation.sh`
- Validation status: PASS

## Reviewed Artifacts

- `sigma/README.md`
- `sigma/curated/README.md`
- `sigma/suppressed/README.md`
- `n8n/workflows/README.md`
- `n8n/workflows/aegisops_alert_ingest/.gitkeep`
- `n8n/workflows/aegisops_approve/.gitkeep`
- `n8n/workflows/aegisops_enrich/.gitkeep`
- `n8n/workflows/aegisops_notify/.gitkeep`
- `n8n/workflows/aegisops_response/.gitkeep`

## Sigma Review Result

The Sigma curated and suppressed directories preserve the approved distinction between future onboarding candidates and documented future suppression decisions.

Both directories remain placeholder-only and do not introduce live Sigma rule, suppression, exception, or decision content.

## n8n Workflow Category Review Result

The tracked n8n workflow skeleton covers the approved alert ingest, enrich, approve, notify, and response categories.

Each category remains a placeholder-only directory with a `.gitkeep` marker, and no exported workflow, trigger, credential, or execution logic is present.

## Live Behavior Review Result

No reviewed Sigma asset introduces runnable detection behavior, and no reviewed n8n asset introduces runnable workflow behavior.

The current tracked assets remain documentation and placeholder markers only.

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
