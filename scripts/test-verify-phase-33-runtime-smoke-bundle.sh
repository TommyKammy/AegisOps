#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-33-runtime-smoke-bundle.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment" "${target}/proxy/nginx/conf.d-first-boot"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

The Phase 33 runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md` is the reviewed post-deployment and post-upgrade handoff check for this runbook.
EOF

  cat <<'EOF' > "${target}/docs/deployment/single-customer-profile.md"
# Single-Customer Deployment Profile

Post-upgrade smoke checks are the reviewed runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md`: reverse-proxy `/readyz`, reverse-proxy `/runtime`, repo-owned compose status, bounded upgrade-window logs, and operator-visible queue or alert review from the mainline surface.
EOF

  cat <<'EOF' > "${target}/proxy/nginx/conf.d-first-boot/control-plane.conf"
location = /healthz {
  proxy_pass http://aegisops_control_plane/healthz;
}
location = /readyz {
  proxy_pass http://aegisops_control_plane/readyz;
}
location = /runtime {
  proxy_pass http://aegisops_control_plane/runtime;
}
location = /inspect-records {
  proxy_pass http://aegisops_control_plane/inspect-records$is_args$args;
}
location = /inspect-reconciliation-status {
  proxy_pass http://aegisops_control_plane/inspect-reconciliation-status;
}
location = /inspect-analyst-queue {
  limit_except GET { deny all; }
  proxy_pass http://aegisops_control_plane/inspect-analyst-queue$is_args$args;
}
location = /inspect-alert-detail {
  limit_except GET { deny all; }
  proxy_pass http://aegisops_control_plane/inspect-alert-detail$is_args$args;
}
location = /inspect-case-detail {
  limit_except GET { deny all; }
  proxy_pass http://aegisops_control_plane/inspect-case-detail$is_args$args;
}
location = /inspect-action-review {
  limit_except GET { deny all; }
  proxy_pass http://aegisops_control_plane/inspect-action-review$is_args$args;
}
location = /inspect-advisory-output {
  limit_except GET { deny all; }
  proxy_pass http://aegisops_control_plane/inspect-advisory-output$is_args$args;
}
location = /operator/queue {
  limit_except GET { deny all; }
  proxy_pass http://aegisops_control_plane/inspect-analyst-queue$is_args$args;
}
EOF
}

write_valid_bundle() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/runtime-smoke-bundle.md"
# Phase 33 Runtime Smoke Bundle

## 1. Purpose and Scope

This document is the reviewed Phase 33 runtime smoke bundle for single-customer operator handoff after deployment or upgrade.

It is intentionally smaller than exhaustive E2E validation and proves only the post-deployment confidence path needed before normal business-hours operation resumes.

The bundle is anchored to `docs/deployment/single-customer-release-bundle-inventory.md`, `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `control-plane/deployment/first-boot/`.

The reviewed smoke path covers startup status, readiness, protected-surface reachability, operator-console read-only sanity, queue/read-only surface sanity, and first low-risk action preconditions.

It does not require optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, or isolated-executor extensions to be enabled.

Operators must run the smoke bundle through the approved reverse proxy boundary, not by publishing the control-plane backend port directly.

## 2. Preconditions

The operator has a prepared untracked runtime env file copied from `control-plane/deployment/first-boot/bootstrap.env.sample`.

The operator has the reviewed proxy authentication headers or equivalent trusted proxy session needed for protected read-only inspection without writing those secret values into the evidence record.

Optional extension URLs, tokens, sidecars, or packages may remain unset.

## 3. Smoke Commands

Use `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml ps`.

Use `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml logs --tail=200`.

Use `curl -fsS http://127.0.0.1:<proxy-port>/healthz`.

Use `curl -fsS http://127.0.0.1:<proxy-port>/readyz`.

For protected surfaces, substitute `<trusted-platform-admin-proxy-auth-headers>` or `<trusted-operator-read-only-proxy-auth-headers>` with the reviewed proxy session header arguments.

Those arguments must come from the trusted proxy or equivalent reviewed operator session, not from sample, fake, or operator-invented values.

