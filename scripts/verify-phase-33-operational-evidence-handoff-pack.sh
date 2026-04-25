#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
runbook_path="${repo_root}/docs/runbook.md"
profile_path="${repo_root}/docs/deployment/single-customer-profile.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_file "${doc_path}" "Phase 33 operational evidence handoff pack"
require_file "${runbook_path}" "runbook document"
require_file "${profile_path}" "single-customer deployment profile"
require_file "${smoke_path}" "Phase 33 runtime smoke bundle"

required_headings=(
  "# Phase 33 Operational Evidence Retention and Audit Handoff Pack"
  "## 1. Purpose and Boundary"
  "## 2. Retained Evidence Categories"
  "## 3. Operator-Visible Handoff Artifacts"
  "## 4. Minimal Handoff Package"
  "## 5. Retention Expectations"
  "## 6. Restore and Reconciliation Alignment"
  "## 7. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "Phase 33 operational evidence handoff pack heading"
done

required_phrases=(
  "This document defines the Phase 33 operational evidence retention and audit handoff pack for the reviewed single-customer profile."
  "The handoff pack is a small-team operational package, not a new archive platform, SIEM replacement, or external authority source."
  'The authoritative record chain remains inside AegisOps reviewed records for approval, evidence, execution, and reconciliation truth.'
  'The pack is anchored to `docs/deployment/single-customer-release-bundle-inventory.md`, `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `docs/deployment/runtime-smoke-bundle.md`.'
  '| Event category | Retained evidence | Authority boundary |'
  '| Upgrade | Approved maintenance window, named operator, pre-change backup custody confirmation, selected restore point, before-and-after repository revisions, pre-change and post-change smoke results, bounded upgrade-window logs, and rollback decision. | Handoff evidence only; upgrade success is accepted only when the reviewed runtime checks and AegisOps record chain remain trustworthy. |'
  '| Restore | Triggering reason, selected restore point, backup custody confirmation, repository revision or release identifier, post-restore readiness checks, and approval, evidence, execution, and reconciliation record-chain validation outcome. | Restore evidence supports return-to-service review but does not redefine record truth outside AegisOps. |'
  '| Approval | Customer-scoped approver ownership, approval decision reference, reviewed case or action scope, timeout or rejection reason when applicable, and any break-glass custody note. | Approval truth remains the reviewed AegisOps approval record, not the handoff note. |'
  '| Execution | Action request reference, approved execution surface, dispatch or refusal receipt, bounded executor or substrate receipt when present, and idempotency or correlation evidence needed for review. | Execution truth remains the AegisOps action-execution record and linked receipt, not vendor-local status alone. |'
  '| Reconciliation | Reconciliation record reference, expected outcome, observed outcome, mismatch or terminal marker, reviewer decision, and linked evidence used to close or escalate the outcome. | Reconciliation truth remains the reviewed AegisOps reconciliation record. |'
  'The operator-visible artifacts are the maintenance or review record, runtime smoke result, backup and restore custody note, bounded logs with secrets redacted, readiness and runtime inspection outputs, and reviewed record-chain references.'
  'The minimal handoff package after deployment, upgrade, restore, approval, execution, or reconciliation review contains:'
  '- the reviewed event type and named operator;'
  '- the repository revision or release identifier when the event changes runtime state;'
  '- the customer-scoped scope reference without embedding live customer secrets;'
  '- the required evidence category entries for the event;'
  '- the runtime smoke result when deployment, upgrade, rollback, or handoff readiness is in scope;'
  '- the backup, restore, or rollback custody reference when recovery state is in scope;'
  '- the AegisOps reviewed record identifiers for approval, execution, evidence, or reconciliation when workflow truth is in scope; and'
  '- the next daily queue, health review, restore review, or reconciliation follow-up owner.'
  'Retention is bounded to the reviewed small-team operating need: keep the latest deploy or upgrade handoff, the latest successful restore rehearsal or restore event, open approval, execution, and reconciliation review evidence, and the evidence required for the next daily or weekly operator review.'
  'Older handoff packs may be summarized or superseded after the reviewed follow-up is complete, provided the AegisOps reviewed records and required backup or restore custody evidence remain intact.'
  'Retention expectations must remain aligned with the Phase 32 restore contract: approval, evidence, execution, and reconciliation records must return cleanly from the selected PostgreSQL-aware restore point before normal operation resumes.'
  'The handoff pack must reference the Phase 33 runtime smoke bundle for deployment, upgrade, rollback, and operator handoff readiness evidence.'
  'If restore, export, readiness, or detail rollup evidence appears to combine mixed snapshots, the handoff must stay blocked until operators can prove one committed state or preserve the refusal as the review outcome.'
  'Enterprise SIEM archive design, unlimited retention, new authority sources, broad external archive integration, vendor-specific archive automation, multi-customer evidence warehouses, and raw secret-bearing evidence bundles are out of scope.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "Phase 33 operational evidence handoff pack statement"
done

require_phrase "${runbook_path}" 'The Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md` is the reviewed minimum package for deployment, upgrade, restore, approval, execution, and reconciliation handoff evidence.' "runbook Phase 33 operational evidence handoff pack link"
require_phrase "${profile_path}" 'The Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md` defines the minimal retained audit package for upgrade, restore, approval, execution, and reconciliation events.' "single-customer profile Phase 33 operational evidence handoff pack link"
require_phrase "${smoke_path}" 'The smoke result is one input to the Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md`; it does not replace approval, execution, restore, or reconciliation record evidence.' "runtime smoke bundle Phase 33 operational evidence handoff pack link"

for forbidden in "requires unlimited retention" "requires enterprise SIEM archive" "external archive integration is required" "creates a new authority source" "retain raw secret-bearing evidence"; do
  if grep -Fqi -- "${forbidden}" "${doc_path}"; then
    echo "Forbidden Phase 33 operational evidence handoff pack statement: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 33 operational evidence handoff pack is present and preserves the reviewed evidence, authority, retention, and archive boundaries."
