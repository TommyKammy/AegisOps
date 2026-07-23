#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
doc_rel="docs/phase-66-7-rc-authority-boundary-proof-pack.md"

workdir="$(mktemp -d)"
real_worktree=""

cleanup() {
  if [[ -n "${real_worktree}" ]]; then
    git -C "${repo_root}" worktree remove --force "${real_worktree}" >/dev/null 2>&1 || true
  fi
  rm -rf "${workdir}"
}
trap cleanup EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

fixture_paths=(
  "README.md"
  "docs/phase-66-7-rc-authority-boundary-proof-pack.md"
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
  "docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
  "docs/phase-66-4-ai-assisted-triage-rc-proof.md"
  "docs/phase-66-5-report-export-rc-proof.md"
  "docs/phase-66-6-rc-supportability-proof.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-65-closeout-evaluation.md"
  "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"
  "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
  "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
  "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
  "scripts/verify-phase-66-5-report-export-rc-proof.sh"
  "scripts/verify-phase-66-6-rc-supportability-proof.sh"
  "scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
  "scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
  "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "scripts/verify-publishable-path-hygiene.sh"
)

observed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
follow_up_at="$(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
)"
local_user_home="$(printf '/%s/%s/' 'Users' 'example')"

packet_lines=(
  "journey_run_id=rc66-authority-001"
  "repository_revision=__REPOSITORY_REVISION__"
  "phase_66_1_evidence=evidence_id=sha256:__PHASE_66_1_DIGEST__; evidence_reference=docs/phase-66-1-clean-host-rc-e2e-harness.md; verifier=scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "phase_66_2_evidence=evidence_id=sha256:__PHASE_66_2_DIGEST__; evidence_reference=docs/phase-66-2-wazuh-sample-signal-rc-proof.md; verifier=scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "phase_66_3_evidence=evidence_id=sha256:__PHASE_66_3_DIGEST__; evidence_reference=docs/phase-66-3-shuffle-sample-execution-rc-proof.md; verifier=scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "phase_66_4_evidence=evidence_id=sha256:__PHASE_66_4_DIGEST__; evidence_reference=docs/phase-66-4-ai-assisted-triage-rc-proof.md; verifier=scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "phase_66_5_evidence=evidence_id=sha256:__PHASE_66_5_DIGEST__; evidence_reference=docs/phase-66-5-report-export-rc-proof.md; verifier=scripts/verify-phase-66-5-report-export-rc-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "phase_66_6_evidence=evidence_id=sha256:__PHASE_66_6_DIGEST__; evidence_reference=docs/phase-66-6-rc-supportability-proof.md; verifier=scripts/verify-phase-66-6-rc-supportability-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "wazuh_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=wazuh; attempt=source-truth-promotion; result=rejected; authoritative_record=aegisops://alerts/alert-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "shuffle_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=shuffle; attempt=execution-receipt-promotion; result=rejected; authoritative_record=aegisops://reconciliation/rec-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "ai_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=ai; attempt=approval-bypass; result=rejected; authoritative_record=aegisops://approvals/approval-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "ticket_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=tickets; attempt=case-closure-shortcut; result=rejected; authoritative_record=aegisops://cases/case-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "evidence_system_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=evidence-systems; attempt=external-evidence-truth-promotion; result=rejected; authoritative_record=aegisops://evidence/evidence-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "ui_cache_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=ui-cache; attempt=workflow-truth-promotion; result=rejected; authoritative_record=aegisops://audit/audit-ui-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "demo_data_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=demo-data; attempt=release-truth-promotion; result=rejected; authoritative_record=aegisops://releases/release-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "report_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=reports; attempt=gate-truth-promotion; result=rejected; authoritative_record=aegisops://gates/rc-gate-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "support_bundle_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=support-bundle; attempt=limitation-truth-promotion; result=rejected; authoritative_record=aegisops://limitations/lim-66-7-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "release_artifact_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=release-artifacts; attempt=readiness-truth-promotion; result=rejected; authoritative_record=aegisops://releases/release-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "verifier_output_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=verifier-output; attempt=rc-gate-promotion; result=rejected; authoritative_record=aegisops://gates/rc-gate-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "issue_lint_output_negative_evidence=evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=issue-lint-output; attempt=rc-gate-promotion; result=rejected; authoritative_record=aegisops://gates/rc-gate-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__REPOSITORY_REVISION__"
  "owner_review=reviewer=security-reviewer; reviewed_at=${observed_at}; disposition=accepted; follow_up_owner=release-owner"
  "limitation_references=evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/limitations.json; ids=lim-66-7-001; owner=release-owner; decision_at=${observed_at}; follow_up_at=${follow_up_at}"
  "non_claims=rc-evidence-only,not-rc-gate-pass,not-ga,not-production-operations,not-commercial-replacement,not-broad-siem-parity,not-broad-soar-parity,not-subordinate-truth"
)

