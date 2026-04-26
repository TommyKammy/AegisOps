#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/runbook.md"

required_headings=(
  "# AegisOps Runbook"
  "## 1. Purpose and Status"
  "## 2. Startup"
  "### 2.1 Startup Preconditions"
  "### 2.2 Reviewed Startup Sequence"
  "### 2.3 Startup Evidence Capture"
  "### 2.4 Ready-to-Operate Checks"
  "## 3. Shutdown"
  "### 3.1 Controlled Shutdown Conditions"
  "### 3.2 Reviewed Shutdown Sequence"
  "### 3.3 Shutdown Evidence Capture"
  "### 3.4 Safe-State Confirmation"
  "## 4. Restore"
  "## 5. Secret Rotation and Break-Glass Custody"
  "### 5.1 Reviewed Secret Sources and Actively Managed Bindings"
  "### 5.2 Reviewed Secret Rotation Checklist"
  "### 5.3 Bootstrap Token and Break-Glass Custody Checklist"
  "## 6. Approval Handling"
  "### 6.1 Approval Role Matrix"
  "### 6.2 Denial, Timeout, Fallback, and Break-Glass Closeout"
  "### 6.3 Approval Evidence and Authority Boundary"
  "## 7. Validation"
  "### 7.1 Selected Slice and Preconditions"
  "### 7.2 Analyst Validation Path"
  "### 7.3 Required Evidence Review"
  "### 7.4 Disable and Rollback Path"
)

