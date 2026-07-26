#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${LAB_DIR}/../../.." && pwd)"
COMPOSE_FILE="${LAB_DIR}/docker-compose.yml"
BOOTSTRAP_ENV="${AEGISOPS_LAB_BOOTSTRAP_ENV:-${LAB_DIR}/bootstrap.env.sample}"

fail() {
  echo "BLOCKED: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command is unavailable: $1"
}

load_bootstrap_environment() {
  [[ -f "${BOOTSTRAP_ENV}" ]] || fail "bootstrap environment file not found: ${BOOTSTRAP_ENV}"

  # shellcheck disable=SC1090
  source "${BOOTSTRAP_ENV}"
  : "${AEGISOPS_LAB_RUNTIME_ROOT:?AEGISOPS_LAB_RUNTIME_ROOT is required}"

  AEGISOPS_LAB_RUNTIME_ROOT="${AEGISOPS_LAB_RUNTIME_ROOT/#\~/${HOME}}"
  assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"
  RUNTIME_ENV="${AEGISOPS_LAB_RUNTIME_ROOT}/runtime.env"
  export AEGISOPS_LAB_RUNTIME_ROOT
  export RUNTIME_ENV
}

load_lab_environment() {
  local bootstrap_runtime_root

  load_bootstrap_environment
  bootstrap_runtime_root="${AEGISOPS_LAB_RUNTIME_ROOT}"
  if [[ -f "${RUNTIME_ENV}" ]]; then
    # shellcheck disable=SC1090
    source "${RUNTIME_ENV}"
  fi
  [[ "${AEGISOPS_LAB_RUNTIME_ROOT}" == "${bootstrap_runtime_root}" ]] \
    || fail "runtime environment root differs from the reviewed bootstrap root"
  assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"

  export AEGISOPS_LAB_RUNTIME_ROOT
  export RUNTIME_ENV
}

require_runtime_configuration() {
  load_lab_environment
  [[ -f "${RUNTIME_ENV}" ]] || fail "runtime environment not initialized; run ${LAB_DIR}/init.sh"
}

require_runtime_environment() {
  require_runtime_configuration
  [[ -d "${AEGISOPS_LAB_SECRET_DIR:-}" ]] || fail "runtime secret directory is missing; rerun ${LAB_DIR}/init.sh"
}

assert_reviewed_lab_pins() {
  [[ "${AEGISOPS_LAB_WAZUH_VERSION:-}" == "4.14.6" ]] \
    || fail "AEGISOPS_LAB_WAZUH_VERSION must remain at reviewed version 4.14.6"
  [[ "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT:-}" == "499184cbeb44fc1086791d11ad4b9bdcb77a9bb9" ]] \
    || fail "AEGISOPS_LAB_WAZUH_DOCKER_COMMIT must remain at the reviewed Wazuh 4.14.6 commit"
  [[ "${AEGISOPS_LAB_SHUFFLE_VERSION:-}" == "2.2.1" ]] \
    || fail "AEGISOPS_LAB_SHUFFLE_VERSION must remain at reviewed version 2.2.1"
  [[ "${AEGISOPS_LAB_WAZUH_PLATFORM:-}" == "linux/arm64" ]] \
    || fail "AEGISOPS_LAB_WAZUH_PLATFORM must remain explicit linux/arm64"
  [[ "${AEGISOPS_LAB_SHUFFLE_PLATFORM:-}" == "linux/amd64" ]] \
    || fail "AEGISOPS_LAB_SHUFFLE_PLATFORM must remain explicit linux/amd64"
}

assert_reviewed_wazuh_checkout() {
  local source_dir="$1"
  local expected_commit="$2"
  local managed_relative_path="$3"
  local actual_commit

  [[ -d "${source_dir}/.git" ]] \
    || fail "Wazuh substrate path is not a Git checkout: ${source_dir}"
  actual_commit="$(git -C "${source_dir}" rev-parse HEAD)"
  [[ "${actual_commit}" == "${expected_commit}" ]] \
    || fail "Wazuh substrate commit is ${actual_commit}; expected ${expected_commit}"
  if ! git -C "${source_dir}" diff --quiet HEAD -- \
    . ":(exclude)${managed_relative_path}"; then
    fail "Wazuh substrate has unreviewed tracked changes outside ${managed_relative_path}"
  fi
}

