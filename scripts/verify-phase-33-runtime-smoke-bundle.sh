#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
runbook_path="${repo_root}/docs/runbook.md"
profile_path="${repo_root}/docs/deployment/single-customer-profile.md"
proxy_path="${repo_root}/proxy/nginx/conf.d-first-boot/control-plane.conf"

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

require_file "${doc_path}" "Phase 33 runtime smoke bundle"
require_file "${runbook_path}" "runbook document"
require_file "${profile_path}" "single-customer deployment profile"
require_file "${proxy_path}" "first-boot proxy config"

required_headings=(
  "# Phase 33 Runtime Smoke Bundle"
  "## 1. Purpose and Scope"
  "## 2. Preconditions"
  "## 3. Smoke Commands"
  "## 4. Handoff Checklist"
  "## 5. Evidence and Health-Review Fit"
  "## 6. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "Phase 33 runtime smoke bundle heading"
done

required_phrases=(
  "This document is the reviewed Phase 33 runtime smoke bundle for single-customer operator handoff after deployment or upgrade."
  "It is intentionally smaller than exhaustive E2E validation and proves only the post-deployment confidence path needed before normal business-hours operation resumes."
  'The bundle is anchored to `docs/deployment/single-customer-release-bundle-inventory.md`, `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `control-plane/deployment/first-boot/`.'
  "The reviewed smoke path covers startup status, readiness, protected-surface reachability, operator-console read-only sanity, queue/read-only surface sanity, and first low-risk action preconditions."
  "It does not require optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, or isolated-executor extensions to be enabled."
  "Operators must run the smoke bundle through the approved reverse proxy boundary, not by publishing the control-plane backend port directly."
  'The operator has a prepared untracked runtime env file copied from `control-plane/deployment/first-boot/bootstrap.env.sample`.'
  "The operator has the reviewed proxy authentication headers or equivalent trusted proxy session needed for protected read-only inspection without writing those secret values into the evidence record."
  "Optional extension URLs, tokens, sidecars, or packages may remain unset."
  'docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml ps'
  'docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml logs --tail=200'
  'curl -fsS http://127.0.0.1:<proxy-port>/healthz'
  'curl -fsS http://127.0.0.1:<proxy-port>/readyz'
  "For protected surfaces, substitute \`<trusted-platform-admin-proxy-auth-headers>\` or \`<trusted-operator-read-only-proxy-auth-headers>\` with the reviewed proxy session header arguments."
  "Those arguments must come from the trusted proxy or equivalent reviewed operator session, not from sample, fake, or operator-invented values."
  'X-Forwarded-Proto: https'
  'X-AegisOps-Proxy-Secret: <reviewed-proxy-secret>'
  'X-AegisOps-Proxy-Service-Account: <reviewed-proxy-service-account>'
  'X-AegisOps-Authenticated-IdP: <reviewed-identity-provider>'
  'X-AegisOps-Authenticated-Subject: <reviewed-operator-subject>'
  'X-AegisOps-Authenticated-Identity: <reviewed-operator-identity>'
  'X-AegisOps-Authenticated-Role: <reviewed-operator-role>'
  'Use a reviewed `platform_admin` role for `<trusted-platform-admin-proxy-auth-headers>` because `/runtime` is platform-admin protected.'
  'Use a reviewed `analyst`, `approver`, or `platform_admin` role for `<trusted-operator-read-only-proxy-auth-headers>` because the read-only inspection routes accept those operator roles.'
  'curl -fsS <trusted-platform-admin-proxy-auth-headers> http://127.0.0.1:<proxy-port>/runtime'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/inspect-analyst-queue'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/operator/queue'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=alerts"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-alert-detail?alert_id=<reviewed-alert-id>"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=cases"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-case-detail?case_id=<reviewed-case-id>"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=action_requests"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-action-review?action_request_id=<reviewed-action-request-id>"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-advisory-output?family=case&record_id=<reviewed-case-id>"'
  'curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/inspect-reconciliation-status'
  'Confirm the operator console can render `/operator/queue` or the configured operator-console base path with the same reviewed backend session, then keep the check read-only.'
  "Confirm the first candidate low-risk action remains in precondition review only: a reviewed alert or case is selected, an allowed low-risk action type is identified, approver ownership is known, and no action request, approval decision, delegation, executor dispatch, or reconciliation write is performed by this smoke bundle."
  "The smoke result must be attached to the deployment, upgrade, or handoff record and referenced by the next daily queue and health review."
  "The weekly platform hygiene review still owns certificate expiry, storage growth, backup drift, and restore-readiness evidence."
  "Full workflow regression, optional-extension full-path validation, broad source coverage, destructive action validation, and exhaustive E2E validation are out of scope."
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "Phase 33 runtime smoke bundle statement"
done

require_phrase "${runbook_path}" 'The Phase 33 runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md` is the reviewed post-deployment and post-upgrade handoff check for this runbook.' "runbook Phase 33 smoke bundle link"
require_phrase "${profile_path}" 'Post-upgrade smoke checks are the reviewed runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md`:' "single-customer profile Phase 33 smoke bundle link"

for proxy_path_fragment in \
  "/healthz" \
  "/readyz" \
  "/runtime" \
  "/inspect-records" \
  "/inspect-reconciliation-status" \
  "/inspect-analyst-queue" \
  "/inspect-alert-detail" \
  "/inspect-case-detail" \
  "/inspect-action-review" \
  "/inspect-advisory-output" \
  "/operator/queue"; do
  require_phrase "${proxy_path}" "location = ${proxy_path_fragment}" "first-boot proxy smoke route"
done

for forbidden in "requires OpenSearch" "requires n8n" "requires Shuffle" "requires ML shadow" "execute the low-risk action" "POST /operator/create-reviewed-action-request"; do
  if grep -Fqi -- "${forbidden}" "${doc_path}"; then
    echo "Forbidden Phase 33 runtime smoke bundle statement: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 33 runtime smoke bundle is present and preserves the reviewed handoff scope."