required_phrases=(
  "This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path."
  'It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.'
  "It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts."
  "The reviewed procedure is limited to the current first-boot runtime floor:"
  'Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.'
  "### 1.1 Reviewed Lab and Single-Customer Operator Profile Map"
  "Operators must use this profile map to decide which reviewed cadence, backup review, restore rehearsal, upgrade-window, and secret-custody expectations apply before a startup, maintenance, or recovery window begins."
  "Shared expectations that stay the same across the reviewed lab and single-customer profiles are:"
  "- both profiles remain business-hours oriented, operator-led, and limited to the reviewed control-plane, PostgreSQL, reverse-proxy, and Wazuh-facing path rather than HA, multi-node, or multi-customer expansion;"
  "- both profiles require PostgreSQL-aware backup custody, configuration backup, restore validation for the approval, evidence, execution, and reconciliation record chain, and rollback to a prior known-good state; and"
  "- both profiles require named ownership for approval and secret handling, with break-glass use kept documented, explicit, and subordinate to the reviewed fail-closed boundary."
  "For the reviewed lab profile, operators should plan for:"
  "- startup, queue, backup, and reverse-proxy health review at least three times per business week, with one operator capturing the readiness result;"
  "- daily PostgreSQL-aware backup plus configuration backup after reviewed changes, with one named operator verifying the backup job outcome;"
  "- at least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery;"
  "- upgrades that fit one business-hours maintenance window, with rollback returning to the prior known-good backup without extra platform staff or high-availability failover machinery; and"
  "- one named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list as sufficient custody for the lab path."
  "For the reviewed single-customer profile, operators should plan for:"
  "- daily queue and health review on business days plus weekly platform hygiene review for certificates, storage growth, and backup drift;"
  "- daily PostgreSQL-aware backup, weekly backup review, and reviewed configuration backup before platform changes that affect customer operations;"
  "- monthly restore rehearsal against a reviewed single-customer recovery target, including validation that customer-scoped workflow truth and linked evidence return cleanly;"
  "- one planned maintenance window per month, with rollback remaining operator-led and free of cluster failover tooling or multi-customer coordination assumptions; and"
  "- named customer-scoped approver ownership, a reviewed secret rotation checklist, and explicit break-glass custody for customer credentials."
  "Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations."
  "Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites."
  "The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file."
  'Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.'
  "The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface."
  'the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;'
  'the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and'
  'the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.'
  "The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress."
  'Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.'
  'the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;'
  'the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;'
  "This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment."
  "Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window."
  "The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git."
  "Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set."
  'The reviewed upgrade path is the one approved platform-change sequence for the current first-boot and single-customer operating posture.'
  'Before a reviewed upgrade begins, operators must confirm all of the following:'
  'Operators must not treat optional OpenSearch, n8n, Shuffle, assistant, or executor surfaces as upgrade prerequisites, upgrade success gates, or reasons to widen the current approved runtime floor.'
  'The reviewed upgrade sequence is:'
  'Capture the pre-upgrade readiness, runtime, compose status, and bounded logs through the approved reverse-proxy-first boundary before changing the running stack.'
  'Apply the reviewed repository revision or release through the repo-owned first-boot compose path without widening ingress, publishing the backend port directly, or introducing HA or multi-node choreography.'
  'Re-run the documented startup path from Section 2 and confirm migration bootstrap, PostgreSQL reachability, and reverse-proxy admission complete under the reviewed first-boot contract.'
  'Compare the post-upgrade `/runtime` output, readiness evidence, and operator-visible queue state against the pre-change evidence before ending maintenance.'
  'Rollback must begin the same day if the upgraded environment cannot satisfy the reviewed readiness path, preserve the approved reverse-proxy-first boundary, or keep the operator-visible record chain trustworthy before the maintenance window expires.'
  'The minimum evidence set for a reviewed upgrade window is:'
  'This reviewed upgrade path stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by keeping upgrades inside one business-hours maintenance window, preserving same-day rollback readiness, and avoiding HA or fleet-orchestration claims.'
  "Restore validation before normal operations resume must confirm that:"
  "Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy."
  "Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored."
  'This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.'
  "This section defines the reviewed operator contract for rotating actively managed runtime secrets and handling bootstrap or break-glass material without widening the current fail-closed boundary."
  'It supplements `docs/auth-baseline.md`, `docs/phase-27-day-2-hardening-validation.md`, and `control-plane/tests/test_runtime_secret_boundary.py` by turning the approved secret boundary into one explicit day-2 checklist.'
  "The approved secret sources for the current reviewed path are:"
  "The actively managed runtime bindings that operators must track as reviewed operational inputs are:"
  "Use this checklist for scheduled rotation, emergency rotation, and any ownership-change or scope-change rotation event affecting the reviewed runtime:"
  "If the reviewed backend secret source is unavailable, unreadable, stale, or resolves to an empty value, rotation must stop and remain failed closed."
  "Bootstrap and break-glass material are recovery exceptions only."
  "After any break-glass use, operators must rotate the exposed bootstrap or break-glass material before the environment returns to normal operation and must preserve evidence showing the exception was closed."
  "The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default."
  "Approval handling procedures must preserve human review, auditability, and the separation between detection and execution."
  "| Approver | Reviews the exact AegisOps action request, linked case, requested scope, evidence, risk, and expiry window before recording approve or deny on the AegisOps approval decision record. |"
  "| Fallback approver | Acts only when the primary approver is unavailable or the approval window would otherwise expire, and must preserve the fallback reason, time window, and same scope limits as the original request. |"
  "| Platform admin | Maintains reviewed identity, role binding, runtime, and secret-custody plumbing, but does not approve an action unless separately named as the approver for that request. |"
  "| Operator | Prepares the action request, evidence bundle, and routing note, then waits for the reviewed approval outcome instead of self-approving, executing, or treating a ticket comment as approval. |"
  "| Support owner | Coordinates degradation, denial, timeout, fallback, or break-glass follow-up evidence and next-owner handoff, but does not approve, execute, reconcile, or redefine AegisOps workflow truth. |"
  "A denied approval keeps the action request blocked from execution, records the denial reason on the AegisOps approval decision record, and preserves any external ticket or support note only as subordinate coordination context."
  "An approval timeout or expired approval window keeps execution blocked until a new reviewed request is created or the documented fallback approver path records the same scope, reason, and evidence in AegisOps."
  "Fallback approval handling requires a named fallback approver, the reason the primary approver could not decide inside the reviewed window, the unchanged action scope, and evidence that the fallback did not widen authority."
  "Break-glass closeout is a recovery closeout path only: it must document trigger, custodian, approving reviewer, bounded access window, affected binding, rotation or invalidation evidence, readiness or refusal check, clean-state proof, and return-to-normal owner without converting break-glass use into approval, execution, or reconciliation authority."
  "Approval truth remains the AegisOps approval decision record; external ticket comments, assistant output, browser state, downstream execution receipts, optional evidence, or support notes must not approve, deny, expire, supersede, execute, or reconcile an action."
  "Approval, execution, and reconciliation evidence must stay visibly separated: the approval record says whether the exact request is allowed, the execution record says what was attempted or refused, and the reconciliation record says whether the observed outcome matches the approved intent."
  "Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path."
  "The operator health review contract is the reviewed business-hours cadence for deciding whether the mainline path is ready, safely degraded, or escalation-bound."
  'Each business day, operators must review `curl -fsS http://127.0.0.1:<proxy-port>/readyz`, `curl -fsS http://127.0.0.1:<proxy-port>/runtime`, the reviewed queue and alert surfaces, and any explicit degraded-state markers before treating the platform as ready for normal work.'
  "The daily review must classify each degraded condition as safe for continued business-hours inspection, requiring same-day follow-up, or requiring escalation before normal operation continues."
  "At least once per business week, operators must review storage growth, certificate expiry horizon, backup drift, and restore-readiness evidence against the reviewed SMB baseline instead of inferring platform hygiene from startup success alone."
  "Weekly review findings must remain operator-visible and must not redefine optional or degraded surfaces as startup blockers when the reviewed mainline path remains healthy."
  'Assistant optional path: `enabled` and `ready` means the bounded advisory surface is available; `degraded` means advisory outputs or receipts are lagging and require operator follow-up without widening authority.'
  'Endpoint evidence optional path: `disabled_by_default` means no reviewed endpoint evidence request is active; `enabled` means a reviewed request is active; `degraded` means receipts or review-state updates are lagging and require follow-up without making endpoint evidence authoritative.'
  'Optional network evidence path: `disabled_by_default` or `unavailable` means the reviewed runtime is operating without that optional path and the mainline queue, approval, execution, and reconciliation path remains valid.'
  'ML shadow path: `disabled_by_default` or `unavailable` means the reviewed runtime is operating without ML shadow mode; any future `enabled` or `degraded` state must remain explicitly shadow-only, audit-focused, and non-blocking.'
  "Escalation is required when readiness is not green on the reviewed ingress path, when queue or alert review cannot be completed from the reviewed mainline surface, when storage or certificate drift threatens the next business-hours window, when backup drift exceeds the reviewed cadence, or when any degraded condition could hide missing provenance or widen authority."
  'The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.'
  "This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours."
  'Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.'
  'If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.'
  "The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation."
)