record_reviewed_file_digest() {
  local path="$1"
  local digest_path="$2"
  local staging_path="${digest_path}.tmp.$$"
  local digest

  digest="$(openssl dgst -sha256 -r "${path}" | awk '{print $1}')"
  [[ "${digest}" =~ ^[0-9a-f]{64}$ ]] \
    || fail "could not record a reviewed SHA-256 digest for ${path}"
  printf '%s\n' "${digest}" >"${staging_path}"
  chmod 600 "${staging_path}"
  mv "${staging_path}" "${digest_path}"
}

assert_reviewed_file_digest() {
  local path="$1"
  local digest_path="$2"
  local expected_digest
  local actual_digest

  [[ -s "${digest_path}" ]] \
    || fail "reviewed digest is missing for ${path}; run ${LAB_DIR}/prepare-substrates.sh"
  expected_digest="$(<"${digest_path}")"
  [[ "${expected_digest}" =~ ^[0-9a-f]{64}$ ]] \
    || fail "reviewed digest is invalid for ${path}; run ${LAB_DIR}/prepare-substrates.sh"
  actual_digest="$(openssl dgst -sha256 -r "${path}" | awk '{print $1}')"
  [[ "${actual_digest}" == "${expected_digest}" ]] \
    || fail "${path} changed after substrate preparation; run ${LAB_DIR}/prepare-substrates.sh"
}

validate_wazuh_certificate_bundle() {
  local cert_dir="$1"
  local certificate
  local certificate_digest
  local key
  local key_digest
  local required_files=(
    root-ca.pem
    root-ca-manager.pem
    wazuh.indexer-key.pem
    wazuh.indexer.pem
    admin.pem
    admin-key.pem
    wazuh.manager.pem
    wazuh.manager-key.pem
    wazuh.dashboard.pem
    wazuh.dashboard-key.pem
  )

  for certificate in "${required_files[@]}"; do
    [[ -s "${cert_dir}/${certificate}" ]] || return 1
  done
  for certificate in \
    root-ca.pem \
    root-ca-manager.pem \
    wazuh.indexer.pem \
    admin.pem \
    wazuh.manager.pem \
    wazuh.dashboard.pem
  do
    openssl x509 -checkend 604800 -noout -in "${cert_dir}/${certificate}" \
      >/dev/null 2>&1 || return 1
  done
  for key in \
    wazuh.indexer-key.pem \
    admin-key.pem \
    wazuh.manager-key.pem \
    wazuh.dashboard-key.pem
  do
    openssl pkey -in "${cert_dir}/${key}" -noout >/dev/null 2>&1 || return 1
  done

  while IFS='|' read -r certificate key; do
    certificate_digest="$(
      openssl x509 -in "${cert_dir}/${certificate}" -pubkey -noout 2>/dev/null |
        openssl pkey -pubin -outform DER 2>/dev/null |
        openssl sha256
    )" || return 1
    key_digest="$(
      openssl pkey -in "${cert_dir}/${key}" -pubout -outform DER 2>/dev/null |
        openssl sha256
    )" || return 1
    [[ "${certificate_digest}" == "${key_digest}" ]] || return 1
  done <<'EOF'
