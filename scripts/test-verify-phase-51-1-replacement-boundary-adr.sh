#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-51-1-replacement-boundary-adr.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_phase511_adr() {
  local target="$1"
  local content="$2"

  mkdir -p "${target}/docs/adr"
  printf '%s\n' "${content}" >"${target}/docs/adr/0011-phase-51-1-replacement-boundary.md"
}

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}"
  printf '%s\n' "# AegisOps" "See docs/adr/0011-phase-51-1-replacement-boundary.md." >"${target}/README.md"

  write_phase511_adr "${target}" '# ADR-0011: Phase 51.1 SMB SecOps Replacement Boundary

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #1041, #1042
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

Phase 51 needs replacement wording that preserves the AegisOps control-plane authority boundary.

## 2. Decision

AegisOps replaces the SMB SecOps operating experience, not Wazuh internals, Shuffle internals, or every SIEM and SOAR capability.

Replacement means the reviewed operator experience for daily SMB SOC work: Wazuh detects, AegisOps decides, records, and reconciles, and Shuffle executes reviewed delegated routine work.

## 3. Allowed Replacement Claims

- Allowed claim: AegisOps can replace the daily SMB SOC operating experience above Wazuh and Shuffle.
- Allowed claim: AegisOps can replace ad hoc ticket-and-script coordination with authoritative alert, case, approval, action request, receipt, reconciliation, audit, and release records.
- Allowed claim: AegisOps can provide a governed SIEM/SOAR operating layer for SMB teams when Wazuh and Shuffle provide the reviewed substrate capabilities.

## 4. Disallowed Replacement Claims

- Disallowed claim: AegisOps already replaces every SIEM capability.
- Disallowed claim: AegisOps already replaces every SOAR capability.
- Disallowed claim: AegisOps reimplements Wazuh detection internals.
- Disallowed claim: AegisOps reimplements Shuffle workflow internals.

## 5. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, and release truth.

AI must not approve actions, execute actions, reconcile execution, close cases, activate detectors, or become source truth.

Wazuh alert status is not AegisOps case truth.

Shuffle workflow success is not AegisOps reconciliation truth.

Tickets, evidence systems, browser state, UI cache, downstream receipts, demo data, Wazuh, Shuffle, and AI output remain subordinate context.

This ADR rejects any shortcut that promotes subordinate surfaces into AegisOps workflow truth.

## 6. Substrate Responsibilities

Wazuh is the detection substrate.

Shuffle is the routine automation substrate.

## 7. Implementation Impact

This ADR does not implement CLI behavior, Wazuh profile generation, Shuffle profile generation, AI daily operations, SIEM breadth, SOAR breadth, packaging, release-candidate behavior, or general-availability behavior.

## 8. Security Impact

Authority remains in AegisOps records.

## 9. Rollback / Exit Strategy

Supersede this ADR if replacement wording changes.

## 10. Validation

Run `bash scripts/verify-phase-51-1-replacement-boundary-adr.sh`.
Run `bash scripts/test-verify-phase-51-1-replacement-boundary-adr.sh`.
Run `node <codex-supervisor-root>/dist/index.js issue-lint 1042 --config <supervisor-config-path>`.

## 11. Non-Goals

No runtime behavior changes are approved by this ADR.

## 12. Approval

- **Proposed By**: Codex for Issue #1042
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-30'
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

missing_adr_repo="${workdir}/missing-adr"
create_valid_repo "${missing_adr_repo}"
rm "${missing_adr_repo}/docs/adr/0011-phase-51-1-replacement-boundary.md"
assert_fails_with \
  "${missing_adr_repo}" \
  "Missing Phase 51.1 replacement boundary ADR"

missing_allowed_claim_repo="${workdir}/missing-allowed-claim"
create_valid_repo "${missing_allowed_claim_repo}"
perl -0pi -e 's#- Allowed claim: AegisOps can provide a governed SIEM/SOAR operating layer for SMB teams when Wazuh and Shuffle provide the reviewed substrate capabilities\.\n##' \
  "${missing_allowed_claim_repo}/docs/adr/0011-phase-51-1-replacement-boundary.md"
assert_fails_with \
  "${missing_allowed_claim_repo}" \
  "Missing Phase 51.1 replacement boundary ADR statement: Allowed claim: AegisOps can provide a governed SIEM/SOAR operating layer for SMB teams when Wazuh and Shuffle provide the reviewed substrate capabilities."

missing_disallowed_claim_repo="${workdir}/missing-disallowed-claim"
create_valid_repo "${missing_disallowed_claim_repo}"
perl -0pi -e 's#- Disallowed claim: AegisOps already replaces every SOAR capability\.\n##' \
  "${missing_disallowed_claim_repo}/docs/adr/0011-phase-51-1-replacement-boundary.md"
assert_fails_with \
  "${missing_disallowed_claim_repo}" \
  "Missing Phase 51.1 replacement boundary ADR statement: Disallowed claim: AegisOps already replaces every SOAR capability."

forbidden_claim_repo="${workdir}/forbidden-claim"
create_valid_repo "${forbidden_claim_repo}"
printf '%s\n' "Allowed claim: AegisOps already replaces every SIEM capability" >>"${forbidden_claim_repo}/docs/adr/0011-phase-51-1-replacement-boundary.md"
assert_fails_with \
  "${forbidden_claim_repo}" \
  "Forbidden Phase 51.1 replacement boundary ADR claim: Allowed claim: AegisOps already replaces every SIEM capability"

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
perl -0pi -e 's#Wazuh alert status is not AegisOps case truth\.\n##' \
  "${missing_authority_repo}/docs/adr/0011-phase-51-1-replacement-boundary.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 51.1 replacement boundary ADR statement: Wazuh alert status is not AegisOps case truth."

missing_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_link_repo}/README.md"
assert_fails_with \
  "${missing_link_repo}" \
  "README must link the Phase 51.1 replacement boundary ADR."

echo "verify-phase-51-1-replacement-boundary-adr tests passed"
