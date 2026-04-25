#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-detector-activation-evidence-handoff.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p \
    "${target}/docs/source-families/github-audit/detector-activation-candidates" \
    "${target}/docs/source-families/entra-id/detector-activation-candidates"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_valid_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/detector-activation-evidence-handoff.md"
# Detector Activation Evidence Handoff Manifest

The detector activation evidence handoff is a compact review package for Phase 40 detector activation, disable, and rollback decisions.

The manifest is evidence custody only; AegisOps-owned alert, case, evidence, reconciliation, and release-gate records remain authoritative.

It must not become a compliance archive platform, unlimited detector history system, external ticket authority, or optional-extension prerequisite.

## 2. Manifest Fields

| Field | Required evidence | Authority boundary |
| --- | --- | --- |
| Rule review evidence | Candidate rule identifier, lifecycle state, source-family package, reviewer, rule intent, source scope, expected alert volume, expected benign cases, false-positive review, next-review date, and activation owner. | Rule review evidence gates activation but does not make the detector source authoritative for case or workflow truth. |
| Fixture and parser evidence | Reviewed fixture paths, parser or decoder identity, validation command result, source field coverage, timestamp quality, provenance evidence, and the exact fixture set used for review. | Fixture evidence proves the admitted alert shape only; parser drift or fixture drift blocks activation until refreshed review is recorded. |
| Activation evidence | Activation window, reviewer sign-off, activation owner, disable owner, rollback owner, release-gate evidence record, repository revision, and the AegisOps alert, case, evidence, or reconciliation identifiers that received detector evidence. | Activation is accepted only through AegisOps-owned records and release-gate evidence, not through Wazuh, OpenSearch, GitHub, Entra ID, or ticket status alone. |
| Rollback and disable evidence | Disable reason, rollback reason, restored rule revision, restored fixture set, validation rerun result, operator notification path, follow-up owner, and release-gate evidence record. | Rollback is a non-destructive content, rule-set, fixture, and validation reset path; it does not authorize direct source-side mutation or undocumented hotfixes. |
| Alert or case admission sanity | AegisOps alert, case, evidence, or reconciliation identifiers, admission result, reviewed linkage to the source-family record, and clean-state outcome for failed or rejected paths. | Case admission remains control-plane-owned and must fail closed when provenance, scope, linkage, or snapshot consistency is missing. |
| Known limitations | Deferred detector behavior, unsupported source fields, parser gaps, expected false-positive limits, retention limit, optional-extension non-requirements, and follow-up owner. | Limitations preserve review context without creating an unlimited history system or expanding detector authority. |

## 3. Required Review Questions

- Does the handoff name the exact candidate rule, source-family package, fixture set, validation command result, reviewer, activation owner, disable owner, rollback owner, and next-review date?
- Does the handoff cite AegisOps-owned alert, case, evidence, reconciliation, or release-gate records for activation and rollback evidence?
- Did alert or case admission preserve explicit reviewed linkage, fail closed on missing provenance or scope, and leave no orphan record, partial durable write, or half-admitted case after rejected paths?

## 4. Source-Family Alignment

GitHub audit and Entra ID runbooks must point detector activation review to this manifest before a candidate moves beyond staging review.

## 5. Validation

Run `scripts/verify-detector-activation-evidence-handoff.sh` after changing this manifest, the GitHub audit runbook, the Entra ID runbook, or detector activation candidate evidence.

## 6. Out of Scope

Unlimited detector history retention, compliance archive platform design, external ticket authority, direct GitHub API actioning, direct Entra ID actioning, optional-extension startup gates, and source-owned workflow truth are out of scope.
EOF

  cat <<'EOF' > "${target}/docs/wazuh-rule-lifecycle-runbook.md"
# Wazuh Rule Lifecycle and Validation Runbook

