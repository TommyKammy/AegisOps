#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-50-maintainability-adr.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_phase50_adr() {
  local target="$1"
  local content="$2"

  mkdir -p "${target}/docs/adr"
  printf '%s\n' "${content}" >"${target}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"
}

create_valid_repo() {
  local target="$1"

  write_phase50_adr "${target}" '# ADR-0004: Phase 50 Maintainability Hotspot Map and Migration Order

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #946, #947
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

Phase 49.0 completed the behavior-preserving `AegisOpsControlPlaneService` decomposition sequence governed by ADR-0003.

ADR-0003 remains authoritative for the Phase 49.0 facade-preservation contract and for the closeout ceiling recorded in `docs/maintainability-hotspot-baseline.txt`.

Phase 50 is a follow-on maintainability backlog. It must lower or fence the remaining hotspots after the ADR-0003 closeout ceiling instead of treating the ceiling as permission for new responsibility growth.

The first Phase 50 implementation issue must not start before this ADR is merged.

## 2. Decision

We will run Phase 50 as ordered, behavior-preserving hotspot reduction after the ADR-0003 closeout.

The Phase 50 target hotspots are:
- `control-plane/aegisops_control_plane/service.py`
- restore validation
- HTTP surface
- assistant, detection, and operator inspection second-hotspot risk
- operator-ui route tests

The migration order is:
1. #947 Phase 50 maintainability ADR and verifier gate
2. `service.py` facade ceiling reduction or fencing
3. restore validation boundary extraction and snapshot-consistency proof
4. HTTP surface routing and auth-boundary review split
5. assistant, detection, and operator inspection second-hotspot risk reduction
6. operator-ui route test decomposition
7. hotspot baseline refresh and Phase 50 validation closeout

The child issues are not parallelizable unless a later accepted ADR or issue update explicitly changes the dependency order.

The Phase 50 baseline refresh may only happen after the implementation slices prove the hotspots have actually been lowered or fenced.

## 3. Decision Drivers

- maintainability
- behavior preservation
- authority-boundary preservation

## 4. Options Considered

### Option A: Ordered post-Phase 49 hotspot reduction

#### Description
Reduce or fence the remaining hotspots in order.

#### Pros
- Keeps implementation tied to a reviewed hotspot map.

#### Cons
- Requires strict sequencing.

### Option B: Refresh the hotspot baseline before extraction

#### Description
Update the baseline up front.

#### Pros
- Makes the target visible early.

#### Cons
- Redefines truth around a desired projection.

### Option C: Let each child issue choose its own hotspot order

#### Description
Allow local extraction order.

#### Pros
- Maximizes scheduling flexibility.

#### Cons
- Recreates ambiguity.

## 5. Rationale

Option A is selected because it follows `docs/maintainability-decomposition-thresholds.md` while respecting the ADR-0003 closeout state.

## 6. Consequences

### Positive Consequences
- Phase 50 has a fixed hotspot map.

### Negative Consequences
- Phase 50 cannot safely parallelize its implementation slices by default.

### Neutral / Follow-up Consequences
- Phase 50 closeout owns the final hotspot baseline refresh.

## 7. Implementation Impact

Later Phase 50 implementation slices must preserve production behavior, public service entrypoints, runtime configuration, and authority semantics unless a separate accepted ADR and scoped issue explicitly allow a change.

The restore validation slice must prove snapshot-consistent reads or explicit rejection of mixed-snapshot results, and failed paths must leave no orphan record, partial durable write, or half-restored state.

The HTTP surface slice must preserve trusted-boundary behavior and must not trust raw forwarded headers, host, proto, tenant, user-id, or client-supplied identity hints unless a trusted proxy or boundary has authenticated and normalized them.

The assistant, detection, and operator inspection slice must keep advisory output, detection evidence, and inspection projections subordinate to directly linked authoritative control-plane records.

The operator-ui route test slice must reduce test hotspot pressure without introducing new operator capability, approval behavior, execution behavior, or routing authority.

## 8. Security Impact

This ADR does not change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, secrets, restore, readiness, or write-capable authority.

## 9. Rollback / Exit Strategy

Rollback removes this ADR and its verifier wiring before Phase 50 implementation starts.

## 10. Validation

Run `bash scripts/verify-phase-50-maintainability-adr.sh`.
Run `bash scripts/test-verify-phase-50-maintainability-adr.sh`.
Run `bash scripts/verify-maintainability-hotspots.sh`.
Run `node <codex-supervisor-root>/dist/index.js issue-lint 947 --config <supervisor-config-path>`.

## 11. Non-Goals

- No production code extraction is approved by this ADR.
- No commercial readiness capability is added.
- Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context and do not become workflow truth.

## 12. Approval

- **Proposed By**: Codex for Issue #947
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

missing_adr_repo="${workdir}/missing-adr"
create_valid_repo "${missing_adr_repo}"
rm "${missing_adr_repo}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"
assert_fails_with \
  "${missing_adr_repo}" \
  "Missing Phase 50 maintainability ADR"

missing_hotspot_repo="${workdir}/missing-hotspot"
create_valid_repo "${missing_hotspot_repo}"
perl -0pi -e 's/- HTTP surface\n//' \
  "${missing_hotspot_repo}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"
assert_fails_with \
  "${missing_hotspot_repo}" \
  "Missing Phase 50 maintainability ADR statement: - HTTP surface"

missing_order_repo="${workdir}/missing-order"
create_valid_repo "${missing_order_repo}"
perl -0pi -e 's/3\. restore validation boundary extraction and snapshot-consistency proof/3. restore validation extraction omitted/' \
  "${missing_order_repo}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"
assert_fails_with \
  "${missing_order_repo}" \
  "Missing Phase 50 maintainability ADR statement: 3. restore validation boundary extraction and snapshot-consistency proof"

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context and do not become workflow truth\.//g' \
  "${missing_authority_repo}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 50 maintainability ADR statement: Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context and do not become workflow truth."

missing_validation_repo="${workdir}/missing-validation"
create_valid_repo "${missing_validation_repo}"
perl -0pi -e 's/Run `bash scripts\/verify-maintainability-hotspots\.sh`\.\n//g' \
  "${missing_validation_repo}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"
assert_fails_with \
  "${missing_validation_repo}" \
  "Missing Phase 50 maintainability ADR statement: Run \`bash scripts/verify-maintainability-hotspots.sh\`."

echo "verify-phase-50-maintainability-adr tests passed"
