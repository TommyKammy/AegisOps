#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-67-1-colima-integration-lab.sh"
workdir="$(mktemp -d)"
trap 'chmod -R u+w "${workdir}" 2>/dev/null || true; rm -rf "${workdir}"' EXIT

copy_fixture() {
  local target="$1"
  mkdir -p \
    "${target}/scripts" \
    "${target}/control-plane/deployment" \
    "${target}/control-plane/deployment/first-boot" \
    "${target}/.github/workflows"
  cp -R "${repo_root}/control-plane/deployment/phase-67-integration-lab" \
    "${target}/control-plane/deployment/"
  cp "${repo_root}/control-plane/deployment/first-boot/Dockerfile" \
    "${target}/control-plane/deployment/first-boot/Dockerfile"
  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/control-plane/README.md" "${target}/control-plane/README.md"
  cp "${repo_root}/.gitignore" "${target}/.gitignore"
  cp "${repo_root}/.dockerignore" "${target}/.dockerignore"
  cp "${repo_root}/.github/workflows/ci.yml" "${target}/.github/workflows/ci.yml"
}

assert_passes() {
  local target="$1"
  if ! bash "${verifier}" "${target}" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    cat "${workdir}/stderr" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"
  if bash "${verifier}" "${target}" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    echo "Expected verifier failure for ${target}" >&2
    exit 1
  fi
  grep -F -- "${expected}" "${workdir}/stderr" >/dev/null || {
    echo "Expected verifier stderr to contain: ${expected}" >&2
    cat "${workdir}/stderr" >&2
    exit 1
  }
}

valid="${workdir}/valid"
copy_fixture "${valid}"
assert_passes "${valid}"

context_mutation="${workdir}/context-mutation"
copy_fixture "${context_mutation}"
printf '\ndocker context use default\n' >>"${context_mutation}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with "${context_mutation}" 'must not mutate the global Docker context'

socket_mount="${workdir}/socket-mount"
copy_fixture "${socket_mount}"
printf '\n# /var/run/docker.sock:/var/run/docker.sock\n' >>"${socket_mount}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${socket_mount}" 'must not mount the Docker socket'

destructive_cleanup="${workdir}/destructive-cleanup"
copy_fixture "${destructive_cleanup}"
printf '\n# accidental cleanup option: --volumes\n' \
  >>"${destructive_cleanup}/control-plane/deployment/phase-67-integration-lab/down.sh"
assert_fails_with "${destructive_cleanup}" 'must preserve named volumes'

emulation_drift="${workdir}/emulation-drift"
copy_fixture "${emulation_drift}"
perl -0pi -e 's/AEGISOPS_LAB_ALLOW_EMULATION=no/AEGISOPS_LAB_ALLOW_EMULATION=yes/' \
  "${emulation_drift}/control-plane/deployment/phase-67-integration-lab/bootstrap.env.sample"
assert_fails_with "${emulation_drift}" 'AEGISOPS_LAB_ALLOW_EMULATION=no'

latest_image="${workdir}/latest-image"
copy_fixture "${latest_image}"
printf '\n# image: example.invalid/lab:latest\n' >>"${latest_image}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${latest_image}" 'must not use latest tags'

unpinned_image="${workdir}/unpinned-image"
copy_fixture "${unpinned_image}"
perl -0pi -e 's#postgres:16\.4\@sha256:[0-9a-f]{64}#postgres:16.4\@sha256:unpinned#' \
  "${unpinned_image}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${unpinned_image}" 'must pin every external Compose image by digest'

migration_proof_drift="${workdir}/migration-proof-drift"
copy_fixture "${migration_proof_drift}"
perl -0pi -e 's/prove_migration_state/prove_removed_migration_state/g' \
  "${migration_proof_drift}/control-plane/deployment/phase-67-integration-lab/control-plane-entrypoint.sh"
assert_fails_with "${migration_proof_drift}" 'prove_migration_state'

migration_definition_drift="${workdir}/migration-definition-drift"
copy_fixture "${migration_definition_drift}"
perl -0pi -e 's/pg_get_constraintdef\(constraint_record\.oid, true\)/removed_constraint_definition/g' \
  "${migration_definition_drift}/control-plane/deployment/phase-67-integration-lab/control-plane-entrypoint.sh"
assert_fails_with "${migration_definition_drift}" 'pg_get_constraintdef(constraint_record.oid, true)'

scope_narrowing_drift="${workdir}/scope-narrowing-drift"
copy_fixture "${scope_narrowing_drift}"
perl -0pi -e 's/assert_no_running_excluded_services/assert_removed_running_excluded_services/g' \
  "${scope_narrowing_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh" \
  "${scope_narrowing_drift}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with "${scope_narrowing_drift}" 'assert_no_running_excluded_services'