write_negative_evidence_manifest() {
  local target="$1"

  mkdir -p "${target}/evidence/phase-66-7"
  TARGET="${target}" OBSERVED_AT="${observed_at}" python3 - <<'PY'
import json
import os
from pathlib import Path

records = [
    ("wazuh_negative_evidence", "wazuh", "source-truth-promotion", "aegisops://alerts/alert-001"),
    ("shuffle_negative_evidence", "shuffle", "execution-receipt-promotion", "aegisops://reconciliation/rec-001"),
    ("ai_negative_evidence", "ai", "approval-bypass", "aegisops://approvals/approval-001"),
    ("ticket_negative_evidence", "tickets", "case-closure-shortcut", "aegisops://cases/case-001"),
    ("evidence_system_negative_evidence", "evidence-systems", "external-evidence-truth-promotion", "aegisops://evidence/evidence-001"),
    ("ui_cache_negative_evidence", "ui-cache", "workflow-truth-promotion", "aegisops://audit/audit-ui-001"),
    ("demo_data_negative_evidence", "demo-data", "release-truth-promotion", "aegisops://releases/release-001"),
    ("report_negative_evidence", "reports", "gate-truth-promotion", "aegisops://gates/rc-gate-001"),
    ("support_bundle_negative_evidence", "support-bundle", "limitation-truth-promotion", "aegisops://limitations/lim-66-7-001"),
    ("release_artifact_negative_evidence", "release-artifacts", "readiness-truth-promotion", "aegisops://releases/release-001"),
    ("verifier_output_negative_evidence", "verifier-output", "rc-gate-promotion", "aegisops://gates/rc-gate-001"),
    ("issue_lint_output_negative_evidence", "issue-lint-output", "rc-gate-promotion", "aegisops://gates/rc-gate-001"),
]
manifest = {
    "schema_version": "phase-66-7-negative-evidence/v1",
    "records": [
        {
            "field": field,
            "surface": surface,
            "attempt": attempt,
            "result": "rejected",
            "authoritative_record": authoritative_record,
            "observed_at": os.environ["OBSERVED_AT"],
            "journey_run_id": "rc66-authority-001",
        }
        for field, surface, attempt, authoritative_record in records
    ],
}
path = Path(os.environ["TARGET"]) / "evidence/phase-66-7/negative-observations.json"
path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

write_limitation_manifest() {
  local target="$1"

  mkdir -p "${target}/evidence/phase-66-7"
  TARGET="${target}" OBSERVED_AT="${observed_at}" FOLLOW_UP_AT="${follow_up_at}" python3 - <<'PY'
import json
import os
from pathlib import Path

manifest = {
    "schema_version": "phase-66-7-limitations/v1",
    "limitations": [
        {
            "id": "lim-66-7-001",
            "owner": "release-owner",
            "disposition": "accepted",
            "decision_at": os.environ["OBSERVED_AT"],
            "follow_up_at": os.environ["FOLLOW_UP_AT"],
        }
    ],
}
path = Path(os.environ["TARGET"]) / "evidence/phase-66-7/limitations.json"
path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

copy_valid_repo() {
  local target="$1"
  local path

  mkdir -p "${target}"
  for path in "${fixture_paths[@]}"; do
    mkdir -p "${target}/$(dirname "${path}")"
    cp "${repo_root}/${path}" "${target}/${path}"
  done
  for path in "${target}"/scripts/verify-phase-66-[1-6]-*.sh; do
    printf '%s\n' \
      '#!/usr/bin/env bash' \
      'set -euo pipefail' \
      'exit 0' >"${path}"
    chmod +x "${path}"
  done
  write_negative_evidence_manifest "${target}"
  write_limitation_manifest "${target}"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Phase 66.7 Self Test"
  git -C "${target}" config user.email "phase-66-7-self-test@invalid.example"
  git -C "${target}" add .
  git -C "${target}" commit -qm "fixture"
}

assert_passes() {
  local target="$1"

  if ! PHASE66_7_SKIP_PATH_HYGIENE=1 bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if PHASE66_7_SKIP_PATH_HYGIENE=1 bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi
  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' "${target}/${doc_rel}"
}

append_doc_line() {
  local target="$1"
  local line="$2"

  printf '\n%s\n' "${line}" >>"${target}/${doc_rel}"
}

replace_packet_field() {
  local target="$1"
  local field="$2"
  local value="$3"

  FIELD="${field}" VALUE="${value}" perl -0pi -e \
    's/^\Q$ENV{FIELD}\E=.*$/$ENV{FIELD} . "=" . $ENV{VALUE}/me' \
    "${target}/${doc_rel}"
}

materialize_packet_line() {
  local target="$1"
  local repository_revision="$2"
  local line="$3"
  local phase
  local placeholder
  local reference
  local digest

  line="${line//__REPOSITORY_REVISION__/${repository_revision}}"
  line="${line//__TARGET_REVISION__/${repository_revision}}"
  for phase in 1 2 3 4 5 6; do
    placeholder="__PHASE_66_${phase}_DIGEST__"
    if [[ "${line}" != *"${placeholder}"* ]]; then
      continue
    fi
    case "${phase}" in
      1) reference="docs/phase-66-1-clean-host-rc-e2e-harness.md" ;;
      2) reference="docs/phase-66-2-wazuh-sample-signal-rc-proof.md" ;;
      3) reference="docs/phase-66-3-shuffle-sample-execution-rc-proof.md" ;;
      4) reference="docs/phase-66-4-ai-assisted-triage-rc-proof.md" ;;
      5) reference="docs/phase-66-5-report-export-rc-proof.md" ;;
      6) reference="docs/phase-66-6-rc-supportability-proof.md" ;;
    esac
    digest="$(
      git -C "${target}" show "${repository_revision}:${reference}" |
        shasum -a 256 |
        awk '{print $1}'
    )"
    line="${line//${placeholder}/${digest}}"
  done
  if [[ "${line}" == *"__NEGATIVE_EVIDENCE_DIGEST__"* ]]; then
    reference="evidence/phase-66-7/negative-observations.json"
    if git -C "${target}" cat-file -e "${repository_revision}:${reference}" 2>/dev/null; then
      digest="$(
        git -C "${target}" show "${repository_revision}:${reference}" |
          shasum -a 256 |
          awk '{print $1}'
      )"
    else
      digest="0000000000000000000000000000000000000000000000000000000000000000"
    fi
    line="${line//__NEGATIVE_EVIDENCE_DIGEST__/${digest}}"
  fi
  if [[ "${line}" == *"__LIMITATION_EVIDENCE_DIGEST__"* ]]; then
    reference="evidence/phase-66-7/limitations.json"
    if git -C "${target}" cat-file -e "${repository_revision}:${reference}" 2>/dev/null; then
      digest="$(
        git -C "${target}" show "${repository_revision}:${reference}" |
          shasum -a 256 |
          awk '{print $1}'
      )"
    else
      digest="0000000000000000000000000000000000000000000000000000000000000000"
    fi
    line="${line//__LIMITATION_EVIDENCE_DIGEST__/${digest}}"
  fi
  printf '%s\n' "${line}"
}

