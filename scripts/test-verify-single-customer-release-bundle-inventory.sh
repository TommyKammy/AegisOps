#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-single-customer-release-bundle-inventory.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p \
    "${target}/control-plane/deployment/first-boot" \
    "${target}/control-plane/tests/fixtures/phase37" \
    "${target}/docs/deployment" \
    "${target}/postgres/control-plane/migrations" \
    "${target}/proxy/nginx/conf.d-first-boot" \
    "${target}/scripts"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_files() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/single-customer-profile.md"
# Single-Customer Deployment Profile

Before install, upgrade, rollback, or handoff, operators must read `docs/deployment/single-customer-release-bundle-inventory.md` as the reviewed versioned inventory for the single-customer launch package, including required artefacts, release binding, image tag expectations, optional-extension exclusions, and verifier ownership.
EOF

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

Before install, upgrade, rollback, restore, or launch handoff, operators must read the Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` to confirm the reviewed single-customer package, release identifier, repository revision, image tag expectations, required artefacts, and optional-extension exclusions.
EOF

  cat <<'EOF' > "${target}/docs/deployment/runtime-smoke-bundle.md"
# Phase 33 Runtime Smoke Bundle

For the Phase 38 single-customer launch package, the smoke result is one required handoff artefact in `docs/deployment/single-customer-release-bundle-inventory.md`; it proves the release-bound first-boot surface rather than optional-extension readiness.
EOF

  cat <<'EOF' > "${target}/docs/deployment/customer-like-rehearsal-environment.md"
# Customer-Like Rehearsal Environment

The Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` treats this customer-like rehearsal preflight as required launch-gate evidence for the single-customer package.
EOF

  cat <<'EOF' > "${target}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
# Phase 37 Restore Rollback Upgrade Evidence Rehearsal

The Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` uses this rehearsal as the required release-gate evidence index for restore, rollback, upgrade, smoke, reviewed-record, and clean-state handoff.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

For the Phase 38 single-customer launch package, `docs/deployment/single-customer-release-bundle-inventory.md` is the reviewed bundle manifest that names this handoff pack as required retained evidence guidance.
EOF

  cat <<'EOF' > "${target}/control-plane/deployment/first-boot/docker-compose.yml"
name: aegisops-first-boot
# docs/deployment/single-customer-release-bundle-inventory.md
services:
  control-plane:
    image: aegisops-control-plane:first-boot
  postgres:
    image: postgres:16.4
  proxy:
    image: nginx:1.27.0
EOF

  cat <<'EOF' > "${target}/control-plane/deployment/first-boot/bootstrap.env.sample"
# docs/deployment/single-customer-release-bundle-inventory.md
AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot
EOF

  cat <<'EOF' > "${target}/control-plane/deployment/first-boot/Dockerfile"
FROM python:3.12-slim-bookworm
COPY --chown=aegisops:aegisops postgres/control-plane/migrations /opt/aegisops/postgres-migrations
EOF

  cat <<'EOF' > "${target}/control-plane/deployment/first-boot/control-plane-entrypoint.sh"
#!/usr/bin/env sh
REQUIRED_MIGRATIONS="
0001_control_plane_schema_skeleton.sql
"
EOF

  cat <<'EOF' > "${target}/proxy/nginx/nginx.conf"
events {}
EOF

  cat <<'EOF' > "${target}/proxy/nginx/conf.d-first-boot/control-plane.conf"
location = /readyz {}
EOF

  touch "${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
  touch "${target}/control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json"

  cat <<'EOF' > "${target}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/verify-customer-like-rehearsal-environment.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/run-phase-37-runtime-smoke-gate.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/verify-single-customer-release-bundle-inventory.sh"
#!/usr/bin/env bash
exit 0
EOF

  touch "${target}/scripts/test-verify-single-customer-release-bundle-inventory.sh"
  chmod +x \
    "${target}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh" \
    "${target}/scripts/verify-customer-like-rehearsal-environment.sh" \
    "${target}/scripts/run-phase-37-runtime-smoke-gate.sh" \
    "${target}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh" \
    "${target}/scripts/verify-single-customer-release-bundle-inventory.sh"
}

write_valid_manifest() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/single-customer-release-bundle-inventory.md"
# Single-Customer Release Bundle Inventory

## 1. Manifest Ownership and Version Binding

This document is the repo-owned release bundle manifest for the Phase 38 single-customer launch package after the Phase 37 launch-gate rehearsal.

It defines the reviewed shipped AegisOps package for one customer environment without creating a package-manager distribution, hosted release channel, multi-customer edition, HA topology, or optional-service install bundle.

Manifest owner: IT Operations, Information Systems Department.

Release identifier format: `aegisops-single-customer-<repository-revision>`.

Repository revision binding: the maintained release record must name the exact Git commit or reviewed tag used for the launch window.

Control-plane image tag binding: the default reviewed image tag is `aegisops-control-plane:first-boot` from `control-plane/deployment/first-boot/docker-compose.yml`; if a release retags it, the release record must name both the repository revision and the reviewed image tag.

Bundle handoff owner: the named single-customer operator or maintainer who accepts startup, smoke, restore, rollback, upgrade, and evidence handoff responsibility for the launch window.

This manifest is the first inventory operators read before install, upgrade, rollback, or handoff.

## 2. Required Launch Bundle Inventory

| Bundle entry | Owner | Source path | Release binding | Handoff relevance |
| --- | --- | --- | --- | --- |
| Release bundle manifest | IT Operations, Information Systems Department | `docs/deployment/single-customer-release-bundle-inventory.md` | Required for every `aegisops-single-customer-<repository-revision>` release record | Defines the shipped package boundary, ownership, required entries, optional exclusions, and verifier. |
| Single-customer deployment profile | IT Operations, Information Systems Department | `docs/deployment/single-customer-profile.md` | Bound to the same repository revision as the release bundle manifest | Names the reviewed one-customer operating profile, runtime inputs, boundary, optional-extension posture, upgrade, rollback, and day-2 expectations. |
| First-boot compose artefact | Platform maintainers | `control-plane/deployment/first-boot/docker-compose.yml` | Source of the reviewed control-plane, PostgreSQL, and proxy service composition for the release revision | Starts the shipped first-boot surface and exposes the expected `aegisops-control-plane:first-boot`, `postgres:16.4`, and `nginx:1.27.0` image expectations. |
| Runtime env sample reference | Platform maintainers | `control-plane/deployment/first-boot/bootstrap.env.sample` | Copied into an untracked runtime env file for the named customer environment | Defines required runtime keys and secret-source references without committing live DSNs, tokens, certificates, or customer credentials. |
| First-boot control-plane image recipe | Platform maintainers | `control-plane/deployment/first-boot/Dockerfile` | Built from the same repository revision as the release record unless a reviewed image tag is explicitly named | Defines the control-plane container build context for the release image expectation. |
| First-boot entrypoint and migration bootstrap | Platform maintainers | `control-plane/deployment/first-boot/control-plane-entrypoint.sh` | Bound to the release revision and exercised during startup, upgrade, rollback, and restore restart | Runs runtime-config validation, PostgreSQL reachability proof, and migration bootstrap before readiness is accepted. |
| Reverse-proxy artefacts | Platform maintainers | `proxy/nginx/nginx.conf`, `proxy/nginx/conf.d-first-boot/control-plane.conf` | Bound to the release revision and mounted by the first-boot compose surface | Preserves the reviewed reverse-proxy-first ingress boundary for health, readiness, runtime, protected read-only inspection, and Wazuh-facing intake. |
| Migration artefacts | Control-plane maintainers | `postgres/control-plane/migrations/` | Bound to the same repository revision and copied into the reviewed first-boot image at `/opt/aegisops/postgres-migrations` | Keeps authoritative approval, evidence, execution, reconciliation, runtime, and readiness state aligned with the shipped control-plane schema. |
| Runbook | IT Operations, Information Systems Department | `docs/runbook.md` | Required operator procedure for the release revision | Gives startup, shutdown, restore, rollback, upgrade, secret rotation, daily health review, and handoff steps. |
| Runtime smoke bundle | IT Operations, Information Systems Department | `docs/deployment/runtime-smoke-bundle.md` | Required post-deployment, post-upgrade, post-rollback, and handoff smoke reference | Proves startup status, readiness, protected read-only reachability, queue sanity, and first low-risk action preconditions through the approved boundary. |
| Customer-like rehearsal preflight | IT Operations, Information Systems Department | `docs/deployment/customer-like-rehearsal-environment.md`, `scripts/verify-customer-like-rehearsal-environment.sh` | Required Phase 37 launch-gate precursor for the release revision | Proves the disposable customer-like topology and runtime env prerequisites before the release gate is accepted. |
| Reviewed record-chain rehearsal | Control-plane maintainers | `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`, `control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json` | Required Phase 37 evidence for the release revision | Replays the reviewed alert, case, action request, approval, execution receipt, reconciliation, and handoff chain. |
| Runtime smoke gate script | IT Operations, Information Systems Department | `scripts/run-phase-37-runtime-smoke-gate.sh` | Required executable Phase 37 smoke evidence producer for the release revision | Produces retained smoke evidence and `manifest.md` for launch-gate handoff. |
| Restore, rollback, and upgrade evidence rehearsal | IT Operations, Information Systems Department | `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh` | Required release-gate evidence index for the release revision | Connects pre-change backup custody, restore validation, same-day rollback decision, post-upgrade smoke, reviewed-record evidence, and clean-state evidence. |
| Operational evidence handoff pack | IT Operations, Information Systems Department | `docs/deployment/operational-evidence-handoff-pack.md` | Required retained audit handoff reference for the release revision | Defines the compact evidence package operators retain after deployment, upgrade, rollback, restore, approval, execution, reconciliation, and launch handoff. |
| Release bundle inventory verifier | Platform maintainers | `scripts/verify-single-customer-release-bundle-inventory.sh`, `scripts/test-verify-single-customer-release-bundle-inventory.sh` | Required CI and local validation for release-bundle manifest changes | Fails closed when required bundle entries, cross-links, optional-extension exclusions, release bindings, or path-hygiene guarantees drift. |

## 3. Optional and Default-Off Extension Inventory

Optional assistant, ML shadow, endpoint evidence, optional network evidence, external ticketing, OpenSearch, n8n, Shuffle, and isolated-executor paths are subordinate or default-off items only.

They are not mainline release prerequisites, startup prerequisites, readiness gates, smoke prerequisites, upgrade success gates, rollback success gates, restore success gates, or handoff blockers for this single-customer launch package.

Operators must not infer optional-extension inclusion from repository directory presence, image availability, env sample comments, matching names, nearby notes, or external substrate health.

## 4. Release Record Requirements

- release identifier in the form `aegisops-single-customer-<repository-revision>`;
- repository revision or reviewed tag;
- control-plane image tag, including `aegisops-control-plane:first-boot` unless an explicit reviewed retag is used;
- first-boot compose path and runtime env sample path;
- reviewed migration artefact revision;
- reverse-proxy artefact revision;
- Phase 37 customer-like rehearsal preflight result;
- Phase 37 reviewed record-chain rehearsal result;
- Phase 37 runtime smoke gate manifest reference;
- restore, rollback, and upgrade release-gate manifest reference;
- clean-state validation confirming no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived a failed path.

The release record must use repo-relative paths, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<repository-revision>`.

