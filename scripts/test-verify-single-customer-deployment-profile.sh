#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-single-customer-deployment-profile.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

For the reviewed single-customer profile, operators should plan for:
EOF

  cat <<'EOF' > "${target}/docs/smb-footprint-and-deployment-profile-baseline.md"
# SMB Footprint and Deployment-Profile Baseline

| Profile | Managed endpoints | vCPU | Memory | Primary storage |
| --- | --- | --- | --- | --- |
| Single-customer | 500 to 1,000 | 12 to 16 | 40 to 56 GB | 0.8 to 1.5 TB usable persistent storage |
EOF
}

write_valid_profile() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/single-customer-profile.md"
# Single-Customer Deployment Profile

## 1. Package Status

This document is the repo-owned single-customer deployment profile package for the reviewed Phase 33 deployment boundary.

It packages the current first-boot runtime surface into the default reviewed deployment shape for one customer environment without adding multi-customer, HA, or optional-service prerequisites.

The package is anchored to `docs/deployment/single-customer-release-bundle-inventory.md`, `docs/runbook.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `control-plane/deployment/first-boot/`.

## 2. Deployable Shape

The required services for this profile are limited to:

- AegisOps control-plane service from `control-plane/`;
- PostgreSQL for authoritative AegisOps-owned state;
- the approved reverse proxy boundary as the only reviewed user-facing ingress path; and
- the Wazuh-facing analytic-signal intake path admitted through the reviewed proxy and control-plane boundary.

The approved repo-owned startup surface remains `control-plane/deployment/first-boot/docker-compose.yml` with `control-plane/deployment/first-boot/bootstrap.env.sample` copied into an untracked runtime env file.

## 3. Approved Inputs

The approved required runtime inputs are:

- `AEGISOPS_CONTROL_PLANE_HOST`;
- `AEGISOPS_CONTROL_PLANE_PORT`;
- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`;
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE`; and
- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`.

The approved secret and boundary inputs are the PostgreSQL credential source, the Wazuh ingest shared secret source, the Wazuh ingest reverse-proxy secret source, the protected-surface reverse-proxy secret source, the protected-surface trusted proxy CIDRs, the protected-surface proxy service account, the reviewed identity-provider binding, the admin bootstrap token source, the break-glass token source, and any reviewed OpenBao address, token, token-file, and mount bindings used to resolve those secrets.

Live secret values, customer credentials, DSNs, bootstrap tokens, break-glass tokens, and environment-specific certificates must stay outside Git.

## 4. Service and Path Boundary

The reverse proxy is the only reviewed user-facing ingress path for health, readiness, runtime inspection, operator UI, and Wazuh-facing intake admission.

The control-plane backend port, PostgreSQL port, and secret backend are internal service surfaces and must not become independently published front doors.

The Wazuh-facing path is a substrate-detection intake path into AegisOps-owned records, not a direct Wazuh-to-automation or Wazuh-owned case-authority shortcut.

## 5. First-Boot to Single-Customer Delta

The single-customer profile keeps the same first-boot service boundary but changes the operator-visible operating contract from a lab rehearsal to one named customer environment.

The single-customer delta is daily business-day queue and health review, weekly platform hygiene review, daily PostgreSQL-aware backup, weekly backup review, pre-change configuration backup, monthly restore rehearsal, one planned maintenance window per month, named customer-scoped approver ownership, reviewed secret rotation, and explicit break-glass custody for customer credentials.

The delta does not add direct backend exposure, browser authority, substrate authority, direct automation shortcuts, HA topology, multi-customer coordination, or optional-service installation.

## 6. Optional Extensions

Optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, and isolated-executor paths are disabled by default, unavailable, or explicitly non-blocking unless a later reviewed package enables one for a bounded purpose.

Optional extensions must not become startup prerequisites, readiness gates, upgrade success gates, or reasons to widen the control-plane, PostgreSQL, reverse-proxy, or Wazuh-facing boundary.

## 7. Upgrade and Same-Day Rollback Rehearsal Contract

The Phase 33 upgrade rehearsal is the single-customer maintenance-window exercise that proves a reviewed repository revision can be introduced and, if needed, returned to the prior known-good state the same day.

Before the rehearsal begins, operators must confirm the daily PostgreSQL-aware backup is current, the pre-change configuration backup has been captured, the restore point for rollback is named, and the backup custody record identifies the operator or break-glass owner for the window.

The rehearsal assumes one planned business-hours maintenance window for the named customer environment, not zero-downtime rollout, HA failover, multi-region recovery, or infrastructure-vendor-specific upgrade tooling.

Rollback decision review happens before the maintenance window closes and must choose one of two recorded outcomes: keep the upgraded revision only if post-upgrade checks pass, or start same-day rollback to the selected restore point if readiness, runtime inspection, reverse-proxy boundary, or record-chain trust cannot be proven.