`docs/detector-activation-evidence-handoff.md` is the reviewed detector activation evidence handoff manifest for Phase 40 activation, disable, rollback, alert or case admission sanity, and known limitations.
EOF

  for family in github-audit entra-id; do
    mkdir -p "${target}/docs/source-families/${family}"
    cat <<'EOF' > "${target}/docs/source-families/${family}/analyst-triage-runbook.md"
# Analyst Triage Runbook

Detector activation evidence handoff must use `docs/detector-activation-evidence-handoff.md` as the manifest for rule review evidence, fixture and parser evidence, activation evidence, rollback evidence, alert or case admission sanity, and known limitations.

The handoff must cite AegisOps-owned alert, case, evidence, reconciliation, or release-gate records; source-family output, Wazuh status, OpenSearch status, GitHub status, Entra ID status, and external ticket fields are evidence only.

Missing provenance, missing parser evidence, missing reviewer ownership, inferred scope linkage, placeholder credentials, or mixed-snapshot admission evidence blocks activation handoff until the prerequisite is supplied.
EOF
  done

  cat <<'EOF' > "${target}/docs/source-families/github-audit/detector-activation-candidates/repository-admin-membership-change.md"
# GitHub Audit Repository Admin Membership Change Candidate

Activation handoff must follow `docs/detector-activation-evidence-handoff.md` before this candidate moves beyond staging review.
EOF

  cat <<'EOF' > "${target}/docs/source-families/entra-id/detector-activation-candidates/privileged-role-assignment.md"
# Entra ID Privileged Role Assignment Candidate

Activation handoff must follow `docs/detector-activation-evidence-handoff.md` before this candidate moves beyond staging review.
EOF
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add .
  git -C "${target}" commit --allow-empty -q -m "fixture"
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
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_manifest_repo="${workdir}/missing-manifest"
create_repo "${missing_manifest_repo}"
write_valid_docs "${missing_manifest_repo}"
rm "${missing_manifest_repo}/docs/detector-activation-evidence-handoff.md"
commit_fixture "${missing_manifest_repo}"
assert_fails_with "${missing_manifest_repo}" "Missing detector activation evidence handoff manifest:"

missing_alignment_repo="${workdir}/missing-alignment"
create_repo "${missing_alignment_repo}"
write_valid_docs "${missing_alignment_repo}"
printf '# GitHub Audit Analyst Triage Runbook\n' > "${missing_alignment_repo}/docs/source-families/github-audit/analyst-triage-runbook.md"
commit_fixture "${missing_alignment_repo}"
assert_fails_with "${missing_alignment_repo}" "Missing GitHub audit detector handoff alignment:"

missing_case_sanity_repo="${workdir}/missing-case-sanity"
create_repo "${missing_case_sanity_repo}"
write_valid_docs "${missing_case_sanity_repo}"
perl -0pi -e 's/\| Alert or case admission sanity \| AegisOps alert, case, evidence, or reconciliation identifiers, admission result, reviewed linkage to the source-family record, and clean-state outcome for failed or rejected paths\. \| Case admission remains control-plane-owned and must fail closed when provenance, scope, linkage, or snapshot consistency is missing\. \|\n//' "${missing_case_sanity_repo}/docs/detector-activation-evidence-handoff.md"
commit_fixture "${missing_case_sanity_repo}"
assert_fails_with "${missing_case_sanity_repo}" "Missing detector activation evidence handoff manifest statement: | Alert or case admission sanity |"

forbidden_authority_repo="${workdir}/forbidden-authority"
create_repo "${forbidden_authority_repo}"
write_valid_docs "${forbidden_authority_repo}"
printf '\nDirect GitHub API actioning is approved for activation handoff.\n' >> "${forbidden_authority_repo}/docs/detector-activation-evidence-handoff.md"
commit_fixture "${forbidden_authority_repo}"
assert_fails_with "${forbidden_authority_repo}" "Forbidden GitHub authority statement: direct GitHub API actioning is approved"

echo "verify-detector-activation-evidence-handoff tests passed"
