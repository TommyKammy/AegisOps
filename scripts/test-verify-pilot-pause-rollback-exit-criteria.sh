#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-pilot-pause-rollback-exit-criteria.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment"
}

write_valid_docs() {
  local target="$1"

  cp "${repo_root}/docs/deployment/pilot-pause-rollback-exit-criteria.md" "${target}/docs/deployment/pilot-pause-rollback-exit-criteria.md"

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

Before continuing, pausing, rolling back, or exiting a single-customer pilot, review `docs/deployment/pilot-pause-rollback-exit-criteria.md` and verify it with `scripts/verify-pilot-pause-rollback-exit-criteria.sh` so pause criteria, rollback criteria, exit criteria, unresolved limitations, next-roadmap input, and operator/support signoff remain bounded to Phase 43.
EOF

  cat <<'EOF' > "${target}/docs/deployment/pilot-readiness-checklist.md"
# Single-Customer Pilot Readiness Checklist and Entry Criteria

Pilot pause, rollback, and exit decisions must use `docs/deployment/pilot-pause-rollback-exit-criteria.md`; entry readiness alone is not exit-success, rollback acceptance, or permission to continue after a paused or degraded pilot.
EOF

  cat <<'EOF' > "${target}/docs/deployment/support-playbook-break-glass-rehearsal.md"
# Support Playbook and Break-Glass Rehearsal

Pilot pause, rollback, and exit decisions must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` so support degradation, break-glass evidence, rollback escalation, unresolved limitations, and next-roadmap input remain reviewed and bounded.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operator-training-handoff-packet.md"
# Operator Training and Handoff Packet

For pilot pause, rollback, continue, or exit signoff, operators must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` after completing the queue, case, action-review, reviewed-record, non-authority, and evidence handoff walkthrough.
EOF

  cat <<'EOF' > "${target}/docs/deployment/release-handoff-evidence-package.md"
# Phase 38 Release Handoff Evidence Package

Pilot exit-success, exit-no-go, pause, continue, and rollback decisions must point to `docs/deployment/pilot-pause-rollback-exit-criteria.md` instead of treating release handoff alone as pilot success.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

Pilot pause, rollback, continue, and exit evidence must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` as the reviewed operator/support decision surface for unresolved limitations and next-roadmap input capture.
EOF

  cat <<'EOF' > "${target}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
# Phase 37 Restore Rollback Upgrade Evidence Rehearsal

Pilot rollback acceptance must stay aligned to `docs/deployment/pilot-pause-rollback-exit-criteria.md`; a same-day rollback decision is not accepted for pilot continuation or exit until operator/support signoff, refusal reason when applicable, and clean-state evidence are retained.
EOF

  mkdir -p "${target}/scripts"
  touch "${target}/scripts/test-verify-pilot-pause-rollback-exit-criteria.sh"
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

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_valid_docs "${valid_repo}"
assert_passes "${valid_repo}"

missing_criteria_repo="${workdir}/missing-criteria"
create_repo "${missing_criteria_repo}"
write_valid_docs "${missing_criteria_repo}"
rm "${missing_criteria_repo}/docs/deployment/pilot-pause-rollback-exit-criteria.md"
assert_fails_with "${missing_criteria_repo}" "Missing pilot pause rollback exit criteria document:"

missing_pause_repo="${workdir}/missing-pause"
create_repo "${missing_pause_repo}"
write_valid_docs "${missing_pause_repo}"
perl -0pi -e 's/^Pause the pilot and keep normal operator use blocked when any of the following are true:\n//m' "${missing_pause_repo}/docs/deployment/pilot-pause-rollback-exit-criteria.md"
assert_fails_with "${missing_pause_repo}" "Missing pilot pause rollback exit criteria statement: Pause the pilot and keep normal operator use blocked"

missing_rollback_alignment_repo="${workdir}/missing-rollback-alignment"
create_repo "${missing_rollback_alignment_repo}"
write_valid_docs "${missing_rollback_alignment_repo}"
printf '# Phase 37 Restore Rollback Upgrade Evidence Rehearsal\n' > "${missing_rollback_alignment_repo}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
assert_fails_with "${missing_rollback_alignment_repo}" 'Missing restore rollback rehearsal pause rollback exit criteria link: Pilot rollback acceptance must stay aligned to `docs/deployment/pilot-pause-rollback-exit-criteria.md`'

missing_signoff_repo="${workdir}/missing-signoff"
create_repo "${missing_signoff_repo}"
write_valid_docs "${missing_signoff_repo}"
perl -0pi -e 's/^Before continuing after a pause, accepting rollback completion, or recording exit-success, operator and support signoff must confirm:\n//m' "${missing_signoff_repo}/docs/deployment/pilot-pause-rollback-exit-criteria.md"
assert_fails_with "${missing_signoff_repo}" "Missing pilot pause rollback exit criteria statement: Before continuing after a pause, accepting rollback completion, or recording exit-success"

forbidden_scope_repo="${workdir}/forbidden-scope"
create_repo "${forbidden_scope_repo}"
write_valid_docs "${forbidden_scope_repo}"
printf '\nThe public launch checklist is approved by pilot exit.\n' >> "${forbidden_scope_repo}/docs/deployment/pilot-pause-rollback-exit-criteria.md"
assert_fails_with "${forbidden_scope_repo}" "Forbidden pilot pause rollback exit criteria statement: public launch checklist is approved"

forbidden_runbook_scope_repo="${workdir}/forbidden-runbook-scope"
create_repo "${forbidden_runbook_scope_repo}"
write_valid_docs "${forbidden_runbook_scope_repo}"
printf '\nThe multi-tenant expansion is approved by pilot exit.\n' >> "${forbidden_runbook_scope_repo}/docs/runbook.md"
assert_fails_with "${forbidden_runbook_scope_repo}" "Forbidden pilot pause rollback exit criteria statement: multi-tenant expansion is approved"

absolute_path_repo="${workdir}/absolute-path"
create_repo "${absolute_path_repo}"
write_valid_docs "${absolute_path_repo}"
printf '\nLocal evidence: /%s/%s/pilot-exit.md\n' "Users" "example" >> "${absolute_path_repo}/docs/deployment/pilot-pause-rollback-exit-criteria.md"
assert_fails_with "${absolute_path_repo}" "Forbidden pilot pause rollback exit guidance: workstation-local absolute path detected"

echo "Pilot pause rollback exit criteria verifier tests passed."