wazuh_upstream_tls_drift="${workdir}/wazuh-upstream-tls-drift"
copy_fixture "${wazuh_upstream_tls_drift}"
perl -0pi -e 's/proxy_ssl_verify on;/proxy_ssl_verify off;/' \
  "${wazuh_upstream_tls_drift}/control-plane/deployment/phase-67-integration-lab/config/control-plane.conf"
assert_fails_with "${wazuh_upstream_tls_drift}" 'proxy_ssl_verify on;'

certificate_renewal_drift="${workdir}/certificate-renewal-drift"
copy_fixture "${certificate_renewal_drift}"
perl -0pi -e 's/openssl x509 -checkend 604800/openssl x509 -noout/g' \
  "${certificate_renewal_drift}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with "${certificate_renewal_drift}" 'openssl x509 -checkend 604800'

network_host_drift="${workdir}/network-host-drift"
copy_fixture "${network_host_drift}"
perl -0pi -e 's/requested\.network_address/requested.network_marker/g' \
  "${network_host_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${network_host_drift}" 'requested.network_address'

duplicate_port_drift="${workdir}/duplicate-port-drift"
copy_fixture "${duplicate_port_drift}"
perl -0pi -e 's/assert_unique_selected_ports/assert_removed_unique_selected_ports/g' \
  "${duplicate_port_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh" \
  "${duplicate_port_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${duplicate_port_drift}" 'assert_unique_selected_ports'

runtime_quoting_drift="${workdir}/runtime-quoting-drift"
copy_fixture "${runtime_quoting_drift}"
perl -0pi -e 's/write_runtime_env_assignment/write_removed_runtime_env_assignment/g' \
  "${runtime_quoting_drift}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with "${runtime_quoting_drift}" 'write_runtime_env_assignment'

bounded_logs_drift="${workdir}/bounded-logs-drift"
copy_fixture "${bounded_logs_drift}"
perl -0pi -e 's/for log_argument in "\$\@"; do/for log_argument in "--follow"; do/' \
  "${bounded_logs_drift}/control-plane/deployment/phase-67-integration-lab/logs.sh"
assert_fails_with "${bounded_logs_drift}" 'for log_argument in "$@"; do'

wazuh_checkout_drift="${workdir}/wazuh-checkout-drift"
copy_fixture "${wazuh_checkout_drift}"
perl -0pi -e 's/diff --quiet HEAD --/diff --quiet HEAD^ --/' \
  "${wazuh_checkout_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh"
assert_fails_with "${wazuh_checkout_drift}" 'diff --quiet HEAD --'

teardown_recovery_drift="${workdir}/teardown-recovery-drift"
copy_fixture "${teardown_recovery_drift}"
perl -0pi -e 's/require_runtime_configuration/require_runtime_environment/' \
  "${teardown_recovery_drift}/control-plane/deployment/phase-67-integration-lab/down.sh"
assert_fails_with "${teardown_recovery_drift}" 'require_runtime_configuration'

proxy_recreate_drift="${workdir}/proxy-recreate-drift"
copy_fixture "${proxy_recreate_drift}"
perl -0pi -e 's/proxy-certificate-recreate-required/proxy-certificate-recreate-removed/g' \
  "${proxy_recreate_drift}/control-plane/deployment/phase-67-integration-lab/init.sh" \
  "${proxy_recreate_drift}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with "${proxy_recreate_drift}" 'proxy-certificate-recreate-required'

proxy_deleted_pair_drift="${workdir}/proxy-deleted-pair-drift"
copy_fixture "${proxy_deleted_pair_drift}"
perl -0pi -e 's/\$\{runtime_previously_initialized\}" == "true/\${runtime_previously_initialized}" == "false/g' \
  "${proxy_deleted_pair_drift}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with "${proxy_deleted_pair_drift}" '"${runtime_previously_initialized}" == "true"'

wazuh_certificate_drift="${workdir}/wazuh-certificate-drift"
copy_fixture "${wazuh_certificate_drift}"
perl -0pi -e 's/validate_wazuh_certificate_bundle/validate_removed_wazuh_certificate_bundle/g' \
  "${wazuh_certificate_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh" \
  "${wazuh_certificate_drift}/control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh"
assert_fails_with "${wazuh_certificate_drift}" 'validate_wazuh_certificate_bundle'

wazuh_marker_order_drift="${workdir}/wazuh-marker-order-drift"
copy_fixture "${wazuh_marker_order_drift}"
perl -0pi -e 's/  mark_wazuh_recreation_required\n  docker_lab cp/  docker_lab cp/' \
  "${wazuh_marker_order_drift}/control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh"
