#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-architecture-runbook-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/scripts"
}

write_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  printf '%s\n' "${content}" >"${target}/${path}"
}

write_architecture_verifier() {
  local target="$1"

  write_file "${target}" "scripts/verify-architecture-doc.sh" "#!/usr/bin/env bash
set -euo pipefail
repo_root=\"\${1:-\$(cd \"\$(dirname \"\${BASH_SOURCE[0]}\")/..\" && pwd)}\"
doc_path=\"\${repo_root}/docs/architecture.md\"

if [[ ! -f \"\${doc_path}\" ]]; then
  echo \"Missing architecture overview document: \${doc_path}\" >&2
  exit 1
fi

if ! grep -Fq \"This overview reflects the current approved baseline and must not be used to infer unapproved architecture changes.\" \"\${doc_path}\"; then
  echo \"Missing architecture statement\" >&2
  exit 1
fi

echo \"Architecture overview document is present and covers the approved baseline roles and boundaries.\""
}

write_runbook_verifier() {
  local target="$1"

  write_file "${target}" "scripts/verify-runbook-doc.sh" "#!/usr/bin/env bash
set -euo pipefail
repo_root=\"\${1:-\$(cd \"\$(dirname \"\${BASH_SOURCE[0]}\")/..\" && pwd)}\"
doc_path=\"\${repo_root}/docs/runbook.md\"

if [[ ! -f \"\${doc_path}\" ]]; then
  echo \"Missing runbook document: \${doc_path}\" >&2
  exit 1
fi

if ! grep -Fq \"Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure.\" \"\${doc_path}\"; then
  echo \"Missing runbook statement\" >&2
  exit 1
fi

echo \"Runbook document is present and captures a reviewed operator contract.\""
}

write_valid_docs() {
  local target="$1"

  write_file "${target}" "docs/architecture.md" "# AegisOps Architecture Overview

This overview reflects the current approved baseline and must not be used to infer unapproved architecture changes."

  write_file "${target}" "docs/runbook.md" "# AegisOps Runbook

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure."
}

write_valid_report() {
  local target="$1"

  write_file "${target}" "docs/architecture-runbook-validation.md" "# Architecture and Runbook Validation

- Validation date: 2026-04-24
- Baseline references: \`docs/architecture.md\`, \`docs/runbook.md\`, \`docs/requirements-baseline.md\`
- Verification commands: \`bash scripts/verify-architecture-doc.sh\`, \`bash scripts/verify-runbook-doc.sh\`
- Validation status: PASS

## Result

The approved architecture overview and concrete runbook contract remain aligned with the repository after the Phase 32 runbook refresh.

The current repository artifacts preserve the documented role boundaries, the reverse-proxy-only access model, and the reviewed repo-owned operator contract for startup, shutdown, restore, rollback, secret rotation, and business-hours health review.

The refreshed runbook narrative does not widen the approved architecture boundary, infer direct backend exposure, or silently authorize runtime scope beyond the current reviewed first-boot posture.

## Deviations

No deviations found."
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_architecture_verifier "${valid_repo}"
write_runbook_verifier "${valid_repo}"
write_valid_docs "${valid_repo}"
write_valid_report "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
write_architecture_verifier "${missing_report_repo}"
write_runbook_verifier "${missing_report_repo}"
write_valid_docs "${missing_report_repo}"
assert_fails_with "${missing_report_repo}" "Missing architecture and runbook validation result document"

missing_phrase_repo="${workdir}/missing-phrase"
create_repo "${missing_phrase_repo}"
write_architecture_verifier "${missing_phrase_repo}"
write_runbook_verifier "${missing_phrase_repo}"
write_valid_docs "${missing_phrase_repo}"
write_file "${missing_phrase_repo}" "docs/architecture-runbook-validation.md" "# Architecture and Runbook Validation

- Validation date: 2026-04-24
- Baseline references: \`docs/architecture.md\`, \`docs/runbook.md\`, \`docs/requirements-baseline.md\`
- Verification commands: \`bash scripts/verify-architecture-doc.sh\`, \`bash scripts/verify-runbook-doc.sh\`
- Validation status: PASS

## Result

Incomplete record."
assert_fails_with "${missing_phrase_repo}" "The approved architecture overview and concrete runbook contract remain aligned with the repository after the Phase 32 runbook refresh."

echo "verify-architecture-runbook-validation tests passed"