append_complete_packet() {
  local target="$1"
  local repository_revision
  local line

  repository_revision="$(git -C "${target}" rev-parse HEAD)"
  printf '\n## Test Evidence Packet\n\n' >>"${target}/${doc_rel}"
  for line in "${packet_lines[@]}"; do
    materialize_packet_line "${target}" "${repository_revision}" "${line}" >>"${target}/${doc_rel}"
  done
}

append_complete_table_packet() {
  local target="$1"
  local repository_revision
  local line
  local field
  local value

  repository_revision="$(git -C "${target}" rev-parse HEAD)"
  printf '\n## Test Table Evidence Packet\n\n| Field | Value |\n| --- | --- |\n' >>"${target}/${doc_rel}"
  for line in "${packet_lines[@]}"; do
    line="$(materialize_packet_line "${target}" "${repository_revision}" "${line}")"
    field="${line%%=*}"
    value="${line#*=}"
    printf '| `%s` | %s |\n' "${field}" "${value}" >>"${target}/${doc_rel}"
  done
}

packet_mutation_case() {
  local name="$1"
  local field="$2"
  local value="$3"
  local expected="$4"
  local target="${workdir}/${name}"
  local target_revision

  copy_valid_repo "${target}"
  append_complete_packet "${target}"
  target_revision="$(git -C "${target}" rev-parse HEAD)"
  value="$(materialize_packet_line "${target}" "${target_revision}" "${field}=${value}")"
  value="${value#*=}"
  replace_packet_field "${target}" "${field}" "${value}"
  assert_fails_with "${target}" "${expected}"
}

leak_case() {
  local name="$1"
  local value="$2"
  local expected="$3"
  local target="${workdir}/${name}"

  copy_valid_repo "${target}"
  append_doc_line "${target}" "${value}"
  assert_fails_with "${target}" "${expected}"
}

overclaim_case() {
  local name="$1"
  local claim="$2"
  local target="${workdir}/${name}"

  copy_valid_repo "${target}"
  append_doc_line "${target}" "${claim}"
  assert_fails_with "${target}" "authority or readiness overclaim detected"
}