assert_fails_with "${wazuh_marker_order_drift}" 'mark_wazuh_recreation_required'

wazuh_start_checkout_drift="${workdir}/wazuh-start-checkout-drift"
copy_fixture "${wazuh_start_checkout_drift}"
perl -0pi -e 's/assert_reviewed_wazuh_checkout/assert_removed_wazuh_checkout/g' \
  "${wazuh_start_checkout_drift}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with "${wazuh_start_checkout_drift}" 'assert_reviewed_wazuh_checkout'

wazuh_digest_drift="${workdir}/wazuh-digest-drift"
copy_fixture "${wazuh_digest_drift}"
perl -0pi -e 's/assert_reviewed_file_digest/assert_removed_file_digest/g' \
  "${wazuh_digest_drift}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with "${wazuh_digest_drift}" 'assert_reviewed_file_digest'

status_evidence_drift="${workdir}/status-evidence-drift"
copy_fixture "${status_evidence_drift}"
perl -0pi -e 's/scope="full"/scope="invalid"/' \
  "${status_evidence_drift}/control-plane/deployment/phase-67-integration-lab/status.sh"
assert_fails_with "${status_evidence_drift}" 'scope="full"'

selected_address_drift="${workdir}/selected-address-drift"
copy_fixture "${selected_address_drift}"
perl -0pi -e 's/selected_address_names/scope_address_list/g' \
  "${selected_address_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh" \
  "${selected_address_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${selected_address_drift}" 'selected_address_names'

published_port_evidence_drift="${workdir}/published-port-evidence-drift"
copy_fixture "${published_port_evidence_drift}"
perl -0pi -e 's/PASS published_ports=\$\{published_ports\}/PASS published_ports=all/' \
  "${published_port_evidence_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${published_port_evidence_drift}" 'record "PASS published_ports=${published_ports}"'

reviewed_pin_drift="${workdir}/reviewed-pin-drift"
copy_fixture "${reviewed_pin_drift}"
perl -0pi -e 's/assert_reviewed_lab_pins/assert_removed_reviewed_lab_pins/g' \
  "${reviewed_pin_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh" \
  "${reviewed_pin_drift}/control-plane/deployment/phase-67-integration-lab/init.sh" \
  "${reviewed_pin_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh" \
  "${reviewed_pin_drift}/control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh"
assert_fails_with "${reviewed_pin_drift}" 'assert_reviewed_lab_pins'

architecture_drift="${workdir}/architecture-drift"
copy_fixture "${architecture_drift}"
perl -0pi -e 's/ARM64 service execution is unavailable/ARM64 service execution unchecked/' \
  "${architecture_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${architecture_drift}" 'ARM64 service execution is unavailable'

evidence_collision_drift="${workdir}/evidence-collision-drift"
copy_fixture "${evidence_collision_drift}"
perl -0pi -e 's/mktemp/printf/g' \
  "${evidence_collision_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${evidence_collision_drift}" 'mktemp "${evidence_dir}/preflight-${scope}-'

credential_guard_drift="${workdir}/credential-guard-drift"
copy_fixture "${credential_guard_drift}"
perl -0pi -e 's/initialized runtime is missing credential/initialized runtime regenerated credential/g' \
  "${credential_guard_drift}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with "${credential_guard_drift}" 'initialized runtime is missing credential'

preserved_volume_guard_drift="${workdir}/preserved-volume-guard-drift"
copy_fixture "${preserved_volume_guard_drift}"
perl -0pi -e 's/assert_no_preserved_phase67_volumes/assert_removed_preserved_phase67_volumes/g' \
  "${preserved_volume_guard_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh" \
  "${preserved_volume_guard_drift}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with "${preserved_volume_guard_drift}" 'assert_no_preserved_phase67_volumes'

evidence_runtime_digest_drift="${workdir}/evidence-runtime-digest-drift"
copy_fixture "${evidence_runtime_digest_drift}"
perl -0pi -e 's/repository_runtime_artifact_sha256/repository_runtime_artifact_md5/g' \
  "${evidence_runtime_digest_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh"
assert_fails_with "${evidence_runtime_digest_drift}" 'repository_runtime_artifact_sha256='

project_subnet_drift="${workdir}/project-subnet-drift"
copy_fixture "${project_subnet_drift}"
perl -0pi -e 's/project_network_subnets/owned_network_cidrs/g' \
  "${project_subnet_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${project_subnet_drift}" 'project_network_subnets'

