#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-runbook-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/runbook.md"
}

inject_profile_map() {
  local target="$1"

  python3 - <<'PY' "${target}/docs/runbook.md"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
marker = "Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.\n\n"
block = """### 1.1 Reviewed Lab and Single-Customer Operator Profile Map

Operators must use this profile map to decide which reviewed cadence, backup review, restore rehearsal, upgrade-window, and secret-custody expectations apply before a startup, maintenance, or recovery window begins.

Shared expectations that stay the same across the reviewed lab and single-customer profiles are:

- both profiles remain business-hours oriented, operator-led, and limited to the reviewed control-plane, PostgreSQL, reverse-proxy, and Wazuh-facing path rather than HA, multi-node, or multi-customer expansion;
- both profiles require PostgreSQL-aware backup custody, configuration backup, restore validation for the approval, evidence, execution, and reconciliation record chain, and rollback to a prior known-good state; and
- both profiles require named ownership for approval and secret handling, with break-glass use kept documented, explicit, and subordinate to the reviewed fail-closed boundary.

For the reviewed lab profile, operators should plan for:

- startup, queue, backup, and reverse-proxy health review at least three times per business week, with one operator capturing the readiness result;
- daily PostgreSQL-aware backup plus configuration backup after reviewed changes, with one named operator verifying the backup job outcome;
- at least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery;
- upgrades that fit one business-hours maintenance window, with rollback returning to the prior known-good backup without extra platform staff or high-availability failover machinery; and
- one named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list as sufficient custody for the lab path.

For the reviewed single-customer profile, operators should plan for:

- daily queue and health review on business days plus weekly platform hygiene review for certificates, storage growth, and backup drift;
- daily PostgreSQL-aware backup, weekly backup review, and reviewed configuration backup before platform changes that affect customer operations;
- monthly restore rehearsal against a reviewed single-customer recovery target, including validation that customer-scoped workflow truth and linked evidence return cleanly;
- one planned maintenance window per month, with rollback remaining operator-led and free of cluster failover tooling or multi-customer coordination assumptions; and
- named customer-scoped approver ownership, a reviewed secret rotation checklist, and explicit break-glass custody for customer credentials.

"""
if "### 1.1 Reviewed Lab and Single-Customer Operator Profile Map" not in text:
    text = text.replace(marker, marker + block)
    path.write_text(text)
PY
}

inject_validation_contract() {
  local target="$1"

  python3 - <<'PY' "${target}/docs/runbook.md"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
marker = "The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`."
block = """The operator health review contract is the reviewed business-hours cadence for deciding whether the mainline path is ready, safely degraded, or escalation-bound.

Each business day, operators must review `curl -fsS http://127.0.0.1:<proxy-port>/readyz`, `curl -fsS http://127.0.0.1:<proxy-port>/runtime`, the reviewed queue and alert surfaces, and any explicit degraded-state markers before treating the platform as ready for normal work.

The daily review must classify each degraded condition as safe for continued business-hours inspection, requiring same-day follow-up, or requiring escalation before normal operation continues.

At least once per business week, operators must review storage growth, certificate expiry horizon, backup drift, and restore-readiness evidence against the reviewed SMB baseline instead of inferring platform hygiene from startup success alone.

Weekly review findings must remain operator-visible and must not redefine optional or degraded surfaces as startup blockers when the reviewed mainline path remains healthy.

Assistant optional path: `enabled` and `ready` means the bounded advisory surface is available; `degraded` means advisory outputs or receipts are lagging and require operator follow-up without widening authority.

Endpoint evidence optional path: `disabled_by_default` means no reviewed endpoint evidence request is active; `enabled` means a reviewed request is active; `degraded` means receipts or review-state updates are lagging and require follow-up without making endpoint evidence authoritative.

Optional network evidence path: `disabled_by_default` or `unavailable` means the reviewed runtime is operating without that optional path and the mainline queue, approval, execution, and reconciliation path remains valid.

ML shadow path: `disabled_by_default` or `unavailable` means the reviewed runtime is operating without ML shadow mode; any future `enabled` or `degraded` state must remain explicitly shadow-only, audit-focused, and non-blocking.

Escalation is required when readiness is not green on the reviewed ingress path, when queue or alert review cannot be completed from the reviewed mainline surface, when storage or certificate drift threatens the next business-hours window, when backup drift exceeds the reviewed cadence, or when any degraded condition could hide missing provenance or widen authority.

"""
if block.strip() not in text:
    text = text.replace(marker, block + marker)
    path.write_text(text)
PY
}