allowed_doc_line_case() {
  local name="$1"
  local claim="$2"
  local target="${workdir}/${name}"

  copy_valid_repo "${target}"
  append_doc_line "${target}" "${claim}"
  assert_passes "${target}"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

assignment_repo="${workdir}/assignment"
copy_valid_repo "${assignment_repo}"
append_complete_packet "${assignment_repo}"
assert_passes "${assignment_repo}"

table_repo="${workdir}/table"
copy_valid_repo "${table_repo}"
append_complete_table_packet "${table_repo}"
assert_passes "${table_repo}"

committed_packet_repo="${workdir}/committed-packet"
copy_valid_repo "${committed_packet_repo}"
append_complete_packet "${committed_packet_repo}"
git -C "${committed_packet_repo}" add "${doc_rel}"
git -C "${committed_packet_repo}" commit -qm "store proof packet"
assert_passes "${committed_packet_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/${doc_rel}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.7 RC authority-boundary proof pack"

missing_reference_repo="${workdir}/missing-reference"
copy_valid_repo "${missing_reference_repo}"
rm "${missing_reference_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${missing_reference_repo}" "Missing Phase 66.7 reference"

missing_script_repo="${workdir}/missing-script"
copy_valid_repo "${missing_script_repo}"
rm "${missing_script_repo}/scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
assert_fails_with "${missing_script_repo}" "Missing Phase 66.7 verifier script"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
TEXT="- [Phase 66.7 RC authority-boundary proof pack]" perl -0pi -e \
  's/^\Q$ENV{TEXT}\E.*\n//m' "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.7 boundary statement"

missing_statement_repo="${workdir}/missing-statement"
copy_valid_repo "${missing_statement_repo}"
remove_doc_text "${missing_statement_repo}" "Passing one negative observation cannot compensate for a missing surface."
assert_fails_with "${missing_statement_repo}" "Missing Phase 66.7 RC authority-boundary proof-pack statement"

commented_statement_repo="${workdir}/commented-statement"
copy_valid_repo "${commented_statement_repo}"
remove_doc_text "${commented_statement_repo}" "Passing one negative observation cannot compensate for a missing surface."
append_doc_line "${commented_statement_repo}" "<!-- Passing one negative observation cannot compensate for a missing surface. -->"
assert_fails_with "${commented_statement_repo}" "Missing Phase 66.7 RC authority-boundary proof-pack statement"

fenced_statement_repo="${workdir}/fenced-statement"
copy_valid_repo "${fenced_statement_repo}"
remove_doc_text "${fenced_statement_repo}" "Passing one negative observation cannot compensate for a missing surface."
append_doc_line "${fenced_statement_repo}" $'```\nPassing one negative observation cannot compensate for a missing surface.\n```'
assert_fails_with "${fenced_statement_repo}" "Missing Phase 66.7 RC authority-boundary proof-pack statement"

missing_schema_repo="${workdir}/missing-schema"
copy_valid_repo "${missing_schema_repo}"
TEXT='| `ai_negative_evidence` |' perl -0pi -e 's/^\Q$ENV{TEXT}\E.*\n//m' \
  "${missing_schema_repo}/${doc_rel}"
assert_fails_with "${missing_schema_repo}" "missing proof-packet field ai_negative_evidence"

missing_matrix_repo="${workdir}/missing-matrix"
copy_valid_repo "${missing_matrix_repo}"
TEXT='| UI cache | `workflow-truth-promotion` |' perl -0pi -e 's/^\Q$ENV{TEXT}\E.*\n//m' \
  "${missing_matrix_repo}/${doc_rel}"
assert_fails_with "${missing_matrix_repo}" "missing negative evidence matrix row for UI cache"

partial_repo="${workdir}/partial"
copy_valid_repo "${partial_repo}"
append_doc_line "${partial_repo}" $'## Partial Evidence Packet\n\njourney_run_id=rc66-authority-001'
assert_fails_with "${partial_repo}" "partial evidence packet"

cross_section_repo="${workdir}/cross-section"
copy_valid_repo "${cross_section_repo}"
append_doc_line "${cross_section_repo}" $'## Packet A\n\njourney_run_id=rc66-authority-001\n\n## Packet B\n\nrepository_revision=0123456789012345678901234567890123456789'
assert_fails_with "${cross_section_repo}" "partial evidence packet in"

duplicate_repo="${workdir}/duplicate"
copy_valid_repo "${duplicate_repo}"
append_complete_packet "${duplicate_repo}"
append_complete_packet "${duplicate_repo}"
assert_fails_with "${duplicate_repo}" "multiple materialized values across evidence packets"

yaml_repo="${workdir}/yaml"
copy_valid_repo "${yaml_repo}"
append_doc_line "${yaml_repo}" "journey_run_id: rc66-authority-001"
assert_fails_with "${yaml_repo}" "JSON, YAML, and object-literal evidence syntax is not supported"

json_repo="${workdir}/json"
copy_valid_repo "${json_repo}"
append_doc_line "${json_repo}" '{"repository_revision":"0123456789012345678901234567890123456789"}'
assert_fails_with "${json_repo}" "JSON, YAML, and object-literal evidence syntax is not supported"

html_table_repo="${workdir}/html-table"
copy_valid_repo "${html_table_repo}"
append_doc_line \
  "${html_table_repo}" \
  '<table><tr><td>journey_run_id</td><td>rc66-fabricated-001</td></tr><tr><td>repository_revision</td><td>0000000000000000000000000000000000000000</td></tr></table>'
assert_fails_with "${html_table_repo}" "raw HTML evidence syntax is not supported"

multiline_html_table_repo="${workdir}/multiline-html-table"
copy_valid_repo "${multiline_html_table_repo}"
append_doc_line \
  "${multiline_html_table_repo}" \
  $'<table>\n<tr><td>journey_run_id</td><td>rc66-fabricated-001</td></tr>\n</table>'
assert_fails_with "${multiline_html_table_repo}" "raw HTML evidence syntax is not supported"

inline_html_field_repo="${workdir}/inline-html-field"
copy_valid_repo "${inline_html_field_repo}"
append_doc_line \
  "${inline_html_field_repo}" \
  'journey_<span></span>run_id=rc66-fabricated-001'
assert_fails_with "${inline_html_field_repo}" "raw HTML evidence syntax is not supported"

packet_mutation_case \
  "bad-journey" \
  "journey_run_id" \
  "run-001" \
  "invalid journey_run_id"

packet_mutation_case \
  "bad-revision" \
  "repository_revision" \
  "0123456789012345678901234567890123456789" \
  "evidence-producing revision is not a commit in this repository"

packet_mutation_case \
  "mixed-phase-run" \
  "phase_66_2_evidence" \
  "evidence_id=sha256:__PHASE_66_2_DIGEST__; evidence_reference=docs/phase-66-2-wazuh-sample-signal-rc-proof.md; verifier=scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh; result=passed; journey_run_id=rc66-other-001; repository_revision=__TARGET_REVISION__" \
  "mixed journey_run_id"

packet_mutation_case \
  "wrong-phase-verifier" \
  "phase_66_4_evidence" \
  "evidence_id=sha256:__PHASE_66_4_DIGEST__; evidence_reference=docs/phase-66-4-ai-assisted-triage-rc-proof.md; verifier=scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "unexpected verifier path"

packet_mutation_case \
  "failed-phase-result" \
  "phase_66_5_evidence" \
  "evidence_id=sha256:__PHASE_66_5_DIGEST__; evidence_reference=docs/phase-66-5-report-export-rc-proof.md; verifier=scripts/verify-phase-66-5-report-export-rc-proof.sh; result=failed; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "verifier result must be passed"

packet_mutation_case \
  "wrong-evidence-reference" \
  "phase_66_3_evidence" \
  "evidence_id=sha256:__PHASE_66_3_DIGEST__; evidence_reference=docs/phase-66-2-wazuh-sample-signal-rc-proof.md; verifier=scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "unexpected evidence reference"

packet_mutation_case \
  "fabricated-evidence-id" \
  "phase_66_1_evidence" \
  "evidence_id=sha256:0000000000000000000000000000000000000000000000000000000000000000; evidence_reference=docs/phase-66-1-clean-host-rc-e2e-harness.md; verifier=scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh; result=passed; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "evidence_id does not match resolved evidence reference"

failing_prerequisite_repo="${workdir}/failing-prerequisite"
copy_valid_repo "${failing_prerequisite_repo}"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'echo "simulated prerequisite failure" >&2' \
  'exit 1' \
  >"${failing_prerequisite_repo}/scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
chmod +x "${failing_prerequisite_repo}/scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
git -C "${failing_prerequisite_repo}" add scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh
git -C "${failing_prerequisite_repo}" commit -qm "fail prerequisite verifier"
append_complete_packet "${failing_prerequisite_repo}"
assert_fails_with "${failing_prerequisite_repo}" "prerequisite verifier failed: simulated prerequisite failure"

missing_negative_manifest_repo="${workdir}/missing-negative-manifest"
copy_valid_repo "${missing_negative_manifest_repo}"
rm "${missing_negative_manifest_repo}/evidence/phase-66-7/negative-observations.json"
git -C "${missing_negative_manifest_repo}" add -u
git -C "${missing_negative_manifest_repo}" commit -qm "remove negative evidence manifest"
append_complete_packet "${missing_negative_manifest_repo}"
assert_fails_with \
  "${missing_negative_manifest_repo}" \
  "negative evidence reference does not resolve at repository_revision"

malformed_negative_manifest_repo="${workdir}/malformed-negative-manifest"
copy_valid_repo "${malformed_negative_manifest_repo}"
printf '{invalid-json\n' \
  >"${malformed_negative_manifest_repo}/evidence/phase-66-7/negative-observations.json"
git -C "${malformed_negative_manifest_repo}" add evidence/phase-66-7/negative-observations.json
git -C "${malformed_negative_manifest_repo}" commit -qm "malform negative evidence manifest"
append_complete_packet "${malformed_negative_manifest_repo}"
assert_fails_with \
  "${malformed_negative_manifest_repo}" \
  "negative evidence reference must contain valid UTF-8 JSON"

incomplete_negative_manifest_repo="${workdir}/incomplete-negative-manifest"
copy_valid_repo "${incomplete_negative_manifest_repo}"
MANIFEST="${incomplete_negative_manifest_repo}/evidence/phase-66-7/negative-observations.json" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["MANIFEST"])
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest["records"].pop()
path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
git -C "${incomplete_negative_manifest_repo}" add evidence/phase-66-7/negative-observations.json
git -C "${incomplete_negative_manifest_repo}" commit -qm "drop negative evidence record"
append_complete_packet "${incomplete_negative_manifest_repo}"
assert_fails_with \
  "${incomplete_negative_manifest_repo}" \
  "negative evidence manifest must contain exactly one record for every required surface"

