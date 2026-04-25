#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
manifest_path="${repo_root}/docs/deployment/single-customer-release-bundle-inventory.md"
profile_path="${repo_root}/docs/deployment/single-customer-profile.md"
runbook_path="${repo_root}/docs/runbook.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
rehearsal_path="${repo_root}/docs/deployment/customer-like-rehearsal-environment.md"
customer_like_verifier_path="${repo_root}/scripts/verify-customer-like-rehearsal-environment.sh"
restore_path="${repo_root}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
compose_path="${repo_root}/control-plane/deployment/first-boot/docker-compose.yml"
env_sample_path="${repo_root}/control-plane/deployment/first-boot/bootstrap.env.sample"
dockerfile_path="${repo_root}/control-plane/deployment/first-boot/Dockerfile"
entrypoint_path="${repo_root}/control-plane/deployment/first-boot/control-plane-entrypoint.sh"
proxy_nginx_path="${repo_root}/proxy/nginx/nginx.conf"
proxy_conf_path="${repo_root}/proxy/nginx/conf.d-first-boot/control-plane.conf"
migrations_path="${repo_root}/postgres/control-plane/migrations"
record_chain_verifier_path="${repo_root}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh"
record_chain_fixture_path="${repo_root}/control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json"
runtime_smoke_gate_path="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"
restore_verifier_path="${repo_root}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"
inventory_verifier_path="${repo_root}/scripts/verify-single-customer-release-bundle-inventory.sh"
inventory_test_path="${repo_root}/scripts/test-verify-single-customer-release-bundle-inventory.sh"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_dir() {
  local path="$1"
  local description="$2"

  if [[ ! -d "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_executable() {
  local path="$1"
  local description="$2"

  require_file "${path}" "${description}"
  if [[ ! -x "${path}" ]]; then
    echo "Missing executable bit for ${description}: ${path}" >&2
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

reject_workstation_paths() {
  local description="$1"
  shift

  local macos_home_pattern linux_home_pattern windows_home_pattern workstation_local_path_pattern
  macos_home_pattern='/'"Users"'/[^[:space:])>]+'
  linux_home_pattern='/'"home"'/[^[:space:])>]+'
  windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
  workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

  if grep -Eq "${workstation_local_path_pattern}" "$@"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi
}

require_file "${manifest_path}" "single-customer release bundle inventory"
require_file "${profile_path}" "single-customer deployment profile"
require_file "${runbook_path}" "runbook document"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${rehearsal_path}" "customer-like rehearsal environment"
require_executable "${customer_like_verifier_path}" "customer-like rehearsal environment verifier"
require_file "${restore_path}" "restore rollback upgrade evidence rehearsal"
require_file "${handoff_path}" "operational evidence handoff pack"
require_file "${compose_path}" "first-boot compose artefact"
require_file "${env_sample_path}" "runtime env sample"
require_file "${dockerfile_path}" "first-boot Dockerfile"
require_file "${entrypoint_path}" "first-boot entrypoint"
require_file "${proxy_nginx_path}" "reverse-proxy nginx config"
require_file "${proxy_conf_path}" "first-boot reverse-proxy route config"
require_dir "${migrations_path}" "control-plane migration artefacts"
require_executable "${record_chain_verifier_path}" "Phase 37 reviewed record-chain rehearsal verifier"
require_file "${record_chain_fixture_path}" "Phase 37 reviewed record-chain fixture"
require_executable "${runtime_smoke_gate_path}" "Phase 37 runtime smoke gate"
require_executable "${restore_verifier_path}" "Phase 37 restore rollback upgrade evidence verifier"
require_executable "${inventory_verifier_path}" "single-customer release bundle inventory verifier"
require_file "${inventory_test_path}" "single-customer release bundle inventory verifier tests"

required_headings=(
  "# Single-Customer Release Bundle Inventory"
  "## 1. Manifest Ownership and Version Binding"
  "## 2. Required Launch Bundle Inventory"
  "## 3. Optional and Default-Off Extension Inventory"
  "## 4. Release Record Requirements"
  "## 5. Verification"
  "## 6. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${manifest_path}" "${heading}" "single-customer release bundle inventory heading"
done

required_manifest_phrases=(
  "This document is the repo-owned release bundle manifest for the Phase 38 single-customer launch package after the Phase 37 launch-gate rehearsal."
  "It defines the reviewed shipped AegisOps package for one customer environment without creating a package-manager distribution, hosted release channel, multi-customer edition, HA topology, or optional-service install bundle."
  "Manifest owner: IT Operations, Information Systems Department."
  'Release identifier format: `aegisops-single-customer-<repository-revision>`.'
  "Repository revision binding: the maintained release record must name the exact Git commit or reviewed tag used for the launch window."
  'Control-plane image tag binding: the default reviewed image tag is `aegisops-control-plane:first-boot` from `control-plane/deployment/first-boot/docker-compose.yml`; if a release retags it, the release record must name both the repository revision and the reviewed image tag.'
  "Bundle handoff owner: the named single-customer operator or maintainer who accepts startup, smoke, restore, rollback, upgrade, and evidence handoff responsibility for the launch window."
  "This manifest is the first inventory operators read before install, upgrade, rollback, or handoff."
  '| Release bundle manifest | IT Operations, Information Systems Department | `docs/deployment/single-customer-release-bundle-inventory.md` | Required for every `aegisops-single-customer-<repository-revision>` release record |'
  '| Single-customer deployment profile | IT Operations, Information Systems Department | `docs/deployment/single-customer-profile.md` | Bound to the same repository revision as the release bundle manifest |'
  '| First-boot compose artefact | Platform maintainers | `control-plane/deployment/first-boot/docker-compose.yml` | Source of the reviewed control-plane, PostgreSQL, and proxy service composition for the release revision |'
  '| Runtime env sample reference | Platform maintainers | `control-plane/deployment/first-boot/bootstrap.env.sample` | Copied into an untracked runtime env file for the named customer environment |'
  '| First-boot control-plane image recipe | Platform maintainers | `control-plane/deployment/first-boot/Dockerfile` | Built from the same repository revision as the release record unless a reviewed image tag is explicitly named |'
  '| First-boot entrypoint and migration bootstrap | Platform maintainers | `control-plane/deployment/first-boot/control-plane-entrypoint.sh` | Bound to the release revision and exercised during startup, upgrade, rollback, and restore restart |'
  '| Reverse-proxy artefacts | Platform maintainers | `proxy/nginx/nginx.conf`, `proxy/nginx/conf.d-first-boot/control-plane.conf` | Bound to the release revision and mounted by the first-boot compose surface |'
  '| Migration artefacts | Control-plane maintainers | `postgres/control-plane/migrations/` | Bound to the same repository revision and copied into the reviewed first-boot image at `/opt/aegisops/postgres-migrations` |'
  '| Runbook | IT Operations, Information Systems Department | `docs/runbook.md` | Required operator procedure for the release revision |'
  '| Runtime smoke bundle | IT Operations, Information Systems Department | `docs/deployment/runtime-smoke-bundle.md` | Required post-deployment, post-upgrade, post-rollback, and handoff smoke reference |'
  '| Customer-like rehearsal preflight | IT Operations, Information Systems Department | `docs/deployment/customer-like-rehearsal-environment.md`, `scripts/verify-customer-like-rehearsal-environment.sh` | Required Phase 37 launch-gate precursor for the release revision |'
  '| Reviewed record-chain rehearsal | Control-plane maintainers | `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`, `control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json` | Required Phase 37 evidence for the release revision |'
  '| Runtime smoke gate script | IT Operations, Information Systems Department | `scripts/run-phase-37-runtime-smoke-gate.sh` | Required executable Phase 37 smoke evidence producer for the release revision |'
  '| Restore, rollback, and upgrade evidence rehearsal | IT Operations, Information Systems Department | `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh` | Required release-gate evidence index for the release revision |'
  '| Operational evidence handoff pack | IT Operations, Information Systems Department | `docs/deployment/operational-evidence-handoff-pack.md` | Required retained audit handoff reference for the release revision |'
  '| Release bundle inventory verifier | Platform maintainers | `scripts/verify-single-customer-release-bundle-inventory.sh`, `scripts/test-verify-single-customer-release-bundle-inventory.sh` | Required CI and local validation for release-bundle manifest changes |'
  "Optional assistant, ML shadow, endpoint evidence, optional network evidence, external ticketing, OpenSearch, n8n, Shuffle, and isolated-executor paths are subordinate or default-off items only."
  "They are not mainline release prerequisites, startup prerequisites, readiness gates, smoke prerequisites, upgrade success gates, rollback success gates, restore success gates, or handoff blockers for this single-customer launch package."
  "Operators must not infer optional-extension inclusion from repository directory presence, image availability, env sample comments, matching names, nearby notes, or external substrate health."
  '- release identifier in the form `aegisops-single-customer-<repository-revision>`;'
  "- repository revision or reviewed tag;"
  '- control-plane image tag, including `aegisops-control-plane:first-boot` unless an explicit reviewed retag is used;'
  "- first-boot compose path and runtime env sample path;"
  "- reviewed migration artefact revision;"
  "- reverse-proxy artefact revision;"
  "- Phase 37 customer-like rehearsal preflight result;"
  "- Phase 37 reviewed record-chain rehearsal result;"
  "- Phase 37 runtime smoke gate manifest reference;"
  "- restore, rollback, and upgrade release-gate manifest reference;"
  "- clean-state validation confirming no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived a failed path."
  'The release record must use repo-relative paths, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<repository-revision>`.'
  "The verifier fails closed when the release bundle manifest is missing, required launch bundle entries are absent, required release binding or handoff fields are stale, cross-links from deployment, runbook, runtime smoke, Phase 37 rehearsal, and evidence handoff surfaces are missing, optional extensions are promoted into mainline prerequisites, or publishable guidance uses workstation-local absolute paths."
  "Package-manager distribution, hosted release channels, direct customer-private production access, zero-downtime deployment, HA, database clustering, multi-customer packaging, vendor-specific backup products, optional-service auto-installation, direct backend exposure, direct browser authority, direct substrate authority, and endpoint, network, assistant, ML, ticketing, OpenSearch, n8n, Shuffle, or isolated-executor paths as launch prerequisites are out of scope."
)

for phrase in "${required_manifest_phrases[@]}"; do
  require_phrase "${manifest_path}" "${phrase}" "single-customer release bundle inventory statement"
done

require_phrase "${profile_path}" 'Before install, upgrade, rollback, or handoff, operators must read `docs/deployment/single-customer-release-bundle-inventory.md` as the reviewed versioned inventory for the single-customer launch package, including required artefacts, release binding, image tag expectations, optional-extension exclusions, and verifier ownership.' "single-customer profile release bundle inventory link"
require_phrase "${runbook_path}" 'Before install, upgrade, rollback, restore, or launch handoff, operators must read the Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` to confirm the reviewed single-customer package, release identifier, repository revision, image tag expectations, required artefacts, and optional-extension exclusions.' "runbook release bundle inventory link"
require_phrase "${smoke_path}" 'For the Phase 38 single-customer launch package, the smoke result is one required handoff artefact in `docs/deployment/single-customer-release-bundle-inventory.md`; it proves the release-bound first-boot surface rather than optional-extension readiness.' "runtime smoke release bundle inventory link"
require_phrase "${rehearsal_path}" 'The Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` treats this customer-like rehearsal preflight as required launch-gate evidence for the single-customer package.' "customer-like rehearsal release bundle inventory link"
require_phrase "${restore_path}" 'The Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` uses this rehearsal as the required release-gate evidence index for restore, rollback, upgrade, smoke, reviewed-record, and clean-state handoff.' "restore rollback upgrade release bundle inventory link"
require_phrase "${handoff_path}" 'For the Phase 38 single-customer launch package, `docs/deployment/single-customer-release-bundle-inventory.md` is the reviewed bundle manifest that names this handoff pack as required retained evidence guidance.' "operational evidence handoff release bundle inventory link"
require_phrase "${compose_path}" "docs/deployment/single-customer-release-bundle-inventory.md" "first-boot compose release bundle inventory link"
require_phrase "${env_sample_path}" "docs/deployment/single-customer-release-bundle-inventory.md" "runtime env sample release bundle inventory link"
require_phrase "${compose_path}" "image: aegisops-control-plane:first-boot" "control-plane image tag expectation"
require_phrase "${compose_path}" "image: postgres:16.4" "PostgreSQL image tag expectation"
require_phrase "${compose_path}" "image: nginx:1.27.0" "reverse-proxy image tag expectation"
require_phrase "${dockerfile_path}" "COPY --chown=aegisops:aegisops postgres/control-plane/migrations /opt/aegisops/postgres-migrations" "migration artefact image binding"
require_phrase "${entrypoint_path}" "REQUIRED_MIGRATIONS=" "first-boot migration bootstrap list"

for forbidden in \
  "requires OpenSearch" \
  "requires n8n" \
  "requires Shuffle" \
  "requires ML shadow" \
  "optional extensions are required" \
  "optional extensions are mainline release prerequisites" \
  "endpoint evidence is required for launch" \
  "network evidence is required for launch" \
  "assistant is required for launch" \
  "external ticketing is required for launch"; do
  if grep -Fqi -- "${forbidden}" "${manifest_path}"; then
    echo "Forbidden single-customer release bundle inventory statement: ${forbidden}" >&2
    exit 1
  fi
done

reject_workstation_paths "single-customer release bundle inventory guidance" \
  "${manifest_path}" \
  "${profile_path}" \
  "${runbook_path}" \
  "${smoke_path}" \
  "${rehearsal_path}" \
  "${restore_path}" \
  "${handoff_path}" \
  "${compose_path}" \
  "${env_sample_path}"

echo "Single-customer release bundle inventory is present, cross-linked, and fail-closed."