## 5. Verification

The verifier fails closed when the release bundle manifest is missing, required launch bundle entries are absent, required release binding or handoff fields are stale, cross-links from deployment, runbook, runtime smoke, Phase 37 rehearsal, and evidence handoff surfaces are missing, optional extensions are promoted into mainline prerequisites, or publishable guidance uses workstation-local absolute paths.

## 6. Out of Scope

Package-manager distribution, hosted release channels, direct customer-private production access, zero-downtime deployment, HA, database clustering, multi-customer packaging, vendor-specific backup products, optional-service auto-installation, direct backend exposure, direct browser authority, direct substrate authority, and endpoint, network, assistant, ML, ticketing, OpenSearch, n8n, Shuffle, or isolated-executor paths as launch prerequisites are out of scope.
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
write_shared_files "${valid_repo}"
write_valid_manifest "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_manifest_repo="${workdir}/missing-manifest"
create_repo "${missing_manifest_repo}"
write_shared_files "${missing_manifest_repo}"
commit_fixture "${missing_manifest_repo}"
assert_fails_with "${missing_manifest_repo}" "Missing single-customer release bundle inventory:"

missing_smoke_entry_repo="${workdir}/missing-smoke-entry"
create_repo "${missing_smoke_entry_repo}"
write_shared_files "${missing_smoke_entry_repo}"
write_valid_manifest "${missing_smoke_entry_repo}"
perl -0pi -e 's/^\| Runtime smoke bundle .*?\n//m' "${missing_smoke_entry_repo}/docs/deployment/single-customer-release-bundle-inventory.md"
commit_fixture "${missing_smoke_entry_repo}"
assert_fails_with "${missing_smoke_entry_repo}" "Missing single-customer release bundle inventory statement: | Runtime smoke bundle"