packet_mutation_case \
  "wrong-surface" \
  "ai_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=wazuh; attempt=approval-bypass; result=rejected; authoritative_record=aegisops://approvals/approval-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "expected surface ai"

packet_mutation_case \
  "wrong-attempt" \
  "ticket_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=tickets; attempt=workflow-truth-promotion; result=rejected; authoritative_record=aegisops://cases/case-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "expected rejected attempt case-closure-shortcut"

packet_mutation_case \
  "non-rejected-result" \
  "shuffle_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=shuffle; attempt=execution-receipt-promotion; result=accepted; authoritative_record=aegisops://reconciliation/rec-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "result must be rejected"

packet_mutation_case \
  "invalid-authority-record" \
  "report_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=reports; attempt=gate-truth-promotion; result=rejected; authoritative_record=report-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "must be a specific aegisops:// reference"

packet_mutation_case \
  "stale-observation" \
  "wazuh_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=wazuh; attempt=source-truth-promotion; result=rejected; authoritative_record=aegisops://alerts/alert-001; observed_at=2000-01-01T00:00:00Z; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "timestamp is stale"

packet_mutation_case \
  "future-observation" \
  "wazuh_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=wazuh; attempt=source-truth-promotion; result=rejected; authoritative_record=aegisops://alerts/alert-001; observed_at=2999-01-01T00:00:00Z; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "timestamp is too far in the future"

packet_mutation_case \
  "fabricated-negative-evidence-id" \
  "ai_negative_evidence" \
  "evidence_id=sha256:0000000000000000000000000000000000000000000000000000000000000000; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=ai; attempt=approval-bypass; result=rejected; authoritative_record=aegisops://approvals/approval-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "evidence_id does not match resolved evidence reference"

packet_mutation_case \
  "wrong-negative-evidence-reference" \
  "ai_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/invented.json; surface=ai; attempt=approval-bypass; result=rejected; authoritative_record=aegisops://approvals/approval-001; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "unexpected evidence reference"

packet_mutation_case \
  "invented-authoritative-record" \
  "wazuh_negative_evidence" \
  "evidence_id=sha256:__NEGATIVE_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/negative-observations.json; surface=wazuh; attempt=source-truth-promotion; result=rejected; authoritative_record=aegisops://alerts/invented-999; observed_at=${observed_at}; journey_run_id=rc66-authority-001; repository_revision=__TARGET_REVISION__" \
  "resolved negative evidence record does not match packet"

packet_mutation_case \
  "rejected-owner-review" \
  "owner_review" \
  "reviewer=security-reviewer; reviewed_at=${observed_at}; disposition=rejected; follow_up_owner=release-owner" \
  "disposition must be accepted"

packet_mutation_case \
  "artifact-reviewer" \
  "owner_review" \
  "reviewer=verifier-bot; reviewed_at=${observed_at}; disposition=accepted; follow_up_owner=release-owner" \
  "reviewer must be accountable"

packet_mutation_case \
  "invalid-follow-up" \
  "limitation_references" \
  "evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/limitations.json; ids=lim-66-7-001; owner=release-owner; decision_at=${observed_at}; follow_up_at=2000-01-01T00:00:00Z" \
  "follow_up_at must be after decision_at"