required_restore_validation_bullets=(
  "- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;"
  "- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;"
  "- execution records and receipts remain intact without orphaning partially restored downstream state;"
  "- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and"
  "- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points."
)

rollback_trigger_header="Rollback must begin when any of the following apply:"

forbidden_phrases=(
  "This runbook is an initial skeleton for approved future operational procedures."
  "Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Detailed shutdown steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Detailed restore steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Future approval guidance should describe:"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing runbook document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing runbook heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing runbook statement: ${phrase}" >&2
    exit 1
  fi
done

for bullet in "${required_restore_validation_bullets[@]}"; do
  if ! grep -Fq -- "${bullet}" "${doc_path}"; then
    echo "Missing restore validation bullet: ${bullet}" >&2
    exit 1
  fi
done

rollback_trigger_line="$(
  grep -nF "${rollback_trigger_header}" "${doc_path}" | head -n 1 | cut -d: -f1
)"
if [[ -z "${rollback_trigger_line}" ]]; then
  echo "Missing runbook statement: ${rollback_trigger_header}" >&2
  exit 1
fi

if ! sed -n "$((rollback_trigger_line + 1))p" "${doc_path}" | grep -Eq '^[[:space:]]*[-*][[:space:]]+'; then
  echo "Rollback trigger block must include a bullet immediately after header: ${rollback_trigger_header}" >&2
  exit 1
fi

for phrase in "${forbidden_phrases[@]}"; do
  if grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Forbidden runbook statement still present: ${phrase}" >&2
    exit 1
  fi
done

echo "Runbook document is present and covers the reviewed startup, shutdown, and retained Phase 6 validation slice."
