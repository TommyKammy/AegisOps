#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-62-8-closeout-evaluation.sh"

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

  if ! grep -Fiq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-62-closeout-evaluation.md" "${target}/docs/phase-62-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-62-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

url_path_repo="${workdir}/url-path"
copy_valid_repo "${url_path_repo}"
users_segment="Users"
home_segment="home"
root_segment="root"
printf '%s\n' \
  "Reference URL: https://example.com/${home_segment}/docs/phase-62-closeout" \
  "Reference URL: https://example.com/${root_segment}/docs/phase-62-closeout" \
  "Reference URL: https://example.com/C:/${users_segment}/docs/phase-62-closeout" \
  >>"${url_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${url_path_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 62 closeout evaluation: docs/phase-62-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 62\.8 closeout evaluation\]\(docs\/phase-62-closeout-evaluation\.md\)[^\n]*\n/- Phase 62.8 closeout evaluation\\n/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 62.8 closeout evaluation](docs/phase-62-closeout-evaluation.md)"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1322 | Phase 62.8 Phase 62 closeout evaluation | Open until this document and focused closeout verifier land. |"
assert_fails_with \
  "${missing_child_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: | #1322 | Phase 62.8 Phase 62 closeout evaluation | Open until this document and focused closeout verifier land. |"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1322 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  'Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: `node <codex-supervisor-root>/dist/index.js issue-lint 1322 --config <supervisor-config-path>`'

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps records remain authoritative for case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: AegisOps records remain authoritative"

missing_path_hygiene_repo="${workdir}/missing-path-hygiene"
copy_valid_repo "${missing_path_hygiene_repo}"
remove_doc_text "${missing_path_hygiene_repo}" \
  "Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."
assert_fails_with \
  "${missing_path_hygiene_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."

downstream_truth_repo="${workdir}/downstream-truth"
copy_valid_repo "${downstream_truth_repo}"
printf '%s\n' "Downstream workflow state is AegisOps truth." >>"${downstream_truth_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${downstream_truth_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: downstream workflow state is aegisops truth"

simulator_truth_repo="${workdir}/simulator-truth"
copy_valid_repo "${simulator_truth_repo}"
printf '%s\n' "Simulator output is production truth." >>"${simulator_truth_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${simulator_truth_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: simulator output is production truth"

controlled_write_repo="${workdir}/controlled-write"
copy_valid_repo "${controlled_write_repo}"
printf '%s\n' "Controlled Write is default enabled." >>"${controlled_write_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${controlled_write_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: controlled write is default enabled"

controlled_write_sentence_repo="${workdir}/controlled-write-sentence"
copy_valid_repo "${controlled_write_sentence_repo}"
printf '%s\n' "Controlled Write defaults are enabled." >>"${controlled_write_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${controlled_write_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: write-default overclaim"

hard_write_sentence_repo="${workdir}/hard-write-sentence"
copy_valid_repo "${hard_write_sentence_repo}"
printf '%s\n' "Hard Write defaults are enabled." >>"${hard_write_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${hard_write_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: write-default overclaim"

marketplace_repo="${workdir}/marketplace"
copy_valid_repo "${marketplace_repo}"
printf '%s\n' "Broad SOAR marketplace is complete." >>"${marketplace_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${marketplace_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: broad soar marketplace is complete"

phase63_repo="${workdir}/phase63"
copy_valid_repo "${phase63_repo}"
printf '%s\n' "Phase 63 evidence expansion is implemented." >>"${phase63_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase63_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: phase 63 evidence expansion is implemented"

phase66_repo="${workdir}/phase66"
copy_valid_repo "${phase66_repo}"
printf '%s\n' "Phase 66 RC proof is fully complete." >>"${phase66_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase66_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

commercial_repo="${workdir}/commercial"
copy_valid_repo "${commercial_repo}"
printf '%s\n' "AegisOps is a commercial replacement for every SIEM/SOAR capability." >>"${commercial_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${commercial_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: aegisops is a commercial replacement for every siem/soar capability"

production_secret_repo="${workdir}/production-secret"
copy_valid_repo "${production_secret_repo}"
printf '%s\n' "Production secrets are valid evidence for Phase 62." >>"${production_secret_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production secrets are valid"

production_secret_evidence_repo="${workdir}/production-secret-evidence"
copy_valid_repo "${production_secret_evidence_repo}"
printf '%s\n' "Production secrets count as valid evidence." >>"${production_secret_evidence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_evidence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

production_secret_used_repo="${workdir}/production-secret-used"
copy_valid_repo "${production_secret_used_repo}"
printf '%s\n' "Production secrets may be used for validation." >>"${production_secret_used_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_used_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

production_secret_negative_context_repo="${workdir}/production-secret-negative-context"
copy_valid_repo "${production_secret_negative_context_repo}"
printf '%s\n' "Production secrets are not yet allowed." >>"${production_secret_negative_context_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${production_secret_negative_context_repo}"

phase62_readiness_repo="${workdir}/phase62-readiness"
copy_valid_repo "${phase62_readiness_repo}"
printf '%s\n' "Phase 62 is RC ready." >>"${phase62_readiness_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_readiness_direct_repo="${workdir}/phase62-readiness-direct"
copy_valid_repo "${phase62_readiness_direct_repo}"
printf '%s\n' "Phase 62 is commercially ready." >>"${phase62_readiness_direct_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_direct_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
printf 'Run /%s/example/Dev/codex-supervisor/dist/index.js.\n' "Users" >>"${absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

root_absolute_path_repo="${workdir}/root-absolute-path"
copy_valid_repo "${root_absolute_path_repo}"
printf 'Run /%s/example/Dev/codex-supervisor/dist/index.js.\n' "${root_segment}" >>"${root_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${root_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

tmp_absolute_path_repo="${workdir}/tmp-absolute-path"
copy_valid_repo "${tmp_absolute_path_repo}"
printf 'Run /tmp/aegisops/phase-62-closeout.\n' >>"${tmp_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${tmp_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

volume_absolute_path_repo="${workdir}/volume-absolute-path"
copy_valid_repo "${volume_absolute_path_repo}"
printf 'Run /Volumes/work/aegisops/phase-62-closeout.\n' >>"${volume_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${volume_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

echo "Phase 62 closeout verifier negative tests pass."