inject_secret_rotation_contract() {
  local target="$1"

  python3 - <<'PY' "${target}/docs/runbook.md"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old_heading = "## 5. Approval Handling"
new_block = """## 5. Secret Rotation and Break-Glass Custody

This section defines the reviewed operator contract for rotating actively managed runtime secrets and handling bootstrap or break-glass material without widening the current fail-closed boundary.

It supplements `docs/auth-baseline.md`, `docs/phase-27-day-2-hardening-validation.md`, and `control-plane/tests/test_runtime_secret_boundary.py` by turning the approved secret boundary into one explicit day-2 checklist.

### 5.1 Reviewed Secret Sources and Actively Managed Bindings

The approved secret sources for the current reviewed path are:

The actively managed runtime bindings that operators must track as reviewed operational inputs are:

### 5.2 Reviewed Secret Rotation Checklist

Use this checklist for scheduled rotation, emergency rotation, and any ownership-change or scope-change rotation event affecting the reviewed runtime:

If the reviewed backend secret source is unavailable, unreadable, stale, or resolves to an empty value, rotation must stop and remain failed closed.

### 5.3 Bootstrap Token and Break-Glass Custody Checklist

Bootstrap and break-glass material are recovery exceptions only.

After any break-glass use, operators must rotate the exposed bootstrap or break-glass material before the environment returns to normal operation and must preserve evidence showing the exception was closed.

## 6. Approval Handling"""
if "## 5. Secret Rotation and Break-Glass Custody" not in text:
    text = text.replace(old_heading, new_block)
text = text.replace("## 6. Validation", "## 7. Validation")
text = text.replace("### 6.1 Selected Slice and Preconditions", "### 7.1 Selected Slice and Preconditions")
text = text.replace("### 6.2 Analyst Validation Path", "### 7.2 Analyst Validation Path")
text = text.replace("### 6.3 Required Evidence Review", "### 7.3 Required Evidence Review")
text = text.replace("### 6.4 Disable and Rollback Path", "### 7.4 Disable and Rollback Path")
path.write_text(text)
PY
}

