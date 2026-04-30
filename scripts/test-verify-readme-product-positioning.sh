#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-readme-product-positioning.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_valid_readme() {
  local target="$1"

  cat <<'EOF' >"${target}/README.md"
# AegisOps

## Product positioning

Current status: AegisOps has a strong pilot foundation, but it is still pre-GA and is not yet a self-service commercial replacement.

Target status: AegisOps aims to provide an AI-agent-native SMB SOC/SIEM/SOAR operating experience above Wazuh and Shuffle.

Replacement means the operating experience and authoritative record chain for daily SMB security operations, not Wazuh internals, Shuffle internals, or every SIEM/SOAR capability.

The Phase 51 replacement boundary is defined by `docs/adr/0011-phase-51-1-replacement-boundary.md`.

Wazuh detects, AegisOps decides, records, and reconciles, and Shuffle executes reviewed delegated routine work.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, and release truth.

AI remains advisory-only and non-authoritative; it must not approve, execute, reconcile, close cases, activate detectors, or become source truth.

Forbidden overclaim: AegisOps must not be described as already GA, already self-service commercial, a replacement for every SIEM/SOAR capability, a reimplementation of Wazuh or Shuffle internals, or a broad autonomous SOC.
EOF
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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
mkdir -p "${valid_repo}"
write_valid_readme "${valid_repo}"
assert_passes "${valid_repo}"

missing_current_status_repo="${workdir}/missing-current-status"
mkdir -p "${missing_current_status_repo}"
write_valid_readme "${missing_current_status_repo}"
perl -0pi -e 's#Current status: AegisOps has a strong pilot foundation, but it is still pre-GA and is not yet a self-service commercial replacement\.\n\n##' "${missing_current_status_repo}/README.md"
assert_fails_with \
  "${missing_current_status_repo}" \
  "Missing README product positioning statement: Current status: AegisOps has a strong pilot foundation, but it is still pre-GA and is not yet a self-service commercial replacement."

ga_overclaim_repo="${workdir}/ga-overclaim"
mkdir -p "${ga_overclaim_repo}"
write_valid_readme "${ga_overclaim_repo}"
printf '%s\n' "AegisOps is already GA." >>"${ga_overclaim_repo}/README.md"
assert_fails_with \
  "${ga_overclaim_repo}" \
  "Forbidden README product positioning overclaim: AegisOps is already GA"

authoritative_ai_repo="${workdir}/authoritative-ai"
mkdir -p "${authoritative_ai_repo}"
write_valid_readme "${authoritative_ai_repo}"
printf '%s\n' "AI is authoritative." >>"${authoritative_ai_repo}/README.md"
assert_fails_with \
  "${authoritative_ai_repo}" \
  "Forbidden README product positioning overclaim: AI is authoritative"

wazuh_truth_repo="${workdir}/wazuh-truth"
mkdir -p "${wazuh_truth_repo}"
write_valid_readme "${wazuh_truth_repo}"
printf '%s\n' "Wazuh owns workflow truth." >>"${wazuh_truth_repo}/README.md"
assert_fails_with \
  "${wazuh_truth_repo}" \
  "Forbidden README product positioning overclaim: Wazuh owns workflow truth"

shuffle_truth_repo="${workdir}/shuffle-truth"
mkdir -p "${shuffle_truth_repo}"
write_valid_readme "${shuffle_truth_repo}"
printf '%s\n' "Shuffle owns workflow truth." >>"${shuffle_truth_repo}/README.md"
assert_fails_with \
  "${shuffle_truth_repo}" \
  "Forbidden README product positioning overclaim: Shuffle owns workflow truth"

autonomous_soc_repo="${workdir}/autonomous-soc"
mkdir -p "${autonomous_soc_repo}"
write_valid_readme "${autonomous_soc_repo}"
printf '%s\n' "AegisOps is a broad autonomous SOC." >>"${autonomous_soc_repo}/README.md"
assert_fails_with \
  "${autonomous_soc_repo}" \
  "Forbidden README product positioning overclaim: AegisOps is a broad autonomous SOC"

echo "README product positioning verifier tests passed."
