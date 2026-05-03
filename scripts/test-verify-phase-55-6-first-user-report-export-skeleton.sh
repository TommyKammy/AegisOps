#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-55-6-first-user-report-export-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/getting-started/fixtures"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 55.6 first-user demo report export skeleton](docs/getting-started/first-user-demo-report-export.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/getting-started/first-user-demo-report-export.md" \
    "${target}/docs/getting-started/first-user-demo-report-export.md"
  cp -R "${repo_root}/docs/getting-started/fixtures/first-user-demo-report-export" \
    "${target}/docs/getting-started/fixtures/first-user-demo-report-export"
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
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/getting-started/first-user-demo-report-export.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 55.6 first-user demo report export skeleton"

missing_label_repo="${workdir}/missing-label"
create_valid_repo "${missing_label_repo}"
cp "${missing_label_repo}/docs/getting-started/fixtures/first-user-demo-report-export/missing-demo-label.json" \
  "${missing_label_repo}/docs/getting-started/fixtures/first-user-demo-report-export/valid-demo-report-export.json"
assert_fails_with \
  "${missing_label_repo}" \
  "Expected valid Phase 55.6 report export fixture valid-demo-report-export.json, got: missing required demo label"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
cp "${secret_repo}/docs/getting-started/fixtures/first-user-demo-report-export/secret-looking-value.json" \
  "${secret_repo}/docs/getting-started/fixtures/first-user-demo-report-export/valid-demo-report-export.json"
assert_fails_with \
  "${secret_repo}" \
  "Expected valid Phase 55.6 report export fixture valid-demo-report-export.json, got: secret-looking value in export output"

commercial_claim_repo="${workdir}/commercial-claim"
create_valid_repo "${commercial_claim_repo}"
cp "${commercial_claim_repo}/docs/getting-started/fixtures/first-user-demo-report-export/commercial-report-claim.json" \
  "${commercial_claim_repo}/docs/getting-started/fixtures/first-user-demo-report-export/valid-demo-report-export.json"
assert_fails_with \
  "${commercial_claim_repo}" \
  "Expected valid Phase 55.6 report export fixture valid-demo-report-export.json, got: demo export claims commercial report breadth"

production_truth_repo="${workdir}/production-truth"
create_valid_repo "${production_truth_repo}"
cp "${production_truth_repo}/docs/getting-started/fixtures/first-user-demo-report-export/production-truth-claim.json" \
  "${production_truth_repo}/docs/getting-started/fixtures/first-user-demo-report-export/valid-demo-report-export.json"
assert_fails_with \
  "${production_truth_repo}" \
  "Expected valid Phase 55.6 report export fixture valid-demo-report-export.json, got: demo export claims production truth"

doc_forbidden_claim_repo="${workdir}/doc-forbidden-claim"
create_valid_repo "${doc_forbidden_claim_repo}"
printf '%s\n' "Demo report export is production truth." \
  >>"${doc_forbidden_claim_repo}/docs/getting-started/first-user-demo-report-export.md"
assert_fails_with \
  "${doc_forbidden_claim_repo}" \
  "Forbidden Phase 55.6 report export skeleton claim: Demo report export is production truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for export review.\n' "Users" \
  >>"${local_path_repo}/docs/getting-started/first-user-demo-report-export.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 55.6 report export skeleton: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 55.6 first-user demo report export skeleton."

echo "Phase 55.6 first-user report export skeleton negative and valid checks passed."
