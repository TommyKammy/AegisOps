#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/control-plane" "${target}/scripts"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
  mkdir -p "${target}/control-plane/tests"
  cp "${repo_root}/control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py" \
    "${target}/control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

restored_root_file_repo="${workdir}/restored-root-file"
create_valid_repo "${restored_root_file_repo}"
printf '%s\n' '"""Unexpected restored Phase29 root file."""' \
  >"${restored_root_file_repo}/control-plane/aegisops_control_plane/phase29_shadow_dataset.py"
assert_fails_with \
  "${restored_root_file_repo}" \
  "Phase 52.6.5 Phase29 root filename must be retired: control-plane/aegisops_control_plane/phase29_shadow_dataset.py"

missing_alias_repo="${workdir}/missing-alias"
create_valid_repo "${missing_alias_repo}"
perl -0pi -e 's/    "aegisops_control_plane\.phase29_shadow_dataset": _alias\(.*?    \),\n//s' \
  "${missing_alias_repo}/control-plane/aegisops_control_plane/core/legacy_import_aliases.py"
assert_fails_with \
  "${missing_alias_repo}" \
  "Phase 52.6.5 missing Phase29 legacy alias: aegisops_control_plane.phase29_shadow_dataset"

wrong_scoring_owner_repo="${workdir}/wrong-scoring-owner"
create_valid_repo "${wrong_scoring_owner_repo}"
perl -0pi -e 's/aegisops_control_plane\.ml_shadow\.legacy_scoring_adapter/aegisops_control_plane.ml_shadow.scoring/' \
  "${wrong_scoring_owner_repo}/control-plane/aegisops_control_plane/core/legacy_import_aliases.py"
assert_fails_with \
  "${wrong_scoring_owner_repo}" \
  "Phase 52.6.5 Phase29 alias target mismatch for aegisops_control_plane.phase29_shadow_scoring"

wrong_attribute_owner_repo="${workdir}/wrong-attribute-owner"
create_valid_repo "${wrong_attribute_owner_repo}"
perl -0pi -e 's/class Phase29ShadowScoreResult\(_impl\.Phase29ShadowScoreResult\):\n    \@property\n    def feature_frequencies_at_inference_time\(self\) -> Mapping\[str, object\]:\n        return \{}\n\n\nclass Phase29OfflineShadowScoringSnapshot\(_impl\.Phase29OfflineShadowScoringSnapshot\):/class Phase29ShadowScoreResult(_impl.Phase29ShadowScoreResult):\n    pass\n\n\nclass Phase29OfflineShadowScoringSnapshot(_impl.Phase29OfflineShadowScoringSnapshot):\n    \@property\n    def feature_frequencies_at_inference_time(self) -> Mapping[str, object]:\n        return {}/' \
  "${wrong_attribute_owner_repo}/control-plane/aegisops_control_plane/ml_shadow/legacy_scoring_adapter.py"
assert_fails_with \
  "${wrong_attribute_owner_repo}" \
  "Phase 52.6.5 legacy scoring wrapper is missing feature_frequencies_at_inference_time"

retained_blocker_repo="${workdir}/retained-blocker"
create_valid_repo "${retained_blocker_repo}"
perl -0pi -e 's/RETAINED_COMPATIBILITY_BLOCKERS: dict\[str, str\] = \{/RETAINED_COMPATIBILITY_BLOCKERS: dict[str, str] = {\n    "aegisops_control_plane.phase29_shadow_dataset": "stale blocker.",/' \
  "${retained_blocker_repo}/control-plane/aegisops_control_plane/core/legacy_import_aliases.py"
assert_fails_with \
  "${retained_blocker_repo}" \
  "Phase 52.6.5 Phase29 path still listed as a retained blocker: aegisops_control_plane.phase29_shadow_dataset"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.6.5 Phase29 retirement artifact: workstation-local absolute path detected"

echo "Phase 52.6.5 Phase29 root filename retirement verifier negative and valid fixtures passed."