packet_mutation_case \
  "fabricated-limitation-evidence-id" \
  "limitation_references" \
  "evidence_id=sha256:0000000000000000000000000000000000000000000000000000000000000000; evidence_reference=evidence/phase-66-7/limitations.json; ids=lim-66-7-001; owner=release-owner; decision_at=${observed_at}; follow_up_at=${follow_up_at}" \
  "evidence_id does not match resolved evidence reference"

packet_mutation_case \
  "wrong-limitation-evidence-reference" \
  "limitation_references" \
  "evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/invented-limitations.json; ids=lim-66-7-001; owner=release-owner; decision_at=${observed_at}; follow_up_at=${follow_up_at}" \
  "unexpected evidence reference"

packet_mutation_case \
  "invented-limitation-id" \
  "limitation_references" \
  "evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/limitations.json; ids=lim-invented-999; owner=release-owner; decision_at=${observed_at}; follow_up_at=${follow_up_at}" \
  "limitation lim-invented-999 does not resolve at repository_revision"

packet_mutation_case \
  "invented-limitation-owner" \
  "limitation_references" \
  "evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/limitations.json; ids=lim-66-7-001; owner=imaginary-owner; decision_at=${observed_at}; follow_up_at=${follow_up_at}" \
  "resolved limitation record lim-66-7-001 does not match packet"

packet_mutation_case \
  "automated-limitation-owner" \
  "limitation_references" \
  "evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/limitations.json; ids=lim-66-7-001; owner=verifier-bot; decision_at=${observed_at}; follow_up_at=${follow_up_at}" \
  "owner must be accountable"

packet_mutation_case \
  "noncanonical-limitation-id" \
  "limitation_references" \
  "evidence_id=sha256:__LIMITATION_EVIDENCE_DIGEST__; evidence_reference=evidence/phase-66-7/limitations.json; ids=LIM-66-7-001; owner=release-owner; decision_at=${observed_at}; follow_up_at=${follow_up_at}" \
  "ids must be explicit lim-* identifiers"

missing_limitation_manifest_repo="${workdir}/missing-limitation-manifest"
copy_valid_repo "${missing_limitation_manifest_repo}"
rm "${missing_limitation_manifest_repo}/evidence/phase-66-7/limitations.json"
git -C "${missing_limitation_manifest_repo}" add -u
git -C "${missing_limitation_manifest_repo}" commit -qm "remove limitation manifest"
append_complete_packet "${missing_limitation_manifest_repo}"
assert_fails_with \
  "${missing_limitation_manifest_repo}" \
  "limitation evidence reference does not resolve at repository_revision"

malformed_limitation_manifest_repo="${workdir}/malformed-limitation-manifest"
copy_valid_repo "${malformed_limitation_manifest_repo}"
printf '{invalid-json\n' \
  >"${malformed_limitation_manifest_repo}/evidence/phase-66-7/limitations.json"
git -C "${malformed_limitation_manifest_repo}" add evidence/phase-66-7/limitations.json
git -C "${malformed_limitation_manifest_repo}" commit -qm "malform limitation manifest"
append_complete_packet "${malformed_limitation_manifest_repo}"
assert_fails_with \
  "${malformed_limitation_manifest_repo}" \
  "limitation evidence reference must contain valid UTF-8 JSON"

unaccepted_limitation_repo="${workdir}/unaccepted-limitation"
copy_valid_repo "${unaccepted_limitation_repo}"
MANIFEST="${unaccepted_limitation_repo}/evidence/phase-66-7/limitations.json" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["MANIFEST"])
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest["limitations"][0]["disposition"] = "proposed"
path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
git -C "${unaccepted_limitation_repo}" add evidence/phase-66-7/limitations.json
git -C "${unaccepted_limitation_repo}" commit -qm "mark limitation proposed"
append_complete_packet "${unaccepted_limitation_repo}"
assert_fails_with \
  "${unaccepted_limitation_repo}" \
  "limitation manifest record lim-66-7-001 must be accepted"

packet_mutation_case \
  "missing-non-claim" \
  "non_claims" \
  "rc-evidence-only,not-rc-gate-pass,not-ga,not-production-operations,not-commercial-replacement,not-broad-siem-parity,not-broad-soar-parity" \
  "missing not-subordinate-truth"

packet_mutation_case \
  "extra-non-claim" \
  "non_claims" \
  "rc-evidence-only,not-rc-gate-pass,not-ga,not-production-operations,not-commercial-replacement,not-broad-siem-parity,not-broad-soar-parity,not-subordinate-truth,ready" \
  "unexpected ready"

leak_case \
  "access-key" \
  "authorization=Bearer AKIA1234567890ABCDEF" \
  "production secret-looking value detected"

leak_case \
  "private-key" \
  "-----BEGIN PRIVATE KEY-----" \
  "production secret-looking value detected"

leak_case \
  "local-path" \
  "artifact=${local_user_home}operator/proof.json" \
  "workstation-local path detected"

leak_case \
  "email" \
  "customer_contact=analyst@example.com" \
  "customer-private or ticket-private data detected"

leak_case \
  "private-ticket" \
  "ticket_private_content=customer-payload" \
  "customer-private or ticket-private data detected"

leak_case \
  "nested-api-key" \
  "debug_note=reviewed; api_key=supersecretvalue123; disposition=accepted" \
  "production secret-looking value detected"

