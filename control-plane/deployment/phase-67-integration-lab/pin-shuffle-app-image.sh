#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
require_command docker
require_command jq
# shellcheck source=shuffle/reviewed-app-image.env
source "${LAB_DIR}/shuffle/reviewed-app-image.env"

"${LAB_DIR}/preflight.sh" --scope shuffle

pinned_reference="$(
  printf '%s@%s' \
    "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}" \
    "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}"
)"
runtime_reference="$(
  printf '%s:%s' \
    "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}" \
    "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_TAG}"
)"

if ! docker_lab image inspect "${pinned_reference}" >/dev/null 2>&1; then
  docker_lab pull \
    --platform "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_PLATFORM}" \
    "${pinned_reference}" \
    >/dev/null
fi

image_metadata="$(docker_lab image inspect "${pinned_reference}")"
actual_image_id="$(jq -er '.[0].Id' <<<"${image_metadata}")"
actual_platform="$(
  jq -er '.[0] | "\(.Os)/\(.Architecture)"' <<<"${image_metadata}"
)"
jq -e \
  --arg pinned_reference "${pinned_reference}" \
  '.[0].RepoDigests | index($pinned_reference) != null' \
  <<<"${image_metadata}" \
  >/dev/null \
  || fail "Shuffle Tools image does not retain the reviewed repository digest"
[[ "${actual_platform}" == "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_PLATFORM}" ]] \
  || fail "Shuffle Tools image platform is ${actual_platform}, expected ${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_PLATFORM}"

docker_lab image tag "${pinned_reference}" "${runtime_reference}"
tagged_image_id="$(
  docker_lab image inspect "${runtime_reference}" --format '{{.Id}}'
)"
[[ "${tagged_image_id}" == "${actual_image_id}" ]] \
  || fail "Shuffle Tools runtime tag does not resolve to the reviewed image"

echo "shuffle_tools_image=${runtime_reference}"
echo "shuffle_tools_image_immutable_ref=${pinned_reference}"