index_definition_drift="${workdir}/index-definition-drift"
copy_fixture "${index_definition_drift}"
perl -0pi -e 's/pg_get_indexdef/index_name_only/g' \
  "${index_definition_drift}/control-plane/deployment/phase-67-integration-lab/control-plane-entrypoint.sh"
assert_fails_with "${index_definition_drift}" "pg_get_indexdef(indexrelid, 1, true) = 'idempotency_key'"

lookup_index_definition_drift="${workdir}/lookup-index-definition-drift"
copy_fixture "${lookup_index_definition_drift}"
perl -0pi -e "s/compared_at DESC/compared_at ASC/g" \
  "${lookup_index_definition_drift}/control-plane/deployment/phase-67-integration-lab/control-plane-entrypoint.sh"
assert_fails_with "${lookup_index_definition_drift}" 'CREATE INDEX reconciliation_records_correlation_alert_latest_idx'

docker_context_secret_drift="${workdir}/docker-context-secret-drift"
copy_fixture "${docker_context_secret_drift}"
perl -0pi -e 's#control-plane/deployment/first-boot/secrets/\n##' \
  "${docker_context_secret_drift}/.dockerignore"
assert_fails_with "${docker_context_secret_drift}" 'control-plane/deployment/first-boot/secrets/'

wazuh_dashboard_credential_drift="${workdir}/wazuh-dashboard-credential-drift"
copy_fixture "${wazuh_dashboard_credential_drift}"
perl -0pi -e 's/\$\{AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD:\?run-init-first\}/kibanaserver/' \
  "${wazuh_dashboard_credential_drift}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${wazuh_dashboard_credential_drift}" 'AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD'

proxy_ui_route_drift="${workdir}/proxy-ui-route-drift"
copy_fixture "${proxy_ui_route_drift}"
perl -0pi -e 's/server_name wazuh\.localhost;/server_name direct-wazuh.localhost;/' \
  "${proxy_ui_route_drift}/control-plane/deployment/phase-67-integration-lab/config/control-plane.conf"
assert_fails_with "${proxy_ui_route_drift}" 'server_name wazuh.localhost;'

direct_ui_port_drift="${workdir}/direct-ui-port-drift"
copy_fixture "${direct_ui_port_drift}"
printf '\n# AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT\n' \
  >>"${direct_ui_port_drift}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${direct_ui_port_drift}" 'Shuffle frontend must not be published'

port_service_owner_drift="${workdir}/port-service-owner-drift"
copy_fixture "${port_service_owner_drift}"
perl -0pi -e 's/com\.docker\.compose\.service=\$\{expected_service\}/com.docker.compose.project=\${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}/' \
  "${port_service_owner_drift}/control-plane/deployment/phase-67-integration-lab/preflight.sh"
assert_fails_with "${port_service_owner_drift}" 'com.docker.compose.service=${expected_service}'

runtime_canonical_drift="${workdir}/runtime-canonical-drift"
copy_fixture "${runtime_canonical_drift}"
perl -0pi -e 's/resolve\(strict=False\)/absolute()/g' \
  "${runtime_canonical_drift}/control-plane/deployment/phase-67-integration-lab/lab-common.sh"
assert_fails_with "${runtime_canonical_drift}" 'pathlib.Path(sys.argv[1]).resolve(strict=False)'

teardown_ownership_drift="${workdir}/teardown-ownership-drift"
copy_fixture "${teardown_ownership_drift}"
perl -0pi -e 's/assert_phase67_compose_project_ownership/assert_removed_project_ownership/g' \
  "${teardown_ownership_drift}/control-plane/deployment/phase-67-integration-lab/down.sh" \
  "${teardown_ownership_drift}/control-plane/deployment/phase-67-integration-lab/destroy-data.sh"
assert_fails_with "${teardown_ownership_drift}" 'assert_phase67_compose_project_ownership'

echo "Phase 67.1 verifier rejects context, socket, cleanup, emulation, image, migration-proof," \
  "image-digest, migration-definition, scope-narrowing, Wazuh-upstream-TLS," \
  "certificate-renewal, network-host, duplicate-port, runtime-quoting, bounded-logs," \
  "Wazuh-checkout, teardown-recovery, proxy-recreate, Wazuh-certificate, Wazuh-marker-order," \
  "status-evidence, selected-address, published-port-evidence, reviewed-pin, architecture," \
  "evidence-collision, credential-guard, preserved-volume, evidence-runtime-digest," \
  "project-subnet, replacement-certificate, start-time Wazuh-checkout, Wazuh-digest," \
  "index-definition, lookup-index-definition, Docker-context-secret, dashboard-credential," \
  "proxy-UI-route, direct-UI-port, port-service-owner, canonical-runtime, and teardown-ownership drift."