wazuh.indexer.pem|wazuh.indexer-key.pem
admin.pem|admin-key.pem
wazuh.manager.pem|wazuh.manager-key.pem
wazuh.dashboard.pem|wazuh.dashboard-key.pem
EOF

  openssl verify -CAfile "${cert_dir}/root-ca.pem" "${cert_dir}/root-ca.pem" \
    >/dev/null 2>&1 || return 1
  openssl verify -CAfile "${cert_dir}/root-ca-manager.pem" "${cert_dir}/root-ca-manager.pem" \
    >/dev/null 2>&1 || return 1
  for certificate in wazuh.indexer.pem admin.pem wazuh.dashboard.pem; do
    openssl verify -CAfile "${cert_dir}/root-ca.pem" "${cert_dir}/${certificate}" \
      >/dev/null 2>&1 || return 1
  done
  openssl verify \
    -CAfile "${cert_dir}/root-ca-manager.pem" \
    "${cert_dir}/wazuh.manager.pem" \
    >/dev/null 2>&1 || return 1
}

assert_safe_runtime_root() {
  local candidate="${1:-}"
  local allowed_root="${HOME}/.local/share/aegisops"
  local canonical_allowed_root
  local canonical_candidate

  [[ -n "${candidate}" ]] || fail "runtime root is empty"
  [[ "${candidate}" == /* ]] || fail "runtime root must be absolute: ${candidate}"
  require_command python3
  canonical_allowed_root="$(
    python3 - "${allowed_root}" <<'PY'
import pathlib
import sys

print(pathlib.Path(sys.argv[1]).resolve(strict=False))
PY
  )" || fail "could not resolve the allowed AegisOps runtime root"
  canonical_candidate="$(
    python3 - "${candidate}" <<'PY'
import pathlib
import sys

print(pathlib.Path(sys.argv[1]).resolve(strict=False))
PY
  )" || fail "could not resolve runtime root: ${candidate}"
  case "${canonical_candidate}" in
    "${canonical_allowed_root}"/*) ;;
    *) fail "runtime root must remain below ${HOME}/.local/share/aegisops/" ;;
  esac
}

docker_lab() {
  : "${AEGISOPS_LAB_DOCKER_CONTEXT:?AEGISOPS_LAB_DOCKER_CONTEXT is required}"
  docker --context "${AEGISOPS_LAB_DOCKER_CONTEXT}" "$@"
}

compose_lab() {
  : "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:?AEGISOPS_LAB_COMPOSE_PROJECT_NAME is required}"
  docker_lab compose \
    --project-name "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" \
    --env-file "${RUNTIME_ENV}" \
    --file "${COMPOSE_FILE}" \
    "$@"
}

compose_scope() {
  local scope="${1:-core}"
  shift

  case "${scope}" in
    core) compose_lab "$@" ;;
    wazuh) compose_lab --profile wazuh "$@" ;;
    shuffle) compose_lab --profile shuffle "$@" ;;
    full) compose_lab --profile wazuh --profile shuffle "$@" ;;
    *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
  esac
}

phase67_volume_suffixes() {
  printf '%s\n' \
    postgres-data \
    wazuh-api-configuration \
    wazuh-etc \
    wazuh-logs \
    wazuh-queue \
    wazuh-integrations \
    wazuh-indexer-data \
    wazuh-dashboard-config \
    wazuh-dashboard-custom \
    shuffle-database
}

assert_no_preserved_phase67_volumes() {
  local existing_volumes
  local preserved_volumes=""
  local suffix
  local volume_name

  require_command docker
  existing_volumes="$(docker_lab volume ls --quiet)" \
    || fail "could not enumerate Docker volumes before initializing new Phase 67.1 credentials"
  while IFS= read -r suffix; do
    volume_name="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-${suffix}"
    if grep -Fqx -- "${volume_name}" <<<"${existing_volumes}"; then
      preserved_volumes="${preserved_volumes}${volume_name}"$'\n'
    fi
  done < <(phase67_volume_suffixes)
  [[ -z "${preserved_volumes}" ]] \
    || fail "runtime.env is missing while preserved Phase 67.1 volumes exist: $(tr '\n' ' ' <<<"${preserved_volumes}"); restore the original runtime.env and credentials, or explicitly destroy the preserved project data before reinitializing"
}

assert_phase67_resource_owned() {
  local resource_type="$1"
  local resource_id="$2"
  local labels
  local phase_label
  local project_label

  case "${resource_type}" in
    container)
      labels="$(
        docker_lab container inspect "${resource_id}" \
          --format '{{index .Config.Labels "com.aegisops.lab.phase"}}|{{index .Config.Labels "com.docker.compose.project"}}'
      )"
      ;;
    network|volume)
      labels="$(
        docker_lab "${resource_type}" inspect "${resource_id}" \
          --format '{{index .Labels "com.aegisops.lab.phase"}}|{{index .Labels "com.docker.compose.project"}}'
      )"
      ;;
    *) fail "unsupported Docker resource type for ownership check: ${resource_type}" ;;
  esac
  IFS='|' read -r phase_label project_label <<<"${labels}"
  [[ "${phase_label}" == "67.1" ]] \
    || fail "${resource_type} '${resource_id}' exists without the Phase 67.1 ownership label"
  [[ "${project_label}" == "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" ]] \
    || fail "${resource_type} '${resource_id}' is not owned by Compose project '${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}'"
}

assert_phase67_compose_project_ownership() {
  local container_ids
  local network_ids
  local resource_id
  local network_name="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-network"
  local suffix
  local volume_ids
  local volume_name

  container_ids="$(
    docker_lab ps --all --quiet \
      --filter "label=com.docker.compose.project=${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}"
  )" || fail "could not enumerate containers for Compose project '${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}'"
  while IFS= read -r resource_id; do
    [[ -z "${resource_id}" ]] \
      || assert_phase67_resource_owned container "${resource_id}"
  done <<<"${container_ids}"
  network_ids="$(
    docker_lab network ls --quiet \
      --filter "label=com.docker.compose.project=${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}"
  )" || fail "could not enumerate networks for Compose project '${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}'"
  while IFS= read -r resource_id; do
    [[ -z "${resource_id}" ]] \
      || assert_phase67_resource_owned network "${resource_id}"
  done <<<"${network_ids}"
  volume_ids="$(
    docker_lab volume ls --quiet \
      --filter "label=com.docker.compose.project=${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}"
  )" || fail "could not enumerate volumes for Compose project '${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}'"
  while IFS= read -r resource_id; do
    [[ -z "${resource_id}" ]] \
      || assert_phase67_resource_owned volume "${resource_id}"
  done <<<"${volume_ids}"

  if docker_lab network inspect "${network_name}" >/dev/null 2>&1; then
    assert_phase67_resource_owned network "${network_name}"
  fi
  while IFS= read -r suffix; do
    volume_name="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-${suffix}"
    if docker_lab volume inspect "${volume_name}" >/dev/null 2>&1; then
      assert_phase67_resource_owned volume "${volume_name}"
    fi
  done < <(phase67_volume_suffixes)
}

selected_port_names() {
  local scope="${1:-core}"

  case "${scope}" in
    core)
      printf '%s\n' PROXY
      ;;
    wazuh)
      printf '%s\n' PROXY WAZUH_DASHBOARD
      ;;
    shuffle)
      printf '%s\n' PROXY SHUFFLE_FRONTEND
      ;;
    full)
      printf '%s\n' PROXY WAZUH_DASHBOARD SHUFFLE_FRONTEND
      ;;
    *)
      fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full"
      ;;
  esac
}

service_name_for_published_port() {
  case "$1" in
    PROXY) printf '%s\n' proxy ;;
    WAZUH_DASHBOARD) printf '%s\n' wazuh-dashboard ;;
    SHUFFLE_FRONTEND) printf '%s\n' shuffle-frontend ;;
    *) fail "unknown published port name '$1'" ;;
  esac
}

selected_address_names() {
  local scope="${1:-core}"

  printf '%s\n' PROXY CONTROL_PLANE POSTGRES
  case "${scope}" in
    core) ;;
    wazuh)
      printf '%s\n' WAZUH_MANAGER WAZUH_INDEXER WAZUH_DASHBOARD
      ;;
    shuffle)
      printf '%s\n' SHUFFLE_BACKEND SHUFFLE_OPENSEARCH SHUFFLE_FRONTEND
      ;;
    full)
      printf '%s\n' \
        WAZUH_MANAGER \
        WAZUH_INDEXER \
        WAZUH_DASHBOARD \
        SHUFFLE_BACKEND \
        SHUFFLE_OPENSEARCH \
        SHUFFLE_FRONTEND
      ;;
    *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
  esac
}

assert_unique_selected_ports() {
  local scope="${1:-core}"
  local selected_ports=" "
  local port_name
  local variable
  local port

  while IFS= read -r port_name; do
    variable="AEGISOPS_LAB_${port_name}_PORT"
    port="${!variable}"
    [[ "${port}" =~ ^[0-9]+$ && "${port}" -ge 1 && "${port}" -le 65535 ]] \
      || fail "${variable} must be an integer from 1 through 65535"
    case "${selected_ports}" in
      *" ${port} "*)
        fail "selected scope '${scope}' assigns duplicate host port ${port}"
        ;;
    esac
    selected_ports="${selected_ports}${port} "
  done < <(selected_port_names "${scope}")
}

write_evidence_header() {
  local output="$1"
  local repository_commit
  local repository_runtime_artifact_sha256
  local repository_runtime_changes
  local repository_runtime_state

  require_command git
  require_command python3
  repository_commit="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null)" \
    || fail "could not identify the repository commit for evidence"
  repository_runtime_changes="$(
    git -C "${REPO_ROOT}" status --porcelain=v1 --untracked-files=all -- \
      .dockerignore control-plane postgres/control-plane/migrations
  )" || fail "could not inspect repository runtime changes for evidence"
  if [[ -n "${repository_runtime_changes}" ]]; then
    repository_runtime_state=dirty
  else
    repository_runtime_state=clean
  fi
  repository_runtime_artifact_sha256="$(
    python3 - "${REPO_ROOT}" <<'PY'
import hashlib
import os
import pathlib
import stat
import sys

repo_root = pathlib.Path(sys.argv[1])
roots = (
    repo_root / ".dockerignore",
    repo_root / "control-plane",
    repo_root / "postgres" / "control-plane" / "migrations",
)
excluded_directories = {"__pycache__", ".pytest_cache"}
entries: list[pathlib.Path] = []
for root in roots:
    if not root.exists() and not root.is_symlink():
        continue
    entries.append(root)
    if not root.is_dir() or root.is_symlink():
        continue
    for directory, directory_names, file_names in os.walk(root):
        directory_names[:] = sorted(
            name for name in directory_names if name not in excluded_directories
        )
        base = pathlib.Path(directory)
        entries.extend(base / name for name in directory_names)
        entries.extend(
            base / name
            for name in sorted(file_names)
            if not name.endswith(".pyc")
        )

digest = hashlib.sha256()
digest.update(b"aegisops-phase67-runtime-artifacts-v1\0")
for path in sorted(
    set(entries),
    key=lambda item: item.relative_to(repo_root).as_posix(),
):
    relative = path.relative_to(repo_root).as_posix().encode()
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if path.is_symlink():
        kind = b"link"
        content = os.readlink(path).encode()
    elif path.is_dir():
        kind = b"directory"
        content = b""
    elif path.is_file():
        kind = b"file"
        content = None
    else:
        continue
    for value in (relative, kind, f"{mode:o}".encode()):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    if content is None:
        digest.update(metadata.st_size.to_bytes(8, "big"))
        with path.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
print(digest.hexdigest())
PY
  )" || fail "could not calculate the repository runtime artifact digest for evidence"
  [[ "${repository_runtime_artifact_sha256}" =~ ^[0-9a-f]{64}$ ]] \
    || fail "repository runtime artifact digest is invalid"
  {
    printf 'recorded_at_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'repository_commit=%s\n' "${repository_commit}"
    printf 'repository_runtime_state=%s\n' "${repository_runtime_state}"
    printf 'repository_runtime_artifact_sha256=%s\n' "${repository_runtime_artifact_sha256}"
  } >"${output}"
}
