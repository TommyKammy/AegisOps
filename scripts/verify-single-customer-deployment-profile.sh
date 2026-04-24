#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/single-customer-profile.md"
runbook_path="${repo_root}/docs/runbook.md"
profile_baseline_path="${repo_root}/docs/smb-footprint-and-deployment-profile-baseline.md"

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

require_file "${doc_path}" "single-customer deployment profile package"
require_file "${runbook_path}" "runbook document"
require_file "${profile_baseline_path}" "SMB deployment profile baseline"

required_headings=(
  "# Single-Customer Deployment Profile"
  "## 1. Package Status"
  "## 2. Deployable Shape"
  "## 3. Approved Inputs"
  "## 4. Service and Path Boundary"
  "## 5. First-Boot to Single-Customer Delta"
  "## 6. Optional Extensions"
  "## 7. Upgrade and Same-Day Rollback Rehearsal Contract"
  "## 8. Day-2 Operating Shape"
  "## 9. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "single-customer deployment profile heading"
done

required_phrases=(
  'This document is the repo-owned single-customer deployment profile package for the reviewed Phase 33 deployment boundary.'
  'It packages the current first-boot runtime surface into the default reviewed deployment shape for one customer environment without adding multi-customer, HA, or optional-service prerequisites.'
  'The package is anchored to `docs/runbook.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `control-plane/deployment/first-boot/`.'
  'The required services for this profile are limited to:'
  '- AegisOps control-plane service from `control-plane/`;'
  '- PostgreSQL for authoritative AegisOps-owned state;'
  '- the approved reverse proxy boundary as the only reviewed user-facing ingress path; and'
  '- the Wazuh-facing analytic-signal intake path admitted through the reviewed proxy and control-plane boundary.'
  'The approved repo-owned startup surface remains `control-plane/deployment/first-boot/docker-compose.yml` with `control-plane/deployment/first-boot/bootstrap.env.sample` copied into an untracked runtime env file.'
  'The approved required runtime inputs are:'
  '- `AEGISOPS_CONTROL_PLANE_HOST`;'
  '- `AEGISOPS_CONTROL_PLANE_PORT`;'
  '- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`;'
  '- `AEGISOPS_CONTROL_PLANE_BOOT_MODE`; and'
  '- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`.'
  'The approved secret and boundary inputs are the PostgreSQL credential source, the Wazuh ingest shared secret source, the Wazuh ingest reverse-proxy secret source, the protected-surface reverse-proxy secret source, the protected-surface trusted proxy CIDRs, the protected-surface proxy service account, the reviewed identity-provider binding, the admin bootstrap token source, the break-glass token source, and any reviewed OpenBao address, token, token-file, and mount bindings used to resolve those secrets.'
  'Live secret values, customer credentials, DSNs, bootstrap tokens, break-glass tokens, and environment-specific certificates must stay outside Git.'
  'The reverse proxy is the only reviewed user-facing ingress path for health, readiness, runtime inspection, operator UI, and Wazuh-facing intake admission.'
  'The control-plane backend port, PostgreSQL port, and secret backend are internal service surfaces and must not become independently published front doors.'
  'The Wazuh-facing path is a substrate-detection intake path into AegisOps-owned records, not a direct Wazuh-to-automation or Wazuh-owned case-authority shortcut.'
  'The single-customer profile keeps the same first-boot service boundary but changes the operator-visible operating contract from a lab rehearsal to one named customer environment.'
  'The single-customer delta is daily business-day queue and health review, weekly platform hygiene review, daily PostgreSQL-aware backup, weekly backup review, pre-change configuration backup, monthly restore rehearsal, one planned maintenance window per month, named customer-scoped approver ownership, reviewed secret rotation, and explicit break-glass custody for customer credentials.'
  'The delta does not add direct backend exposure, browser authority, substrate authority, direct automation shortcuts, HA topology, multi-customer coordination, or optional-service installation.'
  'Optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, and isolated-executor paths are disabled by default, unavailable, or explicitly non-blocking unless a later reviewed package enables one for a bounded purpose.'
  'Optional extensions must not become startup prerequisites, readiness gates, upgrade success gates, or reasons to widen the control-plane, PostgreSQL, reverse-proxy, or Wazuh-facing boundary.'
  'The Phase 33 upgrade rehearsal is the single-customer maintenance-window exercise that proves a reviewed repository revision can be introduced and, if needed, returned to the prior known-good state the same day.'
  'Before the rehearsal begins, operators must confirm the daily PostgreSQL-aware backup is current, the pre-change configuration backup has been captured, the restore point for rollback is named, and the backup custody record identifies the operator or break-glass owner for the window.'
  'The rehearsal assumes one planned business-hours maintenance window for the named customer environment, not zero-downtime rollout, HA failover, multi-region recovery, or infrastructure-vendor-specific upgrade tooling.'
  'Rollback decision review happens before the maintenance window closes and must choose one of two recorded outcomes: keep the upgraded revision only if post-upgrade checks pass, or start same-day rollback to the selected restore point if readiness, runtime inspection, reverse-proxy boundary, or record-chain trust cannot be proven.'
  'Post-upgrade smoke checks are the reviewed runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md`: reverse-proxy `/readyz`, reverse-proxy `/runtime`, repo-owned compose status, bounded upgrade-window logs, and operator-visible queue or alert review from the mainline surface.'
  'Restore compatibility for the rehearsal is inherited from the Phase 32 runbook baseline: approval, evidence, execution, and reconciliation records must return cleanly from the selected PostgreSQL-aware restore point before normal operation resumes.'
  'The rehearsal evidence must retain the maintenance-window approval, named operator, pre-change backup custody confirmation, selected restore point, before-and-after repository revisions, pre-change and post-change smoke results, rollback decision, and any post-rollback restore validation.'
  'Day-2 operation follows the cadence in `docs/runbook.md` and `docs/smb-footprint-and-deployment-profile-baseline.md` for the reviewed single-customer profile.'
  'Operators must preserve PostgreSQL-aware backup custody, restore validation for approval, evidence, execution, and reconciliation records, same-day rollback readiness, certificate and storage-growth hygiene review, and reviewed secret rotation evidence.'
  'HA topology, multi-customer packaging, optional-service auto-installation, vendor-specific deployment automation, direct browser authority, direct substrate authority, and endpoint, network, assistant, or ML shadow paths as deployment prerequisites are out of scope.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "single-customer deployment profile statement"
done

require_phrase "${runbook_path}" "For the reviewed single-customer profile, operators should plan for:" "runbook single-customer profile map"
require_phrase "${profile_baseline_path}" "| Single-customer | 500 to 1,000 | 12 to 16 | 40 to 56 GB | 0.8 to 1.5 TB usable persistent storage |" "SMB baseline single-customer row"

for forbidden in "high availability" "multi-tenant deployment package" "publish the control-plane backend port directly" "requires OpenSearch" "requires n8n" "requires Shuffle" "requires ML shadow"; do
  if grep -Fqi -- "${forbidden}" "${doc_path}"; then
    echo "Forbidden single-customer deployment profile statement: ${forbidden}" >&2
    exit 1
  fi
done

echo "Single-customer deployment profile package is present and preserves the reviewed service, input, boundary, and optional-extension expectations."
