#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-9-closeout-evaluation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

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

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-53-closeout-evaluation.md" "${target}/docs/phase-53-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 53 closeout evaluation: docs/phase-53-closeout-evaluation.md"

missing_readme_link_repo="${workdir}/missing-readme-link"
copy_valid_repo "${missing_readme_link_repo}"
perl -0pi -e 's/\[Phase 53\.9 closeout evaluation\]\(docs\/phase-53-closeout-evaluation\.md\)/Phase 53.9 closeout evaluation/g' \
  "${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 53.9 closeout link: [Phase 53.9 closeout evaluation](docs/phase-53-closeout-evaluation.md)"

missing_subordinate_posture_repo="${workdir}/missing-subordinate-posture"
copy_valid_repo "${missing_subordinate_posture_repo}"
perl -0pi -e 's/Wazuh remains a subordinate detection substrate\.//' \
  "${missing_subordinate_posture_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${missing_subordinate_posture_repo}" \
  "Missing required Phase 53 closeout term in docs/phase-53-closeout-evaluation.md: Wazuh remains a subordinate detection substrate."

missing_source_health_repo="${workdir}/missing-source-health"
copy_valid_repo "${missing_source_health_repo}"
perl -0pi -e 's/\| Source health \| Deferred source-health projection\. \| Subordinate source-health projection states for Wazuh manager, dashboard, indexer, intake, signal freshness, parser, volume, credential, unavailable, stale, degraded, and mismatched posture\. \|\n//' \
  "${missing_source_health_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${missing_source_health_repo}" \
  'Missing required Phase 53 closeout term in docs/phase-53-closeout-evaluation.md: | Source health | Deferred source-health projection. | Subordinate source-health projection states for Wazuh manager, dashboard, indexer, intake, signal freshness, parser, volume, credential, unavailable, stale, degraded, and mismatched posture. |'

missing_sample_signal_repo="${workdir}/missing-sample-signal"
copy_valid_repo "${missing_sample_signal_repo}"
perl -0pi -e 's/\| Sample signal evidence \| Existing Wazuh fixture families for earlier source work\. \| Reviewed SMB single-node SSH authentication failure Wazuh alert and analytic-signal fixtures tied to Phase 53\.4 parser mapping evidence\. \|\n//' \
  "${missing_sample_signal_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${missing_sample_signal_repo}" \
  'Missing required Phase 53 closeout term in docs/phase-53-closeout-evaluation.md: | Sample signal evidence | Existing Wazuh fixture families for earlier source work. | Reviewed SMB single-node SSH authentication failure Wazuh alert and analytic-signal fixtures tied to Phase 53.4 parser mapping evidence. |'

missing_child_issue_lint_repo="${workdir}/missing-child-issue-lint"
copy_valid_repo "${missing_child_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1139 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_child_issue_lint_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${missing_child_issue_lint_repo}" \
  "Missing required Phase 53 closeout term in docs/phase-53-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1139 --config <supervisor-config-path>"

phase61_overclaim_repo="${workdir}/phase61-overclaim"
copy_valid_repo "${phase61_overclaim_repo}"
printf '%s\n' "Phase 61 SIEM breadth is complete" >>"${phase61_overclaim_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${phase61_overclaim_repo}" \
  "Forbidden Phase 53 closeout evaluation claim: Phase 61 SIEM breadth is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "Phase 53 proves commercial replacement readiness" >>"${commercial_overclaim_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 53 closeout evaluation claim: Phase 53 proves commercial replacement readiness"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-53-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 53 closeout evaluation: workstation-local absolute path detected"

echo "Phase 53 closeout evaluation verifier tests passed."
