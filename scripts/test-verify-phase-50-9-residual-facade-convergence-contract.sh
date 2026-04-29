#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-50-9-residual-facade-convergence-contract.sh"

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
  printf '%s\n' "${content}" >"${target}/docs/adr/0006-phase-50-9-residual-facade-convergence-and-projection-guard.md"
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
  write_contract "${target}" '# ADR-0006: Phase 50.9 Residual Facade Convergence and Projection Hotspot Guard

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #974, #975, #980
- **Depends On**: #967
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

Phase 50.8.6 closed #967 and recorded the current residual `service.py` ceiling in `docs/maintainability-hotspot-baseline.txt`.

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule.

ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

This ADR did not refresh the baseline before implementation evidence existed. Phase 50.9.6 closeout issue #980 later refreshed the baseline after the extraction sequence landed.

## 2. Decision

The residual Phase 50.9 target clusters are:

- external evidence helper cluster
- persistence and record-shaping helper cluster
- internal-only delegate cluster
- action-review projection split cluster
- closeout and hotspot-baseline guard cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, projection response semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, and projections remain subordinate context.

## 3. Residual Facade Targets

The Phase 50.8.6 starting ceiling was:

- `max_lines=3505`
- `max_effective_lines=3182`
- `max_facade_methods=185`

The Phase 50.9 implementation target for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines <= 3000`
- `max_effective_lines <= 2750`
- `max_facade_methods <= 160`

A Phase 50.9 closeout may record a lower exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.8.6 ceiling.

Any `service.py` baseline refresh before Phase 50.9 implementation evidence exists is forbidden.

Phase 50.9.6 closeout issue #980 records the accepted residual `service.py` ceiling as:

- `max_lines=3158`
- `max_effective_lines=2853`
- `max_facade_methods=173`
- `phase=50.9.6`
- `issue=#980`

## 4. Projection Hotspot Guard

The action-review projection split target is `control-plane/aegisops_control_plane/action_review_projection.py`.

The projection split must preserve directly linked authoritative action-review records as the anchor for approval, execution, reconciliation, mismatch inspection, path health, coordination outcome, and runtime visibility surfaces.

The projection split must not widen advisory context, recommendation lineage, evidence anchors, reconciliation subject linkage, or operator-facing detail surfaces beyond directly linked authoritative records.

No `action_review_projection.py` hotspot baseline may be recorded before implementation evidence exists.

An `action_review_projection.py` baseline may be recorded only at Phase 50.9 closeout when all of these criteria are true:

- the projection split has already moved directly linked helper ownership out of `service.py`;
- the closeout records measured `action_review_projection.py` line and effective-line counts after the split;
- the closeout names the unresolved projection responsibility cluster;
- the recorded projection ceiling is lower than the pre-Phase 50.9 projection measurement of `max_lines=2034` and `max_effective_lines=1911`;
- the baseline entry names a Phase 50.9 closeout phase and issue;
- the closeout explicitly states why another split would be riskier than accepting the temporary projection hotspot.

Phase 50.9.6 measured `control-plane/aegisops_control_plane/action_review_projection.py` at `projection lines=105` and `projection effective_lines=103`, which is below the verifier threshold and below the pre-Phase 50.9 projection measurement. No projection baseline entry is recorded.

## 5. Migration Order

The Phase 50.9 migration order is:

1. external evidence helper cluster
2. persistence and record-shaping helper cluster
3. internal-only delegate cluster
4. action-review projection split cluster
5. closeout and hotspot-baseline guard cluster

External evidence helpers must move before persistence and record-shaping helpers so evidence admission stays subordinate to AegisOps-owned records.

Persistence and record-shaping helpers must move before internal-only delegates so delegate boundaries do not infer alert, case, action, lifecycle, or evidence linkage from names, paths, comments, or neighboring records.

Internal-only delegates must move before the projection split so projection surfaces continue to read from explicit authoritative records instead of convenience summaries.

The projection split must move before closeout so any `action_review_projection.py` hotspot baseline decision is based on implementation evidence rather than a desired target.

## 6. Validation

Run `bash scripts/verify-phase-50-9-residual-facade-convergence-contract.sh`.

Run `bash scripts/test-verify-phase-50-9-residual-facade-convergence-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 975 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 980 --config <supervisor-config-path>`.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No projection module split is approved by this ADR.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, detection, external-evidence, or operator authority behavior is changed.
- No baseline refresh is approved before Phase 50.9 implementation evidence exists.
- No subordinate source, operator-facing projection, summary, badge, counter, recommendation, evidence snippet, or reconciliation note becomes authoritative workflow truth.
- No exception may raise the Phase 50.8.6 ceiling.

## 8. Approval

- **Proposed By**: Codex for Issue #975
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-29'
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
rm "${missing_contract_repo}/docs/adr/0006-phase-50-9-residual-facade-convergence-and-projection-guard.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 50.9 residual facade convergence contract"

missing_projection_guard_repo="${workdir}/missing-projection-guard"
create_valid_repo "${missing_projection_guard_repo}"
perl -0pi -e 's/No `action_review_projection\.py` hotspot baseline may be recorded before implementation evidence exists\.//g' \
  "${missing_projection_guard_repo}/docs/adr/0006-phase-50-9-residual-facade-convergence-and-projection-guard.md"
assert_fails_with \
  "${missing_projection_guard_repo}" \
  "Missing Phase 50.9 residual facade convergence contract statement: No \`action_review_projection.py\` hotspot baseline may be recorded before implementation evidence exists."

missing_target_repo="${workdir}/missing-target"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/- `max_effective_lines <= 2750`\n//g' \
  "${missing_target_repo}/docs/adr/0006-phase-50-9-residual-facade-convergence-and-projection-guard.md"
assert_fails_with \
  "${missing_target_repo}" \
  "Missing Phase 50.9 residual facade convergence contract statement: - \`max_effective_lines <= 2750\`"

premature_service_baseline_repo="${workdir}/premature-service-baseline"
create_valid_repo "${premature_service_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3000 max_effective_lines=2750 max_facade_methods=160 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0006 phase=50.9 issue=#975" \
  >"${premature_service_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${premature_service_baseline_repo}" \
  "Phase 50.9 closeout requires the accepted Phase 50.9.6 service.py ceiling after implementation evidence exists."

premature_projection_baseline_repo="${workdir}/premature-projection-baseline"
create_valid_repo "${premature_projection_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/action_review_projection.py max_lines=1900 max_effective_lines=1780 phase=50.9 issue=#975" \
  >>"${premature_projection_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${premature_projection_baseline_repo}" \
  "Phase 50.9 contract forbids an action_review_projection.py hotspot baseline before implementation evidence exists."

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative workflow truth\.//g' \
  "${missing_authority_repo}/docs/adr/0006-phase-50-9-residual-facade-convergence-and-projection-guard.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 50.9 residual facade convergence contract statement: AegisOps control-plane records remain authoritative workflow truth."

echo "verify-phase-50-9-residual-facade-convergence-contract tests passed"
