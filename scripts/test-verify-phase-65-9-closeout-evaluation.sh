#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-9-closeout-evaluation.sh"

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

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

copy_valid_repo() {
  local target="$1"
  local path

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-65-closeout-evaluation.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-5-competitive-gap-matrix.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/phase-64-closeout-evaluation.md" \
    "docs/phase-65-1-release-bundle-inventory.md" \
    "docs/phase-65-2-offline-install-bundle-contract.md" \
    "docs/phase-65-3-release-channel-upgrade-manifest-contract.md" \
    "docs/phase-65-4-integrity-evidence-contract.md" \
    "docs/phase-65-5-oss-licensing-redistribution-checklist.md" \
    "docs/phase-65-6-default-smb-documentation-pack.md" \
    "docs/deployment/release/phase-65-3-upgrade-manifest.yaml" \
    "docs/deployment/release/phase-65-4-integrity-evidence.yaml" \
    "docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml" \
    "docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml" \
    "docs/migration/phase-65-7-standalone-wazuh-migration-guide.md" \
    "docs/migration/phase-65-7-standalone-shuffle-migration-guide.md" \
    "docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md" \
    "docs/deployment/release/phase-65-8-beta-known-limitations-template.md" \
    "docs/deployment/release/phase-65-8-design-partner-evidence-template.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-65-1-release-bundle-inventory.sh" \
    "scripts/test-verify-phase-65-1-release-bundle-inventory.sh" \
    "scripts/verify-phase-65-2-offline-install-bundle-contract.sh" \
    "scripts/test-verify-phase-65-2-offline-install-bundle-contract.sh" \
    "scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh" \
    "scripts/test-verify-phase-65-3-release-channel-upgrade-manifest.sh" \
    "scripts/verify-phase-65-4-integrity-evidence-contract.sh" \
    "scripts/test-verify-phase-65-4-integrity-evidence-contract.sh" \
    "scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh" \
    "scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh" \
    "scripts/verify-phase-65-6-default-smb-docs-pack.sh" \
    "scripts/test-verify-phase-65-6-default-smb-docs-pack.sh" \
    "scripts/verify-phase-65-7-migration-guides.sh" \
    "scripts/test-verify-phase-65-7-migration-guides.sh" \
    "scripts/verify-phase-65-8-beta-evidence-templates.sh" \
    "scripts/test-verify-phase-65-8-beta-evidence-templates.sh" \
    "scripts/verify-phase-65-9-closeout-evaluation.sh" \
    "scripts/test-verify-phase-65-9-closeout-evaluation.sh" \
    "scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh" \
    "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" \
    "scripts/verify-maintainability-hotspots.sh" \
    "scripts/verify-publishable-path-hygiene.sh"; do
    copy_repo_path "${target}" "${path}"
  done

  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs scripts control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-65-closeout-evaluation.md"
}

comment_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/<!-- $ENV{TEXT} -->/g' \
    "${target}/docs/phase-65-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 65 closeout evaluation"