Use `X-Forwarded-Proto: https`.

Use `X-AegisOps-Proxy-Secret: <reviewed-proxy-secret>`.

Use `X-AegisOps-Proxy-Service-Account: <reviewed-proxy-service-account>`.

Use `X-AegisOps-Authenticated-IdP: <reviewed-identity-provider>`.

Use `X-AegisOps-Authenticated-Subject: <reviewed-operator-subject>`.

Use `X-AegisOps-Authenticated-Identity: <reviewed-operator-identity>`.

Use `X-AegisOps-Authenticated-Role: <reviewed-operator-role>`.

Use a reviewed `platform_admin` role for `<trusted-platform-admin-proxy-auth-headers>` because `/runtime` is platform-admin protected.

Use a reviewed `analyst`, `approver`, or `platform_admin` role for `<trusted-operator-read-only-proxy-auth-headers>` because the read-only inspection routes accept those operator roles.

Use `curl -fsS <trusted-platform-admin-proxy-auth-headers> http://127.0.0.1:<proxy-port>/runtime`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/inspect-analyst-queue`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/operator/queue`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=alerts"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-alert-detail?alert_id=<reviewed-alert-id>"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=cases"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-case-detail?case_id=<reviewed-case-id>"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=action_requests"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-action-review?action_request_id=<reviewed-action-request-id>"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-advisory-output?family=case&record_id=<reviewed-case-id>"`.

Use `curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/inspect-reconciliation-status`.

## 4. Handoff Checklist

Confirm the operator console can render `/operator/queue` or the configured operator-console base path with the same reviewed backend session, then keep the check read-only.

Confirm the first candidate low-risk action remains in precondition review only: a reviewed alert or case is selected, an allowed low-risk action type is identified, approver ownership is known, and no action request, approval decision, delegation, executor dispatch, or reconciliation write is performed by this smoke bundle.

## 5. Evidence and Health-Review Fit

The smoke result must be attached to the deployment, upgrade, or handoff record and referenced by the next daily queue and health review.

The weekly platform hygiene review still owns certificate expiry, storage growth, backup drift, and restore-readiness evidence.

## 6. Out of Scope

Full workflow regression, optional-extension full-path validation, broad source coverage, destructive action validation, and exhaustive E2E validation are out of scope.
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
write_valid_bundle "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_bundle_repo="${workdir}/missing-bundle"
create_repo "${missing_bundle_repo}"
write_shared_docs "${missing_bundle_repo}"
commit_fixture "${missing_bundle_repo}"
assert_fails_with "${missing_bundle_repo}" "Missing Phase 33 runtime smoke bundle:"

missing_readonly_repo="${workdir}/missing-readonly"
create_repo "${missing_readonly_repo}"
write_shared_docs "${missing_readonly_repo}"
write_valid_bundle "${missing_readonly_repo}"
perl -0pi -e 's/Confirm the operator console can render `\/operator\/queue` or the configured operator-console base path with the same reviewed backend session, then keep the check read-only\.\n\n//' "${missing_readonly_repo}/docs/deployment/runtime-smoke-bundle.md"
commit_fixture "${missing_readonly_repo}"
assert_fails_with "${missing_readonly_repo}" "Missing Phase 33 runtime smoke bundle statement: Confirm the operator console can render"

missing_optional_scope_repo="${workdir}/missing-optional-scope"
create_repo "${missing_optional_scope_repo}"
write_shared_docs "${missing_optional_scope_repo}"
write_valid_bundle "${missing_optional_scope_repo}"
perl -0pi -e 's/It does not require optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, or isolated-executor extensions to be enabled\.\n\n//' "${missing_optional_scope_repo}/docs/deployment/runtime-smoke-bundle.md"
commit_fixture "${missing_optional_scope_repo}"
assert_fails_with "${missing_optional_scope_repo}" "Missing Phase 33 runtime smoke bundle statement: It does not require optional OpenSearch"