Post-upgrade smoke checks are the reviewed runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md`: reverse-proxy `/readyz`, reverse-proxy `/runtime`, repo-owned compose status, bounded upgrade-window logs, and operator-visible queue or alert review from the mainline surface.

Restore compatibility for the rehearsal is inherited from the Phase 32 runbook baseline: approval, evidence, execution, and reconciliation records must return cleanly from the selected PostgreSQL-aware restore point before normal operation resumes.

The rehearsal evidence must retain the maintenance-window approval, named operator, pre-change backup custody confirmation, selected restore point, before-and-after repository revisions, pre-change and post-change smoke results, rollback decision, and any post-rollback restore validation.

## 8. Day-2 Operating Shape

Day-2 operation follows the cadence in `docs/runbook.md` and `docs/smb-footprint-and-deployment-profile-baseline.md` for the reviewed single-customer profile.

Operators must preserve PostgreSQL-aware backup custody, restore validation for approval, evidence, execution, and reconciliation records, same-day rollback readiness, certificate and storage-growth hygiene review, and reviewed secret rotation evidence.

## 9. Out of Scope

HA topology, multi-customer packaging, optional-service auto-installation, vendor-specific deployment automation, direct browser authority, direct substrate authority, and endpoint, network, assistant, or ML shadow paths as deployment prerequisites are out of scope.
EOF
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add .
  git -C "${target}" commit --allow-empty -q -m "fixture"
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

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_shared_docs "${valid_repo}"
write_valid_profile "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_profile_repo="${workdir}/missing-profile"
create_repo "${missing_profile_repo}"
write_shared_docs "${missing_profile_repo}"
commit_fixture "${missing_profile_repo}"
assert_fails_with "${missing_profile_repo}" "Missing single-customer deployment profile package:"

missing_boundary_repo="${workdir}/missing-boundary"
create_repo "${missing_boundary_repo}"
write_shared_docs "${missing_boundary_repo}"
write_valid_profile "${missing_boundary_repo}"
perl -0pi -e 's/The reverse proxy is the only reviewed user-facing ingress path for health, readiness, runtime inspection, operator UI, and Wazuh-facing intake admission\.\n\n//' "${missing_boundary_repo}/docs/deployment/single-customer-profile.md"
commit_fixture "${missing_boundary_repo}"
assert_fails_with "${missing_boundary_repo}" "Missing single-customer deployment profile statement: The reverse proxy is the only reviewed user-facing ingress path"

missing_optional_default_repo="${workdir}/missing-optional-default"
create_repo "${missing_optional_default_repo}"
write_shared_docs "${missing_optional_default_repo}"
write_valid_profile "${missing_optional_default_repo}"
perl -0pi -e 's/Optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, and isolated-executor paths are disabled by default, unavailable, or explicitly non-blocking unless a later reviewed package enables one for a bounded purpose\.\n\n//' "${missing_optional_default_repo}/docs/deployment/single-customer-profile.md"
commit_fixture "${missing_optional_default_repo}"
assert_fails_with "${missing_optional_default_repo}" "Missing single-customer deployment profile statement: Optional OpenSearch, n8n, Shuffle"

missing_upgrade_rehearsal_repo="${workdir}/missing-upgrade-rehearsal"
create_repo "${missing_upgrade_rehearsal_repo}"
write_shared_docs "${missing_upgrade_rehearsal_repo}"
write_valid_profile "${missing_upgrade_rehearsal_repo}"
perl -0pi -e 's/## 7\. Upgrade and Same-Day Rollback Rehearsal Contract\n\n.*?\n\n## 8\. Day-2 Operating Shape/## 8. Day-2 Operating Shape/s' "${missing_upgrade_rehearsal_repo}/docs/deployment/single-customer-profile.md"
commit_fixture "${missing_upgrade_rehearsal_repo}"
assert_fails_with "${missing_upgrade_rehearsal_repo}" "Missing single-customer deployment profile heading: ## 7. Upgrade and Same-Day Rollback Rehearsal Contract"

forbidden_required_extension_repo="${workdir}/forbidden-required-extension"
create_repo "${forbidden_required_extension_repo}"
write_shared_docs "${forbidden_required_extension_repo}"
write_valid_profile "${forbidden_required_extension_repo}"
printf '\nThis profile requires OpenSearch before startup.\n' >> "${forbidden_required_extension_repo}/docs/deployment/single-customer-profile.md"
commit_fixture "${forbidden_required_extension_repo}"
assert_fails_with "${forbidden_required_extension_repo}" "Forbidden single-customer deployment profile statement: requires OpenSearch"

missing_runbook_map_repo="${workdir}/missing-runbook-map"
create_repo "${missing_runbook_map_repo}"
write_shared_docs "${missing_runbook_map_repo}"
write_valid_profile "${missing_runbook_map_repo}"
printf '# AegisOps Runbook\n' > "${missing_runbook_map_repo}/docs/runbook.md"
commit_fixture "${missing_runbook_map_repo}"
assert_fails_with "${missing_runbook_map_repo}" "Missing runbook single-customer profile map: For the reviewed single-customer profile, operators should plan for:"

echo "verify-single-customer-deployment-profile tests passed"