missing_customer_like_verifier_repo="${workdir}/missing-customer-like-verifier"
create_repo "${missing_customer_like_verifier_repo}"
write_shared_files "${missing_customer_like_verifier_repo}"
write_valid_manifest "${missing_customer_like_verifier_repo}"
rm "${missing_customer_like_verifier_repo}/scripts/verify-customer-like-rehearsal-environment.sh"
commit_fixture "${missing_customer_like_verifier_repo}"
assert_fails_with "${missing_customer_like_verifier_repo}" "Missing customer-like rehearsal environment verifier:"

non_executable_customer_like_verifier_repo="${workdir}/non-executable-customer-like-verifier"
create_repo "${non_executable_customer_like_verifier_repo}"
write_shared_files "${non_executable_customer_like_verifier_repo}"
write_valid_manifest "${non_executable_customer_like_verifier_repo}"
chmod -x "${non_executable_customer_like_verifier_repo}/scripts/verify-customer-like-rehearsal-environment.sh"
commit_fixture "${non_executable_customer_like_verifier_repo}"
assert_fails_with "${non_executable_customer_like_verifier_repo}" "Missing executable bit for customer-like rehearsal environment verifier:"

missing_image_tag_repo="${workdir}/missing-image-tag"
create_repo "${missing_image_tag_repo}"
write_shared_files "${missing_image_tag_repo}"
write_valid_manifest "${missing_image_tag_repo}"
perl -0pi -e 's/image: aegisops-control-plane:first-boot/image: aegisops-control-plane:latest/' "${missing_image_tag_repo}/control-plane/deployment/first-boot/docker-compose.yml"
commit_fixture "${missing_image_tag_repo}"
assert_fails_with "${missing_image_tag_repo}" "Missing control-plane image tag expectation: image: aegisops-control-plane:first-boot"

missing_runbook_link_repo="${workdir}/missing-runbook-link"
create_repo "${missing_runbook_link_repo}"
write_shared_files "${missing_runbook_link_repo}"
write_valid_manifest "${missing_runbook_link_repo}"
printf '# AegisOps Runbook\n' > "${missing_runbook_link_repo}/docs/runbook.md"
commit_fixture "${missing_runbook_link_repo}"
assert_fails_with "${missing_runbook_link_repo}" "Missing runbook release bundle inventory link:"

optional_prereq_repo="${workdir}/optional-prereq"
create_repo "${optional_prereq_repo}"
write_shared_files "${optional_prereq_repo}"
write_valid_manifest "${optional_prereq_repo}"
printf '\nThis launch requires OpenSearch before handoff.\n' >> "${optional_prereq_repo}/docs/deployment/single-customer-release-bundle-inventory.md"
commit_fixture "${optional_prereq_repo}"
assert_fails_with "${optional_prereq_repo}" "Forbidden single-customer release bundle inventory statement: requires OpenSearch"

absolute_path_repo="${workdir}/absolute-path"
create_repo "${absolute_path_repo}"
write_shared_files "${absolute_path_repo}"
write_valid_manifest "${absolute_path_repo}"
printf '\nEvidence: /%s/%s/release-bundle/manifest.md\n' "Users" "example" >> "${absolute_path_repo}/docs/deployment/single-customer-release-bundle-inventory.md"
commit_fixture "${absolute_path_repo}"
assert_fails_with "${absolute_path_repo}" "Forbidden single-customer release bundle inventory guidance: workstation-local absolute path detected"

echo "verify-single-customer-release-bundle-inventory tests passed"