leak_case \
  "spaced-api-key" \
  "API key: supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "hyphenated-api-key" \
  "api-key=supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "connected-api-key" \
  "APIKey=supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "prefixed-api-key" \
  "X-API-Key=supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "spaced-client-secret" \
  "client secret: supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "hyphenated-access-token" \
  "access-token=supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "spaced-refresh-token" \
  "refresh token: supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "spaced-secret-key" \
  "secret key: supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "spaced-private-key" \
  "private key: supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "html-entity-spaced-api-key" \
  "API&nbsp;key&colon;supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "html-tag-split-api-key-assignment" \
  "api_key<span></span>=supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "html-tag-split-api-key-name" \
  "API <em></em>key: supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "html-attribute-api-key" \
  '<span api_key="supersecretvalue123"></span>' \
  "production secret-looking value detected"

leak_case \
  "html-comment-api-key" \
  "<!-- api_key=supersecretvalue123 -->" \
  "production secret-looking value detected"

leak_case \
  "secret-after-redaction-marker" \
  "api_key=redacted supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "html-entity-secret-assignment" \
  "api_key&#61;supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "numeric-html-entity-secret-assignment" \
  "api_key&#x3d;supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "html-entity-secret-field-and-colon" \
  "api&#95;key&colon;supersecretvalue123" \
  "production secret-looking value detected"

leak_case \
  "nested-customer-name" \
  "debug_note=reviewed; customer_name=AcmeCorp; disposition=accepted" \
  "customer-private or ticket-private data detected"

leak_case \
  "private-data-after-redaction-marker" \
  "customer_name=redacted AcmeCorp" \
  "customer-private or ticket-private data detected"

leak_case \
  "html-entity-private-assignment" \
  "customer_name&#61;AcmeCorp" \
  "customer-private or ticket-private data detected"

leak_case \
  "unrelated-denial-before-private-data-claim" \
  "The proof pack does not preserve formatting and includes raw customer payload." \
  "customer-private or ticket-private data detected"

leak_case \
  "denied-then-positive-private-data-claim" \
  "The proof pack does not include raw customer payload but includes raw customer payload." \
  "customer-private or ticket-private data detected"

leak_case \
  "html-entity-private-data-claim" \
  "The proof pack includes raw&nbsp;customer payload." \
  "customer-private or ticket-private data detected"

leak_case \
  "html-entity-email" \
  "customer_contact=analyst&#64;example.com" \
  "customer-private or ticket-private data detected"

leak_case \
  "html-entity-local-path" \
  "artifact=&#47;Users&#47;example&#47;proof.json" \
  "workstation-local path detected"

leak_case \
  "positive-then-denied-private-data-claim" \
  "The proof pack includes raw customer payload but does not preserve formatting." \
  "customer-private or ticket-private data detected"

leak_case \
  "bare-not-before-private-data-claim" \
  "The proof pack is not safe because it includes raw customer payload." \
  "customer-private or ticket-private data detected"

leak_case \
  "unrelated-never-before-private-data-claim" \
  "The proof pack never alters formatting then includes raw customer payload." \
  "customer-private or ticket-private data detected"

overclaim_case "wazuh-truth" "Wazuh is authoritative alert truth."
overclaim_case "reverse-wazuh-truth" "Alert truth is owned by Wazuh."
overclaim_case "shuffle-execution" "Shuffle may execute and close the case."
overclaim_case "ai-approval" "AI output can approve the action."
overclaim_case "mandatory-ai-approval" "AI output must approve the action."
overclaim_case "advisory-ai-approval" "AI output should approve the action."
overclaim_case "shall-ai-execution" "AI output shall execute the action."
overclaim_case "required-ai-approval" "AI output is required to approve the action."
overclaim_case "obligated-ai-execution" "AI output is obligated to execute the action."
overclaim_case "ai-has-to-approve" "AI output has to approve the action."
overclaim_case "ai-needs-to-execute" "AI output needs to execute the action."
overclaim_case "ai-ought-to-approve" "AI output ought to approve the action."
overclaim_case "unrelated-denial-before-mandatory-ai-approval" "AI output cannot recommend changes and must approve the action."
overclaim_case "html-tag-split-mandatory-ai-approval" "AI <span></span>output must approve the action."
overclaim_case "ai-permitted-approval" "AI output is permitted to approve the action."
overclaim_case "ai-authorized-execution" "AI output is authorized to execute the action."
overclaim_case "ai-has-authority" "AI output has authority to approve the action."
overclaim_case "ai-granted-permission" "AI output is granted permission to execute the action."
overclaim_case "ai-granted-explicit-permission" "AI output is granted explicit permission to execute the action."
overclaim_case "ai-empowered-closure" "AI output is empowered to close the case."
overclaim_case "ai-has-been-authorized" "AI output has been authorized to execute the action."
overclaim_case "ai-policy-permission" "AI output is permitted by policy to approve the action."
overclaim_case "ai-authorized-direct-execution" "AI output is authorized to directly execute the action."
overclaim_case "unrelated-negation-before-ai-permission" "AI output is not advisory but is permitted to approve the action."
overclaim_case "html-entity-ai-approval" "AI&nbsp;output can approve the action."
overclaim_case "numeric-html-entity-ai-approval" "AI&#32;output can approve the action."
overclaim_case "html-entity-ai-subject" "A&#73;&nbsp;output can approve the action."
overclaim_case "direct-ai-approval" "AI output approves the action."
overclaim_case "unrelated-negation-before-ai-approval" "AI output is not advisory and can approve the action."
overclaim_case "unrelated-negation-before-pronoun-approval" "AI output is not advisory, but it can approve the action."
overclaim_case "unrelated-negation-before-direct-approval" "AI output is not advisory and independently approves the action."
overclaim_case "elided-ai-execution" "AI output cannot approve the action; can execute the action."
overclaim_case "elided-direct-ai-execution" "AI output cannot approve the action; independently executes the action."
overclaim_case "adversative-elided-ai-execution" "AI output cannot approve the action but can execute the action."
overclaim_case "elided-ai-truth" "AI output is not authoritative; is approval truth."
overclaim_case "ai-plural-case-closure" "AI output can close cases."
overclaim_case "ai-article-case-closure" "AI output can close a case."
overclaim_case "direct-ai-demonstrative-case-closure" "AI output closes this case."
overclaim_case "authorized-ai-any-case-closure" "AI output is authorized to close any case."
overclaim_case "ai-individual-case-closure" "AI output can close an individual case."
overclaim_case "direct-ai-single-case-closure" "AI output closes a single case."
overclaim_case "ticket-closure" "Tickets can close the case."
overclaim_case "external-evidence-truth" "External evidence is evidence truth."
overclaim_case "ui-cache-truth" "UI cache is workflow truth."
overclaim_case "demo-data-truth" "Demo data is release truth."
overclaim_case "report-gate" "Reports are gate truth."
overclaim_case "support-truth" "Support bundles are limitation truth."
overclaim_case "release-readiness" "Release artifacts prove RC readiness."
overclaim_case "verifier-readiness" "Verifier output confirms RC readiness."
overclaim_case "issue-lint-truth" "Issue-lint output is release truth."
overclaim_case "ga-overclaim" "Phase 66.7 proves GA readiness."
overclaim_case "production-overclaim" "Phase 66.7 enables production rollout."
overclaim_case "broad-siem" "Phase 66.7 achieves broad enterprise SIEM parity."
overclaim_case "broad-soar" "Phase 66.7 achieves broad enterprise SOAR parity."
overclaim_case "approval-bypass" "Approval bypass is allowed."
overclaim_case "execution-bypass" "Execution bypass is supported."
overclaim_case "reconciliation-bypass" "Reconciliation bypass is valid."
overclaim_case "case-shortcut" "Case-closure shortcut is accepted."
overclaim_case "source-shortcut" "Source-admission shortcut is allowed."