inject_upgrade_contract() {
  local target="$1"

  python3 - <<'PY' "${target}/docs/runbook.md"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
marker = "Restore validation before normal operations resume must confirm that:"
block = """The reviewed upgrade path is the one approved platform-change sequence for the current first-boot and single-customer operating posture.

Before a reviewed upgrade begins, operators must confirm all of the following:

Operators must not treat optional OpenSearch, n8n, Shuffle, assistant, or executor surfaces as upgrade prerequisites, upgrade success gates, or reasons to widen the current approved runtime floor.

The reviewed upgrade sequence is:

1. Capture the pre-upgrade readiness, runtime, compose status, and bounded logs through the approved reverse-proxy-first boundary before changing the running stack.
2. Apply the reviewed repository revision or release through the repo-owned first-boot compose path without widening ingress, publishing the backend port directly, or introducing HA or multi-node choreography.
3. Re-run the documented startup path from Section 2 and confirm migration bootstrap, PostgreSQL reachability, and reverse-proxy admission complete under the reviewed first-boot contract.
4. Compare the post-upgrade `/runtime` output, readiness evidence, and operator-visible queue state against the pre-change evidence before ending maintenance.

Rollback must begin the same day if the upgraded environment cannot satisfy the reviewed readiness path, preserve the approved reverse-proxy-first boundary, or keep the operator-visible record chain trustworthy before the maintenance window expires.

The minimum evidence set for a reviewed upgrade window is:

This reviewed upgrade path stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by keeping upgrades inside one business-hours maintenance window, preserving same-day rollback readiness, and avoiding HA or fleet-orchestration claims.

"""
if block.strip() not in text:
    text = text.replace(marker, block + marker)
    path.write_text(text)
PY
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
write_doc "${valid_repo}" '# AegisOps Runbook

This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.

It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.

It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts.

## 1. Purpose and Status

The reviewed procedure is limited to the current first-boot runtime floor:

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

### 1.1 Reviewed Lab and Single-Customer Operator Profile Map

Operators must use this profile map to decide which reviewed cadence, backup review, restore rehearsal, upgrade-window, and secret-custody expectations apply before a startup, maintenance, or recovery window begins.

Shared expectations that stay the same across the reviewed lab and single-customer profiles are:

- both profiles remain business-hours oriented, operator-led, and limited to the reviewed control-plane, PostgreSQL, reverse-proxy, and Wazuh-facing path rather than HA, multi-node, or multi-customer expansion;
- both profiles require PostgreSQL-aware backup custody, configuration backup, restore validation for the approval, evidence, execution, and reconciliation record chain, and rollback to a prior known-good state; and
- both profiles require named ownership for approval and secret handling, with break-glass use kept documented, explicit, and subordinate to the reviewed fail-closed boundary.

For the reviewed lab profile, operators should plan for:

- startup, queue, backup, and reverse-proxy health review at least three times per business week, with one operator capturing the readiness result;
- daily PostgreSQL-aware backup plus configuration backup after reviewed changes, with one named operator verifying the backup job outcome;
- at least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery;
- upgrades that fit one business-hours maintenance window, with rollback returning to the prior known-good backup without extra platform staff or high-availability failover machinery; and
- one named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list as sufficient custody for the lab path.

For the reviewed single-customer profile, operators should plan for:

- daily queue and health review on business days plus weekly platform hygiene review for certificates, storage growth, and backup drift;
- daily PostgreSQL-aware backup, weekly backup review, and reviewed configuration backup before platform changes that affect customer operations;
- monthly restore rehearsal against a reviewed single-customer recovery target, including validation that customer-scoped workflow truth and linked evidence return cleanly;
- one planned maintenance window per month, with rollback remaining operator-led and free of cluster failover tooling or multi-customer coordination assumptions; and
- named customer-scoped approver ownership, a reviewed secret rotation checklist, and explicit break-glass custody for customer credentials.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

## 2. Startup

The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file.

### 2.1 Startup Preconditions

Preconditions are documented for the reviewed startup path.

### 2.2 Reviewed Startup Sequence

Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.

The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface.

### 2.3 Startup Evidence Capture

- the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;
- the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and
- the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.

### 2.4 Ready-to-Operate Checks

Ready-to-operate checks remain limited to the reviewed first-boot floor.

## 3. Shutdown

The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress.

### 3.1 Controlled Shutdown Conditions

Controlled shutdown remains maintenance-window or fail-closed oriented.

### 3.2 Reviewed Shutdown Sequence

Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.

### 3.3 Shutdown Evidence Capture

- the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;

### 3.4 Safe-State Confirmation

- the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;

## 4. Restore

This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment.

Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window.

The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git.

Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set.

Restore validation before normal operations resume must confirm that:

- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;
- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;
- execution records and receipts remain intact without orphaning partially restored downstream state;
- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and
- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points.

Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy.

Rollback must begin when any of the following apply:
- the reviewed startup path succeeds but post-change validation shows missing or drifted approval, evidence, execution, or reconciliation records;

Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored.

This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path.

The operator health review contract is the reviewed business-hours cadence for deciding whether the mainline path is ready, safely degraded, or escalation-bound.

Each business day, operators must review `curl -fsS http://127.0.0.1:<proxy-port>/readyz`, `curl -fsS http://127.0.0.1:<proxy-port>/runtime`, the reviewed queue and alert surfaces, and any explicit degraded-state markers before treating the platform as ready for normal work.

The daily review must classify each degraded condition as safe for continued business-hours inspection, requiring same-day follow-up, or requiring escalation before normal operation continues.

At least once per business week, operators must review storage growth, certificate expiry horizon, backup drift, and restore-readiness evidence against the reviewed SMB baseline instead of inferring platform hygiene from startup success alone.

Weekly review findings must remain operator-visible and must not redefine optional or degraded surfaces as startup blockers when the reviewed mainline path remains healthy.

Assistant optional path: `enabled` and `ready` means the bounded advisory surface is available; `degraded` means advisory outputs or receipts are lagging and require operator follow-up without widening authority.

Endpoint evidence optional path: `disabled_by_default` means no reviewed endpoint evidence request is active; `enabled` means a reviewed request is active; `degraded` means receipts or review-state updates are lagging and require follow-up without making endpoint evidence authoritative.

Optional network evidence path: `disabled_by_default` or `unavailable` means the reviewed runtime is operating without that optional path and the mainline queue, approval, execution, and reconciliation path remains valid.

ML shadow path: `disabled_by_default` or `unavailable` means the reviewed runtime is operating without ML shadow mode; any future `enabled` or `degraded` state must remain explicitly shadow-only, audit-focused, and non-blocking.

Escalation is required when readiness is not green on the reviewed ingress path, when queue or alert review cannot be completed from the reviewed mainline surface, when storage or certificate drift threatens the next business-hours window, when backup drift exceeds the reviewed cadence, or when any degraded condition could hide missing provenance or widen authority.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
inject_secret_rotation_contract "${valid_repo}"
inject_upgrade_contract "${valid_repo}"
inject_validation_contract "${valid_repo}"
assert_passes "${valid_repo}"

missing_shutdown_repo="${workdir}/missing-shutdown"
create_repo "${missing_shutdown_repo}"
write_doc "${missing_shutdown_repo}" '# AegisOps Runbook

This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.

It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.

It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts.

## 1. Purpose and Status

The reviewed procedure is limited to the current first-boot runtime floor:

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

## 2. Startup

The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file.

### 2.1 Startup Preconditions

Preconditions are documented for the reviewed startup path.

### 2.2 Reviewed Startup Sequence

Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.

The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface.

### 2.3 Startup Evidence Capture

- the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;
- the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and
- the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.

### 2.4 Ready-to-Operate Checks

Ready-to-operate checks remain limited to the reviewed first-boot floor.

## 3. Shutdown

The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress.

### 3.1 Controlled Shutdown Conditions

Controlled shutdown remains maintenance-window or fail-closed oriented.

### 3.2 Reviewed Shutdown Sequence

Shutdown sequence text intentionally omitted here.

### 3.3 Shutdown Evidence Capture

- the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;

### 3.4 Safe-State Confirmation

- the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;

## 4. Restore

This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment.

Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window.

The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git.

Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set.

Restore validation before normal operations resume must confirm that:

- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;
- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;
- execution records and receipts remain intact without orphaning partially restored downstream state;
- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and
- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points.

Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy.

Rollback must begin when any of the following apply:
- the reviewed startup path succeeds but post-change validation shows missing or drifted approval, evidence, execution, or reconciliation records;

Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored.

This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
inject_secret_rotation_contract "${missing_shutdown_repo}"
inject_profile_map "${missing_shutdown_repo}"
inject_upgrade_contract "${missing_shutdown_repo}"
inject_validation_contract "${missing_shutdown_repo}"
assert_fails_with "${missing_shutdown_repo}" 'Missing runbook statement: Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.'

deferred_startup_repo="${workdir}/deferred-startup"
create_repo "${deferred_startup_repo}"
write_doc "${deferred_startup_repo}" '# AegisOps Runbook

This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.

It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.

It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts.

## 1. Purpose and Status

The reviewed procedure is limited to the current first-boot runtime floor:

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

## 2. Startup

Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist.

The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file.

### 2.1 Startup Preconditions

Preconditions are documented for the reviewed startup path.

### 2.2 Reviewed Startup Sequence

Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.

The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface.

### 2.3 Startup Evidence Capture

- the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;
- the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and
- the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.

### 2.4 Ready-to-Operate Checks

Ready-to-operate checks remain limited to the reviewed first-boot floor.

## 3. Shutdown

The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress.

### 3.1 Controlled Shutdown Conditions

Controlled shutdown remains maintenance-window or fail-closed oriented.

### 3.2 Reviewed Shutdown Sequence

Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.

### 3.3 Shutdown Evidence Capture

- the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;

### 3.4 Safe-State Confirmation

- the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;

## 4. Restore

This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment.

Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window.

The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git.

Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set.

Restore validation before normal operations resume must confirm that:

- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;
- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;
- execution records and receipts remain intact without orphaning partially restored downstream state;
- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and
- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points.

Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy.

Rollback must begin when any of the following apply:
- the reviewed startup path succeeds but post-change validation shows missing or drifted approval, evidence, execution, or reconciliation records;

Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored.

This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
inject_secret_rotation_contract "${deferred_startup_repo}"
inject_profile_map "${deferred_startup_repo}"
inject_upgrade_contract "${deferred_startup_repo}"
inject_validation_contract "${deferred_startup_repo}"
assert_fails_with "${deferred_startup_repo}" "Forbidden runbook statement still present: Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist."

missing_restore_validation_bullet_repo="${workdir}/missing-restore-validation-bullet"
create_repo "${missing_restore_validation_bullet_repo}"
grep -Fvx -- '- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;' "${valid_repo}/docs/runbook.md" >"${missing_restore_validation_bullet_repo}/docs/runbook.md"
assert_fails_with "${missing_restore_validation_bullet_repo}" "Missing restore validation bullet: - approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;"

missing_rollback_evidence_repo="${workdir}/missing-rollback-evidence"
create_repo "${missing_rollback_evidence_repo}"
write_doc "${missing_rollback_evidence_repo}" '# AegisOps Runbook

This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.

It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.

It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts.

## 1. Purpose and Status

The reviewed procedure is limited to the current first-boot runtime floor:

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

## 2. Startup

The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file.

### 2.1 Startup Preconditions

Preconditions are documented for the reviewed startup path.

### 2.2 Reviewed Startup Sequence

Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.

The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface.

### 2.3 Startup Evidence Capture

- the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;
- the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and
- the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.

### 2.4 Ready-to-Operate Checks

Ready-to-operate checks remain limited to the reviewed first-boot floor.

## 3. Shutdown

The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress.

### 3.1 Controlled Shutdown Conditions

Controlled shutdown remains maintenance-window or fail-closed oriented.

### 3.2 Reviewed Shutdown Sequence

Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.

### 3.3 Shutdown Evidence Capture

- the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;

### 3.4 Safe-State Confirmation

- the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;

## 4. Restore

This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment.

Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window.

The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git.

Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set.

Restore validation before normal operations resume must confirm that:

- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;
- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;
- execution records and receipts remain intact without orphaning partially restored downstream state;
- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and
- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points.

Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy.

Rollback must begin when any of the following apply:
- the reviewed startup path succeeds but post-change validation shows missing or drifted approval, evidence, execution, or reconciliation records;

This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
inject_secret_rotation_contract "${missing_rollback_evidence_repo}"
inject_profile_map "${missing_rollback_evidence_repo}"
inject_upgrade_contract "${missing_rollback_evidence_repo}"
inject_validation_contract "${missing_rollback_evidence_repo}"
assert_fails_with "${missing_rollback_evidence_repo}" "Missing runbook statement: Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored."

missing_rollback_trigger_bullet_repo="${workdir}/missing-rollback-trigger-bullet"
create_repo "${missing_rollback_trigger_bullet_repo}"
write_doc "${missing_rollback_trigger_bullet_repo}" '# AegisOps Runbook

This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.

It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.

It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts.

## 1. Purpose and Status

The reviewed procedure is limited to the current first-boot runtime floor:

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

## 2. Startup

The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file.

### 2.1 Startup Preconditions

Preconditions are documented for the reviewed startup path.

### 2.2 Reviewed Startup Sequence

Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.

The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface.

### 2.3 Startup Evidence Capture

- the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;
- the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and
- the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.

### 2.4 Ready-to-Operate Checks

Ready-to-operate checks remain limited to the reviewed first-boot floor.

## 3. Shutdown

The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress.

### 3.1 Controlled Shutdown Conditions

Controlled shutdown remains maintenance-window or fail-closed oriented.

### 3.2 Reviewed Shutdown Sequence

Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.

### 3.3 Shutdown Evidence Capture

- the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;

### 3.4 Safe-State Confirmation

- the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;

## 4. Restore

This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment.

Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window.

The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git.

Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set.

Restore validation before normal operations resume must confirm that:

- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;
- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;
- execution records and receipts remain intact without orphaning partially restored downstream state;
- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and
- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points.

Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy.

Rollback must begin when any of the following apply:

Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored.

This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
inject_secret_rotation_contract "${missing_rollback_trigger_bullet_repo}"
inject_profile_map "${missing_rollback_trigger_bullet_repo}"
inject_upgrade_contract "${missing_rollback_trigger_bullet_repo}"
inject_validation_contract "${missing_rollback_trigger_bullet_repo}"
assert_fails_with "${missing_rollback_trigger_bullet_repo}" "Rollback trigger block must include a bullet immediately after header: Rollback must begin when any of the following apply:"

missing_profile_map_repo="${workdir}/missing-profile-map"
create_repo "${missing_profile_map_repo}"
cp "${valid_repo}/docs/runbook.md" "${missing_profile_map_repo}/docs/runbook.md"
python3 - <<'PY' "${missing_profile_map_repo}/docs/runbook.md"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "### 1.1 Reviewed Lab and Single-Customer Operator Profile Map\n\n"
    "Operators must use this profile map to decide which reviewed cadence, backup review, restore rehearsal, upgrade-window, and secret-custody expectations apply before a startup, maintenance, or recovery window begins.\n\n"
    "Shared expectations that stay the same across the reviewed lab and single-customer profiles are:\n\n"
    "- both profiles remain business-hours oriented, operator-led, and limited to the reviewed control-plane, PostgreSQL, reverse-proxy, and Wazuh-facing path rather than HA, multi-node, or multi-customer expansion;\n"
    "- both profiles require PostgreSQL-aware backup custody, configuration backup, restore validation for the approval, evidence, execution, and reconciliation record chain, and rollback to a prior known-good state; and\n"
    "- both profiles require named ownership for approval and secret handling, with break-glass use kept documented, explicit, and subordinate to the reviewed fail-closed boundary.\n\n"
    "For the reviewed lab profile, operators should plan for:\n\n"
    "- startup, queue, backup, and reverse-proxy health review at least three times per business week, with one operator capturing the readiness result;\n"
    "- daily PostgreSQL-aware backup plus configuration backup after reviewed changes, with one named operator verifying the backup job outcome;\n"
    "- at least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery;\n"
    "- upgrades that fit one business-hours maintenance window, with rollback returning to the prior known-good backup without extra platform staff or high-availability failover machinery; and\n"
    "- one named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list as sufficient custody for the lab path.\n\n"
    "For the reviewed single-customer profile, operators should plan for:\n\n"
    "- daily queue and health review on business days plus weekly platform hygiene review for certificates, storage growth, and backup drift;\n"
    "- daily PostgreSQL-aware backup, weekly backup review, and reviewed configuration backup before platform changes that affect customer operations;\n"
    "- monthly restore rehearsal against a reviewed single-customer recovery target, including validation that customer-scoped workflow truth and linked evidence return cleanly;\n"
    "- one planned maintenance window per month, with rollback remaining operator-led and free of cluster failover tooling or multi-customer coordination assumptions; and\n"
    "- named customer-scoped approver ownership, a reviewed secret rotation checklist, and explicit break-glass custody for customer credentials.\n\n",
    "",
    1,
)
path.write_text(text)
PY
assert_fails_with "${missing_profile_map_repo}" "Missing runbook statement: ### 1.1 Reviewed Lab and Single-Customer Operator Profile Map"

echo "Runbook verifier tests passed."