missing_protected_auth_repo="${workdir}/missing-protected-auth"
create_repo "${missing_protected_auth_repo}"
write_shared_docs "${missing_protected_auth_repo}"
write_valid_bundle "${missing_protected_auth_repo}"
perl -0pi -e 's/curl -fsS <trusted-platform-admin-proxy-auth-headers> http:\/\/127\.0\.0\.1:<proxy-port>\/runtime/curl -fsS http:\/\/127.0.0.1:<proxy-port>\/runtime/' "${missing_protected_auth_repo}/docs/deployment/runtime-smoke-bundle.md"
commit_fixture "${missing_protected_auth_repo}"
assert_fails_with "${missing_protected_auth_repo}" "Missing Phase 33 runtime smoke bundle statement: curl -fsS <trusted-platform-admin-proxy-auth-headers> http://127.0.0.1:<proxy-port>/runtime"

missing_runbook_link_repo="${workdir}/missing-runbook-link"
create_repo "${missing_runbook_link_repo}"
write_shared_docs "${missing_runbook_link_repo}"
write_valid_bundle "${missing_runbook_link_repo}"
printf '# AegisOps Runbook\n' > "${missing_runbook_link_repo}/docs/runbook.md"
commit_fixture "${missing_runbook_link_repo}"
assert_fails_with "${missing_runbook_link_repo}" "Missing runbook Phase 33 smoke bundle link:"

missing_profile_link_repo="${workdir}/missing-profile-link"
create_repo "${missing_profile_link_repo}"
write_shared_docs "${missing_profile_link_repo}"
write_valid_bundle "${missing_profile_link_repo}"
printf '# Single-Customer Deployment Profile\n' > "${missing_profile_link_repo}/docs/deployment/single-customer-profile.md"
commit_fixture "${missing_profile_link_repo}"
assert_fails_with "${missing_profile_link_repo}" "Missing single-customer profile Phase 33 smoke bundle link:"

missing_proxy_route_repo="${workdir}/missing-proxy-route"
create_repo "${missing_proxy_route_repo}"
write_shared_docs "${missing_proxy_route_repo}"
write_valid_bundle "${missing_proxy_route_repo}"
perl -0pi -e 's/location = \/inspect-reconciliation-status \{\n  proxy_pass http:\/\/aegisops_control_plane\/inspect-reconciliation-status;\n\}\n//' "${missing_proxy_route_repo}/proxy/nginx/conf.d-first-boot/control-plane.conf"
commit_fixture "${missing_proxy_route_repo}"
assert_fails_with "${missing_proxy_route_repo}" "Missing first-boot proxy smoke route: location = /inspect-reconciliation-status"

miswired_proxy_route_repo="${workdir}/miswired-proxy-route"
create_repo "${miswired_proxy_route_repo}"
write_shared_docs "${miswired_proxy_route_repo}"
write_valid_bundle "${miswired_proxy_route_repo}"
perl -0pi -e 's/proxy_pass http:\/\/aegisops_control_plane\/inspect-action-review\$is_args\$args;/proxy_pass http:\/\/aegisops_control_plane\/inspect-records\$is_args\$args;/' "${miswired_proxy_route_repo}/proxy/nginx/conf.d-first-boot/control-plane.conf"
commit_fixture "${miswired_proxy_route_repo}"
assert_fails_with "${miswired_proxy_route_repo}" 'Missing first-boot proxy smoke route: proxy_pass http://aegisops_control_plane/inspect-action-review$is_args$args;'

forbidden_low_risk_write_repo="${workdir}/forbidden-low-risk-write"
create_repo "${forbidden_low_risk_write_repo}"
write_shared_docs "${forbidden_low_risk_write_repo}"
write_valid_bundle "${forbidden_low_risk_write_repo}"
printf '\nOperators may execute the low-risk action after this smoke passes.\n' >> "${forbidden_low_risk_write_repo}/docs/deployment/runtime-smoke-bundle.md"
commit_fixture "${forbidden_low_risk_write_repo}"
assert_fails_with "${forbidden_low_risk_write_repo}" "Forbidden Phase 33 runtime smoke bundle statement: execute the low-risk action"

echo "verify-phase-33-runtime-smoke-bundle tests passed"