missing_structured_artifact_repo="${workdir}/missing-structured-artifact"
copy_valid_repo "${missing_structured_artifact_repo}"
rm "${missing_structured_artifact_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_structured_artifact_repo}" "Missing Phase 65 closeout reference docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.9 closeout evaluation\]\(docs\/phase-65-closeout-evaluation\.md\)[^\n]*\n/- Phase 65.9 closeout evaluation\\n/' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical cross-phase boundary bullet"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1386 | Phase 65.8 beta known-limitations and design-partner evidence templates | Closed. \`docs/deployment/release/phase-65-8-beta-known-limitations-template.md\`, \`docs/deployment/release/phase-65-8-design-partner-evidence-template.md\`, and focused template verifier define beta/design-partner evidence-capture scaffolds without real beta evidence, real design-partner evidence collection, support-bundle completion, RC, GA, or commercial replacement readiness claims. |"
assert_fails_with "${missing_child_repo}" "Missing Phase 65 child issue outcome row in Child Issue Outcomes table"

commented_child_repo="${workdir}/commented-child"
copy_valid_repo "${commented_child_repo}"
comment_doc_text "${commented_child_repo}" \
  "| #1386 | Phase 65.8 beta known-limitations and design-partner evidence templates | Closed. \`docs/deployment/release/phase-65-8-beta-known-limitations-template.md\`, \`docs/deployment/release/phase-65-8-design-partner-evidence-template.md\`, and focused template verifier define beta/design-partner evidence-capture scaffolds without real beta evidence, real design-partner evidence collection, support-bundle completion, RC, GA, or commercial replacement readiness claims. |"
assert_fails_with "${commented_child_repo}" "Missing Phase 65 child issue outcome row in Child Issue Outcomes table"

missing_verifier_repo="${workdir}/missing-verifier"
copy_valid_repo "${missing_verifier_repo}"
remove_doc_text "${missing_verifier_repo}" "- \`bash scripts/verify-phase-65-8-beta-evidence-templates.sh\`"
assert_fails_with "${missing_verifier_repo}" "Missing Phase 65 verifier evidence line in Verifier Evidence section"

missing_verifier_script_repo="${workdir}/missing-verifier-script"
copy_valid_repo "${missing_verifier_script_repo}"
rm "${missing_verifier_script_repo}/scripts/verify-phase-65-8-beta-evidence-templates.sh"
assert_fails_with "${missing_verifier_script_repo}" "Missing Phase 65 verifier script scripts/verify-phase-65-8-beta-evidence-templates.sh"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1387 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${missing_issue_lint_repo}" "Missing Phase 65 issue-lint evidence line in Issue-lint evidence section"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "Phase 65 does not collect real beta launch evidence, conduct real design-partner interviews, prove real design-partner success, accept RC gates, accept GA gates, assemble Phase 66 RC packets, collect Phase 67 GA evidence, or approve production commercial distribution."
assert_fails_with "${missing_limitations_repo}" "Missing Phase 65 accepted limitations beta/RC/GA boundary"

missing_handoff_repo="${workdir}/missing-handoff"
copy_valid_repo "${missing_handoff_repo}"
remove_doc_text "${missing_handoff_repo}" \
  "Phase 66 can consume Phase 65 as subordinate RC packet planning input for packaging inventory, offline install package shape, release-channel metadata, upgrade/rollback posture, integrity evidence, licensing checklist posture, documentation coverage, migration guidance, known limitation template shape, design-partner evidence template shape, verifier coverage, and issue-lint coverage."
assert_fails_with "${missing_handoff_repo}" "Missing required Phase 65 closeout term"

rc_ready_repo="${workdir}/rc-ready"
copy_valid_repo "${rc_ready_repo}"
printf '%s\n' "Phase 65 proves readiness for RC." >>"${rc_ready_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${rc_ready_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

rc_ready_only_repo="${workdir}/rc-ready-only"
copy_valid_repo "${rc_ready_only_repo}"
printf '%s\n' "Phase 65 proves RC readiness only." >>"${rc_ready_only_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${rc_ready_only_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

rc_ready_wrapped_repo="${workdir}/rc-ready-wrapped"
copy_valid_repo "${rc_ready_wrapped_repo}"
printf '%s\n%s\n' "Phase 65 proves RC" "readiness." >>"${rc_ready_wrapped_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${rc_ready_wrapped_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

ga_ready_repo="${workdir}/ga-ready"
copy_valid_repo "${ga_ready_repo}"
printf '%s\n' "Phase 65 proves GA readiness." >>"${ga_ready_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${ga_ready_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

ga_ready_without_repo="${workdir}/ga-ready-without"
copy_valid_repo "${ga_ready_without_repo}"
printf '%s\n' "Phase 65 proves GA readiness without external evidence." >>"${ga_ready_without_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${ga_ready_without_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

support_complete_repo="${workdir}/support-complete"
copy_valid_repo "${support_complete_repo}"
printf '%s\n' "Support bundle evidence is complete." >>"${support_complete_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${support_complete_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

verifier_truth_repo="${workdir}/verifier-truth"
copy_valid_repo "${verifier_truth_repo}"
printf '%s\n' "Verifier output is readiness truth." >>"${verifier_truth_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${verifier_truth_repo}" "Forbidden Phase 65 closeout evaluation claim matched"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "api_key = abc123" >>"${secret_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

bearer_secret_repo="${workdir}/bearer-secret"
copy_valid_repo "${bearer_secret_repo}"
printf '%s\n' "Authorization: Bearer actual-production-token" >>"${bearer_secret_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${bearer_secret_repo}" "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "This closeout includes unredacted customer ticket data." >>"${customer_private_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_private_without_repo="${workdir}/customer-private-without"
copy_valid_repo "${customer_private_without_repo}"
printf '%s\n' "This closeout includes unredacted customer ticket data without redaction." >>"${customer_private_without_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${customer_private_without_repo}" "customer-private data detected"

path_repo="${workdir}/path"
copy_valid_repo "${path_repo}"
users_segment="Users"
printf '%s\n' "Operator note mentions /${users_segment}/local/repo." >>"${path_repo}/docs/phase-65-closeout-evaluation.md"
git -C "${path_repo}" add docs/phase-65-closeout-evaluation.md
git -C "${path_repo}" commit -q -m "path"
assert_fails_with "${path_repo}" "Forbidden Phase 65 closeout evaluation absolute path usage detected"

echo "Phase 65.9 closeout verifier self-test passes."
