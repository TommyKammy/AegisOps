#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-50-12-service-facade-pressure-contract.sh"

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
  printf '%s\n' "${content}" >"${target}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
}

write_baseline() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' \
    "control-plane/aegisops_control_plane/service.py max_lines=1812 max_effective_lines=1632 max_facade_methods=125 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.11.7 issue=#1007" \
    >"${target}/docs/maintainability-hotspot-baseline.txt"
}

create_valid_repo() {
  local target="$1"

  write_baseline "${target}"
  write_contract "${target}" '# ADR-0009: Phase 50.12 Service Facade Pressure Contract

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #1015, #1016
- **Depends On**: #1007
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

Phase 50.11.7 closed #1007 and recorded the accepted residual `service.py` ceiling in `docs/maintainability-hotspot-baseline.txt`.

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule.

ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence.

ADR-0006 remains authoritative for the Phase 50.9 residual facade convergence and projection hotspot guard.

ADR-0007 remains authoritative for the Phase 50.10 facade floor and external-evidence guard.

ADR-0008 remains authoritative for the Phase 50.11 residual DTO/helper extraction order and closeout validation.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

Phase 50.12 needs a repo-owned contract before final facade-pressure implementation slices start so the sub-1500 target, unchanged behavior boundaries, and verification commands are fixed before code moves.

This ADR does not refresh the baseline because Phase 50.12 implementation evidence does not exist yet and follow-on implementation slices remain.

## 2. Decision

Phase 50.12 will reduce the residual `service.py` facade pressure by extracting or fencing directly linked service facade helper clusters in a fixed, behavior-preserving order.

The Phase 50.12 residual extraction clusters are:

- constructor/composition wiring cluster
- action request/approval cluster
- casework write delegate cluster
- assistant residual helper cluster
- detection/action residual helper cluster

Public service entrypoints, runtime behavior, configuration shape, authority semantics, response semantics, and durable-state side effects remain unchanged.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context.

## 3. Starting Measurements

The Phase 50.11.7 starting ceiling for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines=1812`
- `max_effective_lines=1632`
- `max_facade_methods=125`
- `facade_class=AegisOpsControlPlaneService`
- `phase=50.11.7`
- `issue=#1007`

- `physical_lines=1812`
- `effective_lines=1632`
- `AegisOpsControlPlaneService methods=125`

The Phase 50.12 implementation target for `control-plane/aegisops_control_plane/service.py` is:

- `max_lines <= 1500`
- `max_effective_lines <= 1350`
- `max_facade_methods <= 95`

The sub-1500 target is a pressure-reduction target, not permission to change behavior.

A Phase 50.12 closeout may record a lower exception only if it names the unresolved residual cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.11.7 ceiling.

If the sub-1500 target cannot be reached safely, the fallback is to preserve behavior, keep the public `AegisOpsControlPlaneService` facade, record the blocker cluster explicitly, and require the next contract to lower or fence that exact residual cluster instead of claiming long-term completion.

Any `service.py` baseline refresh before Phase 50.12 implementation evidence exists is forbidden.

## 4. Extraction Scope

The constructor/composition wiring cluster owns internal collaborator construction, dependency binding, and facade composition routing that can move behind explicit internal builders without changing public initialization semantics.

The action request/approval cluster owns internal helper code for action request creation, approval decisions, delegation binding, reconciliation routing, mismatch handling, and receipt linkage while preserving authoritative action-review records as the source of truth.

The casework write delegate cluster owns bounded case mutation delegates for observations, leads, recommendations, handoff, disposition, and linked case lifecycle writes while preserving authoritative case records as workflow truth.

The assistant residual helper cluster owns remaining assistant context, advisory, recommendation, citation, draft, and live-assistant helper code that is directly linked to the anchored service request.

The detection/action residual helper cluster owns remaining detection intake, case linkage, external-evidence admission, action-review inspection, and action lifecycle helper code that still sits in the service facade.

No extracted helper may infer tenant, repository, account, issue, case, alert, host, environment, approval, execution, reconciliation, assistant, detection, action, or evidence linkage from naming conventions, path shape, comments, nearby metadata, sibling records, or operator-facing summaries alone.

## 5. Migration Order

The Phase 50.12 migration order is:

1. constructor/composition wiring cluster
2. action request/approval cluster
3. casework write delegate cluster
4. assistant residual helper cluster
5. detection/action residual helper cluster
6. closeout and hotspot-baseline guard cluster

Constructor/composition wiring must move first so later slices depend on explicit collaborator ownership instead of adding more facade-local construction pressure.

Action request/approval helpers must move before casework write delegates so write-path mutations keep using authoritative approval, delegation, reconciliation, and receipt records.

Casework write delegates must move before assistant residual helpers so advisory surfaces continue to attach to directly linked authoritative case records.

Assistant residual helpers must move before detection/action residual helpers so recommendation and citation context cannot broaden evidence, case, or action linkage by sibling or same-parent inference.

Detection/action residual helpers must move before closeout so any residual `service.py` baseline decision is based on implementation evidence rather than a desired target.

## 6. Validation

Run `bash scripts/verify-phase-50-12-service-facade-pressure-contract.sh`.

Run `bash scripts/test-verify-phase-50-12-service-facade-pressure-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `bash scripts/test-verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1016 --config <supervisor-config-path>`.

For the Phase 50.12 Epic, run the same issue-lint command for each Phase 50.12 child issue before allowing implementation slices to proceed.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No constructor, composition, action request, approval, casework write, assistant, detection, action, or external-evidence module split is approved by this ADR.
- No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed.
- No baseline refresh is approved before Phase 50.12 implementation evidence exists.
- No subordinate source, operator-facing projection, summary, badge, counter, snapshot, DTO, recommendation, evidence snippet, reconciliation note, or helper-module output becomes authoritative workflow truth.
- No exception may raise the Phase 50.11.7 ceiling.
- No long-term 50-method completion claim is approved unless later child issues prove it safely.

## 8. Approval

- **Proposed By**: Codex for Issue #1016
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

phase50_12_4_closeout_repo="${workdir}/phase50-12-4-closeout"
create_valid_repo "${phase50_12_4_closeout_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=1619 max_effective_lines=1445 max_facade_methods=117 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.12.4 issue=#1019" \
  >"${phase50_12_4_closeout_repo}/docs/maintainability-hotspot-baseline.txt"
cat >"${phase50_12_4_closeout_repo}/docs/phase-50-maintainability-closeout.md" <<'EOF'
# Phase 50 Maintainability Closeout

Phase 50.12.4 for #1019 fenced casework write compatibility delegates behind the case workflow facade.

- `max_lines=1619`
- `max_effective_lines=1445`
- `max_facade_methods=117`
- `phase=50.12.4`
- `issue=#1019`

Phase 50.12.4 then moved the casework write compatibility delegates out of `AegisOpsControlPlaneService` and into `control-plane/aegisops_control_plane/case_workflow.py`, preserving the public facade entrypoints for observation, lead, recommendation, handoff, and disposition writes.
EOF
assert_passes "${phase50_12_4_closeout_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 50.12 service facade pressure contract"

heading_suffix_repo="${workdir}/heading-suffix"
create_valid_repo "${heading_suffix_repo}"
perl -0pi -e 's/# ADR-0009: Phase 50\.12 Service Facade Pressure Contract/# ADR-0009: Phase 50.12 Service Facade Pressure Contract - superseded/g' \
  "${heading_suffix_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${heading_suffix_repo}" \
  "Missing Phase 50.12 service facade pressure contract heading: # ADR-0009: Phase 50.12 Service Facade Pressure Contract"

missing_measurement_repo="${workdir}/missing-measurement"
create_valid_repo "${missing_measurement_repo}"
perl -0pi -e 's/- `effective_lines=1632`\n//g' \
  "${missing_measurement_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${missing_measurement_repo}" \
  "Missing Phase 50.12 service facade pressure contract statement: - \`effective_lines=1632\`"

missing_target_repo="${workdir}/missing-target"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/- `max_lines <= 1500`\n//g' \
  "${missing_target_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${missing_target_repo}" \
  "Missing Phase 50.12 service facade pressure contract statement: - \`max_lines <= 1500\`"

statement_suffix_repo="${workdir}/statement-suffix"
create_valid_repo "${statement_suffix_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative workflow truth\./AegisOps control-plane records remain authoritative workflow truth. unless assistant output agrees/g' \
  "${statement_suffix_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${statement_suffix_repo}" \
  "Missing Phase 50.12 service facade pressure contract statement: AegisOps control-plane records remain authoritative workflow truth."

missing_cluster_repo="${workdir}/missing-cluster"
create_valid_repo "${missing_cluster_repo}"
perl -0pi -e 's/- assistant residual helper cluster\n//g' \
  "${missing_cluster_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${missing_cluster_repo}" \
  "Missing Phase 50.12 service facade pressure contract statement: - assistant residual helper cluster"

missing_fallback_repo="${workdir}/missing-fallback"
create_valid_repo "${missing_fallback_repo}"
perl -0pi -e 's/If the sub-1500 target cannot be reached safely, the fallback is to preserve behavior, keep the public `AegisOpsControlPlaneService` facade, record the blocker cluster explicitly, and require the next contract to lower or fence that exact residual cluster instead of claiming long-term completion\.//g' \
  "${missing_fallback_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${missing_fallback_repo}" \
  "Missing Phase 50.12 service facade pressure contract statement: If the sub-1500 target cannot be reached safely, the fallback is to preserve behavior, keep the public \`AegisOpsControlPlaneService\` facade, record the blocker cluster explicitly, and require the next contract to lower or fence that exact residual cluster instead of claiming long-term completion."

missing_non_goal_repo="${workdir}/missing-non-goal"
create_valid_repo "${missing_non_goal_repo}"
perl -0pi -e 's/No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed\.//g' \
  "${missing_non_goal_repo}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
assert_fails_with \
  "${missing_non_goal_repo}" \
  "Missing Phase 50.12 service facade pressure contract statement: - No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed."

premature_service_baseline_repo="${workdir}/premature-service-baseline"
create_valid_repo "${premature_service_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=1500 max_effective_lines=1350 max_facade_methods=95 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0009 phase=50.12 issue=#1016" \
  >"${premature_service_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${premature_service_baseline_repo}" \
  "Phase 50.12 contract forbids refreshing the service.py hotspot baseline before implementation evidence exists."

duplicate_service_baseline_repo="${workdir}/duplicate-service-baseline"
create_valid_repo "${duplicate_service_baseline_repo}"
printf '%s\n' \
  "control-plane/aegisops_control_plane/service.py max_lines=1812 max_effective_lines=1632 max_facade_methods=125 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.11.7 issue=#1007" \
  >>"${duplicate_service_baseline_repo}/docs/maintainability-hotspot-baseline.txt"
assert_fails_with \
  "${duplicate_service_baseline_repo}" \
  "Phase 50.12 contract requires exactly one service.py hotspot baseline entry."

echo "verify-phase-50-12-service-facade-pressure-contract tests passed"
