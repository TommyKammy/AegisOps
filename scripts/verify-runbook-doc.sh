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
  "## 5. Approval Handling"
  "## 6. Validation"
  "### 6.1 Selected Slice and Preconditions"
  "### 6.2 Analyst Validation Path"
  "### 6.3 Required Evidence Review"
  "### 6.4 Disable and Rollback Path"
)

required_phrases=(
  "This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path."
  'It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.'
  "It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts."
  "The reviewed procedure is limited to the current first-boot runtime floor:"
  'Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.'
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
  "The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default."
  "Detailed restore steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Approval handling procedures must preserve human review, auditability, and the separation between detection and execution."
  "Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path."
  'The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.'
  "This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours."
  'Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.'
  'If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.'
  "The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation."
)

forbidden_phrases=(
  "This runbook is an initial skeleton for approved future operational procedures."
  "Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Detailed shutdown steps are intentionally deferred until implementation artifacts and validation procedures exist."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing runbook document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing runbook heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing runbook statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${forbidden_phrases[@]}"; do
  if grep -Fq "${phrase}" "${doc_path}"; then
    echo "Forbidden runbook statement still present: ${phrase}" >&2
    exit 1
  fi
done

echo "Runbook document is present and covers the reviewed startup, shutdown, and retained Phase 6 validation slice."
