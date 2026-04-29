#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-50-8-residual-service-hotspot-contract.sh"

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
  printf '%s\n' "${content}" >"${target}/docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md"
}

write_baseline() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' \
    "control-plane/aegisops_control_plane/service.py max_lines=5660 max_effective_lines=5250 max_facade_methods=203 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.7 issue=#953" \
    >"${target}/docs/maintainability-hotspot-baseline.txt"
}

create_valid_repo() {
  local target="$1"

  write_baseline "${target}"
  write_contract "${target}" '# ADR-0005: Phase 50.8 Residual Service Hotspot Migration Contract

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #961, #962
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

ADR-0004 remains authoritative for the Phase 50 hotspot ordering decision.

ADR-0003 remains authoritative for the public facade-preservation exception.

Phase 50.7 recorded the current residual service ceiling in `docs/maintainability-hotspot-baseline.txt`.

This ADR does not refresh the baseline because implementation evidence does not exist yet.

## 2. Decision

The residual Phase 50.8 `service.py` helper clusters are:

- readiness helper cluster
- action-review helper cluster
- intake/lifecycle helper cluster
- action-policy helper cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context.

## 3. Residual Hotspot Map

Residual helper migration only.

## 4. Migration Order

The Phase 50.8 migration order is:

1. readiness helper cluster
2. action-review helper cluster
3. intake/lifecycle helper cluster
4. action-policy helper cluster

Readiness helpers must move before action-review helpers that consume readiness projections.

Action-review helpers must move before action-policy helpers so review-state projections stay anchored to authoritative action records.

Intake/lifecycle helpers must move before action-policy helpers so action policy does not infer case, alert, lifecycle, or evidence linkage from names, paths, comments, or neighboring records.

## 5. Measurement Guard

The current Phase 50.7 ceiling remains:

- `max_lines=5660`
- `max_effective_lines=5250`
- `max_facade_methods=203`

The Phase 50.8 implementation target is:

- `max_lines <= 5200`
- `max_effective_lines <= 4850`
- `max_facade_methods <= 175`

A Phase 50.8 closeout may record an exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.7 ceiling.

Any baseline refresh before implementation evidence exists is forbidden.

## 6. Validation

Run `bash scripts/verify-phase-50-8-residual-service-hotspot-contract.sh`.

Run `bash scripts/test-verify-phase-50-8-residual-service-hotspot-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 962 --config <supervisor-config-path>`.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, or operator authority behavior is changed.

## 8. Approval

- **Proposed By**: Codex for Issue #962
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

duplicate_baseline_repo="${workdir}/duplicate-baseline"
create_valid_repo "${duplicate_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3505 max_effective_lines=3182 max_facade_methods=185 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.8.6 issue=#967" \
  >>"${duplicate_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${duplicate_baseline_repo}" \
  "Phase 50.8 contract requires exactly one service.py hotspot baseline entry."

final_closeout_repo="${workdir}/final-closeout"
create_valid_repo "${final_closeout_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3505 max_effective_lines=3182 max_facade_methods=185 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.8.6 issue=#967" \
  >"${final_closeout_repo}/docs/maintainability-hotspot-baseline.txt"
cat >"${final_closeout_repo}/docs/phase-50-maintainability-closeout.md" <<'EOF'
# Phase 50 Maintainability Closeout

Phase 50.8.6 records the final #967 closeout baseline.

- `max_lines=3505`
- `max_effective_lines=3182`
- `max_facade_methods=185`

The remaining accepted hotspot is the action review projection and visibility helper cluster plus intake and authoritative-state guard helpers.

Any silent re-growth requires another decomposition decision.
EOF
assert_passes "${final_closeout_repo}"

superseding_closeout_repo="${workdir}/superseding-closeout"
create_valid_repo "${superseding_closeout_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3158 max_effective_lines=2853 max_facade_methods=173 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.9.6 issue=#980" \
  >"${superseding_closeout_repo}/docs/maintainability-hotspot-baseline.txt"
cat >"${superseding_closeout_repo}/docs/phase-50-maintainability-closeout.md" <<'EOF'
# Phase 50 Maintainability Closeout

Phase 50.9.6 records the final #980 closeout baseline.

- `max_lines=3158`
- `max_effective_lines=2853`
- `max_facade_methods=173`

The remaining accepted hotspot is the facade dispatch and authority-boundary guard helpers.

The projection split does not require a baseline entry.

Any silent re-growth requires another decomposition decision.
EOF
assert_passes "${superseding_closeout_repo}"

phase50_10_superseding_closeout_repo="${workdir}/phase50-10-superseding-closeout"
create_valid_repo "${phase50_10_superseding_closeout_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3003 max_effective_lines=2704 max_facade_methods=167 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.10.6 issue=#993" \
  >"${phase50_10_superseding_closeout_repo}/docs/maintainability-hotspot-baseline.txt"
cat >"${phase50_10_superseding_closeout_repo}/docs/phase-50-maintainability-closeout.md" <<'EOF'
# Phase 50 Maintainability Closeout

Phase 50.10.6 records the final #993 closeout baseline.

- `max_lines=3003`
- `max_effective_lines=2704`
- `max_facade_methods=167`

The remaining accepted hotspot is the facade dispatch, compatibility entrypoints, and authority-boundary guard helpers.

The external-evidence split does not require a baseline entry.

Any silent re-growth requires another decomposition decision.
EOF
assert_passes "${phase50_10_superseding_closeout_repo}"

superseding_regrowth_repo="${workdir}/superseding-regrowth"
create_valid_repo "${superseding_regrowth_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3159 max_effective_lines=2854 max_facade_methods=174 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.9.6 issue=#980" \
  >"${superseding_regrowth_repo}/docs/maintainability-hotspot-baseline.txt"
cat >"${superseding_regrowth_repo}/docs/phase-50-maintainability-closeout.md" <<'EOF'
# Phase 50 Maintainability Closeout

Phase 50.9.6 records a regrown #980 closeout baseline.

- `max_lines=3159`
- `max_effective_lines=2854`
- `max_facade_methods=174`

The remaining accepted hotspot is the facade dispatch and authority-boundary guard helpers.

The projection split does not require a baseline entry.

Any silent re-growth requires another decomposition decision.
EOF
assert_fails_with \
  "${superseding_regrowth_repo}" \
  "Phase 50.9 superseding closeout baseline must remain at or below the accepted #980 ceiling."

phase50_10_superseding_regrowth_repo="${workdir}/phase50-10-superseding-regrowth"
create_valid_repo "${phase50_10_superseding_regrowth_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=3004 max_effective_lines=2705 max_facade_methods=168 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.10.6 issue=#993" \
  >"${phase50_10_superseding_regrowth_repo}/docs/maintainability-hotspot-baseline.txt"
cat >"${phase50_10_superseding_regrowth_repo}/docs/phase-50-maintainability-closeout.md" <<'EOF'
# Phase 50 Maintainability Closeout

Phase 50.10.6 records a regrown #993 closeout baseline.

- `max_lines=3004`
- `max_effective_lines=2705`
- `max_facade_methods=168`

The remaining accepted hotspot is the facade dispatch, compatibility entrypoints, and authority-boundary guard helpers.

The external-evidence split does not require a baseline entry.

Any silent re-growth requires another decomposition decision.
EOF
assert_fails_with \
  "${phase50_10_superseding_regrowth_repo}" \
  "Phase 50.10 superseding closeout baseline must remain at or below the accepted #993 ceiling."

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 50.8 residual service hotspot contract"

missing_cluster_repo="${workdir}/missing-cluster"
create_valid_repo "${missing_cluster_repo}"
perl -0pi -e 's/- intake\/lifecycle helper cluster\n//g' \
  "${missing_cluster_repo}/docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md"
assert_fails_with \
  "${missing_cluster_repo}" \
  "Missing Phase 50.8 residual service hotspot contract statement: - intake/lifecycle helper cluster"

missing_target_repo="${workdir}/missing-target"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/- `max_effective_lines <= 4850`\n//g' \
  "${missing_target_repo}/docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md"
assert_fails_with \
  "${missing_target_repo}" \
  "Missing Phase 50.8 residual service hotspot contract statement: - \`max_effective_lines <= 4850\`"

premature_baseline_repo="${workdir}/premature-baseline"
create_valid_repo "${premature_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=5200 max_effective_lines=4850 max_facade_methods=175 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0005 phase=50.8 issue=#962" \
  >"${premature_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${premature_baseline_repo}" \
  "After implementation evidence exists, it requires either the final Phase 50.8.6 closeout baseline for #967 or the lower superseding Phase 50.9.6 closeout baseline for #980."

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative workflow truth\.//g' \
  "${missing_authority_repo}/docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 50.8 residual service hotspot contract statement: AegisOps control-plane records remain authoritative workflow truth."

echo "verify-phase-50-8-residual-service-hotspot-contract tests passed"
