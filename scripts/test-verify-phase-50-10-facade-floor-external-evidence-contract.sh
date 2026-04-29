#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-50-10-facade-floor-external-evidence-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_contract() {
  local target="$1"
  local content="$2"

  mkdir -p "${target}/docs/adr"
  printf '%s\n' "${content}" >"${target}/docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md"
}

write_baseline() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' \
    "control-plane/aegisops_control_plane/service.py max_lines=3158 max_effective_lines=2853 max_facade_methods=173 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.9.6 issue=#980" \
    >"${target}/docs/maintainability-hotspot-baseline.txt"
}

create_valid_repo() {
  local target="$1"

  write_baseline "${target}"
  write_contract "${target}" '# ADR-0007: Phase 50.10 Facade Floor and External Evidence Guard Contract

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #987, #988
- **Depends On**: #980
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule.

ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence.

ADR-0006 remains authoritative for the Phase 50.9 residual facade convergence and projection hotspot guard.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

This ADR does not refresh the baseline because Phase 50.10 implementation evidence does not exist yet.

## 2. Decision

The Phase 50.10 target clusters are:

- MISP and osquery helper cluster
- endpoint evidence helper cluster
- service facade helper cluster
- internal caller rewiring cluster
- closeout and hotspot-baseline guard cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, external-evidence response semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, and external-evidence adapter output remain subordinate context.

## 3. Facade Floor Targets

The Phase 50.9.6 starting ceiling for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines=3158`
- `max_effective_lines=2853`
- `max_facade_methods=173`
- `phase=50.9.6`
- `issue=#980`

The Phase 50.10 implementation target for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines <= 2900`
- `max_effective_lines <= 2650`
- `max_facade_methods <= 160`

A Phase 50.10 closeout may record a lower exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.9.6 ceiling.

Any `service.py` baseline refresh before Phase 50.10 implementation evidence exists is forbidden.

## 4. External Evidence Guard

The external-evidence split target is `control-plane/aegisops_control_plane/external_evidence_boundary.py`.

No `external_evidence_boundary.py` hotspot baseline may be recorded before Phase 50.10 implementation evidence exists.

An `external_evidence_boundary.py` baseline may be recorded only at Phase 50.10 closeout when all of these criteria are true:

- the MISP, osquery, and endpoint evidence helpers have already been split into explicitly owned helper modules or fenced helper clusters;
- the closeout records measured `external_evidence_boundary.py` line and effective-line counts after the split;
- the closeout names the unresolved external-evidence responsibility cluster;
- the recorded external-evidence ceiling is lower than the pre-Phase 50.10 measurement of `max_lines=1083` and `max_effective_lines=1033`;
- the baseline entry names a Phase 50.10 closeout phase and issue;
- the closeout explicitly states why another split would be riskier than accepting the temporary external-evidence hotspot.

If those criteria are not all true, the correct result is a follow-up decomposition issue, not a silent external-evidence hotspot exception.

External evidence may enrich a reviewed record only when the AegisOps record chain explicitly binds the evidence subject, source, provenance, and linked case or alert context.

External evidence must not infer tenant, case, alert, host, repository, account, issue, or environment linkage from names, paths, comments, nearby records, adapter output, or neighboring metadata alone.

## 5. Migration Order

The Phase 50.10 migration order is:

1. MISP and osquery helper cluster
2. endpoint evidence helper cluster
3. service facade helper cluster
4. internal caller rewiring cluster
5. closeout and hotspot-baseline guard cluster

MISP and osquery helpers must move before endpoint evidence helpers so subordinate enrichment and reviewed host-context attachment stay explicitly bound to AegisOps-owned records.

Endpoint evidence helpers must move before service facade helpers so endpoint collection and artifact admission do not widen public service authority.

Service facade helpers must move before internal caller rewiring so callers keep using public facade entrypoints until the reviewed internal boundary exists.

Internal caller rewiring must move before closeout so any `external_evidence_boundary.py` hotspot baseline decision is based on implementation evidence rather than a desired target.

## 6. Validation

Run `bash scripts/verify-phase-50-10-facade-floor-external-evidence-contract.sh`.

Run `bash scripts/test-verify-phase-50-10-facade-floor-external-evidence-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 988 --config <supervisor-config-path>`.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No external-evidence module split is approved by this ADR.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, detection, external-evidence, or operator authority behavior is changed.
- No deployment, database, migration, credential source, external substrate, HTTP surface, CLI surface, or operator UI behavior is changed.
- No baseline refresh is approved before Phase 50.10 implementation evidence exists.
- No subordinate source, operator-facing projection, summary, badge, counter, recommendation, evidence snippet, reconciliation note, or external-evidence adapter output becomes authoritative workflow truth.
- No exception may raise the Phase 50.9.6 ceiling.

## 8. Approval

- **Proposed By**: Codex for Issue #988
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

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 50.10 facade floor and external evidence guard contract"

missing_external_guard_repo="${workdir}/missing-external-guard"
create_valid_repo "${missing_external_guard_repo}"
perl -0pi -e 's/No `external_evidence_boundary\.py` hotspot baseline may be recorded before Phase 50\.10 implementation evidence exists\.//g' \
  "${missing_external_guard_repo}/docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md"
assert_fails_with \
  "${missing_external_guard_repo}" \
  "Missing Phase 50.10 facade floor and external evidence guard contract statement: No \`external_evidence_boundary.py\` hotspot baseline may be recorded before Phase 50.10 implementation evidence exists."

missing_target_repo="${workdir}/missing-target"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/- `max_effective_lines <= 2650`\n//g' \
  "${missing_target_repo}/docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md"
assert_fails_with \
  "${missing_target_repo}" \
  "Missing Phase 50.10 facade floor and external evidence guard contract statement: - \`max_effective_lines <= 2650\`"

premature_service_baseline_repo="${workdir}/premature-service-baseline"
create_valid_repo "${premature_service_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=2900 max_effective_lines=2650 max_facade_methods=160 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0007 phase=50.10 issue=#988" \
  >"${premature_service_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${premature_service_baseline_repo}" \
  "Phase 50.10 contract forbids refreshing the service.py baseline before implementation evidence exists."

premature_external_baseline_repo="${workdir}/premature-external-baseline"
create_valid_repo "${premature_external_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/external_evidence_boundary.py max_lines=1000 max_effective_lines=950 phase=50.10 issue=#988" \
  >>"${premature_external_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${premature_external_baseline_repo}" \
  "Phase 50.10 contract forbids an external_evidence_boundary.py hotspot baseline before implementation evidence exists."

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative workflow truth\.//g' \
  "${missing_authority_repo}/docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 50.10 facade floor and external evidence guard contract statement: AegisOps control-plane records remain authoritative workflow truth."

echo "verify-phase-50-10-facade-floor-external-evidence-contract tests passed"