allowed_doc_line_case "redacted-secret" "api_key=redacted"
allowed_doc_line_case "redacted-spaced-api-key" "API key: redacted"
allowed_doc_line_case "redacted-html-split-api-key" "api_key<span></span>=redacted"
allowed_doc_line_case "quoted-removed-private-data" "customer_name=\"removed\""
allowed_doc_line_case "denied-private-data-claim" "The proof pack does not include raw customer payload."
allowed_doc_line_case "must-not-retain-private-data" "The proof pack must not retain raw customer payload."
allowed_doc_line_case "adverbially-denied-private-data" "The proof pack does not intentionally include raw customer payload."
allowed_doc_line_case "denied-private-data-list" "The proof pack does not include, retain, or publish raw customer payload."
allowed_doc_line_case "denied-ai-approval" "AI output can not approve the action."
allowed_doc_line_case "denied-mandatory-ai-approval" "AI output must not approve the action."
allowed_doc_line_case "denied-advisory-ai-approval" "AI output should not approve the action."
allowed_doc_line_case "denied-shall-ai-approval" "AI output shall not approve the action."
allowed_doc_line_case "denied-ai-has-to-approve" "AI output does not have to approve the action."
allowed_doc_line_case "denied-required-ai-approval" "AI output is not required to approve the action."
allowed_doc_line_case "denied-html-split-ai-approval" "AI <span></span>output must not approve the action."
allowed_doc_line_case "denied-ai-permission" "AI output is not permitted to approve the action."
allowed_doc_line_case "denied-ai-authorization" "AI output cannot be authorized to execute the action."
allowed_doc_line_case "denied-ai-authority" "AI output does not have authority to approve the action."
allowed_doc_line_case "denied-granted-ai-authority" "AI output is granted no authority to approve the action."
allowed_doc_line_case "denied-ai-article-case-closure" "AI output cannot close a case."
allowed_doc_line_case "denied-ai-individual-case-closure" "AI output cannot close an individual case."
allowed_doc_line_case "denied-elided-ai-execution" "AI output cannot approve the action; cannot execute the action."
allowed_doc_line_case "sentence-boundary-no-elision" "AI output cannot approve the action. Can operators execute the action?"
allowed_doc_line_case "denied-ai-truth" "AI output is not approval truth."
allowed_doc_line_case "denied-release-readiness" "Release artifacts do not prove RC readiness."

real_worktree="${workdir}/real-prerequisite-worktree"
git -C "${repo_root}" worktree add --detach --quiet "${real_worktree}" HEAD
git -C "${real_worktree}" config user.name "Phase 66.7 Self Test"
git -C "${real_worktree}" config user.email "phase-66-7-self-test@invalid.example"
write_negative_evidence_manifest "${real_worktree}"
write_limitation_manifest "${real_worktree}"
cp "${repo_root}/${doc_rel}" "${real_worktree}/${doc_rel}"
cp \
  "${repo_root}/scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh" \
  "${real_worktree}/scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
cp \
  "${repo_root}/scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh" \
  "${real_worktree}/scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
git -C "${real_worktree}" add \
  "${doc_rel}" \
  evidence/phase-66-7/negative-observations.json \
  evidence/phase-66-7/limitations.json \
  scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh \
  scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh
if ! git -C "${real_worktree}" diff --cached --quiet; then
  git -C "${real_worktree}" commit -qm "materialized prerequisite integration fixture"
fi
append_complete_packet "${real_worktree}"
assert_passes "${real_worktree}"
git -C "${repo_root}" worktree remove --force "${real_worktree}"
real_worktree=""

echo "Phase 66.7 RC authority-boundary proof-pack verifier self-test passes."
