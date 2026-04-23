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
assert_fails_with "${deferred_startup_repo}" "Forbidden runbook statement still present: Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist."

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
assert_fails_with "${missing_rollback_trigger_bullet_repo}" "Rollback trigger block must include a bullet immediately after header: Rollback must begin when any of the following apply:"

echo "Runbook verifier tests passed."
